#!/usr/bin/env node
// Render a page that draws itself as a function of time.
//
// The page contract (a folder with index.html):
//   window.DUR = <seconds>;              length of the film
//   window.render = (t) => { ... };      draw the frame at second t; deterministic, no state carried between calls
//   window.READY = true;                 set once fonts and images are loaded
//
// Usage:
//   node render/render.mjs video <dir> [--fps 30] [--size 1920x1080] [--workers 2] [--out <dir>/out/video.mp4]
//   node render/render.mjs still <dir> <t> [<t> ...] [--size 1920x1080] [--out <dir>/stills]
//   node render/render.mjs texts <dir> [--step 0.1] [--size 1920x1080] [--out texts.json]   what window.TEXTS(t) reports
//
// --variant '<json>' (any command): the page finds the object as window.VARIANT before its scripts run (kit/variant.js
// reads it), so one film renders as several: another palette, seed, line of text or length.
//
// Each worker drives a Chrome of its own and encodes one contiguous range of frames; the ranges are joined without
// re-encoding. Any page error stops the render.
//
// Speed: Chrome paces frames to the display (vsync, 60 Hz), and a screenshot waits for the next one, which put about
// 42 ms on every frame whatever its size or format. With that pacing off a screenshot takes 8-18 ms (1280x720 JPEG),
// and each one still shows the frame just drawn (checked against the canvas's own pixels, frame by frame, on every
// example). One Chrome per worker: tabs of one site share a renderer process, and the workers would take turns on its
// main thread. 2D canvas is drawn in software: on the GPU, shadows and blurs came out a level or two different from
// one render to the next (invisible, but enough to flip a measurement on the edge); in software every render of a
// film is the same, bit for bit. WebGL stays on the GPU. Runs on puppeteer-core, with the Chrome puppeteer installs
// or MOODREEL_CHROME.
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import { spawn } from 'node:child_process';
import puppeteer from 'puppeteer-core';

const TYPES = {
  '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.mjs': 'text/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8', '.css': 'text/css; charset=utf-8', '.svg': 'image/svg+xml',
  '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.webp': 'image/webp', '.gif': 'image/gif',
  '.woff2': 'font/woff2', '.woff': 'font/woff', '.ttf': 'font/ttf', '.otf': 'font/otf', '.wasm': 'application/wasm',
};

function parse(argv) {
  const [cmd, dir, ...rest] = argv;
  const opts = { fps: 30, size: '1920x1080', workers: 1, out: null, times: [], step: 0.1 };
  for (let i = 0; i < rest.length; i++) {
    const a = rest[i];
    if (a === '--fps') opts.fps = Number(rest[++i]);
    else if (a === '--size') opts.size = rest[++i];
    else if (a === '--workers') opts.workers = Number(rest[++i]);
    else if (a === '--out') opts.out = rest[++i];
    else if (a === '--step') opts.step = Number(rest[++i]);
    else if (a === '--variant') opts.variant = JSON.parse(rest[++i]);
    else opts.times.push(Number(a));
  }
  const [w, h] = opts.size.split('x').map(Number);
  if (!['video', 'still', 'texts'].includes(cmd) || !dir || !(w > 0 && h > 0) || !(opts.fps > 0)) {
    console.error('usage: render.mjs video|still|texts <dir> [t ...] [--fps 30] [--size WxH] [--workers N] [--step s] '
      + "[--variant '{...}'] [--out path]");
    process.exit(2);
  }
  if (cmd === 'video' && (w % 2 || h % 2)) {
    console.error(`--size ${w}x${h}: H.264 needs even width and height`);
    process.exit(2);
  }
  return { cmd, dir: path.resolve(dir), w, h, ...opts };
}

// Static files from the film folder only, on loopback.
function serve(root) {
  return new Promise(resolve => {
    const server = http.createServer((req, res) => {
      let rel;
      try { rel = decodeURIComponent(new URL(req.url, 'http://x').pathname); } catch { res.writeHead(400).end(); return; }
      const file = path.resolve(root, '.' + rel);
      if (file !== root && !file.startsWith(root + path.sep)) { res.writeHead(403).end(); return; }
      fs.readFile(file, (err, data) => {
        if (err) { res.writeHead(404).end(); return; }
        res.writeHead(200, { 'Content-Type': TYPES[path.extname(file).toLowerCase()] || 'application/octet-stream' }).end(data);
      });
    });
    server.listen(0, '127.0.0.1', () => resolve(server));
  });
}

let VARIANT = null;                                       // --variant, for every page of the render

async function openPage(browser, url, w, h) {
  const page = await browser.newPage();
  if (VARIANT) await page.evaluateOnNewDocument(v => { window.VARIANT = v; }, VARIANT);
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  page.on('requestfailed', r => errors.push(`failed to load ${r.url()} (${r.failure()?.errorText})`));
  await page.setViewport({ width: w, height: h, deviceScaleFactor: 1 });
  await page.goto(url, { waitUntil: 'load' });
  // ready, or an error first (a page that throws while loading never gets ready: say so now, not in two minutes)
  let poll;
  const failed = new Promise((_, fail) => { poll = setInterval(() => errors.length && fail(new Error(errors.join('\n'))), 100); });
  try {
    await Promise.race([page.waitForFunction(() => window.READY === true, { timeout: 120_000 }), failed]);
  } finally {
    clearInterval(poll);
  }
  if (errors.length) throw new Error(errors.join('\n'));
  return { page, errors };
}

async function frame(ctx, t, type) {
  await ctx.page.evaluate(t => window.render(t), t);
  if (ctx.errors.length) throw new Error(ctx.errors.join('\n'));
  return ctx.page.screenshot(type === 'jpeg' ? { type, quality: 95, optimizeForSpeed: true } : { type });
}

function encoder(file, fps) {
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'mjpeg',
    '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '14', '-pix_fmt', 'yuv420p', file],
  { stdio: ['pipe', 'inherit', 'inherit'] });
  const done = new Promise((ok, fail) => {
    ff.on('error', fail);
    ff.on('close', code => (code === 0 ? ok() : fail(new Error(`ffmpeg exited with ${code}`))));
  });
  const write = buf => (ff.stdin.write(buf) ? Promise.resolve() : new Promise(r => ff.stdin.once('drain', r)));
  return { write, end: () => { ff.stdin.end(); return done; }, kill: () => { done.catch(() => {}); ff.kill('SIGKILL'); } };
}

async function video(launch, url, o) {
  const first = await launch();
  const probe = await openPage(first, url, o.w, o.h);
  const dur = await probe.page.evaluate(() => window.DUR);
  await probe.page.close();
  if (!(dur > 0)) throw new Error(`window.DUR must be a positive number of seconds (got ${dur})`);
  const total = Math.round(dur * o.fps);
  const out = path.resolve(o.out || path.join(o.dir, 'out', 'video.mp4'));
  fs.mkdirSync(path.dirname(out), { recursive: true });
  const tmp = fs.mkdtempSync(path.join(path.dirname(out), '.segments-'));
  const per = Math.ceil(total / o.workers);
  const started = Date.now();
  const open = new Set();                                  // encoders still taking frames: killed if the render fails
  try {
    const parts = await Promise.all([...Array(o.workers)].map(async (_, k) => {
      const a = k * per, b = Math.min(total, a + per);
      if (a >= b) return null;
      const ctx = await openPage(k === 0 ? first : await launch(), url, o.w, o.h);
      const file = path.join(tmp, `part${k}.mp4`);
      const enc = encoder(file, o.fps);
      open.add(enc);
      for (let f = a; f < b; f++) {
        await enc.write(await frame(ctx, f / o.fps, 'jpeg'));
        if ((f - a) % 60 === 0) console.log(`worker ${k}: ${f - a}/${b - a}`);
      }
      open.delete(enc);
      await enc.end();
      await ctx.page.close();
      return file;
    }));
    const list = path.join(tmp, 'parts.txt');
    fs.writeFileSync(list, parts.filter(Boolean).map(p => `file '${p}'`).join('\n'));
    await new Promise((ok, fail) => spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', list,
      '-c', 'copy', out], { stdio: 'inherit' }).on('close', c => (c === 0 ? ok() : fail(new Error('joining parts failed')))));
  } finally {
    for (const enc of open) enc.kill();
    fs.rmSync(tmp, { recursive: true, force: true });
  }
  console.log(`done ${out}: ${total} frames in ${((Date.now() - started) / 1000).toFixed(1)}s`);
}

async function stills(launch, url, o) {
  const outDir = path.resolve(o.out || path.join(o.dir, 'stills'));
  fs.mkdirSync(outDir, { recursive: true });
  const ctx = await openPage(await launch(), url, o.w, o.h);
  for (const t of o.times) {
    const file = path.join(outDir, `t_${t}.jpg`);
    fs.writeFileSync(file, await frame(ctx, t, 'jpeg'));
    console.log(file);
  }
}

// every on-screen text over time, from the page's optional window.TEXTS(t): [{id, text, x0, y0, x1, y1}]
async function texts(launch, url, o) {
  const ctx = await openPage(await launch(), url, o.w, o.h);
  const dur = await ctx.page.evaluate(() => window.DUR);
  const samples = [];
  for (let t = 0; t <= dur + 1e-9; t += o.step) {
    const list = await ctx.page.evaluate(t => (typeof window.TEXTS === 'function' ? window.TEXTS(t) : null), t);
    if (list === null) throw new Error('the page has no window.TEXTS(t)');
    samples.push({ t: Math.round(t * 1000) / 1000, texts: list });
  }
  const json = JSON.stringify({ dur, step: o.step, width: o.w, height: o.h, samples });
  if (o.out) fs.writeFileSync(o.out, json);
  else console.log(json);
}

const o = parse(process.argv.slice(2));
VARIANT = o.variant ?? null;
if (!fs.existsSync(path.join(o.dir, 'index.html'))) { console.error(`no index.html in ${o.dir}`); process.exit(2); }
const server = await serve(o.dir);
const executablePath = process.env.MOODREEL_CHROME || await (await import('puppeteer')).default.executablePath();
const browsers = [];
async function launch() {
  const b = await puppeteer.launch({ executablePath, headless: true, args: ['--hide-scrollbars', '--force-color-profile=srgb',
    '--disable-gpu-vsync', '--disable-frame-rate-limit', '--disable-accelerated-2d-canvas'] });
  browsers.push(b);
  return b;
}
try {
  const url = `http://127.0.0.1:${server.address().port}/index.html`;
  await ({ video, still: stills, texts })[o.cmd](launch, url, o);
} catch (e) {
  console.error(e.message);
  process.exitCode = 1;
} finally {
  await Promise.all(browsers.map(b => b.close().catch(() => {})));
  server.closeAllConnections();
  server.close();
}
