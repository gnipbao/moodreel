// 黄河 (the Yellow River), an Ink Chronicle demo: the river in its own words, in scenes made for it from the style's
// primitives (none of the reference's set pieces: ANALYSIS.md). Public-domain Tang verse is the corpus. See ../DEMO.md.
import { stage } from './kit/stage.js';
import { SIZE, INK } from './kit/tokens.js';
import { loadFaces, SONG, KAI, MONO, font } from './kit/faces.js';
import { paper, night, label, fill } from './kit/paper.js';
import { typed, textPoints, dots, gauss } from './kit/type.js';
import { waves, streaks, glow } from './kit/marks.js';
import { typeSpace } from './kit/space.js';
import { clamp, lerp, smoothstep, ease, hash, path } from './kit/anim.js';
import { DUR, shotAt, T, PLACES, LENGTH_KM } from './timeline.js';

const [W, H] = SIZE;
const CORPUS = '白日依山尽黄河入海流欲穷千里目更上一层楼黄河远上白云间一片孤城万仞山羌笛何须怨杨柳春风不度玉门关' +
  '君不见黄河之水天上来奔流到海不复回九曲黄河万里沙浪淘风簸自天涯如今直上银河去同到牵牛织女家';
const CH = [...CORPUS];
const DIKE = [...'河堤千里金堤固若汤池黄河大堤万里长'];
let S = null, WATER = null, SEA = null, COURSE = null, LOWER = null, LIP = null;

// a smooth course through control points (shares of the frame), walked by arc length
function course(ctrl, n = 600) {
  const P = ctrl.map(([x, y]) => ({ x: x * W, y: y * H })), out = [], per = Math.ceil(n / (P.length - 1));
  for (let i = 0; i < P.length - 1; i++) {
    const p0 = P[Math.max(0, i - 1)], p1 = P[i], p2 = P[i + 1], p3 = P[Math.min(P.length - 1, i + 2)];
    for (let k = 0; k < per; k++) {
      const u = k / per, u2 = u * u, u3 = u2 * u, cr = (a, b2, c, d) => 0.5 * (2 * b2 + (-a + c) * u + (2 * a - 5 * b2 + 4 * c - d) * u2 + (-a + 3 * b2 - 3 * c + d) * u3);
      out.push({ x: cr(p0.x, p1.x, p2.x, p3.x), y: cr(p0.y, p1.y, p2.y, p3.y) });
    }
  }
  out.push(P[P.length - 1]);
  return path(out);
}

// the river as a stream of its own verse: characters flowing along a course, lying along it, the band widening
// downstream, drawn up to the head (as far as it has run)
function stream(g, P, t, head, { size = 30, gap = 36, speed = 110, lanes = [1, 3], col = '#2a2622', fam = KAI, weight = 500, alpha = 1 } = {}) {
  g.save(); g.fillStyle = col; g.font = font(weight, size, fam); g.textAlign = 'center'; g.textBaseline = 'middle';
  const n = Math.ceil(P.length / gap) + 2;
  for (let i = 0; i < n; i++) {
    const s = (i * gap + t * speed) % (n * gap);
    if (s > head || s > P.length) continue;
    const u = s / P.length, L = Math.round(lerp(lanes[0], lanes[1], u)), { x, y, angle } = P.at(s);
    for (let l = 0; l < L; l++) {
      const off = (l - (L - 1) / 2) * gap * 0.9, px = x - Math.sin(angle) * off, py = y + Math.cos(angle) * off;
      g.globalAlpha = alpha * (0.55 + 0.45 * hash(i, l, 5)) * clamp((head - s) / 20);   // each character arrives at once
      g.save(); g.translate(px, py); g.rotate(angle); g.fillText(CH[(i * 3 + l * 7) % CH.length], 0, 0); g.restore();
    }
  }
  g.restore();
}

// a place popping in where the stream reaches it: a dot and its name, a little overshoot
function place(g, x, y, name, t, t0, { col = '#2a2622', accent = false } = {}) {
  if (t < t0) return;
  const k = 1 + 0.6 * (1 - ease.outBack(clamp((t - t0) / 0.22), 2.2));
  g.save(); g.translate(x, y); g.scale(k, k); g.fillStyle = accent ? INK.accent : col;
  g.beginPath(); g.arc(0, 0, accent ? 10 : 6, 0, Math.PI * 2); g.fill();
  g.font = font(accent ? 700 : 400, accent ? 36 : 30, SONG); g.textAlign = 'left'; g.textBaseline = 'middle'; g.fillText(name, 18, 0);
  g.restore();
}

// ---- the source: in the dark, 水 lands like a blow, then runs: its grit trickling down into a thread of water
function source(g, t) {
  night(g, { specks: 60 });
  glow(g, W / 2, 0.42 * H, 140, { a: 0.1 * smoothstep(0.1, 1.0, t) });
  if (t >= T.water && t < T.melt) typed(g, '水', W / 2, 0.42 * H + 0.38 * 360, t, 0, { at: [T.water], size: 360, weight: 900, color: INK.white, align: 'center', slam: 2.4, sdur: 0.1, split: 36 });
  if (t >= T.melt) {
    const u = t - T.melt, pts = [];
    for (let i = 0; i < WATER.length; i++) {
      const [px, py] = WATER[i], f = clamp((u - 0.4 * (1 - (py + 180) / 360) - 0.15 * hash(i, 11)) / 0.45);
      pts.push([W / 2 + px * (1 - 0.94 * ease.inCubic(f)) + Math.sin(f * 7 + i) * 3 * f, 0.42 * H + py + f * f * 640, 2.4 + 1.2 * hash(i, 12), 0.95 * (1 - 0.35 * f)]);
    }
    dots(g, pts, INK.white);
  }
  label(g, '巴颜喀拉山 · 源', '0 km', '#d8d4cf', smoothstep(T.water + 0.3, T.water + 0.6, t));
}

// ---- the course: on paper the river is a stream of its verse winding through nine bends, the camera starting on its
// head and pulling back to the whole course as it runs; its places pop in as it reaches them
function courseShot(g, t, s) {
  paper(g);
  const run = tt => COURSE.length * lerp(0.08, 0.78, ease.inOutCubic(clamp((tt - s.t0) / (s.t1 - s.t0))));
  const e = ease.inOutCubic(clamp((t - s.t0 - 0.45) / 1.3)), z = lerp(2.4, 1.0, e), h = COURSE.at(run(t));   // waits on the head, then pulls away
  g.save(); g.translate(W / 2, H / 2); g.scale(z, z); g.translate(-lerp(h.x, W / 2, e), -lerp(h.y, H / 2, e));
  stream(g, COURSE, t, run(t));
  T.bends.forEach((at, i) => { const p = COURSE.at(run(at)); place(g, p.x + 26, p.y - 34, PLACES[i], t, at); });
  g.restore();
  label(g, '黄河 · 九曲', '', '#3a3632');
}

// ---- the gorge: low between two cliffs of the river's words, the bed of them underfoot; 壶口 lands and the camera
// lurches forward with it
function gorge(g, t, s) {
  paper(g);
  const lurch = 4 * ease.outCubic(clamp((t - T.blow) / 0.3)), z = 10 - 5.2 * (t - s.t0) - lurch;
  const cam = { p: [0.3 * Math.sin((t - s.t0) * 1.2), 1.4, z], l: [0, 2.2, z - 10], fov: 46 };
  g.drawImage(S.render(cam, { theme: 'day', fog: [4, 46], place: k => (k.startsWith('d') ? null : undefined) }), 0, 0, W, H);
  if (t >= T.blow) typed(g, '壶口', W / 2, 0.3 * H + 0.38 * 300, t, 0, { at: [T.blow, T.blow], size: 300, weight: 900, color: INK.ink, align: 'center', slam: 2.2, sdur: 0.1 });
  label(g, '晋陕峡谷 · 壶口', '', '#3a3632');
}

// ---- the falls: the whole river squeezed over the lip, its text pouring in a torrent thickest at its middle, faster
// as it falls, breaking into spray that billows up from the foot
function falls(g, t, s) {
  night(g, { col: '#1b1916', warm: 'rgba(70,64,56,0.45)', specks: 0 });
  const u = t - s.t0, lip = 0.22 * H - 40 * u, x0 = 0.28 * W, x1 = 0.72 * W, cw = 24;
  glow(g, W / 2, 0.86 * H, 220, { col: '236,232,224', a: 0.12 });   // the spray's light
  g.save(); g.font = font(500, 24, KAI); g.textAlign = 'center'; g.textBaseline = 'middle';
  for (let c = 0; x0 + c * cw < x1; c++) {
    const x = x0 + c * cw + cw / 2, n = Math.round(6 + 12 * (1 - Math.abs(x - W / 2) / (0.22 * W)));
    for (let k = 0; k < n; k++) {
      const ph = (hash(c, k, 21) + u * (1.5 + 0.6 * hash(c, 22))) % 1, y = lip + ph * ph * 0.64 * H, a = 0.9 * (1 - smoothstep(0.8, 1, ph));
      g.strokeStyle = `rgba(232,228,220,${0.24 * a})`; g.lineWidth = 2; g.beginPath(); g.moveTo(x, y - 18 - 170 * ph); g.lineTo(x, y - 14); g.stroke();
      g.globalAlpha = a; g.fillStyle = '#ece8e0'; g.fillText(CH[(c * 5 + k * 11) % CH.length], x, y); g.globalAlpha = 1;
    }
  }
  g.restore();
  stream(g, LIP, t, LIP.length, { col: '#d8d4cc', size: 24, gap: 28, speed: 260, lanes: [3, 5], alpha: 0.8 });   // the river running to the edge
  const pts = [];
  for (let i = 0; i < 6000; i++) {
    const f = (hash(i, 31) + u * 0.5) % 1;
    pts.push([W / 2 + gauss(i, 32) * 0.16 * W * (0.5 + 1.3 * f), 0.88 * H - f * 0.34 * H + gauss(i, 33) * 22, 1.6 + 2.8 * hash(i, 34) ** 2, 0.6 * (1 - f)]);
  }
  dots(g, pts, '#e8e4dc');
  streaks(g, t, { n: 90, angle: 0.02, speed: [1.6, 2.6], col: '232,228,220', alpha: [0.05, 0.16] });
  label(g, '壶口 · 瀑布', '', '#d8d4cf');
}

// ---- the flood: in the rain, a dike of blocks carrying its own words; 决 lands (one frame of negative first) and the
// dike bursts toward us
function flood(g, t, s) {
  night(g, { specks: 40 });
  const u = t - T.breach, burst = u >= 0;
  const placeBlock = k => {
    if (!k.startsWith('d')) return null;
    const i = +k.slice(1), c = i % 6, r = Math.floor(i / 6), p0 = [(c - 2.5) * 1.06, 0.5 + r * 1.06, 0];
    if (!burst) return { p: p0, r: [0, 0, 0], grey: true };
    const f = Math.max(0, u - 0.06 * hash(i, 44)), v = [(c - 2.5) * 1.3 + (hash(i, 41) - 0.5) * 2, 2.2 + 3 * hash(i, 42), 5 + 6 * hash(i, 43)];
    return { p: [p0[0] + v[0] * f, p0[1] + v[1] * f - 4.9 * f * f, p0[2] + v[2] * f], r: [f * (hash(i, 45) - 0.5) * 9, f * (hash(i, 46) - 0.5) * 9, f * (hash(i, 47) - 0.5) * 6], grey: true };
  };
  const cam = { p: [0.2 * Math.sin(t * 0.7), 1.9, 8.2 - 0.3 * (t - s.t0)], l: [0, 1.5, 0], fov: 40 };
  g.drawImage(S.render(cam, { theme: 'night', fog: [6, 30], light: { spot: [0, 9, 3], spotI: 70 }, glowGrey: 0.28, place: placeBlock }), 0, 0, W, H);
  streaks(g, t, { n: 420, angle: 0.14, col: '200,196,190', alpha: [0.08, 0.3] });
  if (burst && u < 1 / 30) {                                         // the hardest blow: one frame of negative
    fill(g, '#f4f6f6'); g.save(); g.fillStyle = '#29c9ee'; g.font = font(900, 760, SONG); g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText('决', W / 2, 0.52 * H); g.restore();
    return;
  }
  if (burst) typed(g, '决', W / 2, 0.36 * H + 0.38 * 320, t, 0, { at: [T.breach], size: 320, weight: 900, color: INK.white, align: 'center', slam: 2.4, sdur: 0.1, split: 36 });
  label(g, '黄河 · 决口', '', '#d8d4cf');
}

// ---- the delta: the last reach runs to the coast, the length counting; at the mouth the stream fans into the sea in
// thinner streams that dissolve to grit; the mouth is the one thing marked in the accent
function delta(g, t, s) {
  paper(g);
  const coast = 0.66 * H, mouth = LOWER.at(LOWER.length), push = 1 + 0.16 * ease.outCubic(clamp((t - T.mouth + 0.12) / 0.3));   // holds wide, then lands on the mouth
  g.save(); g.translate(mouth.x, mouth.y); g.scale(push, push); g.translate(-mouth.x, -mouth.y);
  waves(g, t, { y0: coast, y1: H * 1.1, crest: '58,54,48', trough: '255,255,255', alpha: 4.5, drift: 0.4 });
  const run = lerp(0.35, 1, ease.inOutQuad(clamp((t - s.t0) / (T.mouth - s.t0))));   // already running as we cut in
  stream(g, LOWER, t, LOWER.length * run, { lanes: [2, 3] });
  const fan = clamp((t - T.mouth + 0.3) / 0.9);
  if (fan > 0) {                                                     // the delta: thin streams spreading over the sea
    g.save(); g.font = font(500, 24, KAI); g.fillStyle = '#2a2622'; g.textAlign = 'center'; g.textBaseline = 'middle';
    const grit = [];
    for (let k = 0; k < 11; k++) {
      const a = lerp(0.05, 1.45, k / 10) + (hash(k, 51) - 0.5) * 0.12, len = (340 + 300 * hash(k, 52)) * ease.outCubic(fan);
      for (let d = 0; d < len; d += 22) {
        const bend = Math.sin(d / 90 + k) * 18, x = mouth.x + Math.cos(a) * d - Math.sin(a) * bend, y = mouth.y + Math.sin(a) * d * 0.45 + Math.cos(a) * bend * 0.4;
        const far = d / 640, fade = 1 - far;
        if (fade <= 0.05) continue;
        if (far < 0.55) { g.globalAlpha = 0.8 * fade; g.fillText(CH[(k * 13 + Math.round(d / 22) * 5) % CH.length], x, y); }
        else for (let q = 0; q < 6; q++) grit.push([x + gauss(k * 999 + d + q, 53) * 10, y + gauss(k * 999 + d + q, 55) * 5, 1.6 + 1.6 * hash(k, d, q), 0.7 * fade]);
      }
    }
    g.restore(); g.globalAlpha = 1; dots(g, grit, '#2a2622');
  }
  place(g, mouth.x + 30, mouth.y - 40, '入海口 · 东营', t, T.mouth, { accent: true });
  g.restore();
  const steps = [[T.places[0], 3472], [T.places[1], 4678], [T.places[2], LENGTH_KM]];   // the upper, middle and lower reaches
  const km = Math.round(steps.reduce((v, [at, to]) => lerp(v, to, clamp((t - at) / 0.42)), 0));   // counts run evenly
  if (km > 0) {                                                      // in the corner the river leaves empty
    g.fillStyle = '#2a2622'; g.font = `400 64px "${MONO}"`; g.textAlign = 'right'; g.textBaseline = 'alphabetic';
    g.fillText(`${km.toLocaleString('en-US')} km`, 0.9 * W, 0.24 * H);
  }
}

// ---- the end: on paper 海 lands like a blow, then becomes the sea: its grit spreads out and lies down in rows of waves
function end(g, t) {
  paper(g);
  if (t >= T.last && t < T.drift) typed(g, '海', W / 2, 0.47 * H + 0.38 * 420, t, 0, { at: [T.last], size: 420, weight: 900, color: INK.ink, align: 'center', slam: 2.0, sdur: 0.1 });
  if (t >= T.drift) {
    const u = t - T.drift;
    g.save(); g.strokeStyle = INK.ink; g.lineCap = 'round';
    for (let i = 0; i < SEA.length; i += 2) {
      const [px, py] = SEA[i], f = ease.inOutCubic(clamp((u - 0.3 * hash(i, 61)) / 0.6));
      const row = Math.round(py / 30) * 30, x = W / 2 + px * (1 + 2.6 * f) + (hash(i, 62) - 0.5) * 520 * f, y = lerp(0.47 * H + py, 0.8 * H + row * 0.45, f);
      g.globalAlpha = 0.95 - 0.45 * f; g.lineWidth = 2.6 - 1.2 * f; g.beginPath(); g.moveTo(x - 1 - 14 * f, y); g.lineTo(x + 1 + 14 * f, y); g.stroke();
    }
    g.restore();
  }
  label(g, '黄河 · 入海', `${LENGTH_KM.toLocaleString('en-US')} km`, '#3a3632', smoothstep(T.last + 0.3, T.last + 0.6, t));
}

const SHOT = { source, course: courseShot, gorge, falls, flood, delta, end };

stage({
  width: W, height: H, duration: DUR, background: '#000',
  prepare: async () => {
    await loadFaces();
    S = typeSpace(1280, 720);
    S.plane('wallL', { corpus: CORPUS, size: [300, 22], p: [-2.6, 9, -120], r: [0, Math.PI / 2, 0], repeat: [20, 1.5] });
    S.plane('wallR', { corpus: CORPUS, size: [300, 22], p: [2.6, 9, -120], r: [0, -Math.PI / 2, 0], repeat: [20, 1.5] });
    S.plane('bed', { corpus: CORPUS, size: [5.2, 300], p: [0, -0.02, -120], r: [-Math.PI / 2, 0, 0], repeat: [0.35, 24] });
    DIKE.forEach((c, i) => S.block('d' + i, c));
    WATER = textPoints('水', 360, { weight: 900, fam: SONG, step: 3, max: 12000 });
    SEA = textPoints('海', 420, { weight: 900, fam: SONG, step: 3, max: 16000 });
    COURSE = course([[-0.04, 0.16], [0.12, 0.12], [0.26, 0.28], [0.16, 0.46], [0.3, 0.6], [0.48, 0.5], [0.54, 0.28], [0.7, 0.24], [0.8, 0.44], [0.68, 0.62], [0.8, 0.78], [1.04, 0.84]]);
    LOWER = course([[-0.04, 0.1], [0.14, 0.2], [0.28, 0.13], [0.4, 0.3], [0.5, 0.48], [0.62, 0.66]]);
    LIP = course([[0.05, 0.05], [0.25, 0.14], [0.5, 0.2]]);
  },
  draw: (g, t) => {
    const s = shotAt(t);
    g.save(); SHOT[s.kind](g, t, s); g.restore();
  },
});
