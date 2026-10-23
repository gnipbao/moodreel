// Surfaces drawn in code, with the same names as the measurements (moodreel measure: texture.json), so a
// style's tokens.js can pass measured numbers straight in. All seeded and cached: no frame differs by chance.
import { rng } from './core.js';

const cache = new Map();
const offscreen = (w, h) => {
  const c = document.createElement('canvas');
  c.width = Math.max(1, Math.round(w));
  c.height = Math.max(1, Math.round(h));
  return c;
};

// a ground of one colour with paper mottle (slow variation, in grey levels) and fibres; drawn once, reused
export function paper(w, h, { color = '#efe6d2', mottle = 1.5, fibres = 400, seed = 7 } = {}) {
  const key = `paper:${w}:${h}:${color}:${mottle}:${fibres}:${seed}`;
  if (cache.has(key)) return cache.get(key);
  const c = offscreen(w, h), q = c.getContext('2d'), r = rng(seed);
  q.fillStyle = color;
  q.fillRect(0, 0, c.width, c.height);
  if (mottle > 0) {                                        // soft blotches: a low-res noise field, scaled up smooth
    const s = offscreen(32, 18), sq = s.getContext('2d'), img = sq.createImageData(32, 18);
    for (let i = 0; i < img.data.length; i += 4) {
      const v = 128 + (r() - 0.5) * 2 * mottle * 6;
      img.data[i] = img.data[i + 1] = img.data[i + 2] = v;
      img.data[i + 3] = 255;
    }
    sq.putImageData(img, 0, 0);
    q.save();
    q.globalCompositeOperation = 'overlay';
    q.globalAlpha = 0.5;
    q.imageSmoothingQuality = 'high';
    q.drawImage(s, 0, 0, c.width, c.height);
    q.restore();
  }
  q.save();
  q.globalAlpha = 0.05;
  q.strokeStyle = '#6b5a3a';
  for (let k = 0; k < fibres; k++) {
    const x = r() * c.width, y = r() * c.height, a = r() * Math.PI, l = 10 + r() * 30;
    q.beginPath();
    q.moveTo(x, y);
    q.lineTo(x + Math.cos(a) * l, y + Math.sin(a) * l);
    q.stroke();
  }
  q.restore();
  cache.set(key, c);
  return c;
}

// film or print grain over the whole frame, in device pixels; `amount` is the grain as `moodreel measure` reads it
// (grey levels). Overlay grain shows most on mid-grey and least near white or black, so the plate's strength is
// set from the ground's grey to land on the measured amount (calibrated against the measurement). Four seeded
// plates, chosen by frame, so the grain moves but every frame is reproducible
export function grain(g, amount, frame = 0, { moving = true, ground = '#808080' } = {}) {
  if (!(amount > 0)) return;
  const grey = [1, 3, 5].map(i => parseInt(ground.slice(i, i + 2), 16)).reduce((a, b, i) => a + b * [0.299, 0.587, 0.114][i], 0);
  const gain = Math.max(0.05, (2 * Math.min(grey, 255 - grey)) / 255);
  amount = amount / (2.53 * gain);
  const W = g.canvas.width, H = g.canvas.height, key = `grain:${W}:${H}`;
  if (!cache.has(key)) {
    cache.set(key, [0, 1, 2, 3].map(k => {
      const c = offscreen(W, H), q = c.getContext('2d'), img = q.createImageData(W, H), r = rng(100 + k);
      for (let i = 0; i < img.data.length; i += 4) {
        const v = 128 + (r() + r() + r() - 1.5) * 170;     // roughly gaussian
        img.data[i] = img.data[i + 1] = img.data[i + 2] = v;
        img.data[i + 3] = 255;
      }
      q.putImageData(img, 0, 0);
      return c;
    }));
  }
  g.save();
  g.setTransform(1, 0, 0, 1, 0, 0);
  g.globalCompositeOperation = 'overlay';
  g.globalAlpha = Math.min(1, amount / 30);
  g.drawImage(cache.get(key)[moving ? frame % 4 : 0], 0, 0);
  g.restore();
}

// corners darker than the centre by `strength` of the centre's light: the vignette as `moodreel measure` reads it
// (calibrated against the measurement)
export function vignette(g, w, h, strength = 0.12, color = '#000') {
  if (!(strength > 0)) return;                             // a measured -0.002 is no vignette, not a negative alpha
  const gr = g.createRadialGradient(w / 2, h / 2, 0, w / 2, h / 2, Math.hypot(w, h) / 2);
  gr.addColorStop(0.35, 'rgba(0,0,0,0)');
  gr.addColorStop(1, color);
  g.save();
  g.globalAlpha = Math.min(1, strength / 1.16);
  g.fillStyle = gr;
  g.fillRect(0, 0, w, h);
  g.restore();
}

// a halftone screen: `period` px between dot centres, `angle` degrees; use as a fillStyle for any path
export function screen(g, { period = 6, angle = 45, color = '#1b1b1b', dot = 0.42 } = {}) {
  const key = `screen:${period}:${color}:${dot}`;
  if (!cache.has(key)) {
    const c = offscreen(period, period), q = c.getContext('2d');
    q.fillStyle = color;
    q.beginPath();
    q.arc(period / 2, period / 2, period * dot, 0, Math.PI * 2);
    q.fill();
    cache.set(key, c);
  }
  const p = g.createPattern(cache.get(key), 'repeat');
  p.setTransform(new DOMMatrix().rotate(angle));
  return p;
}

// horizontal scanlines in device pixels: every `period` px a line darker by `strength` (0-1)
export function scanlines(g, period = 3, strength = 0.25) {
  const W = g.canvas.width, H = g.canvas.height;
  g.save();
  g.setTransform(1, 0, 0, 1, 0, 0);
  g.fillStyle = `rgba(0,0,0,${strength})`;
  for (let y = 0; y < H; y += period) g.fillRect(0, y, W, 1);
  g.restore();
}

// print layers out of register: draw(g, ink) is called once per ink, offset and multiplied like overprinted
// colours. layers: [{ color, dx, dy }]
export function misregister(g, draw, layers) {
  for (const { color, dx = 0, dy = 0 } of layers) {
    g.save();
    g.globalCompositeOperation = 'multiply';
    g.translate(dx, dy);
    draw(g, color);
    g.restore();
  }
}
