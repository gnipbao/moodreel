// A remake's camera moved as its reference's was. `moodreel camera <reference> --js camera-data.js` reads the
// reference's picture motion window by window, 15 times a second (where its centre goes, px/s at 1920 wide; how fast
// it grows, %/s; how fast it turns, deg/s). follow() adds that motion to a smooth path through a few anchors, so the
// camera pans, tilts and pushes as the reference's did and still stands where the remake's own set needs it.
//
//   import { MOTION } from './camera-data.js';
//   import { follow } from './kit/follow.js';
//   const cam = follow(MOTION, [[20.7, { p: [0.5, 2.6, 5], l: [0, 2.8, 0], fov: 38 }], [33, { p: [3, 14, 10], l: [-12, 2, -14] }],
//     [46.4, { p: [50, 12, -40] }], [48, { f: 2, roll: 0.3 }]], 55, { own: [[18, 20.75]] });
//   draw: const c = cam(t); camera.position.set(...c.p); camera.lookAt(...c.l); camera.rotateZ(c.roll); camera.fov = c.fov;
//
// An anchor [t, { p, l, fov, roll, f, focus, ease }]: with p and l it sets where the camera stands and looks at t; with
// p alone, where it stands; fov, roll and f (depth-of-field blur) carry on from the last anchor that set them; focus
// (the sharp distance) is the anchor's own, the look distance when it has none.
// Between anchors the camera turns, tilts and pushes as measured, plus the smooth difference that meets each anchor.
// From remaking a 64 s one-take 3D film (skills/moodreel/references/distill/remaking.md, "The camera, measured"):
//   - the picture moving x px right is the camera turning left by x / f, f = 540 / tan(fov / 2) at 1920 x 1080
//   - the picture growing is the camera moving along its view at that moment, integrated along the path (after a long
//     pull-back a pan turns where the camera now stands, not where it began); two anchors that aim at different
//     distances move nothing (a camera that flew forward between them passed its subject)
//   - roll comes from the anchors alone: summed, the measured roll drifts (a motion-blurred whip reads as a turn it
//     never undoes, 96 degrees by the end of one film)
//   - a crane or a sideways move shows as little in the fit (the tilt that keeps the subject in frame cancels it):
//     anchors give those
//   - own: spans where the measurement reads the subject, not the camera (a dark frame full of falling pieces, a
//     critter the camera tracks): there the anchors are plain keyframes
const clamp = (x, a, b) => Math.max(a, Math.min(b, x));
const lerp = (a, b, u) => a + (b - a) * u;
const wrap = a => Math.atan2(Math.sin(a), Math.cos(a));
const D2R = Math.PI / 180;
const aim = (p, l) => { const d = l.map((v, k) => v - p[k]), n = Math.hypot(...d); return { yaw: Math.atan2(d[0], -d[2]), pitch: Math.asin(d[1] / n), d: n }; };
const dirOf = (yaw, pitch) => [Math.sin(yaw) * Math.cos(pitch), Math.sin(pitch), -Math.cos(yaw) * Math.cos(pitch)];

// cubic through [t, { v: [...], ease }] keys with Catmull-Rom tangents; a key with ease (and the ends) stops there
export function hermite(keys, t, get) {
  if (t <= keys[0][0]) return get(keys[0][1]);
  const n = keys.length;
  if (t >= keys[n - 1][0]) return get(keys[n - 1][1]);
  let i = 0;
  while (keys[i + 1][0] < t) i++;
  const [t0, k0] = keys[i], [t1, k1] = keys[i + 1], h = t1 - t0, u = (t - t0) / h;
  const v0 = get(k0), v1 = get(k1);
  const tan = j => {
    if (j === 0 || j === n - 1 || keys[j][1].ease) return v0.map(() => 0);
    const a = get(keys[j - 1][1]), b = get(keys[j + 1][1]), dt = keys[j + 1][0] - keys[j - 1][0];
    return a.map((x, q) => (b[q] - x) / dt);
  };
  const m0 = tan(i), m1 = tan(i + 1);
  const h00 = 2 * u ** 3 - 3 * u * u + 1, h10 = u ** 3 - 2 * u * u + u, h01 = -2 * u ** 3 + 3 * u * u, h11 = u ** 3 - u * u;
  return v0.map((x, q) => h00 * x + h10 * h * m0[q] + h01 * v1[q] + h11 * h * m1[q]);
}

// the measured motion as running sums (content travel px, log scale), zero inside the `own` spans
function sums(MOTION, own) {
  const F = MOTION.fps, inOwn = t => own.some(([a, b]) => t >= a && t < b), c = [[0, 0, 0]];
  MOTION.rows.forEach((r, i) => { const w = inOwn((i + 0.5) / F) ? 0 : 1, q = c[c.length - 1];
    c.push([q[0] + w * r[0] / F, q[1] + w * r[1] / F, q[2] + w * r[2] / (100 * F)]); });
  return t => { const x = clamp(t * F, 0, c.length - 1.001), i = Math.floor(x), u = x - i; return c[i].map((v, k) => lerp(v, c[i + 1][k], u)); };
}

export function follow(MOTION, anchors, end, { own = [] } = {}) {
  const F = MOTION.fps, cum = sums(MOTION, own), t0 = anchors[0][0];
  const fpx = fov => 540 / Math.tan(fov * D2R / 2);
  const M = (t, fov) => { const c = cum(t); return [-c[0] / fpx(fov), c[1] / fpx(fov), c[2]]; };
  const carry = key => { let v = null; return anchors.map(([, a]) => (v = a[key] ?? v)); };
  const fovs = carry('fov').map(v => v ?? 35), rolls = carry('roll').map(v => v ?? 0), fs = carry('f').map(v => v ?? 0);
  const focs = anchors.map(([, a]) => a.focus ?? 0);
  // orientation and distance: the anchors that aim (p and l) minus the motion measured by then; the others carry it on
  let last = null, prev = null;
  const aims = anchors.map(([t, a], i) => {
    if (a.l) {
      const w = aim(a.p, a.l), m = M(t, fovs[i]);
      let yaw = w.yaw - m[0];
      if (last !== null) yaw = last + wrap(yaw - last);              // unwrapped: the path turns the short way
      last = yaw;
      prev = [yaw, w.pitch - m[1], Math.log(w.d) + m[2]];
    }
    return [t, { ease: a.ease, v: [...prev, fovs[i], rolls[i], fs[i], focs[i]] }];
  });
  const orient = t => {
    const [yr, pr, ld, fov, roll, f, focus] = hermite(aims, t, k => k.v), m = M(t, fov), d = Math.exp(ld - m[2]);
    return { yaw: yr + m[0], pitch: clamp(pr + m[1], -1.5, 1.5), d, mz: m[2], fov, roll, f, focus: focus || d };
  };
  // the push: how far the measured growth has moved the camera along its view, step by step (the anchors' own look
  // distances are where they aim, not a move: a change between them moves nothing)
  const N = Math.ceil((end - t0) * F) + 2, O = [[0, 0, 0]];
  for (let i = 1; i < N; i++) {
    const a = orient(t0 + (i - 1) / F), b = orient(t0 + i / F), dir = dirOf(b.yaw, b.pitch), step = a.d * (1 - Math.exp(-(b.mz - a.mz)));
    O.push(O[i - 1].map((v, k) => v + dir[k] * step));
  }
  const off = t => { const x = clamp((t - t0) * F, 0, N - 1.001), i = Math.floor(x), u = x - i; return O[i].map((v, k) => lerp(v, O[i + 1][k], u)); };
  const places = anchors.filter(([, a]) => a.p).map(([t, a]) => [t, { ease: a.ease, v: a.p.map((v, k) => v - off(t)[k]) }]);
  return t => {
    const o = orient(t), dir = dirOf(o.yaw, o.pitch), base = hermite(places, t, k => k.v), q = off(t);
    const p = base.map((v, k) => v + q[k]);
    return { p, l: p.map((v, k) => v + dir[k] * o.d), fov: o.fov, roll: o.roll, f: o.f, focus: o.focus };
  };
}
