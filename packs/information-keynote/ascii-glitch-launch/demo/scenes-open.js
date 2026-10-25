// Tidepool, the opening: the year typed and rolled, "In 2026" tracked and broken into cells, an ASCII field, the
// request typed through eight console dresses, the sentence on the studio, the sentence as dashes, the wall of forecast
// cards. Each scene draws on the frame's 2D layer and returns how the frame is finished (kit/glitch.js frame().end).
import { SIZE, GLITCH } from './kit/tokens.js';
import { voice, machine, typed, reel, nudge } from './kit/glitch.js';
import { studio, lens, halo } from './kit/grounds.js';
import { along, track, path, box } from './kit/tracker.js';
import { quadMap, onPlane, focusBelow } from './kit/plane.js';
import { slot } from './kit/montage.js';
import { TYPED, ROLL, BREAK, b } from './timeline.js';

const [W, H] = SIZE;
const clamp = (x, a = 0, z = 1) => Math.max(a, Math.min(z, x));
const lerp = (a, z, u) => a + (z - a) * u;
const ease = u => 1 - (1 - clamp(u)) ** 3;
const inOut = u => (u = clamp(u), u < 0.5 ? 4 * u * u * u : 1 - (-2 * u + 2) ** 3 / 2);
const hash = (n, k = 0) => { const x = Math.sin(n * 127.1 + k * 311.7) * 43758.5453; return x - Math.floor(x); };
const canvas = (w, h) => { const c = document.createElement('canvas'); c.width = w; c.height = h; return c; };
const tp = (k, t) => typed(TYPED[k].text, t, TYPED[k].t0, TYPED[k].cps);

// ---- the year, typed on the studio; its last digit rolls on a reel, the cursor after it
export function year(q, t) {
  studio(q);
  const px = 294, x = 410, base = 644, f = voice(px, 550);
  q.font = f; q.textBaseline = 'alphabetic'; q.fillStyle = GLITCH.ink.dark;
  const head = tp('year', t).slice(0, 6);
  q.fillText(head, x, base);
  if (head.length === 6) {
    const hx = x + q.measureText('In 202').width;
    reel(q, 5 + ease((t - ROLL[0]) / (ROLL[1] - ROLL[0])), hx, base, { step: px * 1.09 });   // a counter: ease-out
    q.fillStyle = GLITCH.ink.dark; q.fillRect(hx + q.measureText('5').width + 8, base - 22, px * 0.25, 22);
  }
  return {};
}

// ---- "In 2026" on a dashed ellipse, each glyph boxed and labelled, creeping right; broken into 16 px cells
export function tracked(q, t, u) {
  q.fillStyle = '#000'; q.fillRect(0, 0, W, H);
  const font = voice(430, 500), rot = [-0.42, -0.3, 0, 0.1, 0.03, 0.12, -0.08];
  const G = along(q, 'In 2026', font, (i, n, ch) => {
    const x = 120 + i * 250 - (i > 2 ? 30 : 0) + u * 110;
    return [x, 560 + Math.sin(i * 0.9 + 0.6 + u * 0.6) * 50 - (i < 2 ? 50 : 0), rot[i] + Math.sin(u * 2.4 + i) * 0.08];
  });
  return {
    over: o => {
      o.save(); o.strokeStyle = 'rgba(255,255,255,0.45)'; o.lineWidth = 2; o.setLineDash([10, 10]);
      o.beginPath(); o.ellipse(975, 560, 900, 420, 0, 0, Math.PI * 2); o.stroke(); o.restore();
      path(o, [[40, 500], ...G.filter(g => g.ch !== ' ').map(g => [g.x, g.y])]);
      const pop = 1 + 0.06 * (1 - nudge(t, BREAK)), Gp = G.map(g => ({ ...g, px: g.px * (t >= BREAK ? pop : 1) }));
      track(o, Gp, { broken: () => t >= BREAK, label: (g, i) => `x: ${Math.round(g.x * 0.55 + 300)}   y: ${Math.round(440 + i * 6 + u * 12)}` });
    },
  };
}

// ---- an ASCII field: a grey console glimpsed in 24 px cells, then black with stray dashes
export function field(q, t, u) {
  if (u < 0.2) {
    q.fillStyle = '#2a2a2a'; q.fillRect(0, 0, W, H * 0.4);
    q.fillStyle = '#9a9a9a'; q.fillRect(W * 0.08, H * 0.06, W * 0.3, H * 0.22);
    q.fillStyle = '#5c5c5c'; q.fillRect(0, H * 0.4, W, H * 0.22);
    q.fillStyle = '#efefef'; q.fillRect(W * 0.32, H * 0.36, W * 0.62, H * 0.26);
    q.fillStyle = '#3a3a3a'; q.fillRect(W * 0.36, H * 0.44, W * 0.34, H * 0.04);
    q.fillStyle = '#878d9c'; q.fillRect(0, H * 0.62, W, H * 0.38);
    return { cells: { mode: 'ascii', cell: GLITCH.cells.field } };
  }
  q.fillStyle = '#000'; q.fillRect(0, 0, W, H);
  for (let i = 0; i < 60; i++) {
    const y = 120 + hash(i, 3) * 840, x = 160 + hash(i, 5) * 1560, w = 30 + hash(i, 7) * 150;
    q.fillStyle = hash(i, 9) > 0.5 ? '#bdbdbd' : '#5a5a5a'; q.fillRect(x, y, w, 4);
  }
  return {};
}

// ---- the request typed through eight console dresses, a dress every five frames: a page in perspective (the
// measured quad), the lens's light, a light card's halo, focus falling off below the request
const LOOKS = [
  { bg: ['#8fa6ff', '#c3b6ff', '#efe2ff'], card: '#fbfbfb', text: '#222', head: 'Bring a coast, a buoy or a harbour to life', headCol: '#5a5f7a', zoom: 1.03, dy: 26, at: [720, 208, 52], lens: [1195, 432, 1227, 761, 0.4, 1.85, 1.14], halo: [1000, 800, 800, 260, 0.8] },
  { bg: ['#050505', '#050505', '#111'], card: '#1b1b1b', text: '#d8d8d8', head: 'What will the sea do?', headCol: '#f2f2f2', zoom: 0.88, dy: -15, at: [1120, 320, 80], dark: true, big: true },
  { bg: ['#1647d6', '#1238b0', '#0b2678'], card: '#1d1e22', text: '#eaeaea', head: 'Tides, swell and wind in one call', headCol: '#cfe0ff', zoom: 0.98, dy: -16, at: [812, 180, 40], dark: true },
  { bg: ['#f2f2f2', '#dedede', '#cfcfcf'], card: '#ffffff', text: '#1d1d1d', head: 'plain words. Get the tide — fast', headCol: '#6a6a6a', zoom: 1.2, dy: 0, at: [440, 180, 62], lens: [998, 550, 1511, 723, 0.52, 3.92, 1.03], halo: [1000, 820, 800, 260, 0.5] },
  { bg: ['#000', '#050505', '#0c0c0c'], card: '#262626', text: '#e6e6e6', head: 'Where every voyage starts', headCol: '#8a8a8a', zoom: 1.05, dy: -9, at: [1500, 60, 50], dark: true, pill: true },
  { bg: ['#86b2da', '#b5d3ee', '#6f9fcf'], card: '#f6f6f6', text: '#1d1d1d', head: 'Ask the sea anything', headCol: '#ffffff', zoom: 1.0, dy: -4, at: [880, 100, 58], headBlur: 9, lens: [1155, 650, 1327, 769, 0.4, 2.35, 1.03], halo: [1000, 820, 800, 260, 0.45] },
  { bg: ['#0b1a4a', '#122a6e', '#08122e'], card: '#1a2240', text: '#e4e8f8', head: 'Forecasts for every harbour', headCol: '#dfe6ff', zoom: 1.05, dy: -23, at: [280, 140, 60], dark: true, pill: true },
  { bg: ['#202020', '#262626', '#161616'], card: '#2a2a2a', text: '#dcdcdc', head: 'Chart the next six hours', headCol: '#9a9a9a', zoom: 0.95, dy: -30, at: [528, 140, 44], dark: true },
];
const PAGE = { cw: 1750, ch: 700, px: 600, py: 700 };
const PAGE_C = canvas(PAGE.cw + 2 * PAGE.px, PAGE.ch + PAGE.py + 60), SHARP = canvas(W, H), SOFT = canvas(W, H);
const QUAD = [[390, 426], [2230, 483], [2138, 1251], [330, 1000]];
export function console_(q, t, u) {
  const k = slot(t, b(4)) % LOOKS.length, L = LOOKS[k];
  const bg = q.createRadialGradient(W * 0.2, H, 50, W * 0.5, H * 0.4, 1500);
  bg.addColorStop(0, L.bg[0]); bg.addColorStop(0.55, L.bg[1]); bg.addColorStop(1, L.bg[2]);
  q.fillStyle = bg; q.fillRect(0, 0, W, H);
  const { cw, ch, px, py } = PAGE, s = L.zoom * (1 + u * 0.02), ox = 450, oy = 590 + (L.dy ?? 0);
  const P = quadMap(QUAD.map(([x, y]) => [ox + (x - ox) * s, oy + (y - 590) * s])), at = (x, y) => P((x - px) / cw, (y - py) / ch);
  const g = PAGE_C.getContext('2d');
  g.clearRect(0, 0, PAGE_C.width, PAGE_C.height);
  const [hx, hy, hxh] = L.at, [u0, v0] = P.inv(hx, hy), [, v1] = P.inv(hx, hy - hxh);
  g.save(); if (L.headBlur) g.filter = `blur(${L.headBlur}px)`;
  g.font = voice(Math.round((v0 - v1) * ch / 0.546), L.big ? 600 : 400); g.fillStyle = L.headCol;
  g.fillText(L.head, px + u0 * cw, py + v0 * ch); g.restore();
  g.fillStyle = L.card; g.beginPath(); g.roundRect(px, py, cw, L.pill ? 270 : ch, L.pill ? 135 : 44); g.fill();
  g.font = voice(80, 500); g.fillStyle = L.text;
  g.fillText((L.pill ? '+   ' : '') + tp('request', t), px + (L.pill ? 44 : 56), py + (L.pill ? 162 : 196));
  if (!L.pill) { g.fillStyle = L.dark ? '#5a5a5a' : '#b8b8b8'; g.font = voice(80, 300); g.fillText('+', px + 56, py + ch - 90); }
  const sq = SHARP.getContext('2d'); sq.clearRect(0, 0, W, H); onPlane(sq, PAGE_C, at);
  focusBelow(q, SHARP, SOFT, { origin: [ox, oy], from: 50 * s, to: 250 * s });
  lens(q, L.lens ?? [1100, 560, 1300, 770, 0.3, 2, 1.02]);
  if (L.halo) halo(q, SOFT, L.halo);
  return { scan: L.dark ? 0.04 : GLITCH.scan.card, post: { vignette: 0.25 } };
}

// ---- the sentence typed on the studio
const SENTENCE = TYPED.sentence.text;
export function sentence(q, t) {
  studio(q);
  q.font = voice(78, 500); q.fillStyle = GLITCH.ink.dark;                 // the line rises into place (a move, no overshoot)
  const done = TYPED.sentence.t0 + TYPED.sentence.text.length / TYPED.sentence.cps + 0.12;
  q.fillText(tp('sentence', t), 110, 567 + (1 - nudge(t, TYPED.sentence.t0, { overshoot: false })) * 24 - nudge(t, done) * 18);
  return { post: { vignette: 0.2 } };
}

// ---- the sentence squashed to a cell's height in the ASCII field (it reads as dashes); a terminal glimpsed through it
export function dashes(q, t, u, dur) {
  studio(q, undefined, { lift: -6 });
  q.save(); q.translate(120, 548); q.scale(1.25, 0.45);
  q.font = voice(64, 900); q.fillStyle = '#000'; q.fillText(SENTENCE, 0, 0); q.restore();
  return { cells: { mode: 'ascii', cell: 14, tap: 'centre' }, over: u > dur * 0.6 ? terminal : null };
}
function terminal(q) {
  q.fillStyle = '#000'; q.fillRect(1270, 680, 650, 400);
  q.strokeStyle = '#ddd'; q.lineWidth = 1.5;
  [[40, 30, 7], [160, 45, 10], [320, 60, 8], [30, 115, 9], [130, 140, 5], [270, 150, 6], [320, 210, 7], [220, 240, 4], [400, 255, 5]]
    .forEach(([x, y, n]) => { for (let k = 0; k < n; k++) q.strokeRect(1270 + x + k * 14, 680 + y, 10, 10); });
}

// ---- the wall of forecast cards: inside a cylinder, the camera dollying in and turning left (fitted on the
// reference: focal 1095, cards 0.416 rad wide and 0.481 apart; 0.9 -> 0.23 radii behind the axis, 0.43 rad, ease-out)
const HARBOURS = ['Kestrel Bay', 'Port Avel', 'Marrow Point', 'Sable Quay', 'Lantern Cove', 'Ostra', 'Halden', 'Brineholm',
  'Gullstone', 'Wrenmouth', 'Skerry', 'Cald Harbour', 'Pellow', 'Dunmere'];
const CARDS = HARBOURS.map((name, i) => {
  const c = canvas(520, 300), g = c.getContext('2d');
  const pal = [['#0f1622', '#e8eef6', '#4fb3ff'], ['#ffffff', '#141414', '#2563eb'], ['#f3efe6', '#1d1d1d', '#0e9f8e'],
    ['#0b0b0b', '#fafafa', '#22c55e'], ['#eaf4fb', '#0d2a3d', '#1d8fd1'], ['#141821', '#e6e9ef', '#f59e0b']][i % 6];
  const [bg, ink, acc] = pal;
  g.fillStyle = bg; g.fillRect(0, 0, 520, 300);
  g.fillStyle = '#1c1c1c'; g.fillRect(0, 0, 520, 14);
  g.fillStyle = '#555'; for (let k = 0; k < 3; k++) { g.beginPath(); g.arc(14 + k * 12, 7, 3, 0, Math.PI * 2); g.fill(); }
  g.fillStyle = ink; g.font = '700 34px Inter'; g.fillText(name, 28, 66);
  g.globalAlpha = 0.6; g.font = '500 20px Inter'; g.fillText(`High ${String(4 + (i * 3) % 9).padStart(2, '0')}:${String((i * 17) % 60).padStart(2, '0')} · ${(1.2 + hash(i, 1) * 2.4).toFixed(1)} m`, 28, 96); g.globalAlpha = 1;
  g.strokeStyle = acc; g.lineWidth = 5; g.beginPath();                       // the tide curve and now
  for (let x = 28; x <= 492; x += 6) g.lineTo(x, 200 + Math.sin(x / 70 + i) * 50);
  g.stroke();
  const nx = 120 + hash(i, 2) * 300; g.fillStyle = acc; g.beginPath(); g.arc(nx, 200 + Math.sin(nx / 70 + i) * 50, 10, 0, Math.PI * 2); g.fill();
  g.globalAlpha = 0.15; g.fillStyle = ink; for (let k = 0; k < 6; k++) g.fillRect(28 + k * 80, 266, 56, 10); g.globalAlpha = 1;
  g.strokeStyle = 'rgba(0,0,0,0.3)'; g.lineWidth = 3; g.strokeRect(1.5, 1.5, 517, 297);
  return c;
});
const WALL = { f: 1095, half: 0.208, step: 0.481, lowOff: -0.188, rows: [[0.252, 0.27], [-0.205, 0.28]] };
const onWall = (th, y, d) => { const z = Math.cos(th) + d; return [W / 2 + WALL.f * Math.sin(th) / z, H / 2 - WALL.f * y / z]; };
function wallCard(q, img, th, yc, h, d) {
  const n = 14, da = 2 * WALL.half / n, sw = img.width / n;
  const ends = [onWall(th - WALL.half, yc + h / 2, d), onWall(th + WALL.half, yc + h / 2, d), onWall(th + WALL.half, yc - h / 2, d), onWall(th - WALL.half, yc - h / 2, d)];
  q.save(); q.shadowColor = 'rgba(0,0,0,0.22)'; q.shadowBlur = 24; q.shadowOffsetY = 8; q.fillStyle = '#888';
  q.beginPath(); ends.forEach(([x, y]) => q.lineTo(x, y)); q.fill(); q.restore();
  for (let k = 0; k < n; k++) {
    const ta = th - WALL.half + k * da, tb = ta + da;
    const p = onWall(ta, yc + h / 2, d), r = onWall(tb, yc + h / 2, d), bb = onWall(ta, yc - h / 2, d);
    const w = Math.min(sw + 0.8, img.width - k * sw);
    q.setTransform((r[0] - p[0]) / sw, (r[1] - p[1]) / sw, (bb[0] - p[0]) / img.height, (bb[1] - p[1]) / img.height, p[0], p[1]);
    q.drawImage(img, k * sw, 0, w, img.height, 0, 0, w, img.height);
  }
  q.setTransform(1, 0, 0, 1, 0, 0);
  return ends;
}
export function wall(q, t, u, dur) {
  studio(q, undefined, { lift: 2 });
  const e = ease(u / dur), d = lerp(0.905, 0.227, e), phi = lerp(-0.01, -0.438, e);
  let tracked = null;
  WALL.rows.forEach(([yc, h], row) => {
    for (let i = -4; i <= 6; i++) {
      const th = phi + i * WALL.step + (row ? WALL.lowOff : 0);
      if (Math.cos(Math.abs(th) + WALL.half) + d < 0.2) continue;
      const ends = wallCard(q, CARDS[(i + 8 + row * 7) % CARDS.length], th, yc, h, d);
      if (row === 0 && i === 2) tracked = ends;
    }
  });
  const s = lerp(0.978, 1.204, e);
  q.save(); q.translate(1109, 540); q.scale(s, s);
  q.font = voice(82, 500); q.fillStyle = '#151515'; q.fillText(SENTENCE, 54 - 1109, 30); q.restore();
  return {
    over: tracked && (o => {
      const xs = tracked.map(p => p[0]), ys = tracked.map(p => p[1]);
      const x0 = Math.min(...xs) - 6, y0 = Math.min(...ys) - 6, x1 = Math.max(...xs) + 6, y1 = Math.max(...ys) + 6;
      box(o, x0, y0, x1, y1, {});
      path(o, [[x1 - 60, y1], [x0 - 200, 700], [x0 - 700, 696]], { color: 'rgba(255,255,255,0.85)', dash: [7, 7], arrows: false });
    }),
    post: { vignette: 0.2 },
  };
}
