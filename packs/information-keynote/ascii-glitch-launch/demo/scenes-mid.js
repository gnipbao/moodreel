// Tidepool, the turn: "BUT" pulled back from hatching into dot cells, a mosaic, the radar and "Most still guess.",
// "guess" as light dot-matrix under the tracker with two inverted flashes, the harbour badges montage.
import { SIZE, GLITCH } from './kit/tokens.js';
import { voice, machine, typed, nudge } from './kit/glitch.js';
import { path } from './kit/tracker.js';
import { slot, during } from './kit/montage.js';
import { TYPED, FLASHES, b } from './timeline.js';

const [W, H] = SIZE;
const clamp = (x, a = 0, z = 1) => Math.max(a, Math.min(z, x));
const lerp = (a, z, u) => a + (z - a) * u;
const ease = u => 1 - (1 - clamp(u)) ** 3;
const hash = (n, k = 0) => { const x = Math.sin(n * 127.1 + k * 311.7) * 43758.5453; return x - Math.floor(x); };
const tp = (k, t) => typed(TYPED[k].text, t, TYPED[k].t0, TYPED[k].cps);

// ---- "BUT": a hatched close-up of the U pulls back to the word, then the word as dot cells
export function but(q, t, u) {
  q.fillStyle = '#000'; q.fillRect(0, 0, W, H);
  const k = ease((u - 0.02) / 0.26), s = lerp(3.4, 1, k);
  q.save(); q.translate(W / 2 + lerp(-260, 0, k), H * 0.52); q.scale(s, s);
  q.font = voice(840, 700); q.textAlign = 'center'; q.textBaseline = 'middle'; q.fillStyle = '#fff'; q.fillText('BUT', 0, 0);
  q.restore(); q.textAlign = 'left'; q.textBaseline = 'alphabetic';
  if (u < 0.23) return { cells: { mode: 'hatch', cell: 30, thr: 0.5, ink: [0.85, 0.85, 0.85], paper: [0, 0, 0] } };
  return { cells: { mode: 'dots', cell: 30, thr: 0.5, gap: 0.08, flick: 0.12, ink: [0.8, 0.8, 0.8], paper: [0, 0, 0] } };
}

// ---- the radar: rings, a sweep, boats lit as it passes them, a coast; the camera closes in
const BOATS = Array.from({ length: 16 }, (_, i) => [hash(i, 1) * Math.PI * 2, 150 + hash(i, 2) * 650, 4 + hash(i, 3) * 6]);
function radar(q, t, zoom, light = 1) {
  q.fillStyle = '#03100d'; q.fillRect(0, 0, W, H);
  q.save(); q.translate(W * 0.52, H * 0.5); q.scale(zoom, zoom);
  q.fillStyle = `rgba(20,60,44,${0.9 * light})`; q.beginPath();                  // the coast
  for (let a = -0.4; a <= 1.3; a += 0.05) q.lineTo(Math.cos(a) * (700 + Math.sin(a * 9) * 60), Math.sin(a) * (700 + Math.sin(a * 9) * 60) - 80);
  q.lineTo(1400, 900); q.lineTo(1400, -400); q.closePath(); q.fill();
  q.strokeStyle = `rgba(90,210,160,${0.28 * light})`; q.lineWidth = 2;
  for (let r = 130; r < 1000; r += 130) { q.beginPath(); q.arc(0, 0, r, 0, Math.PI * 2); q.stroke(); }
  q.beginPath(); q.moveTo(-1000, 0); q.lineTo(1000, 0); q.moveTo(0, -1000); q.lineTo(0, 1000); q.stroke();
  const a = t * 2.4, sweep = q.createConicGradient(a - 1.0, 0, 0);
  sweep.addColorStop(0, 'rgba(90,230,170,0)'); sweep.addColorStop(1.0 / (Math.PI * 2), `rgba(110,240,180,${0.55 * light})`);
  sweep.addColorStop(1.0 / (Math.PI * 2) + 0.001, 'rgba(90,230,170,0)'); sweep.addColorStop(1, 'rgba(90,230,170,0)');
  q.fillStyle = sweep; q.beginPath(); q.arc(0, 0, 1000, 0, Math.PI * 2); q.fill();
  BOATS.forEach(([ang, r, size]) => {
    const since = ((a - ang) % (Math.PI * 2) + Math.PI * 2) % (Math.PI * 2), glow = Math.exp(-since * 0.9) * light;
    q.fillStyle = `rgba(160,255,200,${0.2 + 0.8 * glow})`;
    q.beginPath(); q.arc(Math.cos(ang) * r, Math.sin(ang) * r, size * (1 + glow), 0, Math.PI * 2); q.fill();
  });
  q.restore();
}
export function radarScene(q, t, u) {
  const close = u < 0.1;
  radar(q, t, close ? 0.85 : lerp(1.1, 1.55, ease((u - 0.1) / 0.6)));
  q.font = voice(78, 600); q.fillStyle = '#fff'; q.textAlign = 'center';
  const done = TYPED.radar.t0 + TYPED.radar.text.length / TYPED.radar.cps + 0.05;      // in plain, then settles up
  q.fillText(tp('radar', t), W / 2, H * 0.52 + (1 - nudge(t, TYPED.radar.t0, { overshoot: false })) * 30 - nudge(t, done) * 20); q.textAlign = 'left';
  if (u < 0.15) {                                                   // a corner bracket, glitching in
    q.fillStyle = '#fff'; q.fillRect(1010, 470, 8, 90); q.fillRect(1010, 552, 110, 8);
    q.fillStyle = GLITCH.glow.pink; q.fillRect(990, 470, 26, 26);
  }
  if (close) return { cells: { mode: 'ascii', cell: 18, mix: 0.2 } };
  return { post: { vignette: 0.3 } };
}

// ---- a mosaic: dark coarse blocks for six frames, then the radar bright in fine blocks
export function mosaic(q, t, u) {
  radar(q, t, 1.4, u < 0.1 ? 0.45 : 1.3);
  q.font = voice(78, 600); q.fillStyle = '#fff'; q.fillText('Most', 760, 590);
  return { cells: { mode: 'pixelate', cell: u < 0.1 ? 60 : 20 }, over: u < 0.1 ? null : bars };
}
function bars(q) {
  [[0, 300, 260, 60, '#e2338f'], [300, 640, 420, 40, '#2a2a2a'], [1400, 200, 520, 50, '#5ad2a0']].forEach(([x, y, w, h, c]) => {
    q.fillStyle = c; q.fillRect(x, y, w, h);
  });
}

// ---- "guess": for six frames the radar behind as line glyphs, the word plain; then the word in a light mono set wide,
// as dot cells, each glyph boxed and labelled, a dashed path; inverted for two flashes
const GX = 170, GSTEP = 330, GBASE = 760;
export function guess(q, t, u) {
  const white = during(t, FLASHES.slice(0, 2));
  if (u < 0.1) {
    radar(q, t, 1.55, 3.2);                                           // bright enough to read through the screen
    return { cells: { mode: 'lines', cell: GLITCH.cells.lines, thr: 0.2, ink: [0.2, 0.2, 0.2], paper: [0, 0, 0] },
      over: o => { o.font = machine(290); o.fillStyle = '#cfcfcf'; o.fillText(tp('guess', t), 760, 700); } };
  }
  q.fillStyle = '#000'; q.fillRect(0, 0, W, H);
  q.font = machine(520, 250); q.fillStyle = '#fff';
  const shift = nudge(t, FLASHES[1][0] + FLASHES[1][1] / 60) * -36;   // after the flashes the word steps left, settling
  [...tp('guess', t)].forEach((ch, i) => q.fillText(ch, GX + shift + i * GSTEP, GBASE));
  return {
    cells: { mode: 'dots', cell: 26, thr: 0.3, gap: 0.12, flick: 0.06,
      ink: white ? [0.78, 0.78, 0.78] : [0.95, 0.95, 0.95], paper: white ? [0.93, 0.93, 0.93] : [0, 0, 0] },
    over: o => {
      const n = tp('guess', t).length;
      o.lineWidth = 2; o.font = machine(22);
      for (let i = 0; i < n; i++) {
        const x0 = GX + i * GSTEP + 10, x1 = x0 + 270, y0 = GBASE - 400 + (i === 0 ? 0 : 20), y1 = GBASE + 190;
        o.strokeStyle = white ? 'rgba(90,90,140,0.45)' : GLITCH.track.violet; o.strokeRect(x0, y0, x1 - x0, y1 - y0);
        o.fillStyle = white ? '#777' : '#ddd'; o.fillText(`x: ${Math.round(x0 + 3)}  y: ${Math.round(y0 - 10)}`, x0, y0 - 12);
      }
      path(o, [[GX + 140, GBASE - 360], [GX + 470, GBASE - 120], [GX + 800, GBASE - 160], [GX + 1130, GBASE - 110]],
        { color: white ? 'rgba(0,0,0,0.3)' : 'rgba(255,255,255,0.65)', dash: [9, 9] });
      o.fillStyle = GLITCH.track.dot;
      [[GX + 140, GBASE - 360], [GX + 800, GBASE - 160]].forEach(([x, y]) => { o.beginPath(); o.arc(x, y, 6, 0, Math.PI * 2); o.fill(); });
    },
  };
}

// ---- the harbour badges: a tile in a new dress every five frames, "every port worth sailing", its name below
const MARKS = [
  ['Kestrel Bay', '#0f2a3a', g => { g.strokeStyle = '#e8f4ff'; g.lineWidth = 22; g.beginPath(); g.arc(0, -40, 90, Math.PI * 0.15, Math.PI * 0.85, true); g.stroke(); g.beginPath(); g.moveTo(0, -150); g.lineTo(0, 120); g.moveTo(-100, 40); g.quadraticCurveTo(0, 170, 100, 40); g.stroke(); }],
  ['Port Avel', '#fafafa', g => { g.fillStyle = '#d64545'; g.fillRect(-45, -60, 90, 200); g.fillStyle = '#fff'; g.fillRect(-45, 0, 90, 40); g.fillStyle = '#ffd34d'; g.beginPath(); g.moveTo(-70, -60); g.lineTo(70, -60); g.lineTo(0, -150); g.fill(); }],
  ['Marrow Point', '#1a4ed8', g => { g.strokeStyle = '#fff'; g.lineWidth = 20; for (let k = 0; k < 3; k++) { g.beginPath(); for (let x = -130; x <= 130; x += 10) g.lineTo(x, -60 + k * 60 + Math.sin(x / 30) * 18); g.stroke(); } }],
  ['Sable Quay', '#111', g => { g.fillStyle = '#ff6b3d'; g.beginPath(); g.arc(0, 30, 80, Math.PI, 0); g.fill(); g.fillRect(-10, -140, 20, 120); g.fillStyle = '#fff'; g.fillRect(-80, 30, 160, 20); }],
  ['Lantern Cove', '#fafafa', g => { g.strokeStyle = '#111'; g.lineWidth = 16; g.beginPath(); g.arc(0, 0, 120, 0, Math.PI * 2); g.stroke(); g.fillStyle = '#e2338f'; g.beginPath(); g.moveTo(0, -100); g.lineTo(30, 0); g.lineTo(0, 100); g.lineTo(-30, 0); g.fill(); }],
  ['Ostra', '#e8f1ea', g => { g.fillStyle = '#0e9f8e'; g.beginPath(); g.moveTo(-130, 60); g.lineTo(0, -140); g.lineTo(20, 60); g.fill(); g.fillStyle = '#0b3d36'; g.fillRect(-140, 70, 280, 24); }],
  ['Halden', '#0b1a4a', g => { g.strokeStyle = '#9fd3ff'; g.lineWidth = 18; g.beginPath(); g.moveTo(-130, 20); g.quadraticCurveTo(-40, -80, 20, 0); g.quadraticCurveTo(80, 80, 130, -20); g.stroke(); g.fillStyle = '#9fd3ff'; g.beginPath(); g.arc(70, -90, 26, 0, Math.PI * 2); g.fill(); }],
  ['Brineholm', '#f4f4f4', g => { g.fillStyle = '#111'; g.beginPath(); g.ellipse(0, 0, 140, 60, 0, 0, Math.PI * 2); g.fill(); g.beginPath(); g.moveTo(120, 0); g.lineTo(180, -50); g.lineTo(180, 50); g.fill(); g.fillStyle = '#fff'; g.beginPath(); g.arc(-80, -10, 12, 0, Math.PI * 2); g.fill(); }],
];
const FIELDS = ['#262626', '#0a0a0a', '#2c3a44', '#7a3a2e', '#3c6a7a', '#8a8a8a', '#5a3a2a', '#1f3a34'];
export function harbours(q, t, u) {
  const n = slot(t, b(15.2)), k = n % MARKS.length, [name, tile, mark] = MARKS[k], field = FIELDS[n % FIELDS.length];
  const pop = 0.95 + 0.05 * nudge(t, b(15.2) + n * GLITCH.slot / GLITCH.fps, { dur: 0.083, overshoot: false });   // each tile comes in
  q.fillStyle = '#050505'; q.fillRect(0, 0, W, H);
  q.save(); q.filter = 'blur(36px)';
  q.fillStyle = field; q.fillRect(-100, -100, W + 200, 610);
  q.fillStyle = `hsl(${180 + hash(n, 3) * 60}, 40%, 45%)`; q.globalAlpha = 0.5; q.fillRect(1000 + hash(n, 2) * 400, -50, 600, 400);
  q.restore();
  const g2 = q.createLinearGradient(0, 470, 0, 560); g2.addColorStop(0, 'rgba(5,5,5,0)'); g2.addColorStop(1, '#050505');
  q.fillStyle = g2; q.fillRect(0, 470, W, 610);
  q.save(); q.translate(485, 478); q.rotate(0.012 + hash(n, 7) * 0.055); q.scale(pop, pop); q.transform(1, 0, 0.03, 1, 0, 0);
  q.shadowColor = 'rgba(0,0,0,0.7)'; q.shadowBlur = 50;
  q.fillStyle = '#1d1d1d'; q.beginPath(); q.roundRect(-395, -395, 790, 790, 70); q.fill(); q.shadowBlur = 0;
  q.fillStyle = tile; q.beginPath(); q.roundRect(-381, -381, 762, 762, 58); q.fill();
  const vg = q.createRadialGradient(0, -40, 160, 0, 0, 560); vg.addColorStop(0, 'rgba(0,0,0,0)'); vg.addColorStop(1, 'rgba(0,0,0,0.22)');
  q.fillStyle = vg; q.fill();
  q.scale(1.75, 1.75); mark(q); q.restore();
  q.font = voice(83, 500); q.fillStyle = '#fff'; q.fillText('every port worth sailing', 977, 563 + (1 - nudge(t, b(15.2), { overshoot: false })) * 30);
  q.save(); q.filter = 'blur(5px)'; q.font = voice(118, 700); q.fillStyle = 'rgba(255,255,255,0.5)'; q.fillText(name, 92, 1066);
  const bx = 92 + q.measureText(name).width + 70;
  q.fillStyle = '#c99a1c'; q.beginPath(); q.arc(bx, 1022, 42, 0, Math.PI * 2); q.fill();
  q.strokeStyle = 'rgba(40,30,10,0.8)'; q.lineWidth = 8; q.beginPath(); q.moveTo(bx - 16, 1022); q.lineTo(bx - 4, 1036); q.lineTo(bx + 18, 1008); q.stroke();
  q.restore();
  return { post: { vignette: 0.3 } };
}
