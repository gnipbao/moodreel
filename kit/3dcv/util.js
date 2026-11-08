// kit/3dcv/util.js — ported from 3DCodeVerse (https://github.com/gaoypeng/3dcodeverse), awesome showcase
//   (https://huggingface.co/datasets/3dcodeverse/3dcodeverse-awesome-showcase): the 30-second film's code,
//   source src/core/util.js, round r02, git blob 7b29cec7e017860a19245cd45cd8822b3001e082.
// Licence: CC BY-NC-SA 4.0 (https://creativecommons.org/licenses/by-nc-sa/4.0/), see kit/3dcv/LICENSE.
//   Non-commercial use only; adaptations keep this licence. The rest of moodreel is MIT.
// Changes by moodreel (2026-11-08): three.js taken from ../three.js instead of the bare 'three' import; this header.

// util.js — pure helpers shared by every module: deterministic time, seeded RNG, noise, easing, keyframe tracks,
// splines and camera rigs.  No DOM, no renderer.  Re-exported by stage.js and available on ctx.  See CORE_API.md.
// Owner: core (foundation stage).
import { THREE } from '../three.js';

export const FPS = 24;
/** Global film time in seconds of GLOBAL frame n (1-based). */
export const frameTime = n => (n - 1) / FPS;

// ---------------------------------------------------------------------------------------------- math helpers
export const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
export const lerp = (a, b, t) => a + (b - a) * t;
export const invLerp = (a, b, x) => (b === a ? 0 : (x - a) / (b - a));
export const remap = (x, a, b, c, d, clampIt = true) => { let t = invLerp(a, b, x); if (clampIt) t = clamp(t); return c + (d - c) * t; };
export const smoothstep = (e0, e1, x) => { const t = clamp((x - e0) / (e1 - e0)); return t * t * (3 - 2 * t); };
export const smootherstep = (e0, e1, x) => { const t = clamp((x - e0) / (e1 - e0)); return t * t * t * (t * (t * 6 - 15) + 10); };
export const deg = d => d * Math.PI / 180;
/** Linear interpolation of numbers / arrays / THREE vectors+colours (returns a new value of the same kind). */
export function mixValue(a, b, t) {
  if (typeof a === 'number') return a + (b - a) * t;
  if (Array.isArray(a)) return a.map((v, i) => v + (b[i] - v) * t);
  if (a && a.isVector3) return a.clone().lerp(b, t);
  if (a && a.isVector2) return a.clone().lerp(b, t);
  if (a && a.isColor) return a.clone().lerp(b, t);
  return t < 0.5 ? a : b;
}

// ---------------------------------------------------------------------------------------------- easing
const PI = Math.PI;
export const ease = {
  linear: t => t,
  inQuad: t => t * t, outQuad: t => t * (2 - t), inOutQuad: t => (t < 0.5 ? 2 * t * t : -1 + (4 - 2 * t) * t),
  inCubic: t => t * t * t, outCubic: t => 1 - Math.pow(1 - t, 3),
  inOutCubic: t => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2),
  inQuart: t => t ** 4, outQuart: t => 1 - (1 - t) ** 4, inOutQuart: t => (t < 0.5 ? 8 * t ** 4 : 1 - (-2 * t + 2) ** 4 / 2),
  inSine: t => 1 - Math.cos(t * PI / 2), outSine: t => Math.sin(t * PI / 2), inOutSine: t => -(Math.cos(PI * t) - 1) / 2,
  inExpo: t => (t === 0 ? 0 : Math.pow(2, 10 * t - 10)), outExpo: t => (t === 1 ? 1 : 1 - Math.pow(2, -10 * t)),
  inOutExpo: t => (t === 0 ? 0 : t === 1 ? 1 : t < 0.5 ? Math.pow(2, 20 * t - 10) / 2 : (2 - Math.pow(2, -20 * t + 10)) / 2),
  outBack: t => { const c1 = 1.70158, c3 = c1 + 1; return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2; },
  inOutBack: t => { const c2 = 1.70158 * 1.525; return t < 0.5 ? ((2 * t) ** 2 * ((c2 + 1) * 2 * t - c2)) / 2 : ((2 * t - 2) ** 2 * ((c2 + 1) * (t * 2 - 2) + c2) + 2) / 2; },
  smooth: t => t * t * (3 - 2 * t), smoother: t => t * t * t * (t * (t * 6 - 15) + 10),
  hold: t => 0,
};
const easeFn = e => (typeof e === 'function' ? e : ease[e || 'linear'] || ease.linear);

// ---------------------------------------------------------------------------------------------- seeded RNG
function hashString(s) { let h = 1779033703 ^ s.length; for (let i = 0; i < s.length; i++) { h = Math.imul(h ^ s.charCodeAt(i), 3432918353); h = (h << 13) | (h >>> 19); } return h >>> 0; }
/**
 * rng(seed) -> deterministic generator (mulberry32).  seed: number or string.
 * r() / r.float() in [0,1); r.range(a,b); r.int(a,b) inclusive; r.pick(arr); r.sign(); r.normal(mu,sigma);
 * r.chance(p); r.fork(tag) -> independent child stream; r.shuffle(arr) in place.
 */
export function rng(seed = 1) {
  let a = (typeof seed === 'string' ? hashString(seed) : (seed >>> 0) || 0x9e3779b9);
  const base = a;
  const next = () => { a |= 0; a = (a + 0x6D2B79F5) | 0; let t = Math.imul(a ^ (a >>> 15), 1 | a); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; };
  const r = () => next();
  r.float = next;
  r.range = (lo, hi) => lo + (hi - lo) * next();
  r.int = (lo, hi) => lo + Math.floor(next() * (hi - lo + 1));
  r.pick = arr => arr[Math.floor(next() * arr.length)];
  r.sign = () => (next() < 0.5 ? -1 : 1);
  r.chance = p => next() < p;
  r.normal = (mu = 0, sigma = 1) => { const u = Math.max(1e-9, next()), v = next(); return mu + sigma * Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * PI * v); };
  r.fork = tag => rng((base ^ hashString(String(tag))) >>> 0);
  r.shuffle = arr => { for (let i = arr.length - 1; i > 0; i--) { const j = Math.floor(next() * (i + 1)); [arr[i], arr[j]] = [arr[j], arr[i]]; } return arr; };
  return r;
}
/** Stateless hash noise: hash1(x, seed) in [0,1) for integer-ish x. */
export function hash1(x, seed = 0) { let h = Math.imul((x | 0) ^ Math.imul(seed | 0, 0x27d4eb2d), 0x9E3779B1); h ^= h >>> 15; h = Math.imul(h, 0x85ebca6b); h ^= h >>> 13; return (h >>> 0) / 4294967296; }
/** Smooth 1D value noise in [-1,1] (deterministic) — handy for hand-held camera drift, idle sway. */
export function noise1(x, seed = 0) { const i = Math.floor(x), f = x - i; const u = f * f * (3 - 2 * f); return (lerp(hash1(i, seed), hash1(i + 1, seed), u)) * 2 - 1; }
/** Fractal 1D noise (octaves) in about [-1,1]. */
export function fbm1(x, seed = 0, oct = 3) { let s = 0, a = 0.5, f = 1, n = 0; for (let o = 0; o < oct; o++) { s += a * noise1(x * f, seed + o * 17); n += a; a *= 0.5; f *= 2.03; } return s / n; }

// ---------------------------------------------------------------------------------------------- keyframe tracks
/**
 * track(keys, opts) -> f(frame) -> value.
 *   keys: [[frame, value, easeToNext?], ...]  (value: number | number[] | Vector3 | Color), frames are GLOBAL film frames.
 *   opts.interp: 'ease' (default: each segment eased by the key's ease name, default opts.ease='inOutSine'),
 *                'linear', 'catmull' (C1-smooth Catmull-Rom through all keys; time-aware tangents), 'step'.
 *   Outside the key range the first/last value is held.
 */
export function track(keys, opts = {}) {
  const ks = keys.map(k => (Array.isArray(k) ? { f: k[0], v: k[1], e: k[2] } : k)).sort((a, b) => a.f - b.f);
  const interp = opts.interp || 'ease';
  const defEase = opts.ease || (interp === 'linear' ? 'linear' : 'inOutSine');
  const isArr = Array.isArray(ks[0].v), isVec = ks[0].v && ks[0].v.isVector3, isCol = ks[0].v && ks[0].v.isColor;
  const toArr = v => (typeof v === 'number' ? [v] : Array.isArray(v) ? v : isVec ? [v.x, v.y, v.z] : isCol ? [v.r, v.g, v.b] : v);
  const A = ks.map(k => toArr(k.v));
  const fromArr = a => (typeof ks[0].v === 'number' ? a[0] : isArr ? a : isVec ? new THREE.Vector3(a[0], a[1], a[2]) : isCol ? new THREE.Color(a[0], a[1], a[2]) : a);
  return function (n) {
    if (n <= ks[0].f) return fromArr(A[0].slice());
    const L = ks.length - 1;
    if (n >= ks[L].f) return fromArr(A[L].slice());
    let i = 0; while (i < L && ks[i + 1].f <= n) i++;
    const f0 = ks[i].f, f1 = ks[i + 1].f, u = (n - f0) / (f1 - f0);
    if (interp === 'step') return fromArr(A[i].slice());
    if (interp === 'catmull') {
      const p0 = A[Math.max(0, i - 1)], p1 = A[i], p2 = A[i + 1], p3 = A[Math.min(L, i + 2)];
      const fm = ks[Math.max(0, i - 1)].f, fp = ks[Math.min(L, i + 2)].f, dt = f1 - f0;
      const h00 = 2 * u ** 3 - 3 * u ** 2 + 1, h10 = u ** 3 - 2 * u ** 2 + u, h01 = -2 * u ** 3 + 3 * u ** 2, h11 = u ** 3 - u ** 2;
      const out = p1.map((v, j) => {
        const m1 = (i === 0 ? (p2[j] - p1[j]) / dt : (p2[j] - p0[j]) / (f1 - fm)) * dt;
        const m2 = (i + 1 === L ? (p2[j] - p1[j]) / dt : (p3[j] - p1[j]) / (fp - f0)) * dt;
        return h00 * v + h10 * m1 + h01 * p2[j] + h11 * m2;
      });
      return fromArr(out);
    }
    const e = interp === 'linear' ? ease.linear : easeFn(ks[i].e || defEase);
    const w = e(u);
    return fromArr(A[i].map((v, j) => v + (A[i + 1][j] - v) * w));
  };
}
/** Smooth spline through 3D points with frame keys -> f(n) -> Vector3 (alias of track(..., {interp:'catmull'})). */
export const spline = (keys, opts = {}) => track(keys, { interp: 'catmull', ...opts });

/**
 * cameraRig({ pos, target, fov, roll, up, shake }) -> { apply(camera, n), pos(n), target(n) }
 *   pos / target: track() functions or key arrays ([[frame, [x,y,z]], ...]); key arrays default to Catmull-Rom.
 *   fov: number | track | key array (vertical degrees).  roll: degrees (number | track | keys).
 *   shake: { amp:[x,y,z] metres, rot: degrees, freq: Hz, seed } — smooth hand-held drift (deterministic).
 */
export function cameraRig(spec) {
  const asTrack = (v, interp = 'catmull') => (v == null ? null : typeof v === 'function' ? v : Array.isArray(v) && Array.isArray(v[0]) ? track(v, { interp }) : () => v);
  const P = asTrack(spec.pos), T = asTrack(spec.target), F = asTrack(spec.fov, 'ease'), R = asTrack(spec.roll, 'ease');
  const up = new THREE.Vector3(...(spec.up || [0, 1, 0]));
  const sh = spec.shake;
  const v3 = a => (a.isVector3 ? a.clone() : new THREE.Vector3(a[0], a[1], a[2]));
  return {
    pos: n => v3(P(n)), target: n => v3(T(n)),
    apply(camera, n) {
      const p = v3(P(n)), t = T ? v3(T(n)) : p.clone().add(new THREE.Vector3(0, 0, -1));
      if (sh) {
        const tt = frameTime(n) * (sh.freq || 0.5), s = sh.seed || 7, a = sh.amp || [0.01, 0.01, 0.01];
        p.x += a[0] * fbm1(tt, s); p.y += a[1] * fbm1(tt, s + 1); p.z += a[2] * fbm1(tt, s + 2);
        const r = deg(sh.rot || 0);
        t.x += r * p.distanceTo(t) * fbm1(tt, s + 3); t.y += r * p.distanceTo(t) * fbm1(tt, s + 4);
      }
      camera.up.copy(up);
      camera.position.copy(p);
      camera.lookAt(t);
      if (R) camera.rotateZ(deg(R(n)));
      if (F && camera.isPerspectiveCamera) { const f = F(n); if (f !== camera.fov) { camera.fov = f; } }
      camera.updateProjectionMatrix();
      camera.updateMatrixWorld(true);
    },
  };
}

