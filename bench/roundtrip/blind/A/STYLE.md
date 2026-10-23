# Amber Phosphor — Style Prompt

Amber Phosphor · 琥珀荧光屏 · 1920×1080, 24 fps

> A one-colour CRT terminal drawn in code: monospaced capitals glow amber on a near-black brown screen striped by
> scanlines; text is typed, stamped and zoomed, and the tube itself powers on and off as punctuation.
> References (grammar only): amber monochrome monitors, boot logs, the CRT power-on line and power-off collapse.
> Take the one-hue phosphor logic, the character grid and the raster; never reuse the references' words or names.

## 1. Essence, and what it is not

1. **One hue, one tube.** One hue family (hue ~59–90°); 94 % near-black brown ground, ~4 % saturated. Light only
   ever means "the phosphor is lit".
2. **Scanlines over everything** (all references; every 4 px at 1280 wide, 6 design px at 1920), cutting the
   bright type, faint on the ground.
3. **A character grid.** Monospaced capitals, dot leaders and aligned columns; text hugs a 2.7 % left margin.
4. **Two lit levels.** Amber for ordinary text, a hotter cream for what matters (the status word, the title), and a
   soft bloom around the hot text (by eye).
5. **The screen is an actor.** Power-on (a line, a flash, a settle) and power-off (the raster collapses to a line,
   then a dot) are the style's transitions.

**Not** a green "hacker" terminal or falling-code rain (one amber hue, no green, nothing streams).
**Not** pixel art (glyphs are smooth vector mono, edges crisp 0.443; no dithering, no visible pixel blocks).
**Not** VHS glitch or synthwave (no chroma bleed, no RGB split, no tracking noise, no vignette, no neon gradient).

## 2. Materials & rendering

- **Ground:** one flat colour, no mottle (0.59, under paper level), no vignette (0.00), no screen curvature (by
  eye). Grain measured 2.44 grey levels is "fine", i.e. codec noise: do not add grain.
- **Phosphor marks:** vector text and rules, crisp edges (0.443), with a tight bloom under bright marks: a blurred
  copy of the lit layer at low alpha (by eye; never a wide haze).
- **Scanlines:** the last pass, one dark row every 6 design px (4.0 px measured at 1280); amplitude 3.3–5.4 grey
  levels over the whole frame, clear stripes on lit glyphs, faint on the ground (by eye). Screen space: they never
  move, scale or collapse with the picture.
- **Layer order:** ground → dim structure (rules, plate borders) → amber text → cream text → bloom → scanlines.
- **Inverse video:** a filled amber block with ground-coloured letters (by eye) is the only filled shape.

## 3. Colour logic

- **One hue family only.** Everything is a lightness step of amber: ground, dim rule, amber, cream. Never introduce
  a second hue, not even for error or warning: emphasis is brightness, not colour.
- **Ground ≈ 94 % of the frame**, dark (L* 4.1). Saturated colour stays near 4 %; text is sparse.
- **Amber is the working phosphor** (body text, prompts, the inverse tag): measured #dd9c1e, with per-picture
  readings #e9a620 / #eaa720 for full-strength body text.
- **Cream is the hot phosphor** (#f8dea1, contrast 14.61:1 on the ground): status words ("OK"-type answers), the
  title, one key value. Use it sparingly; if more than one idea is cream, nothing is.
- **Dim steps** (#634210, #442f0e, #2c1c08) are the glow fringe, rules and separators; never body text.
- **The flash** of power-on passes through a warm grey-amber (dip colour #49391b measured).

Example palette (measured): ground #150d06 · dim #442f0e · amber #dd9c1e · cream #f8dea1.

## 4. Type & subtitles

- **One family: a monospaced sans** in capitals (by eye from type-lines.jpg: grotesque mono, no serifs, open
  apertures). Licence-free picks: JetBrains Mono, IBM Plex Mono (OFL), DejaVu Sans Mono. Never a pixel/bitmap face.
- **Sizes (ink height as a share of frame height):** title 13.7 % (kit font size 0.152 H, bold 700); body 3.5 %
  (kit 0.039 H). Title-to-body ratio ~3.9. The 1.5 % tier measured is the dot leaders, not a type size.
- **Case:** all capitals, including subtitles. Punctuation is part of the look: dot leaders, ">", trailing ".".
- **Alignment:** logs and lists flush left at the 2.7 % margin from the top (5.6 %); a title stands alone, centred
  (title screens measure symmetry 0.64–0.68); a status line lives bottom-left under a full-width rule.
- **Weight:** bold for titles (measured 700); body reads regular to medium by eye (the "black" overall reading is
  inflated by bloom and scanlines).
- **Subtitles** are terminal output: a bottom-left `> TEXT` prompt under the rule, amber, typed in; never a caption
  box. Hold ≥ max(1.8 s, speech + 0.6 s) and ≥ other chars / 15 + CJK chars / 4.5 + 1.5 s. CJK needs a mono face
  with CJK glyphs (e.g. Noto Sans Mono CJK), two cells per glyph.

## 5. Motion quality

- **24 fps, on ones** (84 % of frames). Motion ~0.5 of the time; holds short (median 0.17 s, p75 0.29 s): something
  is always typing or blinking.
- **Typing is the default entrance**: characters left to right at a constant rate (a title reveal read as a
  left-anchored wipe of 0.40 s, linear best fit, unclaimed); lines top to bottom, ~0.3 s a line by eye.
- **Status words stamp in** at the line's end, slightly large, settling (one reading: scale 1.11 → 1.0 with a fade;
  ease not claimed).
- **Zoom-to-title**: a small typed title grows in place to full size: scale from ~0.21 to 1 over 1.0–1.56 s,
  **power2.inOut** (claimed; house curve cubic-bezier(0.62, -0.05, 0.38, 1.05)). No overshoot (0 % of entrances).
- **Cursor**: a block cursor blinks on a 0.25 s period, lit for 0.083 s (from the shot's motion runs).
- **Exits are almost instant**: 0.08–0.125 s (median 0.125), ease-in by every guess (power4.in, circ.in, back.in,
  none claimed). Things are switched off, not walked off: exits are ~12× shorter than entrances.
- **Never moves:** the ground, the scanlines, the character grid's left margin. No drift, no float, no camera.

## 6. Camera grammar

Locked frame always (2 of 2 shots locked, no camera move measured). Motion is in the raster, not the lens.

| Move | What it expresses | Can serve |
|---|---|---|
| Locked log screen | a machine reporting, one line at a time | a checklist; a process; a countdown of steps |
| Zoom-to-title (scale in place) | a value or name promoted from the log to the headline | a result; a product name; a verdict |
| Clear screen (instant) | a new page of output | a chapter change; "next"; reset |
| Power-on (line → flash → settle) | the system waking | a beginning of any kind; a reveal after black |
| Power-off collapse | the session ends | an ending; a hard stop; "shutting down" an idea |

- **Transitions:** no cuts or dissolves measured; change pages by a one-frame clear or by power-on/off. The one
  dip measured lasts 0.42 s (out sine.out, in circ.out).
- **Framing:** text never closer than 2.7 % to the left edge, 5.6 % to the top; the status line sits ~4 % from the
  bottom (title screens: bottom margin 3.5–4.2 %) under a full-width rule; a title is centred with ≥ 25 % empty frame on each side.

## 7. Sound palette

All inferred (the references are silent).

- **Machine foley first:** CRT whine while lit; degauss thump and relay click at power-on; keyboard or teletype
  ticks while typing (thinned, not one per glyph); a short beep per status word; fan hum as the bed; a falling zap
  at power-off, then true silence.
- **Music, if any:** one sparse pulse-wave or mono analog synth, low and slow; no big drums, no orchestra.
- **Silence** is the tube off: when the screen is dark, so is the mix.
- **Mix:** dry, close, near-mono, −14 LUFS; ticks duck under a voice. Voice: calm, clipped, an operator reading.

## 8. Native moves

- **Boot log.** Lines type top-left, each ending in a dot leader and a cream status word that stamps in. *Fits
  content like:* a recipe's steps; a release checklist; a day's schedule.
- **Promote to title.** A word typed at body size zooms in place to title size (power2.inOut, ~1.5 s), the rest of
  the screen already cleared. *Fits content like:* a winner announced; a city name; a key number.
- **Inverse tag.** A filled amber block with ground-coloured letters, followed by `> message`. *Fits content like:*
  a speaker label; a category tag; a timestamp.
- **Power-off collapse.** The whole raster squashes vertically to a centre line in ~0.125 s (ease-in), the line
  shrinks to a dot, the dot fades. *Fits content like:* a final punchline; "end of day"; cutting someone off.
- **Blinking cursor wait.** Nothing but a cursor blinking at 0.25 s on an empty screen. *Fits content like:* a
  question left open; suspense before a reveal; "your turn".

## 9. Pitfalls of the medium

- **Scanlines at the wrong scale, or moving.** `scanlines()` works in device px: scale the period to the output or
  the stripes beat with the type; keep them on the glass, outside the picture's transform.
- **Bloom that changes colour.** Full-strength additive glow turns amber white-yellow; blur and add at low alpha.
- **Second hue sneaking in** (a red error, a green OK). Emphasis is cream, not another colour.
- **Proportional fonts.** Dot leaders and columns stop lining up; always a mono face.
- **Thin rules vanish** under H.264 and scanlines at 1080p; draw rules ≥ 2 px.
- **Too much text.** Content covers ~5 % of the frame; a full screen of log reads as noise.
- **Easing the typing.** Typing runs at a constant rate; an eased reveal reads as a wipe, not a machine.

## 10. Engine

What the kit needs (`kit/tokens.js`, `kit/motion.js`, and one style module, `kit/phosphor.js`, to write):

- `tokens.js` as measured (`PALETTE` ground / ink = cream / accent = amber, `TYPE.title` 0.1522 and `TYPE.body`
  0.0389 of height, `LAYOUT.margin` 0.027, scanline period 6); grain unused; families → the chosen mono face.
- `motion.js`: `MOTION.enter.ease = 'power2.inOut'` for zooms (claimed), typing linear (`'none'`), exits an in-class
  curve (`'power4.in'`, inferred); add `cursor: { period: 0.25, on: 0.083 }`.
- `phosphor.js` (to write): `grid()` cell size from the face's advance; `type(g, text, x, y, t, at, cps)` whole
  characters at a constant rate; `stamp()` for status words; `bloom(g)` (blurred lit layer under the sharp one);
  `crt(g, t, {on, off}, draw)` power-on line/flash and power-off collapse as one transform of the picture, before
  `scan(g, period)` = `scanlines()` with the period scaled to the output.

Minimal example (not in the references: a block-character progress bar on the grid):

```js
draw: (g, t) => {
  g.fillStyle = PALETTE.ground; g.fillRect(0, 0, 1920, 1080);
  const c = grid(g), x = LAYOUT.margin * 1920, y = 300, n = Math.floor(value(t, 1, 2, 0, 20, 'none'));
  type(g, 'UPLOAD ....', x, y, t, 0.2, 30);
  g.fillStyle = PALETTE.accent; g.fillText('█'.repeat(n).padEnd(20, '░'), x, y + c.h * 1.5);
  if (n === 20) stamp(g, 'DONE', x + c.w * 22, y + c.h * 1.5, t, 3, PALETTE.ink);
  bloom(g); scan(g, TEXTURE.scanlines.period_px);
}
```

## 11. Variation space

Each film decides the words, which one is promoted, how many pages, whether a status line runs, the typing speed
(within readable) and where the tube turns on and off. §3 fixes the palette; only the share of cream changes.

- **Structures:** (1) a single page of log that fills, then one value is promoted; (2) a dialogue between two
  prompts (`>` user, inverse tag machine) answering each other line by line; (3) a countdown of pages, each cleared
  and replaced, each shorter, ending on one word.
- **Openings:** (1) black, a cursor blinks alone, then typing starts; (2) a full title already lit, overtyped
  letter by letter into a new word; (3) mid-log, lines already scrolling up, as if we walked in late.
- **Endings:** (1) a last status word stamps in cream and holds; (2) every line but one is cleared, and that one
  is promoted to title; (3) the screen clears and only `> _` remains blinking.
