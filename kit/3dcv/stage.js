// kit/3dcv/stage.js — ported from 3DCodeVerse (https://github.com/gaoypeng/3dcodeverse), awesome showcase
//   (https://huggingface.co/datasets/3dcodeverse/3dcodeverse-awesome-showcase): the 30-second film's code,
//   source src/core/stage.js, round r02, git blob 4edad7b791d3b8093a2725a86458f3b1618f6c9a.
// Licence: CC BY-NC-SA 4.0 (https://creativecommons.org/licenses/by-nc-sa/4.0/), see kit/3dcv/LICENSE.
//   Non-commercial use only; adaptations keep this licence. The rest of moodreel is MIT.
// Changes by moodreel (2026-11-08): film(), an adapter for moodreel's stage (kit/stage.js, whose render(t) is
//   synchronous), replaces the page boot and its query-string shot loader: several shots on one page, each with its
//   own ctx, scene and camera, sharing one renderer and one Post per supersampling factor; the renderer draws on an
//   offscreen canvas that is never added to the page; the global state a shot's init leaves (look.env's uniform
//   values; the renderer's tone mapping and exposure, shadow map, clear colour and alpha, output colour space,
//   clipping, viewport and scissor) is kept and put back before each of its frames, and every init starts from the
//   state before the first; a render that returns a Promise is an error; loadGLTF and the imports of the showcase's
//   film-specific modules (props, heroine, kit) removed (a film passes its own as extras); window.__ctx and the
//   gl.finish() after each frame dropped; three.js taken from ../three.js; the original header reworded; this header.
//
// Use, inside moodreel's stage (kit/3dcv/README.md in the repository has the details):
//   import { stage } from './kit/stage.js';
//   import * as cv from './kit/3dcv/stage.js';
//   const film = cv.film({ width: 1920, height: 1080, ss: 2, shots: [shotA, shotB], extras: {}, query: '' });
//   stage({ width: 1920, height: 1080, duration: 10, prepare: () => film.init(), draw: (g, t) => film.draw(g, t, 1920, 1080) });
// A shot is { id?, frames: [first, last] (global frames, 24 fps, n = 1 at t = 0), hold?, ss?, init?(ctx), render(ctx, n) }.

// stage.js — the runtime shots run in: renderer, deterministic time, RNG, easing, keyframe/spline tracks, camera rigs,
// shadow setup, the shot adapter, and the shared `ctx` every shot receives.
import { THREE } from '../three.js';
import * as look from './look.js';
import { Post, defaultPostParams } from './post.js';
import * as paint from './paint.js';
import * as text from './text.js';

import { FPS, frameTime, clamp, lerp, invLerp, remap, smoothstep, smootherstep, deg, mixValue, ease, rng, hash1, noise1, fbm1, track, spline, cameraRig } from './util.js';
export * from './util.js';

// ---------------------------------------------------------------------------------------------- lights & shadows
/**
 * setupShadows(light, { size=2048, extent=6 (ortho half-size, m), near=0.1, far=60, bias=-0.0004, normalBias=0.02,
 *                       radius=4 (soft radius in shadow texels for the look shader's PCF), target:[x,y,z] })
 * Directional lights: the shadow camera is centred on light.target.  The look shader samples the map with its own
 * soft Vogel PCF (16 taps, 24 when radius x shadowSoft x env shadowSoftMul > 3 texels), so keep renderer.shadowMap.type =
 * PCFShadowMap (the default here).  Use a near-white key colour: warm keys multiply in linear light and push skin to salmon.
 */
export function setupShadows(light, o = {}) {
  light.castShadow = true;
  const s = light.shadow;
  s.mapSize.set(o.size || 2048, o.size || 2048);
  s.bias = o.bias ?? -0.0004; s.normalBias = o.normalBias ?? 0.02; s.radius = o.radius ?? 4;
  const c = s.camera;
  if (c.isOrthographicCamera) { const e = o.extent || 6; c.left = -e; c.right = e; c.top = e; c.bottom = -e; }
  c.near = o.near ?? 0.1; c.far = o.far ?? 60; c.updateProjectionMatrix();
  if (o.target && light.target) { light.target.position.set(...o.target); light.target.updateMatrixWorld(); }
  s.needsUpdate = true;
  return light;
}
/**
 * keyLight(scene, { dir:[x,y,z] (direction the light TRAVELS FROM, i.e. light position relative to target),
 *   color, intensity=1, target:[x,y,z], shadow:{...setupShadows opts} | false }) -> DirectionalLight
 * The look shader treats the FIRST directional light as the key of its colour ramp (shadow-casting lights sort first).
 */
export function keyLight(scene, o = {}) {
  const L = new THREE.DirectionalLight(o.color ?? 0xffffff, o.intensity ?? 1);
  const t = new THREE.Vector3(...(o.target || [0, 0, 0])), d = new THREE.Vector3(...(o.dir || [-0.5, 1, 0.6])).normalize();
  L.position.copy(t).addScaledVector(d, o.distance || 20);
  L.target.position.copy(t);
  scene.add(L, L.target);
  if (o.shadow !== false) setupShadows(L, { ...(o.shadow || {}), target: o.target });
  return L;
}

// ---------------------------------------------------------------------------------------------- loaders
async function loadTexture(url, { srgb = true } = {}) {
  const t = await new THREE.TextureLoader().loadAsync(url);
  if (srgb) t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

// ---------------------------------------------------------------------------------------------- global state
// What a shot can leave behind for the next one on the same page: the look env's uniform values (shared by every
// LookMaterial and sky) and the renderer's settings. keep() copies it, putBack() restores it in place.
const copyOf = v => (v && typeof v.clone === 'function' ? v.clone() : Array.isArray(v) ? v.slice() : v);
function keep(renderer) {
  const env = {};
  for (const [k, u] of Object.entries(look.env)) env[k] = copyOf(u.value);
  const sm = renderer.shadowMap;
  return {
    env, clear: renderer.getClearColor(new THREE.Color()), alpha: renderer.getClearAlpha(),
    toneMapping: renderer.toneMapping, exposure: renderer.toneMappingExposure, colorSpace: renderer.outputColorSpace,
    shadows: sm.enabled, shadowType: sm.type, shadowAuto: sm.autoUpdate, clipping: renderer.localClippingEnabled,
    autoClear: renderer.autoClear, viewport: renderer.getViewport(new THREE.Vector4()),
    scissor: renderer.getScissor(new THREE.Vector4()), scissorTest: renderer.getScissorTest(),
  };
}
function putBack(renderer, s) {
  for (const [k, v] of Object.entries(s.env)) {
    const u = look.env[k];
    if (u.value && typeof u.value.copy === 'function' && v && typeof v.copy === 'function') u.value.copy(v);
    else u.value = copyOf(v);
  }
  renderer.setRenderTarget(null);
  renderer.setClearColor(s.clear, s.alpha);
  renderer.toneMapping = s.toneMapping; renderer.toneMappingExposure = s.exposure; renderer.outputColorSpace = s.colorSpace;
  const sm = renderer.shadowMap;
  sm.enabled = s.shadows; sm.type = s.shadowType; sm.autoUpdate = s.shadowAuto;
  renderer.localClippingEnabled = s.clipping; renderer.autoClear = s.autoClear;
  renderer.setViewport(s.viewport); renderer.setScissor(s.scissor); renderer.setScissorTest(s.scissorTest);
}

// ---------------------------------------------------------------------------------------------- film: shots + ctx
/**
 * film({ width=1920, height=1080, ss=2, shots, extras={}, query='' }) -> film
 *   width/height: the WebGL canvas in output pixels; ss: supersampling for shots without their own ss; shots: shot
 *   modules (below); extras: merged into every ctx (a film's own modules); query: what ctx.query (URLSearchParams)
 *   reads. The flags the showcase's page took from its query string still work from it: hold=<n> (every shot's frames
 *   per drawing), ss=<n> (every shot's supersampling), nopost=1 (the post passes off), post=<json> (deep-merged over
 *   every draw's params).
 * A shot: { id?, frames: [first, last] (global frames, 24 fps, n = 1 at t = 0), hold? (2 = on twos), ss?,
 *   async init?(ctx) (build everything here, once), render(ctx, n) (synchronous; a pure function of n: draws with
 *   ctx.draw(scene, camera, params), or returns post params and ctx.scene / ctx.camera are drawn with them) }.
 *   init and render are called as methods of the shot (`this` is the shot).
 * film.init()            async: the renderer (offscreen canvas), one ctx per shot, each shot's init in order
 * film.frameOf(t)        global frame at t seconds: Math.floor(t * 24 + 1e-4) + 1
 * film.shotAt(n)         the shot whose frames hold n (the first one listed), or null
 * film.render(n)         draws global frame n into film.canvas; false when no shot holds n. With hold h the drawing
 *                        frame is n - n % h (never before the shot's first frame): look.setFrame and ctx.frame get it,
 *                        ctx.outFrame and post.outFrame get n (grain flicker moves on every output frame)
 * film.draw(g, t, w, h)  render(frameOf(t)), then g.drawImage(film.canvas, 0, 0, w, h); nothing is drawn when no shot
 *                        holds the frame
 * film.canvas, film.renderer, film.contexts (one ctx per shot, in order)
 */
export function film({ width = 1920, height = 1080, ss = 2, shots = [], extras = {}, query = '' } = {}) {
  shots.forEach((shot, i) => {
    const name = shot && shot.id ? `shot ${shot.id}` : `shot ${i}`;
    if (!shot || typeof shot.render !== 'function') throw new Error(`3dcv film: ${name} has no render()`);
    const f = shot.frames;
    if (!Array.isArray(f) || f.length !== 2 || !Number.isFinite(f[0]) || !Number.isFinite(f[1]) || f[0] > f[1]) {
      throw new Error(`3dcv film: ${name} needs frames: [first, last] (global frames, 1 at t = 0)`);
    }
  });
  const Q = new URLSearchParams(query);
  const qss = Q.get('ss') ? +Q.get('ss') : null, nopost = Q.get('nopost') === '1';
  const postOverride = Q.get('post') ? JSON.parse(Q.get('post')) : null;
  const canvas = document.createElement('canvas');
  canvas.width = width; canvas.height = height;
  const entries = [];
  let booting = null;

  const context = (shot, i, renderer, post) => {
    const first = shot.frames[0], last = shot.frames[1];
    const ctx = {
      THREE, renderer, post, look, paint, text,
      w: width, h: height, aspect: width / height, query: Q, shotId: shot.id ?? String(i), shot,
      FPS, frame: first,
      /** the real output frame being captured (= frame unless the shot holds drawings: hold 2 renders drawing n - n % 2);
       *  post grain.flicker re-seeds on it, so held pairs keep a faint shimmer. Use it for anything that should move on ones. */
      outFrame: first,
      /** global time (s) of frame n */ time: frameTime,
      /** shot-local time (s): 0 at the shot's first frame */ local: n => (n - first) / FPS,
      /** shot-local normalised progress 0..1 over shot.frames */ progress: n => clamp((n - first) / Math.max(1, last - first)),
      rng, hash1, noise1, fbm1, ease, track, spline, cameraRig, clamp, lerp, invLerp, remap, smoothstep, smootherstep, deg, mixValue,
      setupShadows, keyLight, loadTexture,
      scene: new THREE.Scene(), camera: new THREE.PerspectiveCamera(35, width / height, 0.05, 400),
      postParams: defaultPostParams(),
      _drawn: false,
      /** Render `scene` from `camera` through the post pipeline (params: see post.js) to the film's canvas. */
      draw(sc = ctx.scene, cam = ctx.camera, params = ctx.postParams) {
        if (cam.isPerspectiveCamera && Math.abs(cam.aspect - ctx.aspect) > 1e-6) { cam.aspect = ctx.aspect; cam.updateProjectionMatrix(); }
        if (nopost) params = { ...(params || {}), ao: { amount: 0 }, dof: { amount: 0 }, bloom: { strength: 0 }, grain: { amount: 0 }, vignette: { amount: 0 }, paint: { amount: 0 },
          highlight: { knee: 0.98 }, dither: { amount: 0 }, sharpen: 0, soften: 0, diffuse: { mix: 0, add: 0 }, mist: { amount: 0 } };
        post.render(sc, cam, params || {}, ctx.frame, postOverride);
        ctx._drawn = true;
      },
      /** Render a scene to an HDR texture (pre-post), e.g. for portal composites. Returns a THREE.Texture valid this frame. */
      renderToTexture(sc, cam, slot = 'aux0', params = null) { return post.renderToTexture(sc, cam, slot, params); },
    };
    return Object.assign(ctx, extras);
  };

  const boot = async () => {
    const renderer = new THREE.WebGLRenderer({ canvas, antialias: false, alpha: false, preserveDrawingBuffer: true, powerPreference: 'high-performance' });
    renderer.setPixelRatio(1);
    renderer.setSize(width, height, false);
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.NoToneMapping;
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFShadowMap;
    renderer.shadowMap.autoUpdate = true;
    const start = keep(renderer);                     // every shot's init starts from this, as on a page of its own
    const posts = new Map();
    for (let i = 0; i < shots.length; i++) {
      const shot = shots[i], s = qss ?? shot.ss ?? ss;
      if (!posts.has(s)) posts.set(s, new Post(renderer, width, height, s));
      const post = posts.get(s), ctx = context(shot, i, renderer, post);
      putBack(renderer, start);
      if (shot.init) await shot.init(ctx);
      // Precompile so the first captured frame does not pay shader compile in odd states.
      try { renderer.compile(ctx.scene, ctx.camera); } catch (e) { /* scenes may be built lazily */ }
      const hold = Math.max(1, +(Q.get('hold') || shot.hold || 1));
      entries.push({ shot, ctx, post, hold, state: keep(renderer) });
      F.contexts.push(ctx);
    }
    F.renderer = renderer;
  };

  const F = {
    canvas, renderer: null, contexts: [], width, height,
    init: () => booting || (booting = boot()),
    frameOf: t => Math.floor(t * FPS + 1e-4) + 1,
    shotAt: n => shots.find(s => n >= s.frames[0] && n <= s.frames[1]) || null,
    render(n) {
      if (!F.renderer) throw new Error('3dcv film: render() before init() has finished');
      const e = entries.find(x => n >= x.shot.frames[0] && n <= x.shot.frames[1]);
      if (!e) return false;
      const { shot, ctx, post, hold } = e;
      // animation on twos: frame n renders its drawing frame n - n % hold (clamped to the shot's first frame)
      const d = hold > 1 ? Math.max(shot.frames[0], n - (n % hold)) : n;
      putBack(F.renderer, e.state);
      ctx.frame = d; ctx.outFrame = n; post.outFrame = n;
      ctx._drawn = false;
      look.setFrame(d);
      const ret = shot.render(ctx, d);
      if (ret && typeof ret.then === 'function') {
        throw new Error(`3dcv film: the render of shot ${ctx.shotId} returned a Promise; moodreel's render(t) is synchronous, so a shot's render must be too (load and build in init)`);
      }
      if (!ctx._drawn) ctx.draw(ctx.scene, ctx.camera, ret || ctx.postParams);
      return true;
    },
    draw(g, t, w = width, h = height) {
      const drawn = F.render(F.frameOf(t));
      if (drawn) g.drawImage(canvas, 0, 0, w, h);
      return drawn;
    },
  };
  return F;
}
