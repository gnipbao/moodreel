// kit/3dcv/paint.js — ported from 3DCodeVerse (https://github.com/gaoypeng/3dcodeverse), awesome showcase
//   (https://huggingface.co/datasets/3dcodeverse/3dcodeverse-awesome-showcase): the 30-second film's code,
//   source src/core/paint.js, round r02, git blob 7e55945c9231e069ce8dbe6ae024585e2fe473e6.
// Licence: CC BY-NC-SA 4.0 (https://creativecommons.org/licenses/by-nc-sa/4.0/), see kit/3dcv/LICENSE.
//   Non-commercial use only; adaptations keep this licence. The rest of moodreel is MIT.
// Changes by moodreel (2026-11-08): three.js taken from ../three.js instead of the bare 'three' import; this header.

// paint.js — canvas2D painted-texture helpers -> THREE textures.  All randomness is seeded (deterministic).
// Typical use:
//   const P = paint.canvas(1024, 1024);
//   paint.fill(P, '#e7c3a8'); paint.gradient(P, [[0,'#f0d0b8'],[1,'#c9a08e']], {angle: 90});
//   paint.blotches(P, {seed: 3, count: 60, colors: ['#f3d6c0', '#d7ae98'], alpha: 0.12, size: [40, 160]});
//   paint.noise(P, {amount: 0.05, seed: 1});
//   const tex = paint.texture(P, {repeat: [2, 2]});
// Owner: look panel (look promotion stage, 2026-11-01; foundation stage before).
import { THREE } from '../three.js';
import { rng } from './util.js';

/** canvas(w, h) -> { c: HTMLCanvasElement, g: CanvasRenderingContext2D, w, h } */
export function canvas(w = 1024, h = w) {
  const c = document.createElement('canvas'); c.width = w; c.height = h;
  const g = c.getContext('2d', { willReadFrequently: false });
  return { c, g, w, h };
}
/** texture(P, { srgb=true, repeat:[u,v], wrap='repeat'|'clamp'|'mirror', anisotropy=8, mipmaps=true, flipY=true }) -> CanvasTexture */
export function texture(P, o = {}) {
  const t = new THREE.CanvasTexture(P.c || P);
  t.colorSpace = o.srgb === false ? THREE.NoColorSpace : THREE.SRGBColorSpace;
  const wrap = o.wrap === 'clamp' ? THREE.ClampToEdgeWrapping : o.wrap === 'mirror' ? THREE.MirroredRepeatWrapping : (o.repeat || o.wrap === 'repeat') ? THREE.RepeatWrapping : THREE.ClampToEdgeWrapping;
  t.wrapS = t.wrapT = wrap;
  if (o.repeat) t.repeat.set(o.repeat[0], o.repeat[1]);
  t.anisotropy = o.anisotropy ?? 8;
  t.generateMipmaps = o.mipmaps !== false;
  t.minFilter = o.mipmaps === false ? THREE.LinearFilter : THREE.LinearMipmapLinearFilter;
  if (o.flipY === false) t.flipY = false;
  t.needsUpdate = true;
  return t;
}
const cssColor = c => (typeof c === 'string' ? c : c && c.isColor ? '#' + c.getHexString() : Array.isArray(c) ? `rgb(${c.map(v => Math.round(v * 255)).join(',')})` : '#ff00ff');
function hexToRGB(hex) { const h = hex.replace('#', ''); return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)]; }
const rgba = (hex, a) => { const [r, g, b] = hexToRGB(cssColor(hex)); return `rgba(${r},${g},${b},${a})`; };

/** fill(P, color) */
export function fill(P, color) { P.g.save(); P.g.globalAlpha = 1; P.g.fillStyle = cssColor(color); P.g.fillRect(0, 0, P.w, P.h); P.g.restore(); return P; }

/**
 * gradient(P, stops, { angle=90 (deg; 90 = top->bottom), type='linear'|'radial', center:[0.5,0.5], radius:0.7, alpha=1, blend })
 * stops: [[pos 0..1, color], ...]
 */
export function gradient(P, stops, o = {}) {
  const { g, w, h } = P; let gr;
  if (o.type === 'radial') {
    const c = o.center || [0.5, 0.5], r = (o.radius ?? 0.7) * Math.max(w, h);
    gr = g.createRadialGradient(c[0] * w, c[1] * h, 0, c[0] * w, c[1] * h, r);
  } else {
    const a = (o.angle ?? 90) * Math.PI / 180, dx = Math.cos(a), dy = Math.sin(a);
    const L = Math.abs(dx) * w / 2 + Math.abs(dy) * h / 2;
    gr = g.createLinearGradient(w / 2 - dx * L, h / 2 - dy * L, w / 2 + dx * L, h / 2 + dy * L);
  }
  for (const [p, c] of stops) gr.addColorStop(p, cssColor(c));
  g.save(); g.globalAlpha = o.alpha ?? 1; if (o.blend) g.globalCompositeOperation = o.blend;
  g.fillStyle = gr; g.fillRect(0, 0, w, h); g.restore();
  return P;
}

// wrapped copies of a mark that crosses the canvas border (tileable textures)
function tileOffsets(tile, x, y, rad, w, h) {
  if (!tile) return [[0, 0]];
  const out = [];
  for (const ox of [-w, 0, w]) for (const oy of [-h, 0, h]) {
    if (x + ox + rad < 0 || x + ox - rad > w || y + oy + rad < 0 || y + oy - rad > h) continue;
    out.push([ox, oy]);
  }
  return out;
}

/**
 * blotches(P, { seed, count=40, colors:[...], alpha=0.15 (or [min,max]), size:[min,max] px, stretch:[min,max], softness=0.8,
 *               region:[x0,y0,x1,y1] (0..1), blend, tile=false (wrap marks across edges -> seamless repeat) }) — soft daubs.
 */
export function blotches(P, o = {}) {
  const r = rng(o.seed ?? 1), { g, w, h } = P;
  const cols = o.colors || ['#ffffff', '#000000'], n = o.count ?? 40, sz = o.size || [20, 120], st = o.stretch || [1, 2.2];
  const reg = o.region || [0, 0, 1, 1], soft = o.softness ?? 0.8;
  const al = Array.isArray(o.alpha) ? o.alpha : [o.alpha ?? 0.15, o.alpha ?? 0.15];
  g.save(); if (o.blend) g.globalCompositeOperation = o.blend;
  for (let i = 0; i < n; i++) {
    const x = (reg[0] + r() * (reg[2] - reg[0])) * w, y = (reg[1] + r() * (reg[3] - reg[1])) * h;
    const s = r.range(sz[0], sz[1]), k = r.range(st[0], st[1]), ang = o.angle != null ? o.angle * Math.PI / 180 + r.range(-0.2, 0.2) : r() * Math.PI;
    const c = r.pick(cols), a = r.range(al[0], al[1]);
    for (const [ox, oy] of tileOffsets(o.tile, x, y, s * k, w, h)) {
      g.save(); g.translate(x + ox, y + oy); g.rotate(ang); g.scale(k, 1);
      const gr = g.createRadialGradient(0, 0, 0, 0, 0, s);
      gr.addColorStop(0, rgba(c, a)); gr.addColorStop(Math.max(0.01, 1 - soft), rgba(c, a)); gr.addColorStop(1, rgba(c, 0));
      g.fillStyle = gr; g.beginPath(); g.arc(0, 0, s, 0, Math.PI * 2); g.fill();
      g.restore();
    }
  }
  g.restore();
  return P;
}

/**
 * strokes(P, { seed, count=200, colors, alpha=0.1, width:[min,max], length:[min,max], angle (deg, mean), jitter (deg), curve=0.2,
 *              region, blend, tile }) — directional soft brush strokes (hair streaks, grass, painted fabric).
 */
export function strokes(P, o = {}) {
  const r = rng(o.seed ?? 2), { g, w, h } = P;
  const cols = o.colors || ['#ffffff'], n = o.count ?? 200, wd = o.width || [2, 6], ln = o.length || [20, 80];
  const al = Array.isArray(o.alpha) ? o.alpha : [o.alpha ?? 0.1, o.alpha ?? 0.1];
  const reg = o.region || [0, 0, 1, 1], A = (o.angle ?? 0) * Math.PI / 180, J = (o.jitter ?? 15) * Math.PI / 180;
  g.save(); g.lineCap = 'round'; if (o.blend) g.globalCompositeOperation = o.blend;
  for (let i = 0; i < n; i++) {
    const x = (reg[0] + r() * (reg[2] - reg[0])) * w, y = (reg[1] + r() * (reg[3] - reg[1])) * h;
    const a = A + r.range(-J, J), L = r.range(ln[0], ln[1]), cv = (o.curve ?? 0.2) * r.range(-1, 1);
    const x1 = x + Math.cos(a) * L, y1 = y + Math.sin(a) * L;
    const mx = (x + x1) / 2 - Math.sin(a) * L * cv, my = (y + y1) / 2 + Math.cos(a) * L * cv;
    g.strokeStyle = rgba(r.pick(cols), r.range(al[0], al[1])); g.lineWidth = r.range(wd[0], wd[1]);
    for (const [ox, oy] of tileOffsets(o.tile, x, y, L + 4, w, h)) { g.beginPath(); g.moveTo(x + ox, y + oy); g.quadraticCurveTo(mx + ox, my + oy, x1 + ox, y1 + oy); g.stroke(); }
  }
  g.restore();
  return P;
}

/**
 * blocks(P, polys, { soft=0 (px blur), alpha=1 }) — flat colour blocks.  polys: [{ pts:[[u,v],...] (0..1, v down), color }, ...]
 * Use for the vest facets, trouser stripe, building window blocks.
 */
export function blocks(P, polys, o = {}) {
  const { g, w, h } = P;
  g.save(); if (o.soft) g.filter = `blur(${o.soft}px)`; g.globalAlpha = o.alpha ?? 1;
  for (const p of polys) {
    g.fillStyle = cssColor(p.color); g.beginPath();
    p.pts.forEach(([u, v], i) => (i ? g.lineTo(u * w, v * h) : g.moveTo(u * w, v * h)));
    g.closePath(); g.fill();
  }
  g.restore();
  return P;
}

/**
 * noise(P, { seed, amount=0.06 (+-fraction of 255), mono=true, scale=1 (px cell), blend='source-over' }) — fine per-pixel noise,
 * added in place via ImageData (seeded).  For value-noise mottling use fbm().
 */
export function noise(P, o = {}) {
  const r = rng(o.seed ?? 3), { g, w, h } = P, amt = (o.amount ?? 0.06) * 255, sc = Math.max(1, Math.round(o.scale || 1));
  const img = g.getImageData(0, 0, w, h), d = img.data;
  const cw = Math.ceil(w / sc), ch = Math.ceil(h / sc), cells = new Float32Array(cw * ch * 3);
  for (let i = 0; i < cells.length; i++) cells[i] = r() * 2 - 1;
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    const ci = ((y / sc | 0) * cw + (x / sc | 0)) * 3, i = (y * w + x) * 4;
    const n0 = cells[ci] * amt;
    d[i] = Math.max(0, Math.min(255, d[i] + n0)); d[i + 1] = Math.max(0, Math.min(255, d[i + 1] + (o.mono === false ? cells[ci + 1] * amt : n0)));
    d[i + 2] = Math.max(0, Math.min(255, d[i + 2] + (o.mono === false ? cells[ci + 2] * amt : n0)));
  }
  g.putImageData(img, 0, 0);
  return P;
}

/** valueNoise2(seed, period=0 | [px,py]) -> f(x, y) in [0,1] smooth lattice noise (CPU fbm / masks); period>0 wraps the lattice. */
export function valueNoise2(seed = 1, period = 0) {
  const r = rng(seed), N = 256, perm = new Uint8Array(N * 2), vals = new Float32Array(N);
  for (let i = 0; i < N; i++) { perm[i] = i; vals[i] = r(); }
  for (let i = N - 1; i > 0; i--) { const j = Math.floor(r() * (i + 1)); [perm[i], perm[j]] = [perm[j], perm[i]]; }
  for (let i = 0; i < N; i++) perm[N + i] = perm[i];
  const [PX, PY] = Array.isArray(period) ? period : [period, period];
  const v = PX > 0 ? (x, y) => { x = ((x % PX) + PX) % PX; y = ((y % PY) + PY) % PY; return vals[perm[(perm[x & 255] + y) & 511] & 255]; }
    : (x, y) => vals[perm[(perm[x & 255] + y) & 511] & 255];
  return (x, y) => {
    const xi = Math.floor(x), yi = Math.floor(y), xf = x - xi, yf = y - yi;
    const u = xf * xf * (3 - 2 * xf), w = yf * yf * (3 - 2 * yf);
    const a = v(xi, yi), b = v(xi + 1, yi), c = v(xi, yi + 1), d = v(xi + 1, yi + 1);
    return a + (b - a) * u + (c - a) * w + (a - b - c + d) * u * w;
  };
}
/**
 * fbm(P, { seed, scale=0.01 (cycles per px), octaves=4, colors:[dark, light], alpha=0.25, contrast=1, blend, tile }) — painted mottling.
 */
export function fbm(P, o = {}) {
  const { g, w, h } = P, oct = o.octaves ?? 4, sc = o.scale ?? 0.01;
  const ca = hexToRGB(cssColor((o.colors || ['#000000', '#ffffff'])[0])), cb = hexToRGB(cssColor((o.colors || ['#000000', '#ffffff'])[1]));
  const A = o.alpha ?? 0.25, k = o.contrast ?? 1;
  // per octave: frequency (cells per px) and an optional periodic lattice so the texture tiles seamlessly
  const octs = []; let f = sc;
  for (let q = 0; q < oct; q++) {
    const cx = Math.max(1, Math.round(w * f)), cy = Math.max(1, Math.round(h * f));
    octs.push(o.tile ? { n: valueNoise2((o.seed ?? 4) + q * 101, [cx, cy]), fx: cx / w, fy: cy / h, per: true }
                     : { n: valueNoise2((o.seed ?? 4) + q * 101), fx: f, fy: f });
    f *= 2.02;
  }
  const tmp = canvas(w, h), img = tmp.g.createImageData(w, h), d = img.data;
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    let s = 0, amp = 0.5, nn = 0;
    for (let q = 0; q < oct; q++) { const O = octs[q]; s += amp * O.n(x * O.fx + (O.per ? 0 : q * 31.7), y * O.fy + (O.per ? 0 : q * 17.3)); nn += amp; amp *= 0.5; }
    const t = Math.min(1, Math.max(0, (s / nn - 0.5) * k + 0.5));
    const i = (y * w + x) * 4;
    d[i] = ca[0] + (cb[0] - ca[0]) * t; d[i + 1] = ca[1] + (cb[1] - ca[1]) * t; d[i + 2] = ca[2] + (cb[2] - ca[2]) * t; d[i + 3] = 255 * A;
  }
  tmp.g.putImageData(img, 0, 0);
  g.save(); if (o.blend) g.globalCompositeOperation = o.blend; g.drawImage(tmp.c, 0, 0); g.restore();
  return P;
}

/**
 * strata(P, { seed, colors:['#7d9a3c', '#9fb84a', ...] (band fills, cycled), count=8, angle=0 (deg; 0 = horizontal bands),
 *             wave=0.035 (edge amplitude, fraction of the band axis), waves:[1,4] (cycles across the canvas), jag=0.006 (brushy
 *             edge noise), edge=1.2 (px blur of the band edges), rim:{color, width:3 px, alpha:0.5} (lit lip on each band top),
 *             shade:{color, width:0.35 (fraction of the band), alpha:0.25} (soft shadow under each lip), dry:0.35 (dry-brush
 *             streak density along the bands, 0 = none), dryColors, dryAlpha:[0.04,0.12], region:[x0,y0,x1,y1], tile:false })
 * Painterly banded layers: hills / canyon walls / terraces / ploughed fields — wavy colour bands with brushy edges, a lit
 * rim and a soft shade under each lip, and dry-brush streaks running along the band (the reference's striated hills, f612–636,
 * and rust canyon walls, f646–700).  With tile:true the waves are periodic so a repeated texture has no seam.
 */
export function strata(P, o = {}) {
  const r = rng(o.seed ?? 21), { g, w, h } = P;
  const cols = o.colors || ['#86a046', '#a3bb52', '#6f8c3e', '#b6c862'], n = o.count ?? 8;
  const reg = o.region || [0, 0, 1, 1], A = (o.angle ?? 0) * Math.PI / 180;
  const X0 = reg[0] * w, Y0 = reg[1] * h, RW = (reg[2] - reg[0]) * w, RH = (reg[3] - reg[1]) * h;
  const wave = (o.wave ?? 0.035) * RH, wv = o.waves || [1, 4], jag = (o.jag ?? 0.006) * RH, tile = !!o.tile;
  // band boundaries: y_k(x) = base_k + sum of 2 sines (+ brushy jitter); periodic in x when tiling
  const bounds = [];
  for (let k = 0; k <= n; k++) {
    const base = (k / n) * RH + (k > 0 && k < n ? r.range(-0.25, 0.25) * RH / n : 0);
    const f1 = tile ? Math.max(1, Math.round(r.range(wv[0], wv[1]))) : r.range(wv[0], wv[1]), f2 = tile ? f1 + r.int(1, 3) : f1 * r.range(1.7, 2.6);
    const p1 = r() * 6.283, p2 = r() * 6.283, a1 = r.range(0.5, 1) * wave, a2 = r.range(0.15, 0.4) * wave, js = r() * 1000;
    const jn = valueNoise2((o.seed ?? 21) * 7 + k, tile ? [64, 64] : 0);
    bounds.push(x => (k === 0 ? -wave * 2 : k === n ? RH + wave * 2 : base + a1 * Math.sin(x / RW * f1 * 6.283 + p1) + a2 * Math.sin(x / RW * f2 * 6.283 + p2) + (jn(x / RW * 64, js % 64) - 0.5) * 2 * jag));
  }
  const N = Math.max(32, Math.round(RW / 6));
  const band = (cg, k) => {
    cg.beginPath();
    for (let j = 0; j <= N; j++) { const x = j / N * RW; j ? cg.lineTo(x, bounds[k](x)) : cg.moveTo(x, bounds[k](x)); }
    for (let j = N; j >= 0; j--) { const x = j / N * RW; cg.lineTo(x, bounds[k + 1](x)); }
    cg.closePath();
  };
  const L = canvas(Math.ceil(RW), Math.ceil(RH)), lg = L.g;
  lg.save(); if (o.edge ?? 1.2) lg.filter = `blur(${o.edge ?? 1.2}px)`;
  for (let k = 0; k < n; k++) { lg.fillStyle = cssColor(cols[k % cols.length]); band(lg, k); lg.fill(); }
  lg.restore();
  // shade under each lip (soft gradient below the band's top edge) and the lit rim on it
  const sh = o.shade === false ? null : { color: '#2c3a28', width: 0.35, alpha: 0.25, ...(o.shade || {}) };
  const rim = o.rim === false ? null : { color: '#f4f0b8', width: 3, alpha: 0.45, ...(o.rim || {}) };
  for (let k = 1; k < n; k++) {
    if (sh) {
      lg.save(); lg.filter = `blur(${Math.max(1, RH / n * sh.width * 0.35)}px)`; lg.globalAlpha = sh.alpha; lg.fillStyle = cssColor(sh.color);
      lg.beginPath();
      for (let j = 0; j <= N; j++) { const x = j / N * RW; j ? lg.lineTo(x, bounds[k](x) + 1) : lg.moveTo(x, bounds[k](x) + 1); }
      for (let j = N; j >= 0; j--) { const x = j / N * RW; lg.lineTo(x, bounds[k](x) + RH / n * sh.width); }
      lg.closePath(); lg.fill(); lg.restore();
    }
    if (rim) {
      lg.save(); lg.filter = `blur(${Math.max(0.6, rim.width * 0.3)}px)`; lg.globalAlpha = rim.alpha; lg.strokeStyle = cssColor(rim.color); lg.lineWidth = rim.width; lg.lineCap = 'round';
      lg.beginPath();
      for (let j = 0; j <= N; j++) { const x = j / N * RW, y = bounds[k](x) - rim.width * 0.4; j ? lg.lineTo(x, y) : lg.moveTo(x, y); }
      lg.stroke(); lg.restore();
    }
  }
  // dry-brush streaks along the bands (follow the local band direction)
  const dry = o.dry ?? 0.35;
  if (dry > 0) {
    const dc = o.dryColors || ['#ffffff', '#000000'], da = o.dryAlpha || [0.04, 0.12];
    const cnt = Math.round(RW * RH / 260 * dry);
    lg.save(); lg.lineCap = 'round';
    for (let i = 0; i < cnt; i++) {
      const x = r() * RW, k = r.int(0, n - 1), y0 = bounds[k](x), y1 = bounds[k + 1](x), t = r(), y = y0 + (y1 - y0) * t;
      const len = r.range(0.04, 0.16) * RW, x1 = x + len, yb = bounds[k](x1) + (bounds[k + 1](x1) - bounds[k](x1)) * t;
      lg.strokeStyle = rgba(r.pick(dc), r.range(da[0], da[1])); lg.lineWidth = r.range(0.6, 2.2);
      for (const ox of tile ? [0, -RW] : [0]) { lg.beginPath(); lg.moveTo(x + ox, y); lg.quadraticCurveTo(x + ox + len / 2, (y + yb) / 2 + r.range(-1, 1) * 2, x1 + ox, yb); lg.stroke(); }
    }
    lg.restore();
  }
  g.save(); g.translate(X0 + RW / 2, Y0 + RH / 2); g.rotate(A); g.drawImage(L.c, -RW / 2, -RH / 2); g.restore();
  return P;
}

/**
 * speckle(P, { seed, density=0.06 (dots per px), colors:['#ffffff', '#3a2a3a'], alpha:[0.08, 0.3], size:[0.5, 1.4] (px radius),
 *              clump=0.3 (fraction of dots placed next to a previous one), region, blend, tile })
 * Scattered pixel-scale dots: woven-fabric / sandstone / clay speckle for the reference's "speckled fabric" (sh1 visitors,
 * lectern canvas).  Use near-white + darker-than-base colours at low alpha over a flat base.
 */
export function speckle(P, o = {}) {
  const r = rng(o.seed ?? 31), { g, w, h } = P;
  const reg = o.region || [0, 0, 1, 1], cols = o.colors || ['#ffffff', '#3a2a3a'], al = o.alpha || [0.08, 0.3], sz = o.size || [0.5, 1.4];
  const n = Math.round((o.density ?? 0.06) * w * h * (reg[2] - reg[0]) * (reg[3] - reg[1])), clump = o.clump ?? 0.3;
  g.save(); if (o.blend) g.globalCompositeOperation = o.blend;
  let px = 0, py = 0;
  for (let i = 0; i < n; i++) {
    let x, y;
    if (i > 0 && r() < clump) { x = px + r.range(-2.5, 2.5); y = py + r.range(-2.5, 2.5); }
    else { x = (reg[0] + r() * (reg[2] - reg[0])) * w; y = (reg[1] + r() * (reg[3] - reg[1])) * h; }
    px = x; py = y;
    const s = r.range(sz[0], sz[1]);
    g.fillStyle = rgba(r.pick(cols), r.range(al[0], al[1]));
    for (const [ox, oy] of tileOffsets(o.tile, x, y, s, w, h)) { g.beginPath(); g.arc(x + ox, y + oy, s, 0, Math.PI * 2); g.fill(); }
  }
  g.restore();
  return P;
}

/** paper(P, { color='#fbf9f4', fiber=0.04, seed }) — paper base: tone, faint fibres, fine grain. */
export function paper(P, o = {}) {
  fill(P, o.color || '#fbf9f4');
  strokes(P, { seed: (o.seed ?? 5) + 1, count: Math.round(P.w * P.h / 900), colors: ['#d9d3e6', '#ffffff'], alpha: [0.03, 0.08], width: [0.6, 1.4], length: [6, 24], angle: 0, jitter: 90, curve: 0.5 });
  noise(P, { seed: o.seed ?? 5, amount: o.fiber ?? 0.04 });
  return P;
}

/**
 * painted({ w=512, h=512, base, gradient:{stops, angle}, blotches:{...}, strata:{...}, strokes:{...}, speckle:{...}, fbm:{...}, noise:{...}, blocks:[...], repeat, srgb,
 *            tile (default: true when repeat is given — fbm/blotches/strokes wrap so the repeat is seamless) })
 * One-call painted texture.  Steps run in this order: base fill, gradient, fbm, blotches, blocks, strata, strokes, speckle, noise.
 */
export function painted(o = {}) {
  const P = canvas(o.w || 512, o.h || o.w || 512);
  const tile = o.tile ?? !!o.repeat;               // repeated textures are painted seamlessly
  if (o.base) fill(P, o.base);
  if (o.gradient) gradient(P, o.gradient.stops, o.gradient);
  if (o.fbm) fbm(P, { tile, ...o.fbm });
  if (o.blotches) blotches(P, { tile, ...o.blotches });
  if (o.blocks) blocks(P, o.blocks, o.blocksOpts || {});
  if (o.strata) strata(P, { tile, ...o.strata });
  if (o.strokes) strokes(P, { tile, ...o.strokes });
  if (o.speckle) speckle(P, { tile, ...o.speckle });
  if (o.noise) noise(P, o.noise);
  const t = texture(P, { repeat: o.repeat, srgb: o.srgb, wrap: o.wrap });
  t.userData.canvas = P;
  return t;
}

/**
 * clouds({ seed, w=2048, h=1024, shape='streak'|'puff', count=10, band:[lo,hi] (elevation in degrees for an equirect skyDome
 *           texture; with planar:true it is the canvas y range 0..1), size:[min,max] (cloud length as a fraction of the width),
 *           aspect:[min,max] (length / thickness), body:'#f6d8c8', light:'#fff0e4', under:'#b9a6c6', underPos:0.55 (where the cool
 *           underside starts, 0 top .. 1 bottom), edge:1.2 (px blur of the crisp sunlit edge), alpha:[min,max], angle (deg tilt),
 *           veil:0.5 (soft cool haze under each streak), planar:false })
 * -> CanvasTexture (sRGB, RGBA, wrap repeat) for skyDome({clouds}) (equirect: u = azimuth, v = elevation).
 * Painted clouds: crisp warm sunlit bodies over cool violet undersides, sparse so the sky gradient shows between them.
 * 'streak' = long tapered brush-stroke clouds (f560 / f700 skies); 'puff' = small lobed cumulus.
 */
export function clouds(o = {}) {
  const r = rng(o.seed ?? 11), W = o.w || 2048, H = o.h || 1024;
  const P = canvas(W, H), g = P.g;
  const streak = (o.shape || 'streak') === 'streak';
  const band = o.band || [6, 26], sz = o.size || (streak ? [0.08, 0.2] : [0.05, 0.13]), asp = o.aspect || (streak ? [9, 16] : [3.5, 7]), pf = o.puffs || [4, 8];
  const al = o.alpha || [0.82, 0.97], edge = o.edge ?? 1.2, up = o.underPos ?? 0.55, veil = o.veil ?? 0.5;
  const cBody = cssColor(o.body || '#f6d8c8'), cLight = cssColor(o.light || '#fff0e4'), cUnder = cssColor(o.under || '#b9a6c6');
  const yOf = t => (o.planar ? t * H : (0.5 - t / 180) * H);   // degrees -> equirect canvas y (top = zenith)
  const n = o.count ?? 10;
  for (let i = 0; i < n; i++) {
    const L = r.range(sz[0], sz[1]) * W, Hc = L / r.range(asp[0], asp[1]);
    const cx = r() * W, cy = yOf(r.range(band[0], band[1]));
    const tilt = ((o.angle ?? 0) + r.range(-5, 5)) * Math.PI / 180;
    const M = canvas(Math.ceil(L * 1.3), Math.ceil(Hc * 4)), ox = M.w / 2, oy = M.h * 0.6;
    // shape parameters (drawn once per cloud so the veil and the body share the silhouette)
    const sh = { bow: r.range(-0.25, 0.25) * Hc, ph: r.range(0, 6.28), bumps: r.int(2, 5),
      lobes: Array.from({ length: r.int(pf[0], pf[1]) }, () => [r.range(0.85, 1.0), r.range(0.6, 1.1), r.range(1.0, 1.6), r.range(0.7, 0.95), r.range(-0.2, 0.2)]) };
    const shapePath = (cg, k, dy) => {
      cg.beginPath();
      if (streak) {   // tapered brush stroke: arched, bumpy sunlit top edge over a flatter underside
        const N = 48, top = [], bot = [];
        for (let j = 0; j <= N; j++) {
          const t = j / N, x = ox + (t - 0.5) * L * k, prof = Math.pow(Math.sin(Math.PI * Math.min(1, Math.max(0, t * 1.04 - 0.02))), 0.55);
          const mid = oy + dy + sh.bow * Math.sin(Math.PI * t);
          top.push([x, mid - Hc * k * prof * (0.75 + 0.25 * Math.sin(t * sh.bumps * 6.28 + sh.ph))]);
          bot.push([x, mid + Hc * k * prof * 0.3]);
        }
        top.forEach(([x, y], j) => (j ? cg.lineTo(x, y) : cg.moveTo(x, y)));
        for (let j = bot.length - 1; j >= 0; j--) cg.lineTo(bot[j][0], bot[j][1]);
        cg.closePath(); cg.fill();
      } else {         // lobed cumulus with a flat base
        sh.lobes.forEach(([a, b, c, d, e], j) => {
          const t = (j + 0.5) / sh.lobes.length - 0.5, x = ox + t * L * k * a, rad = Hc * k * (0.55 + 0.6 * (1 - Math.abs(t) * 1.6) * b);
          cg.beginPath(); cg.ellipse(x, oy + dy - rad * 0.35, rad * c, rad * d, e, 0, Math.PI * 2); cg.fill();
        });
        cg.fillRect(ox - L * k * 0.5, oy + dy - Hc * k * 0.25, L * k, Hc * k * 0.25);
      }
    };
    // 1. soft cool veil under the cloud (violet underside haze)
    if (veil > 0) { M.g.save(); M.g.filter = `blur(${Math.max(1, Hc * 0.35)}px)`; M.g.globalAlpha = veil; M.g.fillStyle = cUnder; shapePath(M.g, 1.08, Hc * 0.3); M.g.restore(); }
    // 2. the body: crisp silhouette filled with warm sunlit top -> body -> cool underside
    const B = canvas(M.w, M.h), bg = B.g;
    bg.fillStyle = '#fff'; shapePath(bg, 1, 0);
    bg.globalCompositeOperation = 'source-in';
    const gr = bg.createLinearGradient(0, oy - Hc * 1.05, 0, oy + Hc * 0.3);
    gr.addColorStop(0, cLight); gr.addColorStop(Math.max(0.05, up - 0.3), cBody); gr.addColorStop(up, cBody);
    gr.addColorStop(Math.min(0.97, up + 0.3), cUnder); gr.addColorStop(1, cUnder);
    bg.fillStyle = gr; bg.fillRect(0, 0, B.w, B.h); bg.globalCompositeOperation = 'source-over';
    M.g.save(); M.g.filter = edge > 0 ? `blur(${edge}px)` : 'none'; M.g.drawImage(B.c, 0, 0); M.g.restore();
    for (const [dx, dy] of tileOffsets(true, cx, cy, M.w, W, H)) {
      if (dy !== 0) continue;                                                                       // wrap in azimuth only
      g.save(); g.globalAlpha = r.range(al[0], al[1]); g.translate(cx + dx, cy); g.rotate(tilt); g.drawImage(M.c, -ox, -oy); g.restore();
    }
  }
  const t = texture(P, { wrap: 'repeat' });
  t.userData.canvas = P;
  return t;
}
