import { stage, texts } from './kit/stage.js';
import { PALETTE, TYPE, LAYOUT } from './kit/tokens.js';
import { BEAT, MOTION, land } from './kit/motion.js';
import { tween, lerp, rng } from './kit/core.js';

// "Morning": a day's first three things, one card each, a bar of two beats per card at 120 BPM, cut on the downbeat.
// A sun disc pops, the figure slides into register band by band, the word rises out of its slot, the figure acts.
const W = 1920, H = 1080, DUR = 12, CARD = 4 * BEAT * 2;
const [T0, T1, T2, T3] = PALETTE.tones, CREAM = PALETTE.cream;
const CARDS = [{ title: 'WAKE', zh: '起床', seed: 3 }, { title: 'BREW', zh: '煮咖啡', seed: 11 }, { title: 'WALK', zh: '散步', seed: 29 }];
const SUN = { x: 1400, y: 600, r: 330 }, HIP = { x: 1400, y: 640 };
const C = LAYOUT.cell;
const font = (w, px, fam) => `${w} ${px}px ${fam}`;
const mix = (a, b, k) => {
  const p = s => [1, 3, 5].map(i => parseInt(s.slice(i, i + 2), 16));
  const [x, y] = [p(a), p(b)];
  return `rgb(${x.map((v, i) => Math.round(v + (y[i] - v) * k)).join(',')})`;
};

// the pattern: discs on the grid's nodes in the hue's darker tones (low contrast under type), quarter-discs in some
// cells; seeded per card, so every card is its own pattern
function pattern(g, seed) {
  const r = rng(seed);
  g.fillStyle = T1;
  g.fillRect(0, 0, W, H);
  for (let y = 0; y <= H; y += C) {
    for (let x = 0; x <= W; x += C) {
      const tone = [T0, T1, T2][Math.floor(r() * 3)];
      g.fillStyle = tone;
      g.beginPath();
      g.arc(x, y, C / 2, 0, Math.PI * 2);
      g.fill();
      if (r() < 0.5) {
        g.fillStyle = r() < 0.5 ? T0 : T2;
        g.beginPath();
        const a = Math.floor(r() * 4) * Math.PI / 2;
        g.moveTo(x + C / 2, y + C / 2);
        g.arc(x + C / 2, y + C / 2, C / 2, a, a + Math.PI / 2);
        g.fill();
      }
    }
  }
}

// the figure, unit = body height, origin at the hip: far limbs mixed toward the disc, then torso, near limbs, head
function figure(g, at, t, lift) {
  const bar = (x, y, w, h, c) => { g.fillStyle = c; g.beginPath(); g.roundRect(x - w / 2, y, w, h, w / 2); g.fill(); };
  const far = mix(CREAM, T3, 0.4);
  const band = i => {
    const p = land(t, at + 1.5 * BEAT + i * MOTION.band.interval - 0.5 * BEAT + 0.5 * BEAT, MOTION.enter);
    return (1 - p) * MOTION.band.travel * (i % 2 ? 1 : -1);
  };
  const shown = i => t >= at + 0.5 * BEAT + i * MOTION.band.interval;
  g.save();
  g.translate(HIP.x, HIP.y - lift);
  if (shown(2)) {                                          // legs
    g.save(); g.translate(band(2), 0);
    bar(26, 0, 44, 210, far); bar(-26, 0, 44, 210, CREAM);
    g.restore();
  }
  if (shown(1)) {                                          // torso and arms
    g.save(); g.translate(band(1), 0);
    bar(70, -220, 40, 170, far); bar(0, -230, 80, 240, CREAM); bar(-70, -220, 40, 170, CREAM);
    g.restore();
  }
  if (shown(0)) {                                          // head
    g.save(); g.translate(band(0), 0);
    g.fillStyle = CREAM; g.beginPath(); g.arc(0, -290, 46, 0, Math.PI * 2); g.fill();
    g.restore();
  }
  g.restore();
}

// type enters by mask slide-up: it rises out of a slot at its baseline
function rise(g, text, x, base, size, f, p) {
  if (p <= 0) return;
  g.save();
  g.beginPath();
  g.rect(x - 10, base - size * 1.05, 1400, size * 1.05 + size * 0.22);
  g.clip();
  g.font = f;
  g.fillStyle = CREAM;
  g.fillText(text, x, base + (1 - p) * size * 1.25);
  g.restore();
}

stage({
  width: W, height: H, duration: DUR, background: T1,
  fonts: [font(900, 230, TYPE.display), font(600, 72, TYPE.text), font(500, 22, TYPE.mono)],
  draw: (g, t) => {
    const n = Math.min(CARDS.length - 1, Math.floor(t / CARD)), at = n * CARD, card = CARDS[n];
    pattern(g, card.seed);
    // the stage: a sun disc in a lighter neighbouring tone pops on the first beat
    const s = lerp(0.6, 1, land(t, at + BEAT, MOTION.pop));
    if (t >= at + BEAT - MOTION.pop.duration) {
      g.fillStyle = T3;
      g.beginPath();
      g.arc(SUN.x, SUN.y, SUN.r * s, 0, Math.PI * 2);
      g.fill();
    }
    // one action: the figure lifts on beat 6 and settles on beat 7
    const up = tween(t, at + 5 * BEAT, BEAT, MOTION.act.ease) - tween(t, at + 6 * BEAT, BEAT, MOTION.act.ease);
    figure(g, at, t, up * MOTION.act.lift);
    rise(g, card.title, 140, 560, 230, font(900, 230, TYPE.display), land(t, at + 3 * BEAT));
    rise(g, card.zh, 146, 680, 72, font(600, 72, TYPE.text), land(t, at + 3 * BEAT + MOTION.second));
    // the HUD: mono corners and a progress bar of N ticks (current tall, done dimmed, rest faint)
    g.font = font(500, 22, TYPE.mono);
    g.fillStyle = CREAM;
    g.fillText('M O R N I N G', 140, 96);
    g.fillText(`0${n + 1} / 0${CARDS.length}`, 1680, 96);
    CARDS.forEach((_, i) => {
      g.globalAlpha = i === n ? 1 : i < n ? 0.4 : 0.15;
      g.fillRect(140 + 28 * i, i === n ? 944 : 962, 12, i === n ? 36 : 18);
    });
    g.globalAlpha = 1;
  },
});

texts(t => {
  const k = innerWidth / W, n = Math.min(CARDS.length - 1, Math.floor(t / CARD)), at = n * CARD;
  return land(t, at + 3 * BEAT) >= 1
    ? [{ id: `title${n}`, text: CARDS[n].title, x0: 140 * k, y0: 395 * k, x1: 880 * k, y1: 560 * k },
      { id: `zh${n}`, text: CARDS[n].zh, x0: 146 * k, y0: 612 * k, x1: 380 * k, y1: 690 * k }] : [];
});
