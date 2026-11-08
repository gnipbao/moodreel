# Drawing the film

## The page contract

A film is a folder with `index.html` loading `main.js`, which uses `kit/stage.js`:

```js
import { stage, texts } from './kit/stage.js';
stage({ width: 1920, height: 1080, duration: 20, background: PALETTE.ground,
        fonts: ['800 120px Archivo'], images: { logo: 'logo.png' },
        draw: (g, t, assets) => { /* paint the whole frame at second t */ } });
```

`stage` sets `window.DUR`, `window.render(t)` and `window.READY`, scales design units to any output size of the same
aspect, and waits for fonts and images. Render:

```bash
moodreel render still films/<name> 1 4.5 9 --size 1920x1080 --out films/<name>/out/stills
moodreel render video films/<name> --fps 30 --size 1920x1080 --workers 3 --out films/<name>/out/video.mp4
```

## Determinism (the renderer relies on it)

- The frame comes from `t` alone: no `Date.now()`, no `Math.random()` (use `rng(seed)` and `hash()` from kit/core.js),
  no state carried from the previous frame, no `requestAnimationFrame`. Any frame can be rendered alone, in any order,
  by any worker; review stills at chosen times depend on it.
- Expensive things that don't change (a paper texture, a glyph atlas, a background) are built once and cached
  (texture.js does this), keyed by their parameters.
- Animate on twos where the style says so: `const tt = step(t, fps / 2)` for the drawings; keep the camera smooth.

## Using the kit

- Colours, sizes and surfaces from `kit/tokens.js`; timing from `kit/motion.js` (`enter(t, at, i)`, `exit`, `move`, or
  `tween(t, at, MOTION.enter.duration, MOTION.enter.ease)` from core.js). A number typed into main.js that the style
  already has is a number that will drift.
- Surfaces after the picture: `vignette`, then `scanlines`, then `grain(g, TEXTURE.grain, frame, { ground: PALETTE.ground })`
  last (in device pixels).
- Type: `fit()` for a size that fills a width, `wrap()` for lines (CJK-aware), `glyphs()` for per-letter timing. Load
  every face through `fonts:` so the first frame isn't drawn with a fallback.
- One world-to-screen transform for the camera (translate, scale, rotate about a centre); anything that follows a
  subject goes through it.

## Text the reading check can see

Every line of text on screen is reported by `texts(t => [...])`: `{ id, text, x0, y0, x1, y1 }` in output pixels, from
the moment it is fully shown. `moodreel film check` reads it (through `moodreel render texts`) and fails any line that
leaves before it can be read. Report the whole text from its first full frame (a typewriter reports the full line
once it is complete).

## Review before rendering everything

Stills at the beats from TREATMENT.md, side by side, before the full render: framing, contrast, text size, collisions.
Fix in code, re-render the stills. Then render the film and watch it at full speed once.

## An illustrated 3D film

3D that reads as illustration (painted materials, characters on twos under a camera on ones) is three modules on top
of `kit/three.js`, each listed in kit/README.md: `kit/look3d.js` (a colour-ramp material and the clock of the
drawings), `kit/post3d.js` (the painterly finish) and `kit/figure.js` (characters built with `moodreel model build`,
below).

```js
import { stage } from './kit/stage.js';
import { layer3d } from './kit/three.js';
import * as look3d from './kit/look3d.js';
import * as post3d from './kit/post3d.js';
import * as figure from './kit/figure.js';

const FPS = 24, HOLD = 2;
const L = layer3d(1920, 1080, { background: '#e9dcc8', toneMapping: 'none' });    // pixels = the ramps' colours
const finish = post3d.chain(L.renderer, { hold: HOLD, ao: 1, dof: { focus: 4, aperture: 0.4 }, bloom: 0.4,
  shoulder: 1, vignette: 0.25, grain: 0.03, mottle: 0.3 });
const ramps = {};
let fig;

stage({ width: 1920, height: 1080, duration: 8,
  prepare: async () => {
    fig = await figure.load('hero/build/hero.json');
    fig.setMaterial((part, name) => (ramps[name] ??= look3d.ramp(fig.materials[name])));   // one per material
    L.scene.add(fig.root);
  },
  draw: (g, t) => {
    const tt = look3d.held(t, FPS, HOLD);                                         // the figure on twos
    fig.setPose('stand');
    fig.setExpression({ nod: 0.5 + 0.5 * Math.sin(2 * tt) });
    L.look([4 * Math.sin(0.2 * t), 1.5, 4 * Math.cos(0.2 * t)], [0, 1.1, 0]);      // the camera on ones
    finish(L.scene, L.camera, look3d.frameOf(t, FPS));
    g.drawImage(L.canvas, 0, 0, 1920, 1080);                                      // not L.draw(g): no passes
  } });
```

- **The ramp, not lights.** `look3d.ramp({ lit, mid, shade, light, ... })` reads no lights: a surface takes `shade`,
  `mid` or `lit` by how far it turns to `light` (a direction in the world), through wrapped diffuse
  d = clamp((N·L + wrap) / (1 + wrap), 0, 1): exactly `shade` at 0, exactly `lit` at 1, each step `softness` wide in
  d, the colours blended in gamma 2 so the steps read evenly. Three things go on top: an accent along the shadow edge
  (`termTint` at strength `terminator`; left out, `mid` flushed toward rose), a form shade washed over the side turned
  away (`formTint`, at most half covering), and a stipple. Its dots sit on a lattice in the object's rest-pose space,
  about one output pixel across, so they ride the surface as it bends and as the camera moves (under a pan of 12 px a
  frame: NCC 1.000 aligned with the motion, 0.001 aligned with the screen). Each dot moves its pixel about one step
  along the ramp, so dots gather at the terminator and in shadow, and every one is a colour the ramp has. With
  `toneMapping: 'none'` the pixels are the ramp's colours (ΔE2000 0.33 on the lit pole, 0.00 in shadow). Sample each
  material's three colours from the reference on two frames or more; make one material per material name and share
  it between the parts that use it.
- **The finish.** `post3d.chain(renderer, opts)` returns `finish(scene, camera, frame)`. It renders into its own
  target and runs, in order: tinted occlusion (`ao`, `aoTint`, `aoRadius`), depth of field (`dof: { focus, aperture }`),
  bloom (`bloom`, `bloomThreshold`), a shoulder that keeps hue, a vignette, then grain (`grain`, `grainSize`, `flicker`)
  and an airbrush mottle on the encoded picture. Put the result on the stage with `g.drawImage(L.canvas, ...)`:
  `L.draw(g)` would render the scene again without the passes. 0 turns a pass off, and with every pass off the chain
  is the plain render, pixel for pixel. Grain sits in the mid tones (on a test card its spread was 8.4 levels in the
  mid tones, 6.1 in the shadows, 1.4 in the highlights). 1080p with every pass on takes 7.7 ms a frame (median, in
  headless Chrome).
- **A grade per shot.** `finish.opts` holds the options the chain reads. Set the ones the shots change at the top of
  every `draw`, from the shot `t` falls in (`Object.assign(finish.opts, GRADE[shotAt(t)])`), never only when a shot
  starts: a frame may be rendered alone, by any worker.
- **On twos.** Pose characters at `look3d.held(t, fps, 2)`, the time of the drawing on screen; move the camera with
  `t`; give the chain the same `hold`. The chain then steps the stipple's boil and the grain on frame - frame % hold:
  in a still scene frames 2k and 2k + 1 are the same pixel for pixel, and the next drawing changes (by 4.5 levels on
  average on the test scene). `flicker` redraws a share of the grain on every frame, for a reference whose grain moves
  under held drawings (`moodreel probe` says which: its `still` is the least change between neighbouring frames).
  Without a chain, call `look3d.setFrame(look3d.frameOf(t, fps))` once a frame; each material then steps on its own
  `hold`.
- **Shader errors stop the render.** three.js logs a shader that fails to compile and goes on drawing black.
  `look3d.guard(renderer)` (the chain calls it) throws instead, with the compile log and the source lines it names, so
  the render fails on that frame.

### Characters carved from distance fields (SDF)

A character is a Python spec: every part a signed distance field (SDF), meshed, bound to bones and checked before any
shot uses it. `moodreel/model3d/mannequin.py` (the built-in `mannequin`, a jointed figure 1.72 m tall, 33 parts, three
poses) uses every field a spec can have and is the one to copy:

```python
from moodreel.model3d import sdf
from moodreel.model3d.build import Part, along

NAME = "hero"                                                     # names the files: hero.json, hero.bin
BONES = {"hips": (None, (0, 0.96, 0)), "spine": ("hips", (0, 1.06, 0)), "chest": ("spine", (0, 1.24, 0)), ...}
skull = sdf.ellipsoid((0, 1.628, 0), (0.077, 0.098, 0.091))                     # metres
jaw = sdf.ellipsoid((0, 1.568, 0.028), (0.057, 0.05, 0.06))
PARTS = {"head": Part(sdf.smooth_union(skull, jaw, 0.04), "head", "skin", step=0.004),
         "belly": Part(sdf.ellipsoid((0, 1.1, 0), (0.13, 0.115, 0.09)), "spine", "coat",
                       weights=along("spine", "chest", (0, 1.04, 0), (0, 1.2, 0))), ...}
POSES = {"stand": {...}, "write": {"spine": (6, 0, 0), "r_forearm": (0, 0, 40), ...}}      # bone: XYZ Euler degrees
COLLIDE = [("r_forearm", "torso"), ("r_hand", "torso"), ...]                              # measured in every pose
LANDMARKS = {"chin": (0, 1.48, 0.09), ...}                                                # named rest-pose points
MATERIALS = {"skin": {"lit": "#efe6d8", "mid": "#d2c4ae", "shade": "#8c7d69"}, ...}         # look3d.ramp's options
EXPRESSIONS = {"nod": {"neck": (6, 0, 0), "head": (10, 0, 0)}}                            # weighted at run time
```

- Metres, y up; the figure faces +z and its left is +x. Bones carry no rotation at rest, only a position (the joint).
- Parts are fields from `moodreel.model3d.sdf`: `sphere`, `capsule`, `round_cone` (a tapered limb), `ellipsoid`,
  `round_box`, `cylinder`, `torus`, placed (`translate`, `rotate`, `place`, `frame`, `mirror`, `scale`) and combined
  (`union`, `smooth_union`, `smooth_difference`, `smooth_intersection`, `offset`, `shell`). A part follows one bone,
  or `{bone: weight}`; `weights=along(first, second, start, end)` hands it from one bone to the next across a joint,
  so it bends there instead of breaking.
- POSES and EXPRESSIONS turn bones by XYZ Euler degrees about their rest axes (three.js's order); an expression's
  angles are weighted and added on top of the pose. `moodreel.model3d.skin.reach` solves an arm onto a point for a
  pose, the same two-bone solve as `fig.reach`. COLLIDE names the pairs whose penetration is measured, LANDMARKS are
  named rest-pose points, and MATERIALS is copied into the json for `fig.materials`.

Then three commands:

```bash
moodreel model build hero/hero.py              # hero/build/hero.json and hero.bin, for kit/figure.js
moodreel model check hero/hero.py --model hero/build/hero.json --json hero/check.json
moodreel model sheet hero/build/hero.json --out hero/sheet.png --poses stand,write
```

- `moodreel model build` meshes every part by surface nets, with one vertex for each piece of surface in a cell so
  every mesh closes, pulls each vertex onto the surface by Newton steps (a sphere's vertices land within 1e-12 m of
  it) and takes the normals from the field's gradient. The mannequin builds in 0.48 s: 146,540 vertices, 292,948
  triangles.
- `moodreel model check` prints JSON. Every part closed: each edge on two faces, an Euler characteristic of 2 for one
  piece (a part that broke in two at too coarse a step reads 4). `floating`: every part outside the biggest group of
  parts in contact, where parts within 2 mm touch, measured in each other's fields (move a hand 5 cm off its wrist and
  the hand and its five fingers are named). For each pose, the deepest penetration of each COLLIDE pair in mm, read in
  the second part's field in its bone's rest frame (an arm turned 30 mm into the torso reads 30.0 mm). Build until
  every part is closed, nothing floats and no pose sinks a part more than a few millimetres.
- `moodreel model sheet` renders the views across (front, three-quarter, side, back) and the poses down, labelled, in
  plain clay at one scale with a ground line at y = 0, so feet that float or sink show. `sheet.json` beside it gives
  each cell's box and the metres per pixel. The same model gives the same sheet, pixel for pixel. Read it beside the
  reference's frames of the character.

**Proportions in units of one feature.** Pixels change with distance and lens; ratios don't. Pick one feature of the
reference that is sharp and keeps its size from frame to frame (a glasses ring's outer diameter, an eye's width), and
measure every proportion you build to in that unit (eye spacing, face width at the eyes, chin to eye line, head
height), each on two frames or more. Keep a ratio only when its spread (largest minus smallest, over the mean) is
within 15 %. Put LANDMARKS on the same points of the model and compute the same ratios from them, so the figure is
checked against numbers rather than by eye.

### The showcase's own engine: kit/3dcv

`kit/3dcv/` is the engine of 3DCodeVerse's showcase itself, ported from round r02 of its film's code (look3d and
post3d are moodreel's own reading of it). It has `look.js` (the ramp material with its stipple, tuned presets, a
graded sky), `post.js` (the post chain), `paint.js` (seeded painted textures), `text.js` (stroke lettering without
fonts), `util.js` (seeded random numbers, eases, keyframe tracks, splines, camera rigs) and `stage.js`, where the
runtime the showcase's shots ran in became `film()`, an adapter for the stage. kit/3dcv/README.md (in Chinese) lists
the API and every field of ctx. Unlike the rest of the kit it is CC BY-NC-SA 4.0, not MIT (the last point below).

**Which to reach for.** look3d and post3d by default: they are MIT, `ramp()` reads no lights (the light's direction
sits on the material), the chain's options are flat numbers, and figure.js characters take ramps as above. kit/3dcv
when a non-commercial film should have the showcase's own picture, built the way the showcase built it: its tuned
presets (`look.preset(name, overrides)`; skin, hair, cloth, clay, floor, paper, glass, silver and glow among them),
its graded `skyDome()`, and stages the MIT chain doesn't have (a motion smear, barrel and fisheye lenses up to a wide
render on cube faces, an anisotropic Kuwahara pass, `renderToTexture` for one scene composited into another). Its
materials follow the scene's first directional light (shadow casters sort first), so every shot needs a near-white
key (`ctx.keyLight`). Both engines can sit in one film; they share kit/three.js.

A film lists its shot modules in `cv.film()` and gives the stage two calls:

```js
import { stage } from './kit/stage.js';
import { THREE } from './kit/three.js';
import * as cv from './kit/3dcv/stage.js';
import * as look from './kit/3dcv/look.js';

const W = 1920, H = 1080;

const lantern = {                                     // global frames 1-120: 5 s at 24 fps
  id: 'lantern', frames: [1, 120], hold: 2,
  init(ctx) {                                         // once, before any frame; keep handles on `this`
    ctx.keyLight(ctx.scene, { dir: [0.4, 1, 0.7], shadow: { size: 1024, extent: 3 } });
    const ground = new THREE.Mesh(new THREE.CircleGeometry(4, 64), look.preset('floor'));
    ground.rotation.x = -Math.PI / 2;
    this.lamp = new THREE.Mesh(new THREE.CylinderGeometry(0.3, 0.36, 0.8, 48), look.preset('paper'));
    ctx.scene.add(ground, this.lamp);
    look.shadows(ctx.scene);                          // every mesh so far casts and receives
    ctx.scene.add(look.skyDome());                    // the sky after, so it casts nothing
    this.rise = ctx.track([[1, 0.4], [120, 1.6]]);
    this.cam = ctx.cameraRig({ pos: [[1, [0, 1.2, 4.5]], [120, [1.2, 1.8, 3.6]]], target: [0, 0.9, 0] });
  },
  render(ctx, n) {                                    // n: the drawing on screen (held on twos)
    this.lamp.position.y = this.rise(n);              // the lantern on twos
    this.cam.apply(ctx.camera, ctx.outFrame);         // the camera on ones
    return { bloom: { strength: 0.5 }, grain: { amount: 0.03 } };   // post params; the adapter draws ctx.scene
  },
};

const film = cv.film({ width: W, height: H, shots: [lantern] });
stage({ width: W, height: H, duration: 5, prepare: () => film.init(), draw: (g, t) => film.draw(g, t, W, H) });
```

`film.init()` goes in `prepare`: it is async and builds one WebGL renderer on a canvas kept off the page and a ctx per
shot, then runs each shot's `init` in the order listed. `film.draw(g, t, w, h)` renders the frame t falls in and draws
it onto the stage, whose 2D canvas stays the only one on the page. No import map is needed: kit/3dcv takes three.js
from kit/three.js. Import from `kit/three.js` in main.js (or in a file under `shots/` or `lib/`) even when the shots
only use `ctx.THREE`: `film check` and `film deliver` put a missing three.js back in kit/vendor/ only for a film that
names it.

- **A shot module** is a plain object. `frames: [first, last]` (global frames at 24 fps, frame 1 at t = 0) and
  `render(ctx, n)` are required; `id` (its `ctx.shotId`), `hold`, `ss` (supersampling, 1 to 3; the film's default is
  2) and `init(ctx)` are optional. Both methods are called on the shot, so `this` holds its handles. `init` runs once
  and may be async: load and build there. `render` must be synchronous, as the stage's `render(t)` is (a returned
  Promise throws), and a pure function of n: set everything that moves on every frame, with `ctx.rng(seed)` in place
  of `Math.random` and no `Date`. It either draws with `ctx.draw(scene, camera, params)`, or returns post params,
  deep-merged over `defaultPostParams()` for that draw only, and the adapter draws `ctx.scene` through `ctx.camera` (a
  35° perspective camera); returning nothing draws with `ctx.postParams`. `extras` in `cv.film()` adds the film's own
  modules to every ctx.
- **One frame clock.** The shots count frames at 24 fps whatever the film's own rate (`film.frameOf(t)` is
  `Math.floor(t * 24 + 1e-4) + 1`), so make the film at 24 fps (`moodreel film new <name> --style <style> --fps 24`,
  or `"fps": 24` in film.json); at 30 fps some frames of the shots would show twice. Where shot ranges overlap, the
  shot listed first wins; on a frame no shot covers, `film.draw` draws nothing.
- **On twos.** With `hold: 2`, frame n shows drawing d = max(first, n − n % 2): `render` is called with d, so frames
  2k and 2k + 1 show the same drawing, and the stipple's boil and the grain are seeded from d (once every
  `grain.hold` frames, 2 by default, so once a drawing). Two things still move on every output frame: whatever is
  set from `ctx.outFrame` (the camera above, on ones under a lantern on twos), and the `grain.flicker` share of the
  grain (0.1 by default). With `flicker: 0` a held pair is the same pixel for pixel; at 0.3 the pair differs by
  between 0.02 and 2 levels on average while nothing in it moves (tests/test_3dcv.py). The film's `query` overrides
  every shot: `hold=1` puts them all on ones, `ss=1` drafts faster, `nopost=1` shows the materials without the post,
  `post=<json>` merges over every draw's params.
- **Each frame stands alone.** Shots change shared state: the look env that every material and the sky read, and the
  renderer's tone mapping, exposure, shadow map, clear colour and the rest. The adapter starts every shot's `init` from
  the renderer's first state, keeps the state that init leaves, and puts it back before each of that shot's frames.
  So a frame comes out the same pixel for pixel rendered twice, after another shot, or in a film without that other
  shot (tests/test_3dcv.py). What the shot owns, its scene, camera and the objects on `this`, is still set from n in
  `render`.
- **The licence goes with the code.** kit/3dcv is CC BY-NC-SA 4.0, not MIT. A film that uses it carries that code
  under that licence: the film is for non-commercial use only, the files keep their headers and `kit/3dcv/LICENSE`,
  changes to them are shared under the same licence, and the film's CREDITS should name it (3DCodeVerse's showcase,
  CC BY-NC-SA 4.0, with its links). `moodreel film new` copies the whole kit into every new film (`moodreel wall make`
  does too), so a new film's `kit/3dcv/` arrives with its LICENSE whether the film imports it or not: a film meant
  for commercial use must neither keep nor use that folder. Code from kit/3dcv goes into no MIT file (another kit
  module, the Python package, a test, a film template); where MIT code needs the same effect, write it from the
  idea, as look3d and post3d were.
