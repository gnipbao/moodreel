#!/usr/bin/env node
// Render a page that draws itself as a function of time.
//
// The page contract (a folder with index.html):
//   window.DUR = <seconds>;              length of the film
//   window.render = (t) => { ... };      draw the frame at second t; deterministic, no state carried between calls
//   window.READY = true;                 set once fonts and images are loaded
//
// Usage:
//   node render/render.mjs video <dir> [--fps 30] [--size 1920x1080] [--workers 2] [--engine auto|framevelo|chrome]
//                                       [--quality draft|standard|high] [--from s] [--to s] [--out <dir>/out/video.mp4]
//   node render/render.mjs still <dir> <t> [<t> ...] [--size 1920x1080] [--out <dir>/stills]
//   node render/render.mjs texts <dir> [--step 0.1] [--size 1920x1080] [--out texts.json]   what window.TEXTS(t) reports
//
// --variant '<json>' (any command): the page finds the object as window.VARIANT before its scripts run (kit/variant.js
// reads it), so one film renders as several: another palette, seed, line of text or length.
//
// --samples N [--shutter s] (any command): motion blur. The page finds window.MOTION_BLUR = { samples, shutter, fps }
// before its scripts run, and kit/stage.js makes each frame the average of N sub-frames spread over `s` of the frame's
// time (default 0.2, a fifth: a short shutter, so only fast motion streaks). Rendering costs about N times as much.
//
// Two engines make video. FrameVelo (github.com/gnipbao/framevelo, a dependency) keeps every frame on the GPU: the
// stage canvas becomes a VideoFrame for the hardware H.264 encoder (WebCodecs), muxed without a pass through Node or
// x264; it is several times faster and uses a fraction of the CPU. It renders the film through an entry page beside
// index.html that sets window.VARIANT, loads main.js and, once the film is READY, offers render(t) as the seek
// FrameVelo calls for every frame. Chrome (below) screenshots each frame and encodes with x264: slower, but every
// render is the same, bit for bit, which the benches need. --engine auto (the default, or MOODREEL_ENGINE) takes
// FrameVelo when it is installed, on macOS (its tested platform), and Chrome otherwise. Stills and texts are Chrome's.
//
// Chrome: each worker drives a Chrome of its own and encodes one contiguous range of frames; the ranges are joined
// without re-encoding. Any page error stops the render.
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
  const opts = { fps: 30, size: '1920x1080', workers: 1, out: null, times: [], step: 0.1,
    engine: process.env.MOODREEL_ENGINE || 'auto', quality: 'high' };
  for (let i = 0; i < rest.length; i++) {
    const a = rest[i];
    if (a === '--fps') opts.fps = Number(rest[++i]);
    else if (a === '--size') opts.size = rest[++i];
    else if (a === '--workers') opts.workers = Number(rest[++i]);
    else if (a === '--out') opts.out = rest[++i];
    else if (a === '--step') opts.step = Number(rest[++i]);
    else if (a === '--variant') opts.variant = JSON.parse(rest[++i]);
    else if (a === '--engine') opts.engine = rest[++i];
    else if (a === '--quality') opts.quality = rest[++i];
    else if (a === '--bitrate') opts.bitrate = rest[++i];
    else if (a === '--from') opts.from = Number(rest[++i]);
    else if (a === '--samples') opts.samples = Number(rest[++i]);
    else if (a === '--shutter') opts.shutter = Number(rest[++i]);
    else if (a === '--to') opts.to = Number(rest[++i]);
    else opts.times.push(Number(a));
  }
  const [w, h] = opts.size.split('x').map(Number);
  if (!['video', 'still', 'texts'].includes(cmd) || !dir || !(w > 0 && h > 0) || !(opts.fps > 0)
      || (opts.samples != null && !(opts.samples >= 1)) || (opts.shutter != null && !(opts.shutter > 0 && opts.shutter <= 1))
      || !['auto', 'framevelo', 'chrome'].includes(opts.engine) || !['draft', 'standard', 'high'].includes(opts.quality)) {
    console.error('usage: render.mjs video|still|texts <dir> [t ...] [--fps 30] [--size WxH] [--workers N] [--step s] '
      + "[--engine auto|framevelo|chrome] [--quality draft|standard|high] [--variant '{...}'] [--samples N] [--shutter s] [--out path]");
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
let BLUR = null;                                          // --samples/--shutter: window.MOTION_BLUR, for every page

async function openPage(browser, url, w, h) {
  const page = await browser.newPage();
  if (VARIANT) await page.evaluateOnNewDocument(v => { window.VARIANT = v; }, VARIANT);
  if (BLUR) await page.evaluateOnNewDocument(b => { window.MOTION_BLUR = b; }, BLUR);
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
  const from = o.from ?? 0, to = Math.min(dur, o.to ?? dur);              // a slice of the film, for a preview
  const total = Math.round((to - from) * o.fps);
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
        await enc.write(await frame(ctx, from + f / o.fps, 'jpeg'));
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

// FrameVelo's entry page: the film's own page, with window.VARIANT set before its scripts run and Moodreel's contract
// (DUR, render, READY) offered as FrameVelo's once the film is ready. A page error becomes a seek that throws, so the
// render stops on it at once instead of waiting for a film that will never be ready.
const ENTRY = (html, variant, fps, blur) => html
  .replace(/<script\b/i, `<script>window.VARIANT = ${JSON.stringify(variant ?? null)}; window.MOTION_BLUR = ${JSON.stringify(blur ?? null)};</script><script`)
  .replace(/<\/body>/i, `<script>
(() => {
  let failed = null;
  addEventListener('error', e => { failed = e.error || new Error(e.message); });
  addEventListener('unhandledrejection', e => { failed = e.reason; });
  const offer = () => {
    if (failed) window.__framevelo = { duration: 1, seek() { throw failed; } };
    else if (window.READY) window.__framevelo = { duration: window.DUR, fps: ${fps}, seek: t => window.render(t) };
    else setTimeout(offer, 20);
  };
  offer();
})();
</script></body>`);

async function engineFor(o) {
  if (o.engine === 'chrome') return null;
  const fv = await import('framevelo').catch(() => null);
  if (o.engine === 'framevelo' && !fv) throw new Error('--engine framevelo: FrameVelo is not installed (npm install)');
  return o.engine === 'framevelo' || (fv && process.platform === 'darwin') ? fv : null;
}

async function videoFramevelo(fv, o) {
  const out = path.resolve(o.out || path.join(o.dir, 'out', 'video.mp4'));
  fs.mkdirSync(path.dirname(out), { recursive: true });
  const entry = path.join(path.resolve(o.dir), `.framevelo-${process.pid}.html`);
  fs.writeFileSync(entry, ENTRY(fs.readFileSync(path.join(o.dir, 'index.html'), 'utf8'), o.variant, o.fps, BLUR));
  let shown = -60;
  try {
    const r = await fv.render({
      input: entry, output: out, fps: o.fps, viewport: { width: o.w, height: o.h }, width: o.w, height: o.h,
      mode: 'canvas', selector: 'body > canvas', quality: o.quality, readyTimeoutMs: 120_000, chromePath: executablePath,
      ...(o.bitrate ? { bitrate: fv.parseBitrate(o.bitrate) } : {}),
      ...(o.from != null ? { start: o.from } : {}), ...(o.to != null ? { duration: o.to - (o.from ?? 0) } : {}),
      onProgress: (done, total) => { if (done - shown >= 60 || done === total) { shown = done; console.log(`framevelo: ${done}/${total}`); } },
    });
    for (const w of r.warnings) console.log(`framevelo: ${w}`);
    console.log(`done ${out}: ${r.frames} frames in ${(r.wallMs / 1000).toFixed(1)}s (framevelo, `
      + `${r.hardwareEncoder ? 'hardware' : 'software'} ${r.codec}, ${r.mode})`);
  } finally {
    fs.rmSync(entry, { force: true });
  }
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
BLUR = o.samples > 1 ? { samples: Math.round(o.samples), shutter: o.shutter ?? 0.2, fps: o.fps } : null;
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
  const fv = o.cmd === 'video' ? await engineFor(o) : null;
  if (fv) await videoFramevelo(fv, o);
  else await ({ video, still: stills, texts })[o.cmd](launch, url, o);
} catch (e) {
  console.error(e.message);
  process.exitCode = 1;
} finally {
  await Promise.all(browsers.map(b => b.close().catch(() => {})));
  server.closeAllConnections();
  server.close();
}
