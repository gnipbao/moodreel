// kit/3dcv/post.js — ported from 3DCodeVerse (https://github.com/gaoypeng/3dcodeverse), awesome showcase
//   (https://huggingface.co/datasets/3dcodeverse/3dcodeverse-awesome-showcase): the 30-second film's code,
//   source src/core/post.js, round r02, git blob 8eff026f46adcac9581ff9a1776236df800c45f8.
// Licence: CC BY-NC-SA 4.0 (https://creativecommons.org/licenses/by-nc-sa/4.0/), see kit/3dcv/LICENSE.
//   Non-commercial use only; adaptations keep this licence. The rest of moodreel is MIT.
// Changes by moodreel (2026-11-08): three.js taken from ../three.js instead of the bare 'three' import; this header.

// post.js — the film's post pipeline (CORE_API.md §7).  Promoted 2026-11-01 from look variant V1 "illustrated ramp" (judge
// panel pick) with grafts from V2 and V3:
//   V1  two-scale violet-tinted SSAO; calibrated tone-driven grain (fine luminance noise + sparse dark specks) held per
//       drawing; unsharp `sharpen` in the final downsample; shaded portal ring (`portal.shade`); no painterly filter.
//   V3  drives the in-shader stipple-dithered ramp (`dither`, seed per held drawing); clumped grain kernel (centre + half of
//       the +x/+y neighbours, lag-1 ~0.3) with pow(|n|, sparsity) dots; optional airbrush `diffuse` (full-frame mip blur
//       mixed in linear HDR), screen `mist`, `soften`; airbrushed stippled portal-outside gradient with a golden lit rim.
//   V2  `bloom.saturation` (glows keep their hue); lens (fisheye/barrel) before the painterly pass and the final grain, so
//       grain stays uniform in screen space; grain amplitude scales with output resolution.
//   scene (HDR, supersampled, MSAA, depth)  -> [SSAO tinted contact darkening] -> [depth DoF] -> bloom (mip chain) [+ diffusion]
//   -> composite: bloom + diffusion + mist + portal + exposure + highlight shoulder + sRGB + grade + vignette  (display space)
//   -> [lens: barrel / fisheye / chroma] -> [painterly anisotropic Kuwahara] -> downsample + sharpen + tone-driven grain -> canvas
// All parameters are plain objects deep-merged over defaultPostParams() every frame; nothing persists between frames.
// Owner: look panel (look promotion stage).
import { THREE } from '../three.js';
import { env as lookEnv, LENS_GLSL } from './look.js';

/** Defaults; every draw deep-merges the shot's params over a fresh copy of these. */
export function defaultPostParams() {
  return {
    clear: '#000000',            // clear colour when the scene has no background / sky
    exposure: 1.0,
    ao: { amount: 0.0, radius: 0.4, bias: 0.02, intensity: 1.0, color: '#6f5a92', radius2: 0.0, intensity2: 0.6 },  // tinted SSAO: contact radius + optional broad radius2
    dof: { amount: 0.0, focus: 4.0, blur: 6.0, maxBlur: 10.0, range: 0.0 },                  // blur: CoC (output px) at infinity
    bloom: { strength: 0.3, threshold: 0.9, knee: 0.45, radius: 0.75, tint: '#fff4ea', saturation: 1.15 },
    highlight: { knee: 0.72, desat: 0.25 },                                                   // soft shoulder (no flat white)
    grade: { contrast: 1.0, saturation: 1.0, lift: [0, 0, 0], gamma: [1, 1, 1], gain: [1, 1, 1], shadowTint: '#ffffff', highlightTint: '#ffffff', brightness: 0.0 },
    vignette: { amount: 0.22, softness: 0.55, roundness: 0.6, color: '#3a2238' },
    paint: { amount: 0.0, radius: 4.0, sharpness: 8.0, anisotropy: 1.0 },                    // anisotropic Kuwahara (display space)
    // lens (r02): fisheye 0..1 rectilinear -> equidistant, 1..2 equidistant -> equisolid (stronger edge compression, the
    // "bowl"); angle = diagonal FOV of the output in degrees (0 = the camera's own); an angle wider than the camera can
    // render (or > 150) switches to the WIDE renderer: the scene is rendered on up to 6 cube faces around the camera and
    // remapped (any angle up to 330; AO / DoF / overlay off; motion uses its analytic field)
    lens: { fisheye: 0.0, barrel: 0.0, zoom: 1.0, chroma: 0.0, center: [0.5, 0.5], angle: 0, faceSize: 0, wide: 'auto' },
    // output grain: .022 = the reference's mid-tone grain at 640x360 (calibrated together with the in-shader dither/stipple)
    // r02: flicker = fraction of the grain variance re-seeded on EVERY output frame (held drawings keep a faint shimmer, like
    // the reference's held pairs), boil = fraction re-seeded per drawing (the rest is fixed on screen); mottle = soft 3-9 px
    // airbrush mottling (relative to the fine grain, its own slower boil and a warm/cool chroma) — the reference's 3-16 px
    // texture band; chroma lowered .18 -> .1 (the reference's pixel-scale grain is nearly colourless)
    grain: { amount: 0.022, size: 1.0, shadows: 1.0, mids: 0.85, highlights: 0.1, chroma: 0.1, sparsity: 1.15, clump: 0.5, stipple: 0.5,
             animate: true, hold: 2, phase: 0, seed: 0, resScale: true, flicker: 0.1, boil: 1.0,
             mottle: 0.32, mottleSize: 4.0, mottleChroma: 0.2, mottleBoil: 0.4, mottleHighlights: 0.6 },
    // r02: objects on layer `layer` (default 30: obj.layers.set(30)) are drawn AFTER the DoF (crisp sparkles, glints), over the
    // blurred frame and before bloom; depth-tested against the scene; mode 'over' (alpha) or 'add'.  overlay: true = defaults
    overlay: null,     // { layer: 30, scene: null (default: the drawn scene), camera: null, mode: 'over', depthTest: true }
    // r02: directional motion smear in linear HDR (after DoF, before bloom): analytic screen-space field (output px over the
    // shutter: pan + roll about center + zoom) or, with `prev` (previous frame's projection x view Matrix4, non-wide only),
    // per-pixel camera reprojection; depth:[z0,z1] keeps nearer than z0 crisp (fades in to z1; non-wide only)
    motion: null,      // { amount: 1, pan: [0, 0], roll: 0, zoom: 0, center: [0.5, 0.5], prev: null, samples: 16, maxPx: 80, depth: null }
    // in-shader stipple-dithered colour ramp (look env), see look.js: amount in ramp units; shade/mid/lit = tone weights
    dither: { amount: 0.12, size: 1.0, shade: 0.75, mid: 1.0, lit: 0.12, sparsity: 1.35, boil: 0.5 },
    sharpen: 0.2,                // unsharp amount in the final downsample (crisp silhouettes at 640x360; 0 = off)
    soften: 0.0,                 // V3 airbrush tent in the final downsample (0 = off; keep off where thin strokes matter)
    diffuse: { mix: 0.0, add: 0.0, radius: 0.8, tint: '#ffffff' },             // V3 airbrush diffusion (full-frame mip blur, linear HDR)
    mist: { amount: 0.0, color: '#e8cfc2', y0: 0.0, y1: 0.6, power: 1.0 },     // V3 screen-space haze lift: full at y0 (0 = bottom), none at y1
    portal: null,   // { center:[0.5,0.5], radius:[rx,ry] (fraction of frame height), rotation:deg, feather:0.05, outside:Texture|null,
                    //   outsideColor:'#2a2226', rimColor:'#fff2d8', rimWidth:0.03, rimIntensity:1.5, invert:false,
                    //   shade:{inner:'#9a7a78', lit:'#fbeee2', width:0.5 (ring width in portal radii), light:[x,y]} — shaded rounded ring,
                    //   outsideShade:'#a08482', outsideFalloff:0.6 — airbrushed stippled fall-off of the wall away from the rim,
                    //   litRim:{color:'#ffd8a0', width:0.1, intensity:0.4} — golden light on the ring's lit flank }
  };
}

function isObj(v) { return v && typeof v === 'object' && !Array.isArray(v) && !v.isTexture && !v.isColor && !v.isVector3 && !v.isMatrix4 && !v.isObject3D && !v.isCamera; }
export function mergeParams(base, over) {
  if (!over) return base;
  for (const k of Object.keys(over)) {
    const v = over[k];
    if (isObj(v) && isObj(base[k])) mergeParams(base[k], v); else base[k] = v;
  }
  return base;
}
const col = (v, out = new THREE.Color()) => (v == null ? out.setRGB(1, 1, 1) : v.isColor ? out.copy(v) : Array.isArray(v) ? out.setRGB(v[0], v[1], v[2]) : out.set(v));
const vec3 = v => (Array.isArray(v) ? new THREE.Vector3(v[0], v[1], v[2]) : new THREE.Vector3(v, v, v));
const GRAIN_CAL = 0.0068 / 0.022;   // grain.amount .022 -> V1's measured reference-matching amplitude
/** JS twin of look.js lkFishTheta: output radius r (1 = corner) -> view angle, th = half diagonal angle, f = fisheye 0..2 */
export function fishTheta(r, th, f) {
  if (f <= 1 && th < 1.5) { const T = Math.tan(th); return Math.atan(((1 - f) * r + f * Math.tan(Math.min(r * th, 1.55)) / T) * T); }
  const e = r * th;
  return f <= 1 ? e : e + (2 * Math.asin(Math.min(1, Math.max(0, r * Math.sin(th / 2)))) - e) * Math.min(1, Math.max(0, f - 1));
}
// wide lens cube faces relative to the camera: front, right, left, up, down, back (face camera = camera.quaternion * FACE_Q[i])
const FACE_Q = [[0, 0, 0], [0, -90, 0], [0, 90, 0], [90, 0, 0], [-90, 0, 0], [0, 180, 0]]
  .map(([x, y, z]) => new THREE.Quaternion().setFromEuler(new THREE.Euler(x * Math.PI / 180, y * Math.PI / 180, z * Math.PI / 180)));
const FACE_R = FACE_Q.map(q => new THREE.Matrix3().setFromMatrix4(new THREE.Matrix4().makeRotationFromQuaternion(q.clone().invert())));   // camera space -> face space
const FACE_M = FACE_R.map(m => m.elements.slice());   // column-major: row 2 (z) = elements 2, 5, 8
const FACE_AXIS = FACE_Q.map(q => new THREE.Vector3(0, 0, -1).applyQuaternion(q.clone().invert()));   // camera forward in face space

const VS = `varying vec2 vUv; void main(){ vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }`;
const COMMON = `
varying vec2 vUv;
float hash12(vec2 p){ vec3 p3 = fract(vec3(p.xyx) * 0.1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }
vec3 hash32(vec2 p){ vec3 p3 = fract(vec3(p.xyx) * vec3(0.1031, 0.1030, 0.0973)); p3 += dot(p3, p3.yxz + 33.33); return fract((p3.xxy + p3.yzz) * p3.zyx); }
float ign(vec2 p){ return fract(52.9829189 * fract(dot(p, vec2(0.06711056, 0.00583715)))); }
vec2 vogel(int i, int n, float phi){ float r = sqrt((float(i) + 0.5) / float(n)); float th = float(i) * 2.399963229728653 + phi; return vec2(cos(th), sin(th)) * r; }
float luma(vec3 c){ return dot(c, vec3(0.2126, 0.7152, 0.0722)); }
vec3 toSRGB(vec3 c){ c = max(c, 0.0); return mix(c * 12.92, 1.055 * pow(c, vec3(1.0/2.4)) - 0.055, step(0.0031308, c)); }
${LENS_GLSL}
`;

function pass(frag, uniforms) {
  return new THREE.ShaderMaterial({ vertexShader: VS, fragmentShader: COMMON + frag, uniforms, depthTest: false, depthWrite: false });
}

// --------------------------------------------------------------------------------------------- shaders
const AO_FS = `
uniform sampler2D tDepth; uniform mat4 uProjInv; uniform mat4 uProj; uniform vec2 uRes; uniform float uRadius; uniform float uBias; uniform float uIntensity;
uniform float uRadius2; uniform float uIntensity2;
vec3 viewPos(vec2 uv){ float d = texture2D(tDepth, uv).r; vec4 p = uProjInv * vec4(uv * 2.0 - 1.0, d * 2.0 - 1.0, 1.0); return p.xyz / p.w; }
void main(){
  float d = texture2D(tDepth, vUv).r;
  if (d >= 0.99999) { gl_FragColor = vec4(1.0); return; }
  vec2 px = 1.0 / uRes;
  vec3 P = viewPos(vUv);
  vec3 Pr = viewPos(vUv + vec2(px.x, 0.0)), Pl = viewPos(vUv - vec2(px.x, 0.0)), Pu = viewPos(vUv + vec2(0.0, px.y)), Pd = viewPos(vUv - vec2(0.0, px.y));
  vec3 dx = abs(Pr.z - P.z) < abs(P.z - Pl.z) ? Pr - P : P - Pl;
  vec3 dy = abs(Pu.z - P.z) < abs(P.z - Pd.z) ? Pu - P : P - Pd;
  vec3 N = normalize(cross(dx, dy));
  float phi = ign(gl_FragCoord.xy) * 6.2831853;
  float rpx = clamp(uRadius * uProj[1][1] * 0.5 * uRes.y / max(-P.z, 1e-3), 2.0, uRes.y * 0.2);
  float r2 = uRadius * uRadius, occ = 0.0;
  for (int i = 0; i < 16; i++) {
    vec2 o = vogel(i, 16, phi) * rpx * px;
    vec3 S = viewPos(vUv + o);
    vec3 v = S - P; float vv = dot(v, v); float vn = dot(v, N);
    float f = max(r2 - vv, 0.0) / r2;
    occ += f * f * max((vn - uBias * -P.z * 0.02) / sqrt(vv + 1e-4), 0.0);
  }
  float ao = clamp(1.0 - occ * uIntensity * 1.6 / 16.0, 0.0, 1.0);
  if (uRadius2 > 0.0) {   // broad ambient occlusion (desk/floor junctions, under arms) — 12 taps
    float rp2 = clamp(uRadius2 * uProj[1][1] * 0.5 * uRes.y / max(-P.z, 1e-3), 3.0, uRes.y * 0.35);
    float q2 = uRadius2 * uRadius2, occ2 = 0.0;
    for (int i = 0; i < 12; i++) {
      vec2 o = vogel(i, 12, phi + 1.7) * rp2 * px;
      vec3 S = viewPos(vUv + o);
      vec3 v = S - P; float vv = dot(v, v); float vn = dot(v, N);
      float f = max(q2 - vv, 0.0) / q2;
      occ2 += f * max((vn - uBias * -P.z * 0.04) / sqrt(vv + 1e-4), 0.0);
    }
    ao *= clamp(1.0 - occ2 * uIntensity2 * 1.6 / 12.0, 0.0, 1.0);
  }
  gl_FragColor = vec4(vec3(ao), 1.0);
}`;
const AOBLUR_FS = `
uniform sampler2D tAO; uniform sampler2D tDepth; uniform vec2 uRes; uniform float uNear; uniform float uFar; uniform float uOrtho;
float lin(float d){ float z = d * 2.0 - 1.0; return uOrtho > 0.5 ? d : 2.0 * uNear * uFar / (uFar + uNear - z * (uFar - uNear)); }
void main(){
  float zc = lin(texture2D(tDepth, vUv).r); float s = 0.0, w = 0.0;
  for (int x = -2; x <= 2; x++) for (int y = -2; y <= 2; y++) {
    vec2 uv = vUv + vec2(float(x), float(y)) * 1.5 / uRes;
    float z = lin(texture2D(tDepth, uv).r);
    float wt = exp(-abs(z - zc) / max(zc * 0.03, 1e-3)) * exp(-float(x * x + y * y) / 6.0);
    s += texture2D(tAO, uv).r * wt; w += wt;
  }
  gl_FragColor = vec4(vec3(s / max(w, 1e-4)), 1.0);
}`;
const PREP_FS = `
uniform sampler2D tColor; uniform sampler2D tDepth; uniform sampler2D tAO; uniform float uAO; uniform vec3 uAOColor;
uniform float uNear; uniform float uFar; uniform float uOrtho; uniform float uFocus; uniform float uBlur; uniform float uMaxBlur; uniform float uRange; uniform float uDof;
float lin(float d){ float z = d * 2.0 - 1.0; return uOrtho > 0.5 ? uNear + d * (uFar - uNear) : 2.0 * uNear * uFar / (uFar + uNear - z * (uFar - uNear)); }
void main(){
  vec3 c = texture2D(tColor, vUv).rgb;
  c = max(c, 0.0); if (any(isnan(c)) || any(isinf(c))) c = vec3(0.0);   // a non-finite pixel would spread through DoF/bloom
  if (uAO > 0.0) { float a = texture2D(tAO, vUv).r; c *= mix(vec3(1.0), mix(uAOColor, vec3(1.0), a), uAO); }
  float coc = 0.0;
  if (uDof > 0.0) {
    float d = texture2D(tDepth, vUv).r;
    float z = d >= 0.99999 ? 1e5 : lin(d);
    float k = abs(1.0 - uFocus / z);
    float kr = uRange / max(z, 1e-3);
    coc = clamp(uBlur * max(k - kr, 0.0) * uDof, 0.0, uMaxBlur) * sign(z - uFocus);
  }
  gl_FragColor = vec4(c, coc);
}`;
const DOF_FS = `
uniform sampler2D tPrep; uniform vec2 uRes; uniform float uScale; uniform float uMaxBlur;
void main(){
  vec4 c0 = texture2D(tPrep, vUv);
  float coc0 = abs(c0.a) * uScale;
  float maxR = uMaxBlur * uScale;
  if (maxR < 0.5) { gl_FragColor = c0; return; }
  float phi = ign(gl_FragCoord.xy) * 6.2831853;
  float w0 = 1.0 / max(1.0, 0.15 * coc0 * coc0);
  vec3 acc = c0.rgb * w0; float wsum = w0;
  for (int i = 0; i < 64; i++) {
    vec2 o = vogel(i, 64, phi) * maxR;
    float d = length(o);
    vec4 s = texture2D(tPrep, vUv + o / uRes);
    float cs = abs(s.a) * uScale;
    float reach = s.a < c0.a ? cs : min(cs, coc0 * 1.5 + 0.5);   // background cannot bleed over a sharper foreground
    float w = clamp(reach - d + 1.0, 0.0, 1.0) / max(1.0, 0.15 * cs * cs);
    acc += s.rgb * w; wsum += w;
  }
  vec3 blurred = acc / wsum;
  gl_FragColor = vec4(mix(c0.rgb, blurred, clamp(coc0 * 0.75, 0.0, 1.0)), c0.a);
}`;
const BRIGHT_FS = `
uniform sampler2D tSrc; uniform vec2 uTexel; uniform float uThreshold; uniform float uKnee; uniform float uAll;
void main(){
  vec3 c = vec3(0.0);
  c += texture2D(tSrc, vUv + uTexel * vec2(-1.0, -1.0)).rgb; c += texture2D(tSrc, vUv + uTexel * vec2(1.0, -1.0)).rgb;
  c += texture2D(tSrc, vUv + uTexel * vec2(-1.0, 1.0)).rgb; c += texture2D(tSrc, vUv + uTexel * vec2(1.0, 1.0)).rgb;
  c *= 0.25;
  if (uAll < 0.5) {
    float br = max(c.r, max(c.g, c.b));
    float soft = clamp(br - uThreshold + uKnee, 0.0, 2.0 * uKnee); soft = soft * soft / (4.0 * uKnee + 1e-5);
    float contrib = max(soft, br - uThreshold) / max(br, 1e-5);
    c = c * contrib;
    c /= 1.0 + luma(c) * 0.25;  // karis-style tame of fireflies
  }
  gl_FragColor = vec4(c, 1.0);
}`;
const DOWN_FS = `
uniform sampler2D tSrc; uniform vec2 uTexel;
void main(){
  vec3 a = texture2D(tSrc, vUv + uTexel * vec2(-2.0, 2.0)).rgb, b = texture2D(tSrc, vUv + uTexel * vec2(0.0, 2.0)).rgb, c = texture2D(tSrc, vUv + uTexel * vec2(2.0, 2.0)).rgb;
  vec3 d = texture2D(tSrc, vUv + uTexel * vec2(-2.0, 0.0)).rgb, e = texture2D(tSrc, vUv).rgb, f = texture2D(tSrc, vUv + uTexel * vec2(2.0, 0.0)).rgb;
  vec3 g = texture2D(tSrc, vUv + uTexel * vec2(-2.0, -2.0)).rgb, h = texture2D(tSrc, vUv + uTexel * vec2(0.0, -2.0)).rgb, i = texture2D(tSrc, vUv + uTexel * vec2(2.0, -2.0)).rgb;
  vec3 j = texture2D(tSrc, vUv + uTexel * vec2(-1.0, 1.0)).rgb, k = texture2D(tSrc, vUv + uTexel * vec2(1.0, 1.0)).rgb;
  vec3 l = texture2D(tSrc, vUv + uTexel * vec2(-1.0, -1.0)).rgb, m = texture2D(tSrc, vUv + uTexel * vec2(1.0, -1.0)).rgb;
  vec3 o = e * 0.125 + (a + c + g + i) * 0.03125 + (b + d + f + h) * 0.0625 + (j + k + l + m) * 0.125;
  gl_FragColor = vec4(o, 1.0);
}`;
const UP_FS = `
uniform sampler2D tLow; uniform sampler2D tHigh; uniform vec2 uTexel; uniform float uScatter;
void main(){
  vec3 s = vec3(0.0);
  s += texture2D(tLow, vUv + uTexel * vec2(-1.0, -1.0)).rgb; s += texture2D(tLow, vUv + uTexel * vec2(0.0, -1.0)).rgb * 2.0; s += texture2D(tLow, vUv + uTexel * vec2(1.0, -1.0)).rgb;
  s += texture2D(tLow, vUv + uTexel * vec2(-1.0, 0.0)).rgb * 2.0; s += texture2D(tLow, vUv).rgb * 4.0; s += texture2D(tLow, vUv + uTexel * vec2(1.0, 0.0)).rgb * 2.0;
  s += texture2D(tLow, vUv + uTexel * vec2(-1.0, 1.0)).rgb; s += texture2D(tLow, vUv + uTexel * vec2(0.0, 1.0)).rgb * 2.0; s += texture2D(tLow, vUv + uTexel * vec2(1.0, 1.0)).rgb;
  s /= 16.0;
  gl_FragColor = vec4(mix(texture2D(tHigh, vUv).rgb, s, uScatter), 1.0);
}`;
const COMPOSITE_FS = `
uniform sampler2D tColor; uniform sampler2D tBloom; uniform float uBloom; uniform vec3 uBloomTint; uniform float uBloomSat;
uniform sampler2D tDiff; uniform float uDiffMix; uniform float uDiffAdd; uniform vec3 uDiffTint;
uniform float uMist; uniform vec3 uMistColor; uniform float uMistY0; uniform float uMistY1; uniform float uMistPow;
uniform float uExposure; uniform float uKnee; uniform float uDesat;
uniform float uContrast; uniform float uSat; uniform float uBright; uniform vec3 uLift; uniform vec3 uGamma; uniform vec3 uGain; uniform vec3 uShadowTint; uniform vec3 uHighTint;
uniform float uVig; uniform float uVigSoft; uniform float uVigRound; uniform vec3 uVigColor; uniform float uAspect;
uniform float uPortal; uniform vec2 uPCenter; uniform vec2 uPRadius; uniform float uPRot; uniform float uPFeather; uniform sampler2D tOutside; uniform float uHasOutside;
uniform vec3 uOutsideColor; uniform vec3 uRimColor; uniform float uRimWidth; uniform float uRimIntensity; uniform float uPInvert;
uniform float uPShade; uniform vec3 uPInner; uniform float uPRing; uniform vec2 uPLight; uniform vec3 uPLitCol;
uniform vec3 uOutsideShade; uniform float uOutsideFall; uniform vec3 uPLitRimCol; uniform float uPLitRimW; uniform float uPLitRimI;
uniform float uCell; uniform float uGSeed;
void main(){
  vec3 c = texture2D(tColor, vUv).rgb;
  // diffusion (airbrush): soft full-frame glow mixed in linear HDR — lowers contrast, lets bright sky breathe over edges
  if (uDiffMix + uDiffAdd > 0.0) { vec3 df = texture2D(tDiff, vUv).rgb * uDiffTint; c = mix(c, df, uDiffMix) + df * uDiffAdd; }
  vec3 b = texture2D(tBloom, vUv).rgb;
  b = max(mix(vec3(luma(b)), b, uBloomSat), 0.0);          // glows keep their hue instead of washing to white
  c += b * uBloom * uBloomTint;
  if (uMist > 0.0) { float my = pow(clamp((vUv.y - uMistY1) / (uMistY0 - uMistY1 + 1e-5), 0.0, 1.0), uMistPow); c = mix(c, uMistColor, my * uMist); }
  if (uPortal > 0.5) {
    vec2 p = (vUv - uPCenter) * vec2(uAspect, 1.0);
    float cr = cos(uPRot), sr = sin(uPRot); p = mat2(cr, sr, -sr, cr) * p;
    float r = length(p / max(uPRadius, vec2(1e-4)));
    float m = 1.0 - smoothstep(1.0 - uPFeather / max(uPRadius.y, 1e-3), 1.0, r);
    if (uPInvert > 0.5) m = 1.0 - m;
    vec3 outside = uOutsideColor;
    if (uHasOutside > 0.5) outside = texture2D(tOutside, vUv).rgb;
    else {
      vec2 pn = normalize(p / max(uPRadius, vec2(1e-4)) + 1e-5);
      float lit = clamp(dot(pn, normalize(uPLight + 1e-5)) * 0.5 + 0.5, 0.0, 1.0);
      // stipple on the output-pixel grid (seed per held drawing): the wall is an airbrushed, grainy gradient
      vec2 sc = floor(gl_FragCoord.xy / max(uCell, 1.0));
      float sn = hash12(sc + uGSeed * 13.1) + 0.5 * (hash12(sc + vec2(1.0, 0.0) + uGSeed * 13.1) + hash12(sc + vec2(0.0, 1.0) + uGSeed * 13.1)) - 1.0;
      if (uOutsideFall > 0.0) {   // V3: lit near the rim, falling off to the shade colour away from it (more at the bottom)
        float t = smoothstep(1.0, 1.0 + uOutsideFall, r) * mix(0.55, 1.25, smoothstep(0.9, 0.0, vUv.y));
        t = clamp(t + sn * 0.14 * (0.25 + clamp(t, 0.0, 1.0)), 0.0, 1.0);
        outside = mix(uOutsideColor, uOutsideShade, t);
      }
      if (uPShade > 0.5) {
        // V1: the frame around the portal reads as a soft rounded ring: darker inner lip, lit flank toward uPLight
        float t = clamp((r - 1.0) / max(uPRing, 1e-3), 0.0, 1.0);
        float lip = exp(-t * 7.0);                         // inner lip turning away (shade)
        float bulge = sin(clamp(t, 0.0, 1.0) * 3.14159);   // the ring's rounded top catches light
        float k = clamp(bulge * lit * 0.85 + sn * 0.08 * bulge, 0.0, 1.0);
        vec3 ring = mix(outside, uPLitCol, k);
        outside = mix(ring, uPInner, clamp(lip * 0.85 + sn * 0.06 * lip, 0.0, 1.0));
      }
      if (uPLitRimI > 0.0) {      // V3: golden light caught by the lip on the lit flank
        float rw = uPLitRimW / max(uPRadius.y, 1e-3);
        outside += uPLitRimCol * uPLitRimI * exp(-pow((r - 1.0 - rw * 0.6) / max(rw, 1e-4), 2.0)) * smoothstep(0.25, 0.9, lit);
      }
    }
    c = mix(outside, c, m);
    float rw = uRimWidth / max(uPRadius.y, 1e-3);
    c += uRimColor * uRimIntensity * exp(-pow((r - 1.0) / max(rw, 1e-4), 2.0));
  }
  c *= uExposure;
  float mx = max(c.r, max(c.g, c.b));
  if (mx > uKnee) {
    float room = 1.0 - uKnee;
    float mm = uKnee + room * (1.0 - exp(-(mx - uKnee) / room));
    c *= mm / mx;
    c = mix(c, vec3(mm), uDesat * smoothstep(uKnee, 1.0, mx) * clamp((mx - 1.0) * 0.5, 0.0, 1.0));
  }
  c = toSRGB(c);
  c = (c - 0.5) * uContrast + 0.5 + uBright;
  float l = luma(c);
  c = mix(vec3(l), c, uSat);
  c = uGain * (c + uLift * (1.0 - c));
  c = pow(max(c, 0.0), 1.0 / max(uGamma, vec3(1e-3)));
  c *= mix(uShadowTint, uHighTint, smoothstep(0.0, 1.0, l));
  vec2 q = (vUv - 0.5) * vec2(mix(1.0, uAspect, uVigRound), 1.0) * 2.0;
  float vd = length(q) / length(vec2(mix(1.0, uAspect, uVigRound), 1.0));
  float v = smoothstep(1.0 - uVigSoft, 1.0 + 0.2, vd);
  c = mix(c, c * uVigColor, v * uVig);
  gl_FragColor = vec4(c, 1.0);
}`;
const TENSOR_FS = `
uniform sampler2D tSrc; uniform vec2 uTexel;
void main(){
  vec3 a = texture2D(tSrc, vUv + uTexel * vec2(-1.0, -1.0)).rgb, b = texture2D(tSrc, vUv + uTexel * vec2(0.0, -1.0)).rgb, c = texture2D(tSrc, vUv + uTexel * vec2(1.0, -1.0)).rgb;
  vec3 d = texture2D(tSrc, vUv + uTexel * vec2(-1.0, 0.0)).rgb, f = texture2D(tSrc, vUv + uTexel * vec2(1.0, 0.0)).rgb;
  vec3 g = texture2D(tSrc, vUv + uTexel * vec2(-1.0, 1.0)).rgb, h = texture2D(tSrc, vUv + uTexel * vec2(0.0, 1.0)).rgb, i = texture2D(tSrc, vUv + uTexel * vec2(1.0, 1.0)).rgb;
  vec3 sx = (c + 2.0 * f + i - a - 2.0 * d - g) * 0.25;
  vec3 sy = (g + 2.0 * h + i - a - 2.0 * b - c) * 0.25;
  gl_FragColor = vec4(dot(sx, sx), dot(sy, sy), dot(sx, sy), 1.0);
}`;
const TBLUR_FS = `
uniform sampler2D tSrc; uniform vec2 uTexel; uniform vec2 uDir;
void main(){
  vec4 s = vec4(0.0); float w = 0.0;
  for (int i = -6; i <= 6; i++) { float wt = exp(-float(i * i) / 18.0); s += texture2D(tSrc, vUv + uDir * uTexel * float(i)) * wt; w += wt; }
  gl_FragColor = s / w;
}`;
const AKF_FS = `
uniform sampler2D tSrc; uniform sampler2D tTensor; uniform vec2 uTexel; uniform float uRadius; uniform float uQ; uniform float uAlpha; uniform float uAmount;
void main(){
  vec4 base = texture2D(tSrc, vUv);
  vec3 t = texture2D(tTensor, vUv).xyz;  // E=xx, G=yy, F=xy
  float E = t.x, G = t.y, F = t.z;
  float lam1 = 0.5 * (G + E + sqrt((G - E) * (G - E) + 4.0 * F * F));
  float lam2 = 0.5 * (G + E - sqrt((G - E) * (G - E) + 4.0 * F * F));
  vec2 v = vec2(lam1 - E, -F);
  vec2 dir = length(v) > 0.0 ? normalize(v) : vec2(0.0, 1.0);
  float phi = -atan(dir.y, dir.x);
  float A = (lam1 + lam2 > 0.0) ? (lam1 - lam2) / (lam1 + lam2) : 0.0;
  float a = uRadius * clamp((uAlpha + A) / uAlpha, 0.1, 2.0);
  float b = uRadius * clamp(uAlpha / (uAlpha + A), 0.1, 2.0);
  float cphi = cos(phi), sphi = sin(phi);
  mat2 R = mat2(cphi, -sphi, sphi, cphi);
  mat2 S = mat2(0.5 / a, 0.0, 0.0, 0.5 / b);
  mat2 SR = S * R;
  int maxX = int(sqrt(a * a * cphi * cphi + b * b * sphi * sphi));
  int maxY = int(sqrt(a * a * sphi * sphi + b * b * cphi * cphi));
  float zeta = 2.0 / max(uRadius, 1.0);
  float zeroCross = 0.58; float sinZ = sin(zeroCross);
  float eta = (zeta + cos(zeroCross)) / (sinZ * sinZ);
  vec4 m[8]; vec3 s[8];
  for (int k = 0; k < 8; k++) { m[k] = vec4(0.0); s[k] = vec3(0.0); }
  for (int y = -10; y <= 10; y++) {
    if (abs(y) > maxY) continue;
    for (int x = -10; x <= 10; x++) {
      if (abs(x) > maxX) continue;
      vec2 vv = SR * vec2(float(x), float(y));
      if (dot(vv, vv) > 0.25) continue;
      vec3 c = clamp(texture2D(tSrc, vUv + vec2(float(x), float(y)) * uTexel).rgb, 0.0, 1.0);
      float w[8]; float sum = 0.0, z, vxx, vyy;
      vxx = zeta - eta * vv.x * vv.x; vyy = zeta - eta * vv.y * vv.y;
      z = max(0.0, vv.y + vxx); w[0] = z * z; sum += w[0];
      z = max(0.0, -vv.x + vyy); w[2] = z * z; sum += w[2];
      z = max(0.0, -vv.y + vxx); w[4] = z * z; sum += w[4];
      z = max(0.0, vv.x + vyy); w[6] = z * z; sum += w[6];
      vec2 v2 = 0.70710678 * vec2(vv.x - vv.y, vv.x + vv.y);
      vxx = zeta - eta * v2.x * v2.x; vyy = zeta - eta * v2.y * v2.y;
      z = max(0.0, v2.y + vxx); w[1] = z * z; sum += w[1];
      z = max(0.0, -v2.x + vyy); w[3] = z * z; sum += w[3];
      z = max(0.0, -v2.y + vxx); w[5] = z * z; sum += w[5];
      z = max(0.0, v2.x + vyy); w[7] = z * z; sum += w[7];
      float g = exp(-3.125 * dot(vv, vv)) / max(sum, 1e-5);
      for (int k = 0; k < 8; k++) { float wk = w[k] * g; m[k] += vec4(c * wk, wk); s[k] += c * c * wk; }
    }
  }
  vec4 o = vec4(0.0);
  for (int k = 0; k < 8; k++) {
    vec3 mk = m[k].rgb / max(m[k].w, 1e-5);
    vec3 sk = abs(s[k] / max(m[k].w, 1e-5) - mk * mk);
    float sigma2 = sk.r + sk.g + sk.b;
    float wgt = 1.0 / (1.0 + pow(1000.0 * sigma2, 0.5 * uQ));
    o += vec4(mk * wgt, wgt);
  }
  vec3 res = o.w > 0.0 ? o.rgb / o.w : base.rgb;
  gl_FragColor = vec4(mix(base.rgb, res, uAmount), 1.0);
}`;
const LENS_FS = `
uniform sampler2D tSrc; uniform float uAspect; uniform float uFish; uniform float uBarrel; uniform float uZoom; uniform float uChroma; uniform vec2 uCenter; uniform float uThetaMax; uniform vec2 uRes;
uniform float uWarp; uniform float uThOut;
vec2 warp(vec2 uv, float k){
  vec2 p = (uv - uCenter) * vec2(uAspect, 1.0);
  float diag = length(vec2(uAspect, 1.0)) * 0.5;
  float r = length(p) / diag;                       // 1 at the corner
  float rs = r;
  if (uWarp > 0.5) {                                // (wide renderer: the projection is already applied, chroma only)
    rs = r / uZoom;
    if (abs(uThOut - uThetaMax) > 1e-5) rs = tan(min(lkFishTheta(rs, uThOut, uFish), 1.55)) / tan(uThetaMax);   // narrower output angle
    else if (uFish > 0.0) rs = lkFishRs(rs, uThetaMax, uFish);   // 0..1 rect -> equidistant, 1..2 -> equisolid
    rs *= (1.0 + uBarrel * r * r) / (1.0 + uBarrel);   // barrel: centre magnified, corners fixed
  }
  rs *= k;
  vec2 q = r > 1e-6 ? p / r * rs * diag : p;
  return q / vec2(uAspect, 1.0) + uCenter;
}
void main(){
  vec3 c;
  if (uChroma > 0.0) {
    float ca = uChroma / uRes.y;
    c.r = texture2D(tSrc, clamp(warp(vUv, 1.0 + ca), 0.0, 1.0)).r;
    c.g = texture2D(tSrc, clamp(warp(vUv, 1.0), 0.0, 1.0)).g;
    c.b = texture2D(tSrc, clamp(warp(vUv, 1.0 - ca), 0.0, 1.0)).b;
  } else c = texture2D(tSrc, clamp(warp(vUv, 1.0), 0.0, 1.0)).rgb;
  gl_FragColor = vec4(c, 1.0);
}`;
// WIDE lens (r02): output pixel -> view direction (fisheye family, any angle) -> the cube face that sees it
const WIDE_FS = `
uniform sampler2D tF0; uniform sampler2D tF1; uniform sampler2D tF2; uniform sampler2D tF3; uniform sampler2D tF4; uniform sampler2D tF5;
uniform mat3 uFR[6]; uniform float uFOn[6]; uniform float uFE;
uniform float uAspect; uniform float uTheta; uniform float uFish; uniform float uZoom; uniform float uBarrel; uniform vec2 uCenter;
vec4 faceTex(int i, vec2 uv){
  if (i == 0) return texture2D(tF0, uv);
  if (i == 1) return texture2D(tF1, uv);
  if (i == 2) return texture2D(tF2, uv);
  if (i == 3) return texture2D(tF3, uv);
  if (i == 4) return texture2D(tF4, uv);
  return texture2D(tF5, uv);
}
void main(){
  vec2 p = (vUv - uCenter) * vec2(uAspect, 1.0);
  float diag = length(vec2(uAspect, 1.0)) * 0.5;
  float r = length(p) / diag;
  float rs = r / uZoom * (1.0 + uBarrel * r * r) / (1.0 + uBarrel);
  float th = lkFishTheta(rs, uTheta, uFish);
  vec2 az = r > 1e-7 ? p / length(p) : vec2(0.0);
  vec3 d = vec3(sin(th) * az, -cos(th));
  int best = 0; float bz = -1e9; vec3 bq = d;
  for (int i = 0; i < 6; i++) { if (uFOn[i] < 0.5) continue; vec3 q = uFR[i] * d; if (-q.z > bz) { bz = -q.z; best = i; bq = q; } }
  vec2 uv = 0.5 + 0.5 * (bq.xy / max(-bq.z, 1e-4)) * uFE;
  vec4 f = faceTex(best, uv);
  vec3 c = max(f.rgb, 0.0); if (any(isnan(c)) || any(isinf(c))) c = vec3(0.0);
  gl_FragColor = vec4(c, f.a);     // alpha = view distance (m): the motion depth mask uses it
}`;
const COPY_FS = `uniform sampler2D tSrc; void main(){ gl_FragColor = texture2D(tSrc, vUv); }`;
// wide face resolve: colour + euclidean view distance in alpha (from the face depth; tan coords include the face margin)
const FACECOPY_FS = `uniform sampler2D tSrc; uniform sampler2D tDepth; uniform float uNear; uniform float uFar; uniform float uTanE;
void main(){
  float d = texture2D(tDepth, vUv).r;
  float z = d >= 0.99999 ? 1e4 : 2.0 * uNear * uFar / (uFar + uNear - (d * 2.0 - 1.0) * (uFar - uNear));
  vec2 t = (vUv * 2.0 - 1.0) * uTanE;
  gl_FragColor = vec4(texture2D(tSrc, vUv).rgb, min(z * sqrt(1.0 + dot(t, t)), 6e4));
}`;
// overlay (r02): no-DoF layer composited over the (blurred) frame, depth-tested against the scene
const OVL_FS = `
uniform sampler2D tBase; uniform sampler2D tOv; uniform sampler2D tOvD; uniform sampler2D tSceneD; uniform float uDepthTest; uniform float uAdd;
void main(){
  vec4 b = texture2D(tBase, vUv); vec4 o = texture2D(tOv, vUv);
  o.rgb = max(o.rgb, 0.0); if (any(isnan(o))) o = vec4(0.0);
  float vis = 1.0;
  if (uDepthTest > 0.5) vis = texture2D(tOvD, vUv).r <= texture2D(tSceneD, vUv).r + 1e-6 ? 1.0 : 0.0;
  vec3 c = uAdd > 0.5 ? b.rgb + o.rgb * vis : b.rgb * (1.0 - clamp(o.a, 0.0, 1.0) * vis) + o.rgb * vis;
  gl_FragColor = vec4(c, b.a);
}`;
// motion smear (r02): gather along the per-pixel screen motion (analytic pan/roll/zoom field or camera reprojection),
// jittered taps (no stepped ghosts), nearer-than-depth[0] stays crisp and is not smeared into its surroundings
const MOTION_FS = `
uniform sampler2D tSrc; uniform sampler2D tDepth; uniform vec2 uRes; uniform float uAspect; uniform float uSS;
uniform vec2 uPan; uniform float uRoll; uniform float uZoomV; uniform vec2 uMC; uniform float uAmt; uniform float uMaxPx;
uniform float uHasPrev; uniform mat4 uPrevVP; uniform mat4 uInvVP; uniform float uHasDepth; uniform vec2 uDepthFade;
uniform float uNear; uniform float uFar; uniform float uOrtho; uniform float uDistA;
float lin(float d){ float z = d * 2.0 - 1.0; return uOrtho > 0.5 ? uNear + d * (uFar - uNear) : 2.0 * uNear * uFar / (uFar + uNear - z * (uFar - uNear)); }
float fade(vec2 uv){
  if (uHasDepth < 0.5) return 1.0;
  float z = uDistA > 0.5 ? texture2D(tSrc, uv).a : lin(texture2D(tDepth, uv).r);   // wide: distance travels in alpha
  return smoothstep(uDepthFade.x, uDepthFade.y, z);
}
void main(){
  vec4 c0 = texture2D(tSrc, vUv);
  vec2 v;
  if (uHasPrev > 0.5) {
    float d = texture2D(tDepth, vUv).r;
    vec4 w = uInvVP * vec4(vUv * 2.0 - 1.0, d * 2.0 - 1.0, 1.0); w /= w.w;
    vec4 pp = uPrevVP * w; vec2 puv = pp.xy / pp.w * 0.5 + 0.5;
    v = (vUv - puv) * uRes;
  } else {
    vec2 q = (vUv - uMC) * vec2(uAspect, 1.0);
    vec2 dq = vec2(-q.y, q.x) * radians(uRoll) + q * uZoomV;
    v = dq / vec2(uAspect, 1.0) * uRes + uPan * uSS;
  }
  float k0 = fade(vUv);
  v *= uAmt * k0;
  float L = length(v); if (L > uMaxPx * uSS) v *= uMaxPx * uSS / L;
  if (length(v) < 0.75) { gl_FragColor = c0; return; }
  float j = ign(gl_FragCoord.xy);
  vec3 acc = c0.rgb; float ws = 1.0;
  for (int i = 0; i < 16; i++) {
    float t = (float(i) + j) / 16.0 - 0.5;
    vec2 uv = vUv + v * t / uRes;
    float w = uHasDepth > 0.5 ? fade(uv) : 1.0;   // nearer (crisp) pixels do not bleed into the smear
    acc += texture2D(tSrc, uv).rgb * w; ws += w;
  }
  gl_FragColor = vec4(acc / ws, c0.a);
}`;
const FINAL_FS = `
uniform sampler2D tSrc; uniform vec2 uSrcTexel; uniform float uSS;
uniform float uGrain; uniform float uGSize; uniform float uGShadows; uniform float uGMids; uniform float uGHighs; uniform float uGChroma; uniform float uGSparse; uniform float uSeed;
uniform float uGStipple; uniform float uGClump; uniform float uSharpen; uniform float uSoften;
uniform float uGFlicker; uniform float uGBoil; uniform float uFSeed; uniform float uGStatic;
uniform float uMottle; uniform float uMSize; uniform float uMChroma; uniform float uMBoil; uniform float uMHighs;
float gw(vec2 c, float s){ return hash12(c + s) - 0.5; }
// clumped grain field (sigma ~0.58): centre + clump x the +x/+y neighbours
float gclump(vec2 pc, float s){ return (gw(pc, s) + uGClump * (gw(pc + vec2(1.0, 0.0), s) + gw(pc + vec2(0.0, 1.0), s))) / sqrt(1.0 + 2.0 * uGClump * uGClump) * 2.0; }
// smooth value noise on a unit lattice (C2 quintic fade), sigma ~0.23
float vnoise(vec2 p, float s){
  vec2 i = floor(p), f = fract(p); f = f * f * f * (f * (f * 6.0 - 15.0) + 10.0);
  float a = gw(i, s), b = gw(i + vec2(1.0, 0.0), s), c = gw(i + vec2(0.0, 1.0), s), d = gw(i + vec2(1.0, 1.0), s);
  return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
}
// two-octave airbrush mottle (cell, 2.3 cell), a fixed part + a fraction re-seeded per drawing; ~unit sigma
float mottleN(vec2 q, float s, float sd){
  float n0 = vnoise(q, s) + 0.7 * vnoise(q * 0.435 + 17.3, s + 3.1);
  float n1 = vnoise(q, sd) + 0.7 * vnoise(q * 0.435 + 17.3, sd + 3.1);
  return (n0 * sqrt(1.0 - uMBoil) + n1 * sqrt(uMBoil)) * 3.6;
}
void main(){
  vec2 o = uSrcTexel * 0.5 * uSS;
  vec3 c = texture2D(tSrc, vUv).rgb * 0.6;
  c += (texture2D(tSrc, vUv + vec2(o.x, o.y)).rgb + texture2D(tSrc, vUv + vec2(-o.x, o.y)).rgb + texture2D(tSrc, vUv + vec2(o.x, -o.y)).rgb + texture2D(tSrc, vUv + vec2(-o.x, -o.y)).rgb) * 0.1;
  if (uSharpen > 0.0 || uSoften > 0.0) {
    vec2 w = uSrcTexel * 1.5 * uSS;
    vec3 b = (texture2D(tSrc, vUv + vec2(w.x, 0.0)).rgb + texture2D(tSrc, vUv - vec2(w.x, 0.0)).rgb + texture2D(tSrc, vUv + vec2(0.0, w.y)).rgb + texture2D(tSrc, vUv - vec2(0.0, w.y)).rgb) * 0.25;
    c = max(c + (c - b) * uSharpen, 0.0);           // unsharp mask against a ~1.5 output-px blur: crisp silhouettes, no halos
    if (uSoften > 0.0) c = mix(c, (c + b) * 0.5, uSoften);   // V3 airbrush tent (off by default)
  }
  if (uGrain > 0.0) {
    // tone-driven grain on the output-pixel grid: clumped noise (centre + clump x the +x/+y neighbours; the reference's
    // lag-1 ~0.25-0.45), dot-shaped by sparsity, + sparse dark specks; strongest in mid/dark tones
    vec2 pc = floor(gl_FragCoord.xy / max(uGSize, 0.25));
    float s1 = uSeed * 17.31, s2 = uSeed * 9.17 + 41.0;
    // temporal mix (r02): a fixed part (1 - boil) + the per-drawing part (boil), then a fraction (flicker) re-seeded on every
    // output frame, so a held drawing keeps a faint shimmer (the reference's held pairs differ by ~0.3-0.8 levels)
    float n = gclump(pc, s1);
    if (uGBoil < 1.0) n = n * sqrt(uGBoil) + gclump(pc, uGStatic * 17.31 + 401.0) * sqrt(1.0 - uGBoil);
    if (uGFlicker > 0.0) n = n * sqrt(1.0 - uGFlicker) + gclump(pc, uFSeed * 23.17 + 977.0) * sqrt(uGFlicker);
    n = sign(n) * pow(abs(n), uGSparse) * 1.17;   // sigma ~0.65 at sparsity 1.15 (= V1 calibration)
    float l = clamp(luma(c), 0.0, 1.0);
    float tone = uGShadows * (1.0 - l) * (1.0 - l) + uGMids * pow(4.0 * l * (1.0 - l), 1.5) + uGHighs * l * l;   // bright areas stay clean (ref sky ~0.8/255)
    float amp = uGrain * tone;
    float dens = uGStipple * 0.07 * clamp(tone * 1.4, 0.0, 1.0);
    float speck = step(1.0 - dens, hash12(pc * 0.917 + s2 + 13.7)) * (0.6 + 0.8 * hash12(pc + s1 + 5.1));
    vec3 ch = (hash32(pc + s2 * 3.1) - 0.5) * uGChroma;
    c += amp * (vec3(n) + ch) - uGrain * 2.2 * speck * tone * c / max(l + 0.05, 0.05) * 0.5;
    // airbrush mottle (r02): soft 3-9 px luminance + warm/cool variation, in mids/shade and (less) in highlights
    if (uMottle > 0.0) {
      vec2 q = gl_FragCoord.xy / max(uMSize, 0.5);
      float sd = uSeed * 5.13 + 211.0, ss = uGStatic * 5.13 + 97.0;
      float m = mottleN(q, ss, sd);
      float mc = mottleN(q * 0.8 + 41.7, ss + 7.7, sd + 7.7);
      float mt = uGShadows * (1.0 - l) * (1.0 - l) + uGMids * pow(4.0 * l * (1.0 - l), 1.5) + uMHighs * l * l;
      float ma = uGrain * uMottle * mt;
      c += ma * (vec3(m) + mc * uMChroma * vec3(0.9, -0.05, -0.85));
    }
  }
  c += (hash12(gl_FragCoord.xy + 0.37) - 0.5) / 255.0;
  gl_FragColor = vec4(clamp(c, 0.0, 1.0), 1.0);
}`;

// --------------------------------------------------------------------------------------------- Post class
export class Post {
  constructor(renderer, w, h, ss = 2) {
    this.renderer = renderer; this.w = w; this.h = h;
    this.variant = 'promoted';
    this.quadCam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
    this.quad = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), null);
    this.quad.frustumCulled = false;
    this.quadScene = new THREE.Scene(); this.quadScene.add(this.quad);
    this.mats = {
      ao: pass(AO_FS, { tDepth: { value: null }, uProjInv: { value: new THREE.Matrix4() }, uProj: { value: new THREE.Matrix4() }, uRes: { value: new THREE.Vector2() }, uRadius: { value: 0.4 }, uBias: { value: 0.02 }, uIntensity: { value: 1 }, uRadius2: { value: 0 }, uIntensity2: { value: 0.6 } }),
      aoBlur: pass(AOBLUR_FS, { tAO: { value: null }, tDepth: { value: null }, uRes: { value: new THREE.Vector2() }, uNear: { value: 0.1 }, uFar: { value: 100 }, uOrtho: { value: 0 } }),
      prep: pass(PREP_FS, { tColor: { value: null }, tDepth: { value: null }, tAO: { value: null }, uAO: { value: 0 }, uAOColor: { value: new THREE.Color() }, uNear: { value: 0.1 }, uFar: { value: 100 }, uOrtho: { value: 0 }, uFocus: { value: 4 }, uBlur: { value: 6 }, uMaxBlur: { value: 10 }, uRange: { value: 0 }, uDof: { value: 0 } }),
      dof: pass(DOF_FS, { tPrep: { value: null }, uRes: { value: new THREE.Vector2() }, uScale: { value: 2 }, uMaxBlur: { value: 10 } }),
      bright: pass(BRIGHT_FS, { tSrc: { value: null }, uTexel: { value: new THREE.Vector2() }, uThreshold: { value: 1 }, uKnee: { value: 0.5 }, uAll: { value: 0 } }),
      down: pass(DOWN_FS, { tSrc: { value: null }, uTexel: { value: new THREE.Vector2() } }),
      up: pass(UP_FS, { tLow: { value: null }, tHigh: { value: null }, uTexel: { value: new THREE.Vector2() }, uScatter: { value: 0.7 } }),
      comp: pass(COMPOSITE_FS, {
        tColor: { value: null }, tBloom: { value: null }, uBloom: { value: 0 }, uBloomTint: { value: new THREE.Color() }, uBloomSat: { value: 1 },
        tDiff: { value: null }, uDiffMix: { value: 0 }, uDiffAdd: { value: 0 }, uDiffTint: { value: new THREE.Color(1, 1, 1) },
        uMist: { value: 0 }, uMistColor: { value: new THREE.Color() }, uMistY0: { value: 0 }, uMistY1: { value: 0.6 }, uMistPow: { value: 1 },
        uExposure: { value: 1 }, uKnee: { value: 0.75 }, uDesat: { value: 0.3 },
        uContrast: { value: 1 }, uSat: { value: 1 }, uBright: { value: 0 }, uLift: { value: new THREE.Vector3() }, uGamma: { value: new THREE.Vector3(1, 1, 1) }, uGain: { value: new THREE.Vector3(1, 1, 1) },
        uShadowTint: { value: new THREE.Color() }, uHighTint: { value: new THREE.Color() },
        uVig: { value: 0 }, uVigSoft: { value: 0.5 }, uVigRound: { value: 0.5 }, uVigColor: { value: new THREE.Color() }, uAspect: { value: w / h },
        uPortal: { value: 0 }, uPCenter: { value: new THREE.Vector2(0.5, 0.5) }, uPRadius: { value: new THREE.Vector2(0.3, 0.3) }, uPRot: { value: 0 }, uPFeather: { value: 0.05 },
        tOutside: { value: null }, uHasOutside: { value: 0 }, uOutsideColor: { value: new THREE.Color() }, uRimColor: { value: new THREE.Color() }, uRimWidth: { value: 0.03 }, uRimIntensity: { value: 1 }, uPInvert: { value: 0 },
        uPShade: { value: 0 }, uPInner: { value: new THREE.Color() }, uPRing: { value: 0.5 }, uPLight: { value: new THREE.Vector2(0.6, -0.5) }, uPLitCol: { value: new THREE.Color() },
        uOutsideShade: { value: new THREE.Color() }, uOutsideFall: { value: 0 }, uPLitRimCol: { value: new THREE.Color() }, uPLitRimW: { value: 0.1 }, uPLitRimI: { value: 0 },
        uCell: { value: 2 }, uGSeed: { value: 0 },
      }),
      tensor: pass(TENSOR_FS, { tSrc: { value: null }, uTexel: { value: new THREE.Vector2() } }),
      tblur: pass(TBLUR_FS, { tSrc: { value: null }, uTexel: { value: new THREE.Vector2() }, uDir: { value: new THREE.Vector2(1, 0) } }),
      akf: pass(AKF_FS, { tSrc: { value: null }, tTensor: { value: null }, uTexel: { value: new THREE.Vector2() }, uRadius: { value: 4 }, uQ: { value: 8 }, uAlpha: { value: 1 }, uAmount: { value: 1 } }),
      lens: pass(LENS_FS, { tSrc: { value: null }, uAspect: { value: w / h }, uFish: { value: 0 }, uBarrel: { value: 0 }, uZoom: { value: 1 }, uChroma: { value: 0 }, uCenter: { value: new THREE.Vector2(0.5, 0.5) }, uThetaMax: { value: 1 }, uRes: { value: new THREE.Vector2() },
        uWarp: { value: 1 }, uThOut: { value: 1 } }),
      final: pass(FINAL_FS, { tSrc: { value: null }, uSrcTexel: { value: new THREE.Vector2() }, uSS: { value: 2 }, uGrain: { value: 0 }, uGSize: { value: 1 }, uGShadows: { value: 1 }, uGMids: { value: 1 }, uGHighs: { value: 0.3 }, uGChroma: { value: 0.2 }, uGSparse: { value: 1.3 }, uSeed: { value: 0 },
        uGStipple: { value: 0.5 }, uGClump: { value: 0.5 }, uSharpen: { value: 0 }, uSoften: { value: 0 },
        uGFlicker: { value: 0 }, uGBoil: { value: 1 }, uFSeed: { value: 0 }, uGStatic: { value: 0 },
        uMottle: { value: 0 }, uMSize: { value: 4 }, uMChroma: { value: 0.2 }, uMBoil: { value: 0.4 }, uMHighs: { value: 0.6 } }),
      wide: pass(WIDE_FS, { tF0: { value: null }, tF1: { value: null }, tF2: { value: null }, tF3: { value: null }, tF4: { value: null }, tF5: { value: null },
        uFR: { value: Array.from({ length: 6 }, () => new THREE.Matrix3()) }, uFOn: { value: [0, 0, 0, 0, 0, 0] }, uFE: { value: 1 },
        uAspect: { value: w / h }, uTheta: { value: 1 }, uFish: { value: 1 }, uZoom: { value: 1 }, uBarrel: { value: 0 }, uCenter: { value: new THREE.Vector2(0.5, 0.5) } }),
      copy: pass(COPY_FS, { tSrc: { value: null } }),
      facecopy: pass(FACECOPY_FS, { tSrc: { value: null }, tDepth: { value: null }, uNear: { value: 0.1 }, uFar: { value: 100 }, uTanE: { value: 1 } }),
      ovl: pass(OVL_FS, { tBase: { value: null }, tOv: { value: null }, tOvD: { value: null }, tSceneD: { value: null }, uDepthTest: { value: 1 }, uAdd: { value: 0 } }),
      motion: pass(MOTION_FS, { tSrc: { value: null }, tDepth: { value: null }, uRes: { value: new THREE.Vector2() }, uAspect: { value: w / h }, uSS: { value: 2 },
        uPan: { value: new THREE.Vector2() }, uRoll: { value: 0 }, uZoomV: { value: 0 }, uMC: { value: new THREE.Vector2(0.5, 0.5) }, uAmt: { value: 1 }, uMaxPx: { value: 80 },
        uHasPrev: { value: 0 }, uPrevVP: { value: new THREE.Matrix4() }, uInvVP: { value: new THREE.Matrix4() }, uHasDepth: { value: 0 }, uDepthFade: { value: new THREE.Vector2(0, 0) },
        uNear: { value: 0.1 }, uFar: { value: 100 }, uOrtho: { value: 0 }, uDistA: { value: 0 } }),
    };
    this.outFrame = null;   // the real output frame (stage.js sets it; held drawings keep grain.flicker per frame)
    this.aux = {};
    this.setSupersample(ss);
  }

  _rt(w, h, o = {}) {
    return new THREE.WebGLRenderTarget(Math.max(1, Math.round(w)), Math.max(1, Math.round(h)), {
      type: THREE.HalfFloatType, format: THREE.RGBAFormat, minFilter: THREE.LinearFilter, magFilter: THREE.LinearFilter,
      depthBuffer: !!o.depth, stencilBuffer: false, samples: o.samples || 0, depthTexture: o.depth ? new THREE.DepthTexture(Math.round(w), Math.round(h)) : null,
      wrapS: THREE.ClampToEdgeWrapping, wrapT: THREE.ClampToEdgeWrapping,
    });
  }

  /** Change the internal supersampling factor (1..3).  Default 2 (640x360 output renders internally at 1280x720). */
  setSupersample(ss) {
    this.ss = Math.max(1, Math.min(3, ss));
    const W = this.W = Math.round(this.w * this.ss), H = this.H = Math.round(this.h * this.ss);
    if (this.rts) Object.values(this.rts).forEach(r => (Array.isArray(r) ? r.forEach(x => x.dispose()) : r.dispose()));
    Object.values(this.aux).forEach(r => r.dispose()); this.aux = {};
    if (this.wideRT) { this.wideRT.ms.dispose(); this.wideRT.faces.forEach(f => f && f.dispose()); this.wideRT = null; }
    if (this.ovRT) { this.ovRT.dispose(); this.ovRT = null; }
    this.rts = {
      scene: this._rt(W, H, { depth: true, samples: 4 }),
      a: this._rt(W, H), b: this._rt(W, H), c: this._rt(W, H),
      ao: this._rt(W / 2, H / 2), ao2: this._rt(W / 2, H / 2),
      t1: this._rt(W, H), t2: this._rt(W, H),
      down: [], up: [], ddown: [], dup: [],
    };
    let bw = W / 2, bh = H / 2;
    for (let i = 0; i < 6; i++) { this.rts.down.push(this._rt(bw, bh)); this.rts.up.push(this._rt(bw, bh)); bw /= 2; bh /= 2; }
    bw = W / 4; bh = H / 4;   // diffusion chain starts at quarter resolution (it is a broad blur)
    for (let i = 0; i < 5; i++) { this.rts.ddown.push(this._rt(bw, bh)); this.rts.dup.push(this._rt(bw, bh)); bw /= 2; bh /= 2; }
  }

  _run(mat, target) {
    this.quad.material = mat;
    this.renderer.setRenderTarget(target);
    this.renderer.render(this.quadScene, this.quadCam);
  }

  /** held-drawing index for frame n: grain/dither seeds change once per `grain.hold` frames, on the reference's cadence
   *  (drawings start on EVEN global frames: 330|331, 332|333 …; `grain.phase` shifts it) */
  _held(P, frame) { const G = P.grain || {}; return G.animate === false ? 0 : Math.floor((frame - (G.phase || 0)) / Math.max(1, G.twos ? 2 : (G.hold || 1))); }

  /** lens angle used by the fisheye warp (the camera's half diagonal field of view) */
  _theta(camera) {
    const fovY = camera && camera.isPerspectiveCamera ? camera.fov * Math.PI / 180 : 0.8, aspect = this.w / this.h;
    return Math.atan(Math.tan(fovY / 2) * Math.sqrt(aspect * aspect + 1));
  }

  /** wide-lens descriptor for this draw, or null (rectilinear render + LENS warp).  lens.angle (diagonal deg) wider than the
   *  camera covers -> faces; lens.wide: 'auto' | true (force faces) | false (never) */
  _wide(P, camera) {
    const L = P.lens || {};
    if (!camera || !camera.isPerspectiveCamera || L.wide === false) return null;
    const thC = this._theta(camera);
    const thO = L.angle > 0 ? Math.min(L.angle, 330) * Math.PI / 360 : thC;
    if (!(L.wide === true || L.wide === 'on' || thO > thC + 1e-4)) return null;
    const f = thO >= 1.5 ? Math.max(L.fisheye ?? 1, 1) : (L.fisheye ?? 1);
    const zoom = L.zoom || 1, barrel = L.barrel || 0, aspect = this.w / this.h, center = L.center || [0.5, 0.5];
    const Dpx = 0.5 * Math.hypot(this.w, this.h);
    const dth0 = fishTheta(1e-3, thO, f) / 1e-3;                    // d theta / d r at the centre
    let N = L.faceSize > 0 ? L.faceSize : Math.ceil((2 * this.ss * Dpx * zoom / dth0) * 1.02 / 8) * 8;
    N = Math.max(256, Math.min(2048, N));
    const e = 8 / N;                                                // face margin (no bilinear clamp at face seams)
    // faces that see the frame: sample the output (border dense) and classify
    const on = [0, 0, 0, 0, 0, 0], diag = Math.hypot(aspect, 1) * 0.5;
    const box = Array.from({ length: 6 }, () => [1e9, 1e9, -1e9, -1e9]);   // face-plane tan bbox actually sampled
    const test = (u, v) => {
      const px = (u - center[0]) * aspect, py = v - center[1], r = Math.hypot(px, py) / diag;
      const rs = r / zoom * (1 + barrel * r * r) / (1 + barrel), th = fishTheta(rs, thO, f), l = Math.hypot(px, py) || 1;
      const d = [Math.sin(th) * px / l, Math.sin(th) * py / l, -Math.cos(th)];
      let best = 0, bz = -1e9;
      for (let i = 0; i < 6; i++) { const q = FACE_M[i]; const z = -(q[2] * d[0] + q[5] * d[1] + q[8] * d[2]); if (z > bz) { bz = z; best = i; } }
      on[best] = 1;
      const q = FACE_M[best], x = (q[0] * d[0] + q[3] * d[1] + q[6] * d[2]) / bz, y = (q[1] * d[0] + q[4] * d[1] + q[7] * d[2]) / bz, b = box[best];
      b[0] = Math.min(b[0], x); b[1] = Math.min(b[1], y); b[2] = Math.max(b[2], x); b[3] = Math.max(b[3], y);
    };
    for (let i = 0; i <= 96; i++) for (let j = 0; j <= 54; j++) test(i / 96, j / 54);
    // scissor rect per face (face px): sampled bbox + one grid step + margin (the remap never reads outside it)
    const sc = box.map((b, i) => {
      if (!on[i]) return null;
      const pad = 0.08, toPx = t => (t / (1 + e) * 0.5 + 0.5) * N;
      const x0 = Math.max(0, Math.floor(toPx(Math.max(-1 - e, b[0] - pad)))), y0 = Math.max(0, Math.floor(toPx(Math.max(-1 - e, b[1] - pad))));
      const x1 = Math.min(N, Math.ceil(toPx(Math.min(1 + e, b[2] + pad)))), y1 = Math.min(N, Math.ceil(toPx(Math.min(1 + e, b[3] + pad))));
      return [x0, y0, x1 - x0, y1 - y0];
    });
    return { thO, thC, f, N, e, on, sc, zoom, barrel, aspect, center, Dpx };
  }

  /** write the look env values the post owns: pixel scale, lens (grain cells stay one output px after the warp) and the
   *  stipple-dithered ramp (seed per held drawing) */
  _lookEnv(P, frame, camera, wide = null) {
    const D = P.dither || {}, e = lookEnv, L = P.lens || {};
    e.uPxScale.value = this.ss;
    const thC = this._theta(camera);
    e.uLensFish.value = L.fisheye || 0; e.uLensBarrel.value = L.barrel || 0; e.uLensZoom.value = L.zoom || 1; e.uLensTheta.value = thC;
    e.uLensThOut.value = L.angle > 0 && !wide ? Math.min(L.angle * Math.PI / 360, thC) : thC;
    e.uLensCenter.value.set((L.center || [0.5, 0.5])[0], (L.center || [0.5, 0.5])[1]); e.uLensAspect.value = this.w / this.h; e.uLensRes.value.set(this.W, this.H);
    e.uLensWide.value = wide ? 1 : 0;
    if (wide) {
      e.uLensFish.value = wide.f; e.uLensThOut.value = wide.thO; e.uWideK.value = wide.Dpx * wide.zoom; e.uWideFace.value = (wide.N / 2) / (1 + wide.e);
    }
    e.uDitherAmt.value = D.amount ?? 0.12; e.uDitherScale.value = D.size ?? 1;
    e.uDitherShade.value = D.shade ?? 0.75; e.uDitherMid.value = D.mid ?? 1; e.uDitherLit.value = D.lit ?? 0.12;
    e.uDitherSparse.value = D.sparsity ?? 1.35; e.uDitherBoil.value = D.boil ?? 0.5;
    e.uDitherSeed.value = (this._held(P, frame) % 997) + ((P.grain && P.grain.seed) || 0);
  }

  /** Render a scene into an auxiliary HDR texture (no post) — e.g. a portal's other world. Valid until the next call with the same slot.
   *  params (optional): the post params of the draw it is composited into (their `dither`, `grain.hold` and `lens` drive the
   *  in-shader stipple); default: defaultPostParams() — never the previous draw's, so frames stay deterministic.
   *  With params whose lens is WIDE, the faces are rendered and remapped like the draw (portal composites stay aligned). */
  renderToTexture(scene, camera, slot = 'aux0', params = null) {
    if (!this.aux[slot]) this.aux[slot] = this._rt(this.W, this.H, { depth: true, samples: 4 });
    const r = this.renderer, rt = this.aux[slot];
    const P = mergeParams(defaultPostParams(), params);
    if (camera.isPerspectiveCamera && Math.abs(camera.aspect - this.w / this.h) > 1e-6) { camera.aspect = this.w / this.h; camera.updateProjectionMatrix(); }
    const wide = params ? this._wide(P, camera) : null;
    this._lookEnv(P, lookEnv.uFrame.value, camera, wide);
    if (wide) {   // the draw it goes into is wide: give it the same remapped projection (e.g. a portal's outside world)
      if (!this.aux[slot + ':w']) this.aux[slot + ':w'] = this._rt(this.W, this.H);
      this._renderWide(scene, camera, P, wide, this.aux[slot + ':w']); r.setRenderTarget(null);
      return this.aux[slot + ':w'].texture;
    }
    r.setRenderTarget(rt); r.setClearColor(0x000000, 1); r.clear(); r.render(scene, camera); r.setRenderTarget(null);
    return rt.texture;
  }

  /** WIDE lens: render the needed cube faces around the camera (MSAA, copied out per face), then remap into `dst`. */
  _renderWide(scene, camera, P, wd, dst) {
    const r = this.renderer, N = wd.N;
    if (!this.wideRT || this.wideRT.N !== N) {
      if (this.wideRT) { this.wideRT.ms.dispose(); this.wideRT.faces.forEach(f => f && f.dispose()); }
      this.wideRT = { N, ms: this._rt(N, N, { depth: true, samples: 4 }), faces: [null, null, null, null, null, null] };   // depth: true -> resolved depthTexture
    }
    const W = this.wideRT;
    const fc = this.faceCam || (this.faceCam = new THREE.PerspectiveCamera(90, 1, 0.05, 400));
    fc.fov = 2 * Math.atan(1 + wd.e) * 180 / Math.PI; fc.aspect = 1; fc.near = camera.near; fc.far = camera.far; fc.updateProjectionMatrix();
    camera.updateMatrixWorld();
    const cp = new THREE.Vector3(), cq = new THREE.Quaternion(), cs = new THREE.Vector3();
    camera.matrixWorld.decompose(cp, cq, cs);
    const autoSh = r.shadowMap.autoUpdate; let first = true;
    const u = this.mats.wide.uniforms;
    for (let i = 0; i < 6; i++) {
      u.uFOn.value[i] = wd.on[i];
      if (!wd.on[i]) continue;
      if (!W.faces[i]) W.faces[i] = this._rt(N, N);
      fc.position.copy(cp); fc.quaternion.copy(cq).multiply(FACE_Q[i]); fc.updateMatrixWorld(true);
      lookEnv.uWideAxis.value.copy(FACE_AXIS[i]);
      const sr = wd.sc[i]; W.ms.scissor.set(sr[0], sr[1], sr[2], sr[3]); W.ms.scissorTest = sr[2] * sr[3] < N * N;   // shade only what the fisheye reads
      r.setRenderTarget(W.ms); r.setClearColor(col(P.clear), 1); r.clear(true, true, true);
      r.render(scene, fc);
      W.ms.scissorTest = false;
      if (first) { first = false; r.shadowMap.autoUpdate = false; }   // nothing moves between faces
      const fu = this.mats.facecopy.uniforms;
      fu.tSrc.value = W.ms.texture; fu.tDepth.value = W.ms.depthTexture; fu.uNear.value = fc.near; fu.uFar.value = fc.far; fu.uTanE.value = 1 + wd.e;
      this._run(this.mats.facecopy, W.faces[i]);
      u['tF' + i].value = W.faces[i].texture;
    }
    r.shadowMap.autoUpdate = autoSh;
    for (let i = 0; i < 6; i++) { u.uFR.value[i].copy(FACE_R[i]); if (!wd.on[i]) u['tF' + i].value = null; }
    u.uFE.value = 1 / (1 + wd.e); u.uAspect.value = wd.aspect; u.uTheta.value = wd.thO; u.uFish.value = wd.f; u.uZoom.value = wd.zoom; u.uBarrel.value = wd.barrel;
    u.uCenter.value.set(wd.center[0], wd.center[1]);
    // unused sampler slots must still be bound to something valid
    const any = W.faces.find((f, i) => f && wd.on[i]);
    for (let i = 0; i < 6; i++) if (!u['tF' + i].value) u['tF' + i].value = any.texture;
    this._run(this.mats.wide, dst);
  }

  /** The whole pipeline. params: partial post params (deep-merged over defaults), frame: global frame (grain seed). */
  render(scene, camera, params = {}, frame = 1, override = null) {
    const P = mergeParams(mergeParams(defaultPostParams(), params), override);
    if (P.overlay === true) P.overlay = {};
    if (P.motion === true) P.motion = {};
    const r = this.renderer, M = this.mats, R = this.rts, W = this.W, H = this.H;
    const prevAuto = r.autoClear;
    const wide = this._wide(P, camera);
    this._lookEnv(P, frame, camera, wide);
    const held = this._held(P, frame);
    const near = camera.near, far = camera.far, ortho = camera.isOrthographicCamera ? 1 : 0;
    let cur = R.a, aoOn = false, dofOn = false;
    if (wide) {
      // 1w. wide lens: cube faces -> fisheye remap (no depth: AO, DoF and the overlay are off)
      this._renderWide(scene, camera, P, wide, R.a); cur = R.a;
    } else {
    // 1. scene
    r.setRenderTarget(R.scene);
    r.setClearColor(col(P.clear), 1);
    r.clear(true, true, true);
    r.render(scene, camera);
    // 2. AO
    aoOn = P.ao && P.ao.amount > 0;
    if (aoOn) {
      const u = M.ao.uniforms;
      u.tDepth.value = R.scene.depthTexture; u.uProjInv.value.copy(camera.projectionMatrixInverse); u.uProj.value.copy(camera.projectionMatrix);
      u.uRes.value.set(R.ao.width, R.ao.height); u.uRadius.value = P.ao.radius; u.uBias.value = P.ao.bias; u.uIntensity.value = P.ao.intensity;
      u.uRadius2.value = P.ao.radius2 || 0; u.uIntensity2.value = P.ao.intensity2 ?? 0.6;
      this._run(M.ao, R.ao);
      const b = M.aoBlur.uniforms; b.tAO.value = R.ao.texture; b.tDepth.value = R.scene.depthTexture; b.uRes.value.set(R.ao.width, R.ao.height);
      b.uNear.value = near; b.uFar.value = far; b.uOrtho.value = ortho;
      this._run(M.aoBlur, R.ao2);
    }
    // 3. prep (AO multiply + CoC)
    dofOn = P.dof && P.dof.amount > 0;
    {
      const u = M.prep.uniforms;
      u.tColor.value = R.scene.texture; u.tDepth.value = R.scene.depthTexture; u.tAO.value = R.ao2.texture;
      u.uAO.value = aoOn ? P.ao.amount : 0; col(P.ao.color, u.uAOColor.value);
      u.uNear.value = near; u.uFar.value = far; u.uOrtho.value = ortho;
      u.uFocus.value = P.dof.focus; u.uBlur.value = P.dof.blur; u.uMaxBlur.value = P.dof.maxBlur; u.uRange.value = P.dof.range || 0; u.uDof.value = dofOn ? P.dof.amount : 0;
      this._run(M.prep, R.a);
    }
    cur = R.a;
    // 4. DoF gather
    if (dofOn) {
      const u = M.dof.uniforms; u.tPrep.value = R.a.texture; u.uRes.value.set(W, H); u.uScale.value = this.ss; u.uMaxBlur.value = P.dof.maxBlur;
      this._run(M.dof, R.b); cur = R.b;
    }
    // 4b. overlay (r02): the no-DoF layer, depth-tested against the scene, composited before bloom
    const OV = P.overlay;
    if (OV) {
      if (!this.ovRT) this.ovRT = this._rt(W, H, { depth: true, samples: 4 });
      const sc = OV.scene || scene, cam = OV.camera || camera;
      const bg = sc.background, mask = cam.layers.mask, autoSh = r.shadowMap.autoUpdate;
      if (!OV.scene) { sc.background = null; cam.layers.set(OV.layer ?? 30); }
      r.shadowMap.autoUpdate = false;
      r.setRenderTarget(this.ovRT); r.setClearColor(0x000000, 0); r.clear(true, true, true);
      r.render(sc, cam);
      r.shadowMap.autoUpdate = autoSh; sc.background = bg; cam.layers.mask = mask;
      const u = M.ovl.uniforms;
      u.tBase.value = cur.texture; u.tOv.value = this.ovRT.texture; u.tOvD.value = this.ovRT.depthTexture; u.tSceneD.value = R.scene.depthTexture;
      u.uDepthTest.value = OV.depthTest === false || cam !== camera ? 0 : 1; u.uAdd.value = OV.mode === 'add' ? 1 : 0;
      const dst = cur === R.a ? R.b : R.a; this._run(M.ovl, dst); cur = dst;
    }
    }
    // 4c. motion smear (r02)
    const MO = P.motion;
    if (MO && (MO.amount ?? 1) > 0) {
      const u = M.motion.uniforms, hasPrev = !!(MO.prev && MO.prev.isMatrix4) && !wide;
      u.tSrc.value = cur.texture; u.tDepth.value = R.scene.depthTexture; u.uRes.value.set(W, H); u.uAspect.value = this.w / this.h; u.uSS.value = this.ss;
      const pan = MO.pan || [0, 0], mc = MO.center || [0.5, 0.5];
      u.uPan.value.set(pan[0], pan[1]); u.uRoll.value = MO.roll || 0; u.uZoomV.value = MO.zoom || 0; u.uMC.value.set(mc[0], mc[1]);
      u.uAmt.value = MO.amount ?? 1; u.uMaxPx.value = MO.maxPx ?? 80;
      u.uHasPrev.value = hasPrev ? 1 : 0;
      if (hasPrev) { u.uPrevVP.value.copy(MO.prev); u.uInvVP.value.copy(camera.projectionMatrix).multiply(camera.matrixWorldInverse).invert(); }
      const df = MO.depth; u.uHasDepth.value = df ? 1 : 0; if (df) u.uDepthFade.value.set(df[0], df[1]); u.uDistA.value = wide ? 1 : 0;
      u.uNear.value = near; u.uFar.value = far; u.uOrtho.value = ortho;
      const dst = cur === R.a ? R.b : R.a; this._run(M.motion, dst); cur = dst;
    }
    // 5. bloom
    const bloomOn = P.bloom && P.bloom.strength > 0;
    if (bloomOn) {
      const bu = M.bright.uniforms; bu.tSrc.value = cur.texture; bu.uTexel.value.set(1 / W, 1 / H); bu.uThreshold.value = P.bloom.threshold; bu.uKnee.value = Math.max(1e-3, P.bloom.knee); bu.uAll.value = 0;
      this._run(M.bright, R.down[0]);
      for (let i = 1; i < R.down.length; i++) {
        const du = M.down.uniforms; du.tSrc.value = R.down[i - 1].texture; du.uTexel.value.set(1 / R.down[i - 1].width, 1 / R.down[i - 1].height);
        this._run(M.down, R.down[i]);
      }
      let low = R.down[R.down.length - 1];
      for (let i = R.down.length - 2; i >= 0; i--) {
        const uu = M.up.uniforms; uu.tLow.value = low.texture; uu.tHigh.value = R.down[i].texture; uu.uTexel.value.set(1 / low.width, 1 / low.height); uu.uScatter.value = P.bloom.radius;
        this._run(M.up, R.up[i]); low = R.up[i];
      }
    }
    // 5b. airbrush diffusion (V3): full-image mip blur, no threshold
    const D = P.diffuse || {};
    const diffOn = (D.mix || 0) + (D.add || 0) > 0;
    if (diffOn) {
      const bu = M.bright.uniforms; bu.tSrc.value = cur.texture; bu.uTexel.value.set(1 / W, 1 / H); bu.uAll.value = 1;
      this._run(M.bright, R.ddown[0]); bu.uAll.value = 0;
      for (let i = 1; i < R.ddown.length; i++) {
        const du = M.down.uniforms; du.tSrc.value = R.ddown[i - 1].texture; du.uTexel.value.set(1 / R.ddown[i - 1].width, 1 / R.ddown[i - 1].height);
        this._run(M.down, R.ddown[i]);
      }
      let low = R.ddown[R.ddown.length - 1];
      for (let i = R.ddown.length - 2; i >= 0; i--) {
        const uu = M.up.uniforms; uu.tLow.value = low.texture; uu.tHigh.value = R.ddown[i].texture; uu.uTexel.value.set(1 / low.width, 1 / low.height); uu.uScatter.value = D.radius ?? 0.8;
        this._run(M.up, R.dup[i]); low = R.dup[i];
      }
    }
    // 6. composite -> display space
    {
      const u = M.comp.uniforms, g = P.grade, v = P.vignette, po = P.portal;
      u.tColor.value = cur.texture; u.tBloom.value = bloomOn ? R.up[0].texture : R.down[5].texture; u.uBloom.value = bloomOn ? P.bloom.strength : 0; col(P.bloom.tint, u.uBloomTint.value);
      u.uBloomSat.value = P.bloom.saturation ?? 1;
      u.tDiff.value = diffOn ? R.dup[0].texture : R.ddown[4].texture; u.uDiffMix.value = diffOn ? (D.mix || 0) : 0; u.uDiffAdd.value = diffOn ? (D.add || 0) : 0; col(D.tint || '#ffffff', u.uDiffTint.value);
      const mi = P.mist || {}; u.uMist.value = mi.amount || 0; col(mi.color || '#e8cfc2', u.uMistColor.value); u.uMistY0.value = mi.y0 ?? 0; u.uMistY1.value = mi.y1 ?? 0.6; u.uMistPow.value = mi.power ?? 1;
      u.uExposure.value = P.exposure; u.uKnee.value = P.highlight.knee; u.uDesat.value = P.highlight.desat;
      u.uContrast.value = g.contrast; u.uSat.value = g.saturation; u.uBright.value = g.brightness || 0;
      u.uLift.value.copy(vec3(g.lift)); u.uGamma.value.copy(vec3(g.gamma)); u.uGain.value.copy(vec3(g.gain));
      col(g.shadowTint, u.uShadowTint.value); col(g.highlightTint, u.uHighTint.value);
      u.uVig.value = v.amount; u.uVigSoft.value = v.softness; u.uVigRound.value = v.roundness; col(v.color, u.uVigColor.value); u.uAspect.value = this.w / this.h;
      u.uPortal.value = po ? 1 : 0;
      if (po) {
        const c = po.center || [0.5, 0.5], rr = po.radius || [0.3, 0.3];
        u.uPCenter.value.set(c[0], c[1]); u.uPRadius.value.set(Array.isArray(rr) ? rr[0] : rr, Array.isArray(rr) ? rr[1] : rr);
        u.uPRot.value = (po.rotation || 0) * Math.PI / 180; u.uPFeather.value = po.feather ?? 0.05;
        u.tOutside.value = po.outside || null; u.uHasOutside.value = po.outside ? 1 : 0; col(po.outsideColor || '#2a2226', u.uOutsideColor.value);
        col(po.rimColor || '#fff2d8', u.uRimColor.value); u.uRimWidth.value = po.rimWidth ?? 0.03; u.uRimIntensity.value = po.rimIntensity ?? 1.0; u.uPInvert.value = po.invert ? 1 : 0;
        const sh = po.shade; u.uPShade.value = sh ? 1 : 0;
        const L = (sh && sh.light) || po.light || [0.6, -0.5]; u.uPLight.value.set(L[0], L[1]);
        if (sh) { col(sh.inner || '#9a7a78', u.uPInner.value); col(sh.lit || '#fbeee2', u.uPLitCol.value); u.uPRing.value = sh.width ?? 0.5; }
        col(po.outsideShade || po.outsideColor || '#2a2226', u.uOutsideShade.value); u.uOutsideFall.value = po.outsideFalloff || 0;
        const lr = po.litRim; u.uPLitRimI.value = lr ? (lr.intensity ?? 0.4) : 0;
        if (lr) { col(lr.color || '#ffd8a0', u.uPLitRimCol.value); u.uPLitRimW.value = lr.width ?? 0.1; }
        u.uCell.value = this.ss * ((P.dither && P.dither.size) || 1); u.uGSeed.value = held % 997;
      }
      this._run(M.comp, R.c); cur = R.c;
    }
    // 7. lens (before the painterly pass and the grain: both stay uniform in screen space under the fisheye)
    const L = P.lens;
    const thC = this._theta(camera), thO = L && L.angle > 0 ? Math.min(L.angle * Math.PI / 360, thC) : thC;
    if (L && (wide ? L.chroma > 0 : (L.fisheye > 0 || L.barrel !== 0 || L.zoom !== 1 || L.chroma > 0 || thO < thC - 1e-5))) {
      const u = M.lens.uniforms;
      u.tSrc.value = cur.texture; u.uAspect.value = this.w / this.h; u.uFish.value = L.fisheye || 0; u.uBarrel.value = L.barrel || 0; u.uZoom.value = L.zoom || 1; u.uChroma.value = (L.chroma || 0) * this.ss;
      u.uCenter.value.set(L.center[0], L.center[1]); u.uRes.value.set(W, H);
      u.uThetaMax.value = thC; u.uThOut.value = thO; u.uWarp.value = wide ? 0 : 1;   // wide: projection already applied, chroma only
      const dst = cur === R.a ? R.b : R.a; this._run(M.lens, dst); cur = dst;
    }
    // 8. painterly (optional; off by default — flicker risk in motion, washes thin strokes)
    if (P.paint && P.paint.amount > 0) {
      const tu = M.tensor.uniforms; tu.tSrc.value = cur.texture; tu.uTexel.value.set(1 / W, 1 / H); this._run(M.tensor, R.t1);
      const bu = M.tblur.uniforms; bu.uTexel.value.set(1 / W, 1 / H);
      bu.tSrc.value = R.t1.texture; bu.uDir.value.set(1, 0); this._run(M.tblur, R.t2);
      bu.tSrc.value = R.t2.texture; bu.uDir.value.set(0, 1); this._run(M.tblur, R.t1);
      const ku = M.akf.uniforms; ku.tSrc.value = cur.texture; ku.tTensor.value = R.t1.texture; ku.uTexel.value.set(1 / W, 1 / H);
      ku.uRadius.value = Math.min(10, P.paint.radius * this.ss); ku.uQ.value = P.paint.sharpness; ku.uAlpha.value = P.paint.anisotropy; ku.uAmount.value = P.paint.amount;
      const dst = cur === R.a ? R.b : R.a; this._run(M.akf, dst); cur = dst;
    }
    // 9. final -> canvas (downsample + sharpen + grain)
    {
      const u = M.final.uniforms, G = P.grain;
      const res = G.resScale === false ? 1 : Math.pow(Math.max(1, this.h / 360), 0.4);   // V2: grain reads weaker above 360p
      u.tSrc.value = cur.texture; u.uSrcTexel.value.set(1 / W, 1 / H); u.uSS.value = this.ss;
      u.uGrain.value = (G.amount || 0) * GRAIN_CAL * res; u.uGSize.value = G.size; u.uGShadows.value = G.shadows; u.uGMids.value = G.mids; u.uGHighs.value = G.highlights;
      u.uGChroma.value = G.chroma; u.uGSparse.value = G.sparsity; u.uGStipple.value = G.stipple ?? 0; u.uGClump.value = G.clump ?? 0.5;
      u.uSharpen.value = P.sharpen || 0; u.uSoften.value = P.soften || 0;
      u.uSeed.value = (held % 997) + (G.seed || 0);
      // r02 temporal grain: static part, per-drawing boil, per-frame flicker (off when animate:false), airbrush mottle
      const anim = G.animate !== false, of = this.outFrame ?? frame;
      u.uGBoil.value = anim ? Math.min(1, Math.max(0, G.boil ?? 1)) : 1; u.uGStatic.value = (G.seed || 0) + 0.5;
      u.uGFlicker.value = anim ? Math.min(1, Math.max(0, G.flicker ?? 0)) : 0; u.uFSeed.value = (of % 997) + (G.seed || 0) * 3;
      u.uMottle.value = G.mottle ?? 0; u.uMSize.value = (G.mottleSize ?? 4) * Math.pow(Math.max(1, this.h / 360), 0.7);
      u.uMChroma.value = G.mottleChroma ?? 0.2; u.uMBoil.value = anim ? Math.min(1, Math.max(0, G.mottleBoil ?? 0.4)) : 0; u.uMHighs.value = G.mottleHighlights ?? 0.6;
      this._run(M.final, null);
    }
    r.autoClear = prevAuto;
    r.setRenderTarget(null);
    return P;
  }
}
