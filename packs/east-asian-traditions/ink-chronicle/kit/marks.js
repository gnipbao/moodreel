// Ink Chronicle: the style's marks (STYLE §2), each taking any shape or region the film gives it, so a picture is made
// of the same stuff as the type: grit and stipple, a flat wash, rows of small waves, streaks, a bloom of light. None of
// them draws a particular thing; the film decides what they make.
import { SIZE, INK } from './tokens.js';
import { clamp, lerp, hash, noise1 } from './anim.js';
import { dots } from './type.js';

const [W, H] = SIZE;

function inside(poly, x, y) {                                   // even-odd test against a polygon [[x, y], ...]
  let c = false;
  for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
    const [xi, yi] = poly[i], [xj, yj] = poly[j];
    if ((yi > y) !== (yj > y) && x < (xj - xi) * (y - yi) / (yj - yi) + xi) c = !c;
  }
  return c;
}

// stipple: grit filling a polygon, denser and darker where `shade(x, y)` (0..1) says, the grains `size` px
export function stipple(g, poly, { n = 12000, size = [1.2, 2.6], shade = () => 0.5, col = INK.ink, alpha = [0.25, 0.95], seed = 181 } = {}) {
  const xs = poly.map(p => p[0]), ys = poly.map(p => p[1]);
  const x0 = Math.min(...xs), x1 = Math.max(...xs), y0 = Math.min(...ys), y1 = Math.max(...ys), pts = [];
  for (let i = 0; i < n; i++) {
    const x = lerp(x0, x1, hash(i, seed)), y = lerp(y0, y1, hash(i, seed + 1));
    if (!inside(poly, x, y)) continue;
    const s = clamp(shade(x, y));
    if (hash(i, seed + 2) > 0.25 + 0.75 * s) continue;            // the shade thins the grit as well as lightening it
    pts.push([x, y, lerp(size[0], size[1], hash(i, seed + 3)), lerp(alpha[0], alpha[1], s) * (0.7 + 0.3 * hash(i, seed + 4))]);
  }
  dots(g, pts, col);
}

// a wash: a flat field of ink with soft edges, the way a brush lays one down (`soft` px of blur at the edge)
export function wash(g, poly, { col = INK.ink, alpha = 0.25, soft = 6 } = {}) {
  g.save(); g.globalAlpha = alpha; g.fillStyle = col; if (soft) g.filter = `blur(${soft}px)`;
  g.beginPath(); poly.forEach(([x, y], i) => (i ? g.lineTo(x, y) : g.moveTo(x, y))); g.closePath(); g.fill();
  g.restore();
}

// waves: rows of small wave strokes across a band [y0, y1], crowded and fine at its top (the far edge), wider toward
// the viewer, their crests catching light, drifting toward the camera; `light` { x, half } lays a soft column of light
// on it whose crests glitter (a moon, a lamp, the sun)
export function waves(g, t, { y0 = 0.55 * H, y1 = H, rows = 72, drift = 0.6, crest = '196,192,184', alpha = 1, trough = '0,0,0', light = null, glint = 1 } = {}) {
  const sv = t * drift, ph = sv - Math.floor(sv), tw = Math.floor(t * 12), strokes = [[], [], [], []], troughs = [], glints = [[], []];
  for (let j = 0; j < rows; j++) {
    const row = j - Math.floor(sv), u = (j + ph) / rows, k = u * u, y = y0 + (y1 - y0) * k;
    const step = 5 + 64 * k, len = 7 + 78 * k, half = light ? light.half * (0.3 + 0.7 * k) : 0;
    for (let x0 = -len; x0 < W + len; x0 += step) {
      const x = x0 + (hash(row & 1023, Math.round(x0)) - 0.5) * step * 0.9;
      const n = noise1(x / (36 + 240 * k) + row * 3.17 + t * 0.5, (row % 11 + 11) % 11);
      if (light && Math.abs(x - light.x) < half && n > 0.1) { if (hash(row & 1023, Math.round(x0), tw) < 0.55) glints[n > 0.45 ? 1 : 0].push([x, y, len * (0.25 + 0.35 * n), 1 + 1.8 * k]); continue; }
      if (n > 0.2) strokes[Math.min(3, Math.floor((n - 0.2) * 5))].push([x, y, len * (0.4 + 0.6 * n), 1 + 2.4 * k]);
      else if (n < -0.35) troughs.push([x, y + 1 + 3 * k, len, 1 + 3 * k]);
    }
  }
  const draw = (list, colr) => { g.strokeStyle = colr; for (const [x, y, l, w] of list) { g.lineWidth = w; g.beginPath(); g.moveTo(x - l / 2, y); g.lineTo(x + l / 2, y); g.stroke(); } };
  draw(troughs, `rgba(${trough},${0.18 * alpha})`);   // on paper pass a dark crest and alpha 4-6: the marks are ink
  strokes.forEach((list, i) => draw(list, `rgba(${crest},${[0.04, 0.065, 0.09, 0.12][i] * alpha})`));
  if (light) {
    g.save(); g.filter = 'blur(6px)'; g.globalAlpha = 0.85 * glint; g.fillStyle = '#f6f2ea';
    g.beginPath(); g.moveTo(light.x - light.half * 0.15, y0); g.lineTo(light.x + light.half * 0.15, y0); g.lineTo(light.x + light.half * 0.5, y1); g.lineTo(light.x - light.half * 0.5, y1); g.closePath(); g.fill(); g.restore();
    draw(glints[0], `rgba(255,252,244,${0.35 * glint})`); draw(glints[1], `rgba(255,253,248,${0.75 * glint})`);
  }
}

// streaks: long thin strokes falling or flying at an angle (rain, sparks, speed), a few near the lens bigger and soft
export function streaks(g, t, { n = 400, angle = 0.12, speed = [2.4, 4.2], len = [45, 205], col = '230,228,224', alpha = [0.15, 0.5], width = [1.1, 2.7], seed = 521, a = 1 } = {}) {
  g.save(); g.lineCap = 'round';
  for (let i = 0; i < n; i++) {
    const v = lerp(speed[0], speed[1], hash(i, seed + 2)), l = lerp(len[0], len[1], hash(i, seed + 3) ** 1.5);
    const y = ((hash(i, seed + 1) + t * v) % 1.25) * H * 1.25 - 0.2 * H, x = hash(i, seed) * W * 1.2 - 0.1 * W + y * angle;
    g.strokeStyle = `rgba(${col},${a * lerp(alpha[0], alpha[1], hash(i, seed + 5))})`; g.lineWidth = lerp(width[0], width[1], hash(i, seed + 4) ** 2);
    g.beginPath(); g.moveTo(x, y); g.lineTo(x + l * angle, y + l); g.stroke();
  }
  g.restore();
}

// a bloom of light: the soft glow the style's bright things carry (white type on night, a lamp, a moon)
export function glow(g, x, y, r, { col = '255,248,236', a = 0.35, spread = 3 } = {}) {
  const gr = g.createRadialGradient(x, y, r * 0.2, x, y, r * spread);
  gr.addColorStop(0, `rgba(${col},${a})`); gr.addColorStop(1, `rgba(${col},0)`);
  g.fillStyle = gr; g.fillRect(x - r * spread, y - r * spread, 2 * r * spread, 2 * r * spread);
}
