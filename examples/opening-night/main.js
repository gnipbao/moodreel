// opening-night: three instruments play their first night, on 1930s Rubber Hose Cartoon (styles/rubber-hose). The
// score comes first (score.json: a sampled band, stride piano, tuba, trumpets and horn, clarinet, timpani) and every
// entrance, freeze and hit lands on one of its cues. Characters on twos with a boiling line, ink constant in screen
// space, a painted stage cached once, then the print: a 4:3 gate, weave, flicker, scratches, dust and a vignette.
import { stage, texts } from './kit/stage.js';
import { tween, clamp, lerp, hash, noise1, step } from './kit/core.js';
import { grain } from './kit/texture.js';
import { cue, bar, SCORE } from './score.js';

const W = 1920, H = 1080, GX = 240, GW = 1440, FLOOR = 905, BEAT = SCORE.beat_s;
// a cool silver-nitrate print: characters own white and ink; the set lives in the middle greys
const INK = '#0b0c0d', WHITE = '#fbfcfc', SHADE = '#c4c8cb', BODY = '#17191b';
const GREY = ['#2a2e31', '#3f4448', '#565c61', '#6f757a', '#8a9095', '#a7adb1'];
const INKW = 6;
const SCRIPT = '"SignPainter", "Snell Roundhand", cursive', CAPS = '"Copperplate", "Copperplate Gothic Light", serif';

const PIANO_IN = bar(2), FREEZE = cue('freeze'), PEEK = cue('peek'), LEAP = cue('leap'), TADA = cue('tada');
const REACH = cue('reach'), END = cue('end'), CARD = [REACH + BEAT / 2, END];      // the card lands on the end chord
const CURTAIN = [cue('curtain'), cue('curtain') + 0.7], DROP = [cue('tuba') - 0.4, cue('tuba')], GRIP = 330;

// --- the rig toolkit: points transformed first, then stroked, so the ink stays 6 px however a body squashes ---------
let BOIL = 0;                                             // which of three drawings (the line boils at 12 fps)
let BELL = null;                                          // the tuba's bell this frame: the clarinet hides in it
const rig = (x, y, sx = 1, sy = 1, r = 0) => {
  const c = Math.cos(r), s = Math.sin(r);
  return (px, py) => [x + px * sx * c - py * sy * s, y + px * sx * s + py * sy * c];
};
const wob = (id, i) => [1.2 * (hash(id * 97.3 + i * 13.1 + BOIL * 71.7) * 2 - 1), 1.2 * (hash(id * 51.9 + i * 7.7 + BOIL * 33.1) * 2 - 1)];
const pts = (R, list, id) => list.map(([x, y], i) => { const [X, Y] = R(x, y), [dx, dy] = wob(id, i); return [X + dx, Y + dy]; });
const ell = (cx, cy, rx, ry, n = 32, rot = 0, a0 = 0, a1 = 2 * Math.PI) => Array.from({ length: n }, (_, i) => {
  const a = a0 + (a1 - a0) * i / (a1 - a0 >= 2 * Math.PI - 1e-6 ? n : n - 1), x = rx * Math.cos(a), y = ry * Math.sin(a);
  return [cx + x * Math.cos(rot) - y * Math.sin(rot), cy + x * Math.sin(rot) + y * Math.cos(rot)];
});
const rrect = (x0, y0, x1, y1, r) => [[x1 - r, y0 + r, -Math.PI / 2], [x1 - r, y1 - r, 0], [x0 + r, y1 - r, Math.PI / 2],
  [x0 + r, y0 + r, Math.PI]].flatMap(([cx, cy, a]) => ell(cx, cy, r, r, 5, 0, a, a + Math.PI / 2));
function trace(g, P, close = true) {
  g.beginPath();
  g.moveTo(P[0][0], P[0][1]);
  for (let i = 1; i < P.length; i++) g.lineTo(P[i][0], P[i][1]);
  if (close) g.closePath();
}
// a filled shape with its ink; light from the upper left leaves one hard band of shade on the lower right
function form(g, R, list, id, { fill = WHITE, ink = INKW, shade = 0, stroke = INK } = {}) {
  const P = pts(R, list, id);
  trace(g, P);
  g.fillStyle = shade ? SHADE : fill;
  g.fill();
  if (shade) {
    g.save(); trace(g, P); g.clip();
    trace(g, P.map(([x, y]) => [x - shade, y - shade]));
    g.fillStyle = fill; g.fill();
    g.restore();
  }
  if (ink) { trace(g, P); g.lineWidth = ink; g.lineJoin = 'round'; g.strokeStyle = stroke; g.stroke(); }
  return P;
}
const line = (g, a, b, w = 3, color = INK) => {
  g.beginPath(); g.moveTo(a[0], a[1]); g.lineTo(b[0], b[1]); g.lineWidth = w; g.lineCap = 'round'; g.strokeStyle = color; g.stroke();
};
// a rubber-hose limb: one width all along, one smooth bend, round ends
function hose(g, a, b, bend, w = 14, id = 1) {
  const dx = b[0] - a[0], dy = b[1] - a[1], L = Math.hypot(dx, dy) || 1, [jx, jy] = wob(id, 0);
  g.beginPath(); g.moveTo(a[0], a[1]);
  g.quadraticCurveTo((a[0] + b[0]) / 2 - dy / L * bend + jx, (a[1] + b[1]) / 2 + dx / L * bend + jy, b[0], b[1]);
  g.lineCap = 'round'; g.lineWidth = w; g.strokeStyle = INK; g.stroke();
}
// a white four-finger glove pointing along a: palm, three fat fingers, a thumb, a flared cuff; the union outlined
function glove(g, X, Y, a, s = 46, { open = 0, side = 1, grip = 0 } = {}) {
  const R = rig(X, Y, 1, side, a), parts = [ell(0.42 * s, 0, 0.36 * s, 0.31 * s, 20)];
  for (const k of [-1, 0, 1]) {
    const ang = k * (0.3 + 0.35 * open), len = (0.3 - 0.1 * grip) * s;
    parts.push(ell(0.42 * s + Math.cos(ang) * 0.36 * s, Math.sin(ang) * 0.36 * s, len, 0.12 * s, 16, ang));
  }
  parts.push(ell(0.3 * s, -0.32 * s, 0.2 * s, 0.11 * s, 14, -1.0 - 0.5 * open));
  parts.push([[-0.24 * s, -0.31 * s], [0.08 * s, -0.2 * s], [0.08 * s, 0.2 * s], [-0.24 * s, 0.31 * s]]);
  const P = parts.map((p, i) => pts(R, p, 900 + i));
  g.lineJoin = 'round'; g.strokeStyle = INK; g.lineWidth = 2 * INKW;
  for (const p of P) { trace(g, p); g.stroke(); }
  g.fillStyle = WHITE;
  for (const p of P) { trace(g, p); g.fill(); }
  for (const k of [-1, 0, 1]) line(g, R(0.28 * s, k * 0.09 * s), R(0.52 * s, k * 0.11 * s), 2.5);
  line(g, R(-0.07 * s, -0.24 * s), R(-0.07 * s, 0.24 * s), 2.5);
}
// a big black shoe with a white glint on the toe; d turns the toe left or right
function shoe(g, X, Y, d, s = 64) {
  const R = rig(X, Y, d, 1);
  form(g, R, ell(0.2 * s, -0.25 * s, 0.6 * s, 0.3 * s, 26), 700, { fill: INK, ink: 0 });
  form(g, R, ell(0.52 * s, -0.4 * s, 0.13 * s, 0.06 * s, 10, -0.4), 701, { ink: 0 });
}
// a pie eye: a white oval, a pupil 64 % x 74 % of it with a wedge cut toward the upper right; a lid for blinks
function eye(g, R, cx, cy, rx, ry, id, { look = [0, 0], blink = 0, lid = WHITE } = {}) {
  const O = form(g, R, ell(cx, cy, rx, ry, 28), id, { ink: 0 });
  g.save(); trace(g, O); g.clip();
  const px = cx + look[0] * rx * 0.3, py = cy + look[1] * ry * 0.22 + ry * 0.08;
  const pie = [[px, py], ...ell(px, py, rx * 0.64, ry * 0.74, 26, 0, -0.17 * Math.PI, 1.61 * Math.PI)];
  form(g, R, pie, id + 1, { fill: INK, ink: 0 });
  if (blink > 0) {
    const yl = cy - ry + 2 * ry * blink;
    form(g, R, [[cx - rx * 1.2, cy - ry * 1.2], [cx + rx * 1.2, cy - ry * 1.2], [cx + rx * 1.2, yl], [cx - rx * 1.2, yl]], id + 2, { fill: lid, ink: 0 });
    line(g, ...pts(R, [[cx - rx, yl], [cx + rx, yl]], id + 3), 4);
  }
  g.restore();
  trace(g, O); g.lineWidth = INKW - 1; g.strokeStyle = INK; g.stroke();
}
// a mouth: a smile with cheek ticks, or an open grin (ink, a grey tongue), or a surprised O
function mouth(g, R, cx, cy, w, id, { open = 0, o = false, on = WHITE } = {}) {
  const dark = on !== WHITE;                               // on a black body the mouth is drawn in white
  if (o) { form(g, R, ell(cx, cy, w * 0.14, w * 0.18, 16), id, { fill: dark ? GREY[1] : INK, ink: dark ? 3 : 0, stroke: WHITE }); return; }
  if (open > 0) {
    const P = form(g, R, [[cx - w / 2, cy - w * 0.08], ...ell(cx, cy - w * 0.08, w / 2, w * 0.5 * open, 18, 0, 0, Math.PI)], id,
      { fill: dark ? GREY[0] : INK, ink: dark ? 3 : 4, stroke: dark ? WHITE : INK });
    g.save(); trace(g, P); g.clip();
    form(g, R, ell(cx + w * 0.08, cy - w * 0.08 + w * 0.42 * open, w * 0.24, w * 0.16 * open + 4, 14), id + 1, { fill: SHADE, ink: 0 });
    g.restore();
    return;
  }
  const P = pts(R, ell(cx, cy - w * 0.3, w / 2, w * 0.38, 16, 0, 0.18 * Math.PI, 0.82 * Math.PI), id);
  trace(g, P, false); g.lineWidth = 5; g.lineCap = 'round'; g.strokeStyle = dark ? WHITE : INK; g.stroke();
  for (const [e, s] of [[P[0], 1], [P[P.length - 1], -1]]) line(g, [e[0] + s * 4, e[1] - 9], [e[0] - s * 3, e[1] + 6], 4, dark ? WHITE : INK);
}

// --- time: the band's clock freezes on the stop; the characters are drawn on twos -----------------------------------
const band = t => (t >= FREEZE && t < FREEZE + BEAT ? FREEZE : t);
const beats = t => t / BEAT;
const since = (b, k0, period) => (((b - k0) % period) + period) % period;          // beats since the last k0 + n period
const breath = (t, amp) => amp * Math.cos(2 * Math.PI * beats(t));           // stretch on the beat, squash off it
const ampAt = t => (t >= bar(6) && t < TADA ? 0.15 : 0.05);                   // the peak: three times as wide
const pose = t => tween(t, TADA - 0.125, 0.125, 'power3.out');               // the ta-da, landing on its beat
const watch = t => tween(t, REACH, 0.15, 'power2.out');                       // the others drop their arms to watch the reach
const BLINKS = { piano: [5.5, 9.1], tuba: [6.3, 10.6], clar: [9.6, 11.3] };
const blinkAt = (who, t) => (BLINKS[who].some(b => t >= b && t < b + 2 / 12) ? 1 : 0);

// --- the cast ------------------------------------------------------------------------------------------------------
function piano(g, t) {
  const tm = band(t), b = beats(tm), up = pose(t) * (1 - watch(t)), playing = t >= PIANO_IN && t < TADA;
  const a = breath(tm, ampAt(tm)), x = 400;
  const R = rig(x, FLOOR - 4, 1 - 0.7 * a, 1 + a);
  for (const d of [-1, 1]) {
    const hip = R(d * 95, -80), foot = [x + d * 125, FLOOR];
    hose(g, hip, [foot[0] - d * 10, foot[1] - 22], -d * 18, 15, 10 + d);
    shoe(g, foot[0], foot[1], d, 72);
  }
  const lid = playing ? 0.4 * Math.exp(-since(b, 1, 2) * BEAT * 6) : 0;          // the lid jumps on every chord
  form(g, R, rrect(-200, -478 - 26 * lid, 200, -446 - 26 * lid, 10), 20, { fill: BODY, ink: 4 });
  form(g, R, rrect(-185, -450, 185, -70, 24), 21, { fill: BODY, ink: 4 });
  line(g, R(-160, -432), R(-160, -300), 4, GREY[3]);                            // a shine on the black
  for (const d of [-1, 1]) { const P = pts(R, rrect(d > 0 ? 20 : -150, -175, d > 0 ? 150 : -20, -98, 10), 22 + d); trace(g, P); g.lineWidth = 4; g.strokeStyle = GREY[1]; g.stroke(); }
  form(g, R, rrect(-148, -428, 148, -262, 22), 24, { shade: 12 });              // the face: the music desk
  const look = t >= REACH ? [1, -0.4] : t >= TADA ? [0, 0] : t >= LEAP + 0.2 ? [0.6, 0.1] : tm >= FREEZE + BEAT ? [1, -0.1] : t >= DROP[1] ? [1, 0] : [0.4, 0.2];
  for (const d of [-1, 1]) eye(g, R, d * 54, -352, 32, 44, 30 + d * 5, { look, blink: blinkAt('piano', t) });
  mouth(g, R, 0, -296, up ? 96 : 84, 40, { open: up * 0.8 });
  form(g, R, [[-186, -258], [186, -258], [186, -206], [-186, -206]], 41);       // the keys
  for (let i = 1; i < 20; i++) line(g, ...pts(R, [[-186 + i * 18.6, -258], [-186 + i * 18.6, -206]], 50 + i), 2);
  for (let i = 0; i < 19; i++) if ([1, 2, 4, 5, 6].includes(i % 7)) form(g, R, [[-182 + i * 18.6, -258], [-170 + i * 18.6, -258], [-170 + i * 18.6, -230], [-182 + i * 18.6, -230]], 80 + i, { fill: INK, ink: 0 });
  form(g, R, [[-196, -206], [196, -206], [196, -190], [-196, -190]], 42, { fill: BODY, ink: 4 });
  // stride: the left glove on 1 and 3, the right on 2 and 4, lifting between
  const lift = p => 36 * Math.sin(Math.PI * p) ** 0.7;
  const lh = playing ? lift((b % 2) / 2) : 0, rh = playing ? lift(((b + 1) % 2) / 2) : 0;
  for (const [d, hl] of [[-1, lh], [1, rh]]) {
    const sh = R(d * 190, -236);                                                 // from the keyboard's ends
    const hand = up ? [x + d * (150 + 120 * up), FLOOR - 470 - 120 * up] : R(d * 75, -268 - hl);
    hose(g, sh, hand, up ? d * 30 : -d * 30, 15, 60 + d);
    glove(g, hand[0], hand[1], up ? -Math.PI / 2 + d * 0.5 : Math.PI / 2 - d * 0.35, 54, { side: d, open: up });
  }
}

function tuba(g, t) {
  if (t < DROP[0]) return;
  const tm = band(t), b = beats(tm), up = pose(t) * (1 - watch(t)), playing = t >= DROP[1] && t < TADA;
  const fall = t < DROP[1] ? (1 - tween(t, DROP[0], DROP[1] - DROP[0], 'power2.in')) * -1000 : 0;
  const u = (b % 2) / 2, since = (b % 2) * BEAT;
  const hop = playing ? -26 * 4 * u * (1 - u) : 0;
  const land = t >= DROP[1] ? 0.28 * Math.exp(-(t - DROP[1]) * 7) * Math.cos((t - DROP[1]) * 26) : 0;
  const sq = (playing ? 0.1 * Math.exp(-since * 9) : 0) + land;
  const a = breath(tm, ampAt(tm)) - sq, x = 1010, y = FLOOR - 4 + fall + hop;
  const R = rig(x, y, 1 - 0.7 * a, 1 + a);
  for (const d of [-1, 1]) {
    const foot = [x + d * 72, Math.min(FLOOR, y + 4)];
    hose(g, R(d * 50, -70), [foot[0] - d * 8, foot[1] - 20], -d * 14, 15, 110 + d);
    shoe(g, foot[0], foot[1], d, 68);
  }
  // the bell: a cone flaring up and to the right from the coil, a dark mouth; it flares on every oom
  const flare = 1 + (playing ? 0.12 * Math.exp(-since * 8) : 0);
  const rim = [168, -505], rx = 84 * flare, ry = 30 * flare, rot = 0.38;      // the mouth faces along the tube
  const rl = [rim[0] - rx * Math.cos(rot), rim[1] - rx * Math.sin(rot)], rr = [rim[0] + rx * Math.cos(rot), rim[1] + rx * Math.sin(rot)];
  const q = (p0, c, p1) => Array.from({ length: 9 }, (_, i) => { const s = i / 8; return [(1 - s) ** 2 * p0[0] + 2 * s * (1 - s) * c[0] + s * s * p1[0], (1 - s) ** 2 * p0[1] + 2 * s * (1 - s) * c[1] + s * s * p1[1]]; });
  form(g, R, [...q([56, -318], [80, -390], rl), ...q(rr, [160, -370], [120, -292])], 120, { shade: 10 });
  form(g, R, ell(rim[0], rim[1], rx, ry, 28, rot), 121, { shade: 0 });
  form(g, R, ell(rim[0] + 2, rim[1] + 3, rx - 16, ry - 11, 24, rot), 122, { fill: INK, ink: 0 });
  BELL = { c: R(...rim), rx, ry, rot, lip: pts(R, ell(rim[0], rim[1], rx, ry, 16, rot, 0, Math.PI), 123) };
  for (const [i, vx] of [-58, -24, 10].entries()) {                              // three valves
    form(g, R, rrect(vx, -392, vx + 22, -340, 6), 130 + i, { shade: 5 });
    form(g, R, ell(vx + 11, -394, 15, 6, 12), 135 + i);
  }
  form(g, R, ell(0, -212, 152, 158, 40), 140, { shade: 16 });                    // the coil: the whole tuba is the body
  const coil = pts(R, ell(0, -212, 112, 118, 24, 0, 0.62 * Math.PI, 1.38 * Math.PI), 141);
  trace(g, coil, false); g.lineWidth = 4; g.strokeStyle = INK; g.stroke();
  const look = t >= REACH ? [1, -0.6] : t >= TADA ? [0, 0] : t >= LEAP - BEAT / 4 ? [-0.8, 0] : tm >= FREEZE + BEAT ? [0.6, -1] : [-1, 0];
  for (const d of [-1, 1]) eye(g, R, d * 42, -246, 27, 37, 150 + d * 5, { look, blink: blinkAt('tuba', t) });
  form(g, R, ell(0, -208, 10, 8, 10), 160, { fill: INK, ink: 0 });
  mouth(g, R, 0, -168, up ? 90 : 78, 161, { open: up * 0.8 });
  // arms: swung out on the oom, in on the pah; up for the ta-da
  const swing = playing ? 40 * Math.cos(Math.PI * b) : 0;
  for (const d of [-1, 1]) {
    const sh = R(d * 148, -220);
    const hand = up ? [x + d * (180 + 110 * up), y - 470 - 120 * up] : [x + d * 200, y - 210 - d * swing];
    hose(g, sh, hand, d * 30, 15, 170 + d);
    glove(g, hand[0], hand[1], up ? -Math.PI / 2 + d * 0.5 : (d > 0 ? 0 : Math.PI) - d * 0.3, 52, { side: d, open: up });
  }
  // a ring puffs from the bell on every oom, scattered and growing (a row of puffs would read as a thought)
  for (let L = DROP[1]; L < Math.min(tm, TADA); L += 2 * BEAT) {
    const age = tm - L;                                                          // held, like everything, on the stop
    if (age < 0 || age > 1.3) continue;
    const dir = hash(L * 7.1) < 0.5 ? -1 : 1, s = 0.4 + age;
    const [cx, cy] = R(rim[0] + dir * 70 * age + 20 * age, rim[1] - 170 * age);
    const P = pts(rig(cx, cy), ell(0, 0, 34 * s, 18 * s, 22, 0.3 * dir), 180 + Math.round(L));
    trace(g, P); g.lineWidth = 9 * (1 - age / 1.3); g.strokeStyle = SHADE; g.stroke();
  }
}

function clarinet(g, t) {
  if (t < FREEZE) return;
  const tm = band(t), b = beats(tm), up = pose(t);
  const TILT = Math.atan2(Math.sin(BELL.rot), Math.cos(BELL.rot));               // stands along the bell's tube
  const inBell = rise => [BELL.c[0] - Math.sin(TILT) * (520 - 256 * rise), BELL.c[1] + Math.cos(TILT) * (520 - 256 * rise)];
  const ducked = 1 - 0.35 * tween(t, FREEZE + BEAT, 0.12);
  let x, y, r = TILT, s = 0, lift = 0;
  if (t < LEAP - BEAT / 2) {                                                      // pops up in the bell, glances, ducks
    const take = t >= PEEK ? 0.18 * Math.sin(Math.PI * clamp((t - PEEK) / 0.2)) : 0;   // a double take on the tick
    [x, y] = inBell((tween(t, FREEZE, 0.15, 'back.out(2)') + take) * ducked);
    s = t >= FREEZE + BEAT ? -0.15 * tween(t, FREEZE + BEAT, 0.12) : 0;
  } else if (t < LEAP) {                                                          // springs out, one arc onto the brass hit
    const u = (t - (LEAP - BEAT / 2)) / (BEAT / 2), [x0, y0] = inBell(ducked);
    x = lerp(x0, 720, u); y = lerp(y0, FLOOR - 4, u); lift = 280 * 4 * u * (1 - u); s = 0.18; r = lerp(TILT, -0.15, u);
  } else {
    x = 720;
    const d = t - LEAP;
    s = -0.25 * Math.exp(-d * 8) * Math.cos(d * 24);
    r = t < TADA ? 0.12 * Math.cos(Math.PI * b) * clamp(d / 0.3) : 0;            // sways: an extreme on every beat
    if (t >= REACH) { const k = tween(t, REACH, BEAT / 2, 'power3.out'); r = 0.32 * k; s = 0.16 * k; }   // leans into the reach
  }
  if (t >= LEAP) { x = 720; y = FLOOR - 4; }
  const a = (t >= LEAP ? breath(tm, ampAt(tm)) : 0) + s;
  y -= lift;
  const hidden = t < LEAP - BEAT / 2;                                             // only what is out of the bell shows
  if (hidden) {
    const [cx, cy] = BELL.c, m = [Math.cos(BELL.rot), Math.sin(BELL.rot)], ax = [m[1], -m[0]];
    g.save(); g.beginPath();
    g.moveTo(cx - m[0] * 3000, cy - m[1] * 3000); g.lineTo(cx + m[0] * 3000, cy + m[1] * 3000);
    g.lineTo(cx + m[0] * 3000 + ax[0] * 3000, cy + m[1] * 3000 + ax[1] * 3000); g.lineTo(cx - m[0] * 3000 + ax[0] * 3000, cy - m[1] * 3000 + ax[1] * 3000);
    g.closePath(); g.clip();
  }
  const R = rig(x, y, 1 - 0.7 * a, 1 + a, r);
  for (const d of [-1, 1]) {
    const foot = lift || hidden ? R(d * 50, 30) : [x + d * 58, FLOOR];
    hose(g, R(d * 26, -46), [foot[0] - d * 6, foot[1] - 18], -d * 12, 13, 210 + d);
    shoe(g, foot[0], foot[1], d, 58);
  }
  form(g, R, [[-34, -110], [34, -110], [68, -44], [-68, -44]], 220, { fill: BODY, ink: 4 });     // the bell
  form(g, R, ell(0, -44, 68, 14, 22), 221, { fill: BODY, ink: 4 });
  form(g, R, rrect(-34, -432, 34, -104, 14), 222, { fill: BODY, ink: 4 });                      // the tube
  for (const [i, ky] of [-170, -232].entries()) form(g, R, [[-34, ky - 5], [34, ky - 5], [34, ky + 5], [-34, ky + 5]], 223 + i, { fill: GREY[4], ink: 2 });
  for (const [i, ky] of [-140, -200, -262, -300].entries()) form(g, R, ell(0, ky, 7, 7, 10), 226 + i, { fill: GREY[5], ink: 2 });
  line(g, R(-20, -420), R(-20, -330), 4, GREY[3]);
  form(g, R, rrect(-26, -480, 26, -428, 8), 230, { fill: BODY, ink: 4 });                       // the barrel
  const wag = t >= LEAP && t < TADA ? 0.2 * Math.sin(2 * Math.PI * b) : 0;      // the mouthpiece carries the mood
  const RM = rig(...R(0, -480), 1, 1, r + wag);
  form(g, RM, [[-18, 0], [18, 0], [10, -38], [-10, -38]], 231, { fill: BODY, ink: 4 });
  form(g, RM, [[-5, -2], [5, -2], [4, -34], [-4, -34]], 232, { ink: 2 });
  const look = t < PEEK ? [0, 0] : t < FREEZE + BEAT ? [-1, 0] : t < LEAP ? [-0.8, -0.3] : t >= TADA ? [0, 0] : [0.3 * Math.sin(Math.PI * b / 4), 0.2];
  for (const d of [-1, 1]) eye(g, R, d * 22, -384, 23, 31, 240 + d * 5, { look, blink: blinkAt('clar', t), lid: BODY });
  mouth(g, R, 0, -334, 42, 250, { o: t < LEAP, open: t >= TADA ? 0.5 + 0.4 * up : 0, on: BODY });
  // arms: on the keys while it plays; up for the ta-da; then the right one stretches off stage for the card
  const reach = tween(t, REACH, BEAT / 2, 'power3.out');
  for (const d of [-1, 1]) {
    const sh = R(d * 34, -300);
    let hand, ang, open = 0;
    if (d > 0 && t >= REACH) {
      hand = t < CARD[0] ? [lerp(x + 140, GW + 80, reach), lerp(FLOOR - 560, GRIP, reach)] : [cardX(t) - 8, GRIP];
      ang = 0; open = 0;
    } else if (up) {
      hand = [x + d * (120 + 100 * up), y - 520 - 110 * up]; ang = -Math.PI / 2 + d * 0.5; open = up;
    } else if (t >= LEAP) {
      hand = R(d * 4, -246 + d * 50 + 4 * Math.sin(2 * Math.PI * b)); ang = d > 0 ? Math.PI : 0;
    } else {
      hand = R(d * 70, -150); ang = Math.PI / 2;
    }
    hose(g, sh, hand, d > 0 && t >= REACH ? -160 * reach : d * 26, 13, 260 + d);   // the reach arcs over the tuba
    if (!(d > 0 && t >= CARD[0])) glove(g, hand[0], hand[1], ang, 46, { side: d, open });
  }
  if (hidden) {                                                                   // the bell's near lip, back in front
    g.restore();
    trace(g, BELL.lip, false); g.lineCap = 'round'; g.lineWidth = 16; g.strokeStyle = INK; g.stroke();
    g.lineWidth = 6; g.strokeStyle = WHITE; g.stroke();
  }
}

// --- the set: painted once, watercolour washes in the middle greys -----------------------------------------------
const LAYERS = {};
function canvas(k) {
  const c = document.createElement('canvas');
  c.width = Math.round(GW * k); c.height = Math.round(H * k);
  const q = c.getContext('2d');
  q.setTransform(k, 0, 0, k, 0, 0);
  return [c, q];
}
function wash(q, shape, color, seed, { blot = 0.05, edge = 0.22, outline = true } = {}) {
  q.save(); shape(q); q.clip();
  q.fillStyle = color; q.fillRect(0, 0, GW, H);
  let n = seed;
  const r = () => hash(n++ * 1.37);
  for (let i = 0; i < 30; i++) {                                                // soft blotches, +-5 %
    const x = r() * GW, y = r() * H, rad = 60 + r() * 240, light = r() < 0.5;
    const gr = q.createRadialGradient(x, y, 0, x, y, rad);
    gr.addColorStop(0, light ? `rgba(255,255,255,${blot})` : `rgba(0,0,0,${blot})`);
    gr.addColorStop(1, 'rgba(0,0,0,0)');
    q.fillStyle = gr; q.fillRect(x - rad, y - rad, 2 * rad, 2 * rad);
  }
  q.filter = 'blur(16px)'; shape(q); q.lineWidth = 46; q.strokeStyle = `rgba(0,0,0,${edge})`; q.stroke(); q.filter = 'none';
  q.restore();
  if (outline) { shape(q); q.lineWidth = 2.5; q.strokeStyle = GREY[0]; q.stroke(); }
}
function paper(q, seed) {                                                        // the paper's tooth, once
  const c = q.canvas, img = q.getImageData(0, 0, c.width, c.height), d = img.data;
  let a = seed;
  for (let i = 0; i < d.length; i += 4) {
    a = (a * 1103515245 + 12345) & 0x7fffffff;
    const v = ((a >> 8) % 17) - 8;
    d[i] += v; d[i + 1] += v; d[i + 2] += v;
  }
  q.putImageData(img, 0, 0);
}
// a crescent: the arc of one circle outside another, then the other's arc inside it, back
function crescent([ax, ay], ra, [bx, by], rb) {
  const away = Math.atan2(ay - by, ax - bx), arc = (cx, cy, r, keep) => Array.from({ length: 121 }, (_, i) => away - Math.PI + i * Math.PI / 60)
    .map(a => [cx + r * Math.cos(a), cy + r * Math.sin(a)]).filter(keep);
  const outer = arc(ax, ay, ra, ([x, y]) => Math.hypot(x - bx, y - by) > rb);
  const inner = arc(bx, by, rb, ([x, y]) => Math.hypot(x - ax, y - ay) < ra).reverse();
  return q => { q.beginPath(); [...outer, ...inner].forEach(([x, y], i) => (i ? q.lineTo(x, y) : q.moveTo(x, y))); q.closePath(); };
}
const P2 = (...xy) => q => { q.beginPath(); q.moveTo(xy[0], xy[1]); for (let i = 2; i < xy.length; i += 2) q.lineTo(xy[i], xy[i + 1]); q.closePath(); };
function paintSet(k) {
  const [back, q] = canvas(k);
  wash(q, P2(0, 0, GW, 0, GW, 770, 0, 770), GREY[3], 1, { outline: false });                 // the backdrop: a night sky
  const hill = (y0, amp, ph) => q => { q.beginPath(); q.moveTo(0, 770); for (let x = 0; x <= GW; x += 20) q.lineTo(x, y0 - amp * Math.sin(x / 260 + ph) - amp * 0.4 * Math.sin(x / 97 + 2 * ph)); q.lineTo(GW, 770); q.closePath(); };
  wash(q, hill(640, 50, 1.2), GREY[4], 7);
  wash(q, hill(700, 34, 3.1), GREY[2], 13);
  wash(q, crescent([1010, 230], 92, [1050, 205], 80), GREY[5], 19, { edge: 0.06 });
  for (let i = 0; i < 14; i++) {                                                // painted stars: four points
    const x = 220 + hash(i * 3.3) * 1000, y = 70 + hash(i * 5.1) * 420, s = 8 + hash(i * 7.7) * 9;
    if (Math.hypot(x - 1010, y - 230) < 140) continue;
    q.fillStyle = GREY[5]; q.beginPath();
    for (let j = 0; j < 8; j++) { const rr = j % 2 ? s * 0.3 : s, a = j * Math.PI / 4; q.lineTo(x + rr * Math.cos(a), y + rr * Math.sin(a)); }
    q.fill();
  }
  wash(q, P2(0, 770, GW, 770, GW, 1000, 0, 1000), GREY[2], 23);                 // the stage floor: boards
  for (let i = 0; i < 9; i++) { const y = 770 + 230 * ((i + 1) / 9) ** 1.3; q.beginPath(); q.moveTo(0, y); q.lineTo(GW, y); q.lineWidth = 2; q.strokeStyle = GREY[1]; q.stroke(); }
  paper(q, 5);
  const [legs, l] = canvas(k);                                                   // the wings: curtain legs
  for (const x0 of [0, GW - 168]) {
    wash(l, P2(x0, 0, x0 + 168, 0, x0 + 168, 1000, x0, 1000), GREY[1], 29 + x0, { edge: 0.3 });
    for (let f = 0; f < 4; f++) { l.beginPath(); l.moveTo(x0 + 20 + f * 42, 0); l.lineTo(x0 + 26 + f * 42, 1000); l.lineWidth = 9; l.strokeStyle = 'rgba(0,0,0,0.22)'; l.stroke(); }
  }
  const [front, fr] = canvas(k);                                                 // the valance, the lip, the pit
  const scallop = q2 => { q2.beginPath(); q2.moveTo(0, 0); q2.lineTo(GW, 0); for (let x = GW; x >= 0; x -= 90) q2.quadraticCurveTo(x - 45, 160, x - 90, 118); q2.closePath(); };
  wash(fr, scallop, GREY[1], 37, { edge: 0.3 });
  for (let x = 45; x < GW; x += 90) { fr.beginPath(); fr.moveTo(x, 140); fr.lineTo(x, 176); fr.lineWidth = 6; fr.strokeStyle = GREY[4]; fr.stroke(); fr.beginPath(); fr.arc(x, 180, 8, 0, 2 * Math.PI); fr.fillStyle = GREY[4]; fr.fill(); }
  wash(fr, P2(0, 1000, GW, 1000, GW, 1022, 0, 1022), GREY[1], 41);
  wash(fr, P2(0, 1022, GW, 1022, GW, H, 0, H), GREY[0], 43, { outline: false });
  const [curtain, cu] = canvas(k);                                               // the front curtain
  const cshape = q2 => { q2.beginPath(); q2.moveTo(0, 0); q2.lineTo(GW, 0); q2.lineTo(GW, 990); for (let x = GW; x >= 0; x -= 60) q2.quadraticCurveTo(x - 30, 1030, x - 60, 990); q2.closePath(); };
  wash(cu, cshape, GREY[2], 47, { edge: 0.3 });
  cu.save(); cshape(cu); cu.clip();
  for (let f = 0; f < 14; f++) {
    const x0 = f * 104, gr = cu.createLinearGradient(x0, 0, x0 + 104, 0);
    gr.addColorStop(0, 'rgba(0,0,0,0.32)'); gr.addColorStop(0.45, 'rgba(255,255,255,0.10)'); gr.addColorStop(1, 'rgba(0,0,0,0.32)');
    cu.fillStyle = gr; cu.fillRect(x0, 0, 104, 1040);
  }
  cu.restore();
  for (let x = 30; x < GW; x += 60) { cu.beginPath(); cu.moveTo(x, 1010); cu.lineTo(x, 1046); cu.lineWidth = 5; cu.strokeStyle = GREY[4]; cu.stroke(); }
  paper(cu, 9);
  return { back, legs, front, curtain, k };
}

// the footlights breathe with everyone else
function footlights(g, t) {
  const a = breath(band(t), ampAt(band(t)));
  for (let i = 0; i < 9; i++) {
    const x = 105 + i * 154, R = rig(x, 1004, 1 - 0.5 * a, 1 + 1.5 * a);
    form(g, R, ell(0, 0, 44, 30, 20, 0, Math.PI, 2 * Math.PI), 400 + i, { fill: GREY[1], ink: 4 });
    line(g, R(-30, -6), R(30, -6), 4, GREY[4]);
  }
}

// --- lettering: a fat retro script, white with a heavy ink outline and an ink shadow; letters hop on the beat --------
function lettering(g, text, cx, y, size, t, { hop = 16 } = {}) {
  g.font = `${size}px ${SCRIPT}`;
  const w = g.measureText(text).width, x0 = cx - w / 2, tc = step(t, 12);
  const k = Math.floor(beats(tc)), since = tc - k * BEAT;
  for (const pass of ['shadow', 'ink', 'face']) {
    for (let i = 0; i < text.length; i++) {
      const x = x0 + g.measureText(text.slice(0, i)).width, u = (since - i * 0.035) / 0.24;
      const dy = u > 0 && u < 1 ? -hop * Math.sin(Math.PI * u) : 0;
      if (pass === 'shadow') { g.fillStyle = INK; g.fillText(text[i], x + 10, y + dy + 10); g.lineWidth = size * 0.2; g.strokeStyle = INK; g.strokeText(text[i], x + 10, y + dy + 10); }
      else if (pass === 'ink') { g.lineWidth = size * 0.2; g.lineJoin = 'round'; g.strokeStyle = INK; g.strokeText(text[i], x, y + dy); }
      else { g.fillStyle = WHITE; g.fillText(text[i], x, y + dy); }
    }
  }
  return w;
}
// a painted card: a grey plate, a dark band, a white double rule, dot-and-ring ornaments at the corners
function plate(g, x0, y0, x1, y1) {
  g.fillStyle = GREY[1]; g.fillRect(x0, y0, x1 - x0, y1 - y0);
  g.fillStyle = GREY[4]; g.fillRect(x0 + 16, y0 + 16, x1 - x0 - 32, y1 - y0 - 32);
  g.strokeStyle = WHITE;
  for (const [ins, w] of [[30, 5], [42, 2]]) { g.lineWidth = w; g.strokeRect(x0 + ins, y0 + ins, x1 - x0 - 2 * ins, y1 - y0 - 2 * ins); }
  for (const [cx, cy] of [[x0 + 30, y0 + 30], [x1 - 30, y0 + 30], [x0 + 30, y1 - 30], [x1 - 30, y1 - 30]]) {
    g.beginPath(); g.arc(cx, cy, 13, 0, 2 * Math.PI); g.fillStyle = GREY[1]; g.fill(); g.lineWidth = 3; g.stroke();
    g.beginPath(); g.arc(cx, cy, 5, 0, 2 * Math.PI); g.fillStyle = WHITE; g.fill();
  }
  g.lineWidth = 4; g.strokeStyle = INK; g.strokeRect(x0, y0, x1 - x0, y1 - y0);
}
function titleSign(g, t, dy) {
  const tc = step(t, 12), swing = 0.05 * Math.exp(-tc * 5) * Math.sin(tc * 14);   // the chord sets it swinging
  const jolt = [cue('tap1'), cue('tap2')].reduce((j, c) => j + (tc >= c ? -34 * Math.exp(-(tc - c) * 9) * Math.cos((tc - c) * 18) : 0), 0);
  g.save(); g.translate(720, 0); g.rotate(swing); g.translate(-720, jolt);
  for (const x of [380, 1060]) line(g, [x, 0], [x, 300 + dy], 5, GREY[0]);
  plate(g, 230, 300 + dy, 1210, 660 + dy);
  lettering(g, 'Opening Night', 720, 512 + dy, 150, t);
  g.font = `40px ${CAPS}`; g.fillStyle = GREY[0]; g.textAlign = 'center';
  g.fillText('A MOODREEL CARTOON', 720, 600 + dy);
  g.textAlign = 'left';
  g.restore();
}
// the conductor in the pit: a glove and a baton that taps the band in, twice
function baton(g, t) {
  if (t < 0.4 || t > 2.3) return;
  const tc = step(t, 12), rise = tween(tc, 0.4, 0.4, 'back.out(1.6)') * (1 - tween(tc, 1.85, 0.4, 'power2.in'));
  const tap = [cue('tap1'), cue('tap2')].reduce((s, c) => s + (tc >= c ? 0.55 * Math.exp(-(tc - c) * 14) : 0), 0);
  const X = 560, Y = 1220 - 400 * rise, a = -1.05 + tap * 1.4;
  line(g, [X + 30, Y], [X + 30 + 280 * Math.cos(a), Y + 280 * Math.sin(a)], 16, INK);
  line(g, [X + 30, Y], [X + 30 + 275 * Math.cos(a), Y + 275 * Math.sin(a)], 8, WHITE);
  hose(g, [X - 80, H + 100], [X, Y + 30], 24, 18, 300);
  glove(g, X, Y + 14, a, 72, { grip: 1 });
}
// The End, dragged in front of everyone by a glove at its edge
const cardX = t => lerp(GW, 0, tween(t, CARD[0], CARD[1] - CARD[0], 'power2.inOut'));
function endCard(g, t) {
  if (t < CARD[0]) return;
  const x = cardX(t);
  g.save(); g.translate(x, 0);
  plate(g, 0, 0, GW, H);
  lettering(g, 'The End', 720, 640, 320, t, { hop: t >= END ? 30 : 16 });
  g.restore();
  if (t < CARD[1] + BEAT / 2) glove(g, x - 4, GRIP, 0, 50, { grip: 1 });         // gripping the card's edge
}

// --- the print: weave, flicker, scratches, dust, a hair, a heavy vignette, light grain --------------------------------
function damage(g, f) {
  const fl = (noise1(f * 0.9 + 7) * 2 - 1) * 0.035 + (hash(f * 1.7) - 0.5) * 0.02;
  g.fillStyle = fl > 0 ? `rgba(255,255,255,${fl})` : `rgba(0,0,0,${-fl})`; g.fillRect(0, 0, GW, H);
  const seg = Math.floor(f / 36);
  for (let s = 0; s < 3; s++) {
    if (hash(seg * 13.3 + s) < 0.45) continue;
    const x = hash(seg * 7.1 + s * 3.1) * GW + 24 * Math.sin(f * 0.05 + s);
    g.beginPath(); g.moveTo(x, 0); g.quadraticCurveTo(x + 6 * Math.sin(f + s), H / 2, x - 4, H);
    g.lineWidth = 1.6; g.strokeStyle = `rgba(235,238,240,${0.25 + 0.2 * hash(f + s)})`; g.stroke();
  }
  const n = 3 + Math.floor(hash(f * 2.3) * 6);
  for (let i = 0; i < n; i++) {
    const x = hash(f * 3.1 + i * 11.3) * GW, y = hash(f * 5.7 + i * 7.9) * H, r = 1 + hash(f + i * 3.3) * 3.5;
    g.beginPath(); g.ellipse(x, y, r, r * (0.5 + hash(i + f)), hash(i * f) * 3, 0, 2 * Math.PI);
    g.fillStyle = hash(f * 9.1 + i) < 0.6 ? 'rgba(10,11,12,0.8)' : 'rgba(240,242,244,0.7)'; g.fill();
  }
  if (hash(f * 1.31) < 0.06) {
    const x = hash(f * 4.4) * GW, y = hash(f * 6.6) * H;
    g.beginPath(); g.moveTo(x, y); g.bezierCurveTo(x + 40, y - 60, x + 90, y + 50, x + 130, y - 20);
    g.lineWidth = 1.5; g.strokeStyle = 'rgba(10,11,12,0.7)'; g.stroke();
  }
  const v = g.createRadialGradient(GW / 2, H / 2, H * 0.35, GW / 2, H / 2, Math.hypot(GW, H) / 2);
  v.addColorStop(0, 'rgba(0,0,0,0)'); v.addColorStop(1, 'rgba(0,0,0,0.62)');
  g.fillStyle = v; g.fillRect(0, 0, GW, H);
}

texts(t => [
  ...(t < CURTAIN[0] + 0.2 ? [{ id: 'title', text: 'Opening Night', x0: GX + 260, y0: 400, x1: GX + 1180, y1: 540 },
                             { id: 'sub', text: 'A Moodreel Cartoon', x0: GX + 470, y0: 565, x1: GX + 970, y1: 610 }] : []),
  ...(t >= CARD[1] ? [{ id: 'end', text: 'The End', x0: GX + 300, y0: 420, x1: GX + 1140, y1: 690 }] : []),
]);

let SET = null, SCENE = null;
stage({ width: W, height: H, duration: 16, background: '#000', fonts: [`150px ${SCRIPT}`, `40px ${CAPS}`], draw: (g, t) => {
  const k = g.getTransform().a, f = Math.round(t * 24);
  if (!SET || SET.k !== k) { SET = paintSet(k); SCENE = canvas(k); }
  const [sc, q] = SCENE;
  q.setTransform(k, 0, 0, k, 0, 0);
  BOIL = Math.floor(step(band(t), 12) * 12) % 3;
  const tc = step(t, 12);                                                          // the cast on twos
  // the stage squashes on the floor line at the peak
  const sq = t >= bar(6) && t < TADA ? 0.025 * Math.cos(2 * Math.PI * beats(step(t, 12))) : 0;
  q.save(); q.translate(0, FLOOR); q.scale(1 - sq * 0.4, 1 + sq); q.translate(0, -FLOOR);
  q.drawImage(SET.back, 0, 0, GW, H);
  q.restore();
  piano(q, tc); tuba(q, tc); clarinet(q, tc);
  q.drawImage(SET.legs, 0, 0, GW, H);
  if (t < CURTAIN[1]) {
    const dy = -1120 * tween(t, CURTAIN[0], CURTAIN[1] - CURTAIN[0], 'power2.in');
    q.drawImage(SET.curtain, 0, dy, GW, H);
    titleSign(q, t, dy);
  }
  q.drawImage(SET.front, 0, 0, GW, H);
  footlights(q, step(t, 12));
  baton(q, t);
  endCard(q, step(t, 12));
  // the print through the gate: a weave, a rare jump, contrast up, a touch of blur, then the damage on top
  const wx = 1.2 * (noise1(f * 0.15) * 2 - 1), wy = 1.2 * (noise1(f * 0.15 + 50) * 2 - 1) + (hash(f * 3.7) > 0.985 ? 5 : 0);
  g.fillStyle = '#000'; g.fillRect(0, 0, W, H);
  g.save();
  g.beginPath(); g.roundRect(GX, 0, GW, H, 28); g.clip();
  g.filter = 'contrast(1.13) blur(0.5px)';
  g.drawImage(sc, GX + wx, wy, GW, H);
  g.filter = 'none';
  g.translate(GX, 0);
  damage(g, f);
  g.lineWidth = 30; g.strokeStyle = 'rgba(0,0,0,0.5)'; g.filter = 'blur(10px)';
  g.beginPath(); g.roundRect(0, 0, GW, H, 28); g.stroke(); g.filter = 'none';
  g.restore();
  grain(g, 7, f, { ground: GREY[3] });
} });
