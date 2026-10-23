import { stage, texts } from './kit/stage.js';
import { PALETTE, TYPE } from './kit/tokens.js';
import { BEAT, snap, lin } from './kit/motion.js';

// "Programme": a style is a programme. A dot, a grid, rule one, a page turn, rule two, the exception, a knife cut,
// one word. 120 BPM; every snap lands on a beat or an eighth; the exception alone moves linearly, off the grid.
const W = 1920, H = 1080, DUR = 15;
const COL = 146, M = 96, BASE = 760;                        // 122 px columns + 24 px gutters, 96 px margin
const colX = i => M + i * COL;
const FONT = (w, s) => `${w} ${s}px ${TYPE.display}`;
const B = n => n * BEAT;                                    // beats to seconds

const bars = [3, 5, 2, 6, 4, 7].map((h, i) => ({ x: colX(6 + i), h: h * 48, at: B(6) + i * B(0.5) }));
const squares = [...Array(8)].map((_, i) => ({ x: 1920 + M + i * 90, at: B(14) + i * B(0.25) }));
const camAt = B(12);                                        // the page turn lands on beat 12

// text that rises out of a clip at its baseline (Swiss entrances are clip reveals, never fades)
function rise(g, text, x, base, size, weight, color, p) {
  if (p <= 0) return;
  const h = size * 0.75;
  g.save();
  g.beginPath();
  g.rect(x - 20, base - size * 1.1, 3000, size * 1.35);          // down to the descenders
  g.clip();
  g.font = FONT(weight, size);
  g.fillStyle = color;
  g.fillText(text, x, base + (1 - p) * (h + size * 0.3));
  g.restore();
}

// an element deleted by a knife: collapse to its midline
function collapse(g, mid, c, draw) {
  if (c >= 1) return;
  g.save();
  g.translate(0, mid);
  g.scale(1, 1 - c);
  g.translate(0, -mid);
  draw();
  g.restore();
}

const camX = t => -960 * snap(t, camAt);
const cut = (t, k) => snap(t, B(23.5) + k * B(0.125), B(0.5));   // the system closes, nearest to the knife first

stage({
  width: W, height: H, duration: DUR, background: PALETTE.ground,
  fonts: [FONT(700, 560), FONT(700, 96), FONT(500, 26)],
  draw: (g, t) => {
    g.save();
    g.translate(camX(t), 0);
    // the grid grows from the dot, column by column, ordered by distance (lines grow linearly along their length)
    g.fillStyle = PALETTE.grid;
    for (let i = 0; i < 20; i++) {
      const p = lin(t, B(1) + i * B(0.125), B(1));
      const len = p * 540;
      if (len > 0) g.fillRect(colX(i), 540 - len, 1, 2 * len);
    }
    // the first dot, taken back when the numeral lands
    const d = snap(t, B(1)) - snap(t, B(4), B(0.5));
    if (d > 0) {
      g.fillStyle = PALETTE.ink;
      g.beginPath();
      g.arc(M, 540, 10 * d, 0, Math.PI * 2);
      g.fill();
    }
    // rule one: a giant numeral, a caption row, bars from a score, a word
    rise(g, '1', M - 30, BASE, 560, 700, PALETTE.ink, snap(t, B(4)));
    const c1 = snap(t, B(5));
    if (c1 > 0) {
      g.fillStyle = PALETTE.ink;
      g.fillRect(M, 930, 3 * COL - 24, 1 * c1 + 0.01);
      rise(g, 'rule 1 — measure first', M, 966, 26, 500, PALETTE.note, c1);
    }
    bars.forEach((b, i) => {
      const p = snap(t, b.at), c = cut(t, 3 + i);
      if (p > 0) collapse(g, BASE - b.h / 2, c, () => {
        g.fillStyle = PALETTE.ink;
        g.fillRect(b.x, BASE - b.h * p, 122, b.h * p + 1);
      });
    });
    collapse(g, 270, cut(t, 10), () => rise(g, 'measure', colX(6), 300, 96, 700, PALETTE.ink, snap(t, B(9))));
    // rule two, on the next spread
    const knife = lin(t, B(21), B(0.5)), gone = snap(t, B(22.5), B(0.75));
    collapse(g, BASE - 210, gone, () => rise(g, '2', 1920 + M - 30, BASE, 560, 700, PALETTE.ink, snap(t, B(13))));
    if (knife > 0 && gone < 1) {
      g.fillStyle = PALETTE.ink;
      g.fillRect(1920 + M - 60, BASE - 210, 520 * knife, 3);
    }
    squares.forEach((s, i) => collapse(g, 890, cut(t, i * 0.5), () => {
      const p = snap(t, s.at);
      if (p <= 0) return;
      g.save();
      g.beginPath();
      g.rect(s.x, 860, 60, 60);
      g.clip();
      g.fillStyle = PALETTE.ink;
      g.fillRect(s.x, 860 + (1 - p) * 62, 60, 60);
      g.restore();
    }));
    collapse(g, 950, cut(t, 1), () => {
      const c2 = snap(t, B(15));
      if (c2 <= 0) return;
      g.fillStyle = PALETTE.ink;
      g.fillRect(1920 + M, 930, 3 * COL - 24, 1);
      rise(g, 'rule 2 — one signal colour', 1920 + M, 966, 26, 500, PALETTE.note, c2);
    });
    g.restore();

    // the exception: linear, unsnapped, off the grid, the only thing in the signal colour
    const ex = lin(t, B(17), B(3));
    if (ex > 0) {
      const x = 2100 - ex * 640;
      g.fillStyle = PALETTE.accent;
      g.fillRect(x, 360, 120, 120);
      if (t >= B(20) && t < B(25)) {
        g.font = FONT(500, 26);
        g.fillStyle = PALETTE.note;
        g.fillText(`x ${Math.round(x)} · off grid`, x, 520);
      }
    }
    // the end: one word, flush left in the corner
    rise(g, 'programme', M, 1000, 96, 700, PALETTE.ink, snap(t, B(25.5)));
  },
});

texts(t => {
  const k = innerWidth / W, cx = camX(t), out = [];
  const add = (id, text, x, y0, y1, w) => out.push({ id, text, x0: (x) * k, y0: y0 * k, x1: (x + w) * k, y1: y1 * k });
  if (snap(t, B(4)) >= 1 && cx > -640) add('one', '1', M - 30 + cx, BASE - 420, BASE, 300);
  if (snap(t, B(5)) >= 1 && cx > -300) add('caption1', 'rule 1 — measure first', M + cx, 940, 972, 300);
  if (snap(t, B(9)) >= 1 && cut(t, 10) <= 0) add('measure', 'measure', colX(6) + cx, 228, 300, 380);
  if (snap(t, B(13)) >= 1 && snap(t, B(22.5), B(0.75)) <= 0) add('two', '2', 1920 + M - 30 + cx, BASE - 420, BASE, 300);
  if (snap(t, B(15)) >= 1 && cut(t, 1) <= 0) add('caption2', 'rule 2 — one signal colour', 1920 + M + cx, 940, 972, 330);
  if (t >= B(20) && t < B(25)) add('readout', 'x 1460 · off grid', 1460, 494, 526, 230);
  if (snap(t, B(25.5)) >= 1) add('end', 'programme', M, 928, 1000, 470);
  return out;
});
