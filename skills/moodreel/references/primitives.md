# Primitives and recipes

The kit (`kit/`, copied into every project and film) and how the common materials and moves of flat 2D styles are
built with it. Write a style's own modules next to these when it needs more (a woodcut carver, a riso print pass);
§10 of its STYLE.md points to them.

## Modules

| Module | Exports |
|---|---|
| `stage.js` | `stage({...})`, `texts(fn)` |
| `eases.js` | `ease(name)` (GSAP names, or `bezier(x1,y1,x2,y2)` as the kit writes a style's own curve), `bezier(x1, y1, x2, y2)` |
| `core.js` | `clamp`, `lerp`, `tween(t, at, dur, ease)`, `value(t, at, dur, from, to, ease)`, `keys([[t, v, ease]…])`, `stagger(at, interval, i)`, `step(t, rate)`, `rng(seed)`, `hash(n)`, `noise1(x)` |
| `texture.js` | `paper(w, h, {color, mottle, fibres, seed})`, `grain(g, amount, frame, {ground})`, `vignette(g, w, h, strength)`, `screen(g, {period, angle, color, dot})`, `scanlines(g, period, strength)`, `misregister(g, draw, layers)` |
| `text.js` | `fit(g, text, font, width)`, `wrap(g, text, width)`, `glyphs(g, text, x)` |
| `tokens.js`, `motion.js` | the style's measured values, `enter`, `exit`, `move` |

## Recipes

**Flat ground with paper.** `g.drawImage(paper(W, H, { color: PALETTE.ground, mottle: TEXTURE.mottle }), 0, 0)` once per
frame (cached); fibres only when the references show them.

**3D.** `const L = layer3d(W, H, { background, shadows: true })`; build meshes, lights and materials once into
`L.scene`; in draw, set every position, rotation and the camera from t (`L.look(orbit(t * speed, r, h), target)`;
no clocks, no AnimationMixer), then `L.draw(g)` and draw type on top. `L.toScreen([x, y, z])` gives the stage point
for a label pinned in the world. Flat shading (`flatShading: true`) for low-poly, `PCFSoftShadowMap` shadows from one
key light; everything renders the same every time on one machine.

**Brushwork.** Paint a static plate flat (plain shapes, value first), then `g.drawImage(repaint(plate, { key, cell,
fine, mark: 'dab' | 'stroke' }), 0, 0)`: coarse marks over the planes, fine ones along the edges, each along its edge
(cached, so a static plate costs nothing per frame). Marks being painted on screen are drawn live: `stroke(g, points,
{ width, profile, bristles, reveal })`, `ink(g, points, { wet, reveal })`, `crayon(g, points, { width, tooth })`,
`wash(g, polygon, { passes, jitter, pool })`. Lay them at `TEXTURE.brush.spacing` and turned by
`TEXTURE.brush.angle` when the references were measured; everything takes a seed.

**Pixel art.** `const P = pixels(...TEXTURE.pixel.native, TEXTURE.pixel.palette)`; draw with `P.rect`, `P.line`,
`P.disc`, `P.sprite(rows, legend, x, y)` and dithered gradients `P.shade(x, y, w, h, a, b, u)`, all in native pixels;
`P.present(g, { scale: TEXTURE.pixel.scale, table })` each frame. A palette fade or a colour-depth change is a table
(`reduce(palette, keep)`, `stepTable(n, ramps, ±1)`), never an alpha; the camera moves by `snap(x)`.

**Halftone fill.** `g.fillStyle = screen(g, { period: TEXTURE.halftone.period_px, angle: 45, color: PALETTE.ink })`,
then fill any path. Two screens at different angles overprinted with `misregister` give a two-colour print.

**Riso / screen-print misregistration.** `misregister(g, (g, ink) => { g.fillStyle = ink; g.fill(shape) },
[{ color: '#ff48b0', dx: 0, dy: 0 }, { color: '#ffe800', dx: 5, dy: 4 }])`; keep offsets fixed per shot (seeded), not
per frame, unless the style shimmers.

**Entrance (rise and fade).** `const p = enter(t, at, i); g.globalAlpha = p; y = y0 + (1 - p) * MOTION.enter.travel * H`.
For a scale-pop, `s = lerp(MOTION.enter.scale_from, 1, p)` with the style's back.out.

**Staggered group.** `items.forEach((it, i) => draw(it, enter(t, at, i)))`: `enter` applies `MOTION.stagger.interval`;
order the items as `MOTION.stagger.order` says (left-to-right, top-to-bottom).

**Exit.** `1 - exit(t, at)` as opacity, or a slide out through the frame edge; exits are usually shorter and ease-in.

**Wipe or mask reveal.** `g.save(); g.beginPath(); g.rect(x, y, w * tween(t, at, d, ease), h); g.clip(); draw(); g.restore()`.

**Line draw-on.** `g.setLineDash([len * p, len]); g.stroke(path)` with `p = tween(...)`, length from the path.

**Per-letter text.** `glyphs(g, text, x)` gives each glyph's centre; animate glyph `k` with `enter(t, at + k * 0.03)`.

**Counter.** `Math.round(count(t, at, 0, 4200)).toLocaleString()` (the kit's `count` runs on the references' counting
curve, `MOTION.count`, and its `format` says how they print numbers); without one, `value(t, at, d, 0, 4200, 'power3.out')`.
Report the final text in TEXTS.

**Camera push.** One transform for the world: `g.translate(W / 2 + panX, H / 2); g.scale(z, z); g.translate(-W / 2, -H / 2)`
with `z = value(t, at, d, 1, 1.12, 'sine.inOut')`; draw the ground oversized so the edges never show.

**Dissolve / dip.** Draw the outgoing shot, then the incoming one with `globalAlpha = tween(...)`; for a dip, a full-frame
rectangle of the dip colour whose alpha rises then falls around the cut.

**Ambient loop.** `y + MOTION.loop.y * loop(t)` for a bob, `1 + MOTION.loop.scale * loop(t)` for a pulse,
`g.rotate(t * MOTION.loop.rot * Math.PI / 180)` for a spin; offset `loop(t, period, i * 0.25)` per element so a row
doesn't move in lockstep. **Particles:** seed each dot's place and speed from `MOTION.particles` (speed p10-p90,
direction) and wrap it round the frame: `x = (x0 + vx * t) mod W`, so any frame stands alone.

**On twos.** `const tt = step(t, 12)` for drawings at 24 fps; the camera keeps `t`.
