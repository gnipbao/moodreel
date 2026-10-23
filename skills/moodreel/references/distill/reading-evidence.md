# Reading the evidence

`moodreel measure <project>` writes `measure/*.json` and `MEASURE.md`. Read MEASURE.md first, then open the evidence
for anything that surprises you. State what a number shows separately from what you infer it means.

## Colour (`measure/palette.json`)

- `roles.ground` is what a reference video shows before anything stands on it, when its opening frame is one colour
  (`ground_from` says so), else the colour holding the frame's border; `roles.ink` stands furthest in lightness from
  it, weighed by how much of the picture it covers; `roles.accent` is the most saturated colour that stays under 15 %
  of the picture. Check them against the sheet: a photo, a busy illustration or a film that opens on a picture can
  put the "ground" somewhere surprising.
- `colors[].presence` is how many references use a colour (≥ 1 % of the picture). A colour in one reference only is
  that picture's content, not the style's palette.
- `structure`: hue families, chromatic colours, light / dark / mid ground, mean chroma, saturated and neutral area.
  These become §3's rules ("one signal colour", "neutrals carry 90 % of the frame").
- `per_ref` palettes show what changes between references: often the accent changes per piece while the ground and
  ink stay. That is a rule too.

## Surface (`measure/texture.json`)

| Number | Means | Treat as noise when |
|---|---|---|
| `grain` (grey levels of fine noise on the ground, else in flat areas) | none < 0.8 < fine < 2.5 < visible < 6 < heavy | "fine" is usually codec noise: don't reproduce it |
| `mottle` (slow variation of the ground) | none < 0.8 < paper < 3 < blotchy | |
| `vignette` (share of the centre's light lost at a corner, the smallest over the quadrants that show ground; under 3 grey levels counts as none) | none < 0.04 < soft < 0.15 < strong | |
| `edge_sharpness` (how much of an edge's contrast is crossed in a pixel) | crisp ≥ 0.32 > soft ≥ 0.2 > blurred | |
| `halftone` / `scanlines` (amplitude in grey levels; codec blocks never reach the thresholds) | a printed screen or CRT rows | |

The kit's `grain()` and `vignette()` take these numbers as they are: they are calibrated against the measurement.
Screen and scanline periods are measured at a long edge of 1280 px; `moodreel kit` converts them to the film's design
pixels.

## Layout and type

- `layout.json`: margins, content density, centroid, symmetry, dominant alignment, left-aligned columns. Margins and
  alignment become rules in §4 and §6; density and symmetry describe the composition's temperament.
- `type.json`: line heights (ink, ascender to descender) as a share of the frame height, size tiers, title-to-body
  ratio, stroke weight (light, regular, bold, black). The kit turns a line's ink into a font size at 0.9 em, right
  for a mixed-case line; a line without ascenders or descenders reads up to a quarter small, so check the crops. **Read the words, case and typeface class yourself** in `evidence/type-lines.jpg`: geometric
  or grotesque sans, serif, slab, mono, script, display. Pick licensed faces that match (OFL from Google Fonts or
  Fontsource); record the choice in DECISIONS.md.

## Motion (`measure/motion.json`, `evidence/motion-*/`)

The grammar per video: shots (count, lengths, cuts, dissolves, dips through a colour), camera moves, drawings held on
twos, motion density, holds, and per role (entrance, exit, move): durations, ease classes and families, overshoot,
vocabulary (rise+fade, scale-pop, slide-in…), travel, start scale, staggers with interval and order.

- **What to trust**: t50 timing (within a frame on the bench), ease *class* (in / out / inOut, with overshoot or
  ringing), staggers, cuts and dissolves, camera on a textured ground.
- **What is claimed only when sure**: an ease *family*. `ease: "unknown"` with a `best` means the curve's name is
  not claimed; `equivalent` lists the families that fit the same samples. Its *class* (in, out, inOut, with
  overshoot) needs fewer readings and is claimed on its own when every family the evidence can't rule out shares it
  (`class`). The grammar counts claimed families in `eases` and claimed classes in `classes`; the fits' best guesses
  are kept apart in `guesses`.
- **The style's own curve**: when a role's tweens share a claimed class, one cubic-bezier is fitted through all of
  them (`curve`, with the number of tweens and the residual). A house curve with no GSAP name (a Swiss snap,
  `cubic-bezier(.7,0,.2,1)`) comes back this way. The kit takes a family read at least twice; else this curve when
  the class was read at least twice; else it keeps the timing, says `unread`, and the curve is yours to take from
  the evidence, marked `inferred`.
- **One-axis changes** have a `reading`: `stretch` (a bar growing from its base, a word collapsing to its midline:
  `sy` / `sx`, the share shown, with its `anchor`), `clip` (type rising out of a slot, a sun rising behind a
  horizon: the element's position from the edge that moves with it, labelled `clip-rise`) and `wipe` (a mask or a
  roller sweeping a shape on in place: `wipe`, the share shown). A solid shape can't tell a stretch from a wipe or
  from rising inside a slot of its own size; it is read as a stretch. A slot hides a clip reveal's start, so its
  curve is rarely claimed: read its class from the evidence strip.
- **What isn't measured yet**: rotation, line draw-on, per-letter text, particles and loops, and elements nested
  inside a larger shape that changes in the same run (reflections on a sea that is being wiped on). Look at the
  evidence strips (`evidence/motion-*/evidence/*.jpg`, every motion run with its tracked elements boxed) and
  describe them yourself, marked `inferred`.
- **Camera unknown or locked on a flat ground** can't tell a pan from the whole picture moving: a page turn on a plain
  ground reads as elements moving together.

## Rhythm (`measure/rhythm.json`, videos with sound)

Tempo and whether cuts and arrivals land on beats, against chance. "Cuts on a beat 0.8 (chance 0.16)" is a rule;
"0.2 (chance 0.16)" means the edit ignores the music.
