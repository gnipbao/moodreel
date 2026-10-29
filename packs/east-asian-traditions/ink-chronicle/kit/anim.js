// Time helpers for shots driven by events: eased progress through a window, a pulse that decays after a hit, a spring's
// step response, keyframes, a hash that holds still across a frame's motion-blur shutter, and paths walked by length.
// All pure functions of their arguments.
//
//   prog(t, a, b, ease.outExpo)     0 before a, 1 after b, eased in between
//   pulse(t, t0, 0.12)              1 at t0, halving every 0.12 s after (0 before t0)
//   springStep(t - t0, 3.4, 0.42)   a damped spring answering a step at t0: 0 -> 1 with overshoot
//   keys(t, [[0, 0], [1.2, 5, ease.outCubic], [2, 3]])   the ease on a key shapes the segment ending there
//   frameIdx(t)                     the 60 fps frame t falls in: seed flicker and shake with it, so one frame shows one state
//   const P = path(points); P.at(s) -> { x, y, angle } at arc length s; P.length
//
// After mexicat/pdoom-video's engine/util.ts (MIT, Copyright (c) 2026 Giacomo Magnanini). See NOTICE.

export const clamp = (x, a = 0, b = 1) => (x < a ? a : x > b ? b : x);
export const lerp = (a, b, u) => a + (b - a) * u;
export const TAU = Math.PI * 2;
export const smoothstep = (a, b, x) => { const u = clamp((x - a) / (b - a)); return u * u * (3 - 2 * u); };

export const ease = {
  linear: u => u,
  inQuad: u => u * u,
  outQuad: u => 1 - (1 - u) * (1 - u),
  inOutQuad: u => (u < 0.5 ? 2 * u * u : 1 - (-2 * u + 2) ** 2 / 2),
  inCubic: u => u * u * u,
  outCubic: u => 1 - (1 - u) ** 3,
  inOutCubic: u => (u < 0.5 ? 4 * u * u * u : 1 - (-2 * u + 2) ** 3 / 2),
  inQuart: u => u ** 4,
  outQuart: u => 1 - (1 - u) ** 4,
  inOutQuart: u => (u < 0.5 ? 8 * u ** 4 : 1 - (-2 * u + 2) ** 4 / 2),
  outQuint: u => 1 - (1 - u) ** 5,
  inExpo: u => (u <= 0 ? 0 : 2 ** (10 * u - 10)),
  outExpo: u => (u >= 1 ? 1 : 1 - 2 ** (-10 * u)),
  inOutExpo: u => (u <= 0 ? 0 : u >= 1 ? 1 : u < 0.5 ? 2 ** (20 * u - 10) / 2 : (2 - 2 ** (-20 * u + 10)) / 2),
  outBack: (u, s = 1.70158) => 1 + (s + 1) * (u - 1) ** 3 + s * (u - 1) ** 2,
  inBack: (u, s = 1.70158) => (s + 1) * u ** 3 - s * u * u,
};

export const prog = (x, a, b, fn = ease.linear) => fn(clamp((x - a) / (b - a)));
export const pulse = (t, t0, half = 0.12) => (t < t0 ? 0 : 0.5 ** ((t - t0) / half));
export const window01 = (x, a, b, fadeIn = 0.2, fadeOut = 0.2) => Math.min(smoothstep(a, a + fadeIn, x), 1 - smoothstep(b - fadeOut, b, x));

export function springStep(t, freq = 4, damping = 0.35) {
  if (t <= 0) return 0;
  const w = TAU * freq;
  return 1 - Math.exp(-damping * w * t) * Math.cos(w * Math.sqrt(1 - damping * damping) * t);
}

export function keys(t, list) {
  if (!list.length) return 0;
  if (t <= list[0][0]) return list[0][1];
  for (let i = 1; i < list.length; i++) {
    const [tk, vk, fn] = list[i];
    if (t <= tk) {
      const [tp, vp] = list[i - 1];
      return lerp(vp, vk, (fn ?? ease.inOutCubic)((t - tp) / (tk - tp)));
    }
  }
  return list[list.length - 1][1];
}

export const frameIdx = (t, fps = 60) => Math.round(t * fps);

// a stateless hash of numbers to 0..1
export function hash(...xs) {
  let h = 2166136261 >>> 0;
  for (const x of xs) {
    h ^= Math.floor(x * 1000003) | 0;
    h = Math.imul(h, 16777619);
    h ^= h >>> 13;
    h = Math.imul(h, 0x5bd1e995);
    h ^= h >>> 15;
  }
  return (h >>> 0) / 4294967296;
}

const fade = u => u * u * u * (u * (u * 6 - 15) + 10);
export function noise1(x, seed = 0) {
  const i = Math.floor(x);
  return lerp(hash(i, seed) * 2 - 1, hash(i + 1, seed) * 2 - 1, fade(x - i));
}

// a polyline walked by arc length
export function path(pts) {
  const L = [0];
  for (let i = 1; i < pts.length; i++) L.push(L[i - 1] + Math.hypot(pts[i].x - pts[i - 1].x, pts[i].y - pts[i - 1].y));
  const length = L[L.length - 1] ?? 0;
  return { pts, lengths: L, length,
    at(s) {
      const n = pts.length;
      if (n < 2) return { x: pts[0]?.x ?? 0, y: pts[0]?.y ?? 0, angle: 0 };
      s = clamp(s, 0, length);
      let lo = 0, hi = n - 1;
      while (hi - lo > 1) { const m = (lo + hi) >> 1; if (L[m] < s) lo = m; else hi = m; }
      const a = pts[lo], b = pts[hi], seg = L[hi] - L[lo], u = seg > 0 ? (s - L[lo]) / seg : 0;
      return { x: lerp(a.x, b.x, u), y: lerp(a.y, b.y, u), angle: Math.atan2(b.y - a.y, b.x - a.x) };
    } };
}
