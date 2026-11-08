// kit/3dcv/text.js — ported from 3DCodeVerse (https://github.com/gaoypeng/3dcodeverse), awesome showcase
//   (https://huggingface.co/datasets/3dcodeverse/3dcodeverse-awesome-showcase): the 30-second film's code,
//   source src/core/text.js, round r02, git blob 706a7faa118058ba4af0b5f168a6c37a41aa7154.
// Licence: CC BY-NC-SA 4.0 (https://creativecommons.org/licenses/by-nc-sa/4.0/), see kit/3dcv/LICENSE.
//   Non-commercial use only; adaptations keep this licence. The rest of moodreel is MIT.
// Changes by moodreel (2026-11-08): three.js taken from ../three.js instead of the bare 'three' import; the
//   default title lines of titleTexture (now ['TITLE']) and the default phrase of createWriter (now 'HELLO'),
//   which quoted a film's on-screen words, made neutral, and the comments that quoted them reworded; this header.

// text.js — vector stroke lettering drawn with our own glyph skeletons (no fonts).  See CORE_API.md §Text.
//  * ROMAN: thin, elegant classical roman capitals (Trajan-like): broad-nib thick/thin modulation, bracketed serifs,
//    wide tracking — for a large title, e.g. one set into a floor.
//  * HAND: neat handwritten monoline capitals with progressive stroke reveal and nib position — a phrase written out.
// Glyph space: x in [0, adv] (cap-height units), y up, baseline 0, cap height 1.
// Owner: core (foundation stage).
import { THREE } from '../three.js';
import { rng, noise1 } from './util.js';
import * as paint from './paint.js';

// ------------------------------------------------------------------------------------------------ path builders
const D2R = Math.PI / 180;
function arc(cx, cy, rx, ry, a0, a1, n) {
  n = n || Math.max(8, Math.ceil(Math.abs(a1 - a0) / 6));
  const p = []; for (let i = 0; i <= n; i++) { const a = (a0 + (a1 - a0) * i / n) * D2R; p.push([cx + rx * Math.cos(a), cy + ry * Math.sin(a)]); }
  return p;
}
function bz(p0, p1, p2, p3, n = 20) {
  const p = []; for (let i = 0; i <= n; i++) { const t = i / n, u = 1 - t;
    p.push([u * u * u * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t * t * t * p3[0], u * u * u * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t * t * t * p3[1]]); }
  return p;
}
const join = (...parts) => { const out = []; for (const p of parts) for (const q of p) { const l = out[out.length - 1]; if (!l || Math.hypot(l[0] - q[0], l[1] - q[1]) > 1e-6) out.push(q); } return out; };
const L = (x0, y0, x1, y1) => [[x0, y0], [x1, y1]];
// stroke: { p: points, w: width multiplier, s: [startSerif, endSerif] }  serif codes: 'b' foot, 't' head, 'vd' flare down, 'vu' flare up, 'vb' both
const S = (p, w = 1, s0 = null, s1 = null) => ({ p, w, s: [s0, s1] });

/** Glyph skeletons (shared by ROMAN and HAND).  adv = advance width (cap-height units). */
export const GLYPHS = {
  ' ': { adv: 0.32, st: [] },
  A: { adv: 0.80, st: [S(L(0.02, 0, 0.40, 1), 1, 'b', null), S(L(0.40, 1, 0.78, 0), 1, null, 'b'), S(L(0.19, 0.32, 0.61, 0.32), 0.9)] },
  B: { adv: 0.56, st: [S(L(0.06, 1, 0.06, 0), 1, 't', 'b'), S(join(L(0.06, 1, 0.29, 1), arc(0.29, 0.765, 0.205, 0.235, 90, -90), L(0.29, 0.53, 0.06, 0.53)), 1),
    S(join(L(0.06, 0.53, 0.32, 0.53), arc(0.32, 0.265, 0.235, 0.265, 90, -90), L(0.32, 0, 0.06, 0)), 1)] },
  C: { adv: 0.76, st: [S(arc(0.43, 0.5, 0.41, 0.51, 48, 315, 56), 1, 'vb', 'vu')] },
  D: { adv: 0.80, st: [S(L(0.06, 1, 0.06, 0), 1, 't', 'b'), S(join(L(0.06, 1, 0.33, 1), arc(0.33, 0.5, 0.41, 0.5, 90, -90, 40), L(0.33, 0, 0.06, 0)), 1)] },
  E: { adv: 0.52, st: [S(L(0.07, 1, 0.07, 0), 1, 't', 'b'), S(L(0.07, 1, 0.47, 1), 1, null, 'vd'), S(L(0.07, 0.53, 0.40, 0.53), 1, null, 'vb'), S(L(0.07, 0, 0.50, 0), 1, null, 'vu')] },
  F: { adv: 0.50, st: [S(L(0.07, 1, 0.07, 0), 1, 't', 'b'), S(L(0.07, 1, 0.47, 1), 1, null, 'vd'), S(L(0.07, 0.52, 0.40, 0.52), 1, null, 'vb')] },
  G: { adv: 0.80, st: [S(arc(0.43, 0.5, 0.41, 0.51, 48, 335, 56), 1, 'vb', null), S(L(0.78, 0.43, 0.78, 0.05), 0.9, 't', null)] },
  H: { adv: 0.78, st: [S(L(0.06, 1, 0.06, 0), 1, 't', 'b'), S(L(0.72, 1, 0.72, 0), 1, 't', 'b'), S(L(0.06, 0.52, 0.72, 0.52), 1)] },
  I: { adv: 0.13, st: [S(L(0.065, 1, 0.065, 0), 1, 't', 'b')] },
  J: { adv: 0.40, st: [S(join(L(0.32, 1, 0.32, 0.16), arc(0.17, 0.16, 0.15, 0.2, 0, -150, 16)), 1, 't', null)] },
  K: { adv: 0.70, st: [S(L(0.06, 1, 0.06, 0), 1, 't', 'b'), S(L(0.64, 1, 0.08, 0.44), 1, 't', null), S(L(0.25, 0.6, 0.69, 0), 1, null, 'b')] },
  L: { adv: 0.54, st: [S(L(0.07, 1, 0.07, 0), 1, 't', null), S(L(0.07, 0, 0.52, 0), 1, null, 'vu')] },
  M: { adv: 0.98, st: [S(L(0.07, 0, 0.12, 1), 0.45, 'b', 't'), S(L(0.12, 1, 0.49, 0), 1), S(L(0.49, 0, 0.86, 1), 1), S(L(0.86, 1, 0.91, 0), 1, 't', 'b')] },
  N: { adv: 0.80, st: [S(L(0.06, 0, 0.06, 1), 0.45, 'b', 't'), S(L(0.06, 1, 0.74, 0), 1), S(L(0.74, 0, 0.74, 1), 0.45, null, 't')] },
  O: { adv: 0.86, st: [S(arc(0.43, 0.5, 0.42, 0.51, 90, 450, 72), 1)] },
  P: { adv: 0.56, st: [S(L(0.06, 1, 0.06, 0), 1, 't', 'b'), S(join(L(0.06, 1, 0.29, 1), arc(0.29, 0.74, 0.235, 0.26, 90, -90), L(0.29, 0.48, 0.06, 0.48)), 1)] },
  Q: { adv: 0.86, st: [S(arc(0.43, 0.5, 0.42, 0.51, 90, 450, 72), 1), S(bz([0.40, 0.02], [0.55, -0.04], [0.75, -0.08], [0.92, -0.16], 12), 1)] },
  R: { adv: 0.66, st: [S(L(0.06, 1, 0.06, 0), 1, 't', 'b'), S(join(L(0.06, 1, 0.30, 1), arc(0.30, 0.75, 0.23, 0.25, 90, -90), L(0.30, 0.5, 0.06, 0.5)), 1),
    S(bz([0.26, 0.5], [0.40, 0.42], [0.52, 0.18], [0.68, 0], 14), 1, null, 'b')] },
  S: { adv: 0.50, st: [S(join(bz([0.45, 0.88], [0.38, 1.02], [0.05, 1.03], [0.06, 0.76], 16), bz([0.06, 0.76], [0.07, 0.52], [0.46, 0.52], [0.46, 0.25], 18), bz([0.46, 0.25], [0.46, -0.03], [0.09, -0.04], [0.03, 0.12], 16)), 1, 'vb', 'vu')] },
  T: { adv: 0.70, st: [S(L(0.01, 1, 0.69, 1), 1, 'vd', 'vd'), S(L(0.35, 1, 0.35, 0), 1, null, 'b')] },
  U: { adv: 0.78, st: [S(join(L(0.07, 1, 0.07, 0.32), arc(0.385, 0.32, 0.315, 0.32, 180, 360, 30), L(0.70, 0.32, 0.70, 1)), 1, 't', 't')] },
  V: { adv: 0.76, st: [S(L(0.01, 1, 0.38, 0), 1, 't', null), S(L(0.38, 0, 0.75, 1), 1, null, 't')] },
  W: { adv: 1.14, st: [S(L(0.01, 1, 0.29, 0), 1, 't', null), S(L(0.29, 0, 0.57, 1), 1), S(L(0.57, 1, 0.85, 0), 1), S(L(0.85, 0, 1.13, 1), 1, null, 't')] },
  X: { adv: 0.72, st: [S(L(0.03, 1, 0.69, 0), 1, 't', 'b'), S(L(0.67, 1, 0.05, 0), 1, 't', 'b')] },
  Y: { adv: 0.70, st: [S(L(0.01, 1, 0.35, 0.47), 1, 't', null), S(L(0.69, 1, 0.35, 0.47), 1, 't', null), S(L(0.35, 0.47, 0.35, 0), 1, null, 'b')] },
  Z: { adv: 0.64, st: [S(L(0.05, 1, 0.60, 1), 1, 'vd', null), S(L(0.60, 1, 0.03, 0), 1), S(L(0.03, 0, 0.62, 0), 1, null, 'vu')] },
  '.': { adv: 0.2, st: [S([[0.1, 0.03], [0.1, 0.035]], 1)] },
  ',': { adv: 0.2, st: [S(L(0.11, 0.05, 0.07, -0.1), 1)] },
  "'": { adv: 0.16, st: [S(L(0.08, 1, 0.07, 0.8), 1)] },
  '-': { adv: 0.4, st: [S(L(0.05, 0.42, 0.35, 0.42), 1)] },
};

// densify a polyline at ~step spacing (glyph units)
function densify(p, step = 0.012) {
  const out = [p[0]];
  for (let i = 1; i < p.length; i++) {
    const a = p[i - 1], b = p[i], d = Math.hypot(b[0] - a[0], b[1] - a[1]), n = Math.max(1, Math.ceil(d / step));
    for (let k = 1; k <= n; k++) out.push([a[0] + (b[0] - a[0]) * k / n, a[1] + (b[1] - a[1]) * k / n]);
  }
  return out;
}

/**
 * layout(text, { tracking=0.12 (em extra per letter), xScale=1 }) -> { glyphs:[{ch, x, def}], width }  (cap-height units)
 */
export function layout(text, o = {}) {
  const tr = o.tracking ?? 0.12, xs = o.xScale ?? 1; let x = 0; const glyphs = [];
  for (const ch of text.toUpperCase()) {
    const def = GLYPHS[ch] || GLYPHS[' '];
    glyphs.push({ ch, x, def });
    x += def.adv * xs + (ch === ' ' ? 0 : tr);
  }
  const last = glyphs[glyphs.length - 1];
  return { glyphs, width: last ? last.x + last.def.adv * xs : 0 };
}

// ------------------------------------------------------------------------------------------------ ROMAN rendering
/**
 * drawRoman(g, text, { x, y (baseline px), size (cap height px), color='#6b4658', tracking=0.14, align='center'|'left'|'right',
 *                      thick=0.105, thin=0.022, nibAngle=28 (deg), contrastPow=2.4, serif=1 (scale), opacity=1 })
 * Draws thin elegant roman capitals with broad-nib modulation and bracketed serifs into a 2D context.  Returns width in px.
 */
export function drawRoman(g, text, o = {}) {
  const size = o.size || 100, tr = o.tracking ?? 0.14, lay = layout(text, { tracking: tr });
  const W = lay.width * size;
  let x0 = o.x ?? 0; if ((o.align || 'center') === 'center') x0 -= W / 2; else if (o.align === 'right') x0 -= W;
  const y0 = o.y ?? size;
  const thick = o.thick ?? 0.105, thin = o.thin ?? 0.022, nib = (o.nibAngle ?? 28) * D2R, pw = o.contrastPow ?? 2.4, sf = o.serif ?? 1;
  const X = gx => x0 + gx * size, Y = gy => y0 - gy * size;
  g.save(); g.fillStyle = o.color || '#6b4658'; g.globalAlpha = o.opacity ?? 1;
  const width = (dx, dy, mul) => { const a = Math.atan2(dy, dx); return (thin + (thick - thin) * Math.pow(Math.abs(Math.sin(a - nib)), pw)) * Math.min(1, mul) + (mul > 1 ? (mul - 1) * thick : 0); };
  for (const gl of lay.glyphs) {
    for (const st of gl.def.st) {
      const pts = densify(st.p.map(([px, py]) => [gl.x + px, py]));
      if (pts.length < 2) { g.beginPath(); g.arc(X(pts[0][0]), Y(pts[0][1]), thick * size * 0.6, 0, Math.PI * 2); g.fill(); continue; }
      const left = [], right = [];
      for (let i = 0; i < pts.length; i++) {
        const a = pts[Math.max(0, i - 1)], b = pts[Math.min(pts.length - 1, i + 1)];
        const dx = b[0] - a[0], dy = b[1] - a[1], len = Math.hypot(dx, dy) || 1;
        let w = width(dx, dy, st.w) * 0.5;
        // tapered stroke ends of curves look calligraphic; straight stems stay full
        const nx = -dy / len, ny = dx / len;
        left.push([pts[i][0] + nx * w, pts[i][1] + ny * w]); right.push([pts[i][0] - nx * w, pts[i][1] - ny * w]);
      }
      g.beginPath();
      left.forEach(([px, py], i) => (i ? g.lineTo(X(px), Y(py)) : g.moveTo(X(px), Y(py))));
      for (let i = right.length - 1; i >= 0; i--) g.lineTo(X(right[i][0]), Y(right[i][1]));
      g.closePath(); g.fill();
      // serifs
      st.s.forEach((code, k) => {
        if (!code || sf <= 0) return;
        const p = pts[k === 0 ? 0 : pts.length - 1], q = pts[k === 0 ? 1 : pts.length - 2];
        const sw = width(p[0] - q[0], p[1] - q[1], st.w);
        serif(g, X, Y, p[0], p[1], code, sw, size, sf, thin);
      });
    }
  }
  g.restore();
  return W;
}
function serif(g, X, Y, x, y, code, stemW, size, sf, thin) {
  if (code === 'b' || code === 't') {
    const dir = code === 'b' ? 1 : -1;           // bracket goes up from the baseline ('b') or down from the cap line ('t')
    const h = stemW * 0.5, Ls = 0.085 * sf + stemW * 0.15, t = thin * 1.05, bh = 0.075 * sf;
    g.beginPath();
    g.moveTo(X(x - h), Y(y + dir * bh));
    g.quadraticCurveTo(X(x - h), Y(y + dir * t), X(x - h - Ls), Y(y + dir * t * 0.75));
    g.lineTo(X(x - h - Ls - 0.006), Y(y));
    g.lineTo(X(x + h + Ls + 0.006), Y(y));
    g.lineTo(X(x + h + Ls), Y(y + dir * t * 0.75));
    g.quadraticCurveTo(X(x + h), Y(y + dir * t), X(x + h), Y(y + dir * bh));
    g.closePath(); g.fill();
  } else {
    const up = code === 'vu' || code === 'vb', dn = code === 'vd' || code === 'vb';
    const hw = thin * 0.9, ext = 0.09 * sf;
    g.beginPath();
    g.moveTo(X(x - hw * 1.2), Y(y + (up ? ext : thin * 0.6)));
    g.quadraticCurveTo(X(x - hw * 0.4), Y(y), X(x - hw * 1.2), Y(y - (dn ? ext : thin * 0.6)));
    g.lineTo(X(x + hw * 0.6), Y(y - (dn ? ext * 0.85 : thin * 0.6)));
    g.lineTo(X(x + hw * 0.6), Y(y + (up ? ext * 0.85 : thin * 0.6)));
    g.closePath(); g.fill();
  }
}

/**
 * titleTexture({ lines:['TITLE'], width=4096, height=1024, color='#6b4658', capHeight (px, default auto),
 *                lineGap=0.42 (em between lines), tracking=0.14, align='center', background=null (transparent) | css colour,
 *                softness=0 (px blur, ink bleed), thick, thin, nibAngle })
 * -> { texture (sRGB, transparent background unless given), canvas, aspect, capHeightUV (cap height as fraction of texture height) }
 */
export function titleTexture(o = {}) {
  const lines = o.lines || ['TITLE'];
  const P = paint.canvas(o.width || 4096, o.height || 1024);
  if (o.background) paint.fill(P, o.background);
  const tr = o.tracking ?? 0.14, gap = o.lineGap ?? 0.42;
  const maxW = Math.max(...lines.map(l => layout(l, { tracking: tr }).width));
  const cap = o.capHeight || Math.min((P.w * 0.92) / maxW, (P.h * 0.9) / (lines.length + (lines.length - 1) * gap));
  const totalH = cap * (lines.length + (lines.length - 1) * gap);
  let y = (P.h - totalH) / 2 + cap;
  if (o.softness) P.g.filter = `blur(${o.softness}px)`;
  for (const line of lines) {
    const ax = o.align === 'left' ? P.w * 0.04 : o.align === 'right' ? P.w * 0.96 : P.w / 2;
    drawRoman(P.g, line, { x: ax, y, size: cap, color: o.color, tracking: tr, align: o.align || 'center', thick: o.thick, thin: o.thin, nibAngle: o.nibAngle });
    y += cap * (1 + gap);
  }
  P.g.filter = 'none';
  const texture = paint.texture(P, { wrap: 'clamp', anisotropy: 16 });
  return { texture, canvas: P, aspect: P.w / P.h, capHeightUV: cap / P.h };
}

// ------------------------------------------------------------------------------------------------ HAND writer
/**
 * createWriter({ text='HELLO', width=2048, height=1448, box:[x0,y0,x1,y1] (0..1 of canvas; text is fitted and
 *   centred in it), capHeight (px, default fit), tracking=0.22, xScale=0.86, inkWidth=0.085 (em), ink='#3c4a7a',
 *   glow='#b9f4ff', glowTail=1.6 (em of freshly written stroke that still glows), seed=7, jitter=1, liftWeight=0.5,
 *   background: null | css colour | (P) => void   (e.g. P => paint.paper(P)), glowBackground='#000000' })
 * -> writer {
 *   canvas, texture        — ink (+ background) texture, sRGB
 *   glowCanvas, glowTexture — emissive mask of the fresh glowing ink (use as emissiveMap)
 *   totalLength            — ink + weighted pen-lift travel (em)
 *   update(progress 0..1)  — redraws both canvases; returns nib state (below)
 *   nibAt(progress)        — nib state without drawing: { u, v (texture UV, v up), x, y (canvas px), down (pen on paper), stroke, letter }
 * }
 * Stroke order follows the glyph skeleton order (natural handwriting order).
 */
export function createWriter(o = {}) {
  const text = o.text || 'HELLO';
  const Wc = o.width || 2048, Hc = o.height || 1448;
  const P = paint.canvas(Wc, Hc), G = paint.canvas(Wc, Hc);
  const box = o.box || [0.08, 0.3, 0.92, 0.6];
  const tr = o.tracking ?? 0.22, xs = o.xScale ?? 0.86, lay = layout(text, { tracking: tr, xScale: xs });
  const bw = (box[2] - box[0]) * Wc, bh = (box[3] - box[1]) * Hc;
  const cap = o.capHeight || Math.min(bw / lay.width, bh);
  const ox = box[0] * Wc + (bw - lay.width * cap) / 2, base = box[1] * Hc + (bh + cap) / 2;
  const r = rng(o.seed ?? 7), jit = o.jitter ?? 1, inkW = (o.inkWidth ?? 0.085) * cap;
  // build strokes in canvas px with per-letter jitter + smooth wobble
  const strokes = [];
  lay.glyphs.forEach((gl, li) => {
    const rot = r.range(-2.2, 2.2) * D2R * jit, dy = r.range(-0.025, 0.025) * jit, sc = 1 + r.range(-0.035, 0.035) * jit;
    const cx = gl.x + gl.def.adv * xs * 0.5;
    gl.def.st.forEach((st, si) => {
      const pts = densify(st.p.map(([px, py]) => [px * xs, py]), 0.02).map(([px, py], k) => {
        let x = (px - gl.def.adv * xs * 0.5) * sc, y = (py - 0.5) * sc;
        const xr = x * Math.cos(rot) - y * Math.sin(rot), yr = x * Math.sin(rot) + y * Math.cos(rot);
        const wob = 0.008 * jit;
        return [ox + (cx + xr + 0) * cap + noise1(k * 0.15 + li * 7 + si, 11) * wob * cap, base - (yr + 0.5 + dy) * cap + noise1(k * 0.15 + li * 5 + si, 23) * wob * cap];
      });
      strokes.push({ pts, letter: li });
    });
  });
  // arc lengths (px) incl. pen-lift travel
  const liftW = o.liftWeight ?? 0.5;
  let acc = 0; const segs = [];
  strokes.forEach((s, i) => {
    if (i > 0) { const a = strokes[i - 1].pts[strokes[i - 1].pts.length - 1], b = s.pts[0]; const d = Math.hypot(b[0] - a[0], b[1] - a[1]) * liftW; segs.push({ lift: true, from: a, to: b, s0: acc, s1: acc + d }); acc += d; }
    const cum = [0]; for (let k = 1; k < s.pts.length; k++) cum.push(cum[k - 1] + Math.hypot(s.pts[k][0] - s.pts[k - 1][0], s.pts[k][1] - s.pts[k - 1][1]));
    s.cum = cum; s.s0 = acc; s.len = cum[cum.length - 1];
    segs.push({ lift: false, stroke: i, s0: acc, s1: acc + s.len }); acc += s.len;
  });
  const total = acc;
  const inkCol = new THREE.Color(o.ink || '#3c4a7a'), glowCol = new THREE.Color(o.glow || '#b9f4ff');
  const tail = (o.glowTail ?? 1.6) * cap;
  const nibAt = p => {
    const s = Math.min(total, Math.max(0, p * total));
    let seg = segs.find(q => s >= q.s0 && s <= q.s1) || segs[segs.length - 1];
    let x, y, down;
    if (seg.lift) { const t = (s - seg.s0) / Math.max(1e-6, seg.s1 - seg.s0); x = seg.from[0] + (seg.to[0] - seg.from[0]) * t; y = seg.from[1] + (seg.to[1] - seg.from[1]) * t; down = false; }
    else { const st = strokes[seg.stroke], d = s - st.s0; let k = 1; while (k < st.cum.length - 1 && st.cum[k] < d) k++; const t = (d - st.cum[k - 1]) / Math.max(1e-6, st.cum[k] - st.cum[k - 1]);
      x = st.pts[k - 1][0] + (st.pts[k][0] - st.pts[k - 1][0]) * t; y = st.pts[k - 1][1] + (st.pts[k][1] - st.pts[k - 1][1]) * t; down = p > 0 && p < 1; }
    return { u: x / Wc, v: 1 - y / Hc, x, y, down, stroke: seg.lift ? -1 : seg.stroke, letter: seg.lift ? -1 : strokes[seg.stroke].letter };
  };
  const drawBg = () => {
    const bg = o.background;
    P.g.clearRect(0, 0, Wc, Hc);
    if (typeof bg === 'function') bg(P); else if (bg) paint.fill(P, bg);
    G.g.clearRect(0, 0, Wc, Hc); paint.fill(G, o.glowBackground || '#000000');
  };
  drawBg();
  const bgSnapshot = paint.canvas(Wc, Hc); bgSnapshot.g.drawImage(P.c, 0, 0);
  const texture = paint.texture(P, { wrap: 'clamp', anisotropy: 16 });
  const glowTexture = paint.texture(G, { wrap: 'clamp', anisotropy: 16 });
  const css = c => `rgb(${Math.round(c.r * 255)},${Math.round(c.g * 255)},${Math.round(c.b * 255)})`;
  const tmpC = new THREE.Color();
  function update(progress) {
    const sNow = Math.min(total, Math.max(0, progress * total));
    P.g.clearRect(0, 0, Wc, Hc); P.g.drawImage(bgSnapshot.c, 0, 0);
    paint.fill(G, o.glowBackground || '#000000');
    for (const g of [P.g, G.g]) { g.lineCap = 'round'; g.lineJoin = 'round'; }
    for (const st of strokes) {
      if (st.s0 >= sNow) break;
      for (let k = 1; k < st.pts.length; k++) {
        const sk = st.s0 + st.cum[k - 1]; if (sk >= sNow) break;
        const age = sNow - (st.s0 + st.cum[k]);
        const fresh = Math.max(0, 1 - age / tail);
        const press = 0.86 + 0.14 * Math.sin(st.cum[k] / cap * 3.1 + st.letter);
        tmpC.copy(inkCol).lerp(glowCol, fresh * fresh);
        let [ax, ay] = st.pts[k - 1], [bx, by] = st.pts[k];
        const remain = sNow - sk, segLen = st.cum[k] - st.cum[k - 1];
        if (remain < segLen) { const t = remain / segLen; bx = ax + (bx - ax) * t; by = ay + (by - ay) * t; }
        P.g.strokeStyle = css(tmpC); P.g.lineWidth = inkW * press;
        P.g.beginPath(); P.g.moveTo(ax, ay); P.g.lineTo(bx, by); P.g.stroke();
        if (fresh > 0) { G.g.strokeStyle = `rgba(${Math.round(glowCol.r * 255)},${Math.round(glowCol.g * 255)},${Math.round(glowCol.b * 255)},${fresh})`; G.g.lineWidth = inkW * press * 1.6; G.g.beginPath(); G.g.moveTo(ax, ay); G.g.lineTo(bx, by); G.g.stroke(); }
      }
    }
    texture.needsUpdate = true; glowTexture.needsUpdate = true;
    return nibAt(progress);
  }
  update(0);
  return { canvas: P, texture, glowCanvas: G, glowTexture, totalLength: total / cap, capHeightPx: cap, update, nibAt, strokes };
}
