// Signal Plates idiom: the line field. Thousands of hairlines integrated through a flow (curl noise by default, so they
// never cross or clump), drawn on the GPU with kit/gl.js lines: contour fields, streams, a pull toward a point. Each
// line tapers in and out along its length; its brightness can follow a tone (lit near a source, dim far off).
//
//   const L = P.G.lines(120000);
//   const field = lineField({ count: 2400, steps: 48, h: 7, seed: 3,
//     flow: (x, y, t) => swirl(x, y, t, { scale: 1 / 420, around: [1300, 560], pull: 0.4 }) });
//   L.clear(); field.draw(L, t, { tone: (x, y) => ... }); L.render(P.hdr);
//
// Everything is computed from t (seeds from `seed`, the flow from t): any frame stands alone. A field whose flow does
// not change (`still: true`) is integrated once and reused; it can still move: `xf` maps its points (a turn, a drift)
// and `pulse` sends light along the lines (energy running down them, into the point they are drawn to).
import { rng } from './core.js';
import { linear } from './gl.js';
import { PALETTE } from './tokens.js';

// 3D value noise, smooth (quintic), from integer hashes; -1..1
function h3(x, y, z) {
  let n = (Math.imul(x, 374761393) + Math.imul(y, 668265263) + Math.imul(z, 2147483647)) | 0;
  n = Math.imul(n ^ (n >>> 13), 1274126177);
  return ((n ^ (n >>> 16)) >>> 0) / 4294967296 * 2 - 1;
}
const q = u => u * u * u * (u * (u * 6 - 15) + 10);
export function noise3(x, y, z) {
  const xi = Math.floor(x), yi = Math.floor(y), zi = Math.floor(z), u = q(x - xi), v = q(y - yi), w = q(z - zi);
  const L = (a, b, k) => a + (b - a) * k;
  const c = (dx, dy, dz) => h3(xi + dx, yi + dy, zi + dz);
  return L(L(L(c(0, 0, 0), c(1, 0, 0), u), L(c(0, 1, 0), c(1, 1, 0), u), v),
    L(L(c(0, 0, 1), c(1, 0, 1), u), L(c(0, 1, 1), c(1, 1, 1), u), v), w);
}

// the curl of a noise potential at (x, y) px, evolving with t: a divergence-free flow. Optionally wound round a point
// (`around`, `spin` > 0 anticlockwise on screen) and drawn into it (`pull`).
export function swirl(x, y, t, { scale = 1 / 400, speed = 0.15, around = null, spin = 0, pull = 0, octaves = 2 } = {}) {
  const e = 0.5, pot = (a, b) => {
    let s = 0, amp = 1, f = scale;
    for (let o = 0; o < octaves; o++, amp *= 0.5, f *= 2.1) s += amp * noise3(a * f, b * f, t * speed + o * 7.3);
    return s;
  };
  let vx = (pot(x, y + e) - pot(x, y - e)) / (2 * e * scale), vy = -(pot(x + e, y) - pot(x - e, y)) / (2 * e * scale);
  if (around) {
    const dx = x - around[0], dy = y - around[1], r = Math.hypot(dx, dy) + 1e-6;
    vx += (-dy / r) * spin - (dx / r) * pull;
    vy += (dx / r) * spin - (dy / r) * pull;
  }
  return [vx, vy];
}

// A field of `count` lines, each `steps` steps of `h` px through `flow(x, y, t)` (any scale: it is normalised), seeded
// by `spawn(r, i)` (default: anywhere in the frame). draw() appends the segments to a kit/gl.js lines batch.
export function lineField({ count = 2000, steps = 40, h = 6, seed = 1, flow = swirl, spawn = null, width = 1.1,
  W = 1920, H = 1080, still = false } = {}) {
  const r = rng(seed);
  const seeds = Array.from({ length: count }, (_, i) => (spawn ? spawn(r, i) : [r() * W, r() * H]));
  const jitter = seeds.map(() => r());
  // one line's points through the flow at t
  const trace = ([x, y], t) => {
    const pts = [x, y];
    for (let s = 0; s < steps; s++) {
      const [vx, vy] = flow(x, y, t), m = Math.hypot(vx, vy) || 1;
      const mx = x + (vx / m) * h * 0.5, my = y + (vy / m) * h * 0.5;    // midpoint step: lines hold their spacing
      const [ux, uy] = flow(mx, my, t), um = Math.hypot(ux, uy) || 1;
      x += (ux / um) * h; y += (uy / um) * h;
      pts.push(x, y);
      if (x < -200 || x > W + 200 || y < -200 || y > H + 200) break;
    }
    return pts;
  };
  let cache = null;
  return {
    seeds,
    // tone(x, y) 0..1 sets each line's brightness where it starts (graphite at 0, bone at 1); alpha scales them all;
    // grow 0..1 draws each line only that far along (a field drawing itself on); xf(x, y) -> [x, y] moves the points;
    // pulse { at, speed (steps a second), length (steps), gain } adds light travelling down every line
    draw(L, t, { tone = () => 0.6, alpha = 1, grow = 1, color = null, w = width, xf = null, pulse = null } = {}) {
      const dim = linear(PALETTE.graphite), lit = linear(PALETTE.bone);
      const n = Math.max(1, Math.round(steps * grow));
      if (still) cache ??= seeds.map(p => trace(p, 0));
      for (let i = 0; i < seeds.length; i++) {
        const pts = still ? cache[i] : trace(seeds[i], t);
        const k = Math.min(1, Math.max(0, tone(pts[0], pts[1])));
        const rgb = color ?? dim.map((d, c) => d + (lit[c] - d) * k);
        const a0 = alpha * (0.35 + 0.65 * k) * (0.6 + 0.4 * jitter[i]);
        const m = Math.min(n, pts.length / 2 - 1);
        let [x, y] = xf ? xf(pts[0], pts[1]) : [pts[0], pts[1]];
        for (let s = 0; s < m; s++) {
          const [nx, ny] = xf ? xf(pts[2 * s + 2], pts[2 * s + 3]) : [pts[2 * s + 2], pts[2 * s + 3]];
          const u = (s + 0.5) / steps;
          let a = a0 * Math.min(1, u * 6) * Math.min(1, (1 - u) * 4);
          if (pulse) {
            const d = (((pulse.speed * (t - (pulse.at ?? 0)) + jitter[i] * steps - s) % steps) + steps) % steps;
            a *= 1 + (pulse.gain ?? 3) * Math.max(0, 1 - d / (pulse.length ?? 8));
          }
          if (x > -40 && x < W + 40 && y > -40 && y < H + 40) L.seg(x, y, 0, nx, ny, 0, w, rgb[0], rgb[1], rgb[2], a);
          x = nx; y = ny;
        }
      }
    } };
}
