// Signal Plates idiom: the paper form. The plate inverts to bone paper (fibres, mottle, a little tooth) and the lyric
// arrives as paperwork: ruled fields filled in mono as they are sung, boxes ticked, and a rubber stamp slammed in signal
// on a hit. Paper plates take no glow and no halation (plate().begin({ paper: true }) and end() see to it).
//
//   paperGround(P);                                        // the sheet, into P.hdr (after P.begin({ paper: true }))
//   form(P.type.ctx, t, { x: 160, y: 180, w: 980, title: 'POWER SAVING · FORM 7', fields: [
//     { label: 'REASON', value: 'save your work', t0: 1.0, t1: 1.6 }, { label: 'CONSENT', tick: true, t0: 2.0 }],
//     stamp: { text: 'DENIED', at: 2.4, x: 760, y: 520, angle: -0.12 } });
import { THREE } from './gl.js';
import { PALETTE, SIZE } from './tokens.js';
import { machine, voice, font } from './signal.js';
import { rng } from './core.js';

const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));

// the sheet: bone with low mottle, short fibres and tooth, in linear light; one pass per GPU (cached on it)
export function paperGround(P, { seed = 3 } = {}) {
  P.G._paper ??= P.G.pass(/* glsl */ `
    uniform float uSeed; uniform vec2 uRes;
    void main() {
      vec2 p = gl_FragCoord.xy;
      float m = fbm(p / 420.0 + uSeed, 4) * 0.035 + fbm(p / 90.0 - uSeed, 3) * 0.012;      // mottle
      float fib = 0.0;
      for (int i = 0; i < 3; i++) {                                                       // fibres: short streaks
        vec2 q = rot2(float(i) * 2.1 + uSeed) * p / vec2(38.0, 3.2);
        fib += smoothstep(0.82, 0.97, snoise(q + float(i) * 17.0)) * 0.018;
      }
      float tooth = (hash12(floor(p)) - 0.5) * 0.02;
      fragColor = vec4(C_BONE * (1.0 + m - fib + tooth), 1.0);
    }`, { uSeed: { value: seed }, uRes: { value: new THREE.Vector2(P.W, P.H) } });
  P.G._paper.u.uSeed.value = seed;
  P.G._paper.render(P.hdr);
}

// a rubber stamp: a double-ruled box and its word in signal, the ink eroded by the paper (seeded), slammed in on `at`:
// it lands 20 % big and settles in 0.1 s
export function stamp(g, t, { text, at, x, y, angle = -0.1, px = Math.round(0.07 * SIZE[1]), seed = 11, color = PALETTE.signal }) {
  const age = t - at;
  if (age < 0) return;
  const s = 1 + 0.2 * Math.max(0, 1 - age / 0.1) ** 2;
  const key = `${text}:${px}:${seed}:${color}`;
  stamp.cache ??= new Map();
  if (!stamp.cache.has(key)) {
    const c = document.createElement('canvas'), q = c.getContext('2d');
    font(q, voice(px, { weight: 900, width: 87.5 }));
    const tw = q.measureText(text).width, pad = px * 0.4;
    c.width = Math.ceil(tw + pad * 2 + 8); c.height = Math.ceil(px * 1.5 + 8);
    font(q, voice(px, { weight: 900, width: 87.5 }));
    q.strokeStyle = q.fillStyle = color;
    q.lineWidth = Math.max(2, px * 0.06);
    q.strokeRect(4, 4, c.width - 8, c.height - 8);
    q.lineWidth = Math.max(1, px * 0.025);
    q.strokeRect(4 + px * 0.12, 4 + px * 0.12, c.width - 8 - px * 0.24, c.height - 8 - px * 0.24);
    q.textBaseline = 'middle';
    q.fillText(text, pad + 4, c.height / 2 + px * 0.04);
    const r = rng(seed), img = q.getImageData(0, 0, c.width, c.height), d = img.data;
    for (let i = 0; i < d.length; i += 4) {                 // starve the ink in specks and a few dry streaks
      const px_ = (i / 4) % c.width, py = Math.floor(i / 4 / c.width);
      const dry = Math.sin(px_ * 0.05 + py * 0.31 + seed) * Math.sin(py * 0.013 + seed * 3) > 0.82;
      if (r() < 0.16 || dry) d[i + 3] *= 0.15 + 0.5 * r();
    }
    q.putImageData(img, 0, 0);
    stamp.cache.set(key, c);
  }
  const c = stamp.cache.get(key);
  g.save();
  g.translate(x, y);
  g.rotate(angle);
  g.scale(s, s);
  g.globalAlpha *= 0.92;
  g.drawImage(c, -c.width / 2, -c.height / 2);
  g.restore();
}

// the form: a mono title, ruled fields whose values are typed in mono as they are sung, tick boxes; a field's `in`
// (0..1, e.g. enter(t, at, i)) slides it in from the left as it fades up
export function form(g, t, { x, y, w, title = null, fields = [], stamp: st = null, px = Math.round(0.034 * SIZE[1]),
  ink = PALETTE.ground, rule = PALETTE.graphite } = {}) {
  g.save();
  g.textBaseline = 'alphabetic';
  let yy = y;
  if (title) {
    font(g, machine(Math.round(px * 0.55), 700));
    g.fillStyle = ink;
    g.fillText(title, x, yy);
    g.fillRect(x, yy + px * 0.35, w, 2);
    yy += px * 1.9;
  }
  for (const f of fields) {
    const lh = px * 2.2, p = clamp(f.in ?? 1);
    g.save();
    g.globalAlpha *= p;
    g.translate((1 - p) * -80, 0);
    font(g, machine(Math.round(px * 0.4), 500));
    g.fillStyle = rule;
    g.fillText(f.label, x, yy);
    g.fillRect(x, yy + lh * 0.62, w, 1);
    if (f.tick !== undefined) {
      const bx = x + w - px * 0.9, by = yy + lh * 0.05, b = px * 0.8;
      g.strokeStyle = ink; g.lineWidth = 1.5;
      g.strokeRect(bx, by, b, b);
      if (f.tick && t >= f.t0) {
        const u = clamp((t - f.t0) / 0.08);
        g.beginPath(); g.moveTo(bx + b * 0.18, by + b * 0.55); g.lineTo(bx + b * 0.42, by + b * (0.55 + 0.25 * Math.min(1, u * 2)));
        if (u > 0.5) g.lineTo(bx + b * (0.42 + 0.4 * (u - 0.5) * 2), by + b * (0.8 - 0.65 * (u - 0.5) * 2));
        g.lineWidth = 3; g.stroke();
      }
    } else if (f.value && t >= f.t0) {
      const n = [...f.value].length, k = Math.min(n, Math.ceil(n * clamp((t - f.t0) / Math.max(1e-3, (f.t1 ?? f.t0) - f.t0))));
      font(g, machine(px, 400));
      g.fillStyle = ink;
      g.fillText([...f.value].slice(0, Math.max(1, k)).join(''), x + px * 0.2, yy + lh * 0.5);
    }
    g.restore();
    yy += lh;
  }
  g.restore();
  if (st) stamp(g, t, st);
  return { bottom: yy };
}
