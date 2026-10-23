# Amber Phosphor Terminal — Style Prompt

Amber Phosphor Terminal · 琥珀荧光终端 · 1920×1080

> A monochrome character terminal as the whole world: one phosphor hue glowing on an off-black tube, monospaced
> capitals printed onto a fixed cell grid, every frame striped by scanlines. Things are typed, cleared, zoomed and
> switched off; the tube switching on and off is the punctuation.
> References (grammar only): power-on self-test screens of 1980s office computers (a log of checks, each answered);
> single-colour phosphor monitors (one hue, two brightnesses, glow, rows); the picture tube's life (a line opening
> into a picture, a picture collapsing to a dot). Never a product's name, logo, boot text or typeface.

## 1. Essence, and what it is not

1. **One phosphor hue on near-black.** The ground (#150d06, L* 4.1) holds 94 % of every picture; all marks belong
   to one hue family (hues 59–89°). Hierarchy is brightness, never a second hue.
2. **A character grid.** Rows 4.44 % of the frame height apart, cells about 1.26–1.29 % of the width (derived from
   line and word positions: roughly 80 × 22); left edge at 2.7 %.
3. **Scanlines on everything**, ground and glyphs: every reference (share 1.0), period 4 px at 1280 (6 design px).
4. **Printed, not animated**: characters snap on in reading order (10 of 15 tracked appearances are static snaps),
   a block cursor blinks, a page clears in one frame.
5. **The tube's life as transitions**: a line opens into the picture; the picture collapses to a line, then a dot.

Not **hacker green-rain** (falling glyphs, glitch tearing), not **VHS / synthwave** (colour fringes, tracking noise,
vignette: 0.0 here on all eight pictures), not **pixel art** (here smooth outline type, crisp edges 0.443).

## 2. Materials & rendering

- **Tube face**: a flat, uncurved rectangle of ground. No corner darkening (vignette 0.0), no mottle (0.595); by
  eye no barrel distortion, bezel or reflection.
- **Phosphor**: each glyph drawn at its brightness, then a soft halo of the same hue around it (by eye; the dark
  #2c1c08 covers 1.5 % of the pictures, in all five, around the type). Two passes: a blurred copy at low alpha,
  then the sharp glyph. Brighter glyphs glow more.
- **Scanlines last, in screen space**: dark rows every 6 design px over ground and type; on the ground they read as
  3.3–5.4 grey levels (per picture), on bright glyphs as clear stripes (by eye about half the period dark). The
  raster belongs to the screen and never moves with content.
- **Grain** 2.44 ("fine", likely codec): the screen reads clean; if any noise is added, the kit's `grain()` at that
  value and no more. Edges crisp (0.443).

## 3. Colour logic

- **One hue, three working brightnesses** over the ground: dim (rules, halos, the inactive) → body (the saturated
  mid phosphor, ordinary text) → bright (the pale near-white of the same hue, for what matters now: a result, a
  title). Value order is meaning order.
- **Bright is scarce**: the pale ink covers about 1.3 % of the pictures, the body colour under 1 %; 94 % of the
  frame is neutral, saturated area 4 %, mean chroma 6.1.
- **Inverse video** is the only filled shape (by eye): ground-coloured letters on a body-colour block, for a short
  tag, never a paragraph.
- No second hue; no pure black or white (the ground keeps its tint at L* 4.1, the brightest ink chroma 33).
- The power-on flash decays through a warm mid-dark (#49391b).

Example (the measured amber): ground #150d06 · halo #2c1c08 · dim #442f0e / #634210 · body #dd9c1e (edge tones
#ad7a18, #895f14) · bright #f8dea1 (14.61:1 on the ground; body 8.1:1). Another single phosphor hue is open (§11).

## 4. Type & subtitles

- **One monospaced face, all capitals**, bold to extra-bold (title 700, overall 800). By eye a grotesque monospace
  with plain round O's: an OFL face such as JetBrains Mono 800 or IBM Plex Mono 700. Never proportional: the grid
  is the style.
- **Sizes** (line ink, share of frame height): body 3.3–3.6 % (median 3.5 %, kit 0.0389); title 12.5–14.9 % (median
  13.7 %, kit 0.1522); ratio 3.91. The 1.5 % tier is the dot leaders, not text.
- **Placement**: logs from the top-left margins (2.7 % / 5.6 %) down the grid; one title alone, centred, a little
  above the middle (its line spans 37–51 % of the height); a status line at the foot (91 %) under a full-width
  hairline in the dim tone.
- **Label · leader · value**: a label, a run of dots, then the value; the answer word in bright.
- **Subtitles are terminal output**: a prompt line at the foot (`>` then words, typed on) or a new log line, never
  a floating plate. Each stays ≥ CJK chars / 4.5 + other chars / 15 + 1.5 s after it finishes typing.

## 5. Motion quality

- **24 fps on ones** (share 0.84). Change is discrete: characters, cursor, clears.
- **Typing**: characters appear whole, one after another, at machine speed (by eye: a seven-line log in about 2 s,
  run 1.04–3.08 s; a short word in a few frames). Measured as left-anchored wipes (0.40–1.0 s); build it as
  characters. An answer may land a beat after its line.
- **Cursor**: a solid one-cell block, on and off every 0.25 s (state changes 0.25 s apart), after the last character.
- **The one smooth move, the zoom**: a typed word grows from about 0.21 of its size (scale_from median 0.214) to
  full in 1.0–1.56 s, drifting about 10 % of the frame to its place, power2.inOut (claimed; fitted
  cubic-bezier(0.619, −0.048, 0.381, 1.048)). No overshoot (0 %).
- **Ticks**: a small settle, scale 0.915 to 1 in about 0.1 s (one measured).
- **Exits collapse**, in 0.08–0.125 s (median 0.125 s): squashing toward the centre line (scale to 0.55–0.69, about
  7 % of travel). Ease not claimed; every fitted guess is ease-in, so ease-in (inferred). Exits are over ten times
  shorter than entrances (0.125 vs 1.56 s): a screen shuts off, it never fades.
- **Holds** between printed events are short (median 0.167 s, p75 0.29 s); motion about half the time (0.511).
  Between bursts only the cursor moves.
- **Never moves**: the scanlines, the margins, the grid.

## 6. Camera grammar

Locked (2 of 2 shots, no camera move measured): the screen is the frame; scale changes belong to the content.

| Move | What it expresses | Can serve |
|---|---|---|
| Locked screen, text typing on | a machine reporting step by step | a checklist; a process; a log of facts |
| Hard clear (one frame) | a new page, a decision taken | a chapter change; "next"; a clean slate |
| Zoom from a typed word | one result promoted to headline | a name; a verdict; the number that matters |
| Power-on (line → band → picture, dip 0.42 s) | waking, a session starting | an arrival; a launch; a morning |
| Power-off (line, then dot) | a session ending | a sign-off; a shutdown; "that's all" |

Measured: one dip (0.417 s through #49391b, fitted fade-out sine.out, fade-in circ.out); no cuts or dissolves.
Within a screen, change is clear-and-reprint. A cut to another layout is open (unseen): land it on clean ground.

## 7. Sound palette (inferred: the references are silent)

The hardware's own sounds: a soft high whine and low thump at power-on; dry relay clicks and short data chirps
under typing (machine output, not a typist); a tick per answer; a low fan or mains hum. A slow rising tone may
carry the zoom; power-off is a short descending zap into silence. Music, if any: a sparse analogue synth pulse or
one held tone, dry. Silence after the dot belongs to the ending. −14 LUFS, effects forward.

## 8. Native moves

- **Power-on.** A thin line grows from the centre, opens into a bright band, flashes the frame and decays through
  the flash colour (run 0.29–0.63 s, then the dip). *Fits:* a product waking; the first day of something; a report
  beginning.
- **Self-test log.** Label · leader · value lines typed down the grid, each answered in bright. *Fits:* a feature
  list; a recipe's steps; a team's results.
- **Cursor wait.** The log stops; only the cursor blinks for a beat or two. *Fits:* suspense before a reveal; a
  question to the viewer; a pause in a countdown.
- **Promote to headline.** Clear, type one word small, zoom it to title size while the status line types. *Fits:* a
  brand name; a winner; a verdict.
- **Power-off.** Everything squashes to the centre line, the line shrinks to a dot, the dot fades (run 8.50–8.83 s).
  *Fits:* an ending; something discontinued; "goodnight".

## 9. Pitfalls of the medium

- **Scanlines moiré when rescaled**: draw them in device pixels after the picture, with the period scaled to the output.
- **Glow that makes new colours**: blur each glyph in its own colour only; no additive white, no other hue.
- **Proportional fallback fonts** break the grid: load the mono face before the first frame.
- **Typing too slowly** turns a machine into a typist; keep human speed for a prompt meant to be read along.
- **Dissolves and soft fades** read as video, not a tube: change pages by a clear, end by a collapse.
- **Too much bright** flattens the hierarchy; **a pure black ground** loses the tube's tint.

## 10. Engine

What the kit needs:

- `kit/tokens.js`: `PALETTE` as measured; `TYPE.display` and `TYPE.text` set to the chosen monospace (the
  placeholders are a proportional sans); `TEXTURE.scanlines.period_px` 6; a `GRID` token (row 0.0444 of the height,
  cell about 0.0127 of the width, origin at the margins).
- `kit/motion.js`: `MOTION.enter.ease` is null: the zoom takes `power2.inOut`, typing no tween; `MOTION.exit.ease`
  is unread: ease-in (inferred) at 0.125 s; add a blink half-period of 0.25 s and a typing rate.
- `kit/texture.js`: `scanlines(g, period, strength)` draws 1 px rows; this style needs a duty parameter (rows about
  half the period thick) or its own raster.
- A style module `crt.js`: `phosphor(g, draw, color)` (halo then sharp pass), `powerOn` / `powerOff(g, t, at,
  draw)` (scale the picture about the centre: y to a line, x to a dot, then alpha), `typed(text, t, at, cps)` (the
  visible prefix from `t` alone), `cursor(g, t, x, y)`.

Minimal example, a block-character progress bar (not in the references):

```js
// positions, sizes and times in this example are illustrative, not measured
const n = Math.floor(clamp((t - 2) / 1.5) * 24);                 // cells lit, from t alone
phosphor(g, g => { g.fillStyle = PALETTE.accent; g.fillText('█'.repeat(n) + '░'.repeat(24 - n), cellX(2), rowY(6)); }, PALETTE.accent);
if (n === 24) phosphor(g, g => { g.fillStyle = PALETTE.ink; g.fillText('DONE', cellX(28), rowY(6)); }, PALETTE.ink);
scanlines(g, TEXTURE.scanlines.period_px * g.canvas.width / 1920, 0.3);
```

## 11. Variation space

Each film decides the phosphor hue (amber measured; green or white rebuilt as the same steps), how many screens and
whether it cuts between them on clean ground, page density (a lone prompt to a full table), whether it opens and
closes with the tube's life, typing speed per line, and what is promoted to a title. Unseen and open: split
terminals, scrolling output, a cursor editing a line, ASCII diagrams on the grid; each keeps grid, hue and scanlines.

- **Structures**: a question at the prompt answered by a growing log; a countdown of numbered screens, each cleared
  for the next; a dialogue between two prompts ending in one promoted word.
- **Openings**: already lit, a cursor blinking alone for two beats; one answer typed in bright at the centre; a
  screen full of dim text clearing to empty in one frame.
- **Endings**: the last line typed, cursor left blinking; a promoted word collapsing alone while the rest stays;
  the status line typing a final word and the screen holding still.
