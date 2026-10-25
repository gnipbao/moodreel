// The hero lights: particle fields and light objects drawn in cells. A tunnel of characters fanning from a vanishing
// point; a ring of streaks (a field turning about a pivot above its middle, seen through a window); a neon tube built of
// lit cells; a beam of light built of 16 px ASCII cells. One hue family per film (GLITCH.glow, or cyan, lime, amber).
//
//   import { tunnel, ring, neon, beam } from './kit/fields.js';
//   q.globalCompositeOperation = 'lighter'; ring(q, t, { hue: x => 200 }); q.globalCompositeOperation = 'source-over';
import { SIZE, GLITCH } from './tokens.js';

const [W, H] = SIZE;
const hash = (n, k = 0) => { const x = Math.sin(n * 127.1 + k * 311.7) * 43758.5453; return x - Math.floor(x); };
const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
const POOL = Array.from({ length: 14000 }, (_, i) => [1, 2, 3, 4, 5, 6].map(k => hash(i, k)));

// characters streaming out along rays from a vanishing point, small and dim near it, large and bright away from it
export function tunnel(q, u, { vp = [W / 2, H * 0.1], rays = 110, per = 26, speed = 5, hue = 352, font = 'JetBrains Mono',
  chars = 'ABCDEFGHJKMNPRSTUVWXYZ0123456789$#%&@*+=?' } = {}) {
  for (let r = 0; r < rays; r++) {
    const phi = 0.02 * Math.PI + (r / (rays - 1)) * 0.96 * Math.PI, dx = Math.cos(phi), dy = Math.sin(phi);
    for (let k = 0; k < per; k++) {
      const s = ((k + hash(r, 1) + u * speed) % per) / per, d = 40 + 2100 * s ** 1.8;
      const x = vp[0] + dx * d, y = vp[1] + dy * d * 0.75;
      if (x < -20 || x > W + 20 || y > H + 20) continue;
      const n = r * per + k;
      q.font = `500 ${6 + 28 * s}px "${font}"`;
      q.fillStyle = `hsla(${hue - 7 + hash(n, 3) * 15}, 65%, ${32 + hash(n, 4) * 30}%, ${clamp(0.25 + s)})`;
      q.fillText(chars[Math.floor(hash(n, 5) * chars.length)], x, y);
    }
  }
}

// a ring of vertical streaks: a field turning about `pivot` on ellipses `aspect` wide to 1 high at `rate` rad/s, seen
// through an elliptical window (and outside a hole, if given). Measured on the reference: the pivot 180 px above the
// window's middle, about 1 rad/s, 2:1; the streaks 3-8 px wide and 20-90 long, some with hot cores; lit share ~19 %.
// hue(x) gives each streak's hue across the frame; ink draws them all in one colour (an inverted frame)
export function ring(q, t, { pivot = [962, 470], aspect = 2.02, rate = 1.0, reach = 640, count = 6000,
  window: win = [962, 650, 855, 420], hole = null, hue = () => 300, light = [22, 50], width = [4, 10], length = [20, 100],
  ink = null } = {}) {
  const [wx, wy, wrx, wry] = win;
  for (let i = 0; i < count; i++) {
    const [h1, h2, h3, h4, h5, h6] = POOL[i];
    const a = h1 * Math.PI * 2 - t * rate, rho = reach * Math.sqrt(h2);
    const x0 = pivot[0] + Math.cos(a) * rho * aspect, y0 = pivot[1] + Math.sin(a) * rho;
    const e = ((x0 - wx) / wrx) ** 2 + ((y0 - wy) / wry) ** 2;
    if (e > 1) continue;
    if (hole && ((x0 - hole[0]) / hole[2]) ** 2 + ((y0 - hole[1]) / hole[3]) ** 2 < 1) continue;
    const near = 0.7 + 0.6 * clamp((y0 - (wy - wry)) / (2 * wry)), core = h6 > 0.95, edge = clamp((1 - e) / 0.08);
    const len = (length[0] + h3 * h3 * (length[1] - length[0])) * near;
    const w = core ? 2 : width[0] + Math.floor(h4 * 4) * (width[1] - width[0]) / 4, x = Math.round(x0 / 3) * 3;
    q.fillStyle = ink ?? (core ? `hsla(${hue(x) + 50}, 100%, ${78 + h5 * 12}%, ${0.95 * edge})`
      : `hsla(${hue(x) + (h5 - 0.5) * 24}, ${72 + h4 * 22}%, ${light[0] + h5 * (light[1] - light[0])}%, ${(0.28 + h5 * 0.4) * edge})`);
    q.fillRect(x, y0 - len / 2, w, len);
  }
}

// a neon tube built of lit cells, white-hot in the middle and coloured toward its end, with its glow
export function neon(q, x, y, w, h, { color = GLITCH.glow.neon, cell = 12 } = {}) {
  q.save(); q.shadowColor = color; q.shadowBlur = 70; q.fillStyle = color;
  q.beginPath(); q.roundRect(x, y, w, h, w / 2); q.fill(); q.restore();
  for (let cy = y + 4; cy < y + h - 4; cy += cell) for (let cx = x + 2; cx < x + w - 2; cx += cell) {
    const k = (cy - y) / h;
    q.fillStyle = k > 0.88 ? color : k > 0.8 ? '#ffc6e6' : '#fff0f8';
    q.fillRect(cx + 1, cy + 1, cell - 2, cell - 2);
  }
}

// a beam of light in 16 px ASCII cells, the grid from the frame's corner: white cells with a centre dot on a grey grid
// inside, one hot cell with a cross at its edge, then one dark one; xl(y), xr(y): its edges; top: where it starts
export function beam(q, xl, xr, top, { cell = 16, edge = GLITCH.glow.pink, outer = '#4a1631', cross = '#ff8fc8', crossOuter = '#a3245f',
  slopes = [1.53, 1.06], x1 = W } = {}) {
  const crossed = (x, y, color) => {
    q.strokeStyle = color; q.lineWidth = 1.4; q.beginPath();
    q.moveTo(x + 2, y + 2); q.lineTo(x + cell - 2, y + cell - 2); q.moveTo(x + cell - 2, y + 2); q.lineTo(x + 2, y + cell - 2); q.stroke();
  };
  for (let y = Math.floor((top - 40) / cell) * cell; y < H; y += cell) for (let x = 0; x < x1; x += cell) {
    const cx = x + cell / 2, cy = y + cell / 2;
    const d = Math.min((cx - xl(cy)) / slopes[0], (xr(cy) - cx) / slopes[1], cy - top);   // depth inside the beam, px
    if (d < -26) continue;
    if (d > 0) {
      q.fillStyle = '#a9a9a9'; q.fillRect(x, y, cell, cell);
      q.fillStyle = d < 7 && hash(x, y) > 0.5 ? '#f3b8d6' : '#e2e2e2'; q.fillRect(x + 2, y + 2, cell - 4, cell - 4);
      q.fillStyle = '#5a5a5a'; q.fillRect(x + cell / 2 - 1, y + cell / 2 - 1, 2, 2);
    } else if (d > -11) { q.fillStyle = edge; q.fillRect(x, y, cell, cell); crossed(x, y, cross); }
    else { q.fillStyle = outer; q.fillRect(x, y, cell, cell); crossed(x, y, crossOuter); }
  }
}

// the dark ground of the beam: every 16 px cell a grey ring on a warm near-black, lighter toward the middle right
export function ringGround(q, { cell = 16, centre = [1100, 560] } = {}) {
  for (let y = 0; y < H; y += cell) for (let x = 0; x < W; x += cell) {
    const v = 1 - 0.38 * clamp(Math.hypot((x - centre[0]) / 1150, (y - centre[1]) / 700));
    q.fillStyle = `rgb(${Math.round(31 * v)},${Math.round(22 * v)},${Math.round(21 * v)})`; q.fillRect(x, y, cell, cell);
    q.strokeStyle = `rgba(190,168,165,${0.8 * v})`; q.lineWidth = 1.6;
    q.beginPath(); q.arc(x + cell / 2, y + cell / 2, cell * 0.36, 0, Math.PI * 2); q.stroke();
  }
}
