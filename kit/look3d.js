// The illustrated look for three.js: a colour-ramp material in place of lighting, and the clock that makes it boil
// on the drawings rather than on the frames.
//
//   import { layer3d, THREE } from './kit/three.js';
//   import * as look3d from './kit/look3d.js';
//   const L = layer3d(1920, 1080, { background: '#e9dcc8', toneMapping: 'none' });
//   const skin = look3d.ramp({ lit: '#f4d2bd', mid: '#e0a596', shade: '#9a6478', terminator: 0.5, termTint: '#d8606e',
//                              formTint: '#6c5a9c', stipple: 1, light: [0.5, 0.8, 0.6] });
//   L.scene.add(new THREE.Mesh(geometry, skin));
//   draw: (g, t) => { const n = look3d.frameOf(t, 24); look3d.setFrame(n); figure.pose(look3d.held(t, 24, 2)); L.draw(g); }
//
// ramp(): no lights are read. Each surface takes one of three colours by how far it turns to `light` (a direction in
// the world): wrapped diffuse d = clamp((N·L + wrap) / (1 + wrap), 0, 1) is exactly `shade` at 0, exactly `lit` at 1
// and `mid` between, the colours blended in a perceptual space (gamma 2) so the steps read evenly. `softness` is how
// wide each step is, in d. On top: a band of `termTint` along the shade/mid step (`terminator`, its strength), an
// airbrushed wash of `formTint` over the side turned away, and a stipple: dots on a lattice fixed in the object's own
// space, one output pixel across (from the screen derivatives), so they ride the surface as the camera moves. A dot
// moves its pixel along the ramp, so it only shows where the ramp changes (the terminator, the shadow side) and its
// colour is always one the ramp really has. `boil` of the dots are drawn afresh on each new drawing.
// With NoToneMapping and sRGB output the pixels are the ramp colours themselves.
//
// setFrame(n) sets the frame every ramp material reads; a material redraws its boiling dots on n - n % hold (its own
// hold). post3d.chain() calls it for you with the chain's drawing (setFrame(n, true)), and the materials' own hold
// then steps aside. guard(renderer) turns a shader that fails to compile into a thrown Error carrying
// the compile log (three.js only logs it and goes on drawing black). frameOf(t, fps) is the frame at time t;
// held(t, fps, hold) the time of the drawing on screen then: animate characters with held(t, ...), the camera with t.
import { THREE } from './three.js';

export { THREE };

// the frame number every ramp material reads (one uniform object, shared, so one call moves them all), and whether
// each material steps it on its own hold (1) or it is a drawing already, the chain's (0)
const FRAME = { value: 0 };
const OWN_HOLD = { value: 1 };

export function setFrame(n, drawing = false) {
  FRAME.value = Number.isFinite(n) ? n : 0;
  OWN_HOLD.value = drawing ? 0 : 1;
}

export const frameOf = (t, fps) => Math.floor(t * fps + 1e-4);

export function held(t, fps = 24, hold = 1) {
  const n = frameOf(t, fps), h = Math.max(1, Math.round(hold));
  return (n - (((n % h) + h) % h)) / fps;                    // the floor to a multiple of hold, negative frames too
}

// ---- colour --

// '#rrggbb', 0xrrggbb or [r, g, b] in 0..1, all sRGB -> sRGB components 0..1
function srgb(c) {
  if (Array.isArray(c)) return c.slice(0, 3).map(Number);
  if (typeof c === 'number') return [(c >> 16) & 255, (c >> 8) & 255, c & 255].map(v => v / 255);
  const s = String(c).trim().replace(/^#/, '');
  const hex = s.length === 3 ? s.split('').map(ch => ch + ch).join('') : s;
  if (!/^[0-9a-f]{6}$/i.test(hex)) throw new Error(`look3d: not a colour: ${c}`);
  return [0, 2, 4].map(i => parseInt(hex.slice(i, i + 2), 16) / 255);
}

// the sRGB curve undone: what the GPU blends and three.js encodes back on the way out
const unbend = v => (v > 0.04045 ? Math.pow((v + 0.055) / 1.055, 2.4) : v / 12.92);

// a colour in the ramp's working space: the square root of linear light (gamma 2), where equal steps look equal
const perceptual = c => new THREE.Vector3(...srgb(c).map(v => Math.sqrt(unbend(v))));

// an accent for the terminator when none is given: mid, more saturated and turned toward rose, as skin flushes
// where light gives way to shadow
function flush(c) {
  const [r, g, b] = srgb(c);
  const hi = Math.max(r, g, b), lo = Math.min(r, g, b), l = (hi + lo) / 2, span = hi - lo;
  let h = 0;
  if (span > 1e-6) {
    if (hi === r) h = ((g - b) / span + 6) % 6;
    else if (hi === g) h = (b - r) / span + 2;
    else h = (r - g) / span + 4;
  }
  h *= 60;
  const s0 = span < 1e-6 ? 0 : span / (1 - Math.abs(2 * l - 1));
  const toward = 350, turn = ((toward - h + 540) % 360) - 180;          // the short way round to rose
  const hue = (h + 0.35 * turn + 360) % 360, sat = Math.min(0.85, s0 * 1.5 + 0.12), lum = l * 0.92;
  const k = n => (n + hue / 30) % 12, a = sat * Math.min(lum, 1 - lum);
  const f = n => lum - a * Math.max(-1, Math.min(k(n) - 3, 9 - k(n), 1));
  return [f(0), f(8), f(4)];
}

// ---- the material --

// three.js shader chunks, written as #include lines from short names
const chunks = (suffix, names) => names.split(/\s+/).filter(Boolean).map(n => `#include <${n}_${suffix}>`).join('\n');

const VERT = /* glsl */ `
${chunks('vertex', 'skinning_pars morphtarget_pars fog_pars')}
varying vec3 vTurn;   // the normal in view space: which way the surface faces the light
varying vec3 vHome;   // the rest-pose position in the object's own space: the stipple lattice is fixed to it
void main() {
${chunks('vertex', 'beginnormal morphinstance morphnormal skinbase skinnormal defaultnormal')}
  vTurn = transformedNormal;
${chunks('vertex', 'begin morphtarget skinning project fog')}
  vHome = position;   // before morphs and bones, so the dots stay on the same skin as it bends
}`;

const FRAG = /* glsl */ `
uniform vec3 uShade;
uniform vec3 uMid;
uniform vec3 uLit;
uniform vec3 uTerm;
uniform vec3 uForm;
uniform vec3 uLight;     // toward the light, world space, unit length
uniform vec4 uTone;      // wrap, softness, terminator strength, form wash strength
uniform vec4 uDots;      // stipple, boil, hold, 0
uniform float uFrame;
uniform float uOwnHold;
varying vec3 vTurn;
varying vec3 vHome;
${chunks('fragment', 'fog_pars')}

// where the two steps of the ramp sit in d: shade gives way to mid at 0.3, mid to lit at 0.7, so a step as wide as
// 0.6 still ends exactly on shade at d = 0 and on lit at d = 1
const float SHADE_TO_MID = 0.3;
const float MID_TO_LIT = 0.7;

// the colour of the gradient at wrapped diffuse x (not clamped: below 0 is the side turned away), perceptual space;
// hw is half the width of each step
vec3 gradientAt(float x, float hw) {
  float d = clamp(x, 0.0, 1.0);
  float toMid = smoothstep(SHADE_TO_MID - hw, SHADE_TO_MID + hw, d);
  float toLit = smoothstep(MID_TO_LIT - hw, MID_TO_LIT + hw, d);
  vec3 c = mix(mix(uShade, uMid, toMid), uLit, toLit);
  // the accent rides the shade/mid step, a little wider than the step itself
  float reach = max(hw, 0.05) * 1.25;
  c = mix(c, uTerm, uTone.z * (1.0 - smoothstep(0.0, reach, abs(d - SHADE_TO_MID))));
  // the form wash: none on the lit side, deepening as the surface turns past the terminator into the dark
  float facing = x * (1.0 + uTone.x) - uTone.x;
  c = mix(c, uForm, uTone.w * (1.0 - smoothstep(-0.8, 0.1, facing)));
  return c;
}

// integer hashing: a 32-bit avalanche (xor-shifts and odd multipliers), then lattice cells folded through it
uint scramble(uint k) {
  k = (k ^ (k >> 16u)) * 0x21f0aaadu;
  k = (k ^ (k >> 15u)) * 0xd35a2d97u;
  return k ^ (k >> 15u);
}
uint cellKey(ivec3 cell, int level, uint salt) {
  uint k = scramble(uint(cell.x) ^ salt);
  k = scramble(k + uint(cell.y) * 0x9e3779b9u);
  k = scramble(k ^ uint(cell.z) * 0x7f4a7c15u);
  return scramble(k + uint(level + 4096) * 0x94d049bbu);
}

// how far a lattice cell's dot moves its pixel along the ramp (0: no dot in this cell); down is the chance that it
// moves toward the shadow
float dotPush(ivec3 cell, int level, float density, float reach, float down, uint drawing) {
  uint k = cellKey(cell, level, 0x5bd1e995u);
  // boil: this share of the cells draws its dot afresh on every new drawing; the others never change
  if (float(k & 1023u) < uDots.y * 1024.0) k = cellKey(cell, level, drawing);
  if (float((k >> 10u) & 1023u) / 1024.0 >= density) return 0.0;
  float way = float((k >> 20u) & 63u) / 64.0 < down ? -1.0 : 1.0;
  return way * reach * (0.45 + 0.55 * float(k >> 26u) / 63.0);
}

void main() {
  vec3 n = normalize(vTurn);
#ifdef DOUBLE_SIDED
  n *= gl_FrontFacing ? 1.0 : -1.0;
#endif
  vec3 toLight = normalize((viewMatrix * vec4(uLight, 0.0)).xyz);
  float x = (dot(n, toLight) + uTone.x) / (1.0 + uTone.x);
  // a hard step (softness 0) still gets a pixel of anti-aliasing; past 0.6 the steps would spill over the ends
  float hw = min(max(0.5 * uTone.y, max(fwidth(x), 1e-4)), 0.3);

  // derivatives first, outside any branch: how much of the object one output pixel covers
  vec3 acrossX = dFdx(vHome), acrossY = dFdy(vHome);
  float push = 0.0;
  if (uDots.x > 0.0) {
    // the lattice: power-of-two cells near one pixel, with a hand-over to the next size, so a dolly changes the
    // dots gradually while a pan or a still frame keeps every one of them where it is. The size is the geometric
    // mean of the two footprints: a floor seen at a glancing angle gets dots of about a pixel's area, not dashes
    float foot = sqrt(length(acrossX) * length(acrossY));
    float level = log2(max(foot, 1e-12)) + 0.3;
    float lv = floor(level), coarser = level - lv;
    float size = exp2(lv);
    ivec3 fine = ivec3(floor(vHome / size));
    bool big = float(cellKey(fine, int(lv), 0x2545f491u) & 65535u) / 65536.0 < coarser;
    ivec3 cell = big ? ivec3(floor(vHome / (2.0 * size))) : fine;
    int at = big ? int(lv) + 1 : int(lv);
    // dots crowd the terminator and the shadow side and are gone by the lit plateau; each reaches about one step.
    // Past the terminator most of them fall toward the shadow: dark spots on the light side, as a painter dots it
    float d = clamp(x, 0.0, 1.0);
    float density = min(1.0, uDots.x * 0.24 * (1.0 - smoothstep(SHADE_TO_MID, MID_TO_LIT + 0.1, d)));
    float down = mix(0.5, 0.85, smoothstep(SHADE_TO_MID, MID_TO_LIT, d));
    float reach = 0.1 + 0.75 * max(hw, 0.06);
    float drawing = uFrame - mod(uFrame, uOwnHold > 0.5 ? max(uDots.z, 1.0) : 1.0);
    push = dotPush(cell, at, density, reach, down, scramble(uint(int(drawing)) + 0x68e31da4u));
  }

  vec3 c = gradientAt(x + push, hw);
  gl_FragColor = vec4(c * c, 1.0);                             // back from the perceptual space to linear light
${chunks('fragment', 'fog colorspace')}
}`;

// a ShaderMaterial whose copies (material.clone()) keep reading the shared frame instead of a frozen copy of it
class Ramp extends THREE.ShaderMaterial {
  copy(source) {
    super.copy(source);
    Object.assign(this.uniforms, { uFrame: FRAME, uOwnHold: OWN_HOLD });
    return this;
  }
}

export function ramp({ lit = '#efd9c4', mid = '#b98d80', shade = '#5b4a66', light = [0.5, 0.8, 0.6], wrap = 0.3,
  softness = 0.3, terminator = 0.35, termTint = null, formTint = null, stipple = 0.6, boil = 0.1, hold = 1,
  side = THREE.FrontSide } = {}) {
  const dir = new THREE.Vector3(...light);
  if (!(dir.lengthSq() > 0)) throw new Error('look3d.ramp: light must be a non-zero direction');
  dir.normalize();
  const uniforms = THREE.UniformsUtils.merge([THREE.UniformsLib.fog, {
    uShade: { value: perceptual(shade) },
    uMid: { value: perceptual(mid) },
    uLit: { value: perceptual(lit) },
    uTerm: { value: perceptual(termTint ?? flush(mid)) },
    uForm: { value: perceptual(formTint ?? shade) },
    uLight: { value: dir },
    // a form wash is a translucent airbrush layer: at most half covering
    uTone: { value: new THREE.Vector4(wrap, Math.max(0, softness), Math.min(1, Math.max(0, terminator)),
      formTint == null ? 0 : 0.5) },
    uDots: { value: new THREE.Vector4(Math.max(0, stipple), Math.min(1, Math.max(0, boil)), Math.max(1, Math.round(hold)), 0) },
  }]);
  Object.assign(uniforms, { uFrame: FRAME, uOwnHold: OWN_HOLD });   // shared after the merge, which copies what it is given
  return new Ramp({
    name: 'look3d.ramp', uniforms, vertexShader: VERT, fragmentShader: FRAG, fog: true, lights: false,
    toneMapped: false, side,
  });
}

// ---- the shader guard --

const GUARDED = new WeakSet();

// the info log of one stage, with the source lines it points at
function stageLog(gl, shader, label) {
  const log = (gl.getShaderInfoLog(shader) || '').trim();
  if (!log) return `${label}: (no log)`;
  const src = (gl.getShaderSource(shader) || '').split('\n');
  const lines = [...new Set([...log.matchAll(/ERROR:\s*\d+:(\d+)/g)].map(m => Number(m[1])))].slice(0, 3);
  const around = lines.map(at => {
    const first = Math.max(1, at - 2);                     // two lines either side of the one it names
    return src.slice(first - 1, at + 2).map((s, i) => `${first + i === at ? '>' : ' '} ${String(first + i).padStart(4)} | ${s}`)
      .join('\n');
  }).join('\n  ...\n');
  return `${label}:\n${log}${around ? `\n${around}` : ''}`;
}

export function guard(renderer) {
  if (GUARDED.has(renderer)) return renderer;
  // a program that already failed before the guard went on: say so now
  for (const p of renderer.info?.programs || []) {
    const dg = p.diagnostics;
    if (dg && dg.runnable === false) {
      throw new Error(`look3d.guard: shader program "${p.name}" failed earlier\nprogram log: ${dg.programLog}\n`
        + `vertex log: ${dg.vertexShader.log}\nfragment log: ${dg.fragmentShader.log}`);
    }
  }
  GUARDED.add(renderer);
  renderer.debug.checkShaderErrors = true;
  const before = renderer.debug.onShaderError;
  renderer.debug.onShaderError = (gl, program, vs, fs) => {
    if (typeof before === 'function') before(gl, program, vs, fs);
    const prog = (gl.getProgramInfoLog(program) || '').trim();
    throw new Error(['look3d.guard: a shader did not compile or link',
      `program log: ${prog || '(empty)'}`, stageLog(gl, fs, 'fragment shader'), stageLog(gl, vs, 'vertex shader')].join('\n'));
  };
  return renderer;
}
