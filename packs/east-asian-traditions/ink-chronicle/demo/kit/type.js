// Ink Chronicle: type as matter (STYLE §1, §2, §5). Typing a character at a time, the slam (a word arriving at about
// twice its size, full on its first frame, settling in a few frames, its colours split on a dark ground), text turned to
// points for grit, specks laid over a glyph, a word shattering, a line jumbling, rows of a line trembling, and a field
// of type filling any region. Every function takes t and draws the whole state at t; none of them is a scene.
import { SIZE, INK } from './tokens.js';
import { clamp, lerp, smoothstep, ease, hash, keys } from './anim.js';
import { SONG, KAI, MONO, font } from './faces.js';
import { canvas } from './paper.js';

const [W, H] = SIZE;

// text: each character appears at its own time (from t0, `cps` a second, or `at` times), fading in over `fade` s;
// laid out horizontally or down a column, the whole line placed by `align` so it doesn't move while it is typed
export function layout(text, size, { vertical = false, gap = 1.0, g = null, fontStr = null } = {}) {
  const ch = [...text], out = [];
  let x = 0;
  for (const c of ch) {
    const w = vertical ? size : g ? (g.font = fontStr, g.measureText(c).width) : size;
    out.push({ c, x: vertical ? 0 : x, y: vertical ? x : 0, w });
    x += (vertical ? size : w) * gap;
  }
  return { chars: out, length: x };
}

export function typed(g, text, x, y, t, t0, { cps = 6, at = null, size = 40, weight = 400, fam = SONG, color = INK.ink, vertical = false,
  gap = 1.0, align = 'left', fade = 0.12, alpha = 1, rise = 0.15, blur = 0, out = null, slam: s0 = 0, sdur = 0.1, split = 0 } = {}) {
  const f = font(weight, size, fam);
  g.save(); g.font = f; g.fillStyle = color; g.textBaseline = vertical ? 'top' : 'alphabetic'; g.textAlign = 'left';
  const L = layout(text, size, { vertical, gap, g, fontStr: f });
  const off = align === 'center' ? -L.length / 2 : align === 'right' ? -L.length : 0;
  L.chars.forEach((c, i) => {
    const ti = at ? at[i] : t0 + i / cps;
    if (t < ti) return;
    let a = s0 ? alpha : clamp((t - ti) / fade) * alpha;            // a slam is there at once, at full size
    if (out) a *= 1 - clamp((t - out[0] - i * (out[2] ?? 0)) / out[1]);
    if (a <= 0) return;
    const u = clamp((t - ti) / fade), dy = s0 ? 0 : (1 - u) * size * rise;
    const px = vertical ? x - size / 2 : x + off + c.x, py = vertical ? y + off + c.y + dy : y + dy;
    g.globalAlpha = a;
    if (blur > 0 && !s0) g.filter = `blur(${(1 - u) * blur}px)`;
    if (s0) {                                   // landing: s0 times the size, settling in sdur s, its colours split on impact
      const s = slam(t, ti, s0, sdur), cx = vertical ? x : px + c.w / 2, cy = vertical ? py + size / 2 : py - size * 0.38;
      g.save(); g.translate(cx, cy); g.scale(s, s); g.translate(-cx, -cy);
      if (split && s > 1.002) {
        const d = split * (s - 1) / (s0 - 1);
        g.save(); g.globalCompositeOperation = 'screen';
        g.fillStyle = '#ff2b2b'; g.fillText(c.c, px - d, py); g.fillStyle = '#22e8ff'; g.fillText(c.c, px + d, py);
        g.restore();
      }
      g.fillText(c.c, px, py);
      g.restore();
    } else g.fillText(c.c, px, py);
  });
  g.restore();
  return L;
}

// a character landing: s0 times its size at ti, settling in dur s (the reference's lines land in three frames)
export function slam(t, ti, s0 = 2.2, dur = 0.1) { const u = clamp((t - ti) / dur); return 1 + (s0 - 1) * (1 - u) ** 3; }

// the points of a text's ink (in design px about its centre), every `step` px
export function textPoints(text, size, { weight = 900, fam = SONG, vertical = false, gap = 1.0, step = 4, max = 6000 } = {}) {
  const n = [...text].length, w = vertical ? size * 1.4 : size * n * gap * 1.2 + size, h = vertical ? size * n * gap * 1.1 + size : size * 1.6;
  const [c, g] = canvas(Math.ceil(w), Math.ceil(h));
  g.fillStyle = '#000'; g.font = font(weight, size, fam); g.textBaseline = 'middle'; g.textAlign = 'center';
  if (vertical) [...text].forEach((ch, i) => g.fillText(ch, w / 2, size * 0.7 + i * size * gap));
  else g.fillText(text, w / 2, h / 2);
  const d = g.getImageData(0, 0, c.width, c.height).data, pts = [];
  for (let y = 0; y < c.height; y += step) for (let x = 0; x < c.width; x += step) if (d[(y * c.width + x) * 4 + 3] > 128) pts.push([x - w / 2, y - (vertical ? size * 0.7 + (n - 1) * size * gap / 2 : h / 2)]);
  if (pts.length > max) { const k = pts.length / max; return Array.from({ length: max }, (_, i) => pts[Math.floor(i * k)]); }
  return pts;
}

// a dot cloud drawn with one colour: pts [[x, y, r, a], ...]
export function dots(g, pts, col) {
  g.fillStyle = col;
  for (const [x, y, r, a] of pts) {
    if (a <= 0.01) continue;
    g.globalAlpha = Math.min(1, a);
    if (r > 2.2) { g.beginPath(); g.arc(x, y, r / 2, 0, 6.2832); g.fill(); } else g.fillRect(x - r / 2, y - r / 2, r, r);
  }
  g.globalAlpha = 1;
}

// a normal deviate from two hashes (for clouds of grit that are dense in the middle)
export const gauss = (i, seed) => Math.sqrt(-2 * Math.log(Math.max(1e-6, hash(i, seed)))) * Math.cos(6.2832 * hash(i, seed + 1));

// specks over what is already drawn on a layer, and only there (ink that is grit, not a flat fill)
export function speckle(g, w, h, n, col, seed = 0, size = 2) {
  g.save(); g.globalCompositeOperation = 'source-atop'; g.fillStyle = col;
  for (let i = 0; i < n; i++) { const s = size * (0.5 + hash(i, seed + 2)); g.globalAlpha = 0.45 + 0.55 * hash(i, seed + 3); g.fillRect(hash(i, seed) * w, hash(i, seed + 1) * h, s, s); }
  g.restore();
}

// an ink splash: blots and specks round a point, grown by u (0..1)
export function splash(g, x, y, u, seed, { n = 160, r = 160, col = INK.ink } = {}) {
  g.fillStyle = col;
  for (let i = 0; i < n; i++) {
    const a = hash(i, seed) * Math.PI * 2, d = r * Math.pow(hash(i, seed + 1), 1.6) * (0.4 + 0.6 * u), s = (1 + hash(i, seed + 2) * 7) * (1 - 0.5 * hash(i, seed + 3) * u);
    g.globalAlpha = clamp(u * 3) * (0.5 + 0.5 * hash(i, seed + 4));
    g.beginPath(); g.arc(x + Math.cos(a) * d, y + Math.sin(a) * d * 0.7, s, 0, Math.PI * 2); g.fill();
  }
  g.globalAlpha = 1;
}

const SHARDS = {};

export function shards(ch, size, color = INK.white) {
  const key = ch + size + color;
  if (SHARDS[key]) return SHARDS[key];
  const n = Math.ceil(size * 1.3), [c, q] = canvas(n, n);
  q.font = font(900, size, SONG); q.fillStyle = color; q.textAlign = 'center'; q.textBaseline = 'middle'; q.fillText(ch, n / 2, n / 2 + size * 0.04);
  const h = n / 2, split = (poly, px, py, nx, ny) => {                // a convex polygon either side of a line
    const a = [], b = [];
    poly.forEach((p, i) => {
      const r = poly[(i + 1) % poly.length], sp = (p[0] - px) * nx + (p[1] - py) * ny, sr = (r[0] - px) * nx + (r[1] - py) * ny;
      (sp >= 0 ? a : b).push(p);
      if ((sp >= 0) !== (sr >= 0)) { const k = sp / (sp - sr); const m = [p[0] + (r[0] - p[0]) * k, p[1] + (r[1] - p[1]) * k]; a.push(m); b.push(m); }
    });
    return [a, b].filter(x => x.length >= 3);
  };
  let polys = [[[-h, -h], [h, -h], [h, h], [-h, h]]];
  const seed = ch.codePointAt(0) % 97;
  for (let k = 0; k < 4; k++) {
    const ang = (hash(k, 321 + seed) - 0.5) * 2.4 + (k % 2 ? 1.57 : 0.6), px = (hash(k, 322 + seed) - 0.5) * size * 0.6, py = (hash(k, 323 + seed) - 0.5) * size * 0.6;
    polys = polys.flatMap(P => split(P, px, py, Math.cos(ang), Math.sin(ang)));
  }
  return (SHARDS[key] = { img: c, n, polys: polys.map(P => ({ P, cx: P.reduce((s, p) => s + p[0], 0) / P.length, cy: P.reduce((s, p) => s + p[1], 0) / P.length })) });
}

export function shatter(g, text, x, y, size, t, t0, { fade = [t0 + 0.6, t0 + 0.9], color = INK.white, gravity = 4600 } = {}) {
  const ch = [...text], a = 1 - smoothstep(fade[0], fade[1], t);
  if (a <= 0) return;
  ch.forEach((c, i) => {
    const S = shards(c, size, color), gx = x + (i - (ch.length - 1) / 2) * size;
    S.polys.forEach(({ P, cx, cy }, k) => {
      const tau = Math.max(0, t - t0 - 0.04 * hash(k, 331 + i)), vx = (cx / size) * 520 + (hash(k, 332 + i) - 0.5) * 160, vy = -30 - 60 * hash(k, 333 + i);
      const pop = t >= t0 ? 1 : 0, dx = vx * tau + Math.sign(cx || 1) * 12 * pop, dy = vy * tau + 0.5 * gravity * tau * tau + 8 * pop, rot = (hash(k, 334 + i) - 0.5) * (9 * tau + 0.12 * pop);   // the crack opens at once
      g.save(); g.globalAlpha = a; g.translate(gx + cx + dx, y + cy + dy); g.rotate(rot); g.translate(-cx, -cy);
      g.beginPath(); P.forEach(([px, py], j) => (j ? g.lineTo(px, py) : g.moveTo(px, py))); g.closePath(); g.clip();
      g.drawImage(S.img, -S.n / 2, -S.n / 2); g.restore();
    });
  });
}

// a line that loses its hold: it tilts and its characters turn and slip against each other, in place (the
// reference at 60.65-60.95 s)
export function jumble(g, text, x, y, size, t, t0, { tilt = -0.14, box = 0, color = INK.white, weight = 900, fam = SONG } = {}) {
  const ch = [...text], u = ease.outCubic(clamp((t - t0) / 0.3));
  g.save(); g.translate(x, y); g.rotate(tilt * u);
  if (box) { g.save(); g.globalAlpha = box; g.strokeStyle = color; g.lineWidth = 2.5; g.strokeRect(-ch.length * size / 2 - 20, -size * 0.96, ch.length * size + 40, size * 1.24); g.restore(); }
  g.font = font(weight, size, fam); g.fillStyle = color; g.textAlign = 'center'; g.textBaseline = 'alphabetic';
  ch.forEach((c, i) => {
    const r = (hash(i, 311 + ch.length) - 0.5) * 1.1 * u, dx = (hash(i, 312 + ch.length) - 0.5) * 70 * u, dy = (hash(i, 313 + ch.length) - 0.5) * 80 * u;
    g.save(); g.translate((i - (ch.length - 1) / 2) * size + dx, dy); g.rotate(r); g.fillText(c, 0, 0); g.restore();
  });
  g.restore();
}

// rows of a repeated line filling the frame from the top, one every `every` s, each trembling sideways frame by frame
// (anxiety as motion, not as text)
export function rows(g, text, t, t0, { every = 0.04, size = 49, gap = 71, color = '#6c6864', weight = 500, fam = SONG, tremble = 120, alpha = 0.85, out = null, count = 16, y0 = 40 } = {}) {
  if (t < t0) return;
  const a = out ? 1 - smoothstep(out[0], out[1], t) : 1;
  g.save(); g.fillStyle = color; g.font = font(weight, size, fam); g.textBaseline = 'alphabetic';
  for (let r = 0; r < count; r++) {
    const ra = a * clamp((t - t0 - r * every) / 0.05); if (ra <= 0) continue;
    const jx = (hash(r, Math.floor(t * 30), 7) - 0.5) * tremble;
    g.globalAlpha = ra * alpha; g.fillText(text.repeat(Math.ceil(W / (size * [...text].length)) + 2), -((r * 173) % (size * 7)) - size * 2 + jx, y0 + r * gap);
  }
  g.restore();
}

// a field of type: a region (a rectangle, or any polygon) filled with the film's own characters in runs of its text,
// cell by cell as `dens` rises (a cell's type is set once, so a denser field keeps the earlier), more cells boxed white
// on black as `boxed` rises (dark fields where they join). `dens` and `boxed` are keys over t - t0 ([[s, value], ...]),
// or plain numbers. Options: `pull` (keys of a camera scale about the frame's centre), `keys` (a handful of large keys
// landing every `keyEvery` s), `name` (a boxed word kept clear in the middle). A page of type, a word made of type, a
// map or a mountain filled with it: the field is a material, the film decides its shape.
export function typeField(g, t, { corpus, t0 = 0, region = [0, 0, W, H], shape = null, cell = 42, dens = 1, boxed = 0, pull = null,
  keyCount = 0, keyEvery = 0.1, keySize = 120, name = null, ground = null, inkCol = '#141210', boxCol = '#0e0d0c', boxInk = '#e9e6e1' } = {}) {
  const chars = [...corpus], u = t - t0, val = v => (Array.isArray(v) ? keys(u, v) : v);
  const s = pull ? keys(u, pull) : 1, d = val(dens), b = val(boxed), [rx, ry, rw, rh] = region;
  if (ground) { g.fillStyle = ground; g.fillRect(rx, ry, rw, rh); }
  const inPoly = (x, y) => { let c = false; for (let i = 0, j = shape.length - 1; i < shape.length; j = i++) { const [xi, yi] = shape[i], [xj, yj] = shape[j]; if ((yi > y) !== (yj > y) && x < (xj - xi) * (y - yi) / (yj - yi) + xi) c = !c; } return c; };
  g.save(); g.translate(W / 2, H / 2); g.scale(s, s); g.translate(-W / 2, -H / 2);
  g.textAlign = 'center'; g.textBaseline = 'middle';
  const cols = Math.ceil(rw / cell) + 1, rowsN = Math.ceil(rh / cell) + 1;
  for (let j = 0; j < rowsN; j++) for (let i = 0; i < cols; i++) {
    const k = j * 97 + i, x = rx + i * cell, y = ry + j * cell, cx = x + cell / 2, cy = y + cell / 2;
    if ((x + cell - W / 2) * s + W / 2 < 0 || (x - W / 2) * s + W / 2 > W || (y + cell - H / 2) * s + H / 2 < 0 || (y - H / 2) * s + H / 2 > H) continue;
    if (shape && !inPoly(cx, cy)) continue;
    if (name && Math.abs(cx - W / 2) < cell * 1.6 && Math.abs(cy - H / 2) < cell * 0.8) continue;
    if (hash(k, 41) > d) continue;
    const ch = chars[(j * 23 + i + 1000) % chars.length];
    if (hash(k, 43) < b) { g.fillStyle = boxCol; g.fillRect(x - 0.5, y - 0.5, cell + 1, cell + 1); g.fillStyle = boxInk; g.font = font(700, cell * 0.67, SONG); g.fillText(ch, cx, cy + 1); }
    else { g.fillStyle = inkCol; g.font = font(900, cell * 0.74, SONG); g.fillText(ch, cx, cy + 1); }
  }
  if (name) { g.fillStyle = boxCol; g.font = font(900, 48, SONG); const nw = g.measureText(name).width + 36; g.fillRect(W / 2 - nw / 2, H / 2 - 34, nw, 68); g.fillStyle = '#f2f0ec'; g.fillText(name, W / 2, H / 2 + 2); }
  g.restore();
  if (!keyCount || u < 0.07) return;
  const n = Math.floor((u - 0.07) / keyEvery), tb = t0 + 0.07 + n * keyEvery;   // the keys: a new handful lands every keyEvery s
  for (let q = 0; q < keyCount; q++) {
    const h = n * 7 + q, sz = (keySize - keySize / 3 * clamp(u / 1.4)) * (0.8 + 0.5 * hash(h, 404));
    const x = rx + (0.06 + 0.88 * hash(h, 402)) * rw, y = ry + (0.08 + 0.84 * hash(h, 403)) * rh;
    if (shape && !inPoly(x, y)) continue;
    const k = slam(t, tb, 1.5, 0.05);
    g.save(); g.translate(x, y); g.scale(k, k); g.shadowColor = 'rgba(10,9,8,0.75)'; g.shadowBlur = 26 * k;
    g.fillStyle = boxCol; g.fillRect(-sz * 0.6, -sz * 0.6, sz * 1.2, sz * 1.2); g.shadowBlur = 0;
    g.fillStyle = '#f2f0ec'; g.font = font(900, sz, SONG); g.textAlign = 'center'; g.textBaseline = 'middle';
    g.fillText(chars[(h * 13 + 5) % chars.length], 0, sz * 0.04); g.restore();
  }
}
