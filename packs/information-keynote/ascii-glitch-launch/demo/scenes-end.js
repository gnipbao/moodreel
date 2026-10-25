// Tidepool, the answer: a tunnel of characters ("it starts with"), "Good" and a neon tube, "data" and a beam of cells,
// the ring round "and every good forecast" (an inverted frame, then blue rushing out), "lives on" by a dim lighthouse
// through ring cells, the name typed beside posts cutting fast, the mark on black, then on white.
import { SIZE, GLITCH } from './kit/tokens.js';
import { voice, machine, typed, nudge } from './kit/glitch.js';
import { dark, glyphGround } from './kit/grounds.js';
import { box } from './kit/tracker.js';
import { tunnel as charTunnel, ring as streakRing, neon, beam, ringGround } from './kit/fields.js';
import { slot, during } from './kit/montage.js';
import { TYPED, FLASHES, GLITCHES, b, shot } from './timeline.js';

const [W, H] = SIZE;
const clamp = (x, a = 0, z = 1) => Math.max(a, Math.min(z, x));
const lerp = (a, z, u) => a + (z - a) * u;
const smooth = u => { u = clamp(u); return u * u * (3 - 2 * u); };
const hash = (n, k = 0) => { const x = Math.sin(n * 127.1 + k * 311.7) * 43758.5453; return x - Math.floor(x); };
const canvas = (w, h) => { const c = document.createElement('canvas'); c.width = w; c.height = h; return c; };
const centred = (q, text, x, y) => { q.textAlign = 'center'; q.fillText(text, x, y); q.textAlign = 'left'; };
const tp = (k, t) => typed(TYPED[k].text, t, TYPED[k].t0, TYPED[k].cps);

// ---- characters streaming from a vanishing point, red, then every colour; "it starts with", tracked
export function tunnel(q, t, u, dur) {
  q.fillStyle = '#050505'; q.fillRect(0, 0, W, H);
  if (u < dur * 0.55) charTunnel(q, u, { hue: 352 });
  else for (let i = 0; i < 16000; i++) {                            // then streaks rushing out, every colour
    const a = hash(i, 1) * Math.PI * 2, z = ((hash(i, 2) * 10 - u * 9) % 10 + 10) % 10 + 0.25;
    const x = W / 2 + Math.cos(a) * 1150 / z, y = H * 0.52 + Math.sin(a) * 720 / z, l = 14 / z;
    if (x < -40 || x > W + 40 || y < -40 || y > H + 40) continue;
    q.strokeStyle = `hsla(${(a / Math.PI * 180 + 360 + hash(i, 5) * 40) % 360}, 85%, 58%, ${clamp(1.4 - z / 7)})`;
    q.lineWidth = Math.min(5, 7 / z);
    q.beginPath(); q.moveTo(x, y); q.lineTo(x + Math.cos(a) * l, y + Math.sin(a) * l); q.stroke();
  }
  q.save(); q.filter = 'blur(30px)'; q.fillStyle = 'rgba(0,0,0,0.8)';
  q.beginPath(); q.ellipse(W / 2, H * 0.55, 520, 200, 0, 0, Math.PI * 2); q.fill(); q.restore();
  q.save(); q.translate(W / 2, 628 + (1 - nudge(t, shot('tunnel').t0, { overshoot: false })) * 50); q.rotate(-0.05);   // the words rise in
  q.font = voice(150, 800); q.fillStyle = '#fff'; centred(q, 'it starts with', 0, 0); q.restore();
  return {
    over: o => {
      o.font = machine(22); o.fillStyle = '#ddd';
      ['x: 702  y: 507', 'x: 1188  y: 507'].forEach((s, i) => o.fillText(s, 600 + i * 520, 448));
      o.setLineDash([8, 8]); o.strokeStyle = 'rgba(255,255,255,0.5)'; o.lineWidth = 2;
      o.beginPath(); o.ellipse(W / 2, 580, 600, 130, 0, Math.PI * 1.05, Math.PI * 1.95); o.stroke(); o.setLineDash([]);
    },
    post: { bloom: 0.4, bloomThreshold: 0.6, vignette: 0.3 },
  };
}

// ---- "Good" and a pink neon tube on the dark ground
export function good(q, t) {
  dark(q, { dither: 0.11 });
  q.fillStyle = 'rgba(0,0,0,0.4)'; q.fillRect(1420, 640, 60, 440);
  neon(q, 1424, 120, 52, 520);
  q.font = voice(116, 600); q.fillStyle = '#fff'; q.fillText('Good', 560 - (1 - nudge(t, shot('good').t0, { overshoot: false })) * 60, 600 - nudge(t, shot('good').t0 + 0.35, { overshoot: false }) * 14);   // slides in, then lifts
  return { post: { bloom: 0.8, bloomThreshold: 0.75, vignette: 0.35 } };
}

// ---- "data" and a beam of light in 16 px cells, on the ring ground; the beam's top steps out a cell
const RINGS = (() => { const c = canvas(W, H); ringGround(c.getContext('2d')); return c; })();
export function data(q, t, u) {
  q.drawImage(RINGS, 0, 0);
  const k = nudge(t, shot('data').t0 + 0.4), top = lerp(568, 552, k);            // the beam steps out a cell, settling
  beam(q, y => 848 - 1.16 * (y - 600) - 12 * k * clamp((1000 - y) / 300), y => 911 - 0.36 * (y - 600) + 8 * k * clamp((1000 - y) / 300), top, { x1: 1040 });
  q.font = voice(126, 600); q.fillStyle = '#fff'; q.fillText('data', 1240 + (1 - nudge(t, shot('data').t0, { overshoot: false })) * 80, 583 - nudge(t, shot('data').t0 + 0.4) * 16);   // slides in; lifts, settling
  return {};
}

// ---- the ring: a field of streaks turning about a pivot above its middle, warm left to violet right; one inverted
// frame; then a blue ring with a hole that rushes out and goes
const hueAcross = x => { const s = clamp((x - 150) / 1650); return (s < 0.22 ? lerp(22, -24, s / 0.22) : lerp(-24, -82, (s - 0.22) / 0.78)) + 360; };
export function ring(q, t, u) {
  const flash = during(t, FLASHES.slice(2)), blue = t >= FLASHES[2][0] + FLASHES[2][1] / 60;
  q.fillStyle = flash ? '#f2f2f2' : '#000'; q.fillRect(0, 0, W, H);
  if (u < 0.05) return {};
  const grow = 1 + 0.08 * u, line = 'and every good forecast', pop = 0.94 + 0.06 * nudge(t, shot('ring').t0 + 0.05, { overshoot: false });
  q.font = voice(Math.round(90 * pop), 500);
  if (flash) {
    streakRing(q, t, { count: 6000, ink: 'rgba(24,18,26,0.55)', window: [962, 650, 855 * grow, 420 * grow], reach: 640 * grow });
    q.fillStyle = '#111'; centred(q, line, 960, 572);
    return {};
  }
  q.save(); q.globalCompositeOperation = 'lighter';
  if (!blue) streakRing(q, t, { count: 6000, hue: hueAcross, window: [962, 650, 855 * grow, 420 * grow], reach: 640 * grow });
  else {
    const since = t - (FLASHES[2][0] + FLASHES[2][1] / 60), k = 1 + 4 * Math.max(0, since - 0.15) ** 2;
    const fade = clamp(1 - (Math.max(0, since - 0.2) / 0.45) ** 2);   // gone by the cut, not before it
    if (fade > 0) {
      q.save(); q.translate(958, 609); q.scale(k, k); q.translate(-958, -609); q.globalAlpha = fade;
      streakRing(q, t, { count: 13000, pivot: [958, 523], aspect: 1.75, rate: 1.06, reach: 560, window: [958, 609, 776, 445],
        hole: [950, 560, 370, 170], hue: () => 208, light: [20, 54], width: [2, 5], length: [8, 52] });
      q.restore();
    }
  }
  q.restore();
  if (!blue) { q.save(); q.filter = 'blur(8px)'; q.globalAlpha = 0.7; q.fillStyle = '#fff'; centred(q, line, 960, 572); q.restore(); }
  q.fillStyle = '#fff'; centred(q, line, 960, 572);
  return { post: blue ? {} : { bloom: 0.25, bloomThreshold: 0.65 } };
}

// ---- "lives on": a dim lighthouse on the left through 12 px ring cells; its lamp the one white blot
const LIGHTHOUSE = (() => {
  const c = canvas(W, H), g = c.getContext('2d');
  g.fillStyle = '#040506'; g.fillRect(0, 0, W, H);
  g.fillStyle = 'rgba(70,90,96,0.45)'; g.beginPath();                    // the tower, tapering, banded
  g.moveTo(360, 1080); g.lineTo(420, 560); g.lineTo(560, 560); g.lineTo(620, 1080); g.fill();
  g.fillStyle = 'rgba(120,140,146,0.35)'; for (let k = 0; k < 4; k++) g.fillRect(380 + k * 8, 640 + k * 110, 220 - k * 16, 40);
  g.fillStyle = 'rgba(90,110,116,0.5)'; g.fillRect(400, 530, 180, 30);    // the gallery and the lantern room
  g.fillStyle = 'rgba(60,76,82,0.5)'; g.fillRect(430, 420, 120, 110);
  g.fillStyle = 'rgba(100,120,126,0.5)'; g.beginPath(); g.moveTo(420, 420); g.lineTo(490, 360); g.lineTo(560, 420); g.fill();
  g.save(); g.filter = 'blur(30px)'; g.fillStyle = 'rgba(140,170,176,0.25)';   // its beam into the haze
  g.beginPath(); g.moveTo(490, 470); g.lineTo(1100, 300); g.lineTo(1100, 560); g.fill(); g.restore();
  g.fillStyle = 'rgba(30,40,44,0.6)'; g.fillRect(0, 980, 900, 100);       // the rocks
  return c;
})();
export function liveson(q, t) {
  q.fillStyle = '#000'; q.fillRect(0, 0, W, H); q.globalAlpha = 0.85; q.drawImage(LIGHTHOUSE, 0, 0); q.globalAlpha = 1;
  return {
    cells: { mode: 'ascii', ramp: 'rings', cell: GLITCH.cells.rings, thr: 0.2, ring: 0.028 },
    over: o => {
      o.fillStyle = '#f2f2f2';                                         // the lamp, in cells
      for (let y = 444; y < 516; y += 12) for (let x = 456; x < 528; x += 12) if (Math.hypot(x + 6 - 490, y + 6 - 476) < 34) o.fillRect(x, y, 12, 12);
      o.font = voice(96, 600); o.fillStyle = '#fff'; o.fillText(tp('liveson', t), 1001, 573 + (1 - nudge(t, TYPED.liveson.t0, { overshoot: false })) * 30);
    },
    post: { vignette: 0.2 },
  };
}

// ---- the name typed on the left; posts (invented: handles, text, a forecast shot) cutting on the right
const POSTS = (() => {
  const shots = [
    g => { g.fillStyle = '#eaf4fb'; g.fillRect(0, 0, 700, 380); g.strokeStyle = '#1d8fd1'; g.lineWidth = 8; g.beginPath(); for (let x = 20; x <= 680; x += 8) g.lineTo(x, 200 + Math.sin(x / 80) * 90); g.stroke(); },
    g => { g.fillStyle = '#0f1622'; g.fillRect(0, 0, 700, 380); g.fillStyle = '#4fb3ff'; for (let k = 0; k < 12; k++) g.fillRect(40 + k * 54, 300 - 40 - hash(k, 4) * 180, 36, 40 + hash(k, 4) * 180); },
    g => { g.fillStyle = '#fafafa'; g.fillRect(0, 0, 700, 380); g.fillStyle = '#111'; g.font = '700 46px Inter'; g.fillText('High 06:12 · 2.4 m', 60, 120); g.fillStyle = '#0e9f8e'; g.fillRect(60, 170, 420, 24); g.fillStyle = '#ccc'; g.fillRect(60, 220, 300, 24); },
    g => { g.fillStyle = '#1a4ed8'; g.fillRect(0, 0, 700, 380); g.strokeStyle = '#fff'; g.lineWidth = 14; for (let k = 0; k < 4; k++) { g.beginPath(); for (let x = 0; x <= 700; x += 10) g.lineTo(x, 90 + k * 70 + Math.sin(x / 40 + k) * 16); g.stroke(); } },
    g => { g.fillStyle = '#fde68a'; g.fillRect(0, 0, 700, 380); g.fillStyle = '#92400e'; g.font = '700 52px Inter'; g.fillText('Sailed at 05:40', 70, 210); },
    g => { g.fillStyle = '#111'; g.fillRect(0, 0, 700, 380); g.strokeStyle = '#5ad2a0'; g.lineWidth = 3; for (let r = 40; r < 260; r += 50) { g.beginPath(); g.arc(350, 190, r, 0, Math.PI * 2); g.stroke(); } },
  ];
  return shots.map((shot, i) => {
    const c = canvas(860, 760), g = c.getContext('2d');
    g.fillStyle = '#0c0c0c'; g.fillRect(0, 0, 860, 760);
    g.fillStyle = `hsl(${180 + hash(i, 1) * 80}, 45%, 50%)`; g.beginPath(); g.arc(50, 50, 22, 0, Math.PI * 2); g.fill();
    g.fillStyle = '#eee'; g.font = '700 24px Inter'; g.fillText(['Tidepool', 'Ines Varga', 'Theo', 'Tidepool', 'Ruth K.', 'Ari'][i], 84, 46);
    g.fillStyle = '#777'; g.font = '400 20px Inter'; g.fillText('@handle · 2h', 84, 72);
    g.fillStyle = '#cfcfcf'; for (let k = 0; k < 4; k++) g.fillRect(30, 110 + k * 32, 560 + hash(i * 7 + k, 2) * 240, 14);
    const s = canvas(700, 380); shot(s.getContext('2d'));
    g.save(); g.beginPath(); g.roundRect(80, 270, 700, 380, 18); g.clip(); g.drawImage(s, 80, 270); g.restore();
    g.fillStyle = '#444'; for (let k = 0; k < 4; k++) g.fillRect(40 + k * 190, 700, 60, 10);
    return c;
  });
})();
const POST_SLOTS = [0, -1, 2, 1, 5, -1, 3, 4, 2, 0, 5, 3, 1, 4];
export function name(q, t) {
  const bg = q.createLinearGradient(0, 0, W, H); bg.addColorStop(0, '#1c1c1c'); bg.addColorStop(1, '#0a0a0a');
  q.fillStyle = bg; q.fillRect(0, 0, W, H);
  dark(q, { middle: 'rgba(0,0,0,0)', edge: 'rgba(0,0,0,0)', dither: 0.045 });
  q.font = voice(104, 600); q.fillStyle = '#fff'; q.fillText(tp('name', t), 110, 585 + (1 - nudge(t, TYPED.name.t0, { overshoot: false })) * 40 - nudge(t, b(24.6)) * 30);
  const n = Math.floor(slot(t, b(23.75), 7)), p = t < b(23.75) ? null : POST_SLOTS[n % POST_SLOTS.length];
  if (p !== null) {
    const slide = (1 - nudge(t, b(23.75) + n * 7 / 60, { dur: 0.1, overshoot: false })) * 60;   // each post slides in
    q.save(); q.translate(1420 + slide, 540); q.scale(1.12, 1.12); q.shadowColor = 'rgba(0,0,0,0.7)'; q.shadowBlur = 40;
    if (p < 0) { q.fillStyle = '#0c0c0c'; q.fillRect(-430, -380, 860, 300); q.fillStyle = '#cfcfcf'; for (let k = 0; k < 3; k++) q.fillRect(-400, -320 + k * 34, 600, 14); }
    else q.drawImage(POSTS[p], -430, -380);
    q.restore();
  }
  return { post: { vignette: 0.3 } };
}

// ---- the mark: a crest of a wave, its stroke round. It turns toward upright and grows a little through both closing
// scenes (the reference's measured turn: 6 degrees by a smoothstep over 1.65 s, 316 -> 330 px)
function mark(q, t, color, cy, s = 1, t0 = b(27.4)) {
  const ang = (-24 + 6 * smooth((t - t0) / 1.65)) * Math.PI / 180, dt = Math.max(0, t - b(26.6)), L = (316 + 6.5 * dt) * s;
  q.save(); q.translate(956, cy); q.rotate(ang);
  q.strokeStyle = color; q.lineWidth = (26.5 + 1.7 * dt) * s; q.lineCap = 'round'; q.beginPath();
  for (let x = -L / 2; x <= L / 2 + 0.1; x += L / 40) q.lineTo(x, -Math.sin((x / L + 0.5) * Math.PI * 2) * L * 0.16);
  q.stroke(); q.restore();
}
const FIELD = (() => {
  const c = canvas(W, H), g = c.getContext('2d');
  g.fillStyle = '#808080'; g.fillRect(0, 0, W, H); g.filter = 'blur(6px)';
  for (let i = 0; i < 2500; i++) { g.fillStyle = hash(i, 1) > 0.5 ? '#b0b0b0' : '#505050'; g.beginPath(); g.arc(hash(i, 2) * W, hash(i, 3) * H, 8 + hash(i, 4) * 24, 0, Math.PI * 2); g.fill(); }
  return c;
})();
export function markScene(q, t, u) {
  q.fillStyle = '#000'; q.fillRect(0, 0, W, H);
  if (u < 0.13) {
    for (let i = 0; i < 9; i++) { q.fillStyle = '#5a5a5a'; q.fillRect(300 + hash(i, 1) * 1300, 150 + hash(i, 2) * 800, 40 + hash(i, 3) * 90, 3); }
    return {};
  }
  if (during(t, GLITCHES.slice(5))) {                               // six frames: a dim field of glyphs, a black disc, the mark
    q.drawImage(FIELD, 0, 0);
    return { cells: { mode: 'lines', cell: 12, thr: 0.3, ink: [0.035, 0.035, 0.035], paper: [0, 0, 0] }, over: o => {
      o.fillStyle = '#000'; o.beginPath(); o.arc(970, 540, 510, 0, Math.PI * 2); o.fill(); mark(o, t, '#fff', 543, 1.13);
    } };
  }
  const glitch = u < 0.3;
  mark(q, t, glitch ? '#bdbdbd' : '#fff', 543, glitch ? 1.13 : 1);
  if (glitch) for (let i = 0; i < 60; i++) { q.fillStyle = `rgba(255,255,255,${hash(i, Math.floor(t * 60)) * 0.4})`; q.fillRect(860 + hash(i, 2) * 200, 450 + hash(i, 3) * 200, 3, 3); }
  return { over: u < 0.9 ? o => box(o, 760, 430, 1150, 650, { color: GLITCH.track.red, ink: '#ccc', labelPx: 18 }) : null };
}

// ---- the white end card: a clean disc, line glyphs toward the corners, the mark turning; then black
const END = glyphGround({ light: true });
export function end(q, t) {
  q.drawImage(END, 0, 0);
  mark(q, t, '#111', 547);
  return { post: { exposure: 1.23 } };
}
export function black(q) { q.fillStyle = '#000'; q.fillRect(0, 0, W, H); return {}; }
