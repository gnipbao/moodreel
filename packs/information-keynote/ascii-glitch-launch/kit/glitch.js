// ASCII Glitch Launch: the style's own core. Its two voices (Inter for the words, JetBrains Mono for the machine),
// typing and the number reel, and the frame: a 2D layer the scene draws on, sent through the cell pass (kit/cells.js)
// or straight, a layer over it for what the cells must not touch (the tracker, type over a glyph screen), the scan
// lines, then the film post with a grain that holds still (the reference's never moves).
//
//   import { faces, voice, machine, typed, frame } from './kit/glitch.js';
//   const F = frame();
//   stage({ width: 1920, height: 1080, duration, prepare: faces, draw: (g, t) => {
//     const q = F.begin('#000');                    // the cleared layer, 1920 x 1080
//     ...draw the scene on q...
//     F.end(g, t, { cells: { mode: 'ascii', cell: 16 }, over: o => { ... }, scan: GLITCH.scan.dark });
//   } });
import { gpu } from './gl.js';
import { cells } from './cells.js';
import { SIZE, TYPE, GLITCH } from './tokens.js';
import { bezier } from './eases.js';

const FONT = name => new URL(`./fonts/${name}`, import.meta.url).href;

// the two voices (DECISIONS.md 3, SIL OFL): load once, before the first frame (stage({ prepare: faces }))
export async function faces() {
  const list = [['Inter', 'Inter.woff2', { weight: '100 900' }], ['JetBrains Mono', 'JetBrainsMono.ttf', { weight: '100 800' }]];
  await Promise.all(list.map(([family, file, desc]) =>
    new FontFace(family, `url(${JSON.stringify(FONT(file))})`, desc).load().then(f => document.fonts.add(f))));
}

// font strings. Weights are read off the reference line by line (`moodreel probe --region`): phrases Medium (500),
// scene words Semibold (600), a heavy word now and then (800); the machine Regular, or Light (250) for dot-matrix words
export const voice = (px, weight = 500) => `${weight} ${px}px ${TYPE.display}`;
export const machine = (px, weight = 400) => `${weight} ${px}px "${TYPE.text}"`;
// a tier's size in px at this height: hero (20 % of the frame), line (15 %), phrase (8.9 %), label (2 %)
export const size = (tier, H = SIZE[1]) => Math.round(TYPE[tier] * H);

// text typed in at `cps` characters a second from t0 (a prompt at 36, a line at up to 150)
export const typed = (text, t, t0, cps = 36) => text.slice(0, Math.max(0, Math.min(text.length, Math.floor((t - t0) * cps) + 1)));

// the style's move (STYLE.md §5): 0.17 s, ease-out, half of them overshooting about 4 % on the measured curve
// bezier(0.433, 1.198, 1.0, 0.927). Progress from `at`, 0 -> 1 (past 1 a moment when it overshoots)
const SETTLE = bezier(0.433, 1.198, 1.0, 0.927);
export function nudge(t, at, { dur = 0.171, overshoot = true } = {}) {
  const u = Math.max(0, Math.min(1, (t - at) / dur));
  return overshoot ? SETTLE(u) : 1 - (1 - u) ** 3;
}

// a digit rolling on a reel: `value` runs on (4.6 shows 4 going and 5 coming); the digit at the value dark, its
// neighbours grey above and below, one line apart
export function reel(g, value, x, y, { step, ink = GLITCH.ink.dark, grey = '#a5a5a5' } = {}) {
  const lh = step ?? parseFloat(g.font.match(/(\d+(\.\d+)?)px/)[1]) * 1.09;
  for (let d = Math.floor(value) - 2; d <= Math.ceil(value) + 2; d++) {
    const off = (d - value) * lh, k = Math.max(0, 1 - Math.abs(d - value) * 0.6);
    if (Math.abs(off) > lh * 1.6) continue;
    g.fillStyle = mixHex(grey, ink, k);
    g.fillText(String(((d % 10) + 10) % 10), x, y + off);
  }
}

// rows 2 and 3 of every 4 darkened by `amount`: the scan lines over every scene (GLITCH.scan by ground)
export function scanlines(g, amount, W = SIZE[0], H = SIZE[1]) {
  if (!amount) return;
  g.save(); g.fillStyle = `rgba(0,0,0,${amount})`;
  for (let y = 2; y < H; y += 4) g.fillRect(0, y, W, 2);
  g.restore();
}

// the frame: begin() gives the scene's 2D layer; end() finishes it onto the stage's context
export function frame() {
  const [W, H] = SIZE, G = gpu(W, H), layer = G.layer(W, H), over = G.layer(W, H), hdr = G.rt(), C = cells(G);
  return {
    G, W, H,
    begin(background = '#000') {
      layer.clear(background);
      layer.ctx.setTransform(1, 0, 0, 1, 0, 0);
      return layer.ctx;
    },
    // cells: options for the cell pass (mode ascii | dots | pixelate | hatch | lines, cell, ...), or none
    // over: o => { ... } drawn after the cells; scan: the scan lines' strength; post: the film post's settings
    end(g, t, { cells: pass = null, over: drawOver = null, scan = 0, post = {} } = {}) {
      const tex = layer.upload();
      if (pass) C.draw(tex, hdr, { t, ...pass });
      else G.comp(tex, hdr, { mode: 'replace' });
      if (drawOver || scan) {
        over.clear(); over.ctx.setTransform(1, 0, 0, 1, 0, 0);
        if (drawOver) drawOver(over.ctx, t);
        scanlines(over.ctx, scan, W, H);
        G.comp(over.upload(), hdr);
      }
      G.post(hdr.texture, { bloom: 0, halation: 0, ca: 0, vignette: 0, grain: GLITCH.grain, ...post, time: 0 });
      G.show(g, 0, 0, W, H);
    },
  };
}

function mixHex(a, b, k) {
  const p = h => [1, 3, 5].map(i => parseInt(h.slice(i, i + 2), 16)), A = p(a), B = p(b);
  return `rgb(${A.map((v, i) => Math.round(v + (B[i] - v) * k)).join(',')})`;
}
