// Real material, as `moodreel media add` put it in media/ (manifest.json: kind, size, frames, rate, source, licence).
// Load it before the stage, so the page is ready only when every frame is:
//
//   import { load } from './kit/media.js';
//   const M = await load();                         // or load(['parade', 'map'])
//   stage({ ..., draw: (g, t) => { g.drawImage(M.frame('parade', t, { from: 2 }), 0, 0, 1920, 1080); } });
//
// Footage is one image per film frame, so a frame of the film never waits on a video seek: frame(name, t) is the
// image at clip time (t - from) * rate, held on its first frame before and its last after (or wrapped, with loop).

const image = src => new Promise((ok, fail) => {
  const im = new Image();
  im.onload = () => ok(im);
  im.onerror = () => fail(new Error(`media ${src} did not load`));
  im.src = src;
});

const csv = text => {
  const [head, ...rows] = text.trim().split(/\r?\n/).map(l => l.split(text.includes('\t') ? '\t' : ','));
  return rows.map(r => Object.fromEntries(head.map((h, i) => [h.trim(), isNaN(+r[i]) || r[i] === '' ? (r[i] ?? '').trim() : +r[i]])));
};

export async function load(names = null) {
  const manifest = await (await fetch('media/manifest.json')).json();
  const want = names || Object.keys(manifest);
  const got = {};
  await Promise.all(want.map(async name => {
    const e = manifest[name];
    if (!e) throw new Error(`no media ${name} (moodreel media add)`);
    if (e.kind === 'footage') {
      const pad = n => String(n).padStart(5, '0');
      got[name] = await Promise.all(Array.from({ length: e.frames }, (_, i) => image(`${e.path}${pad(i + 1)}.jpg`)));
    } else if (e.kind === 'still') {
      got[name] = await image(e.path);
    } else {
      const text = await (await fetch(e.path)).text();
      got[name] = e.format === 'csv' || e.format === 'tsv' ? csv(text) : e.format === 'txt' ? text : JSON.parse(text);
    }
  }));
  const entry = name => {
    if (!(name in got)) throw new Error(`media ${name} was not loaded`);
    return manifest[name];
  };
  return {
    manifest,
    info: entry,
    frame(name, t, { from = 0, rate = 1, loop = false } = {}) {
      const e = entry(name), frames = got[name];
      let i = Math.floor((t - from) * rate * e.fps + 1e-6);
      i = loop ? ((i % frames.length) + frames.length) % frames.length : Math.max(0, Math.min(frames.length - 1, i));
      return frames[i];
    },
    still: name => (entry(name), got[name]),
    data: name => (entry(name), got[name]),
    // the credit line the film owes for a piece (for an on-screen credit card)
    credit: name => `${entry(name).source} — ${entry(name).license}`,
  };
}
