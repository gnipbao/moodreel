#!/usr/bin/env node
// The social wall's browser: find a product's real posts on platforms that need no login, and record the ones the
// user picks, each as a card for the wall (`moodreel wall`, skills/moodreel/references/produce/social-wall.md).
//
//   node render/wall.mjs search <query> --out <dir> [--platforms youtube,bilibili] [--max 24] [--lang en-US]
//       writes <dir>/candidates.json and <dir>/thumbs/NN.jpg: every post whose title, description or tags name the
//       query, numbered for the user to pick from
//   node render/wall.mjs record <dir> --pick 1,4,7 [--seconds 6.5] [--lang en-US]
//       opens each picked post in a phone-sized window, lets it play muted and records the post as it shows (the
//       platform's own player, title and buttons) to <dir>/clips/NN.webm, with <dir>/clips.json
//
// Manners: one page at a time, a pause between pages, no login and no way round a platform's checks. A page that
// asks for a sign-in or shows a bot check stops that post, with the reason, and the rest go on. Consent banners are
// declined (only what the page needs). The proxy in HTTPS_PROXY, when set, is the browser's.
import fs from 'node:fs';
import path from 'node:path';
import puppeteer from 'puppeteer';

const argv = process.argv.slice(2);
const opt = (name, dflt) => { const i = argv.indexOf(`--${name}`); return i >= 0 ? argv[i + 1] : dflt; };
const [cmd, target] = argv;
const sleep = ms => new Promise(ok => setTimeout(ok, ms));
const norm = s => (s || '').toLowerCase().replace(/<[^>]+>/g, '').replace(/[\s\-_·.]+/g, '');

async function browser(lang) {
  const proxy = process.env.HTTPS_PROXY || process.env.https_proxy;
  return puppeteer.launch({ headless: true, args: ['--autoplay-policy=no-user-gesture-required', `--lang=${lang}`,
    '--hide-scrollbars', '--force-color-profile=srgb', ...(proxy ? [`--proxy-server=${proxy.replace(/^\w+:\/\//, '')}`] : [])] });
}

// a page the platform won't show without a sign-in or a check: stop rather than work round it
async function blocked(page) {
  const text = (await page.evaluate(() => document.body?.innerText || '')).slice(0, 4000);
  if (/not a bot|unusual traffic|verify you are human|验证码|人机验证|安全验证/i.test(text)) return 'a bot check';
  if (/sign in to (watch|continue|confirm)|请先登录|登录后查看/i.test(text)) return 'a sign-in';
  return null;
}

async function declineConsent(page) {
  for (const label of ['Reject all', 'Reject the use of cookies', '全部拒绝', '拒绝全部']) {
    const b = await page.$(`::-p-aria(${label})`);
    if (b) { await b.click(); await sleep(1500); return true; }
  }
  return false;
}

// YouTube's interface language follows `hl`, not the browser's
const hl = lang => lang.startsWith('zh') ? lang : lang.split('-')[0];

async function youtube(page, query, max, lang) {
  await page.goto(`https://www.youtube.com/results?search_query=${encodeURIComponent(query)}&hl=${hl(lang)}`, { waitUntil: 'networkidle2', timeout: 60000 });
  if (await declineConsent(page)) await page.waitForNetworkIdle({ timeout: 20000 }).catch(() => {});
  const why = await blocked(page);
  if (why) { console.error(`youtube: ${why}, skipped`); return []; }
  const items = await page.evaluate(() => {
    const out = [], text = t => t?.simpleText ?? t?.runs?.map(r => r.text).join('') ?? t?.content ?? '';
    const walk = o => {
      if (!o || typeof o !== 'object') return;
      if (o.videoRenderer) {
        const v = o.videoRenderer;
        out.push({ kind: 'video', id: v.videoId, title: text(v.title), author: text(v.ownerText), views: text(v.viewCountText),
          date: text(v.publishedTimeText), duration: text(v.lengthText), about: (v.detailedMetadataSnippets || []).map(s => text(s.snippetText)).join(' '),
          thumb: v.thumbnail?.thumbnails?.at(-1)?.url });
      } else if (o.shortsLockupViewModel) {
        const s = o.shortsLockupViewModel;
        out.push({ kind: 'short', id: s.onTap?.innertubeCommand?.reelWatchEndpoint?.videoId, title: s.overlayMetadata?.primaryText?.content,
          views: s.overlayMetadata?.secondaryText?.content, thumb: s.thumbnail?.sources?.[0]?.url });
      } else if (o.reelItemRenderer) {
        const s = o.reelItemRenderer;
        out.push({ kind: 'short', id: s.videoId, title: text(s.headline), views: text(s.viewCountText), thumb: s.thumbnail?.thumbnails?.[0]?.url });
      }
      for (const k in o) walk(o[k]);
    };
    walk(window.ytInitialData);
    return out;
  });
  const seen = new Set(), q = norm(query);
  const posts = items.filter(i => i.id && !seen.has(i.id) && seen.add(i.id) && norm(`${i.title} ${i.author} ${i.about}`).includes(q)).slice(0, max)
    .map(i => ({ ...i, platform: 'youtube', url: i.kind === 'short' ? `https://www.youtube.com/shorts/${i.id}` : `https://www.youtube.com/watch?v=${i.id}`,
      thumb: i.thumb || `https://i.ytimg.com/vi/${i.id}/hqdefault.jpg` }));
  // a Short's result doesn't name its channel; YouTube's oEmbed (the data an embed shows) does
  for (const p of posts.filter(p => !p.author)) {
    p.author = await page.evaluate(async url => (await (await fetch(`/oembed?format=json&url=${encodeURIComponent(url)}`)).json())?.author_name,
      p.url).catch(() => '') || '';
    await sleep(250);
  }
  return posts;
}

async function bilibili(page, query, max) {
  const found = [];
  const listen = async r => {
    if (!/x\/web-interface\/(wbi\/)?search\/(type|all)/.test(r.url())) return;
    try {
      const d = (await r.json())?.data;
      const rows = Array.isArray(d?.result) ? d.result.flatMap(x => (x.result_type ? (x.result_type === 'video' ? x.data : []) : [x])) : [];
      found.push(...rows);
    } catch { /* not JSON */ }
  };
  page.on('response', listen);
  await page.goto(`https://search.bilibili.com/video?keyword=${encodeURIComponent(query)}`, { waitUntil: 'networkidle2', timeout: 60000 });
  await sleep(1500);
  page.off('response', listen);
  // the first page of results comes rendered with the page, in its store; later pages through the API above
  found.unshift(...await page.evaluate(() => window.__pinia?.searchTypeResponse?.searchTypeResponse?.result || []));
  const why = await blocked(page);
  if (why && !found.length) { console.error(`bilibili: ${why}, skipped`); return []; }
  const seen = new Set(), q = norm(query);
  const posts = found.filter(v => v.bvid && !seen.has(v.bvid) && seen.add(v.bvid) && norm(`${v.title} ${v.description} ${v.tag}`).includes(q))
    .slice(0, max).map(v => ({ platform: 'bilibili', kind: 'video', id: v.bvid, url: `https://www.bilibili.com/video/${v.bvid}`,
      title: (v.title || '').replace(/<[^>]+>/g, ''), author: v.author, views: String(v.play ?? ''), duration: v.duration,
      date: v.pubdate ? new Date(v.pubdate * 1000).toISOString().slice(0, 10) : '', about: (v.description || '').slice(0, 200),
      thumb: (v.pic || '').replace(/^\/\//, 'https://') }));
  // what the uploader allows: a post marked "no reprint" (未经作者授权，禁止转载) is flagged for the user's pick
  for (const p of posts) {
    const rights = await page.evaluate(async id => (await (await fetch(`https://api.bilibili.com/x/web-interface/view?bvid=${id}`,
      { credentials: 'include' })).json())?.data?.rights, p.id).catch(() => null);
    if (rights?.no_reprint) p.notice = '未经作者授权，禁止转载';
    await sleep(300);
  }
  return posts;
}

async function search() {
  const out = opt('out'), max = +opt('max', 24), lang = opt('lang', 'en-US');
  const platforms = opt('platforms', 'youtube,bilibili').split(',');
  fs.mkdirSync(path.join(out, 'thumbs'), { recursive: true });
  const b = await browser(lang), page = await b.newPage();
  await page.setViewport({ width: 1280, height: 900 });
  await page.setExtraHTTPHeaders({ 'Accept-Language': `${lang},${lang.split('-')[0]};q=0.9` });
  const all = [];
  for (const p of platforms) {
    const got = await ({ youtube, bilibili })[p]?.(page, target, max, lang) ?? [];
    console.log(`${p}: ${got.length} posts name "${target}"`);
    all.push(...got);
    await sleep(1200);
  }
  const shot = await b.newPage();
  for (const [i, c] of all.entries()) {
    c.n = i + 1;
    if (!c.thumb) continue;
    try {
      const r = await shot.goto(c.thumb, { timeout: 30000, referer: c.platform === 'bilibili' ? 'https://www.bilibili.com/' : undefined });
      if (r?.ok()) fs.writeFileSync(path.join(out, 'thumbs', `${String(c.n).padStart(2, '0')}.jpg`), await r.buffer());
    } catch { /* a missing thumbnail only leaves a blank tile */ }
  }
  await b.close();
  fs.writeFileSync(path.join(out, 'candidates.json'), JSON.stringify({ query: target, searched: new Date().toISOString(), platforms, posts: all }, null, 1));
  console.log(`${all.length} candidates -> ${path.join(out, 'candidates.json')}`);
}

// how each kind of post is shown: the window it opens in (CSS px; screencasts are taken at one pixel per CSS px, so
// the window is large enough for a card of a 4K wall), and the parts of the page a card keeps (their union)
const FRAME = {
  youtube: {
    short: { view: [900, 1240], keep: ['#shorts-player', 'reel-action-bar-view-model'], pad: [0, 16, 0, 0] },
    video: { view: [840, 1240], keep: ['#movie_player', '#above-the-fold'], pad: [0, 0, 8, 0] },
  },
  bilibili: { video: { view: [1600, 1240], keep: ['.video-info-container', '.bpx-player-video-area'], pad: [0, 0, 0, 0] } },
};

async function record() {
  const dir = target, seconds = +opt('seconds', 6.5), lang = opt('lang', 'en-US');
  const picks = opt('pick', '').split(',').map(Number).filter(Boolean);
  const { posts } = JSON.parse(fs.readFileSync(path.join(dir, 'candidates.json'), 'utf8'));
  fs.mkdirSync(path.join(dir, 'clips'), { recursive: true });
  const b = await browser(lang), clips = [];
  for (const n of picks) {
    const c = posts.find(p => p.n === n);
    if (!c) { console.error(`no candidate ${n}`); continue; }
    const frame = FRAME[c.platform]?.[c.kind];
    const page = await b.newPage();
    await page.setViewport({ width: frame.view[0], height: frame.view[1] });
    await page.setExtraHTTPHeaders({ 'Accept-Language': `${lang},${lang.split('-')[0]};q=0.9` });
    try {
      await page.goto(c.platform === 'youtube' ? `${c.url}${c.url.includes('?') ? '&' : '?'}hl=${hl(lang)}` : c.url, { waitUntil: 'networkidle2', timeout: 60000 });
      if (await declineConsent(page)) await page.waitForNetworkIdle({ timeout: 20000 }).catch(() => {});
      // the video plays, muted, from the start; an ad before it is waited out (skipped when the player offers it)
      const playing = await page.waitForFunction(() => {
        document.querySelector('.ytp-skip-ad-button, .ytp-ad-skip-button-modern')?.click();
        const v = [...document.querySelectorAll('video')].find(v => v.offsetWidth > 100);
        if (!v || document.querySelector('.ad-showing')) return false;
        v.muted = true;
        if (v.paused) v.play().catch(() => {});
        return v.currentTime > 0.3;
      }, { timeout: 45000, polling: 250 }).then(() => true, () => false);
      if (!playing) throw new Error(`its video did not start${(await blocked(page)) ? ` (the page shows ${await blocked(page)})` : ''}`);
      // a sign-in prompt over the player is closed (it is an offer, not a wall); the post stays as the platform shows it
      await page.evaluate(() => {
        document.querySelectorAll('.bpx-player-toast-item .bpx-player-toast-cancel, .bili-mini-close-icon').forEach(e => e.click());
        const v = [...document.querySelectorAll('video')].find(v => v.offsetWidth > 100);
        v.currentTime = 0;
      });
      await sleep(600);
      const crop = await page.evaluate(({ keep, pad }) => {
        const rs = keep.map(s => document.querySelector(s)?.getBoundingClientRect()).filter(r => r && r.width > 40 && r.height > 40);
        if (!rs.length) return null;
        const x0 = Math.max(0, Math.min(...rs.map(r => r.left)) - pad[3]), y0 = Math.max(0, Math.min(...rs.map(r => r.top)) - pad[0]);
        const x1 = Math.min(innerWidth, Math.max(...rs.map(r => r.right)) + pad[1]), y1 = Math.min(innerHeight, Math.max(...rs.map(r => r.bottom)) + pad[2]);
        return { x: Math.round(x0), y: Math.round(y0), width: Math.floor(x1 - Math.round(x0)), height: Math.floor(y1 - Math.round(y0)) };
      }, frame);
      const notice = (await page.evaluate(() => document.body.innerText.match(/未经作者授权[，,]?禁止转载/)?.[0])) || c.notice || null;
      // the author as the page names them (the credit's name), when the search had none
      const author = c.author || await page.evaluate(() => ['ytd-reel-video-renderer[is-active] yt-reel-channel-bar-view-model a',
        'ytd-reel-video-renderer[is-active] .ytReelChannelBarViewModelChannelName', '#owner #channel-name a', '.up-name']
        .map(s => document.querySelector(s)?.textContent?.trim()).find(Boolean) || '');
      const name = String(n).padStart(2, '0');
      const file = path.join(dir, 'clips', `${name}.webm`);
      const rec = await page.screencast({ path: file, fps: 30, quality: 16, ...(crop ? { crop } : {}) });
      await sleep(seconds * 1000);
      await rec.stop();
      clips.push({ n, file: path.relative(dir, file), platform: c.platform, kind: c.kind, url: c.url, title: c.title, author,
        notice, recorded: new Date().toISOString(), size: crop ? [crop.width, crop.height] : frame.view });
      console.log(`${name} ${c.platform} ${c.url} ${crop ? `${crop.width}x${crop.height}` : 'whole window'}${notice ? `  [${notice}]` : ''}`);
    } catch (e) {
      console.error(`${n} ${c.url}: ${e.message}, skipped`);
    }
    await page.close();
    await sleep(1500);
  }
  await b.close();
  fs.writeFileSync(path.join(dir, 'clips.json'), JSON.stringify(clips, null, 1));
  console.log(`${clips.length} of ${picks.length} recorded -> ${path.join(dir, 'clips.json')}`);
}

const run = { search, record }[cmd];
if (run) await run();
else console.error('usage: wall.mjs search <query> --out <dir> | record <dir> --pick 1,2,3');
