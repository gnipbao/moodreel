import { stage, texts } from './kit/stage.js';
import { PALETTE, TYPE, TEXTURE } from './kit/tokens.js';
import { MOTION, typed, power, off } from './kit/motion.js';
import { tween, lerp } from './kit/core.js';

// "Boot": the tube wakes, the machine reports itself line by line, clears, types its name, leans in until the name
// fills the glass, and switches off to a dot.
const W = 1920, H = 1080, DUR = 10;
const [CW, CH] = TYPE.cell;
const { dim, normal, bold } = PALETTE.ramp;
const font = (px, w = 400) => `${w} ${px}px ${TYPE.text}`;
const LOG = ['MOODREEL BIOS 0.4', 'MEM CHECK ......... 640K OK', 'LOADING KIT ......... OK', 'PALETTE  P3 AMBER .. OK',
  'GRID     80 X 22 ... OK', 'READERS  MOTION .... OK', 'READY.'];
const starts = LOG.reduce((a, line) => [...a, a[a.length - 1] + line.length * MOTION.type.perChar + 0.1], [0.9]);
const LOG_END = starts[LOG.length];
const CLEAR = 4.0, TITLE = 'MOODREEL', PUSH = 4.6, OFF = 8.5;

function glyphs(g, text, col, row, colour, px = TYPE.size, cw = CW, ch = CH, x0 = 0, y0 = 0) {
  g.font = font(px, colour === bold ? 700 : 400);
  g.fillStyle = colour;
  for (let i = 0; i < text.length; i++) g.fillText(text[i], x0 + (col + i) * cw, y0 + (row + 1) * ch - ch * 0.22);
}

function picture(g, t) {
  if (t < CLEAR) {
    LOG.forEach((line, i) => {
      const s = typed(t, starts[i], line);
      if (!s) return;
      const ok = s.endsWith('OK');
      glyphs(g, ok ? s.slice(0, -2) : s, 2, 1 + i, normal);
      if (ok) glyphs(g, 'OK', 2 + s.length - 2, 1 + i, bold);
    });
    if (t > LOG_END && Math.floor((t - LOG_END) / 0.25) % 2 === 0) {      // the cursor waits
      g.fillStyle = bold;
      g.fillRect(2 * CW, (1 + LOG.length) * CH + 6, CW, CH - 12);
    }
    return;
  }
  // after the clear: the title on a grid that grows about its centre (the camera), and the LOG strip outside it
  const z = lerp(1, MOTION.push.to, tween(t, PUSH, MOTION.push.duration, MOTION.push.ease));
  const s = typed(t, CLEAR, TITLE, MOTION.title.perChar);
  g.save();
  g.translate(W / 2, 480);
  g.scale(z, z);
  glyphs(g, s, 0, 0, bold, TYPE.size, CW, CH, -TITLE.length * CW / 2, -CH / 2);
  g.restore();
  g.fillStyle = dim;
  g.fillRect(48, 956, W - 96, 2);
  g.fillStyle = normal;
  g.fillRect(48, 978, 3 * CW + 16, CH);
  g.font = font(TYPE.size, 700);
  g.fillStyle = PALETTE.ground;
  g.fillText('LOG', 56, 978 + CH - 11);
  const words = ['> SYSTEM', 'READY'].filter((_, i) => t >= 4.4 + i * 0.3).join(' ');
  glyphs(g, words, 5, 0, normal, TYPE.size, CW, CH, 48, 978 - CH * 0 - CH + CH);
}

stage({
  width: W, height: H, duration: DUR, background: PALETTE.ground,
  fonts: [font(40), font(40, 700)],
  draw: (g, t) => {
    g.fillStyle = PALETTE.ground;
    g.fillRect(0, 0, W, H);
    g.shadowColor = 'rgba(255,176,0,0.6)';
    g.shadowBlur = TEXTURE.glow;
    // power on: a line grows from the centre, the raster opens and its flash decays
    const line = power(t, 0.3), open = power(t, 0.55);
    if (line > 0 && t < 1.0) {
      g.fillStyle = bold;
      const w = W * line, h = lerp(4, H, open), a = open > 0 ? Math.exp(-(t - 0.55) / MOTION.afterglow) : 1;
      g.globalAlpha = a;
      g.fillRect((W - w) / 2, (H - h) / 2, w, h);
      g.globalAlpha = 1;
    }
    // power off: the picture squashes to a line, the line to a dot, the dot glows out
    const sy = off(t, OFF), sx = off(t, OFF + MOTION.off.duration);
    if (sx < 1) {
      g.save();
      g.translate(W / 2, H / 2);
      g.scale(1 - sx * 0.995, lerp(1, 0.01, sy));
      g.translate(-W / 2, -H / 2);
      picture(g, t);
      g.restore();
    } else {
      g.globalAlpha = Math.exp(-(t - OFF - 2 * MOTION.off.duration) / 0.15);
      g.fillStyle = bold;
      g.beginPath();
      g.arc(W / 2, H / 2, 6, 0, Math.PI * 2);
      g.fill();
      g.globalAlpha = 1;
    }
    g.shadowColor = 'transparent';
    const { period_px: p, strength } = TEXTURE.scanlines;               // the glass: fine scanlines over everything
    g.fillStyle = `rgba(0,0,0,${strength})`;
    for (let y = 0; y < H; y += p) g.fillRect(0, y, W, 2);
  },
});

texts(t => {
  const k = innerWidth / W;
  return t >= CLEAR + TITLE.length * MOTION.title.perChar && t < OFF
    ? [{ id: 'title', text: TITLE, x0: 400 * k, y0: 360 * k, x1: 1520 * k, y1: 600 * k }] : [];
});
