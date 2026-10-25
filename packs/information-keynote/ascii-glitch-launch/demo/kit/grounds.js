// Grounds and light: the light studio (drawn from a measured 16 x 9 light map with its fine row texture), the dark
// ground with the screen-door dither, the lens's elliptical light over a look, a light card's clipped halo, and the end
// card's ground (a clean disc, line glyphs darkening toward the corners).
//
//   import { studio, dark, lens, halo, glyphGround } from './kit/grounds.js';
//   studio(q);                                       // the measured studio light
//   dark(q);                                         // near-black with the dither
//   lens(q, GLITCH.lens);                            // after drawing a light look: its ellipse of light
import { SIZE, GLITCH } from './tokens.js';

const [W, H] = SIZE;
const hash = (n, k = 0) => { const x = Math.sin(n * 127.1 + k * 311.7) * 43758.5453; return x - Math.floor(x); };
const canvas = (w, h) => { const c = document.createElement('canvas'); c.width = w; c.height = h; return c; };
const smooth = u => { u = Math.max(0, Math.min(1, u)); return u * u * (3 - 2 * u); };
const lerp = (a, b, u) => a + (b - a) * u;

// the studio: grey drawn from a light map (16 x 9 cells, grey after the film post; lifted by what the post takes),
// brighter across the middle than a round vignette would make it. map: GLITCH.studio, or any map `moodreel probe` reads
const maps = new Map();
export function studio(q, map = GLITCH.studio, { lift = 8 } = {}) {
  const key = JSON.stringify([map, lift]);
  if (!maps.has(key)) {
    const c = canvas(map[0].length, map.length), g = c.getContext('2d'), d = g.createImageData(c.width, c.height);
    map.forEach((row, j) => row.forEach((v, i) => {
      const k = (j * c.width + i) * 4;
      d.data[k] = d.data[k + 1] = d.data[k + 2] = Math.min(255, v + lift); d.data[k + 3] = 255;
    }));
    g.putImageData(d, 0, 0);
    maps.set(key, c);
  }
  q.save(); q.imageSmoothingEnabled = true; q.imageSmoothingQuality = 'high'; q.drawImage(maps.get(key), 0, 0, W, H);
  q.globalAlpha = 0.035; q.fillStyle = '#000';
  for (let y = 0; y < H; y += 3) q.fillRect(0, y, W, 1);
  q.restore();
}

// the dark ground: a cool grey glow in the middle falling to near-black, the screen door over it
export function dark(q, { middle = '#24222c', edge = '#0d0c12', dither = GLITCH.dither.alpha } = {}) {
  const bg = q.createRadialGradient(W * 0.5, H * 0.45, 100, W * 0.5, H * 0.5, 1200);
  bg.addColorStop(0, middle); bg.addColorStop(1, edge);
  q.fillStyle = bg; q.fillRect(0, 0, W, H);
  crossDither(q, `rgba(255,255,255,${dither})`);
}

// the screen door: diagonals crossing every 14 px (under 4 % it vanishes in H.264, over 15 % it reads as a pattern)
export function crossDither(q, color, step = GLITCH.dither.step) {
  q.save(); q.strokeStyle = color; q.lineWidth = 2;
  for (let k = -H; k < W; k += step) {
    q.beginPath(); q.moveTo(k, 0); q.lineTo(k + H, H); q.stroke();
    q.beginPath(); q.moveTo(k + H, 0); q.lineTo(k, H); q.stroke();
  }
  q.restore();
}

// the lens's light over a look: light x gain x (1 - strength x d^power), d the distance in an ellipse (centre, radii);
// fitted per look on the reference, the far corners at half the light
export function lens(q, [lx, ly, rx, ry, strength, power, gain] = GLITCH.lens) {
  q.save(); q.translate(lx, ly); q.scale(1, ry / rx);
  const v = q.createRadialGradient(0, 0, 0, 0, 0, rx * 1.8);
  for (let i = 0; i <= 12; i++) { const d = i / 12 * 1.8; v.addColorStop(i / 12, `rgba(0,0,0,${Math.min(0.7, strength * d ** power)})`); }
  q.fillStyle = v; q.fillRect(-4000, -4000, 8000, 8000);
  if (gain > 1) {
    const b = q.createRadialGradient(0, 0, 0, 0, 0, rx);
    b.addColorStop(0, `rgba(255,255,255,${(gain - 1) * 0.9})`); b.addColorStop(1, 'rgba(255,255,255,0)');
    q.globalCompositeOperation = 'screen'; q.fillStyle = b; q.fillRect(-4000, -4000, 8000, 8000);
  }
  q.restore();
}

// a light card's halo: a plateau at the light's limit across most of the card, falling off only toward its edges, as
// if the card clipped before the lens darkened the frame. Drawn after lens(), on the card alone: `page` is a canvas
// holding the card (its alpha limits the halo)
const HALO = new Map();
export function halo(q, page, [hx, hy, hrx, hry, strength] = GLITCH.halo) {
  if (!HALO.has(page)) HALO.set(page, canvas(page.width, page.height));
  const c = HALO.get(page), g = c.getContext('2d');
  g.globalCompositeOperation = 'copy'; g.drawImage(page, 0, 0); g.globalCompositeOperation = 'source-in';
  g.save(); g.translate(hx, hy); g.scale(1, hry / hrx);
  const h = g.createRadialGradient(0, 0, 0, 0, 0, hrx);
  h.addColorStop(0, `rgba(255,255,255,${strength})`); h.addColorStop(0.6, `rgba(255,255,255,${strength * 0.9})`);
  h.addColorStop(1, 'rgba(255,255,255,0)');
  g.fillStyle = h; g.fillRect(-4000, -6000, 8000, 12000); g.restore();
  q.save(); q.globalCompositeOperation = 'screen'; q.drawImage(c, 0, 0); q.restore();
}

// the end card's ground, held still: a clean disc in the middle, fine scan rows, and outside the disc 12 px cells of
// line glyphs (a dot, a slash, a cross, now and then a ring) darkening toward the corners in blotches. light: true for
// the white card (grey glyphs on white), false for its dark twin (dim glyphs on black)
export function glyphGround({ light = true, radius = 665, cell = 12, seed = 9 } = {}) {
  const c = canvas(W, H), g = c.getContext('2d');
  g.fillStyle = light ? '#fdfdfd' : '#000'; g.fillRect(0, 0, W, H);
  if (light) { g.fillStyle = 'rgba(0,0,0,0.012)'; for (let y = 2; y < H; y += 4) g.fillRect(0, y, W, 2); }
  const lattice = (x, y) => hash(x * 31 + y * 57, seed);
  const noise = (x, y) => {
    const X = Math.floor(x), Y = Math.floor(y), fx = smooth(x - X), fy = smooth(y - Y);
    return lerp(lerp(lattice(X, Y), lattice(X + 1, Y), fx), lerp(lattice(X, Y + 1), lattice(X + 1, Y + 1), fx), fy);
  };
  g.strokeStyle = light ? 'rgba(30,30,30,0.15)' : 'rgba(255,255,255,0.12)';
  g.fillStyle = light ? 'rgba(30,30,30,0.24)' : 'rgba(255,255,255,0.18)'; g.lineWidth = 1.2;
  for (let y = 0; y < H; y += cell) for (let x = 0; x < W; x += cell) {
    const r = Math.hypot(x + cell / 2 - W / 2, y + cell / 2 - H / 2);
    if (r < radius) continue;
    const v = (r - radius) / 420 + (noise(x / 60, y / 60) - 0.5) * 0.9 + (hash(x, y) - 0.5) * 0.25;
    if (v < 0.02 || hash(y, x) < 0.12) continue;
    g.beginPath();
    if (v < 0.3) { g.fillRect(x + cell / 2 - 1, y + cell / 2 - 1, 2, 2); continue; }
    if (v > 1.05 && hash(x + 1, y) > 0.6) g.arc(x + cell / 2, y + cell / 2, cell * 0.38, 0, Math.PI * 2);
    else {
      g.moveTo(x, y + cell); g.lineTo(x + cell, y);
      if (v > 0.7) { g.moveTo(x, y); g.lineTo(x + cell, y + cell); }
    }
    g.stroke();
  }
  return c;
}
