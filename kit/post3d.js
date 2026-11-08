// The painterly finish for a three.js scene: one call per frame renders the scene into a target of its own, runs the
// passes in order and puts the result on the renderer's canvas.
//
//   import * as post3d from './kit/post3d.js';
//   const finish = post3d.chain(L.renderer, { hold: 2, ao: 1, aoTint: '#4b3f66', dof: { focus: 6.5, aperture: 0.5 },
//     bloom: 0.5, shoulder: 1, vignette: 0.3, grain: 0.03, grainSize: 1.2, flicker: 0.1, mottle: 0.3 });
//   draw: (g, t) => { finish(L.scene, L.camera, look3d.frameOf(t, 24)); g.drawImage(L.canvas, 0, 0, 1920, 1080); }
//
// The passes, each off at 0:
//   ao        occlusion from the depth buffer, two rings (a tight one for contact, a wide one under arms and along
//             floors), darkening toward `aoTint` (a colour multiplied in) rather than toward grey; `aoRadius` is the
//             wide ring in world units (default 0.6)
//   dof       { focus, aperture }: focus is the distance in focus, in world units; aperture is the blur radius of
//             something infinitely far, in percent of the frame height (thin-lens: nearer than focus blurs faster)
//   bloom     glow from what passes `bloomThreshold` (default 0.75, linear), six levels, the glow keeping its colour
//   shoulder  highlights roll off by their brightest channel, so a bright colour keeps its hue instead of going white
//   vignette  corners darker by this share
//   grain     strength of grain in the mid tones (sRGB, 0..1); shadows get about two thirds of it, highlights a sixth.
//             `grainSize` is how many pixels a grain spans (1: neighbours share about a third). The grain is redrawn
//             on frame - frame % hold, and `flicker` of it on every frame
//   mottle    an airbrush unevenness 3-16 px across, redrawn with the grain
// With every pass off the scene is rendered straight to the canvas. The output takes the renderer's colour space;
// the shoulder is the chain's only tone curve (the renderer's tone mapping is not applied on top, so ramp colours
// arrive as they were set). chain() runs look3d.guard(renderer) and look3d.setFrame(frame - frame % hold)
// for you, so ramp materials boil on the chain's `hold` (default 1); `fps` (default 24) is kept with the options, the
// passes themselves count frames. draw.opts holds the options: change them between frames (a shot's own grade);
// draw.dispose() frees the targets. Every pass is a function of the frame alone.
import { THREE } from './three.js';
import { guard, setFrame } from './look3d.js';

export { THREE };

export const POST3D = { fps: 24, hold: 1, ao: 0, aoTint: '#4b3f66', aoRadius: 0.6, dof: 0, bloom: 0, bloomThreshold: 0.75,
  shoulder: 0, vignette: 0, grain: 0, grainSize: 1, flicker: 0, mottle: 0 };

// ---- passes --

// every pass draws one triangle that covers the screen; its corners come from the vertex number, no buffers needed
const SCREEN = /* glsl */ `
varying vec2 vSt;
void main() {
  float sx = gl_VertexID == 1 ? 3.0 : -1.0;
  float sy = gl_VertexID == 2 ? 3.0 : -1.0;
  vSt = 0.5 + 0.5 * vec2(sx, sy);
  gl_Position = vec4(sx, sy, 0.0, 1.0);
}`;

// shared by the passes: a 32-bit avalanche for noise, and positions rebuilt from the depth buffer
const LIB = /* glsl */ `
varying vec2 vSt;
const vec3 LUMA = vec3(0.2126, 0.7152, 0.0722);
const float GOLDEN = 2.399963;   // the golden angle: taps on a sunflower spiral cover a disc evenly
uint scramble(uint k) {
  k = (k ^ (k >> 16u)) * 0x21f0aaadu;
  k = (k ^ (k >> 15u)) * 0xd35a2d97u;
  return k ^ (k >> 15u);
}
// a fixed turn per pixel (0..1), so neighbouring pixels sample along different directions
float spinAt(vec2 frag, uint salt) {
  uvec2 c = uvec2(frag);
  return float(scramble(c.x * 0x6c8e9cf5u ^ scramble(c.y + salt)) >> 8u) / 16777216.0;
}
`;

const DEPTH = /* glsl */ `
uniform sampler2D uDepth;
uniform mat4 uUnproject;
uniform vec2 uFull;      // the full picture, px
// the view-space point at a pixel of the full picture, read with texelFetch: a half-size pass sits on the corners
// between full-size pixels, where a filtered read could land on either side and tear the rebuilt surface
vec3 pointAt(ivec2 px) {
  ivec2 c = clamp(px, ivec2(0), ivec2(uFull) - 1);
  vec2 ndc = 2.0 * (vec2(c) + 0.5) / uFull - 1.0;
  vec4 h = uUnproject * vec4(ndc, 2.0 * texelFetch(uDepth, c, 0).r - 1.0, 1.0);
  return h.xyz / h.w;
}
bool emptyAt(ivec2 px) { return texelFetch(uDepth, clamp(px, ivec2(0), ivec2(uFull) - 1), 0).r >= 1.0; }
`;

const OCCLUDE = /* glsl */ `
${LIB}${DEPTH}
uniform mat4 uProject;
uniform float uRadius;   // the wide ring, world units

// the surface's facing at p, from the neighbour on each axis that lies on the same surface (not across an edge)
vec3 facingAt(ivec2 at, vec3 p) {
  vec3 l = pointAt(at - ivec2(1, 0)), r = pointAt(at + ivec2(1, 0));
  vec3 b = pointAt(at - ivec2(0, 1)), t = pointAt(at + ivec2(0, 1));
  vec3 alongX = abs(r.z - p.z) < abs(p.z - l.z) ? r - p : p - l;
  vec3 alongY = abs(t.z - p.z) < abs(p.z - b.z) ? t - p : p - b;
  vec3 n = normalize(cross(alongX, alongY));
  return dot(n, p) > 0.0 ? -n : n;
}

// six taps on a disc of the given radius around p: how high the neighbours rise over p's tangent plane, near ones
// counting
float ring(ivec2 at, vec3 p, vec3 n, float radius, float pxPerUnit, float turn) {
  float onScreen = min(radius * pxPerUnit, 0.25 * uFull.y);
  if (onScreen < 1.5) return 0.0;
  float rise = 0.0;
  for (int i = 0; i < 6; i++) {
    float a = 6.2831853 * turn + float(i) * GOLDEN;
    vec2 o = vec2(cos(a), sin(a)) * onScreen * sqrt((float(i) + 0.5) / 6.0);
    vec3 v = pointAt(at + ivec2(floor(o + 0.5))) - p;
    float len = length(v);
    float lift = max(dot(v, n) / max(len, 1e-5) - 0.1, 0.0);
    rise += lift * (1.0 - smoothstep(0.7 * radius, 1.5 * radius, len));
  }
  return clamp(rise / 6.0 * 1.8, 0.0, 1.0);
}

void main() {
  ivec2 at = 2 * ivec2(gl_FragCoord.xy);                // this half-size pixel's first full-size pixel
  if (emptyAt(at)) { gl_FragColor = vec4(0.0); return; }   // nothing drawn here
  vec3 p = pointAt(at);
  vec3 n = facingAt(at, p);
  // pixels per world unit at this depth (an orthographic camera has the same scale at every depth)
  float pxPerUnit = 0.5 * uFull.y * uProject[1][1] / (uProject[3][3] > 0.5 ? 1.0 : max(-p.z, 1e-4));
  float turn = spinAt(gl_FragCoord.xy, 0x1b873593u);
  float tight = ring(at, p, n, 0.25 * uRadius, pxPerUnit, turn);
  float wide = ring(at, p, n, uRadius, pxPerUnit, turn + 0.5);
  gl_FragColor = vec4(1.0 - (1.0 - tight) * (1.0 - 0.7 * wide), 0.0, 0.0, 1.0);
}`;

// the occlusion smoothed over 5 x 5 of its own pixels, only across samples at a similar depth
const SOFTEN = /* glsl */ `
${LIB}${DEPTH}
uniform sampler2D uOcc;
void main() {
  ivec2 here = ivec2(gl_FragCoord.xy), most = textureSize(uOcc, 0) - 1;
  float z0 = pointAt(2 * here).z;
  float tol = 0.04 * abs(z0) + 1e-3;
  float sum = 0.0, weight = 0.0;
  for (int j = -2; j <= 2; j++) {
    for (int i = -2; i <= 2; i++) {
      ivec2 q = clamp(here + ivec2(i, j), ivec2(0), most);
      float w = 1.0 - smoothstep(0.5 * tol, tol, abs(pointAt(2 * q).z - z0));
      sum += w * texelFetch(uOcc, q, 0).r;
      weight += w;
    }
  }
  gl_FragColor = vec4(sum / max(weight, 1e-4), 0.0, 0.0, 1.0);
}`;

// the scene with its occlusion multiplied in; alpha carries the signed blur radius for the depth of field
const PREPARE = /* glsl */ `
${LIB}${DEPTH}
uniform sampler2D uScene;
uniform sampler2D uOcc;
uniform vec3 uTint;      // what full occlusion multiplies by (linear)
uniform float uAo;
uniform vec4 uLens;      // focus distance, px of blur at infinity, largest radius px, on
void main() {
  vec3 c = texture(uScene, vSt).rgb;
  if (uAo > 0.0) c *= mix(vec3(1.0), uTint, clamp(uAo * texture(uOcc, vSt).r, 0.0, 1.0));
  float radius = 0.0;
  if (uLens.w > 0.0) {
    float dist = max(-pointAt(ivec2(gl_FragCoord.xy)).z, 1e-4);
    radius = clamp(uLens.y * (1.0 - uLens.x / dist), -uLens.z, uLens.z);   // < 0 nearer than focus, > 0 beyond
  }
  gl_FragColor = vec4(c, radius);
}`;

// thin-lens blur gathered on a spiral; a tap only counts where its own blur reaches this pixel, so a sharp neighbour
// does not smear into a soft background
const LENS = /* glsl */ `
${LIB}
uniform sampler2D uSharp;
uniform vec2 uFull;
void main() {
  vec4 here = texture(uSharp, vSt);
  float r = abs(here.a);
  if (r < 0.5) { gl_FragColor = vec4(here.rgb, 1.0); return; }
  float turn = 6.2831853 * spinAt(gl_FragCoord.xy, 0xcc9e2d51u);
  vec3 sum = here.rgb;
  float weight = 1.0;
  for (int i = 0; i < 24; i++) {
    float a = turn + float(i) * GOLDEN;
    vec2 o = vec2(cos(a), sin(a)) * r * sqrt((float(i) + 0.5) / 24.0);
    vec4 tap = texture(uSharp, vSt + o / uFull);
    float reach = length(o);
    float w = smoothstep(reach - 1.0, reach + 1.0, abs(tap.a));
    sum += w * tap.rgb;
    weight += w;
  }
  gl_FragColor = vec4(sum / weight, 1.0);
}`;

// bloom, first level: a 4 x 4 box down to half size, keeping only what glows; scaled by the brightest channel so
// the glow keeps the hue and saturation of its source
const GLOW_START = /* glsl */ `
${LIB}
uniform sampler2D uSrc;
uniform vec2 uStep;      // one source pixel
uniform float uThreshold;
void main() {
  vec3 c = vec3(0.0);
  for (int k = 0; k < 4; k++) c += texture(uSrc, vSt + uStep * vec2(k == 0 || k == 2 ? -1.0 : 1.0, k < 2 ? -1.0 : 1.0)).rgb;
  c *= 0.25;
  float peak = max(c.r, max(c.g, c.b));
  float knee = 0.25 * uThreshold + 1e-4;
  float into = clamp(peak - uThreshold + knee, 0.0, 2.0 * knee);
  float glow = max(peak - uThreshold, into * into / (4.0 * knee));
  gl_FragColor = vec4(c * (glow / max(peak, 1e-4)), 1.0);
}`;

// halving: the centre and its four diagonal neighbours, bilinear, a soft 4 x 4 footprint
const GLOW_DOWN = /* glsl */ `
${LIB}
uniform sampler2D uSrc;
uniform vec2 uStep;
void main() {
  vec3 c = 4.0 * texture(uSrc, vSt).rgb;
  for (int k = 0; k < 4; k++) c += texture(uSrc, vSt + uStep * vec2(k % 2 == 0 ? -1.0 : 1.0, k < 2 ? -1.0 : 1.0)).rgb;
  gl_FragColor = vec4(c / 8.0, 1.0);
}`;

// doubling: a 3 x 3 tent over the smaller level, laid onto this level
const GLOW_UP = /* glsl */ `
${LIB}
uniform sampler2D uSmall;
uniform sampler2D uLevel;
uniform vec2 uStep;      // one pixel of the smaller level
void main() {
  vec3 c = vec3(0.0);
  for (int j = -1; j <= 1; j++) {
    for (int i = -1; i <= 1; i++) {
      float w = (2.0 - abs(float(i))) * (2.0 - abs(float(j)));
      c += w * texture(uSmall, vSt + vec2(float(i), float(j)) * uStep).rgb;
    }
  }
  gl_FragColor = vec4(texture(uLevel, vSt).rgb + c / 16.0, 1.0);
}`;

// the last pass: glow, shoulder, vignette, then the output encoding, then grain and mottle on the encoded picture
const FINISH = /* glsl */ `
${LIB}
uniform sampler2D uImg;
uniform sampler2D uGlow;
uniform sampler2D uScene;   // for its alpha
uniform vec2 uFull;
uniform vec4 uLook;         // bloom, shoulder, vignette, mottle
uniform vec4 uGrain;        // strength, size px, flicker, 0
uniform vec2 uClock;        // the drawing (frame - frame % hold), the frame

const float KNEE = 0.8;
// the brightest channel rolls off above the knee toward 1 and the others follow it, so the hue holds
vec3 rollOff(vec3 c) {
  float top = max(c.r, max(c.g, c.b));
  if (top <= KNEE) return c;
  float rolled = 1.0 - (1.0 - KNEE) * exp((KNEE - top) / (1.0 - KNEE));
  return c * (rolled / top);
}

// grain lives in the mid tones: full there, about two thirds in the shadows, a sixth at the top
float toneWeight(float l) {
  float up = smoothstep(0.0, 0.42, l), down = smoothstep(0.42, 1.0, l);
  return mix(0.55, 1.0, up) * mix(1.0, 0.12, down);
}

uint drawingKey() { return scramble(uint(int(uClock.x)) * 0x2c1b3c6du + 0x297a2d39u); }
uint frameKey() { return scramble(uint(int(uClock.y)) * 0x5e2d58d9u + 0x9e3779b9u); }

// one grain: a triangular variate of unit variance; the flicker share of them redrawn every frame
float grainCell(vec2 cell, uint drawing, uint frame) {
  uvec2 c = uvec2(ivec2(cell) + 65536);
  uint spot = c.x * 0x8da6b343u ^ c.y * 0xd8163841u;
  uint k = scramble(spot ^ drawing);
  if (float(scramble(spot + 0x7ed55d16u ^ drawing) & 1023u) < uGrain.z * 1024.0) k = scramble(spot ^ frame);
  return (float((k & 65535u) + (k >> 16u)) / 65535.0 - 1.0) * 2.4494897;
}

// grains spread by a gaussian 0.55 of their size: at size 1 neighbouring pixels share about a third
float grainAt(vec2 px, uint drawing, uint frame) {
  vec2 q = px / max(uGrain.y, 0.25);
  vec2 home = floor(q);
  float sum = 0.0, energy = 0.0;
  for (int j = -1; j <= 1; j++) {
    for (int i = -1; i <= 1; i++) {
      vec2 cell = home + vec2(float(i), float(j));
      vec2 dd = q - cell - 0.5;
      float w = exp(-1.65 * dot(dd, dd));
      sum += w * grainCell(cell, drawing, frame);
      energy += w * w;
    }
  }
  return sum * inversesqrt(energy);
}

// smooth value noise, -1..1, cells one unit across
float lump(vec2 p, uint salt, uint drawing) {
  vec2 base = floor(p), f = p - base;
  vec2 s = f * f * (3.0 - 2.0 * f);
  float v[4];
  for (int k = 0; k < 4; k++) {
    uvec2 c = uvec2(ivec2(base) + ivec2(k % 2, k / 2) + 65536);
    v[k] = float(scramble(c.x * 0x27d4eb2fu ^ scramble(c.y ^ salt) ^ drawing) >> 8u) / 8388608.0 - 1.0;
  }
  return mix(mix(v[0], v[1], s.x), mix(v[2], v[3], s.x), s.y);
}

// the airbrush: three octaves 12, 6 and 3 px across
float mottleAt(vec2 px, uint drawing) {
  return 0.55 * lump(px / 12.0, 0x51u, drawing) + 0.3 * lump(px / 6.0, 0xa3u, drawing) + 0.15 * lump(px / 3.0, 0xf7u, drawing);
}

void main() {
  float a = texture(uScene, vSt).a;
  vec3 c = texture(uImg, vSt).rgb / (a < 0.999 ? max(a, 1e-4) : 1.0);   // edges against a clear background
  if (uLook.x > 0.0) {
    vec3 g = texture(uGlow, vSt).rgb;
    float gy = dot(g, LUMA);
    c += uLook.x * max(vec3(gy) + 1.25 * (g - vec3(gy)), 0.0);   // the glow keeps, even lifts, its colour
  }
  if (uLook.y > 0.0) c = mix(c, rollOff(c), uLook.y);
  if (uLook.z > 0.0) {
    vec2 aspect = vec2(uFull.x / uFull.y, 1.0);
    float r = length((vSt - 0.5) * aspect) / length(0.5 * aspect);   // 0 in the middle, 1 in a corner
    c *= 1.0 - uLook.z * smoothstep(0.2, 1.0, r * r);
  }
  vec3 s = linearToOutputTexel(vec4(max(c, 0.0), 1.0)).rgb;
  uint drawing = drawingKey();
  if (uGrain.x > 0.0) s += uGrain.x * toneWeight(dot(clamp(s, 0.0, 1.0), LUMA)) * grainAt(gl_FragCoord.xy, drawing, frameKey());
  if (uLook.w > 0.0) s *= 1.0 + 0.08 * uLook.w * mottleAt(gl_FragCoord.xy, drawing);
  gl_FragColor = vec4(clamp(s, 0.0, 1.0) * a, a);                 // premultiplied, as the canvas expects
}`;

// a full-screen pass: its own scene holding one triangle; uniforms are filled per frame
function pass(frag, uniforms) {
  const material = new THREE.ShaderMaterial({ vertexShader: SCREEN, fragmentShader: frag, uniforms, depthTest: false,
    depthWrite: false, blending: THREE.NoBlending, toneMapped: false });
  const shape = new THREE.BufferGeometry();
  shape.setDrawRange(0, 3);
  shape.boundingSphere = new THREE.Sphere(new THREE.Vector3(), Infinity);
  const mesh = new THREE.Mesh(shape, material);
  mesh.frustumCulled = false;
  const scene = new THREE.Scene();
  scene.add(mesh);
  return { u: material.uniforms, scene, material, dispose() { material.dispose(); shape.dispose(); } };
}

const tex = () => ({ value: null });
const vec2 = () => ({ value: new THREE.Vector2() });

// a linear colour from '#rrggbb', 0xrrggbb or [r, g, b] in 0..1 (all sRGB), whatever three.js's colour management
// is set to
function linear(c) {
  let v;
  if (Array.isArray(c)) v = c.slice(0, 3).map(Number);
  else if (typeof c === 'number') v = [(c >> 16) & 255, (c >> 8) & 255, c & 255].map(x => x / 255);
  else {
    const s = String(c).trim().replace(/^#/, '');
    const hex = s.length === 3 ? s.split('').map(ch => ch + ch).join('') : s;
    if (!/^[0-9a-f]{6}$/i.test(hex)) throw new Error(`post3d: not a colour: ${c}`);
    v = [0, 2, 4].map(i => parseInt(hex.slice(i, i + 2), 16) / 255);
  }
  return new THREE.Vector3(...v.map(x => (x > 0.04045 ? Math.pow((x + 0.055) / 1.055, 2.4) : x / 12.92)));
}

export function chain(renderer, opts = {}) {
  const o = { ...POST3D, ...opts };
  const blank = new THREE.Camera();                     // the passes place their own triangle; any camera will do
  const msaa = renderer.getContext().getContextAttributes()?.antialias ? 4 : 0;
  const P = {};                                         // passes, built on first use
  let T = null;                                         // targets for the current drawing-buffer size
  const size = new THREE.Vector2();

  const get = (name, frag, uniforms) => (P[name] ??= pass(frag, uniforms()));   // uniforms: made once, on first use
  const run = (p, target) => { renderer.setRenderTarget(target); renderer.render(p.scene, blank); };
  // the passes that rebuild positions from the depth buffer share three uniforms
  const withDepth = extra => ({ uDepth: tex(), uUnproject: { value: new THREE.Matrix4() }, uFull: vec2(), ...extra });
  const aim = (p, camera) => {
    p.u.uDepth.value = T.scene.depthTexture;
    p.u.uUnproject.value.copy(camera.projectionMatrixInverse);
    p.u.uFull.value.set(T.w, T.h);
    return p;
  };

  function targets(w, h) {
    if (T && T.w === w && T.h === h) return T;
    if (T) T.all.forEach(t => t.dispose());
    const all = [];
    const make = (tw, th, extra = {}) => {
      const t = new THREE.WebGLRenderTarget(Math.max(1, tw), Math.max(1, th), { type: THREE.HalfFloatType,
        minFilter: THREE.LinearFilter, magFilter: THREE.LinearFilter, depthBuffer: false, generateMipmaps: false, ...extra });
      all.push(t);
      return t;
    };
    const hw = Math.ceil(w / 2), hh = Math.ceil(h / 2);
    T = { w, h, all,
      scene: make(w, h, { depthBuffer: true, samples: msaa, depthTexture: new THREE.DepthTexture(w, h) }),
      occ: make(hw, hh, { format: THREE.RedFormat }), soft: make(hw, hh, { format: THREE.RedFormat }),
      prep: make(w, h), lens: make(w, h), down: [], up: [] };
    for (let i = 0, lw = hw, lh = hh; i < 6; i++, lw = Math.ceil(lw / 2), lh = Math.ceil(lh / 2)) {
      T.down.push(make(lw, lh));
      T.up.push(i < 5 ? make(lw, lh) : null);           // the smallest level is only read
    }
    return T;
  }

  function draw(scene, camera, frame = 0) {
    guard(renderer);
    const hold = Math.max(1, Math.round(o.hold || 1));
    const drawing = frame - (((frame % hold) + hold) % hold);
    setFrame(drawing, true);                             // the chain's hold, not each material's
    const lens = o.dof && o.dof.aperture > 0 ? o.dof : null;
    const on = { ao: o.ao > 0, dof: !!lens, bloom: o.bloom > 0, shoulder: o.shoulder > 0, vignette: o.vignette > 0,
      grain: o.grain > 0, mottle: o.mottle > 0 };
    if (!Object.values(on).some(Boolean)) {             // nothing to do: the plain render, pixel for pixel
      renderer.setRenderTarget(null);
      renderer.render(scene, camera);
      return;
    }
    renderer.getDrawingBufferSize(size);
    const w = Math.round(size.x), h = Math.round(size.y);
    const t = targets(w, h);

    renderer.setRenderTarget(t.scene);
    if (!renderer.autoClear) renderer.clear();
    renderer.render(scene, camera);

    const autoClear = renderer.autoClear;
    renderer.autoClear = false;                          // every pass covers every pixel
    try {
      let img = t.scene.texture;
      if (on.ao) {
        const a = aim(get('occlude', OCCLUDE, () => withDepth({ uProject: { value: new THREE.Matrix4() },
          uRadius: { value: 0.6 } })), camera);
        a.u.uProject.value.copy(camera.projectionMatrix);
        a.u.uRadius.value = o.aoRadius;
        run(a, t.occ);
        const s = aim(get('soften', SOFTEN, () => withDepth({ uOcc: tex() })), camera);
        s.u.uOcc.value = t.occ.texture;
        run(s, t.soft);
      }
      if (on.ao || on.dof) {
        const p = aim(get('prepare', PREPARE, () => withDepth({ uScene: tex(), uOcc: tex(),
          uTint: { value: new THREE.Vector3(1, 1, 1) }, uAo: { value: 0 }, uLens: { value: new THREE.Vector4() } })), camera);
        p.u.uScene.value = img;
        p.u.uOcc.value = t.soft.texture;
        p.u.uTint.value.copy(linear(o.aoTint));
        p.u.uAo.value = on.ao ? o.ao : 0;
        if (lens) p.u.uLens.value.set(lens.focus, lens.aperture * 0.01 * h, 0.04 * h, 1);
        else p.u.uLens.value.set(1, 0, 0, 0);
        run(p, t.prep);
        img = t.prep.texture;
      }
      if (on.dof) {
        const l = get('lens', LENS, () => ({ uSharp: tex(), uFull: vec2() }));
        l.u.uSharp.value = img;
        l.u.uFull.value.set(w, h);
        run(l, t.lens);
        img = t.lens.texture;
      }
      let glow = null;
      if (on.bloom) {
        const g0 = get('glowStart', GLOW_START, () => ({ uSrc: tex(), uStep: vec2(), uThreshold: { value: 0.75 } }));
        g0.u.uSrc.value = img;
        g0.u.uStep.value.set(1 / w, 1 / h);
        g0.u.uThreshold.value = o.bloomThreshold;
        run(g0, t.down[0]);
        const gd = get('glowDown', GLOW_DOWN, () => ({ uSrc: tex(), uStep: vec2() }));
        for (let i = 1; i < 6; i++) {
          gd.u.uSrc.value = t.down[i - 1].texture;
          gd.u.uStep.value.set(1 / t.down[i - 1].width, 1 / t.down[i - 1].height);
          run(gd, t.down[i]);
        }
        const gu = get('glowUp', GLOW_UP, () => ({ uSmall: tex(), uLevel: tex(), uStep: vec2() }));
        let small = t.down[5];
        for (let i = 4; i >= 0; i--) {
          gu.u.uSmall.value = small.texture;
          gu.u.uLevel.value = t.down[i].texture;
          gu.u.uStep.value.set(1 / small.width, 1 / small.height);
          run(gu, t.up[i]);
          small = t.up[i];
        }
        glow = t.up[0].texture;
      }
      const f = get('finish', FINISH, () => ({ uImg: tex(), uGlow: tex(), uScene: tex(), uFull: vec2(),
        uLook: { value: new THREE.Vector4() }, uGrain: { value: new THREE.Vector4() }, uClock: vec2() }));
      f.u.uImg.value = img;
      f.u.uGlow.value = glow ?? img;
      f.u.uScene.value = t.scene.texture;
      f.u.uFull.value.set(w, h);
      f.u.uLook.value.set(on.bloom ? o.bloom / 6 : 0, on.shoulder ? o.shoulder : 0, on.vignette ? o.vignette : 0,
        on.mottle ? o.mottle : 0);                       // the six glow levels are summed: a sixth each
      f.u.uGrain.value.set(on.grain ? o.grain : 0, o.grainSize, Math.min(1, Math.max(0, o.flicker)), 0);
      f.u.uClock.value.set(drawing, frame);
      run(f, null);
    } finally {
      renderer.autoClear = autoClear;
    }
  }

  draw.opts = o;
  draw.dispose = () => { if (T) T.all.forEach(x => x.dispose()); Object.values(P).forEach(p => p.dispose()); T = null; };
  return draw;
}
