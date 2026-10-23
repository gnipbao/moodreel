// Time and randomness for pages drawn as a function of time. Everything here is deterministic: the same t gives
// the same picture, in any order, on any worker (no Date.now, no unseeded Math.random, no state between frames).
import { ease } from './eases.js';

export const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
export const lerp = (a, b, u) => a + (b - a) * u;
export const TAU = Math.PI * 2;

// progress of a tween at time t: 0 before `at`, 1 after `at + dur`, eased in between
export const tween = (t, at, dur, name = 'power2.out') => ease(name)(clamp((t - at) / dur));

// a value tweened from `from` to `to`
export const value = (t, at, dur, from, to, name) => lerp(from, to, tween(t, at, dur, name));

// keyframes [[t, v], ...] with an ease per segment (the ease of the segment's end key, default linear)
export function keys(list) {
  return t => {
    if (t <= list[0][0]) return list[0][1];
    for (let i = 1; i < list.length; i++) {
      const [t1, v1, e = 'none'] = list[i], [t0, v0] = list[i - 1];
      if (t <= t1) return lerp(v0, v1, ease(e)((t - t0) / (t1 - t0)));
    }
    return list[list.length - 1][1];
  };
}

// a seeded generator (mulberry32) and stable hashes for per-item variation
export function rng(seed) {
  let a = seed | 0;
  return () => {
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
export const hash = n => {
  const x = Math.sin(n * 127.1 + 311.7) * 43758.5453;
  return x - Math.floor(x);
};
export const noise1 = x => {
  const i = Math.floor(x), f = x - i, u = f * f * (3 - 2 * f);
  return lerp(hash(i), hash(i + 1), u);
};

// time held on n-frame steps (animation on twos: step(t, fps / 2)); the camera should stay smooth
export const step = (t, rate) => Math.floor(t * rate + 1e-6) / rate;

// the i-th item of a staggered group starts `interval` after the previous one
export const stagger = (at, interval, i) => at + interval * i;
