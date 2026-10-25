// Battery Low — the Signal Plates demo (24.4 s). A phone's battery falls from 20 % to 1 % while a plea is typed, a
// request is denied and the hook "SAVE IT" slams harder each time; on the last beat the screen goes black.
// The edit and every shared event are in timeline.js; the music is the film's own score (score.json -> music-data.js).
import { stage } from './kit/stage.js';
import { PALETTE, SIZE, LAYOUT } from './kit/tokens.js';
import { MOTION, enter } from './kit/motion.js';
import { ease } from './kit/eases.js';
import { faces, plate, voice, machine, font, karaoke, ticks, size } from './kit/signal.js';
import { engraved } from './kit/engraved.js';
import { lineField, swirl } from './kit/linefield.js';
import { prompt } from './kit/prompt.js';
import { form, paperGround, stamp } from './kit/form.js';
import { grain } from './kit/texture.js';
import { music, pop } from './kit/music.js';
import { rng, tween } from './kit/core.js';
import { AUDIO, LYRICS } from './music-data.js';
import { BEAT, b, DUR, shotAt, value, dropAt, HOOKS, PLEA, RETYPE, REQUEST, FOOTNOTE, line, sparkU, letterTimes } from './timeline.js';

const [W, H] = SIZE, LEFT = Math.round(LAYOUT.margin * W);
const M = music(AUDIO, LYRICS);
const P = plate(W, H);
const L = P.G.lines(120000);
const clamp = (x, a = 0, b_ = 1) => Math.max(a, Math.min(b_, x));
const lerp = (a, z, u) => a + (z - a) * u;

// ---- the cell: an engraved battery lying a little tilted, + terminal right, the charge a hot band at the left end
const TILT = -0.16;
const cell = engraved(P.G, { axis: [1, 0, 0], freq: 30, glowFill: 0.12, glsl: /* glsl */ `
  uniform float uLevel, uPulse, uFlicker;
  vec3 local(vec3 p) { p.xy = rot2(${TILT.toFixed(3)}) * p.xy; return p; }
  float sdCyl(vec3 p, float h, float r, float k) { vec2 d = vec2(length(p.yz) - r + k, abs(p.x) - h + k); return min(max(d.x, d.y), 0.0) + length(max(d, 0.0)) - k; }
  float map(vec3 p) {
    p = local(p);
    float body = sdCyl(p, 1.35, 0.56, 0.08);
    float nub = sdCyl(p - vec3(1.43, 0.0, 0.0), 0.12, 0.2, 0.04);
    float seam = abs(p.x - 0.95) - 0.012;
    return smin(max(body, -max(seam, length(p.yz) - 0.55)), nub, 0.04);
  }
  vec3 glow(vec3 p, vec3 n) {
    p = local(p);
    float edge = -1.35 + uLevel * 2.7;
    float band = 1.0 - smoothstep(edge - 0.01, edge + 0.01, p.x);
    float lit = 0.55 + 0.45 * max(0.0, dot(n, normalize(vec3(-0.5, 0.6, 0.6))));
    vec3 nl = n; nl.xy = rot2(${TILT.toFixed(3)}) * nl.xy;
    float side = 1.0 - smoothstep(0.35, 0.8, abs(nl.x));                    // the band is on the barrel, not the end cap
    return C_SIGNAL * (2.0 + 2.5 * uPulse) * band * side * lit * (1.0 - uFlicker);
  }`, uniforms: { uLevel: { value: 0.2 }, uPulse: { value: 0 }, uFlicker: { value: 0 } } });

const toWorld = ([x, y, z]) => [x * Math.cos(TILT) - y * Math.sin(TILT), x * Math.sin(TILT) + y * Math.cos(TILT), z];
const CAM = {
  wide: { eye: [-2.6, 1.5, 6.6], target: [-1.55, 0.1, 0], fov: 30 },
  band: { eye: [-4.2, 1.1, 3.4], target: [-1.0, -0.1, 0], fov: 30 },
  term: { eye: [3.3, 0.55, 2.4], target: [1.45, -0.25, 0], fov: 30 },
};
const dolly = (c, k) => ({ ...c, eye: c.eye.map((e, i) => lerp(e, c.target[i], k)) });   // k of the way in
const orbit = (c, deg) => {                                                   // turned `deg` about the target's up axis
  const a = deg * Math.PI / 180, [ex, ey, ez] = c.eye.map((e, i) => e - c.target[i]);
  return { ...c, eye: [c.target[0] + ex * Math.cos(a) + ez * Math.sin(a), c.target[1] + ey, c.target[2] - ex * Math.sin(a) + ez * Math.cos(a)] };
};

// a world point to stage px, through a camera (the shader's camera, in JS)
function project({ eye, target, fov }, p) {
  const sub = (a, z) => a.map((x, i) => x - z[i]), dot = (a, z) => a.reduce((s, x, i) => s + x * z[i], 0);
  const norm = a => { const m = Math.hypot(...a); return a.map(x => x / m); };
  const cross = (a, z) => [a[1] * z[2] - a[2] * z[1], a[2] * z[0] - a[0] * z[2], a[0] * z[1] - a[1] * z[0]];
  const f = norm(sub(target, eye)), r = norm(cross(f, [0, 1, 0])), u = cross(r, f), d = sub(p, eye);
  const fl = 0.5 / Math.tan((fov * Math.PI) / 360), z = Math.max(1e-3, dot(d, f));
  return [W / 2 + (dot(d, r) / z) * fl * H, H / 2 - (dot(d, u) / z) * fl * H];
}

// the charging cable, in the cell's own space: from below the frame up into the + terminal
const CABLE = (() => {
  const a = [3.6, -3.6, 1.6], c1 = [3.3, -1.0, 1.3], c2 = [2.6, -0.05, 0.5], z = [1.58, 0, 0], out = [];
  for (let i = 0; i <= 120; i++) {
    const u = i / 120, v = 1 - u;
    out.push(toWorld([0, 1, 2].map(k => v * v * v * a[k] + 3 * v * v * u * c1[k] + 3 * v * u * u * c2[k] + u * u * u * z[k])));
  }
  const len = [0];
  for (let i = 1; i < out.length; i++) len.push(len[i - 1] + Math.hypot(...out[i].map((x, k) => x - out[i - 1][k])));
  return { pts: out, len, total: len[len.length - 1] };
})();
// the cable up to the spark (u 0..1 of its length), as stage points through a camera; the spark's world point
function cableTo(cam, u) {
  const d = u * CABLE.total, pts = [];
  let head = CABLE.pts[0];
  for (let i = 0; i < CABLE.pts.length; i++) {
    if (CABLE.len[i] <= d) { pts.push(project(cam, CABLE.pts[i])); head = CABLE.pts[i]; continue; }
    const k = (d - CABLE.len[i - 1]) / (CABLE.len[i] - CABLE.len[i - 1]);
    head = CABLE.pts[i - 1].map((x, j) => lerp(x, CABLE.pts[i][j], k));
    pts.push(project(cam, head));
    break;
  }
  return { pts, head };
}

// the spark and its line: a hairline dragged behind, its last stretch still hot, a bright core and sputtering sparks
function spark(t, pts, { burst = 1, line = 1, ahead = null } = {}) {
  const q = P.type.ctx, hot = P.hot.ctx;
  if (ahead?.length > 1) {                                                    // the cable still to run, faint
    q.save(); q.strokeStyle = PALETTE.graphite; q.globalAlpha = 0.6; q.lineWidth = 1.2; q.setLineDash([3, 6]);
    q.beginPath(); ahead.forEach(([x, y], i) => (i ? q.lineTo(x, y) : q.moveTo(x, y))); q.stroke(); q.restore();
  }
  if (pts.length < 2) return;
  q.save();
  q.lineWidth = 1.3;
  q.strokeStyle = PALETTE.graphite;
  q.globalAlpha = line;
  q.beginPath();
  pts.forEach(([x, y], i) => (i ? q.lineTo(x, y) : q.moveTo(x, y)));
  q.stroke();
  q.lineWidth = 2;
  let run = 0;
  for (let i = pts.length - 1; i > 0 && run < 160; i--) {
    const [x0, y0] = pts[i - 1], [x1, y1] = pts[i];
    q.globalAlpha = line * (1 - run / 160) ** 1.5;
    q.strokeStyle = PALETTE.signal;
    q.beginPath(); q.moveTo(x0, y0); q.lineTo(x1, y1); q.stroke();
    run += Math.hypot(x1 - x0, y1 - y0);
  }
  q.restore();
  const [hx, hy] = pts[pts.length - 1], f = Math.round(t * 60), r = rng(5000 + f);
  hot.save();
  hot.fillStyle = PALETTE.ember;
  hot.beginPath(); hot.arc(hx, hy, 5.5 * burst ** 0.5, 0, Math.PI * 2); hot.fill();
  hot.fillStyle = '#FFF4E6';
  hot.beginPath(); hot.arc(hx, hy, 2.4, 0, Math.PI * 2); hot.fill();
  for (let i = 0; i < Math.round(9 * burst); i++) {                       // thrown off, seeded by the frame
    const a = r() * Math.PI * 2, d = 6 + r() * 34 * burst ** 0.7, s = 1 + r() * 1.6;
    hot.globalAlpha = 0.4 + 0.6 * r();
    hot.fillStyle = r() < 0.5 ? PALETTE.signal : PALETTE.ember;
    hot.beginPath(); hot.arc(hx + Math.cos(a) * d, hy + Math.sin(a) * d * 0.7, s, 0, Math.PI * 2); hot.fill();
  }
  hot.restore();
}

// ---- the fields: a contour ground wound round a point, and lines drawn into a point (cached: their flow holds still)
const C0 = [W * 0.66, H * 0.5];
const ground = lineField({ count: 420, steps: 90, h: 8, seed: 9, W, H, still: true,
  spawn: r => { const a = r() * Math.PI * 2, d = 380 + 420 * Math.sqrt(r()); return [C0[0] + Math.cos(a) * d, C0[1] + Math.sin(a) * d * 0.62]; },
  flow: (x, y, t) => swirl(x, y, t, { scale: 1 / 900, around: C0, spin: 2.6, pull: 0, octaves: 1 }) });
const DRAIN = [W * 0.64, H * 0.52];
const drain = lineField({ count: 1100, steps: 70, h: 8, seed: 4, W, H, still: true,
  flow: (x, y, t) => swirl(x, y, t, { scale: 1 / 520, around: DRAIN, spin: 0.9, pull: 0.75 }) });
function contours(t, { alpha = 0.2, grow = 1, at = C0, turn = 0.06 } = {}) {
  const a = turn * surge(t, 0) * BEAT, c = Math.cos(a), s = Math.sin(a), dx = at[0] - C0[0], dy = at[1] - C0[1];
  ground.draw(L, t, { tone: () => 0.15, alpha, grow, w: 2,
    xf: (x, y) => [C0[0] + (x - C0[0]) * c - (y - C0[1]) * s + dx, C0[1] + (x - C0[0]) * s + (y - C0[1]) * c + dy] });
  flush();                                                                    // the ground goes down before the cell
}
const flush = () => { if (L.count) { L.render(P.hdr); L.clear(); } };

// ---- type
// a sung line in the voice: words dim until sung, lit in signal while sung, then bone
function sungLine(q, ln, x, y, t, px = size('lineSmall')) {
  if (!ln || t < ln.start - 0.45 || t > ln.end + 0.85) return;
  const sh = shotAt(t), gone = ln.end < exitAt(sh) ? out(t, Math.max(ln.end + 0.05, exitAt(sh)), 'power2.out') : 0;
  const fin = inn(t, Math.max(sh.t0, ln.start - 0.45), 1);
  q.save();
  q.globalAlpha *= fin * (1 - gone);                                          // rises in; leaves rising, before the cut
  q.translate(0, (1 - fin) * 30 - gone * 30);
  font(q, voice(px, { weight: 300, width: 100 }));
  q.textBaseline = 'alphabetic';
  const space = q.measureText(' ').width;
  let cx = x;
  for (const w of ln.words) {
    const u = clamp((t - w.start) / Math.max(0.05, w.end - w.start));
    cx += karaoke(q, w.w, cx, y, u, { lit: t < w.end ? PALETTE.signal : PALETTE.bone }) + space;
  }
  q.restore();
}
// a value pinned in the world: a leader line, the number in signal, a note in ash
function pin(q, [x, y], t, { dx = 70, dy = -150, note = 'CHARGE  −1 % / BAR' } = {}) {
  if (y + dy < 130) dy = Math.abs(dy);                                        // keep the label inside the title-safe frame
  if (x + dx + 240 > W - 96) dx = -Math.abs(dx) - 240;
  const v = String(value(t)).padStart(2, '0') + ' %', lx = x + dx, ly = y + dy;
  const sh = shotAt(t), at = Math.max(dropAt(t), sh.t0), p = inn(t, at, sh.i);
  const gone = sh.z - sh.a >= 2 ? out(t, exitAt(sh)) : 0;
  q.save();
  q.globalAlpha = p * (1 - gone);
  q.strokeStyle = PALETTE.graphite; q.lineWidth = 1;
  q.beginPath(); q.moveTo(x, y - 8); q.lineTo(lx, ly + 18); q.lineTo(lx + 220, ly + 18); q.stroke();
  q.translate((1 - p) * -50, -gone * 40);                                     // slides in; rises away
  font(q, machine(size('note'), 500));
  q.fillStyle = PALETTE.signal;
  q.fillText(v, lx + 8, ly);
  font(q, machine(size('small'), 400));
  q.fillStyle = PALETTE.ash;
  q.fillText(note, lx + 8, ly + 44);
  q.restore();
}
// the value full screen: a counter that rolls on each drop, a meter under it
function readout(q, t) {
  const v = value(t), at = dropAt(t), u = ease(MOTION.count?.ease ?? 'power2.inOut')(clamp((t - at) / (MOTION.count?.duration ?? 0.11)));
  const prev = String(Math.min(20, v + 1)).padStart(2, '0'), cur = String(v).padStart(2, '0');
  const px = Math.round(0.3 * H), x = LEFT, y = Math.round(H * 0.62), s0 = shotAt(t).t0;
  const drop = inn(t, s0, 1), num = inn(t, s0, 0), grow = inn(t, s0 + 0.08, 1);   // drops in; pops in; grows
  font(q, machine(size('note'), 500));
  q.fillStyle = PALETTE.ash;
  q.globalAlpha = drop;
  q.fillText('BATTERY', x + 6, y - px * 0.92 - (1 - drop) * 40);
  q.globalAlpha = 1;
  const lk = M.lastHit('kick', t), kp = lk && t - lk[0] < 0.4 ? 1 - ease(MOTION.move.ease)(clamp((t - lk[0]) / MOTION.move.duration)) : 0;
  q.save();
  const sc = (0.86 + 0.14 * num) * (1 + 0.05 * kp);                          // pops in where it stands; a kick pops it
  q.globalAlpha = clamp(num * 1.5);
  q.translate(x, y); q.scale(sc, sc); q.translate(-x, -y);
  q.beginPath(); q.rect(x - 10, y - px * 0.82, W, px * 0.98); q.clip();
  font(q, machine(px, 700));
  q.fillStyle = PALETTE.signal;
  if (u < 1 && at > 0) {
    q.globalAlpha = 1 - u; q.fillText(prev, x, y - u * px * 0.9);
    q.globalAlpha = u; q.fillText(cur, x, y + (1 - u) * px * 0.9);
    q.globalAlpha = 1;
  } else q.fillText(cur, x, y);
  const w = q.measureText('00').width;
  font(q, machine(Math.round(px * 0.45), 500));
  q.fillText('%', x + w + px * 0.08, y);
  q.restore();
  const mw = W * 0.42, my = y + px * 0.22;                                   // the meter: hairline box, ticks, fill
  q.strokeStyle = PALETTE.graphite; q.lineWidth = 1;
  q.strokeRect(x + 0.5, my + 0.5, mw, 18);
  for (let i = 1; i < 10; i++) q.fillRect(x + (mw * i) / 10, my + 18, 1, 8);
  q.fillStyle = PALETTE.signal;
  q.fillRect(x + 3, my + 3, grow * (mw - 6) * (v / 100) * (u < 1 && at > 0 ? lerp((v + 1) / v, 1, u) : 1), 13);
}

// the hook, slammed: its look escalates each time (width condenses, then expands; copies pack in; it glows)
const HOOK_LOOK = [
  { width: 100, px: 0.197, copies: 0, shake: 10 },
  { width: 75, px: 0.26, copies: 2, shake: 14 },
  { width: 62.5, px: 0.34, copies: 4, shake: 20 },
  { width: 125, px: 0.36, copies: 0, shake: 26, stacked: true },
];
function hook(q, t, k) {
  const { save, it } = HOOKS[k], look = HOOK_LOOK[k], px = Math.round(look.px * H);
  const S = M.slams([save.start, it.start], { amt: 0.14 + 0.03 * k, shake: look.shake });
  const sl = S(t), y = Math.round(H * (look.stacked ? 0.44 : 0.6));
  const push = t >= it.start ? ease(MOTION.move.ease)(clamp((t - it.start) / MOTION.move.duration)) : 0;
  const shot = shotAt(t), leave = out(t, exitAt(shot));
  q.save();
  q.translate(LEFT + sl.x, y + sl.y - push * 0.025 * H);
  q.scale(sl.s, sl.s);
  font(q, voice(px, { weight: 900, width: look.width }));
  q.textBaseline = 'alphabetic';
  for (let c = 1; c <= look.copies; c++) {                                  // copies pack in above and below, on beats
    for (const dir of [-1, 1]) {
      const p = enter(t, save.start + ((c - 1) * 2 + (dir > 0 ? 1 : 0)) * BEAT / 4, 0);
      if (p <= 0) continue;
      q.globalAlpha = clamp(p * 1.4) * (0.5 - 0.08 * c) * (1 - leave);
      q.fillStyle = c % 2 ? PALETTE.graphite : PALETTE.panel;
      q.fillText('SAVE IT', (1 - p) * -60 * dir + leave * 260 * dir, dir * c * px * 0.86);
    }
  }
  q.globalAlpha = 1;
  if (t >= save.start - 0.3) {
    const sw = karaoke(q, 'SAVE', 0, 0, clamp((t - save.start) / Math.max(0.05, save.end - save.start)),
      { lit: t < save.end ? PALETTE.signal : PALETTE.bone, dim: t < save.start ? 0.35 : 1, base: t < save.start ? PALETTE.bone : PALETTE.bone });
    if (t >= it.start) {
      const ix = look.stacked ? 0 : sw + px * 0.22, iy = look.stacked ? px * 0.9 : 0;
      const pp = pop(t - it.start, 0.16, 1.2);
      q.save();
      q.translate(ix, iy + pp.dy * px * 0.04);
      q.scale(pp.s, pp.s);
      q.fillStyle = PALETTE.signal;
      q.fillText('IT', 0, 0);
      if (k >= 2) { const hq = P.hot.ctx; hq.save(); hq.setTransform(q.getTransform()); font(hq, voice(px, { weight: 900, width: look.width }));
        hq.globalAlpha = 0.35 * M.hit('kick', t, 0.15) + 0.15; hq.fillStyle = PALETTE.ember; hq.fillText('IT', 0, 0); hq.restore(); }
      q.restore();
    }
  }
  q.restore();
}

// ---- the plates
// the drums as the reference answers them (moodreel sync): a kick shakes the frame, dying with a 0.067 s half-life;
// a snare at 0.85 of that. No frame-wide punch.
const downbeat = t => { const d = M.downbeats.filter(x => x <= t).pop(); return d === undefined ? 0 : 0.5 ** ((t - d) / 0.05); };
const kick = t => Math.max(M.hit('kick', t, 0.067), 0.85 * M.hit('snare', t, 0.067), 1.6 * downbeat(t));
function cellPlate(t, cam, { pulse = 0, flicker = 0 } = {}) {
  cell.u.uLevel.value = value(t) / 100;
  cell.u.uPulse.value = pulse;
  cell.u.uFlicker.value = flicker;
  cell.look(cam.eye, cam.target, cam.fov);
  cell.render(P.hdr, t);
}
const creep = (s, t, amt = 0.04) => 1 + amt * clamp((M.ct(t) - s.t0) / (s.t1 - s.t0));     // the beat-clock creep

// the style's motion (kit/motion.js, STYLE.md §5): an entrance eases out over MOTION.enter.duration, every other one
// overshooting ~5 %; an exit accelerates away over MOTION.exit.duration; a move is short and overshoots ~6 %
const inn = (t, at, k = 0) => tween(t, at, MOTION.enter.duration, k % 2 ? MOTION.enter.ease : MOTION.enter.overshoot_ease);
const out = (t, at, how = MOTION.exit.ease) => tween(t, at, MOTION.exit.duration, how);
const mv = (t, at) => tween(t, at, MOTION.move.duration, MOTION.move.ease);
// the surge: from `from`, every beat steps on by one and every off-beat (the hats) by a half, each step a short move
// that settles, then holds to the next (the reference moves on the eighths too: hat -> motion, moodreel sync)
const EIGHTHS = M.beats.flatMap(x => [[x, 1], [x + BEAT / 2, 0.5]]);
function surge(t, from) {
  let sum = 0, last = null;
  for (const [x, w] of EIGHTHS) {
    if (x < from - 0.02 || x > t) continue;
    if (last) sum += last[1];
    last = [x, w];
  }
  return last ? sum + last[1] * mv(t, last[0]) : 0;
}
const exitAt = s => s.t1 - MOTION.exit.duration - 0.08;                      // leave before the cut, seen to the end

function draw(g, t) {
  const s = shotAt(t), u = (t - s.t0) / (s.t1 - s.t0);
  const q = P.type.ctx;
  let post = { hit: 0, zoom: 1, shake: [0, 0], flash: 0 };
  const dark = s.kind !== 'form' && s.kind !== 'formClose' && s.kind !== 'stamp';
  P.begin({ paper: !dark });
  L.clear();
  switch (s.kind) {
    case 'cursor': {                                                          // a blinking cursor on a black plate
      const on = (M.beatAt(t) % 1) < 0.5;
      if (on) { q.fillStyle = PALETTE.signal; q.fillRect(LEFT + 4, H * 0.5 - 40, 26, 50); }
      const p = inn(t, b(0.25), 0), out = tween(t, exitAt(s), MOTION.exit.duration, MOTION.exit.ease);
      font(q, machine(size('small'), 500));
      q.globalAlpha = p * (1 - out); q.fillStyle = PALETTE.ash;
      q.fillText('LOW POWER MODE  ·  20 %', LEFT, H * 0.5 - 70 + (1 - p) * 12 - out * 30);
      q.globalAlpha = 1;
      post.zoom = 1 + 0.015 * surge(t, s.t0);
      break;
    }
    case 'field': {                                                           // the contour ground draws itself on
      contours(t, { alpha: 0.32, grow: 0.1 + 0.9 * clamp(surge(t, s.t0) / 5.5) });      // draws itself on in steps
      pin(q, [C0[0], C0[1]], t, { note: 'CHARGE' });
      post.zoom = 1 + 0.015 * surge(t, s.t0);
      break;
    }
    case 'band': {                                                            // close on the charge, punched by the kicks
      const flick = s.a === 31 ? (Math.round(t * 60) % 5 < 2 ? 0.8 : 0) : 0;
      contours(t, { alpha: 0.12 });
      const bcam = orbit(dolly(CAM.band, 0.03 * surge(t, s.t0)), -3 * surge(t, s.t0));
      cellPlate(t, bcam, { pulse: kick(t), flicker: flick });
      const bp = project(bcam, toWorld([-1.35 + (value(t) / 100) * 1.35, 0.57, 0]));
      pin(q, bp, t, { dx: 90, dy: -170 });
      post.hit = kick(t);
      break;
    }
    case 'readout': readout(q, t); post.zoom = 1 + 0.015 * surge(t, s.t0); post.hit = kick(t) * 0.6; break;
    case 'cell': case 'follow': {                                             // the cell, the spark climbing its cable
      const cam = orbit(dolly(CAM.wide, 0.025 * surge(t, s.t0)), 2.5 * surge(t, s.t0));      // steps on the beat
      contours(t, { alpha: 0.2 });
      cellPlate(t, cam, { pulse: kick(t) * 0.5 });
      const c = cableTo(cam, sparkU(t));
      spark(t, c.pts, { ahead: cableTo(cam, 1).pts.slice(c.pts.length - 1) });
      sungLine(q, s.kind === 'cell' ? line('my', 8) : line('before', 20), LEFT, Math.round(H * 0.2), t);
      if (s.kind === 'follow') {                                              // follow the spark: lean toward it
        const [hx, hy] = c.pts[c.pts.length - 1];
        post.shake = [(W / 2 - hx) * 0.25 * u, (H / 2 - hy) * 0.25 * u];
      }
      post.hit = kick(t) * 0.6;
      break;
    }
    case 'spark': case 'last': {                                              // close on the spark
      const u0 = sparkU(t), here = cableTo(CAM.wide, u0).head;
      const term = toWorld([1.58, 0, 0]), mid = here.map((x, i) => (x + term[i]) / 2);   // the spark and where it is going
      const cam = s.kind === 'last' ? CAM.term : { eye: [mid[0] + 0.9, mid[1] + 0.7, mid[2] + 4.6], target: mid, fov: 30 };
      contours(t, { alpha: 0.1 });
      cellPlate(t, cam, { flicker: s.kind === 'last' && (Math.round(t * 60) % 4 < 2) ? 0.7 : 0 });
      const c = cableTo(cam, u0);
      spark(t, c.pts, { burst: s.kind === 'last' ? 2.4 : 1, ahead: cableTo(cam, 1).pts.slice(c.pts.length - 1) });
      post.zoom = 1 + 0.015 * surge(t, s.t0);
      if (s.kind === 'last') post.flash = 0.25 * Math.max(0, 1 - Math.abs(t - b(47.5)) / 0.04);
      break;
    }
    case 'drain': case 'dim': {                                               // lines drawn into the point where it goes
      const fade = s.kind === 'dim' ? lerp(1, 0.35, clamp(u * 3)) : 1;
      drain.draw(L, t, { tone: (x, y) => 1 - Math.min(1, Math.hypot(x - DRAIN[0], y - DRAIN[1]) / 750), alpha: 0.38 * fade, w: 1.1,
        pulse: { at: s.t0, speed: 60, length: 10, gain: 2.5 } });
      P.hot.ctx.fillStyle = PALETTE.signal;
      P.hot.ctx.beginPath(); P.hot.ctx.arc(DRAIN[0], DRAIN[1], 5 + 3 * kick(t), 0, Math.PI * 2); P.hot.ctx.fill();
      pin(q, DRAIN, t, { dx: 80, dy: -190, note: 'DRAIN  ·  SCREEN 100 %' });
      sungLine(q, line('the', 12), LEFT, Math.round(H * 0.2), t);
      post.zoom = 1 + 0.015 * surge(t, s.t0);
      post.hit = kick(t);
      break;
    }
    case 'idle': case 'prompt': case 'retype': case 'whip': {                // the plea, typed as tokens
      const toWhip = s.kind === 'whip' && u >= 0.5;
      if (toWhip) {                                                           // the whip lands on the cell from the right
        cellPlate(t, CAM.wide);
        contours(t, { alpha: 0.2 });
        spark(t, cableTo(CAM.wide, sparkU(t)).pts);
        post.shake = [W * 1.1 * (1 - ease('power3.out')((u - 0.5) * 2)), 0];
        post.edge = 1;
        break;
      }
      contours(t, { alpha: 0.2 });
      const tokens = s.kind === 'idle' ? [] : s.kind === 'retype' ? RETYPE.map(x => ({ ...x, alts: [[x.text, 0.97], ['stop', 0.02]] }))
        : PLEA.map((x, k) => ({ ...x, alts: [[['save', 0.71], ['close', 0.12], ['lose', 0.06]], [['your', 0.88], ['all', 0.07]],
          [['work', 0.58], ['files', 0.21], ['tabs', 0.09], ['face', 0.04]]][k].map(([w, p]) => [w, p]) }));
      prompt(q, s.kind === 'whip' ? b(19.4) : t, { x: LEFT, y: Math.round(H * 0.5), w: 760, px: size('lineSmall') + 6, appear: s.kind === 'retype' ? b(39) : b(15),
        label: `LOW POWER  ·  ${String(value(t)).padStart(2, '0')} %`, meta: 'battery_saver: on', tokens });
      if (s.kind === 'whip') { post.shake = [-W * 1.1 * ease('power3.in')(u * 2), 0]; post.edge = 1; }
      post.hit = kick(t) * 0.4;
      break;
    }
    case 'form': case 'formClose': case 'stamp': {                            // inversion to paper: the request, denied
      paperGround(P);
      font(q, voice(size('line'), { weight: 800, width: 100 }));
      q.fillStyle = PALETTE.ground;
      const tp = enter(t, b(24), 0);
      q.globalAlpha = clamp(tp * 1.5);
      q.fillText('Power saving.', LEFT + (1 - tp) * -40, Math.round(H * 0.17));
      q.globalAlpha = 1;
      const rows = [
        { label: 'REQUEST', value: REQUEST.text, t0: REQUEST.t0, t1: REQUEST.t1 },
        { label: 'TIME REMAINING', value: '00:04:12', t0: b(24.5), t1: b(25) },
        { label: 'I UNDERSTAND THE SCREEN WILL GO DARK', tick: true, t0: b(27) },
      ];
      q.save();
      rows.forEach((r, i) => { r.in = enter(t, b(24), i + 1); });
      form(q, t, { x: LEFT, y: Math.round(H * 0.3), w: 900, title: 'FORM 7  ·  REQUEST FOR MORE TIME', fields: rows });
      q.restore();
      if (s.kind === 'stamp') {
        stamp(q, t, { text: 'DENIED', at: b(28), x: LEFT + 760, y: Math.round(H * 0.74), angle: -0.12 });
        const k = Math.max(0, 1 - (t - b(28)) / 0.25), r = rng(Math.round(t * 60));
        post.shake = [(r() - 0.5) * 30 * k, (r() - 0.5) * 30 * k];
      }
      if (s.kind === 'formClose') { post.zoom = 1.45 + 0.012 * surge(t, s.t0); post.shake = [W * 0.17, H * 0.02]; }
      break;
    }
    case 'hook': {
      const k = HOOKS.findIndex(h => h.save.start >= s.t0 - 0.05 && h.save.start < s.t1);
      contours(t, { alpha: 0.12 + 0.04 * k, turn: 0.1 });
      hook(q, t, k);
      post.hit = kick(t) * (1 + 0.3 * k);
      if (k === 3) post.flash = 0.18 * Math.max(0, 1 - (t - HOOKS[3].it.start) / 0.12) * (t >= HOOKS[3].it.start ? 1 : 0);
      break;
    }
    case 'black': {                                                           // the screen goes; only the line stays
      const fade = clamp(1 - (t - b(48)) / b(3));
      if (fade > 0) spark(t, cableTo(CAM.wide, 1).pts, { burst: 0, line: fade * 0.6 });
      P.hot.ctx.clearRect(0, 0, W, H);
      const typed = letterTimes(FOOTNOTE).filter(([, at]) => at <= t).map(([c]) => c).join('');
      if (typed) {
        font(q, machine(size('small') + 4, 500));
        q.fillStyle = PALETTE.ash;
        q.fillText(typed, LEFT, H - 150);
        if ((M.beatAt(t) % 1) < 0.5) q.fillRect(LEFT + q.measureText(typed).width + 6, H - 166, 10, 20);
      }
      break;
    }
  }
  if (dark && s.kind !== 'black') ticks(q, W, H);
  if (post.zoom === 1 && s.kind !== 'black' && s.kind !== 'whip') post.zoom = 1 + 0.012 * surge(t, s.t0);
  flush();
  P.end(g, t, post);
}

stage({ width: W, height: H, duration: DUR, background: PALETTE.ground, prepare: faces, draw,
  finish: (g, t) => {                                                         // grain once per frame, after the blur
    const s = shotAt(t), paper = s.kind === 'form' || s.kind === 'formClose' || s.kind === 'stamp';
    grain(g, 1.2, Math.round(t * 60), { ground: paper ? PALETTE.bone : PALETTE.ground });
  } });
