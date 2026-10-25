// Signal Plates: the style's own core. Its three voices (fonts), the karaoke light of a sung word, and the plate: a GPU
// frame in linear HDR where the idioms draw (kit/engraved.js, kit/linefield.js, kit/prompt.js, kit/form.js), with a 2D
// layer for type, a hot layer for what glows, and the film post with the style's finish (tokens.js FINISH).
//
//   import { faces, voice, machine, karaoke, plate } from './kit/signal.js';
//   const P = plate();
//   stage({ ..., prepare: faces, draw: (g, t) => {
//     P.begin();                                   // the ground, in linear light
//     ...idioms render into P.hdr...
//     const q = P.type.ctx; q.font = voice(200, { weight: 900, width: 75 }); karaoke(q, 'WORK', 160, 640, u);
//     P.end(g, t, { hit: M.hit('kick', t) });       // type and glow composited, the post, onto the stage
//   } });
import { gpu, linear } from './gl.js';
import { PALETTE, TYPE, FINISH, SIZE } from './tokens.js';

const FONT = name => new URL(`./fonts/${name}`, import.meta.url).href;

// the three voices (DECISIONS.md 3, SIL OFL): load once, before the first frame (stage({ prepare: faces }))
export async function faces() {
  const list = [
    ['Archivo', 'Archivo-var.ttf', { weight: '100 900', stretch: '62.5% 125%' }],
    ['Plex Mono', 'IBMPlexMono-Regular.ttf', { weight: '400' }],
    ['Plex Mono', 'IBMPlexMono-Medium.ttf', { weight: '500' }],
    ['Plex Mono', 'IBMPlexMono-Bold.ttf', { weight: '700' }],
    ['Cormorant Garamond', 'CormorantGaramond-Italic-var.ttf', { weight: '300 700', style: 'italic' }],
  ];
  await Promise.all(list.map(([family, file, desc]) =>
    new FontFace(family, `url(${JSON.stringify(FONT(file))})`, desc).load().then(f => document.fonts.add(f))));
}

// Archivo's width axis by the canvas's keywords (62.5 % to 125 %); between steps, scale x yourself
const STRETCH = [[62.5, 'extra-condensed'], [75, 'condensed'], [87.5, 'semi-condensed'], [100, 'normal'],
  [112.5, 'semi-expanded'], [125, 'expanded']];
export const stretch = width => STRETCH.reduce((a, b) => (Math.abs(b[0] - width) < Math.abs(a[0] - width) ? b : a))[1];

// font strings: the voice (the lyric), the machine (tokens, labels, readouts), the prophet (rare)
export const voice = (px, { weight = 800, width = 100 } = {}) => `${weight} ${stretch(width)} ${px}px ${TYPE.display}`;
export const machine = (px, weight = 400) => `${weight} ${px}px ${TYPE.text}`;
export const prophet = (px, weight = 400) => `italic ${weight} ${px}px ${TYPE.serif}`;
// set a font on a context, width included (fontStretch is what Chrome reads for the canvas)
export function font(g, f) {
  g.font = f;
  const k = STRETCH.find(([, kw]) => f.includes(` ${kw} `));
  if ('fontStretch' in g) g.fontStretch = k ? k[1] : 'normal';
}

// size of a tier, in px at this height: hook, hookSmall, line, lineSmall, note, small, tiny
export const size = (tier, H = SIZE[1]) => Math.round(TYPE[tier] * H);

// A sung word: dim (bone at 35 %) until it is sung, then lit from left to right as the voice crosses it (u 0..1),
// never ahead of it. Lit in `lit` (signal for the word being sung, bone once it is done). Returns its width.
export function karaoke(g, text, x, y, u, { lit = PALETTE.signal, dim = 0.35, base = PALETTE.bone, underline = false } = {}) {
  const w = g.measureText(text).width;
  g.save();
  g.globalAlpha *= dim;
  g.fillStyle = base;
  g.fillText(text, x, y);
  g.restore();
  if (u > 0) {
    g.save();
    g.beginPath();
    const asc = g.measureText('Hg').actualBoundingBoxAscent * 1.4;
    g.rect(x - 2, y - asc, (w + 4) * Math.min(1, u), asc * 1.8);
    g.clip();
    g.fillStyle = lit;
    g.fillText(text, x, y);
    if (underline) g.fillRect(x, y + asc * 0.16, w, Math.max(2, asc * 0.045));
    g.restore();
  }
  return w;
}

// a hairline registration tick in each corner (a plate's frame), graphite, 1 px at 1080p
export function ticks(g, W = SIZE[0], H = SIZE[1], { inset = 40, len = 22, color = PALETTE.graphite } = {}) {
  g.save();
  g.strokeStyle = color;
  g.lineWidth = 1;
  for (const [x, y, sx, sy] of [[inset, inset, 1, 1], [W - inset, inset, -1, 1], [inset, H - inset, 1, -1], [W - inset, H - inset, -1, -1]]) {
    g.beginPath();
    g.moveTo(x + sx * len, y + 0.5 * sy);
    g.lineTo(x + 0.5 * sx, y + 0.5 * sy);
    g.lineTo(x + 0.5 * sx, y + sy * len);
    g.stroke();
  }
  g.restore();
}

// linear rgb of a palette colour, for shaders and lines
export const lin = name => linear(PALETTE[name] ?? name);

// The plate: a GPU frame in linear HDR. begin() clears it to the ground (or bone paper with { paper: true });
// idioms render into P.hdr; P.type is a 2D layer for type and marks (composited as drawn, so orange passes the glow
// threshold and bone doesn't), P.hot a 2D layer composited `heat` times brighter (the spark's core, a hot band);
// end() composites both, runs the post with the style's finish and draws the result on the stage.
export function plate(W = SIZE[0], H = SIZE[1], opts = {}) {
  const G = gpu(W, H, opts);
  const hdr = G.rt(), type = G.layer(W, H), hot = G.layer(W, H);
  let paperPlate = false;
  return { G, hdr, type, hot, W, H,
    begin({ paper = false, color } = {}) {
      paperPlate = paper;
      G.clear(hdr, lin(color ?? (paper ? 'bone' : 'ground')), 1);
      type.clear();
      hot.clear();
    },
    // the post's settings for this frame: hit (a drum's hit, 0..1) shakes the frame FINISH.kickShake px, seeded by the
    // frame so a frame shows one state across its shutter, and widens the fringe (the reference answers its kicks with
    // shake, not a zoom: moodreel sync); flash, invert, shake, zoom pass on
    end(g, t, { hit = 0, flash = 0, invert = 0, shake = [0, 0], zoom = 1, heat = 2.5, grain, exposure = 1, ...rest } = {}) {
      const f = Math.round(t * 60), h = n => { const x = Math.sin(f * 127.1 + n * 311.7) * 43758.5453; return x - Math.floor(x) - 0.5; };
      shake = [shake[0] + 2 * h(1) * FINISH.kickShake * hit, shake[1] + 2 * h(2) * FINISH.kickShake * hit];
      G.comp(type.upload(), hdr);
      G.comp(hot.upload(), hdr, { tint: [heat, heat, heat] });
      const blur = window.MOTION_BLUR?.samples > 1;
      G.post(hdr.texture, {
        bloom: FINISH.bloom, bloomThreshold: FINISH.bloomThreshold, vignette: FINISH.vignette,
        halation: paperPlate ? 0 : FINISH.halation,                    // no halation or glow on paper
        ca: FINISH.ca * (paperPlate ? 0.3 : 1) * (1 + 1.5 * hit), zoom, flash, invert, shake,   // ink on paper takes no fringe
        exposure: exposure * (1 + FINISH.kickGlow * hit),                                        // the glow breathes up on the hit
        grain: grain ?? (blur ? 0 : FINISH.grain),                     // under motion blur, grain goes in finish()
        time: t, ...(paperPlate ? { bloom: 0 } : {}), ...rest,
      });
      G.show(g, 0, 0, W, H);
    } };
}
