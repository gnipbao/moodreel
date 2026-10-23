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
