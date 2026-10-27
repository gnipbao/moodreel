// A remake framed as its reference, subject by subject. `moodreel track <reference> --spec look.json --js track-data.js`
// has Jev (TypeSafe's vision model) box each named subject in the reference's frames, 8 times a second: TRACK[name] is
// [[t, seen, cx, cy, w, h], ...] in fractions of the frame. The remake knows where its own subjects stand (a few points
// each: a box's corners). At every tracked moment lock() finds, in one solve, the least change that puts every subject
// where the reference has it:
//
//   the camera         moved and turned (x, y, z, yaw, pitch); field of view and roll stay the remake's
//   moving subjects    slid along the axes they may move on (a critter on its surface: x and z; the film's points
//                      function puts it back on whatever is under it)
//
// against what Jev saw: each subject's box (the part inside the frame: a box cut by the frame is compared as cut), each
// weighed by how sure Jev is that it is there; and a subject Jev does not see in the reference is pushed out of the
// remake's frame (what the reference does not show, the remake should not either). The corrections are smoothed
// (Gaussians: the boxes jitter by a percent or two; the camera's over `smoothCam`, 0.3 s, so the lock adds no motion the
// reference hasn't - over 0.12 s it swam at 2.7 times the reference's speed; a subject's over `smoothMove`, 0.12 s, so it
// keeps its hops) and fade in and out at a span's ends unless it ends on a cut. Each moment's solve also stays near the
// one before (`hold`): solved alone, a moment where camera and subject could trade places picked either, and a critter
// whose remake camera craned up where the reference's held flew 31 units across the keyboard in a second. The
// remake's camera keeps its own fast motion (follow.js: the measured pans and pushes); the lock moves only where it
// stands and aims.
//
// A subject that is not one convex thing (a river, a town, a crowd) is given as { cloud: points }: its box is the box of
// those of its points that land inside the frame.
//
//   import { TRACK } from './track-data.js';
//   import { lock } from './kit/lock.js';
//   const L = lock(t => shot(t).cam, TRACK, {
//     set: { keyboard: () => KEYBOARD, plant: t => (t < 15.2 ? PLANT : null) },   // world points at t (null: not there)
//     moving: { critter: { points: (t, d) => critterPoints(t, d), axes: [0, 2] } }, // d: the offset tried, [x, y, z]
//   }, { spans: [[8.0, 14.383, 0.3, 0], [14.383, 18.2, 0, 0.3]] });                // [from, to, fade in, fade out]
//   draw: const c = L.cam(t); critter offset = L.move.critter(t)
//   window.REPORT = () => L.report;                    // node render/render.mjs report <film>: px off, before and after
import { THREE } from './gl.js';
import { hermite } from './follow.js';

const aim = (p, l) => { const d = l.map((v, k) => v - p[k]), n = Math.hypot(...d); return { yaw: Math.atan2(d[0], -d[2]), pitch: Math.asin(d[1] / n), d: n }; };
const dirOf = (yaw, pitch) => [Math.sin(yaw) * Math.cos(pitch), Math.sin(pitch), -Math.cos(yaw) * Math.cos(pitch)];
const smoothstep = (a, b, x) => { const u = Math.max(0, Math.min(1, (x - a) / (b - a))); return u * u * (3 - 2 * u); };

// ---- what part of the frame a set of points covers: clipped at the camera's near plane (every segment between two
// points, so a box reaching behind the camera keeps its front), projected, its hull clipped to the frame
const C3 = new THREE.PerspectiveCamera(36, 16 / 9, 0.05, 5000), V = new THREE.Vector3(), NEAR = 0.05;
function hull(P) {
  const p = [...P].sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  if (p.length < 3) return p;
  const cross = (o, a, b) => (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]), lo = [], hi = [];
  for (const q of p) { while (lo.length >= 2 && cross(lo[lo.length - 2], lo[lo.length - 1], q) <= 0) lo.pop(); lo.push(q); }
  for (const q of p.reverse()) { while (hi.length >= 2 && cross(hi[hi.length - 2], hi[hi.length - 1], q) <= 0) hi.pop(); hi.push(q); }
  return [...lo.slice(0, -1), ...hi.slice(0, -1)];
}
function clipToFrame(poly) {
  let out = poly;
  for (const [k, edge, keep] of [[0, 0, 1], [0, 1, -1], [1, 0, 1], [1, 1, -1]]) {
    const inside = q => (q[k] - edge) * keep >= 0, src = out;
    out = [];
    for (let i = 0; i < src.length; i++) {
      const a = src[i], b = src[(i + 1) % src.length];
      if (inside(a)) out.push(a);
      if (inside(a) !== inside(b)) { const u = (edge - a[k]) / (b[k] - a[k]); out.push([a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u]); }
    }
    if (!out.length) break;
  }
  return out;
}
const bbox = P => [Math.min(...P.map(q => q[0])), Math.min(...P.map(q => q[1])), Math.max(...P.map(q => q[0])), Math.max(...P.map(q => q[1]))];
// { box: [l, t, r, b] of the part in the frame (fractions), inFrame } or null when it is all behind the camera
export function visible(c, pts, aspect = 16 / 9) {
  C3.fov = c.fov; C3.aspect = aspect; C3.updateProjectionMatrix();
  C3.position.set(...c.p); C3.up.set(0, 1, 0); C3.lookAt(...c.l); C3.rotateZ(c.roll || 0); C3.updateMatrixWorld(true);
  const q = pts.map(p => V.set(p[0], p[1], p[2]).applyMatrix4(C3.matrixWorldInverse).toArray()), front = [];
  for (let i = 0; i < q.length; i++) {
    if (q[i][2] <= -NEAR) front.push(q[i]);
    for (let j = i + 1; j < q.length; j++) {
      const a = q[i], b = q[j];
      if ((a[2] + NEAR) * (b[2] + NEAR) < 0) { const u = (-NEAR - a[2]) / (b[2] - a[2]); front.push(a.map((v, k) => v + (b[k] - v) * u)); }
    }
  }
  if (!front.length) return null;
  const P = front.map(p => { V.set(p[0], p[1], p[2]).applyMatrix4(C3.projectionMatrix); return [(V.x + 1) / 2, (1 - V.y) / 2]; });
  const h = hull(P), cut = clipToFrame(h);
  return cut.length >= 3 ? { box: bbox(cut), inFrame: true } : { box: bbox(h), inFrame: false };
}
// a scattered subject: the box of its points inside the frame (none: as a solid, so it can be pulled back in)
function visibleCloud(c, pts, aspect) {
  const inFrame = [];
  for (const p of pts) {
    V.set(p[0], p[1], p[2]).applyMatrix4(C3.matrixWorldInverse);
    if (V.z > -NEAR) continue;
    V.applyMatrix4(C3.projectionMatrix);
    const x = (V.x + 1) / 2, y = (1 - V.y) / 2;
    if (x >= 0 && x <= 1 && y >= 0 && y <= 1) inFrame.push([x, y]);
  }
  return inFrame.length >= 2 ? { box: bbox(inFrame), inFrame: true } : visible(c, pts, aspect);
}
export function visibleOf(c, sub, aspect = 16 / 9) {
  if (!sub.cloud) return visible(c, sub, aspect);
  visible(c, sub.cloud.slice(0, 1), aspect);                 // sets up the camera
  return visibleCloud(c, sub.cloud, aspect);
}
// box against box, side by side, in fractions of the frame's height (x scaled by the aspect)
export function boxError(v, obs, aspect = 16 / 9) {
  if (!v) return [1, 1, 1, 1];
  return [(v.box[0] - obs[0]) * aspect, v.box[1] - obs[1], (v.box[2] - obs[2]) * aspect, v.box[3] - obs[3]];
}
// how much of the frame a subject the reference does not show takes in the remake
const presence = (v, aspect = 16 / 9) => (v && v.inFrame ? Math.sqrt((v.box[2] - v.box[0]) * aspect * (v.box[3] - v.box[1])) : 0);
const obsBox = ([, , cx, cy, w, h]) => [cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2];

// ---- Levenberg-Marquardt on a residual function of n parameters (numeric Jacobian)
function solve(f, n, iters = 40) {
  let x = new Array(n).fill(0), r = f(x), e = r.reduce((s, v) => s + v * v, 0), lam = 1e-2;
  for (let it = 0; it < iters; it++) {
    const J = [];
    for (let k = 0; k < n; k++) { const xk = x.slice(); xk[k] += 1e-4; const rk = f(xk); J.push(rk.map((v, i) => (v - r[i]) / 1e-4)); }
    const A = [...Array(n)].map((_, i) => [...Array(n)].map((_, j) => J[i].reduce((s, v, q) => s + v * J[j][q], 0)));
    const g = [...Array(n)].map((_, i) => J[i].reduce((s, v, q) => s + v * r[q], 0));
    let better = false;
    for (let tries = 0; tries < 8 && !better; tries++) {
      const M = A.map((row, i) => row.map((v, j) => v + (i === j ? lam * (v + 1e-9) : 0)));
      const dx = gauss(M, g.map(v => -v)), x2 = x.map((v, k) => v + dx[k]), r2 = f(x2), e2 = r2.reduce((s, v) => s + v * v, 0);
      if (e2 < e) { const gain = e - e2; x = x2; r = r2; e = e2; lam = Math.max(1e-7, lam / 3); better = true; if (gain < 1e-10) return { x, e }; }
      else lam *= 4;
    }
    if (!better) break;
  }
  return { x, e };
}
function gauss(M, v) {
  const n = v.length, A = M.map((row, i) => [...row, v[i]]);
  for (let c = 0; c < n; c++) {
    let p = c;
    for (let r = c + 1; r < n; r++) if (Math.abs(A[r][c]) > Math.abs(A[p][c])) p = r;
    [A[c], A[p]] = [A[p], A[c]];
    const d = A[c][c] || 1e-12;
    for (let r = 0; r < n; r++) if (r !== c) { const k = A[r][c] / d; for (let q = c; q <= n; q++) A[r][q] -= k * A[c][q]; }
  }
  return A.map((row, i) => row[n] / (row[i] || 1e-12));
}

// a camera moved by [dx, dy, dz, dyaw, dpitch] (world units, radians)
export function moveCam(c, D) {
  const a = aim(c.p, c.l), p = c.p.map((v, k) => v + D[k]), dir = dirOf(a.yaw + D[3], a.pitch + D[4]);
  return { ...c, p, l: p.map((v, k) => v + dir[k] * a.d) };
}
const centroid = pts => [0, 1, 2].map(k => pts.reduce((s, q) => s + q[k], 0) / pts.length);

export function lock(cam, TRACK, { set = {}, moving = {} }, { spans, weight = {}, keep = 0.02, keepMove = 0.01, hold = 0.03,
  absent = 0.15, away = 0.5, smoothCam = 0.3, smoothMove = 0.2, minSeen = 0.5, aspect = 16 / 9 } = {}) {
  const row = (name, t) => (TRACK[name] || []).find(r => Math.abs(r[0] - t) < 1e-6);
  const times = [...new Set(Object.values(TRACK).flat().map(r => r[0]))].sort((a, b) => a - b);
  const mov = Object.entries(moving).map(([n, m]) => [n, m.points, m.axes || [0, 1, 2]]);
  const report = { spans: [] }, camKeys = [], moveKeys = Object.fromEntries(mov.map(([n]) => [n, []]));
  const px = e => Math.round(Math.hypot(...e) / 2 * 1080 * 10) / 10;      // a box's error: the root of its sides' squares, px at 1080
  for (const [t0, t1] of spans) {
    const rep = { from: t0, to: t1, samples: 0, before: {}, after: {}, shown: {} }, add = (o, k, v) => { (o[k] = o[k] || []).push(v); };
    let last = null;                                   // the moment before's solution, in world units: [camera's 5, each subject's 3]
    for (const t of times.filter(t => t >= t0 && t < t1)) {
      const obs = n => { const r = row(n, t); return r ? { box: obsBox(r), seen: r[1], w: (weight[n] ?? 1) * r[1] } : null; };
      const setPts = Object.fromEntries(Object.entries(set).map(([n, f]) => [n, f(t)]).filter(([, p]) => p));
      const subjects = [...Object.keys(setPts), ...mov.map(([n]) => n)].map(n => [n, obs(n)]).filter(([, o]) => o);
      if (!subjects.some(([, o]) => o.seen >= minSeen)) continue;
      const c = cam(t), a = aim(c.p, c.l), sp = 0.1 * a.d, sa = 0.05;
      const zero = mov.map(([, f]) => f(t, [0, 0, 0]));
      const scale = zero.map(p => 0.1 * Math.hypot(...centroid(p.cloud || p).map((v, k) => v - c.p[k])));
      // parameters: the camera's five, then each moving subject's axes
      const unpack = x => {
        let k = 5;
        const cc = moveCam(c, [x[0] * sp, x[1] * sp, x[2] * sp, x[3] * sa, x[4] * sa]);
        const d = mov.map(([, , axes], i) => { const o = [0, 0, 0]; for (const ax of axes) o[ax] = x[k++] * scale[i]; return o; });
        return { cc, d };
      };
      const n = 5 + mov.reduce((s, [, , axes]) => s + axes.length, 0);
      const units = [sp, sp, sp, sa, sa, ...mov.flatMap(([, , axes], i) => axes.map(() => scale[i]))];
      const prior = last ? [...last.slice(0, 5), ...mov.flatMap(([, , axes], i) => axes.map(ax => last[5 + 3 * i + ax]))].map((v, k) => v / units[k]) : null;
      const pointsOf = (name, d) => { const i = mov.findIndex(([m]) => m === name); return i < 0 ? setPts[name] : mov[i][1](t, d[i]); };
      const res = x => {
        const { cc, d } = unpack(x), r = [];
        for (const [name, o] of subjects) {
          const v = visibleOf(cc, pointsOf(name, d), aspect);
          if (o.seen >= minSeen) for (const e of boxError(v, o.box, aspect)) r.push(e * o.w);
          else if (o.seen < absent) r.push(presence(v, aspect) * away * (weight[name] ?? 1));
        }
        for (let k = 0; k < n; k++) r.push(x[k] * (k < 5 ? keep : keepMove));
        if (prior) for (let k = 0; k < n; k++) r.push((x[k] - prior[k]) * hold);
        return r;
      };
      const s = solve(res, n), { cc, d } = unpack(s.x), D = [s.x[0] * sp, s.x[1] * sp, s.x[2] * sp, s.x[3] * sa, s.x[4] * sa];
      camKeys.push([t, D, t0]);
      last = [...D, ...d.flat()];
      mov.forEach(([name], i) => moveKeys[name].push([t, d[i], t0]));
      const none = mov.map(() => [0, 0, 0]);
      for (const [name, o] of subjects) {
        if (o.seen >= minSeen) {
          add(rep.before, name, px(boxError(visibleOf(c, pointsOf(name, none), aspect), o.box, aspect)));
          add(rep.after, name, px(boxError(visibleOf(cc, pointsOf(name, d), aspect), o.box, aspect)));
        } else if (o.seen < absent) add(rep.shown, name, presence(visibleOf(cc, pointsOf(name, d), aspect), aspect) > 0.02 ? 1 : 0);
      }
      rep.samples++;
    }
    const mean = o => Object.fromEntries(Object.entries(o).map(([k, v]) => [k, Math.round(v.reduce((s, x) => s + x, 0) / v.length * 100) / 100]));
    report.spans.push({ ...rep, before: mean(rep.before), after: mean(rep.after), shown: mean(rep.shown) });
  }
  // smoothed over time within a span, then a cubic through the smoothed keys; faded at a span's soft ends
  const curve = (keys, smooth) => {
    const sm = spans.map(([a]) => {
      const ks = keys.filter(k => k[2] === a);
      return ks.map(([t]) => {
        let wsum = 0; const acc = ks[0][1].map(() => 0);
        for (const [u, d] of ks) { const w = Math.exp(-((u - t) ** 2) / (2 * smooth * smooth)); wsum += w; d.forEach((v, k) => { acc[k] += w * v; }); }
        return [t, { v: acc.map(v => v / wsum) }];
      });
    });
    return t => {
      const i = spans.findIndex(([a, b]) => t >= a && t < b);
      if (i < 0 || !sm[i].length) return null;
      const [a, b, fin = 0.25, fout = 0.25] = spans[i];
      const ramp = (fin > 0 ? smoothstep(a, a + fin, t) : 1) * (fout > 0 ? 1 - smoothstep(b - fout, b, t) : 1);
      return hermite(sm[i], t, k => k.v).map(v => v * ramp);
    };
  };
  const camC = curve(camKeys, smoothCam), moves = Object.fromEntries(mov.map(([n]) => [n, curve(moveKeys[n], smoothMove)]));
  return {
    cam: t => { const c = cam(t), D = camC(t); return D ? moveCam(c, D) : c; },
    move: Object.fromEntries(mov.map(([n]) => [n, t => moves[n](t) || [0, 0, 0]])),
    report,
  };
}
