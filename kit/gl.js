// The GPU layer: full-screen shader passes into HDR (linear, half-float) targets, Canvas 2D layers sent up as
// textures, thousands of anti-aliased hairlines per frame (2D pixels or 3D with a camera), a GLSL library (hashes,
// simplex noise, fbm, curl, 2D/3D signed distances, smooth union, engraving hatch, a heat ramp) and a film post
// (bloom pyramid, halation, chromatic fringe, tone shoulder, vignette, shake and zoom). For what a 2D canvas can't
// draw at 60 fps: ray-marched bodies, lensing, line fields of 10k-200k segments, engraving that follows a surface.
//
//   import { gpu } from './kit/gl.js';
//   const G = gpu(1920, 1080);
//   const scene = G.pass(`uniform float uT; void main() { fragColor = vec4(heat(0.5 + 0.5 * snoise(vUv * 4.0 + uT)), 1.0); }`,
//                        { uT: { value: 0 } });
//   const hdr = G.rt();
//   draw: (g, t) => { scene.u.uT.value = t; scene.render(hdr); G.post(hdr.texture, { bloom: 0.6 }); G.show(g); }
//
// Colours in shaders are linear and may pass 1 (that is what blooms); the post writes sRGB. Palette colours are
// constants C_<NAME> (gpu({ palette }) adds or replaces them). Everything is set from t: no state between frames.
//
// Adapted from mexicat/pdoom-video (MIT, Copyright (c) 2026 Giacomo Magnanini): engine/gl.ts, engine/lines.ts,
// engine/glsl/common.ts and engine/post.ts, at output scale 1. The simplex noise is Ashima Arts / Stefan Gustavson's
// (MIT). See NOTICE.
import { THREE } from './three.js';

export { THREE };

export const PALETTE = { ink: '#0A0A0B', ink2: '#151517', graphite: '#5E5B57', ash: '#9C978F', bone: '#EEE9DF',
  signal: '#FF4D12', ember: '#FF8A3D', blood: '#C21D0B', acid: '#D8FF3C' };

export function linear(hex) {
  const n = parseInt(hex.replace('#', ''), 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255].map(v => {
    const s = v / 255;
    return s <= 0.04045 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4;
  });
}

const v3 = c => `vec3(${c.map(x => x.toFixed(5)).join(',')})`;

// the GLSL library, with the palette as linear constants C_INK, C_BONE, ...
export function glsl(palette = PALETTE) {
  const pal = { ...PALETTE, ...palette };
  return /* glsl */ `
#define PI 3.14159265359
#define TAU 6.28318530718
#define PX_SCALE 1.0
#define FRAG_PX (gl_FragCoord.xy)
${Object.entries(pal).map(([k, v]) => `const vec3 C_${k.toUpperCase()} = ${v3(linear(v))};`).join('\n')}

// rotated-grid supersample offset k (0..3) within one pixel, in px
vec2 rgss(int k) { return k == 0 ? vec2(0.125, -0.375) : k == 1 ? vec2(0.375, 0.125) : k == 2 ? vec2(-0.125, 0.375) : vec2(-0.375, -0.125); }
float sat(float x) { return clamp(x, 0.0, 1.0); }
vec3 sat(vec3 x) { return clamp(x, 0.0, 1.0); }
float remap(float x, float a, float b, float c, float d) { return c + (d - c) * sat((x - a) / (b - a)); }
mat2 rot2(float a) { float c = cos(a), s = sin(a); return mat2(c, -s, s, c); }
float luma(vec3 c) { return dot(c, vec3(0.2126, 0.7152, 0.0722)); }

// hashes
float hash11(float p) { p = fract(p * .1031); p *= p + 33.33; p *= p + p; return fract(p); }
float hash12(vec2 p) { vec3 p3 = fract(vec3(p.xyx) * .1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }
vec2 hash22(vec2 p) { vec3 p3 = fract(vec3(p.xyx) * vec3(.1031, .1030, .0973)); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.xx + p3.yz) * p3.zy); }
float hash13(vec3 p3) { p3 = fract(p3 * .1031); p3 += dot(p3, p3.zyx + 31.32); return fract((p3.x + p3.y) * p3.z); }
vec3 hash33(vec3 p3) { p3 = fract(p3 * vec3(.1031, .1030, .0973)); p3 += dot(p3, p3.yxz + 33.33); return fract((p3.xxy + p3.yxx) * p3.zyx); }

// simplex noise (Ashima Arts / Stefan Gustavson, MIT)
vec3 _mod289(vec3 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
vec4 _mod289(vec4 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
vec2 _mod289(vec2 x) { return x - floor(x * (1.0 / 289.0)) * 289.0; }
vec3 _permute(vec3 x) { return _mod289(((x * 34.0) + 10.0) * x); }
vec4 _permute(vec4 x) { return _mod289(((x * 34.0) + 10.0) * x); }
vec4 _taylorInvSqrt(vec4 r) { return 1.79284291400159 - 0.85373472095314 * r; }
float snoise(vec2 v) {
  const vec4 C = vec4(0.211324865405187, 0.366025403784439, -0.577350269189626, 0.024390243902439);
  vec2 i = floor(v + dot(v, C.yy)); vec2 x0 = v - i + dot(i, C.xx);
  vec2 i1 = (x0.x > x0.y) ? vec2(1.0, 0.0) : vec2(0.0, 1.0);
  vec4 x12 = x0.xyxy + C.xxzz; x12.xy -= i1; i = _mod289(i);
  vec3 p = _permute(_permute(i.y + vec3(0.0, i1.y, 1.0)) + i.x + vec3(0.0, i1.x, 1.0));
  vec3 m = max(0.5 - vec3(dot(x0, x0), dot(x12.xy, x12.xy), dot(x12.zw, x12.zw)), 0.0);
  m = m * m; m = m * m;
  vec3 x = 2.0 * fract(p * C.www) - 1.0; vec3 h = abs(x) - 0.5; vec3 ox = floor(x + 0.5); vec3 a0 = x - ox;
  m *= 1.79284291400159 - 0.85373472095314 * (a0 * a0 + h * h);
  vec3 g; g.x = a0.x * x0.x + h.x * x0.y; g.yz = a0.yz * x12.xz + h.yz * x12.yw;
  return 130.0 * dot(m, g);
}
float snoise(vec3 v) {
  const vec2 C = vec2(1.0 / 6.0, 1.0 / 3.0); const vec4 D = vec4(0.0, 0.5, 1.0, 2.0);
  vec3 i = floor(v + dot(v, C.yyy)); vec3 x0 = v - i + dot(i, C.xxx);
  vec3 g = step(x0.yzx, x0.xyz); vec3 l = 1.0 - g; vec3 i1 = min(g.xyz, l.zxy); vec3 i2 = max(g.xyz, l.zxy);
  vec3 x1 = x0 - i1 + C.xxx; vec3 x2 = x0 - i2 + C.yyy; vec3 x3 = x0 - D.yyy;
  i = _mod289(i);
  vec4 p = _permute(_permute(_permute(i.z + vec4(0.0, i1.z, i2.z, 1.0)) + i.y + vec4(0.0, i1.y, i2.y, 1.0)) + i.x + vec4(0.0, i1.x, i2.x, 1.0));
  float n_ = 0.142857142857; vec3 ns = n_ * D.wyz - D.xzx;
  vec4 j = p - 49.0 * floor(p * ns.z * ns.z); vec4 x_ = floor(j * ns.z); vec4 y_ = floor(j - 7.0 * x_);
  vec4 x = x_ * ns.x + ns.yyyy; vec4 y = y_ * ns.x + ns.yyyy; vec4 h = 1.0 - abs(x) - abs(y);
  vec4 b0 = vec4(x.xy, y.xy); vec4 b1 = vec4(x.zw, y.zw);
  vec4 s0 = floor(b0) * 2.0 + 1.0; vec4 s1 = floor(b1) * 2.0 + 1.0; vec4 sh = -step(h, vec4(0.0));
  vec4 a0 = b0.xzyw + s0.xzyw * sh.xxyy; vec4 a1 = b1.xzyw + s1.xzyw * sh.zzww;
  vec3 p0 = vec3(a0.xy, h.x); vec3 p1 = vec3(a0.zw, h.y); vec3 p2 = vec3(a1.xy, h.z); vec3 p3 = vec3(a1.zw, h.w);
  vec4 norm = _taylorInvSqrt(vec4(dot(p0, p0), dot(p1, p1), dot(p2, p2), dot(p3, p3)));
  p0 *= norm.x; p1 *= norm.y; p2 *= norm.z; p3 *= norm.w;
  vec4 m = max(0.5 - vec4(dot(x0, x0), dot(x1, x1), dot(x2, x2), dot(x3, x3)), 0.0); m = m * m;
  return 105.0 * dot(m * m, vec4(dot(p0, x0), dot(p1, x1), dot(p2, x2), dot(p3, x3)));
}
float fbm(vec2 p, int oct) { float s = 0.0, a = 0.5; for (int i = 0; i < 8; i++) { if (i >= oct) break; s += a * snoise(p); p = rot2(0.6) * p * 2.03 + 11.7; a *= 0.5; } return s; }
float fbm(vec3 p, int oct) { float s = 0.0, a = 0.5; for (int i = 0; i < 8; i++) { if (i >= oct) break; s += a * snoise(p); p = p * 2.03 + 11.7; a *= 0.5; } return s; }
// curl of 2D noise: a divergence-free flow field
vec2 curl2(vec2 p, float t) {
  float e = 0.01;
  float n1 = snoise(vec3(p + vec2(0.0, e), t)), n2 = snoise(vec3(p - vec2(0.0, e), t));
  float n3 = snoise(vec3(p + vec2(e, 0.0), t)), n4 = snoise(vec3(p - vec2(e, 0.0), t));
  return vec2(n1 - n2, -(n3 - n4)) / (2.0 * e);
}

// signed distances
float sdCircle(vec2 p, float r) { return length(p) - r; }
float sdBox(vec2 p, vec2 b) { vec2 d = abs(p) - b; return length(max(d, 0.0)) + min(max(d.x, d.y), 0.0); }
float sdSegment(vec2 p, vec2 a, vec2 b) { vec2 pa = p - a, ba = b - a; float h = sat(dot(pa, ba) / dot(ba, ba)); return length(pa - ba * h); }
float sdSphere(vec3 p, float r) { return length(p) - r; }
float sdBox3(vec3 p, vec3 b) { vec3 q = abs(p) - b; return length(max(q, 0.0)) + min(max(q.x, max(q.y, q.z)), 0.0); }
float sdCapsule(vec3 p, vec3 a, vec3 b, float r) { vec3 pa = p - a, ba = b - a; float h = sat(dot(pa, ba) / dot(ba, ba)); return length(pa - ba * h) - r; }
float sdTorus(vec3 p, vec2 t) { vec2 q = vec2(length(p.xz) - t.x, p.y); return length(q) - t.y; }
float smin(float a, float b, float k) { float h = sat(0.5 + 0.5 * (b - a) / k); return mix(b, a, h) - k * h * (1.0 - h); }
float smax(float a, float b, float k) { return -smin(-a, -b, k); }

// hairlines: 1 - smoothstep(a, b, d) with d in px (or a, b multiples of fwidth)
float pxLine(float d, float a, float b) { return 1.0 - smoothstep(a, b, d); }
// a line of half-width hw with a linear ramp of aa
float rampLine(float d, float hw, float aa) { return sat((hw - d) / aa + 0.5); }
// anti-aliased fill and stroke of a distance field (d < 0 inside)
float aaFill(float d) { float w = fwidth(d); return 1.0 - smoothstep(-w, w, d); }
float aaStroke(float d, float wd) { float w = fwidth(d); return 1.0 - smoothstep(wd * 0.5 - w, wd * 0.5 + w, abs(d)); }
// engraving hatch: lines at integer u, each wider with darkness (0 paper, 1 full ink); ink coverage 0..1.
// hatchD takes du from the caller, for a coordinate whose fwidth lies (an angle that wraps)
float hatchD(float u, float darkness, float du) {
  float f = abs(fract(u) - 0.5), half_w = 0.5 * sat(darkness), aa = max(du, 1e-4);
  return 1.0 - smoothstep(half_w - aa, half_w + aa, 0.5 - f);
}
float hatch(float u, float darkness) { return hatchD(u, darkness, fwidth(u)); }
// engraving with a hairline that is always there and a cross-hatch in the deep shadows
float engrave(vec2 uv, float darkness, float freq, float angle) {
  float a = hatch((rot2(angle) * uv * freq).y, darkness * 1.1);
  float b = hatch((rot2(1.1) * uv * freq).y, sat(darkness * 2.0 - 1.1));
  return max(a, b);
}

vec3 toSRGB(vec3 c) { return mix(12.92 * c, 1.055 * pow(max(c, 0.0), vec3(1.0 / 2.4)) - 0.055, step(0.0031308, c)); }
vec3 toLinear(vec3 c) { return mix(c / 12.92, pow((c + 0.055) / 1.055, vec3(2.4)), step(0.04045, c)); }
// the heat ramp: 0 ink, 0.5 signal, 1 white-hot
vec3 heat(float x) {
  x = sat(x);
  vec3 c = mix(C_INK, C_BLOOD, smoothstep(0.0, 0.3, x));
  c = mix(c, C_SIGNAL, smoothstep(0.25, 0.55, x));
  c = mix(c, C_EMBER, smoothstep(0.55, 0.8, x));
  return mix(c, vec3(1.0, 0.93, 0.85), smoothstep(0.8, 1.0, x));
}
`;
}

// identity below 0.72, a smooth exponential shoulder above, very bright values going to white
export const SHOULDER = /* glsl */ `
vec3 shoulder(vec3 x) {
  const float k = 0.72;
  vec3 y = mix(x, k + (1.0 - k) * (1.0 - exp(-(x - k) / (1.0 - k))), step(k, x));
  float over = max(max(x.r, x.g), x.b);
  return mix(y, vec3(1.0), smoothstep(2.0, 12.0, over) * 0.85);
}`;

export const POST = { exposure: 1, bloom: 0.55, bloomThreshold: 0.85, bloomKnee: 0.5, bloomRadius: 0.75, halation: 0.25,
  ca: 1.2, grain: 0, vignette: 0.35, fade: 0, flash: 0, invert: 0, shake: [0, 0], zoom: 1, time: 0 };

const LINE_VERT = /* glsl */ `
precision highp float;
in vec3 position;          // quad corner: x 0..1 along the segment, y -1..1 across
in vec3 iA; in vec3 iB;    // the segment's ends
in vec4 iColor;            // linear rgb (may pass 1), alpha
in float iWidth;           // px, or world units with worldWidth
uniform mat4 projectionMatrix; uniform mat4 modelViewMatrix;
uniform vec2 res; uniform bool screen2D; uniform bool worldWidth; uniform float widthScale;
out vec2 vLocal; out float vLen; out float vHalfW; out vec4 vColor;
vec4 toClip(vec3 p) {
  if (screen2D) return vec4(p.x / res.x * 2.0 - 1.0, 1.0 - p.y / res.y * 2.0, p.z, 1.0);
  return projectionMatrix * modelViewMatrix * vec4(p, 1.0);
}
void main() {
  vec4 ca = toClip(iA), cb = toClip(iB);
  if (ca.w <= 0.0 || cb.w <= 0.0) { gl_Position = vec4(2.0, 2.0, 2.0, 1.0); return; }   // behind the camera
  vec2 sa = ca.xy / ca.w * 0.5 * res, sb = cb.xy / cb.w * 0.5 * res;
  float w = iWidth * widthScale;
  if (worldWidth && !screen2D) {
    float pa = projectionMatrix[1][1] * 0.5 * res.y / ca.w, pb = projectionMatrix[1][1] * 0.5 * res.y / cb.w;
    w = iWidth * widthScale * mix(pa, pb, position.x);
  }
  float hw = max(w * 0.5, 0.35) + 1.0;
  vec2 d = sb - sa; float len = length(d);
  vec2 dir = len > 1e-4 ? d / len : vec2(1.0, 0.0), nrm = vec2(-dir.y, dir.x);
  float along = mix(-hw, len + hw, position.x);
  vec2 p = sa + dir * along + nrm * position.y * hw;
  gl_Position = vec4(p / (0.5 * res), mix(ca.z / ca.w, cb.z / cb.w, position.x), 1.0);
  vLocal = vec2(along, position.y * hw);
  vLen = len; vHalfW = max(w * 0.5, 0.35);
  vColor = iColor * vec4(1.0, 1.0, 1.0, min(1.0, w / 0.7));    // lines thinner than 0.7 px fade instead of shrinking
}`;

const LINE_FRAG = /* glsl */ `
precision highp float;
in vec2 vLocal; in float vLen; in float vHalfW; in vec4 vColor;
out vec4 fragColor;
void main() {
  float x = clamp(vLocal.x, 0.0, vLen);
  float d = length(vec2(vLocal.x - x, vLocal.y)) - vHalfW;     // a capsule, in px
  float a = clamp(0.5 - d, 0.0, 1.0) * vColor.a;
  if (a <= 0.0) discard;
  fragColor = vec4(vColor.rgb * a, a);
}`;

export function gpu(width = 1920, height = 1080, { palette = {} } = {}) {
  const canvas = document.createElement('canvas');
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: false, preserveDrawingBuffer: true, alpha: false });
  renderer.setPixelRatio(1);
  renderer.setSize(width, height, false);
  renderer.autoClear = false;
  const GLSL = glsl(palette);
  const tri = new THREE.BufferGeometry();
  tri.setAttribute('position', new THREE.Float32BufferAttribute([-1, -1, 0, 3, -1, 0, -1, 3, 0], 3));
  const ortho = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);

  // an HDR target (count > 1: several outputs, for a G-buffer)
  const rt = (w = width, h = height, o = {}) => new THREE.WebGLRenderTarget(Math.max(1, Math.round(w)), Math.max(1, Math.round(h)),
    { type: THREE.HalfFloatType, format: THREE.RGBAFormat, minFilter: THREE.LinearFilter, magFilter: THREE.LinearFilter,
      depthBuffer: false, ...o });

  // a full-screen pass: `frag` declares its uniforms and main() writing fragColor; vUv (0..1) and the library are in
  // scope. raw: true takes a whole shader of its own (several outputs: layout(location = n) out vec4 ...)
  function pass(frag, uniforms = {}, { blend = 'none', raw = false } = {}) {
    const mat = new THREE.RawShaderMaterial({
      glslVersion: THREE.GLSL3, uniforms, depthTest: false, depthWrite: false,
      vertexShader: 'precision highp float;\nin vec3 position;\nout vec2 vUv;\nvoid main() { vUv = position.xy * 0.5 + 0.5; gl_Position = vec4(position.xy, 0.0, 1.0); }',
      fragmentShader: raw ? frag : `precision highp float;\nprecision highp int;\nin vec2 vUv;\nout vec4 fragColor;\n${GLSL}\n${frag}`,
    });
    blending(mat, blend);
    const scene = new THREE.Scene(), mesh = new THREE.Mesh(tri, mat);
    mesh.frustumCulled = false;
    scene.add(mesh);
    return { mat, u: mat.uniforms,
      render(target = null, clear = false) { renderer.setRenderTarget(target); if (clear) renderer.clear(); renderer.render(scene, ortho); } };
  }

  // a Canvas 2D surface sent up as an sRGB texture (decoded to linear when sampled); upload() after drawing
  function layer(w = width, h = height, { srgb = true } = {}) {
    const c = document.createElement('canvas');
    c.width = w; c.height = h;
    const ctx = c.getContext('2d');
    const texture = new THREE.CanvasTexture(c);
    texture.colorSpace = srgb ? THREE.SRGBColorSpace : THREE.NoColorSpace;
    texture.minFilter = THREE.LinearFilter;
    texture.generateMipmaps = false;
    return { canvas: c, ctx, texture, w, h,
      clear(color) {
        ctx.setTransform(1, 0, 0, 1, 0, 0);
        ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over'; ctx.filter = 'none'; ctx.shadowBlur = 0;
        if (color) { ctx.fillStyle = color; ctx.fillRect(0, 0, w, h); } else ctx.clearRect(0, 0, w, h);
      },
      upload() { texture.needsUpdate = true; return texture; } };
  }

  // hairlines: capsule segments with linear colours, in 2D px (y down) or in 3D through a camera
  function lines(capacity, { screen2D = true, worldWidth = false, blend = 'add', depthTest = false } = {}) {
    const geo = new THREE.InstancedBufferGeometry();
    geo.setAttribute('position', new THREE.BufferAttribute(new Float32Array([0, -1, 0, 1, -1, 0, 1, 1, 0, 0, 1, 0]), 3));
    geo.setIndex([0, 1, 2, 0, 2, 3]);
    const A = new Float32Array(capacity * 3), B = new Float32Array(capacity * 3), C = new Float32Array(capacity * 4), Wd = new Float32Array(capacity);
    const attrs = [[A, 3, 'iA'], [B, 3, 'iB'], [C, 4, 'iColor'], [Wd, 1, 'iWidth']].map(([arr, n, name]) => {
      const at = new THREE.InstancedBufferAttribute(arr, n);
      at.setUsage(THREE.DynamicDrawUsage);
      geo.setAttribute(name, at);
      return at;
    });
    const mat = new THREE.RawShaderMaterial({ glslVersion: THREE.GLSL3, vertexShader: LINE_VERT, fragmentShader: LINE_FRAG,
      uniforms: { res: { value: new THREE.Vector2(width, height) }, screen2D: { value: screen2D }, worldWidth: { value: worldWidth },
        widthScale: { value: 1 } },
      transparent: true, depthWrite: false, depthTest });
    blending(mat, blend);
    const mesh = new THREE.Mesh(geo, mat);
    mesh.frustumCulled = false;
    const scene = new THREE.Scene();
    scene.add(mesh);
    const cam2d = new THREE.OrthographicCamera(0, width, 0, height, -1, 1);
    const L = { count: 0, capacity,
      clear() { L.count = 0; },
      seg(ax, ay, az, bx, by, bz, w, r, g, b, a = 1) {
        if (L.count >= capacity) return;
        const i = L.count++;
        A.set([ax, ay, az], i * 3); B.set([bx, by, bz], i * 3); C.set([r, g, b, a], i * 4); Wd[i] = w;
      },
      seg2(ax, ay, bx, by, w, rgb, a = 1) { L.seg(ax, ay, 0, bx, by, 0, w, rgb[0], rgb[1], rgb[2], a); },
      polyline(pts, w, rgb, a = 1) {
        for (let i = 1; i < pts.length; i++) {
          const p = pts[i - 1], q = pts[i];
          L.seg(p.x, p.y, p.z ?? 0, q.x, q.y, q.z ?? 0, w, rgb[0], rgb[1], rgb[2], a);
        }
      },
      // draw into `target` (not cleared); a camera for 3D
      render(target = null, camera = null, widthScale = 1) {
        for (const at of attrs) { at.needsUpdate = true; at.clearUpdateRanges(); at.addUpdateRange(0, L.count * at.itemSize); }
        geo.instanceCount = L.count;
        mat.uniforms.widthScale.value = widthScale;
        mat.uniforms.res.value.set(target ? target.width : width, target ? target.height : height);
        renderer.setRenderTarget(target);
        renderer.render(scene, camera ?? cam2d);
      } };
    return L;
  }

  // draw a texture over a target: blend mode, opacity, tint, uv scale (> 1 shows it smaller) and offset
  const comps = {};
  function comp(tex, target = null, { mode = 'normal', opacity = 1, tint = [1, 1, 1], scale = [1, 1], offset = [0, 0], premult = mode !== 'multiply' } = {}) {
    const p = comps[mode] ??= pass(/* glsl */ `
      uniform sampler2D tex; uniform float opacity; uniform vec3 tint; uniform vec4 uvXform; uniform bool premult;
      void main() {
        vec2 uv = (vUv - 0.5) * uvXform.xy + 0.5 + uvXform.zw;
        if (uv.x < 0.0 || uv.x > 1.0 || uv.y < 0.0 || uv.y > 1.0) discard;
        vec4 c = texture(tex, uv);
        c.rgb *= tint;
        if (premult) c.rgb *= c.a;
        fragColor = c * opacity;
      }`, { tex: { value: null }, opacity: { value: 1 }, tint: { value: new THREE.Vector3() }, uvXform: { value: new THREE.Vector4() },
      premult: { value: true } }, { blend: mode });
    p.u.tex.value = tex; p.u.opacity.value = opacity; p.u.tint.value.set(...tint);
    p.u.uvXform.value.set(scale[0], scale[1], offset[0], offset[1]); p.u.premult.value = premult;
    p.render(target);
  }

  function clear(target = null, rgb = [0, 0, 0], a = 1) {
    renderer.setRenderTarget(target);
    renderer.setClearColor(new THREE.Color().setRGB(rgb[0], rgb[1], rgb[2], THREE.LinearSRGBColorSpace), a);
    renderer.clear(true, true, true);
  }

  // the film post: HDR linear in, sRGB out (to `out`, or the canvas that show() puts on the stage)
  const MIPS = 7, mips = [], ups = [];
  for (let i = 0, w = width >> 1, h = height >> 1; i < MIPS; i++, w >>= 1, h >>= 1) {
    mips.push(rt(Math.max(2, w), Math.max(2, h)));
    ups.push(rt(Math.max(2, w), Math.max(2, h)));
  }
  let P = null;
  function post(src, params = {}, out = null) {
    const p = { ...POST, ...params };
    P ??= {
      pre: pass(/* glsl */ `
        uniform sampler2D src; uniform vec2 texel; uniform float threshold, knee;
        void main() {      // 4-tap box down, soft threshold on the brightest channel
          vec3 c = texture(src, vUv + texel * vec2(-1, -1)).rgb + texture(src, vUv + texel * vec2(1, -1)).rgb
                 + texture(src, vUv + texel * vec2(-1, 1)).rgb + texture(src, vUv + texel * vec2(1, 1)).rgb;
          c = min(c * 0.25, vec3(40.0));
          float l = max(c.r, max(c.g, c.b)), rq = clamp(l - threshold + knee, 0.0, 2.0 * knee);
          rq = rq * rq / (4.0 * knee + 1e-5);
          fragColor = vec4(c * max(rq, l - threshold) / max(l, 1e-5), 1.0);
        }`, { src: { value: null }, texel: { value: new THREE.Vector2() }, threshold: { value: 1 }, knee: { value: 0.5 } }),
      down: pass(/* glsl */ `
        uniform sampler2D src; uniform vec2 texel;
        vec3 T(vec2 o) { return texture(src, vUv + texel * o).rgb; }
        void main() {      // 13-tap down (Jimenez 2014)
          vec3 a = T(vec2(-2, -2)), b = T(vec2(0, -2)), c = T(vec2(2, -2)), d = T(vec2(-1, -1)), e = T(vec2(1, -1));
          vec3 f = T(vec2(-2, 0)), g = T(vec2(0)), h = T(vec2(2, 0)), i = T(vec2(-1, 1)), j = T(vec2(1, 1));
          vec3 k = T(vec2(-2, 2)), l = T(vec2(0, 2)), m = T(vec2(2, 2));
          fragColor = vec4((d + e + i + j) * 0.125 + (a + b + g + f + b + c + h + g + f + g + l + k + g + h + m + l) * 0.03125, 1.0);
        }`, { src: { value: null }, texel: { value: new THREE.Vector2() } }),
      up: pass(/* glsl */ `
        uniform sampler2D src, prev; uniform vec2 texel; uniform float radius;
        void main() {      // 9-tap tent up, added to the level below
          vec2 o = texel * radius;
          vec3 s = texture(src, vUv - o).rgb + 2.0 * texture(src, vUv + vec2(0, -o.y)).rgb + texture(src, vUv + vec2(o.x, -o.y)).rgb
            + 2.0 * texture(src, vUv + vec2(-o.x, 0)).rgb + 4.0 * texture(src, vUv).rgb + 2.0 * texture(src, vUv + vec2(o.x, 0)).rgb
            + texture(src, vUv + vec2(-o.x, o.y)).rgb + 2.0 * texture(src, vUv + vec2(0, o.y)).rgb + texture(src, vUv + o).rgb;
          fragColor = vec4(texture(prev, vUv).rgb + s / 16.0, 1.0);
        }`, { src: { value: null }, prev: { value: null }, texel: { value: new THREE.Vector2() }, radius: { value: 1 } }),
      final: pass(/* glsl */ `
        uniform sampler2D src, bloomTex, haloTex;
        uniform float exposure, bloom, halation, ca, grain, vignette, fade, flash, time, zoom, invert;
        uniform vec2 shake, res;
        ${SHOULDER}
        void main() {
          vec2 uv = (vUv - 0.5) / zoom + 0.5 - shake / res, dc = uv - 0.5;
          float r2 = dot(dc * vec2(res.x / res.y, 1.0), dc * vec2(res.x / res.y, 1.0));
          vec2 off = dc * r2 * ca / res.x * 4.0;
          vec3 col = vec3(texture(src, uv + off).r, texture(src, uv).g, texture(src, uv - off).b);
          col += texture(bloomTex, uv).rgb * bloom;
          col += vec3(1.0, 0.18, 0.04) * luma(texture(haloTex, uv).rgb) * halation;
          col = shoulder(col * exposure);
          col = mix(col, vec3(0.8515) - col * 0.84, invert);
          col += C_BONE * flash;
          col *= mix(1.0, smoothstep(0.95, 0.25, length(dc * vec2(1.0, 0.8))), vignette);
          vec3 s = toSRGB(sat(col * (1.0 - fade)));
          float lm = luma(s), g1 = hash12(gl_FragCoord.xy + fract(time * 13.37) * 1000.0) - 0.5;
          float g2 = hash12(floor(gl_FragCoord.xy / 2.0) + fract(time * 7.13) * 1000.0) - 0.5;
          s += (g1 * 0.6 + g2 * 0.4) * grain * (0.55 + 1.2 * lm * (1.0 - lm));
          fragColor = vec4(sat(s + (hash12(gl_FragCoord.xy * 1.37 + time) - 0.5) / 255.0), 1.0);
        }`, Object.fromEntries([...['src', 'bloomTex', 'haloTex'].map(k => [k, { value: null }]),
        ...['exposure', 'bloom', 'halation', 'ca', 'grain', 'vignette', 'fade', 'flash', 'time', 'zoom', 'invert'].map(k => [k, { value: 0 }]),
        ['shake', { value: new THREE.Vector2() }], ['res', { value: new THREE.Vector2(width, height) }]])),
    };
    P.pre.u.src.value = src; P.pre.u.texel.value.set(1 / width, 1 / height);
    P.pre.u.threshold.value = p.bloomThreshold; P.pre.u.knee.value = p.bloomKnee;
    P.pre.render(mips[0]);
    for (let i = 1; i < MIPS; i++) {
      P.down.u.src.value = mips[i - 1].texture; P.down.u.texel.value.set(1 / mips[i - 1].width, 1 / mips[i - 1].height);
      P.down.render(mips[i]);
    }
    let prev = mips[MIPS - 1].texture;
    for (let i = MIPS - 2; i >= 0; i--) {
      const small = i === MIPS - 2 ? mips[MIPS - 1] : ups[i + 1];
      P.up.u.src.value = prev; P.up.u.prev.value = mips[i].texture;
      P.up.u.texel.value.set(1 / small.width, 1 / small.height); P.up.u.radius.value = 0.5 + p.bloomRadius;
      P.up.render(ups[i]);
      prev = ups[i].texture;
    }
    const f = P.final.u;
    f.src.value = src; f.bloomTex.value = ups[0].texture; f.haloTex.value = ups[3].texture;
    for (const k of ['exposure', 'halation', 'ca', 'grain', 'vignette', 'fade', 'flash', 'time', 'zoom', 'invert']) f[k].value = p[k];
    f.bloom.value = p.bloom / 3;                        // the pyramid sums about three levels' worth
    f.shake.value.set(p.shake[0], p.shake[1]);
    P.final.render(out);
  }

  return { THREE, renderer, canvas, width, height, GLSL, rt, pass, layer, lines, comp, clear, post,
    // put the canvas (what post() drew with out = null) on the 2D stage
    show(g, x = 0, y = 0, w = width, h = height) { g.drawImage(canvas, x, y, w, h); } };
}

function blending(mat, mode) {
  if (mode === 'none') { mat.blending = THREE.NoBlending; return; }
  if (mode === 'replace') { mat.blending = THREE.NoBlending; return; }
  mat.blending = THREE.CustomBlending;
  mat.transparent = true;
  mat.blendEquation = THREE.AddEquation;
  const F = THREE;
  const set = (s, d, sa, da) => Object.assign(mat, { blendSrc: s, blendDst: d, blendSrcAlpha: sa, blendDstAlpha: da });
  if (mode === 'normal') set(F.OneFactor, F.OneMinusSrcAlphaFactor, F.OneFactor, F.OneMinusSrcAlphaFactor);
  else if (mode === 'add') set(F.OneFactor, F.OneFactor, F.ZeroFactor, F.OneFactor);
  else if (mode === 'screen') set(F.OneFactor, F.OneMinusSrcColorFactor, F.ZeroFactor, F.OneFactor);
  else if (mode === 'multiply') set(F.DstColorFactor, F.OneMinusSrcAlphaFactor, F.ZeroFactor, F.OneFactor);
  else if (mode === 'max') { mat.blendEquation = THREE.MaxEquation; set(F.OneFactor, F.OneFactor, F.OneFactor, F.OneFactor); }
}
