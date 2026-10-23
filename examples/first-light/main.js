import { stage, texts } from './kit/stage.js';
import { PALETTE, INKS, TYPE, TEXTURE } from './kit/tokens.js';
import { drawn, enter, sweep, kick } from './kit/motion.js';
import { paper, grain, screen } from './kit/texture.js';
import { lerp } from './kit/core.js';

// "First Light": two plates. The teal plate prints a sea, the orange plate a sun; where they meet they make the
// third colour. A swimmer crosses, the title is printed twice, and the orange plate lifts away: one ink left.
const W = 1920, H = 1080, DUR = 12;
const HORIZON = 640;
const SUN = { x: 1350, r: 170, from: 830, to: 420, at: 1.5 };
const SWIM = { at: 4.0, dur: 4.0, from: -60, to: 1500, y: 712 };
const TITLE = { text: 'first light', x: 140, base: 330, at: 8.5 };
const KICK = 9.5, LIFT = 10.5;
const FONT = `${TYPE.titleWeight} ${Math.round(TYPE.title * H)}px ${TYPE.display}`;
const [TEAL, ORANGE] = INKS;

// each plate is its own canvas: ink on white, then multiplied onto the paper out of register, as a riso prints
const plates = INKS.map(() => document.createElement('canvas'));
function plate(c, g) {
  const { width, height } = g.canvas;
  if (c.width !== width || c.height !== height) Object.assign(c, { width, height });
  const q = c.getContext('2d');
  q.setTransform(1, 0, 0, 1, 0, 0);
  q.fillStyle = '#fff';
  q.fillRect(0, 0, width, height);
  q.setTransform(g.getTransform());
  return q;
}
const tint = (q, ink, level) => screen(q, { period: TEXTURE.halftone.period_px, angle: ink.angle, color: ink.color, dot: Math.sqrt(level / Math.PI) });

function swimmer(q, x, y, T, color, grow = 0) {
  const arm = T * Math.PI * 2;                            // one stroke a second, drawn on twos
  q.save();
  q.translate(x, y);
  q.scale(1.6, 1.6);
  q.fillStyle = q.strokeStyle = color;
  q.lineCap = 'round';
  q.beginPath();
  q.ellipse(-34, 6, 42 + grow, 9 + grow, 0, 0, Math.PI * 2);
  q.fill();
  q.beginPath();
  q.arc(0, -8, 16 + grow, 0, Math.PI * 2);
  q.fill();
  q.lineWidth = 12 + 2 * grow;
  q.beginPath();
  q.moveTo(-14, 0);
  q.lineTo(-14 + 46 * Math.cos(arm), -46 * Math.abs(Math.sin(arm)));
  q.stroke();
  q.restore();
}

function title(q, color, T) {
  const p = sweep(T, TITLE.at);
  if (p <= 0) return;
  q.save();
  q.beginPath();
  q.rect(TITLE.x - 20, 0, 40 + 960 * p, H);             // the roller passes left to right
  q.clip();
  q.font = FONT;
  q.fillStyle = color;
  q.fillText(TITLE.text, TITLE.x, TITLE.base);
  q.restore();
}

stage({
  width: W, height: H, duration: DUR, background: PALETTE.ground, fonts: [FONT],
  draw: (g, t) => {
    const T = drawn(t);                                    // every drawing, sweep and kick on twos
    const sun = lerp(SUN.from, SUN.to, enter(t, SUN.at)), rise = enter(t, SUN.at);
    const sx = lerp(SWIM.from, SWIM.to, Math.min(1, Math.max(0, (T - SWIM.at) / SWIM.dur)));
    const swimming = T > SWIM.at && T < SWIM.at + SWIM.dur;
    const bob = 4 * Math.sin(T * Math.PI * 2);

    // plate 1, teal: the sea arrives under the roller, the sky is two stepped tints, the title, a paper halo
    const a = plate(plates[0], g);
    a.save();
    a.beginPath();
    a.rect(0, 0, W * sweep(T, 0.6, 0.8), H);
    a.clip();
    a.fillStyle = TEAL.color;
    a.fillRect(0, HORIZON, W, H - HORIZON);
    a.restore();
    if (T >= 3.5) {                                        // printed on a beat, not faded
      a.fillStyle = tint(a, TEAL, 0.4);
      a.fillRect(0, 0, W, 150);
      a.fillStyle = tint(a, TEAL, 0.2);
      a.fillRect(0, 150, W, 150);
    }
    title(a, TEAL.color, T);
    if (swimming) swimmer(a, sx, SWIM.y + bob, T, '#fff', 5);

    // plate 2, orange: the sun above the horizon, its reflection in bars across the sea, the swimmer, the title again
    const b = plate(plates[1], g);
    b.fillStyle = ORANGE.color;
    b.save();
    b.beginPath();
    b.rect(0, 0, W, HORIZON);
    b.clip();
    b.beginPath();
    b.arc(SUN.x, sun, SUN.r, 0, Math.PI * 2);
    b.fill();
    b.restore();
    for (let j = 0; j < 6; j++) {
      const w = (300 - j * 44) * rise;
      if (w > 0) b.fillRect(SUN.x - w / 2, HORIZON + 26 + j * 58, w, 16);
    }
    if (swimming) swimmer(b, sx, SWIM.y + bob, T, ORANGE.color);
    title(b, ORANGE.color, T);

    // print: paper, then each plate multiplied at its own offset; the orange plate kicks once and then lifts away
    const k = g.getTransform().a;
    g.drawImage(paper(W, H, { color: PALETTE.ground, mottle: TEXTURE.mottle }), 0, 0);
    INKS.forEach((ink, i) => {
      const lift = i === 1 ? sweep(T, LIFT) : 0;
      if (lift >= 1) return;
      g.save();
      g.setTransform(1, 0, 0, 1, 0, 0);
      g.globalCompositeOperation = 'multiply';
      g.beginPath();
      g.rect(lift * g.canvas.width, 0, g.canvas.width, g.canvas.height);
      g.clip();
      g.drawImage(plates[i], (ink.dx + (i === 1 ? kick(T, KICK) : 0)) * k, ink.dy * k);
      g.restore();
    });
    grain(g, TEXTURE.grain, Math.floor(T * 12), { ground: PALETTE.ground });
  },
});

texts(t => {
  const T = drawn(t), k = innerWidth / W;
  return sweep(T, TITLE.at) >= 1 ? [{ id: 'title', text: TITLE.text, x0: TITLE.x * k, y0: (TITLE.base - 115) * k, x1: 900 * k, y1: (TITLE.base + 35) * k }] : [];
});
