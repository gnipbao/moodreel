// kit/3dcv/look.js — ported from 3DCodeVerse (https://github.com/gaoypeng/3dcodeverse), awesome showcase
//   (https://huggingface.co/datasets/3dcodeverse/3dcodeverse-awesome-showcase): the 30-second film's code,
//   source src/core/look.js, round r02, git blob 353f5696c49e0076ad2502b4aa87590af36d2c7c.
// Licence: CC BY-NC-SA 4.0 (https://creativecommons.org/licenses/by-nc-sa/4.0/), see kit/3dcv/LICENSE.
//   Non-commercial use only; adaptations keep this licence. The rest of moodreel is MIT.
// Changes by moodreel (2026-11-08): three.js taken from ../three.js instead of the bare 'three' import; this header.

// look.js — the film's shading look (CORE_API.md §6).  Promoted 2026-11-01 from look variant V1 "illustrated ramp"
// (judge panel pick) with grafts from V2 and V3:
//   V1  analytic colour ramp shade -> mid -> lit mixed in a perceptual (gamma-2) space; terminator accent (rose-red skin
//       terminator, richer cloth); derived ramps keep saturation in shade (vertex-coloured terrain / city / canyon);
//       surface-anchored pixel-scale stipple specks; directional warm/cool aerial haze; sky `side` lobe; re-measured presets.
//   V3  STIPPLE-DITHERED RAMP: the tone is dithered BEFORE the ramp lookup, l' = l + n·A·w(l), so grain gathers at the
//       terminator, in shade and in cast-shadow penumbrae, and every speck is a real ramp colour (violet in peach) instead
//       of a grey offset.  n is V1's surface-anchored derivative-LOD lattice (stable under camera motion) with V3's clumped
//       kernel (centre + half of the +x/+y/+z neighbours, lag-1 ~0.3) and pow(|n|, sparsity) dot shape; a fraction `boil`
//       of it re-seeds every held drawing (post sets the seed).  Dithered sky elevation and haze mix (4h(1-h)).
//   V3+V2  airbrushed FORM SHADE: shade-side surfaces turning away from the camera roll off into shade × violet formTint
//       (round sleeves/trousers without outlines; per-material `form`, low on cloth/skin presets).
//   V2  sky-coupled haze (hazeTop / hazeTopAmount by view elevation + warm hazeSun lobe), 24-tap Vogel PCF for big soft
//       radii and env shadowSoftMul.
// Owner: look panel (look promotion stage).  Hook authors: avoid the `uLk*` / `lk*` prefixes (internal names).
import { THREE } from '../three.js';
export const VARIANT = 'promoted';
export const VERSION = 'look-r1 (V1 + V2/V3 grafts)';

const C = v => (v == null ? null : v.isColor ? v.clone() : Array.isArray(v) ? new THREE.Color(v[0], v[1], v[2]) : new THREE.Color(v));
const V3 = v => (v.isVector3 ? v.clone() : new THREE.Vector3(v[0], v[1], v[2]));

// ------------------------------------------------------------------------------------------------ shared env
/**
 * Scene-wide uniforms shared by every LookMaterial (same uniform objects).  Change per frame with setEnv({...}).
 * Colours are linear (THREE.Color handles sRGB hex conversion).  post.js writes pxScale and the dither* values every draw.
 */
export const env = {
  uLitTint: { value: C(0xfff0de) },      // derived-ramp lit multiplier (warm cream/peach)
  uMidTint: { value: C(0xe2c4c4) },      // derived-ramp mid multiplier
  uShadeTint: { value: C(0x8f80b4) },    // derived-ramp shade multiplier (cool mauve/violet)
  uShadeSat: { value: 0.35 },            // derived-ramp: extra saturation kept in the shade (0 = plain multiply)
  uShadowTint: { value: C(0xe2d6ea) },   // extra multiplier inside received (cast) shadows, all materials
  uShadowMul: { value: 1.0 },            // global cast-shadow strength multiplier
  uShadowSoftMul: { value: 1.0 },        // global PCF radius multiplier (V2; >1 = bigger, softer cast shadows)
  uBounceColor: { value: C(0xffb48a) },  // warm fill from below (floor bounce) on the shade side
  uBounceMul: { value: 1.0 },
  uRimTint: { value: C(0xffffff) },      // global multiplier of every material's rim colour
  uRimMul: { value: 1.0 },
  uKeyDirWorld: { value: new THREE.Vector3(-0.4, 0.8, 0.45).normalize() }, // used only when the scene has no DirectionalLight
  uHazeColor: { value: C(0xe9c8b8) },    // haze colour at the horizon looking TOWARD the key light (or everywhere)
  uHazeAway: { value: C(0xe9c8b8) },     // haze colour looking AWAY from the key light (V1 warm/cool split)
  uHazeDirAmt: { value: 0.0 },           // 0 = uniform haze colour; 1 = full warm/cool split (set automatically by hazeAway)
  uHazeSunPow: { value: 1.5 },           // falloff of the warm (sunward) haze lobe of the split
  uHazeSunDir: { value: new THREE.Vector3(0, 0, 0) },   // world direction of the warm lobe; (0,0,0) = the key light
  uHazeTop: { value: C(0xe9c8b8) },      // V2 sky-coupled haze: colour looking UP (zenith) ...
  uHazeTopAmount: { value: 0.0 },        // ... blended in by view elevation (0 = off)
  uHazeSunColor: { value: C(0xffd2a8) }, // V2 additive warm glow in the haze toward hazeSunDir (or the key) ...
  uHazeSunAmount: { value: 0.0 },        // ... strength (0 = off)
  uHazeDither: { value: 1.0 },           // V3 grainy haze: dither of the haze mix factor (x dither amount, 4h(1-h))
  uHazeDensity: { value: 0.0 },          // 1/m;  0 disables haze
  uHazeStart: { value: 0.0 },            // m from camera before haze starts
  uHazeBase: { value: 0.0 },             // world height where haze is full
  uHazeFalloff: { value: 0.0 },          // 1/m exponential falloff above uHazeBase (0 = uniform)
  uHazeMax: { value: 1.0 },
  uGrainMul: { value: 1.0 },             // global multiplier of per-material mottling grain
  uStippleMul: { value: 1.0 },           // global multiplier of per-material stipple specks
  uTermMul: { value: 1.0 },              // global multiplier of the terminator accent
  uRampGamma: { value: 2.0 },            // perceptual space the ramp is mixed in (1 = linear, as the foundation look)
  uFormMul: { value: 1.0 },              // global multiplier of the per-material form shade
  uFormTint: { value: C(0x8a7aa8) },     // multiplier of the shade colour at the deepest form roll-off (violet)
  // ---- stipple-dithered ramp (post.js writes these from params.dither every draw) ----
  uDitherAmt: { value: 0.12 },           // dither amplitude in ramp units (0 = smooth ramps)
  uDitherShade: { value: 0.75 },         // weight in the shade ((1-l)^2)
  uDitherMid: { value: 1.0 },            // weight across the terminator (4 l (1-l))
  uDitherLit: { value: 0.12 },           // weight in full light (l^2)
  uDitherSparse: { value: 1.35 },        // >1 = sparser, dot-like specks
  uDitherScale: { value: 1.0 },          // speck cell size in output pixels
  uDitherBoil: { value: 0.5 },           // fraction of the dither variance re-seeded every held drawing (0 = fixed on the surface)
  uDitherSeed: { value: 0.0 },           // boil seed (post: one per held drawing)
  uPxScale: { value: 2.0 },              // internal pixels per output pixel (set by post.js every draw)
  // post lens (set by post.js every draw): in-shader grain cells are scaled by the lens' local magnification so specks stay
  // ~one output pixel after the fisheye / barrel warp (the fisheye magnifies the frame centre ~2x)
  uLensFish: { value: 0.0 }, uLensTheta: { value: 1.0 }, uLensZoom: { value: 1.0 }, uLensBarrel: { value: 0.0 },
  uLensCenter: { value: new THREE.Vector2(0.5, 0.5) }, uLensAspect: { value: 16 / 9 }, uLensRes: { value: new THREE.Vector2(1280, 720) },
  // WIDE lens (post renders cube faces): output px per unit radius, face px per unit tan, main optical axis in face view space
  uLensThOut: { value: 1.0 },              // output half diagonal angle (lens.angle; = uLensTheta unless narrower / wide)
  uLensWide: { value: 0.0 }, uWideK: { value: 367.0 }, uWideFace: { value: 480.0 }, uWideAxis: { value: new THREE.Vector3(0, 0, -1) },
  uGlobalTint: { value: C(0xffffff) },   // multiplies every LookMaterial result (mood / dark stage)
  uFrame: { value: 1.0 },
};
const ENV_KEYS = {
  litTint: 'uLitTint', midTint: 'uMidTint', shadeTint: 'uShadeTint', shadeSat: 'uShadeSat', shadowTint: 'uShadowTint', shadowMul: 'uShadowMul',
  shadowSoftMul: 'uShadowSoftMul', bounceColor: 'uBounceColor', bounceMul: 'uBounceMul', rimTint: 'uRimTint', rimMul: 'uRimMul', keyDir: 'uKeyDirWorld',
  hazeColor: 'uHazeColor', hazeAway: 'uHazeAway', hazeDirAmt: 'uHazeDirAmt', hazeSunPow: 'uHazeSunPow', hazeSunDir: 'uHazeSunDir',
  hazeTop: 'uHazeTop', hazeTopAmount: 'uHazeTopAmount', hazeSunColor: 'uHazeSunColor', hazeSunAmount: 'uHazeSunAmount', hazeDither: 'uHazeDither',
  hazeDensity: 'uHazeDensity', hazeStart: 'uHazeStart', hazeBase: 'uHazeBase', hazeFalloff: 'uHazeFalloff', hazeMax: 'uHazeMax', grainMul: 'uGrainMul',
  stippleMul: 'uStippleMul', termMul: 'uTermMul', rampGamma: 'uRampGamma', formMul: 'uFormMul', formTint: 'uFormTint',
  ditherAmount: 'uDitherAmt', ditherShade: 'uDitherShade', ditherMid: 'uDitherMid', ditherLit: 'uDitherLit', ditherSparsity: 'uDitherSparse',
  ditherScale: 'uDitherScale', ditherBoil: 'uDitherBoil', ditherSeed: 'uDitherSeed',
  pxScale: 'uPxScale', globalTint: 'uGlobalTint',
  lensFish: 'uLensFish', lensTheta: 'uLensTheta', lensZoom: 'uLensZoom', lensBarrel: 'uLensBarrel', lensCenter: 'uLensCenter', lensAspect: 'uLensAspect', lensRes: 'uLensRes',
  lensThOut: 'uLensThOut', lensWide: 'uLensWide', wideK: 'uWideK', wideFace: 'uWideFace', wideAxis: 'uWideAxis',
};
// keys owned by post.js (written every draw) — resetEnv() leaves them alone
const POST_KEYS = new Set(['pxScale', 'lensFish', 'lensTheta', 'lensZoom', 'lensBarrel', 'lensCenter', 'lensAspect', 'lensRes', 'lensThOut', 'lensWide', 'wideK', 'wideFace', 'wideAxis', 'ditherAmount', 'ditherShade', 'ditherMid', 'ditherLit', 'ditherSparsity', 'ditherScale', 'ditherBoil', 'ditherSeed']);
export const ENV_DEFAULTS = Object.fromEntries(Object.entries(ENV_KEYS).map(([k, u]) => [k, env[u].value.clone ? env[u].value.clone() : env[u].value]));
/**
 * setEnv({litTint, shadeTint, hazeColor:'#e9c8b8', hazeAway:'#b9b4cc', hazeTop:'#8f8aa8', hazeTopAmount:0.5, hazeDensity:0.02, ...})
 * — partial update of the shared env.  Giving hazeColor without hazeAway makes the haze uniform (foundation behaviour);
 * giving hazeAway enables the warm/cool split; hazeTop + hazeTopAmount couple it to the sky's elevation gradient.
 */
export function setEnv(o = {}) {
  for (const [k, v] of Object.entries(o)) {
    const u = ENV_KEYS[k]; if (!u) { console.warn('look.setEnv: unknown key', k); continue; }
    if (k === 'hazeSunDir') { const d = V3(v); env.uHazeSunDir.value.copy(d.lengthSq() > 0 ? d.normalize() : d); continue; }
    const cur = env[u].value;
    if (cur.isColor) cur.copy(C(v)); else if (cur.isVector3) cur.copy(V3(v)).normalize(); else if (cur.isVector2) cur.set(v[0] ?? v.x, v[1] ?? v.y); else env[u].value = v;
  }
  if ('hazeColor' in o && !('hazeAway' in o)) { env.uHazeAway.value.copy(env.uHazeColor.value); if (!('hazeDirAmt' in o)) env.uHazeDirAmt.value = 0; }
  if ('hazeAway' in o && !('hazeDirAmt' in o)) env.uHazeDirAmt.value = 1;
}
/** Restore every env value to its default (call at the start of a shot's init / render if it changes the env). Post-owned keys are kept. */
export function resetEnv() {
  setEnv(Object.fromEntries(Object.entries(ENV_DEFAULTS).filter(([k]) => !POST_KEYS.has(k)).map(([k, v]) => [k, v.clone ? v.clone() : v])));
}
export function setFrame(n) { env.uFrame.value = n; }

// ------------------------------------------------------------------------------------------------ GLSL
// Lens family shared with post.js (r02).  r = output radius (1 = frame corner, after zoom), th = half diagonal angle (rad),
// f = fisheye 0..2: 0 rectilinear, 1 equidistant, 2 equisolid (more edge compression = stronger bowl).  f <= 1 is the
// look-r1 formula (rectilinear radius blend), so old shots render identically.  th >= 1.5 (wide renderer) needs f >= 1.
export const LENS_GLSL = /* glsl */`
float lkFishTheta(float r, float th, float f) {      // output radius -> view angle from the optical axis
  if (f <= 1.0 && th < 1.5) { float T = tan(th); return atan(mix(r, tan(min(r * th, 1.55)) / T, f) * T); }
  float e = r * th;
  return f <= 1.0 ? e : mix(e, 2.0 * asin(clamp(r * sin(th * 0.5), 0.0, 1.0)), clamp(f - 1.0, 0.0, 1.0));
}
float lkFishRs(float r, float th, float f) {         // rectilinear-render radius (1 = corner) seen at output radius r
  if (f <= 1.0) return mix(r, tan(min(r * th, 1.55)) / tan(th), f);
  return tan(min(lkFishTheta(r, th, f), 1.55)) / tan(th);
}
`;
// Shared noise (LookMaterial + skyDome): surface-anchored clumped lattice noise whose cell stays ~one output pixel.
const NOISE_GLSL = /* glsl */`
uniform float uLensFish; uniform float uLensTheta; uniform float uLensZoom; uniform float uLensBarrel; uniform vec2 uLensCenter; uniform float uLensAspect; uniform vec2 uLensRes;
uniform float uLensWide; uniform float uWideK; uniform float uWideFace; uniform vec3 uWideAxis; uniform float uLensThOut;
${LENS_GLSL}
float lkLensWarp(float r) {   // = post.js LENS_FS warp(): output radius -> scene radius (1 = frame corner)
  float rs = r / uLensZoom;
  if (abs(uLensThOut - uLensTheta) > 1e-5) rs = tan(min(lkFishTheta(rs, uLensThOut, uLensFish), 1.55)) / tan(uLensTheta);
  else if (uLensFish > 0.0) rs = lkFishRs(rs, uLensTheta, uLensFish);
  return rs * (1.0 + uLensBarrel * r * r) / (1.0 + uLensBarrel);
}
float lkLensD(float r) { float a = max(r - 1e-3, 0.0), b = r + 1e-3; return (lkLensWarp(b) - lkLensWarp(a)) / (b - a); }
// scene pixels per output pixel at this fragment after the post lens (<1 where the lens magnifies, e.g. the fisheye centre)
float lkLensScale() {
  if (uLensFish <= 0.0 && uLensBarrel == 0.0 && uLensZoom == 1.0 && abs(uLensThOut - uLensTheta) < 1e-5) return 1.0;
  vec2 p = (gl_FragCoord.xy / uLensRes - uLensCenter) * vec2(uLensAspect, 1.0);
  float rT = length(p) / (length(vec2(uLensAspect, 1.0)) * 0.5);
  float r = rT;
  for (int i = 0; i < 4; i++) r = max(r - (lkLensWarp(r) - rT) / max(lkLensD(r), 1e-3), 0.0);
  float rad = lkLensD(r), tng = r > 1e-3 ? lkLensWarp(r) / r : rad;
  return clamp(sqrt(max(rad * tng, 0.0)), 0.2, 5.0);
}
// internal (rendered) pixels per OUTPUT pixel at a view-space point vp (camera at the origin looking down -Z).
// Normal renders: supersampling x lens magnification.  WIDE lens (post renders cube faces): face pixels per radian at this
// fragment (N/2 / cos^1.5) over output pixels per radian of the fisheye at its angle from the main optical axis.
float lkPxPerOut(vec3 vp, float pxScale) {
  if (uLensWide < 0.5) return pxScale * lkLensScale();
  vec3 d = normalize(vp);
  float face = uWideFace / pow(max(-d.z, 0.05), 1.5);
  float th = acos(clamp(dot(d, uWideAxis), -1.0, 1.0));
  float r = th / max(uLensThOut, 1e-3);
  for (int i = 0; i < 4; i++) {
    float t0 = lkFishTheta(max(r - 1e-3, 0.0), uLensThOut, uLensFish), t1 = lkFishTheta(r + 1e-3, uLensThOut, uLensFish);
    r = max(r - (lkFishTheta(r, uLensThOut, uLensFish) - th) / max((t1 - t0) / (r + 1e-3 - max(r - 1e-3, 0.0)), 1e-3), 0.0);
  }
  float t0 = lkFishTheta(max(r - 1e-3, 0.0), uLensThOut, uLensFish), t1 = lkFishTheta(r + 1e-3, uLensThOut, uLensFish);
  float outRad = uWideK * (r + 1e-3 - max(r - 1e-3, 0.0)) / max(t1 - t0, 1e-5);
  float outTan = th > 1e-3 ? uWideK * r / sin(th) : outRad;
  return clamp(face / sqrt(max(outRad * outTan, 1e-6)), 0.25, 8.0);
}
float lkHashI(vec3 p) { // well-mixed hash for integer lattice cells
  uvec3 q = uvec3(ivec3(p) + ivec3(32768));
  q = q * uvec3(1597334673u, 3812015801u, 2798796415u);
  uint n = (q.x ^ q.y ^ q.z) * 1597334673u; n ^= n >> 16u; n *= 2246822519u; n ^= n >> 13u;
  return float(n) * (1.0 / 4294967296.0);
}
// clumped cell value (V3 kernel in 3-D): centre + half of the +x/+y/+z neighbours -> lag-1 correlation ~0.29 like the
// reference grain clumps; scaled to V3's 2-D kernel range (sigma ~0.354, |n| <~ 1)
float lkClumpH(vec3 c) {
  return (lkHashI(c) - 0.5 + 0.5 * (lkHashI(c + vec3(1.0, 0.0, 0.0)) + lkHashI(c + vec3(0.0, 1.0, 0.0)) + lkHashI(c + vec3(0.0, 0.0, 1.0)) - 1.5)) * 0.926;
}
// surface-anchored noise: 3-D lattice on the surface coordinate sp; the cell is ~scale output pixels at any distance
// (derivative LOD); the two nearest power-of-two lattices are blended variance-preserving.  seed shifts the lattice.
float lkSurfNoise(vec3 sp, float scale, float pxScale, float seed) {
  float fp = max(max(length(dFdx(sp)), length(dFdy(sp))), 1e-7) * pxScale * scale;
  float lv = log2(fp); float fl = floor(lv); float t = lv - fl; float c0 = exp2(fl);
  vec3 so = vec3(floor(seed) * 131.0, floor(seed) * 71.0 + 11.0, floor(seed) * 29.0 + 5.0);
  float h0 = lkClumpH(floor(sp / c0) + so);
  float h1 = lkClumpH(floor(sp / (c0 * 2.0)) + so + vec3(101.0, 37.0, 59.0));
  return (h0 * (1.0 - t) + h1 * t) / sqrt((1.0 - t) * (1.0 - t) + t * t);
}
// dither noise: a fixed part anchored on the surface + a fraction 'boil' re-seeded per drawing; dot-shaped by 'sparse'
float lkDitherNoise(vec3 sp, float scale, float pxScale, float boil, float seed, float sparse) {
  float n = lkSurfNoise(sp, scale, pxScale, 0.0);
  if (boil > 0.0) n = n * sqrt(1.0 - boil) + lkSurfNoise(sp, scale, pxScale, seed + 1.0) * sqrt(boil);
  return sign(n) * pow(abs(n), sparse);
}
`;

const PARS = /* glsl */`
varying vec3 vLookWorldPos;
varying vec3 vLookObjPos;
varying vec2 vLookUv;
uniform vec3 uLit; uniform vec3 uMid; uniform vec3 uShade; uniform float uExplicit;
uniform float uWrap; uniform float uTerm; uniform float uSoft; uniform float uMidPos;
uniform float uLkBands; uniform float uLkBandSoft; uniform float uFacet;
uniform float uShadowStrength; uniform float uShadowSoft;
uniform vec3 uRimColor; uniform float uRim; uniform float uRimPower; uniform float uRimLit;
uniform float uBounce; uniform float uPointGain;
uniform float uGrain; uniform float uGrainScale; uniform float uHazeMul;
uniform float uIrid; uniform float uFresAlpha; uniform float uFresAlphaPow; uniform float uUnlit;
uniform vec3 uGradAxis; uniform vec2 uGradRange; uniform vec3 uGradColor; uniform float uGradAmount;
uniform float uGroundAO; uniform float uGroundAOHeight;
uniform float uTermSat; uniform vec3 uTermColor; uniform float uTermTint; uniform float uTermWidth;
uniform float uStipple; uniform float uStippleDark; uniform float uStippleScale; uniform float uShadeSatMat;
uniform float uForm; uniform float uFormPow; uniform float uFormLit; uniform float uDither; uniform float uChroma;
uniform float uSpec; uniform vec3 uSpecColor; uniform float uSpecSize; uniform float uSpecSoft;
uniform float uRefl; uniform vec3 uReflTop; uniform vec3 uReflHor; uniform vec3 uReflBot; uniform float uReflBase; uniform float uReflSharp; uniform float uReflBlend;
uniform vec3 uLitTint; uniform vec3 uMidTint; uniform vec3 uShadeTint; uniform float uShadeSat; uniform vec3 uShadowTint; uniform float uShadowMul; uniform float uShadowSoftMul;
uniform vec3 uBounceColor; uniform float uBounceMul; uniform vec3 uRimTint; uniform float uRimMul; uniform vec3 uKeyDirWorld;
uniform vec3 uHazeColor; uniform vec3 uHazeAway; uniform float uHazeDirAmt; uniform float uHazeSunPow; uniform vec3 uHazeSunDir;
uniform vec3 uHazeTop; uniform float uHazeTopAmount; uniform vec3 uHazeSunColor; uniform float uHazeSunAmount; uniform float uHazeDither;
uniform float uHazeDensity; uniform float uHazeStart; uniform float uHazeBase; uniform float uHazeFalloff; uniform float uHazeMax;
uniform float uGrainMul; uniform float uStippleMul; uniform float uTermMul; uniform float uRampGamma; uniform float uPxScale;
uniform float uFormMul; uniform vec3 uFormTint;
uniform float uDitherAmt; uniform float uDitherShade; uniform float uDitherMid; uniform float uDitherLit; uniform float uDitherSparse;
uniform float uDitherScale; uniform float uDitherBoil; uniform float uDitherSeed;
uniform vec3 uGlobalTint; uniform float uFrame;
${NOISE_GLSL}
float lkHash3(vec3 p) { p = fract(p * 0.3183099 + vec3(0.71, 0.113, 0.419)); p *= 17.0; return fract(p.x * p.y * p.z * (p.x + p.y + p.z)); }
float lkNoise3(vec3 x) {
  vec3 i = floor(x); vec3 f = fract(x); f = f * f * (3.0 - 2.0 * f);
  return mix(mix(mix(lkHash3(i), lkHash3(i + vec3(1,0,0)), f.x), mix(lkHash3(i + vec3(0,1,0)), lkHash3(i + vec3(1,1,0)), f.x), f.y),
             mix(mix(lkHash3(i + vec3(0,0,1)), lkHash3(i + vec3(1,0,1)), f.x), mix(lkHash3(i + vec3(0,1,1)), lkHash3(i + vec3(1,1,1)), f.x), f.y), f.z);
}
float lkIGN(vec2 p) { return fract(52.9829189 * fract(dot(p, vec2(0.06711056, 0.00583715)))); }
vec2 lkVogel(int i, int n, float phi) { float r = sqrt((float(i) + 0.5) / float(n)); float th = float(i) * 2.399963229728653 + phi; return vec2(cos(th), sin(th)) * r; }
vec3 lkHue(float h) { return clamp(abs(fract(h + vec3(0.0, 2.0/3.0, 1.0/3.0)) * 6.0 - 3.0) - 1.0, 0.0, 1.0); }
float lkLum(vec3 c) { return dot(c, vec3(0.2126, 0.7152, 0.0722)); }
vec3 lkSat(vec3 c, float s) { float l = lkLum(c); return max(mix(vec3(l), c, s), 0.0); }
vec3 lkToP(vec3 c) { return pow(max(c, 0.0), vec3(1.0 / uRampGamma)); }
vec3 lkFromP(vec3 c) { return pow(max(c, 0.0), vec3(uRampGamma)); }
// V1 surface stipple cell value (uniform, sub-output-pixel cells): fine sand + sparse dark specks
float lkStippleH(vec3 sp, float seed, float pxs) {
  float fp = max(max(length(dFdx(sp)), length(dFdy(sp))), 1e-7) * pxs * uStippleScale * 0.7;
  float lv = log2(fp); float fl = floor(lv); float t = lv - fl; float c0 = exp2(fl);
  float h0 = lkHashI(floor(sp / c0) + vec3(seed, 0.0, 0.0)) - 0.5;
  float h1 = lkHashI(floor(sp / (c0 * 2.0)) + vec3(0.0, seed + 7.0, 0.0)) - 0.5;
  return 0.5 + (h0 * (1.0 - t) + h1 * t) / sqrt((1.0 - t) * (1.0 - t) + t * t);
}
#if defined( USE_SHADOWMAP ) && NUM_DIR_LIGHT_SHADOWS > 0 && defined( SHADOWMAP_TYPE_PCF )
// soft PCF: Vogel disc, 16 taps for small radii, 24 for big soft shadows (V2) — rotated per pixel (IGN)
float lookSoftShadow(sampler2DShadow sm, vec2 size, float intensity, float bias, float radius, vec4 coord) {
  coord.xyz /= coord.w; coord.z += bias;
  if (coord.x < 0.0 || coord.x > 1.0 || coord.y < 0.0 || coord.y > 1.0 || coord.z > 1.0) return 1.0;
  float r = radius / size.x;
  float phi = lkIGN(gl_FragCoord.xy) * 6.2831853;
  float s = 0.0;
  if (radius > 3.0) { for (int i = 0; i < 24; i++) s += texture(sm, vec3(coord.xy + lkVogel(i, 24, phi) * r, coord.z)); s /= 24.0; }
  else { for (int i = 0; i < 16; i++) s += texture(sm, vec3(coord.xy + lkVogel(i, 16, phi) * r, coord.z)); s /= 16.0; }
  return mix(1.0, s, intensity);
}
#endif
`;

const LIGHTING = /* glsl */`
// ===== look-r1 illustrated-ramp lighting (replaces three's light accumulation) =====
vec3 lkAlbedo = diffuseColor.rgb;
vec3 lkN = normalize(normal);
vec3 lkFlat = normalize(cross(dFdx(vViewPosition), dFdy(vViewPosition)));
if (uFacet > 0.0) lkN = normalize(mix(lkN, lkFlat, uFacet));
vec3 lkV = normalize(vViewPosition);
vec3 lkWN = inverseTransformDirection(lkN, viewMatrix);
vec3 lkWP = vLookWorldPos;
vec3 lkL = normalize((viewMatrix * vec4(uKeyDirWorld, 0.0)).xyz);
vec3 lkKeyCol = vec3(1.0);
float lkShadow = 1.0;
#if NUM_DIR_LIGHTS > 0
  lkL = directionalLights[0].direction;
  lkKeyCol = directionalLights[0].color;
  #if defined( USE_SHADOWMAP ) && NUM_DIR_LIGHT_SHADOWS > 0
    if (receiveShadow) {
    #if defined( SHADOWMAP_TYPE_PCF )
      lkShadow = lookSoftShadow(directionalShadowMap[0], directionalLightShadows[0].shadowMapSize, directionalLightShadows[0].shadowIntensity,
                                directionalLightShadows[0].shadowBias, directionalLightShadows[0].shadowRadius * uShadowSoft * uShadowSoftMul, vDirectionalShadowCoord[0]);
    #else
      lkShadow = getShadow(directionalShadowMap[0], directionalLightShadows[0].shadowMapSize, directionalLightShadows[0].shadowIntensity,
                           directionalLightShadows[0].shadowBias, directionalLightShadows[0].shadowRadius, vDirectionalShadowCoord[0]);
    #endif
    }
  #endif
#endif
float lkNdl = dot(lkN, lkL);
float lkNdV = clamp(dot(lkN, lkV), 0.0, 1.0);
float lkW = (lkNdl + uWrap) / (1.0 + uWrap);
float lkl = smoothstep(uTerm - uSoft, uTerm + uSoft, lkW);
if (uLkBands > 0.5) { float b = lkl * uLkBands; float fb = floor(b); lkl = clamp((fb + smoothstep(0.5 - uLkBandSoft, 0.5 + uLkBandSoft, fract(b))) / uLkBands, 0.0, 1.0); }
float lkSh = mix(1.0, lkShadow, clamp(uShadowStrength * uShadowMul, 0.0, 1.0));
float lkLit0 = lkl * lkSh;                       // continuous tone
float lkPxS = lkPxPerOut(-vViewPosition, uPxScale);   // internal px per final output px at this fragment (lens-aware, wide-aware)
// stipple-dithered tone (V3 on V1's surface lattice): grain density follows tone, each speck is a ramp colour
float lkDA = uDitherAmt * uDither * (1.0 - uUnlit);
float lkDither = 0.0;
float lkLit = lkLit0;
if (lkDA > 0.0) {
  lkDither = lkDitherNoise(vLookObjPos, uDitherScale, lkPxS, uDitherBoil, uDitherSeed, uDitherSparse);
  float sw = uDitherMid * 4.0 * lkLit0 * (1.0 - lkLit0) + uDitherShade * (1.0 - lkLit0) * (1.0 - lkLit0) + uDitherLit * lkLit0 * lkLit0;
  lkLit = clamp(lkLit0 + lkDither * lkDA * sw, 0.0, 1.0);
}
// ramp colours: explicit (hand-tuned per material) or derived from the albedo with the env tints
vec3 lkShadeAlb = lkSat(lkAlbedo, 1.0 + uShadeSat * uShadeSatMat);
vec3 lkCS = mix(lkShadeAlb * uShadeTint, lkAlbedo * uShade, uExplicit);
vec3 lkCM = lkAlbedo * mix(uMidTint, uMid, uExplicit);
vec3 lkBase = lkAlbedo * mix(vec3(1.0), uMid, uExplicit);   // reflectance used by additive light (bounce, point lights)
vec3 lkCL = lkAlbedo * mix(uLitTint, uLit, uExplicit) * lkKeyCol;
lkCM = mix(lkCM, lkCM * lkKeyCol, 0.5);
// perceptual-space ramp (gamma uRampGamma): painted mid-tones, not a linear wash toward the lit colour
vec3 lkPS = lkToP(lkCS), lkPM = lkToP(lkCM), lkPL = lkToP(lkCL);
vec3 lookColor = lkFromP(lkLit < uMidPos ? mix(lkPS, lkPM, lkLit / max(uMidPos, 1e-3)) : mix(lkPM, lkPL, (lkLit - uMidPos) / max(1.0 - uMidPos, 1e-3)));
// terminator accent: saturated (optionally tinted) band where light turns to shade — on forms and on cast-shadow edges
{
  float tb = 1.0 - smoothstep(0.0, max(uTermWidth, 1e-3), abs(lkLit - uMidPos * 0.9));
  float ta = tb * tb * uTermMul;
  vec3 acc = lkSat(lookColor, 1.0 + uTermSat) * mix(vec3(1.0), uTermColor, uTermTint);
  lookColor = mix(lookColor, acc, ta);
}
// tinted received shadow: cast shadow regions go cooler than self-shade
lookColor *= mix(vec3(1.0), uShadowTint, (1.0 - lkSh) * lkl);
// colour gradient along an object-space axis (painted fades, darker hems ...)
if (uGradAmount > 0.0) { float g = clamp((dot(vLookObjPos, uGradAxis) - uGradRange.x) / max(uGradRange.y - uGradRange.x, 1e-4), 0.0, 1.0); lookColor *= mix(vec3(1.0), uGradColor, uGradAmount * (1.0 - g)); }
// soft contact darkening near the ground plane (world y)
if (uGroundAO > 0.0) { float a = 1.0 - smoothstep(0.0, uGroundAOHeight, lkWP.y); lookColor *= mix(vec3(1.0), uShadowTint * uShadeTint, uGroundAO * a * a); }
// airbrushed form shade (V3/V2): shade-side surfaces turning away from the camera roll off into a deeper violet shade
if (uForm * uFormMul > 0.0 && uUnlit < 0.5) {
  float fe = pow(1.0 - lkNdV, uFormPow);
  float fm = fe * mix(1.0, 1.0 - smoothstep(0.15, 0.85, lkLit0), uFormLit);
  fm = clamp(fm * uForm * uFormMul + lkDither * 0.5 * lkDA * fm, 0.0, 1.0);
  lookColor = mix(lookColor, lkCS * uFormTint, fm);
}
// warm bounce from below on the shade side
lookColor += lkBase * uBounceColor * uBounce * uBounceMul * pow(clamp(-lkWN.y * 0.5 + 0.5, 0.0, 1.0), 2.0) * (1.0 - lkLit) * 0.35;
// coloured point-light glow (paper, nib, lily, portal) — no ramp, wrapped
#if NUM_POINT_LIGHTS > 0
  for (int i = 0; i < NUM_POINT_LIGHTS; i++) {
    vec3 lv = pointLights[i].position + vViewPosition;
    float d = length(lv);
    float att = getDistanceAttenuation(d, pointLights[i].distance, pointLights[i].decay);
    float nl = clamp((dot(lkN, lv / max(d, 1e-4)) + 0.4) / 1.4, 0.0, 1.0);
    lookColor += lkBase * pointLights[i].color * att * nl * uPointGain;
  }
#endif
// rim
float lkFr = pow(1.0 - lkNdV, uRimPower);
float lkRimMask = mix(1.0, smoothstep(-0.15, 0.55, lkNdl) * mix(1.0, lkSh, 0.7), uRimLit);
lookColor += uRimColor * uRimTint * uRim * uRimMul * lkFr * lkRimMask;
// painted specular (r02): a soft-edged highlight SHAPE (smoothstepped Blinn lobe), lit side only, follows the key + its shadow
if (uSpec > 0.0) {
  float nh = max(dot(lkN, normalize(lkL + lkV)), 0.0);
  float sp = pow(nh, exp2(mix(9.0, 2.5, clamp(uSpecSize, 0.0, 1.0))));
  sp = smoothstep(0.5 - uSpecSoft * 0.5, 0.5 + uSpecSoft * 0.5 + 1e-3, sp + lkDither * 0.12 * lkDA);
  lookColor += uSpecColor * lkKeyCol * uSpec * sp * lkSh;
}
// stylised environment reflection (r02): ground / horizon band / sky picked by the reflected ray's world elevation, with a
// grainy painted horizon edge; fresnel-weighted (glossy bronze domes, glass facades, chrome) — no environment map needed
if (uRefl > 0.0) {
  vec3 lkR = inverseTransformDirection(reflect(-lkV, lkN), viewMatrix);
  float re = lkR.y + lkDither * 0.05 * uDither * step(1e-6, lkDA);   // grainy painted horizon edge
  float hw = 0.5 / max(uReflSharp, 0.1);
  vec3 env = re < 0.0 ? mix(uReflHor, uReflBot, smoothstep(0.0, hw, -re)) : mix(uReflHor, uReflTop, smoothstep(0.0, hw * 1.6, re));
  float fr = clamp(uReflBase + (1.0 - uReflBase) * pow(1.0 - lkNdV, 4.0), 0.0, 1.0) * uRefl;
  lookColor = mix(lookColor, uReflBlend > 0.5 ? lookColor * env * 2.0 : env, fr);
}
// iridescent sheen (glass, paper)
if (uIrid > 0.0) { vec3 h = lkHue(lkFr * 1.6 + dot(lkWN, vec3(0.35, 0.55, 0.25)) * 0.9 + 0.1 * sin(dot(lkWP, vec3(3.1, 1.7, 2.3)))); lookColor += uIrid * mix(vec3(1.0), h, 0.75) * (0.25 + lkFr); }
if (uUnlit > 0.5) lookColor = lkAlbedo;
lookColor += totalEmissiveRadiance;
// per-surface mottling grain (object space, fades out when cells get smaller than a pixel)
if (uGrain > 0.0) {
  vec3 gp = vLookObjPos * uGrainScale;
  float fw = length(fwidth(gp));
  float gn = (lkNoise3(gp) + lkNoise3(gp * 2.17 + 13.1) * 0.6) / 1.6 - 0.5;
  float lum = dot(lookColor, vec3(0.299, 0.587, 0.114));
  lookColor *= 1.0 + gn * uGrain * uGrainMul * (1.15 - 0.6 * clamp(lum, 0.0, 1.0)) * clamp(1.4 - fw, 0.0, 1.0);
}
// surface-anchored tone-driven stipple specks (V1): pixel-scale, fixed to the surface, denser in shade / dark tones
if (uStipple > 0.0 && uStippleMul > 0.0) {
  float hs = lkStippleH(vLookObjPos, 0.0, lkPxS);
  float hd = lkStippleH(vLookObjPos * 1.0007 + 3.17, 53.0, lkPxS);
  float dark = 1.0 - sqrt(clamp(lkLum(lookColor), 0.0, 1.0));            // ~ 1 - display luma
  float tone = clamp(0.3 + 0.7 * max(1.0 - lkLit0, dark), 0.0, 1.0);
  float sym = (hs - 0.5) * 0.3 * (0.6 + 0.4 * tone);                      // fine symmetric mottle
  float dens = uStippleDark * (0.06 + 0.2 * tone);                        // 6..26 % of cells carry a dark speck
  float speck = step(1.0 - dens, hd) * 0.12 * (0.5 + 0.5 * tone);
  float k = uStipple * uStippleMul;
  lookColor *= max(1.0 + k * (sym - speck), 0.0);
}
// per-material chroma (V3): < 1 calms, > 1 enriches
if (uChroma != 1.0) lookColor = lkSat(lookColor, uChroma);
// fresnel alpha (glass, thin films)
if (uFresAlpha > 0.0) diffuseColor.a = mix(diffuseColor.a, 1.0, uFresAlpha * pow(1.0 - lkNdV, uFresAlphaPow));
// atmospheric haze: warm toward the key / sun, cool away from it (V1), toward the zenith colour looking up (V2), grainy (V3)
float lkHaze = 0.0; vec3 lkHazeCol = uHazeColor;      // exposed to hooks (undo / redo the haze: see CORE_API §6)
if (uHazeDensity > 0.0 && uHazeMul > 0.0) {
  float dist = length(vViewPosition);
  float hz = 1.0 - exp(-max(dist - uHazeStart, 0.0) * uHazeDensity);
  if (uHazeFalloff > 0.0) hz *= exp(-max(lkWP.y - uHazeBase, 0.0) * uHazeFalloff);
  vec3 hzSun = dot(uHazeSunDir, uHazeSunDir) > 0.0 ? normalize((viewMatrix * vec4(uHazeSunDir, 0.0)).xyz) : lkL;
  float sunCos = dot(-lkV, hzSun);
  float sunward = pow(clamp(sunCos * 0.5 + 0.5, 0.0, 1.0), uHazeSunPow);
  lkHazeCol = mix(uHazeColor, mix(uHazeAway, uHazeColor, sunward), uHazeDirAmt);
  if (uHazeTopAmount > 0.0) { vec3 vd = normalize(lkWP - cameraPosition); lkHazeCol = mix(lkHazeCol, uHazeTop, uHazeTopAmount * smoothstep(-0.05, 0.6, vd.y)); }
  if (uHazeSunAmount > 0.0) lkHazeCol += uHazeSunColor * uHazeSunAmount * pow(max(sunCos, 0.0), 5.0);
  lkHaze = clamp(min(hz, uHazeMax) * uHazeMul, 0.0, 1.0);
  if (lkDA > 0.0 && uHazeDither > 0.0) lkHaze = clamp(lkHaze + lkDither * uDitherAmt * uHazeDither * 2.4 * lkHaze * (1.0 - lkHaze), 0.0, 1.0);
  lookColor = mix(lookColor, lkHazeCol, lkHaze);
}
lookColor *= uGlobalTint;
`;

let HOOK_ID = 0;
/**
 * LookMaterial — create with look.material(opts) or look.preset(name, overrides).  Uniform values live in mat.look
 * (e.g. mat.look.uRim.value = 0.4); look.set(mat, {...}) takes the friendly option names.
 */
export class LookMaterial extends THREE.MeshLambertMaterial {
  constructor(opts = {}) {
    super();
    this.isLookMaterial = true;
    // NB: keep this.type = 'MeshLambertMaterial' — three picks the shader template (and uniforms) by type.
    this.look = {
      uLit: { value: new THREE.Color(1, 1, 1) }, uMid: { value: new THREE.Color(0.8, 0.8, 0.8) }, uShade: { value: new THREE.Color(0.5, 0.5, 0.6) },
      uExplicit: { value: 0 },
      uWrap: { value: 0.45 }, uTerm: { value: 0.45 }, uSoft: { value: 0.32 }, uMidPos: { value: 0.5 },
      uLkBands: { value: 0 }, uLkBandSoft: { value: 0.12 }, uFacet: { value: 0 },
      uShadowStrength: { value: 1 }, uShadowSoft: { value: 1 },
      uRimColor: { value: new THREE.Color(1.0, 0.86, 0.74) }, uRim: { value: 0.0 }, uRimPower: { value: 3.0 }, uRimLit: { value: 1.0 },
      uBounce: { value: 1.0 }, uPointGain: { value: 1.0 },
      uGrain: { value: 0.0 }, uGrainScale: { value: 180.0 }, uHazeMul: { value: 1.0 },
      uIrid: { value: 0 }, uFresAlpha: { value: 0 }, uFresAlphaPow: { value: 2.5 }, uUnlit: { value: 0 },
      uGradAxis: { value: new THREE.Vector3(0, 1, 0) }, uGradRange: { value: new THREE.Vector2(0, 1) }, uGradColor: { value: new THREE.Color(0.8, 0.75, 0.9) }, uGradAmount: { value: 0 },
      uGroundAO: { value: 0 }, uGroundAOHeight: { value: 0.25 },
      uTermSat: { value: 0.3 }, uTermColor: { value: new THREE.Color(1, 1, 1) }, uTermTint: { value: 0 }, uTermWidth: { value: 0.3 },
      uStipple: { value: 0 }, uStippleDark: { value: 0.5 }, uStippleScale: { value: 1 }, uShadeSatMat: { value: 1 },
      uForm: { value: 0 }, uFormPow: { value: 2.2 }, uFormLit: { value: 1 }, uDither: { value: 1 }, uChroma: { value: 1 },
      uSpec: { value: 0 }, uSpecColor: { value: new THREE.Color(1.0, 0.95, 0.88) }, uSpecSize: { value: 0.35 }, uSpecSoft: { value: 0.35 },
      uRefl: { value: 0 }, uReflTop: { value: C('#cfd6f2') }, uReflHor: { value: C('#fff1dc') }, uReflBot: { value: C('#5a3a3a') }, uReflBase: { value: 0.25 },
      uReflSharp: { value: 2.5 }, uReflBlend: { value: 0 },
    };
    this.hook = null;
    if (opts) set(this, opts);
  }
  onBeforeCompile(shader) {
    Object.assign(shader.uniforms, this.look, env);
    if (this.hook && this.hook.uniforms) Object.assign(shader.uniforms, this.hook.uniforms);
    shader.vertexShader = shader.vertexShader
      .replace('#include <common>', '#include <common>\nvarying vec3 vLookWorldPos;\nvarying vec3 vLookObjPos;\nvarying vec2 vLookUv;')
      .replace('#include <project_vertex>', `#include <project_vertex>
  vec4 lkWorld = vec4(transformed, 1.0);
  #ifdef USE_BATCHING
    lkWorld = batchingMatrix * lkWorld;
  #endif
  #ifdef USE_INSTANCING
    lkWorld = instanceMatrix * lkWorld;
  #endif
  vLookWorldPos = (modelMatrix * lkWorld).xyz;
  vLookObjPos = position;
  vLookUv = uv;
  ${this.hook && this.hook.vertex ? this.hook.vertex : ''}`);
    let fs = shader.fragmentShader;
    fs = fs.replace('#include <shadowmap_pars_fragment>', '#include <shadowmap_pars_fragment>\n' + PARS + (this.hook && this.hook.pars ? this.hook.pars : ''));
    fs = fs.replace('#include <lights_lambert_fragment>', LIGHTING + (this.hook && this.hook.fragment ? '\n// --- hook ---\n' + this.hook.fragment + '\n' : ''));
    fs = fs.replace('#include <lights_fragment_begin>', '').replace('#include <lights_fragment_maps>', '').replace('#include <lights_fragment_end>', '').replace('#include <aomap_fragment>', '');
    fs = fs.replace(/vec3 outgoingLight = [^;]*;/, 'vec3 outgoingLight = lookColor;');
    shader.fragmentShader = fs;
  }
  customProgramCacheKey() { return 'lookr1' + (this.hook ? ':' + this.hook.key : ''); }
  copy(src) { super.copy(src); if (src.look) { for (const k in src.look) { const v = src.look[k].value; this.look[k] = { value: v && v.clone ? v.clone() : v }; } } this.hook = src.hook; return this; }
}

/**
 * set(mat, opts) — update a LookMaterial with friendly option names (all optional):
 *  color | map | vertexColors                 base albedo (map / vertex colours multiply). Hex, '#rrggbb', [r,g,b] linear, Color.
 *  lit, mid, shade                            explicit ramp colours (switches to explicit mode; albedo then multiplies them —
 *                                             keep color white or use a near-white painted map)
 *  explicit: bool                             force explicit / derived mode (derived = albedo x env lit/mid/shade tints)
 *  wrap (0.45), terminator (0.45), softness (0.32), midPos (0.5)        ramp shape
 *  bands (0 = smooth; N = colour-block steps), bandSoft (0.12), facet (0..1 flat-face normals)
 *  shadow (1 = full received-shadow strength), shadowSoft (1 = light.shadow.radius texels multiplier)
 *  rim (0), rimColor, rimPower (3), rimLit (1 = only on the key-lit side; 0 = everywhere)
 *  bounce (1), pointGain (1)                  warm floor bounce, point-light glow gain
 *  grain (0), grainScale (180 cells per object-space metre)              per-surface mottling
 *  haze (1 = full env haze, 0 = none)         per-material haze multiplier
 *  iridescence (0), fresnelAlpha (0), fresnelAlphaPow (2.5), unlit (false)
 *  grad: {axis:[0,1,0], range:[y0,y1], color, amount}                    object-space colour fade (amount at range[0])
 *  groundAO (0), groundAOHeight (0.25)        soft darkening near world y = 0
 *  termSat (0.3), termColor ('#fff'), termTint (0), termWidth (0.3)     terminator accent band (saturation / colour)
 *  stipple (0), stippleDark (0.5), stippleScale (1 = speck of ~one output pixel)   surface-anchored tone-driven specks
 *  shadeSat (1 = env shadeSat; derived mode only)                       saturation kept in derived shade colours
 *  dither (1)                                 multiplier of the stipple-dithered ramp (0 = smooth ramp: eyes, text, glows)
 *  form (0), formPow (2.2), formLit (1)       airbrushed violet roll-off of shade-side silhouettes (formLit 1 = shade side only)
 *  chroma (1)                                 saturation multiplier of the shaded colour (terrain/canyon: < 1 calms)
 *  spec (0), specColor ('#fff2e0'), specSize (0.35: 0 tiny .. 1 broad), specSoft (0.35: edge softness)   r02 painted highlight
 *     shape (soft-edged Blinn lobe on the key-lit side; glossy domes, chrome, eyes) — the look has almost no specular: keep it small
 *  reflect (0), reflectColors: [top, horizon, bottom] ('#cfd6f2', '#fff1dc', '#5a3a3a'), reflectBase (0.25: facing weight;
 *     grazing = 1), reflectSharp (2.5: horizon band sharpness), reflectBlend ('mix' | 'multiply')   r02 stylised environment
 *     reflection by the reflected ray's world elevation (sky / bright horizon band / dark ground), grainy edge
 *  emissive, emissiveIntensity, emissiveMap, opacity, transparent, side, depthWrite, alphaTest, flatShading, blending
 *  hook: {uniforms, pars, fragment, vertex}   custom GLSL (see CORE_API.md §Hooks)
 */
export function set(mat, o = {}) {
  const u = mat.look;
  const has = k => Object.prototype.hasOwnProperty.call(o, k) && o[k] !== undefined;
  if (has('color')) mat.color.copy(C(o.color));
  if (has('map')) { mat.map = o.map; mat.needsUpdate = true; }
  if (has('vertexColors')) { mat.vertexColors = o.vertexColors; mat.needsUpdate = true; }
  if (has('lit') || has('mid') || has('shade')) {
    if (has('lit')) u.uLit.value.copy(C(o.lit));
    if (has('shade')) u.uShade.value.copy(C(o.shade));
    if (has('mid')) u.uMid.value.copy(C(o.mid)); else if (has('lit') && has('shade')) u.uMid.value.copy(C(o.lit)).lerp(C(o.shade), 0.5);
    u.uExplicit.value = 1;
    if (!has('color')) mat.color.setRGB(1, 1, 1);
  }
  if (has('explicit')) u.uExplicit.value = o.explicit ? 1 : 0;
  const num = { wrap: 'uWrap', terminator: 'uTerm', softness: 'uSoft', midPos: 'uMidPos', bands: 'uLkBands', bandSoft: 'uLkBandSoft', facet: 'uFacet',
    shadow: 'uShadowStrength', shadowSoft: 'uShadowSoft', rim: 'uRim', rimPower: 'uRimPower', rimLit: 'uRimLit', bounce: 'uBounce',
    pointGain: 'uPointGain', grain: 'uGrain', grainScale: 'uGrainScale', haze: 'uHazeMul', iridescence: 'uIrid', fresnelAlpha: 'uFresAlpha',
    fresnelAlphaPow: 'uFresAlphaPow', groundAO: 'uGroundAO', groundAOHeight: 'uGroundAOHeight',
    termSat: 'uTermSat', termTint: 'uTermTint', termWidth: 'uTermWidth', stipple: 'uStipple', stippleDark: 'uStippleDark',
    stippleScale: 'uStippleScale', shadeSat: 'uShadeSatMat', form: 'uForm', formPow: 'uFormPow', formLit: 'uFormLit', dither: 'uDither', chroma: 'uChroma' };
  for (const [k, n] of Object.entries(num)) if (has(k)) u[n].value = o[k];
  if (has('unlit')) u.uUnlit.value = o.unlit ? 1 : 0;
  if (has('rimColor')) u.uRimColor.value.copy(C(o.rimColor));
  if (has('spec')) u.uSpec.value = o.spec;
  if (has('specColor')) u.uSpecColor.value.copy(C(o.specColor));
  if (has('specSize')) u.uSpecSize.value = o.specSize;
  if (has('specSoft')) u.uSpecSoft.value = o.specSoft;
  if (has('reflect')) u.uRefl.value = o.reflect;
  if (has('reflectColors')) { const rc = o.reflectColors; u.uReflTop.value.copy(C(rc[0])); u.uReflHor.value.copy(C(rc[1])); u.uReflBot.value.copy(C(rc[2])); }
  if (has('reflectBase')) u.uReflBase.value = o.reflectBase;
  if (has('reflectSharp')) u.uReflSharp.value = o.reflectSharp;
  if (has('reflectBlend')) u.uReflBlend.value = o.reflectBlend === 'multiply' ? 1 : 0;
  if (has('termColor')) { u.uTermColor.value.copy(C(o.termColor)); if (!has('termTint')) u.uTermTint.value = Math.max(u.uTermTint.value, 0.3); }
  if (has('grad')) {
    const g = o.grad;
    if (!g) u.uGradAmount.value = 0;
    else {
      if (g.axis) u.uGradAxis.value.copy(V3(g.axis)).normalize();
      if (g.range) u.uGradRange.value.set(g.range[0], g.range[1]);
      if (g.color) u.uGradColor.value.copy(C(g.color));
      u.uGradAmount.value = g.amount ?? 0.5;
    }
  }
  if (has('emissive')) mat.emissive.copy(C(o.emissive));
  if (has('emissiveIntensity')) mat.emissiveIntensity = o.emissiveIntensity;
  if (has('emissiveMap')) { mat.emissiveMap = o.emissiveMap; mat.needsUpdate = true; }
  for (const k of ['opacity', 'transparent', 'side', 'depthWrite', 'depthTest', 'alphaTest', 'flatShading', 'blending', 'alphaMap', 'polygonOffset', 'polygonOffsetFactor', 'polygonOffsetUnits', 'toneMapped', 'name']) {
    if (has(k)) { mat[k] = o[k]; if (k !== 'opacity' && k !== 'name') mat.needsUpdate = true; }
  }
  if (has('hook')) {
    const h = o.hook;
    mat.hook = h ? { ...h, key: h.key || ('h' + (++HOOK_ID) + ':' + hashStr((h.pars || '') + (h.fragment || '') + (h.vertex || ''))) } : null;
    mat.needsUpdate = true;
  }
  return mat;
}
function hashStr(s) { let h = 0; for (let i = 0; i < s.length; i++) h = (Math.imul(h, 31) + s.charCodeAt(i)) | 0; return (h >>> 0).toString(36); }

/** material(opts) -> new LookMaterial (see set() for options). */
export function material(opts = {}) { return new LookMaterial(opts); }

// ------------------------------------------------------------------------------------------------ presets
/**
 * Palette presets: explicit ramp colours (sRGB hex) measured on the 1080p reference (V1, cross-checked with V3) and tuned by
 * eye side by side at 640x360.  Each material has its own hue path from lit to shade (warm lit, violet/blue-shifted shade).
 * `form` = airbrushed violet roll-off on shade-side silhouettes (low on cloth/skin: round volumes without outlines).
 */
export const PRESETS = {
  // skin: peach lit, rose mid, rose-mauve shade with a rose-red terminator (f330 ear/neck), soft wrap, faint warm rim
  skin: { lit: '#f6ccb9', mid: '#e9a69c', shade: '#a95c6c', wrap: 0.55, terminator: 0.42, softness: 0.38, termSat: 0.32, termColor: '#e2564e', termTint: 0.16, termWidth: 0.3,
    rim: 0.15, rimColor: '#ffd9c2', rimPower: 2.6, grain: 0.04, grainScale: 900, bounce: 0.8, stipple: 0.2, stippleDark: 0.3, form: 0.14, formPow: 2.6, dither: 0.8 },
  // hair: smooth soft volume (no strand map — reads as stripes in close-up), deep violet-brown shade
  hair: { lit: '#90594e', mid: '#6c4044', shade: '#3e2338', wrap: 0.38, softness: 0.36, termSat: 0.35, rim: 0.2, rimColor: '#e8a07e', rimPower: 2.2, grain: 0.03, grainScale: 700,
    stipple: 0.35, stippleDark: 0.4, form: 0.22, formPow: 2.4 },
  // cloth blues (vest = pale periwinkle facets, jacket = mid blue with teal-lit tops, top = dark blue)
  vest: { lit: '#cbdcfb', mid: '#9fb5ea', shade: '#6670a8', wrap: 0.35, terminator: 0.5, softness: 0.36, facet: 0.45, termSat: 0.25, rim: 0.12, rimColor: '#f4e6ff', grain: 0.05, grainScale: 500,
    stipple: 0.3, stippleDark: 0.35, form: 0.14 },
  jacket: { lit: '#5196cf', mid: '#3767a4', shade: '#213372', wrap: 0.3, terminator: 0.55, softness: 0.45, termSat: 0.35, rim: 0.16, rimColor: '#9cc8ff', grain: 0.04, grainScale: 500,
    stipple: 0.6, stippleDark: 0.55, form: 0.24 },
  top: { lit: '#4479b5', mid: '#2d5590', shade: '#1c2d62', wrap: 0.3, terminator: 0.55, softness: 0.45, termSat: 0.3, rim: 0.08, grain: 0.04, grainScale: 500, stipple: 0.6, stippleDark: 0.55, form: 0.22 },
  trousers: { lit: '#a27cbc', mid: '#62479a', shade: '#33275f', wrap: 0.3, terminator: 0.55, softness: 0.42, termSat: 0.35, rim: 0.2, rimColor: '#c9b3ff', rimPower: 2.4, grain: 0.04, grainScale: 400,
    stipple: 0.6, stippleDark: 0.55, form: 0.24 },
  trouserStripe: { lit: '#c9b7ee', mid: '#9c8ad2', shade: '#62549a', wrap: 0.3, terminator: 0.55, softness: 0.42, grain: 0.08, grainScale: 400, stipple: 0.35, stippleDark: 0.4, form: 0.15 },
  shoes: { lit: '#5698e3', mid: '#3466b8', shade: '#22377c', wrap: 0.4, softness: 0.25, rim: 0.1, stipple: 0.45, form: 0.15 },
  eyeWhite: { lit: '#fbf6f2', mid: '#ece2e2', shade: '#b8a9bd', wrap: 0.7, softness: 0.5, shadow: 0.4, termSat: 0, dither: 0.3 },
  iris: { lit: '#a2c24a', mid: '#6e9a2c', shade: '#3e5a24', wrap: 0.8, softness: 0.5, shadow: 0.3, termSat: 0, dither: 0.3 },
  pupil: { lit: '#2a1e26', mid: '#21171f', shade: '#150e16', wrap: 1, softness: 0.5, shadow: 0.2, termSat: 0, dither: 0 },
  glassesRim: { lit: '#a9c8f0', mid: '#7fa3d8', shade: '#5a6fae', wrap: 0.6, softness: 0.3, rim: 0.3, rimColor: '#ffffff', rimPower: 2.0, termSat: 0.2, dither: 0.5 },
  lips: { lit: '#e88f8a', mid: '#cf6f78', shade: '#94526e', wrap: 0.6, softness: 0.4, dither: 0.5 },
  mouthDark: { lit: '#6e3346', mid: '#5a2a3c', shade: '#3a1a2c', wrap: 1, softness: 0.5, shadow: 0.3, termSat: 0, dither: 0 },
  // clay / lectern: apricot top, mauve-violet front; heavy tone-driven stipple (f560 lectern is sandstone-speckled)
  clay: { lit: '#f2b18a', mid: '#c98a7c', shade: '#6f5170', wrap: 0.3, terminator: 0.5, softness: 0.24, termSat: 0.4, rim: 0.12, rimColor: '#ffd2b0',
    grain: 0.04, grainScale: 160, groundAO: 0.35, stipple: 1.0, stippleDark: 0.75, form: 0.12, formPow: 3 },
  // museum floor: dusty rose-sand, cool mauve in shadow; heavy soft shadows; stipple grain
  floor: { lit: '#d9b4a0', mid: '#c19c8f', shade: '#8c7080', wrap: 0.8, softness: 0.5, shadow: 0.85, shadowSoft: 2.5, termSat: 0.2, grain: 0.05, grainScale: 25, bounce: 0,
    stipple: 0.6, stippleDark: 0.55 },
  plinth: { lit: '#ece2df', mid: '#c8bccb', shade: '#8781a4', wrap: 0.35, softness: 0.25, termSat: 0.25, grain: 0.04, grainScale: 120, groundAO: 0.4, stipple: 0.5, stippleDark: 0.5, form: 0.1 },
  // glass (pen): translucent, iridescent fresnel, bright rim
  glass: { lit: '#e9f2ff', mid: '#c9d6f2', shade: '#9aa4d4', opacity: 0.38, transparent: true, depthWrite: false, fresnelAlpha: 0.8, fresnelAlphaPow: 2.0,
    iridescence: 0.22, rim: 0.65, rimColor: '#ffffff', rimPower: 2.4, rimLit: 0, shadow: 0.3, side: THREE.DoubleSide, termSat: 0, dither: 0.3 },
  silver: { lit: '#f4f4fb', mid: '#b8bccc', shade: '#6b6e88', wrap: 0.2, terminator: 0.55, softness: 0.12, rim: 0.6, rimColor: '#ffffff', rimPower: 1.8, rimLit: 0, bands: 3, bandSoft: 0.2, termSat: 0, dither: 0.4 },
  paper: { lit: '#fbfaff', mid: '#efeefa', shade: '#c9c3df', wrap: 0.8, softness: 0.5, shadow: 0.6, grain: 0.03, grainScale: 300, termSat: 0, dither: 0.5 },
  // emissive glow (paper light, nib, lily core, portal): unlit, strong emission (bloom picks it up; post compresses highlights)
  glow: { color: '#ffffff', unlit: true, emissive: '#fff6e0', emissiveIntensity: 1.6, haze: 0.2, termSat: 0, dither: 0 },
  // flat sky / backdrop helpers
  backdrop: { unlit: true, haze: 0, termSat: 0, dither: 0 },
};
/** preset(name, overrides) -> LookMaterial */
export function preset(name, overrides = {}) {
  const p = PRESETS[name];
  if (!p) throw new Error('look.preset: unknown preset ' + name);
  return material({ name, ...p, ...overrides });
}

// ------------------------------------------------------------------------------------------------ sky / backdrop
/**
 * skyDome({ radius=300, stops:[[elev01, '#hex'], ...] (elev01: 0 = horizon, 1 = zenith, negative = below horizon; max 6),
 *           sunDir:[x,y,z], sunColor, sunSize (0.12; 0 = no disc), sunGlow (0.3), sunGlowPow (6; lower = broader glow),
 *           side: {dir:[x,y,z], color, amount (0.6), power (1.5)} — broad lateral colour lobe (e.g. grey-violet away from the sun),
 *           clouds: Texture (equirect RGBA, e.g. paint.clouds()), cloudAlpha (1), cloudContrast:[lo,hi] (alpha smoothstep),
 *           dither (1) — grainy-gradient sky: the elevation (and cloud alpha) is dithered with the film's stipple noise,
 *           anchored to the sky so it turns with the camera })
 * -> Mesh (BackSide sphere, unlit, not affected by haze).  mesh.userData.setStops(stops) updates colours; userData.uniforms.
 */
export function skyDome(o = {}) {
  const N = 6;
  const stops = (o.stops || [[-0.3, '#d8b5a5'], [0, '#f2cdb4'], [0.25, '#d9c2c8'], [0.6, '#aaa6c4'], [1, '#8f93bb']]).slice(0, N);
  const sd = o.side || null;
  const cc = o.cloudContrast || [0, 1];
  const uniforms = {
    uStopPos: { value: new Array(N).fill(2) }, uStopCol: { value: Array.from({ length: N }, () => new THREE.Color()) }, uCount: { value: stops.length },
    uSunDir: { value: V3(o.sunDir || [-0.4, 0.25, -0.8]).normalize() }, uSunColor: { value: C(o.sunColor || '#fff0d8') },
    uSunSize: { value: o.sunSize ?? 0.12 }, uSunGlow: { value: o.sunGlow ?? 0.3 }, uSunGlowPow: { value: o.sunGlowPow ?? 6 },
    uClouds: { value: o.clouds || null }, uHasClouds: { value: o.clouds ? 1 : 0 }, uCloudColor: { value: C(o.cloudColor || '#f6d3c8') },
    uCloudAlpha: { value: o.cloudAlpha ?? 1 }, uCloudLo: { value: cc[0] }, uCloudHi: { value: cc[1] },
    uSideDir: { value: V3(sd && sd.dir ? sd.dir : [1, 0, 0]).normalize() }, uSideColor: { value: C(sd && sd.color ? sd.color : '#8a8098') },
    uSideAmt: { value: sd ? (sd.amount ?? 0.6) : 0 }, uSidePow: { value: sd ? (sd.power ?? 1.5) : 1 },
    uSkyDither: { value: o.dither ?? 1 },
    uGlobalTint: env.uGlobalTint, uDitherAmt: env.uDitherAmt, uDitherScale: env.uDitherScale, uDitherBoil: env.uDitherBoil, uDitherSeed: env.uDitherSeed,
    uDitherSparse: env.uDitherSparse, uPxScale: env.uPxScale,
    uLensFish: env.uLensFish, uLensTheta: env.uLensTheta, uLensZoom: env.uLensZoom, uLensBarrel: env.uLensBarrel, uLensCenter: env.uLensCenter,
    uLensAspect: env.uLensAspect, uLensRes: env.uLensRes, uLensThOut: env.uLensThOut, uLensWide: env.uLensWide, uWideK: env.uWideK, uWideFace: env.uWideFace, uWideAxis: env.uWideAxis,
  };
  const setStops = st => { st.forEach((s, i) => { uniforms.uStopPos.value[i] = s[0]; uniforms.uStopCol.value[i].copy(C(s[1])); }); uniforms.uCount.value = st.length; };
  setStops(stops);
  const mat = new THREE.ShaderMaterial({
    uniforms, side: THREE.BackSide, depthWrite: false,
    vertexShader: `varying vec3 vDir; varying vec3 vSkyP; varying vec3 vSkyV; void main(){ vDir = normalize((modelMatrix * vec4(position, 0.0)).xyz); vSkyP = position; vec4 mv = modelViewMatrix * vec4(position, 1.0); vSkyV = mv.xyz; vec4 p = projectionMatrix * mv; gl_Position = p.xyww; }`,
    fragmentShader: `
      varying vec3 vDir; varying vec3 vSkyP; varying vec3 vSkyV; uniform float uStopPos[${N}]; uniform vec3 uStopCol[${N}]; uniform int uCount;
      uniform vec3 uSunDir; uniform vec3 uSunColor; uniform float uSunSize; uniform float uSunGlow; uniform float uSunGlowPow;
      uniform sampler2D uClouds; uniform float uHasClouds; uniform vec3 uCloudColor; uniform vec3 uGlobalTint;
      uniform float uCloudAlpha; uniform float uCloudLo; uniform float uCloudHi;
      uniform vec3 uSideDir; uniform vec3 uSideColor; uniform float uSideAmt; uniform float uSidePow;
      uniform float uSkyDither; uniform float uDitherAmt; uniform float uDitherScale; uniform float uDitherBoil; uniform float uDitherSeed; uniform float uDitherSparse; uniform float uPxScale;
      ${NOISE_GLSL}
      vec3 toP(vec3 c){ return sqrt(max(c, 0.0)); }
      void main(){
        vec3 d = normalize(vDir); float e = d.y;
        // grainy gradient: dither the elevation with the sky-anchored stipple noise (grain shows only where the gradient changes)
        float sn = 0.0;
        if (uSkyDither * uDitherAmt > 0.0) { sn = lkDitherNoise(vSkyP, uDitherScale, lkPxPerOut(vSkyV, uPxScale), uDitherBoil, uDitherSeed, uDitherSparse); e += sn * uDitherAmt * uSkyDither * 0.22; }
        vec3 col = toP(uStopCol[0]);
        for (int i = 1; i < ${N}; i++) { if (i >= uCount) break; float a = uStopPos[i-1], b = uStopPos[i]; col = mix(col, toP(uStopCol[i]), smoothstep(a, b, e)); }
        col *= col;
        if (uSideAmt > 0.0) { float s = pow(clamp(dot(d, uSideDir) * 0.5 + 0.5, 0.0, 1.0), uSidePow); col = mix(col, uSideColor, s * uSideAmt * smoothstep(-0.15, 0.25, e + 0.1)); }
        float s = max(dot(d, normalize(uSunDir)), 0.0);
        col += uSunColor * (uSunGlow * pow(s, uSunGlowPow) + 0.6 * smoothstep(1.0 - uSunSize * 0.02, 1.0 - uSunSize * 0.012, s));
        if (uHasClouds > 0.5) {
          vec2 uv = vec2(atan(d.z, d.x) / 6.2831853 + 0.5, asin(clamp(d.y, -1.0, 1.0)) / 3.14159265 + 0.5);
          vec4 c = texture2D(uClouds, uv);
          float ca = smoothstep(uCloudLo, uCloudHi, c.a + sn * uDitherAmt * uSkyDither * 0.35) * uCloudAlpha;
          col = mix(col, c.rgb, ca);
        }
        gl_FragColor = vec4(col * uGlobalTint, 1.0);
      }`,
  });
  const mesh = new THREE.Mesh(new THREE.SphereGeometry(o.radius || 300, 48, 24), mat);
  mesh.frustumCulled = false; mesh.renderOrder = -1000;
  mesh.userData.setStops = setStops; mesh.userData.uniforms = uniforms;
  return mesh;
}

/**
 * gradientBackground(stops, size) — a 2-stop+ vertical gradient texture (screen space) for scene.background.
 * Cheap alternative to skyDome for shots that never see a horizon.
 */
export function gradientBackground(stops = [[0, '#c8a3a0'], [1, '#f0c4a4']], size = 256) {
  const c = document.createElement('canvas'); c.width = 4; c.height = size;
  const g = c.getContext('2d'); const gr = g.createLinearGradient(0, 0, 0, size);
  for (const [p, col] of stops) gr.addColorStop(p, col);
  g.fillStyle = gr; g.fillRect(0, 0, 4, size);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

/** Walk an object tree and set castShadow / receiveShadow on every mesh. */
export function shadows(root, cast = true, receive = true) { root.traverse(o => { if (o.isMesh) { o.castShadow = cast; o.receiveShadow = receive; } }); return root; }
