// Painted marks: brush strokes, watercolour washes, palette-knife dabs, crayon and ink, and a repaint that turns a
// flat illustration into strokes. Every mark is a function of its points and a seed, so a frame repaints the same
// every time; cache what has finished painting (an offscreen canvas) and draw stroke by stroke only what is being
// painted. The numbers that `moodreel measure` reads from painted references (texture.json `brush`: stroke size,
// how much the strokes follow one direction, pooled edges) are the parameters here.
import { rng, noise1, hash } from './core.js';

// paper grain: a 2-D value noise in paper coordinates (the same tooth wherever a mark passes)
export const tooth = (x, y) => {
  const ix = Math.floor(x), iy = Math.floor(y), fx = x - ix, fy = y - iy;
  const h = (a, b) => hash(a * 57.31 + b * 131.7);
  const u = fx * fx * (3 - 2 * fx), v = fy * fy * (3 - 2 * fy);
  return (h(ix, iy) * (1 - u) + h(ix + 1, iy) * u) * (1 - v) + (h(ix, iy + 1) * (1 - u) + h(ix + 1, iy + 1) * u) * v;
};

// a shape's outline with its edges broken into short steps and pushed in and out by noise: a hand-made, wandering edge
export function wobble(polygon, { amount = 4, step = 8, seed = 1 } = {}) {
  const out = [];
  polygon.forEach((a, i) => {
    const b = polygon[(i + 1) % polygon.length], len = Math.hypot(b[0] - a[0], b[1] - a[1]), n = Math.max(1, Math.round(len / step));
    const nx = -(b[1] - a[1]) / (len || 1), ny = (b[0] - a[0]) / (len || 1);
    for (let k = 0; k < n; k++) {
      const u = k / n, d = amount * (2 * noise1(seed * 9.7 + (i * 31 + k) * 0.37) - 1);
      out.push([a[0] + (b[0] - a[0]) * u + nx * d, a[1] + (b[1] - a[1]) * u + ny * d]);
    }
  });
  return out;
}

// how wide a stroke is along its length (u from 0 at the start to 1 at the end)
export const PROFILES = {
  brush: u => Math.min(1, u * 6) * (1 - 0.55 * u),        // loaded at the start, running dry
  leaf: u => Math.sin(Math.PI * u),
  even: u => Math.min(1, u * 10, (1 - u) * 10),
  tip: u => Math.min(1, u * 10) * (1 - u * u),
  trunk: u => 1 - 0.6 * u,
};

const lerpPt = (a, b, u) => [a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u];

// a smooth path through the points (Catmull-Rom), n samples
export function spine(points, n = 48) {
  if (points.length < 2) return points.slice();
  const out = [], P = [points[0], ...points, points[points.length - 1]];
  for (let k = 0; k < n; k++) {
    const s = (k / (n - 1)) * (points.length - 1), i = Math.min(Math.floor(s), points.length - 2), u = s - i;
    const [p0, p1, p2, p3] = [P[i], P[i + 1], P[i + 2], P[i + 3]];
    out.push([0, 1].map(d => 0.5 * ((2 * p1[d]) + (-p0[d] + p2[d]) * u + (2 * p0[d] - 5 * p1[d] + 4 * p2[d] - p3[d]) * u * u
      + (-p0[d] + 3 * p1[d] - 3 * p2[d] + p3[d]) * u * u * u)));
  }
  return out;
}

// the outline of a stroke along `points`: its width follows the profile, its edges are roughened by value noise
export function ribbon(points, { width = 12, profile = 'brush', rough = 0.22, seed = 1, n = 48 } = {}) {
  const sp = spine(points, n), prof = PROFILES[profile] || PROFILES.brush, left = [], right = [];
  sp.forEach((p, k) => {
    const q = sp[Math.min(k + 1, n - 1)], o = sp[Math.max(k - 1, 0)];
    const dx = q[0] - o[0], dy = q[1] - o[1], len = Math.hypot(dx, dy) || 1, u = k / (n - 1);
    const w = (width / 2) * prof(u);
    const wl = w * (1 + rough * (2 * noise1(seed * 7.1 + k * 0.45) - 1)), wr = w * (1 + rough * (2 * noise1(seed * 3.3 + k * 0.45 + 50) - 1));
    left.push([p[0] - (dy / len) * wl, p[1] + (dx / len) * wl]);
    right.push([p[0] + (dy / len) * wr, p[1] - (dx / len) * wr]);
  });
  return [...left, ...right.reverse()];
}

const fillPoly = (g, poly) => {
  g.beginPath();
  poly.forEach(([x, y], i) => (i ? g.lineTo(x, y) : g.moveTo(x, y)));
  g.closePath();
  g.fill();
};

// a brush stroke: a thin body wash plus bristle traces running along it, darker where the hairs drag
export function stroke(g, points, { color = '#222', alpha = 0.6, width = 12, profile = 'brush', rough = 0.22, bristles = 5,
  seed = 1, reveal = 1 } = {}) {
  const r = rng(seed), n = 48, cut = Math.max(2, Math.round(n * Math.min(1, reveal)));   // reveal: painted so far
  const sp = spine(points, n).slice(0, cut);
  if (sp.length < 2) return;
  g.save();
  g.fillStyle = color;
  g.globalAlpha = alpha;
  fillPoly(g, ribbon(sp, { width, profile, rough, seed, n: sp.length }));
  g.strokeStyle = color;
  g.lineCap = 'round';
  for (let b = 0; b < bristles; b++) {                    // each hair: an offset across the width, its own wobble
    const off = (r() * 2 - 1) * 0.42 * width, lw = 0.6 + r() * 1.6;
    g.globalAlpha = alpha * (0.35 + 0.5 * r());
    g.lineWidth = lw;
    g.beginPath();
    sp.forEach((p, k) => {
      const q = sp[Math.min(k + 1, sp.length - 1)], o = sp[Math.max(k - 1, 0)];
      const dx = q[0] - o[0], dy = q[1] - o[1], len = Math.hypot(dx, dy) || 1;
      const w = off * PROFILES[profile](k / (n - 1)) * (1 + 0.15 * (noise1(seed + b * 13 + k * 0.3) - 0.5));
      const x = p[0] - (dy / len) * w, y = p[1] + (dx / len) * w;
      k ? g.lineTo(x, y) : g.moveTo(x, y);
    });
    g.stroke();
  }
  g.restore();
}

// a watercolour wash: the shape painted in `passes` jittered passes, so the edges, where the passes disagree, pool
// darker than the middle; `bloom` adds a soft back-run inside
export function wash(g, polygon, { color = '#4a7fa5', alpha = 0.35, passes = 3, jitter = 3, pool = 0.6, seed = 1 } = {}) {
  g.save();
  g.fillStyle = color;
  g.strokeStyle = color;
  g.lineJoin = 'round';
  for (let p = 0; p < passes; p++) {                      // each pass wanders its own way, by up to 2.5 x jitter
    const poly = wobble(polygon, { amount: jitter * 2.5, step: 6 + 2 * p, seed: seed * 17 + p });
    g.globalAlpha = alpha / passes;
    fillPoly(g, poly);
    g.globalAlpha = (alpha / passes) * pool;             // pigment pooling at the drying edge
    g.lineWidth = 1 + jitter * 0.6;
    g.stroke();
  }
  g.restore();
}

// a palette-knife dab: longer than wide, slanted ends, the value jittered; relief lights its upper edge and shades its
// lower one (light from the upper left)
export function dab(g, x, y, r, angle, color, { long = 2.2, wide = 1.15, slant = 0.35, jitter = 0.06, relief = 0.22,
  seed = 1 } = {}) {
  const R = rng(seed), L = r * long * (0.85 + 0.3 * R()), Wd = r * wide * (0.85 + 0.3 * R());
  const a = angle + (R() * 2 - 1) * 0.23, ca = Math.cos(a), sa = Math.sin(a);
  const pts = [[-L / 2 + slant * Wd, -Wd / 2], [L / 2, -Wd / 2], [L / 2 - slant * Wd, Wd / 2], [-L / 2, Wd / 2]]
    .map(([u, v]) => [x + u * ca - v * sa, y + u * sa + v * ca]);
  const k = 1 + (R() * 2 - 1) * jitter;
  const c = color.match(/\w\w/g).map(h => Math.max(0, Math.min(255, Math.round(parseInt(h, 16) * k))));
  g.save();
  g.fillStyle = `rgb(${c[0]},${c[1]},${c[2]})`;
  fillPoly(g, pts);
  if (relief > 0) {
    g.lineWidth = Math.max(1, r * 0.12);
    g.globalAlpha = relief;
    g.strokeStyle = '#ffffff';
    g.beginPath(); g.moveTo(...pts[0]); g.lineTo(...pts[1]); g.stroke();
    g.strokeStyle = '#000000';
    g.beginPath(); g.moveTo(...pts[2]); g.lineTo(...pts[3]); g.stroke();
  }
  g.restore();
}

// crayon or dry brush: many short strokes along the path, broken where the paper's tooth stands up
export function crayon(g, points, { color = '#c0392b', width = 8, tooth: grit = 0.45, alpha = 0.85, grain = 2.2, seed = 1 } = {}) {
  const r = rng(seed), length = points.slice(1).reduce((L, p, i) => L + Math.hypot(p[0] - points[i][0], p[1] - points[i][1]), 0);
  const sp = spine(points, Math.max(8, Math.round(length / 1.5)));    // steps of about 1.5 px: the wax lays in specks
  g.save();
  g.fillStyle = color;
  for (let k = 0; k < sp.length - 1; k++) {
    const [x0, y0] = sp[k], [x1, y1] = sp[k + 1];
    const dx = x1 - x0, dy = y1 - y0, len = Math.hypot(dx, dy) || 1;
    const edge = width / 2 * (0.85 + 0.3 * noise1(seed + k * 0.05));  // the crayon's own wavering edge
    for (let off = -edge; off < edge; off += 1) {
      const x = x0 + (-dy / len) * off, y = y0 + (dx / len) * off;
      // wax catches the paper's peaks and skips its valleys; pressing harder (the middle) fills more of them
      const press = 1 - Math.abs(off) / edge;
      if (tooth(x / grain, y / grain) < grit * (1.15 - 0.5 * press)) continue;
      g.globalAlpha = alpha * (0.55 + 0.45 * r());
      g.fillRect(x, y, 1.4, 1.4);
    }
  }
  g.restore();
}

// ink: a brush stroke whose wet edge bleeds into the paper (a soft halo under a crisp body)
export function ink(g, points, { color = '#141414', width = 10, wet = 0.5, profile = 'tip', seed = 1, reveal = 1 } = {}) {
  g.save();
  if (wet > 0) {
    g.shadowColor = color;
    g.shadowBlur = width * 1.2 * wet;
    stroke(g, points, { color, alpha: 0.25 * wet, width: width * 1.25, profile, rough: 0.35, bristles: 0, seed, reveal });
    g.shadowBlur = 0;
  }
  stroke(g, points, { color, alpha: 0.9, width, profile, rough: 0.2, bristles: 3, seed: seed + 1, reveal });
  g.restore();
}

const cache = new Map();

// a flat illustration (a canvas drawn with plain shapes) repainted as knife dabs or brush strokes: coarse dabs over
// the large planes, finer ones where the plate changes (its edges), each laid along the edge it sits on and in the
// plate's colour there. Repainted once per (plate, options) and cached: a static plate costs nothing per frame.
export function repaint(plate, { key, cell = 14, fine = 6, mark = 'dab', seed = 1, angle = 0.35 } = {}) {
  const id = key && `${key}:${cell}:${fine}:${mark}:${seed}:${angle}`;
  if (id && cache.has(id)) return cache.get(id);
  const w = plate.width, h = plate.height, src = plate.getContext('2d').getImageData(0, 0, w, h).data;
  const out = document.createElement('canvas');
  out.width = w;
  out.height = h;
  const g = out.getContext('2d'), R = rng(seed);
  g.filter = 'blur(1.5px)';                                // a thin underpainting, so no canvas shows between marks
  g.drawImage(plate, 0, 0);
  g.filter = 'none';
  const at = (x, y) => {
    const i = 4 * (Math.min(h - 1, Math.max(0, Math.round(y))) * w + Math.min(w - 1, Math.max(0, Math.round(x))));
    return [src[i], src[i + 1], src[i + 2]];
  };
  const lum = (x, y) => { const c = at(x, y); return 0.3 * c[0] + 0.59 * c[1] + 0.11 * c[2]; };
  const hex = c => '#' + c.map(v => v.toString(16).padStart(2, '0')).join('');
  for (const size of [cell, fine]) {                       // coarse to fine
    for (let y = size / 2; y < h; y += size * 0.8) {
      for (let x = size / 2; x < w; x += size * 0.8) {
        const px = x + (R() - 0.5) * size * 0.6, py = y + (R() - 0.5) * size * 0.6;
        const gx = lum(px + size / 2, py) - lum(px - size / 2, py), gy = lum(px, py + size / 2) - lum(px, py - size / 2);
        const edge = Math.hypot(gx, gy);
        if (size === fine && edge < 12) continue;          // fine marks only along edges
        if (size === cell && edge >= 40 && R() < 0.5) continue;
        const a = edge > 8 ? Math.atan2(gy, gx) + Math.PI / 2 : angle;   // along the edge; else the plate's own slant
        const c = hex(at(px, py));
        if (mark === 'dab') dab(g, px, py, size * 0.55, a, c, { seed: seed + Math.round(px * 7 + py * 13) });
        else stroke(g, [[px - Math.cos(a) * size, py - Math.sin(a) * size], [px + Math.cos(a) * size, py + Math.sin(a) * size]],
          { color: c, alpha: 0.85, width: size * 0.9, profile: 'leaf', bristles: 3, seed: seed + Math.round(px * 7 + py * 13) });
      }
    }
  }
  if (id) cache.set(id, out);
  return out;
}
