// every-style: a sound-off news short about the style library, on Caption News (styles/caption-news). The footage is
// Moodreel's own example films, taken in with `moodreel media add` (media/manifest.json: source and licence).
import { stage, texts } from './kit/stage.js';
import { tween, clamp } from './kit/core.js';
import { load } from './kit/media.js';

const M = await load();
const W = 1920, H = 1080, SHOT = 3.0, TURN = 2, END = 12.5;   // cuts on the 120 BPM half-beat grid; shot 3 is the turn;
// the last shot holds 0.5 s longer, an ending
const IVORY = '#f7f5ef', HONEY = '#ffc21a', INK = '#0e0e0c';
const ZH = '"PingFang SC", "Noto Sans SC", sans-serif', EN = '"Helvetica Neue", Helvetica, sans-serif';
// one shot per caption: its footage, the Chinese line in chunks ({} the keyword), the English line, a source tag
const SHOTS = [
  { clip: 'show', zh: ['{59}', '套风格'], en: '59 styles, all code.', source: 'Moodreel styles/index.json · 2026.10', count: 59 },
  { clip: 'harbour', zh: ['过去只能做', '{23}', '套'], en: 'Until now, only 23.', source: 'styles/index.json · phase: mvp' },
  { clip: 'island', zh: ['现在', '{全部}', '能做'], en: 'Now all of them can.' },
  { clip: 'save', zh: ['像素 笔触', '{3D}', '配乐'], en: 'Pixels, brushes, 3D, music.' },
];

function chunkLine(g, s, chunks, local) {
  g.font = `600 88px ${ZH}`;
  let x = 120;
  chunks.forEach((c, k) => {
    const at = 0.12 * k, u = local < at ? 0 : tween(local, at, 0.13, 'back.out(1.6)');  // each chunk slams 0.12 s after
    const key = c.startsWith('{'), text = key ? c.slice(1, -1) : c;
    const shown = s.count != null && key ? String(Math.round(s.count * tween(local, 0.15, 0.6, 'power3.out'))) : text;
    const w = g.measureText(key ? String(s.count ?? text) : text).width;
    if (u > 0) {
      g.save();
      g.translate(x + w / 2, 948 - 30); g.scale(1.3 - 0.3 * u, 1.3 - 0.3 * u); g.globalAlpha = clamp((local - at) / 0.04); g.translate(-(x + w / 2), -(948 - 30));
      if (key) {                                         // the keyword: a honey block wipes in behind it, the text turns ink
        const wipe = tween(local, at, 0.12, 'none');
        g.fillStyle = HONEY; g.fillRect(x - 14, 948 - 84, (w + 28) * wipe, 104);
      }
      g.shadowColor = 'rgba(0,0,0,0.6)'; g.shadowBlur = key ? 0 : 20;
      g.fillStyle = key ? INK : IVORY; g.fillText(shown, x, 948);
      g.restore();
    }
    x += w + 28;
  });
}

texts(t => {
  const i = Math.min(SHOTS.length - 1, Math.floor(t / SHOT)), s = SHOTS[i], local = t - i * SHOT;
  const on = [{ id: `zh${i}`, text: s.zh.join('').replace(/[{}]/g, ''), x0: 120, y0: 864, x1: 900, y1: 968 }];
  if (local >= 0.1) on.push({ id: `en${i}`, text: s.en, x0: 120, y0: 986, x1: 620, y1: 1026 });
  return on;
});

stage({ width: W, height: H, duration: END, background: '#000', fonts: [`600 88px ${ZH}`, `500 33px ${EN}`],
  draw: (g, t) => {
    const i = Math.min(SHOTS.length - 1, Math.floor(t / SHOT)), s = SHOTS[i], local = t - i * SHOT;
    g.filter = 'contrast(1.07) saturate(0.92) brightness(0.98)';                      // one grade for all the footage
    g.drawImage(M.frame(s.clip, t, { from: i * SHOT }), 0, 0, W, H);                   // footage, full bleed
    g.filter = 'none';
    g.globalCompositeOperation = 'soft-light'; g.fillStyle = 'rgba(255,170,90,0.06)'; g.fillRect(0, 0, W, H);
    g.globalCompositeOperation = 'source-over';
    const shade = g.createLinearGradient(0, 560, 0, H);   // the caption needs its ground
    shade.addColorStop(0, 'rgba(0,0,0,0)'); shade.addColorStop(1, 'rgba(0,0,0,0.84)');
    g.fillStyle = shade; g.fillRect(0, 560, W, H - 560);
    const lid = g.createLinearGradient(0, 0, 0, 200);     // and so do the bug and the credit
    lid.addColorStop(0, 'rgba(0,0,0,0.55)'); lid.addColorStop(1, 'rgba(0,0,0,0)');
    g.fillStyle = lid; g.fillRect(0, 0, W, 200);
    // channel bug (a fictional channel), top left
    g.fillStyle = HONEY; g.fillRect(96, 52, 360, 46);
    g.fillStyle = INK; g.font = `600 26px ${ZH}`; g.fillText('画格快讯', 112, 84);
    g.font = `700 20px ${EN}`; g.fillText('FRAME WIRE · STYLES', 232, 83);
    if (s.source) {                                      // source tag, on data shots: slides in 0.2 s
      const u = tween(local, 0.2, 0.2, 'power2.out'), x = 96 - 420 * (1 - u);
      g.fillStyle = IVORY; g.fillRect(x, 108, 70, 36); g.fillStyle = INK; g.font = `600 22px ${ZH}`; g.fillText('来源', x + 12, 134);
      g.fillStyle = 'rgba(14,14,12,0.85)'; g.fillRect(x + 70, 108, 420, 36);
      g.fillStyle = IVORY; g.font = `500 20px ${EN}`; g.fillText(s.source, x + 84, 133);
    }
    g.font = `500 19px ${EN}`;                           // footage credit, top right, on every shot
    const credit = `视频 ${M.info(s.clip).original.replace('.mp4', '')} · Moodreel · MIT`, cw = g.measureText(credit).width + 28;
    g.fillStyle = 'rgba(0,0,0,0.5)'; g.fillRect(W - 96 - cw, 56, cw, 34); g.fillStyle = IVORY; g.fillText(credit, W - 96 - cw + 14, 79);
    chunkLine(g, s, s.zh, local);
    const e = clamp((local - 0.1) / 0.18);               // the English line: fades and rises 10 px, 0.1 s after
    if (e > 0) { g.globalAlpha = e; g.fillStyle = IVORY; g.font = `500 33px ${EN}`; g.fillText(s.en, 120, 1014 + 10 * (1 - e)); g.globalAlpha = 1; }
    const flash = t - TURN * SHOT;                       // the turn gets a two-frame white flash
    if (flash >= 0 && flash < 2 / 24) { g.fillStyle = '#fff'; g.globalAlpha = 1 - flash * 12; g.fillRect(0, 0, W, H); g.globalAlpha = 1; }
  } });
