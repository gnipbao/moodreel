import { stage, texts } from './kit/stage.js';
import { PALETTE, TYPE, TEXTURE } from './kit/tokens.js';
import { BEAT, MOTION, land, go } from './kit/motion.js';
import { vignette } from './kit/texture.js';
import { lerp } from './kit/core.js';

// "Shipped": a release checklist ticks through on the beat, the window switches off like a tube, the version
// number takes the screen alone, and one lime tile is left lit with a toast.
const W = 1920, H = 1080, DUR = 10;
const B = n => n * BEAT;
const [S1, S2, S3] = PALETTE.surfaces, [T1, T2, T3] = PALETTE.text;
const WIN = { x: 480, y: 220, w: 960, h: 560 };
const ROWS = ['build', 'tests', 'docs', 'deploy'];
const font = (w, px, fam = TYPE.text) => `${w} ${px}px ${fam}`;

function rounded(g, x, y, w, h, r) {
  g.beginPath();
  g.roundRect(x, y, w, h, r);
}

function stageBg(g) {
  g.fillStyle = PALETTE.ground;
  g.fillRect(0, 0, W, H);
  let gr = g.createRadialGradient(960, 160, 0, 960, 160, 1000);       // the lift at the upper centre
  gr.addColorStop(0, 'rgba(120,140,190,0.10)');
  gr.addColorStop(1, 'rgba(120,140,190,0)');
  g.fillStyle = gr;
  g.fillRect(0, 0, W, H);
  gr = g.createRadialGradient(1520, 820, 0, 1520, 820, 640);           // one cool glow, single-digit opacity
  gr.addColorStop(0, 'rgba(90,120,255,0.06)');
  gr.addColorStop(1, 'rgba(90,120,255,0)');
  g.fillStyle = gr;
  g.fillRect(0, 0, W, H);
  for (let i = 0; i * 48 <= W; i++) {                                  // the hairline grid on the 48 px module
    g.fillStyle = i % 4 ? 'rgba(255,255,255,0.03)' : 'rgba(255,255,255,0.06)';
    g.fillRect(i * 48, 0, 1, H);
  }
  for (let j = 0; j * 48 <= H; j++) {
    g.fillStyle = j % 4 ? 'rgba(255,255,255,0.03)' : 'rgba(255,255,255,0.06)';
    g.fillRect(0, j * 48, W, 1);
  }
}

// the window: expands from its centre, rows slide in, checks pop, then it switches off (squash to a line, a dot)
function windowShot(g, t) {
  const open = land(t, B(2), MOTION.expand);
  const offY = go(t, B(7)), offX = go(t, B(7) + MOTION.exit.duration, { ease: 'power2.in', duration: 0.1 });
  if (open <= 0 || offX >= 1) return;
  const cx = WIN.x + WIN.w / 2, cy = WIN.y + WIN.h / 2;
  g.save();
  g.translate(cx, cy);
  const s = lerp(0.2, 1, open);
  g.scale(s * (1 - offX), s * lerp(1, 0.02, offY));
  g.translate(-cx, -cy);
  g.shadowColor = 'rgba(0,0,0,0.5)';
  g.shadowBlur = 40;
  g.shadowOffsetY = 12;
  g.fillStyle = S2;
  rounded(g, WIN.x, WIN.y, WIN.w, WIN.h, 18);
  g.fill();
  g.shadowColor = 'transparent';
  g.strokeStyle = 'rgba(255,255,255,0.08)';
  g.lineWidth = 1;
  g.stroke();
  g.fillStyle = S3;                                                    // the title bar: a glyph and a title only
  rounded(g, WIN.x, WIN.y, WIN.w, 56, [18, 18, 0, 0]);
  g.fill();
  g.fillStyle = T3;
  g.fillRect(WIN.x + 24, WIN.y + 22, 12, 12);
  g.font = font(500, 22, TYPE.mono);
  g.fillStyle = T2;
  g.fillText('release.md', WIN.x + 52, WIN.y + 36);
  ROWS.forEach((name, i) => {
    const arrive = B(2 + i), p = land(t, arrive);
    if (t < arrive - MOTION.enter.duration) return;
    const y = WIN.y + 110 + i * 100, x = WIN.x + 64 + (1 - p) * 60;
    g.fillStyle = S1;
    rounded(g, x, y, WIN.w - 128, 72, 12);
    g.fill();
    g.strokeStyle = T3;
    g.lineWidth = 2;
    rounded(g, x + 22, y + 22, 28, 28, 6);
    g.stroke();
    g.font = font(500, 34);
    g.fillStyle = T1;
    g.fillText(name, x + 80, y + 48);
    const c = land(t, B(3 + i), { ease: 'back.out(1.3)', duration: 0.2 });
    if (c > 0) {                                                       // the check pops on the next beat
      g.save();
      g.translate(x + 36, y + 36);
      g.scale(c, c);
      g.fillStyle = T2;
      rounded(g, -14, -14, 28, 28, 6);
      g.fill();
      g.restore();
    }
  });
  g.restore();
}

stage({
  width: W, height: H, duration: DUR, background: PALETTE.ground,
  fonts: [font(600, 280, TYPE.display), font(500, 34), font(500, 22, TYPE.mono), font(500, 38)],
  draw: (g, t) => {
    stageBg(g);
    windowShot(g, t);
    // the number takes the screen alone, with no caption over it, and switches off the same way
    const n = land(t, B(9), MOTION.expand), off = go(t, B(13));
    if (n > 0 && off < 1) {
      g.save();
      g.translate(960, 540);
      const s = lerp(0.6, 1, n);
      g.scale(s, s * (1 - off));
      g.font = font(600, 280, TYPE.display);
      g.textAlign = 'center';
      g.textBaseline = 'middle';
      g.fillStyle = T1;
      g.fillText('2.0', 0, 10);
      g.restore();
    }
    // one tile left lit in the accent, then a toast says it
    const k = land(t, B(14), { ease: 'back.out(1.3)', duration: 0.25 });
    if (k > 0) {
      g.save();
      g.translate(960, 500);
      g.scale(k, k);
      g.shadowColor = PALETTE.accent;
      g.shadowBlur = 48;
      g.fillStyle = PALETTE.accent;
      rounded(g, -48, -48, 96, 96, 18);
      g.fill();
      g.restore();
    }
    const q = go(t, B(15), MOTION.toast);
    if (q > 0) {
      g.save();
      g.globalAlpha = q;
      g.translate(0, (1 - q) * MOTION.toast.rise);
      g.fillStyle = 'rgba(27,32,48,0.92)';
      rounded(g, 780, 880, 360, 76, 38);
      g.fill();
      g.strokeStyle = 'rgba(255,255,255,0.12)';
      g.stroke();
      g.fillStyle = PALETTE.accent;
      g.beginPath();
      g.arc(828, 918, 8, 0, Math.PI * 2);
      g.fill();
      g.font = font(500, 38);
      g.fillStyle = T1;
      g.fillText('shipped', 856, 931);
      g.restore();
    }
    vignette(g, W, H, TEXTURE.vignette);
  },
});

texts(t => {
  const k = innerWidth / W, out = [];
  if (land(t, B(9), MOTION.expand) >= 1 && go(t, B(13)) <= 0) out.push({ id: 'number', text: '2.0', x0: 760 * k, y0: 440 * k, x1: 1160 * k, y1: 650 * k });
  if (go(t, B(15), MOTION.toast) >= 1) out.push({ id: 'toast', text: 'shipped', x0: 856 * k, y0: 900 * k, x1: 1010 * k, y1: 940 * k });
  return out;
});
