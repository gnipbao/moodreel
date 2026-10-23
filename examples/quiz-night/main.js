// quiz-night: a two-round game show about telling styles apart, on Game Show Flat (styles/game-show). The music comes
// first: score.json holds the 120 BPM grid and the cue table, and every pop, drop and stamp below lands on a cue.
import { stage, texts } from './kit/stage.js';
import { tween, clamp } from './kit/core.js';
import { cue, bar, SCORE } from './score.js';

const W = 1920, H = 1080, BEAT = SCORE.beat_s;
const INK = '#1b1424', CREAM = '#fff4dc', WHITE = '#ffffff', YELLOW = '#ffd23f';
const FONT = '"Arial Rounded MT Bold", "Arial Black", Helvetica, sans-serif';
const SETS = [
  { at: 0, ground: '#ffb870', pattern: '#ffa85a', floor: '#e8833a', kind: 'stripes' },     // round 1: tangerine
  { at: cue('round2'), ground: '#3dbfb0', pattern: '#6fd8cb', floor: '#279283', kind: 'dots' }, // round 2: teal
];
const CAST = [                                          // each contestant owns a colour, never the set's
  { name: 'SWISS', body: YELLOW, x: 640, drop: 'drop1' },
  { name: 'RISO', body: '#ff6fae', x: 960, drop: 'drop2' },
  { name: 'PIXEL', body: '#4f7bff', x: 1280, drop: 'drop3' },
];
const FLOOR = 860;
const HITS = ['correct', 'round2', 'winner'];

// a hard offset shadow: the shape in ink, shifted, then the shape
function shadowed(g, off, path, fill) {
  g.save(); g.translate(off, off); path(); g.fillStyle = INK; g.fill(); g.restore();
  path(); g.fillStyle = fill; g.fill(); g.lineWidth = 8; g.strokeStyle = INK; g.lineJoin = 'round'; g.stroke();
}

// telop text: the ink stroke painted under the fill, about 14 % of the size
function telop(g, text, x, y, size, fill = WHITE, align = 'center') {
  g.font = `900 ${size}px ${FONT}`;
  g.textAlign = align; g.textBaseline = 'middle'; g.lineJoin = 'round';
  g.lineWidth = size * 0.28; g.strokeStyle = INK; g.strokeText(text, x, y);
  g.fillStyle = fill; g.fillText(text, x, y);
}

// a back-eased pop that starts on its cue
const pop = (t, at, d = 0.35) => (t < at ? 0 : tween(t, at, d, 'back.out(2)'));
// a punch of the frame on each hit, decaying in 0.16 s
const punch = t => HITS.reduce((z, c) => z + (t >= cue(c) ? 0.035 * Math.exp(-(t - cue(c)) / 0.16) : 0), 0);
// a damped wobble after each hit (squash), ~30 rad/s for ~0.35 s
const wobble = t => HITS.reduce((s, c) => s + (t >= cue(c) ? 0.14 * Math.exp(-(t - cue(c)) / 0.12) * Math.cos(30 * (t - cue(c))) : 0), 0);

function set(g, t, s) {
  g.fillStyle = s.ground; g.fillRect(-200, -200, W + 400, H + 400);
  g.fillStyle = s.pattern;
  if (s.kind === 'stripes') {                            // diagonal stripes, scrolling slowly
    const shift = (t * 40) % 160;
    for (let x = -H - 160; x < W + 200; x += 160) {
      g.beginPath(); g.moveTo(x + shift, -200); g.lineTo(x + shift + 70, -200); g.lineTo(x + shift + 70 + H + 400, H + 200);
      g.lineTo(x + shift + H + 400, H + 200); g.fill();
    }
  } else {                                               // offset polka dots
    for (let y = 40, row = 0; y < FLOOR; y += 110, row++)
      for (let x = (row % 2) * 70; x < W + 70; x += 140) { g.beginPath(); g.arc(x, y, 22, 0, Math.PI * 2); g.fill(); }
  }
  g.fillStyle = s.floor; g.fillRect(-200, FLOOR, W + 400, H - FLOOR + 200);
  g.fillStyle = INK; g.fillRect(-200, FLOOR - 4, W + 400, 8);
}

// one body construction for the whole cast: a rounded bean, mitten arms, eyes with a catch-light, a name tag
function bean(g, c, x, y, { squash = 0, shout = false, still = false } = {}) {
  g.save(); g.translate(x, y); g.scale(1 + squash, 1 - squash);
  const body = () => { g.beginPath(); g.roundRect(-85, -230, 170, 230, 85); };
  shadowed(g, 12, body, c.body);
  g.lineWidth = 16; g.lineCap = 'round'; g.strokeStyle = INK;     // arms: up on a shout, down otherwise
  for (const s of [-1, 1]) {
    g.beginPath(); g.moveTo(s * 80, -120); g.lineTo(s * (shout ? 130 : 115), shout ? -260 : -60); g.stroke();
  }
  for (const s of [-1, 1]) {                             // eyes and catch-lights
    g.fillStyle = WHITE; g.beginPath(); g.ellipse(s * 32, -160, 22, 28, 0, 0, Math.PI * 2); g.fill();
    g.lineWidth = 5; g.stroke();
    g.fillStyle = INK; g.beginPath(); g.ellipse(s * 32, still ? -152 : -158, 11, 14, 0, 0, Math.PI * 2); g.fill();
  }
  g.fillStyle = INK; g.beginPath();
  if (shout) g.ellipse(0, -95, 26, 22, 0, 0, Math.PI * 2); else g.arc(0, -105, 22, 0.15 * Math.PI, 0.85 * Math.PI);
  shout ? g.fill() : (g.lineWidth = 7, g.stroke());
  g.restore();
  telop(g, c.name, x, y + 50, 36, CREAM);                 // name tag on the floor band
}

function burst(g, x, y, p) {                              // a star, a ring and speed lines
  if (p <= 0) return;
  g.save(); g.translate(x, y); g.scale(p, p);
  g.beginPath();
  for (let k = 0; k < 24; k++) { const r = k % 2 ? 150 : 250, a = (k / 24) * Math.PI * 2; g.lineTo(Math.cos(a) * r, Math.sin(a) * r); }
  g.closePath(); g.fillStyle = YELLOW; g.fill(); g.lineWidth = 8; g.strokeStyle = INK; g.stroke();
  g.restore();
}

texts(t => {                                             // what is on screen, for the reading-time check
  const on = [];
  if (t >= cue('card') && t < cue('round2')) on.push({ id: 'card', text: 'WHICH STYLE?', x0: 610, y0: 140, x1: 1310, y1: 300 });
  if (t >= cue('answer') && t < cue('round2')) on.push({ id: 'answer', text: 'SWISS!', x0: 480, y0: 465, x1: 800, y1: 575 });
  if (t >= cue('correct') && t < cue('round2')) on.push({ id: 'right', text: 'RIGHT!', x0: 1260, y0: 330, x1: 1700, y1: 470 });
  if (t >= cue('round2')) on.push({ id: 'round', text: 'ROUND 2', x0: 60, y0: 50, x1: 440, y1: 150 });
  if (t >= cue('winner')) on.push({ id: 'winner', text: 'WINNER!', x0: 660, y0: 120, x1: 1260, y1: 280 });
  for (const c of CAST) if (t >= cue(c.drop)) on.push({ id: c.name, text: c.name, x0: c.x - 90, y0: FLOOR + 25, x1: c.x + 90, y1: FLOOR + 75 });
  return on;
});

stage({ width: W, height: H, duration: 12, background: SETS[0].ground, fonts: [`900 64px ${FONT}`], draw: (g, t) => {
  const round = t >= cue('round2') ? 1 : 0;
  const z = 1 + punch(t);
  g.save(); g.translate(W / 2, H / 2); g.scale(z, z); g.translate(-W / 2, -H / 2);
  set(g, t, SETS[round]);
  const beat = Math.floor(t / BEAT), stopped = t >= cue('think') && t < cue('think') + BEAT;
  CAST.forEach((c, i) => {
    const land = cue(c.drop);
    if (t < land - 0.4) return;
    const fall = t < land ? tween(t, land - 0.4, 0.4, 'power2.in') : 1;           // drops from the sky, lands on its cue
    const phase = ((t / BEAT) + (i % 2) * 0.5) % 1;                                  // neighbours hop on the off-beat
    const hop = t > land + 0.05 && !stopped ? 18 * 4 * phase * (1 - phase) : 0;
    const y = FLOOR - (1 - fall) * 1000 - hop;
    const winner = i === 0 && t >= cue('winner');
    bean(g, c, c.x, y, { squash: (i === 0 ? wobble(t) : 0) + (t >= land && t < land + 0.12 ? 0.12 : 0),
      shout: winner && (t - cue('winner')) % (2 * BEAT) < BEAT, still: stopped });
  });
  if (round === 0) {
    const pc = pop(t, cue('card'));                      // the round card
    if (pc > 0) {
      g.save(); g.translate(960, 220); g.scale(pc, pc);
      shadowed(g, 14, () => { g.beginPath(); g.roundRect(-350, -80, 700, 160, 40); }, CREAM);
      telop(g, 'WHICH STYLE?', 0, 4, 78, YELLOW);
      g.restore();
    }
    if (stopped) telop(g, '?', 960, 470, 140, WHITE);    // the held breath: the band stops, the cast freezes
    const pa = pop(t, cue('answer'));                    // SWISS answers
    if (pa > 0) {
      g.save(); g.translate(640, 520); g.scale(pa, pa);
      shadowed(g, 10, () => { g.beginPath(); g.roundRect(-160, -55, 320, 110, 55); }, WHITE);
      telop(g, 'SWISS!', 0, 2, 58, YELLOW);
      g.restore();
    }
    const pr = pop(t, cue('correct'), 0.3);              // the judgement, with its burst
    burst(g, 1480, 400, pr);
    if (pr > 0) { g.save(); g.translate(1480, 400); g.scale(pr, pr); g.rotate(-0.12); telop(g, 'RIGHT!', 0, 0, 104, '#ff6fae'); g.restore(); }
  } else {
    const pb = pop(t, cue('round2'), 0.3);               // corner sticker banner
    g.save(); g.translate(250, 100); g.scale(pb, pb); g.rotate(-0.06);
    shadowed(g, 10, () => { g.beginPath(); g.roundRect(-190, -50, 380, 100, 20); }, '#ff6fae');
    telop(g, 'ROUND 2', 0, 2, 64, WHITE);
    g.restore();
    const ps = pop(t, cue('board'));                     // the scoreboard: one plate per contestant
    if (ps > 0) CAST.forEach((c, i) => {
      const pts = i === 0 ? (t >= cue('point') ? 2 : 1) : i === 1 ? 1 : 0;
      g.save(); g.translate(c.x, 470); g.scale(ps, ps);
      shadowed(g, 12, () => { g.beginPath(); g.roundRect(-90, -70, 180, 140, 26); }, CREAM);
      const bump = i === 0 ? pop(t, cue('point'), 0.3) : 1;
      g.scale(i === 0 && t >= cue('point') ? 0.7 + 0.3 * bump : 1, i === 0 && t >= cue('point') ? 0.7 + 0.3 * bump : 1);
      telop(g, String(pts), 0, 4, 96, c.body);
      g.restore();
    });
    const pw = pop(t, cue('winner'), 0.3);
    if (pw > 0) { g.save(); g.translate(960, 200); g.scale(pw, pw); telop(g, 'WINNER!', 0, 0, 120, YELLOW); g.restore(); }
  }
  g.restore();
  const flash = t - cue('round2');                       // the cut on the bar line, with a very short white flash
  if (flash >= 0 && flash < 2 / 24) { g.fillStyle = WHITE; g.globalAlpha = clamp(1 - flash * 12); g.fillRect(0, 0, W, H); g.globalAlpha = 1; }
}});
