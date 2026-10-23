// harbour-dawn: a harbour paints itself in at dawn, on Watercolor Brush (styles/watercolor). Paper is the white;
// every shape is a wash or a brush stroke from kit/brush.js, laid structure first, each in its slice of time.
import { stage, texts } from './kit/stage.js';
import { tween, clamp } from './kit/core.js';
import { paper } from './kit/texture.js';
import { wash, stroke, ink } from './kit/brush.js';

const W = 1920, H = 1080, HORIZON = 560;
const SKY = '#f3c9a0', GLOW = '#e8a77d', WATER = '#9fb4c4', DEEP = '#7f97aa', SHORE = '#8a9a8f', HULL = '#5f7486';
const ACCENT = '#c8442a', INK = '#3b2f2a', BROWN = '#7a5c48';
const HAND = '"Bradley Hand", "Noteworthy", "Chalkboard SE", cursive';
const p = (t, at, d) => clamp((t - at) / d);              // a stroke's share of its slice
const BOATS = [{ x: 520, w: 300, mast: 300, at: 2.4 }, { x: 980, w: 360, mast: 360, at: 2.7 }, { x: 1420, w: 260, mast: 250, at: 3.0 }];

// a brush-edge wipe: the wash shows left of a wavy vertical edge that crosses the frame
function wiped(g, u, seed, draw) {
  if (u <= 0) return;
  g.save();
  g.beginPath();
  const edge = -120 + (W + 240) * u;
  g.moveTo(-50, -50);
  for (let y = -50; y <= H + 50; y += 40) g.lineTo(edge + 60 * Math.sin(y / 90 + seed) + 30 * Math.sin(y / 31 + 2 * seed), y);
  g.lineTo(-50, H + 50);
  g.closePath();
  g.clip();
  draw();
  g.restore();
}

texts(t => [
  ...(t >= 6.8 ? [{ id: 'label', text: 'buoy · 06:12', x0: 1250, y0: 330, x1: 1560, y1: 380 }] : []),
  ...(t >= 7.3 ? [{ id: 'title', text: 'Harbour, dawn', x0: 120, y0: 960, x1: 470, y1: 1010 }] : []),
]);

stage({ width: W, height: H, duration: 10, background: '#efe3cf', fonts: [`40px ${HAND}`], draw: (g, t) => {
  g.drawImage(paper(W, H, { color: '#efe3cf', mottle: 2.2, fibres: 900, seed: 11 }), 0, 0);
  // the sky: two washes, the warmer one low (darker is more passes, not a darker pigment)
  wiped(g, tween(t, 0.0, 1.2, 'sine.inOut'), 1, () => {
    wash(g, [[-40, -40], [W + 40, -40], [W + 40, HORIZON + 10], [-40, HORIZON + 10]], { color: SKY, alpha: 0.45, jitter: 6, seed: 2 });
    wash(g, [[-40, 330], [W + 40, 360], [W + 40, HORIZON + 10], [-40, HORIZON + 10]], { color: GLOW, alpha: 0.32, jitter: 8, seed: 3 });
  });
  for (let k = 0; k < 5; k++) {                          // broad strokes across the sky, bristles breaking into dashes
    const y = 120 + k * 80, x = -60 + ((k * 211) % 300);
    stroke(g, [[x, y], [x + 700, y - 18], [x + 1400, y + 6], [x + 2000, y - 10]], { color: k > 2 ? GLOW : SKY, alpha: 0.28,
      width: 60, profile: 'brush', bristles: 7, seed: 10 + k, reveal: p(t, 0.3 + k * 0.12, 0.8) });
  }
  wiped(g, tween(t, 0.8, 1.4, 'sine.inOut'), 4, () =>    // the water
    wash(g, [[-40, HORIZON], [W + 40, HORIZON], [W + 40, H + 40], [-40, H + 40]], { color: WATER, alpha: 0.5, jitter: 6, seed: 5 }));
  wiped(g, tween(t, 1.6, 1.0, 'sine.inOut'), 7, () =>    // a far shore, one wash
    wash(g, [[-40, HORIZON + 4], [300, 520], [700, 540], [1100, 505], [1500, 530], [W + 40, 515], [W + 40, HORIZON + 6]],
      { color: SHORE, alpha: 0.55, jitter: 3, seed: 8 }));
  // ripples on the water: horizontal strokes, painted on in their slice
  for (let k = 0; k < 9; k++) {
    const y = 640 + k * 45, x = 120 + ((k * 337) % 1400);
    stroke(g, [[x, y], [x + 140, y - 3], [x + 300, y + 2]], { color: DEEP, alpha: 0.45, width: 10, profile: 'leaf', bristles: 3,
      seed: 20 + k, reveal: p(t, 1.8 + k * 0.08, 0.5) });
  }
  BOATS.forEach((b, i) => {
    const sway = t > 5.0 ? 0.006 * (Math.sin(1.15 * t + i) + 0.4 * Math.sin(2.7 * t + 2 * i)) : 0;   // only once finished
    const hull = p(t, b.at, 0.6);
    if (hull > 0) {
      const y = HORIZON + 70, top = [[b.x - b.w / 2, y], [b.x + b.w / 2, y], [b.x + b.w / 2 - 40, y + 60], [b.x - b.w / 2 + 30, y + 60]];
      g.save(); g.globalAlpha = hull;
      wash(g, top, { color: HULL, alpha: 0.7, jitter: 2.5, seed: 40 + i });
      g.restore();
      // its reflection: short horizontal dabs under the hull, broken and fading
      for (let r = 0; r < 5; r++) stroke(g, [[b.x - b.w * 0.35 + r * 12, y + 85 + r * 18], [b.x + b.w * (0.3 - r * 0.05), y + 88 + r * 18]],
        { color: HULL, alpha: 0.35 - r * 0.05, width: 9, profile: 'even', bristles: 2, seed: 60 + i * 7 + r, reveal: p(t, 4.6 + i * 0.15 + r * 0.06, 0.4) });
    }
    g.save();                                            // the mast in ink, drawn up from the deck, swaying after
    g.translate(b.x, HORIZON + 70); g.transform(1, 0, sway, 1, 0, 0);
    ink(g, [[0, 0], [2, -b.mast * 0.5], [-1, -b.mast]], { color: INK, width: 7, wet: 0.35, profile: 'even', seed: 80 + i,
      reveal: p(t, 3.6 + i * 0.25, 0.7) });
    g.restore();
  });
  // the accent, reserved for one thing: the buoys
  [[1300, 700], [760, 760]].forEach(([x, y], i) => {
    const u = p(t, 5.4 + i * 0.2, 0.4);
    if (u > 0) { g.save(); g.globalAlpha = u; wash(g, [[x - 18, y], [x, y - 26], [x + 18, y], [x, y + 14]], { color: ACCENT, alpha: 0.85, jitter: 2, seed: 90 + i }); g.restore(); }
  });
  // the annotation layer: a pen leader line, then the label opening left to right
  const lead = p(t, 6.2, 0.4);
  if (lead > 0) {
    g.strokeStyle = BROWN; g.lineWidth = 2; g.beginPath(); g.moveTo(1310, 690); g.lineTo(1310, 690 - 300 * lead); g.stroke();
  }
  const label = (s, x, y, size, at, color) => {
    const u = p(t, at, 0.5);
    if (u <= 0) return;
    g.save(); g.beginPath(); g.rect(x - 10, y - size, (s.length * size * 0.62 + 20) * tween(u, 0, 1, 'sine.out'), size * 1.6); g.clip();
    g.fillStyle = color; g.font = `${size}px ${HAND}`; g.fillText(s, x, y); g.restore();
  };
  label('buoy · 06:12', 1260, 372, 40, 6.3, INK);
  label('Harbour, dawn', 120, 1000, 44, 6.8, BROWN);
}});
