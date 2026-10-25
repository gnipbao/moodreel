// The tracker: a word read by a machine. Each glyph in a thin box (red, 2.5 px) with its coordinates above it in the
// mono, a green dot on its centre, a dashed path with arrowheads through the centres; and the glyph broken into square
// cells (16 px with 2 px gaps on the year; dot-matrix words are the cell pass's `dots` mode instead).
//
//   import { along, track, path } from './kit/tracker.js';
//   const G = along(q, 'Tidepool', voice(300, 600), (i, n) => [300 + i * 190, 560 + Math.sin(i) * 40, -0.05 * i]);
//   path(q, G.map(g => [g.x, g.y - g.px * 0.25]), { from: [100, 620] });
//   track(q, G, { broken: i => t > 1.2 + i * 0.02 });
import { GLITCH } from './tokens.js';
import { machine } from './glitch.js';

const hash = (n, k = 0) => { const x = Math.sin(n * 127.1 + k * 311.7) * 43758.5453; return x - Math.floor(x); };

// lay a word out glyph by glyph: place(i, n, glyph) -> [x, y, rot] for each glyph's centre (y is its middle);
// returns [{ ch, w, x, y, rot, font, px }] (spaces are kept, with no box)
export function along(q, text, font, place) {
  q.save(); q.font = font;
  const px = parseFloat(font.match(/(\d+(\.\d+)?)px/)[1]);
  const out = [...text].map((ch, i, all) => {
    const [x, y, rot = 0] = place(i, all.length, ch);
    return { ch, w: q.measureText(ch).width, x, y, rot, font, px };
  });
  q.restore();
  return out;
}

// draw the glyphs with their boxes, labels and dots. broken(i) says which glyphs show as cells; label(g, i) its text
export function track(q, glyphs, { color = GLITCH.track.red, ink = '#fff', broken = () => false, cell = 16, gap = 2,
  labels = true, dots = true, label = (g, i) => `x: ${Math.round(g.x)}   y: ${Math.round(g.y)}`, labelPx = 30 } = {}) {
  glyphs.forEach((g, i) => {
    if (g.ch === ' ') return;
    q.save();
    q.translate(g.x, g.y); q.rotate(g.rot);
    // the dot on the glyph's middle, its baseline 0.36 em below, the box a little past the cap height and baseline
    const bw = g.w + 24, top = -0.52 * g.px, bottom = 0.48 * g.px, base = 0.36 * g.px;
    q.strokeStyle = color; q.lineWidth = 2.5;
    q.strokeRect(-bw / 2, top, bw, bottom - top);
    if (labels) { q.font = machine(labelPx); q.fillStyle = ink; q.fillText(label(g, i), -bw / 2, top - 16); }
    if (broken(i)) glyphCells(q, g.ch, g.font, -g.w / 2, base, cell, { gap, seed: i, color: ink });
    else { q.font = g.font; q.fillStyle = ink; q.fillText(g.ch, -g.w / 2, base); }
    if (dots) { q.fillStyle = GLITCH.track.dot; q.beginPath(); q.arc(0, 0, Math.max(5, g.px * 0.02), 0, Math.PI * 2); q.fill(); }
    q.restore();
  });
}

// a dashed path through points (a smooth curve), arrowheads every `every` points
export function path(q, points, { color = 'rgba(255,255,255,0.75)', dash = [10, 10], width = 2, arrows = true, every = 2 } = {}) {
  if (points.length < 2) return;
  q.save(); q.strokeStyle = color; q.fillStyle = color; q.lineWidth = width; q.setLineDash(dash);
  q.beginPath(); q.moveTo(...points[0]);
  for (let i = 1; i < points.length; i++) {
    const [x0, y0] = points[i - 1], [x1, y1] = points[i];
    q.quadraticCurveTo(x0 + (x1 - x0) * 0.5, y0, x1, y1);
  }
  q.stroke(); q.setLineDash([]);
  if (arrows) for (let i = 1; i < points.length; i += every) {
    const [x0, y0] = points[i - 1], [x1, y1] = points[i], a = Math.atan2(y1 - y0, x1 - x0), mx = (x0 + x1) / 2, my = (y0 + y1) / 2;
    q.save(); q.translate(mx, my); q.rotate(a);
    q.beginPath(); q.moveTo(7, 0); q.lineTo(-5, -5); q.lineTo(-5, 5); q.closePath(); q.fill(); q.restore();
  }
  q.restore();
}

// a box round a region with its label: what the tracker draws on a card, a mark or a word it follows
// (label: its text, by default its centre's coordinates; false for none)
export function box(q, x0, y0, x1, y1, { color = GLITCH.track.cyan, label, labelPx = 17, ink = 'rgba(70,170,190,0.95)' } = {}) {
  q.save(); q.strokeStyle = color; q.lineWidth = 2; q.strokeRect(x0, y0, x1 - x0, y1 - y0);
  if (label !== false) { q.font = machine(labelPx); q.fillStyle = ink; q.fillText(label ?? `x: ${Math.round((x0 + x1) / 2)}  y: ${Math.round((y0 + y1) / 2)}`, x0, y0 - 10); }
  q.restore();
}

// a glyph sampled on a grid: its lit cells as squares (the type breaking into cells). share < 1 drops some cells
const masks = new Map();
export function glyphCells(q, ch, font, x, y, cell, { color = '#fff', gap = 2, share = 1, seed = 0 } = {}) {
  const key = `${ch}|${font}|${cell}`;
  if (!masks.has(key)) {
    const c = document.createElement('canvas'), m = c.getContext('2d');
    m.font = font;
    const w = Math.ceil(m.measureText(ch).width) + 20, h = Math.ceil(parseFloat(font.match(/(\d+(\.\d+)?)px/)[1]) * 1.3);
    c.width = w; c.height = h;
    m.font = font; m.fillStyle = '#fff'; m.textBaseline = 'alphabetic';
    m.fillText(ch, 10, h * 0.8);
    const d = m.getImageData(0, 0, w, h).data, on = [];
    for (let gy = 0; gy < h; gy += cell) for (let gx = 0; gx < w; gx += cell) {
      const cx = Math.min(w - 1, Math.floor(gx + cell / 2)), cy = Math.min(h - 1, Math.floor(gy + cell / 2));
      if (d[(cy * w + cx) * 4] > 110) on.push([gx - 10, gy - h * 0.8]);
    }
    masks.set(key, on);
  }
  q.fillStyle = color;
  masks.get(key).forEach(([gx, gy], i) => {
    if (hash(i, seed) > share) return;
    q.fillRect(x + gx + gap / 2, y + gy + gap / 2, cell - gap, cell - gap);
  });
}
