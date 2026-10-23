# Two-Ink Riso Poster — Style Prompt

Two-Ink Riso Poster · 双色孔版海报 · 1920×1080

> A flat poster printed in two inks on cream stock, built on screen one ink pass at a time: full-bleed bands pulled
> across the sheet, a disc rising behind a horizon, halftone tints snapped on, chunky type printed slightly out of
> register. Where the two inks overlap they make the darkest tone; grain lives inside the ink.
> References (grammar only): risograph and two-colour screen-printed posters (flat inks, overprint, halftone tints,
> misregistration); mid-century minimal landscape prints (bands, one disc, a horizon). Never copy a print's
> layout, a printer's lettering or a poster's motif.

## 1. Essence, and what it is not

1. **Two inks plus paper.** One cool ink and one warm ink on a light, uneven stock (2 hue families, 5 chromatic
   colours); every other tone is a tint or an overprint of those two.
2. **Overprint makes the dark.** The darkest colour (#084142, 1.2 % of the pictures) appears exactly where the warm
   ink lies under the cool one: reflections, type, the sun under the halftone sky (by eye, consistent with multiply).
3. **Halftone tints, not gradients.** Light tones are dot screens of an ink (88 % of the pictures; period 4.67 px at
   1280, 7 design px at 1920; angle 104.8°; amplitude 23–27 grey levels).
4. **Full-bleed bands.** The picture is horizontal strips edge to edge (margins 0 on every side, content 61 % of the
   frame, symmetry 0.83) with one round subject and a few small marks.
5. **Printed, then pulled.** Layers arrive as print passes: a band grows from one edge at constant speed, a tint
   snaps on, type prints on in groups of letters, all on twos.

It is not **flat vector / corporate illustration** (no grain, no halftone, gradients and drop shadows), not
**synthwave sunsets** (no neon, no gradient sky, no perspective grid), not **letterpress or multi-colour
screen print** (no impression, no third ink: the dark is an overlap).

## 2. Materials & rendering

- **Stock**: cream paper with slow blotchy unevenness (mottle 4.10, range 1.14–4.88); no vignette (0.0).
- **Ink**: flat fills with crisp-to-soft edges (sharpness 0.338, range 0.226–0.383) and a visible stipple
  (grain 3.27, range 2.32–5.94), by eye heaviest inside the inked areas, as if the drum starved the ink in specks.
- **Halftone**: tints of the cool ink are round dots on a slanted screen; the sky reads as two tint levels (by
  eye a denser band above a lighter one). A tint printed over the warm ink turns its dots dark (overprint).
- **Overprint**: ink layers combine by multiply, so overlap is the dark tone; never draw the dark as a third ink
  where an overlap would make it.
- **Misregistration**: on type (and by eye on small shapes) the warm and cool plates sit a few pixels apart, so a
  warm fringe shows on one side and a cool one on the other, with the dark overprint in the middle. Fixed per film,
  not per frame.
- Grain, mottle and screen are anchored to the sheet: the paper does not move, the dots do not crawl. Rendering
  model: paper → cool-ink pass → warm-ink pass (multiply) → halftone tints → grain within ink.

## 3. Colour logic

- **The cool ink carries the frame**: it is the largest area (40 % here, more than the paper's 29 %), as a solid
  band and in its tints (#99c2bb 13.4 %, #c6d8ce 12.0 %).
- **The warm ink is the subject**: 3.0 % of the frame, in 4 of 5 references; it marks what is alive or looked at
  (the sun, the boat, the type's fringe). Keep it small and round-edged.
- **Text is dark or cool ink**: the overprint dark or the cool ink on paper (4.46:1); the warm ink (2.58:1 on the
  paper) is too light to carry words alone.
- **Order of values**: paper (L* 94.2) → tints → warm (L* 61.9) → cool (L* 46.2) → overprint (L* 24.4).
- Mean chroma 18.6; neutral area 29 %, saturated 3 %: a calm, mostly mid-value sheet.
- No gradients, no black, no white beyond the paper.

Example (the measured pair): paper #f4eee2 · cool #087a7a (tints #99c2bb, #c6d8ce, edge #57a19d) · warm #f06c69
(edges #ca6866, #dda9a2) · overprint #084142. Other ink pairs are open (§11).

## 4. Type & subtitles

- **One heavy geometric sans, lowercase** (weight black, 800; by eye single-storey g, round bowls, tight
  spacing): an OFL face such as League Spartan 800–900 or Jost 800.
- **One size, large**: the title line is 15.6–15.7 % of the frame height (kit font size 0.1739); no second tier was
  seen. Left-aligned, set high (box from 7 % left, 18.75 % top), straddling the edge between a tint band and the
  paper.
- **Printed in two plates**: the word in the overprint dark with a warm and a cool fringe from misregistration,
  or in the cool ink alone.
- **Subtitles** are short lowercase lines in the same face, in the cool ink on paper, left-aligned at the title's
  edge, printed on like the title. Each stays ≥ CJK chars / 4.5 + other chars / 15 + 1.5 s once fully printed.

## 5. Motion quality

- **24 fps on twos** (stepping 2, share 1.0): every drawing holds two frames; nothing moves on ones.
- **Entrances 0.8–2.4 s** (two measured): a band stretched from its edge, linear ('none', claimed, 0.79 s); a disc
  rising out from behind a horizon, power2.out (claimed, 2.44 s). No overshoot (0 % of entrances).
- **Snap-ons**: a tint layer appears whole in one drawing (sky: a 0.08 s run); type prints on in groups of letters
  in about 0.4 s for two words (run 8.54–8.96 s).
- **Drift**: a small warm object crosses at constant speed, linear (claimed), travelling 58.6 % of the frame in
  2.85 s; by eye it rocks as it goes.
- **Exits are quicker** than entrances (median 0.33 s vs 1.6 s): a wipe-off 0.17 s, a pop 0.33 s, ease-in by eye
  (guess power4.in, not claimed); some marks simply vanish between two drawings. A drifting object leaves by
  drifting on.
- **Holds** 0.56–0.83 s between events (median 0.67 s); motion about 58 % of the time.
- **Never moves**: the paper, the halftone screen, the horizon line once printed, the camera.

## 6. Camera grammar

Locked (1 of 1 shot): the frame is the sheet. One continuous shot, no cuts, dissolves or dips measured.

| Move | What it expresses | Can serve |
|---|---|---|
| Locked sheet, layers printed on | a picture being made, calm assembly | a title card; a place; a slow arrival |
| Band pulled from an edge (linear) | a new layer of the world laid down | a ground; a sea; a field; a timeline |
| Rise behind an edge (power2.out) | emergence, something dawning | a sun; a figure; a number coming up |
| Linear drift across | quiet travel, time passing | a journey; a delivery; a passer-by |
| Ink swap on a word | a change of state without motion | a before/after; a reveal of meaning |

Unseen and open: a cut between two sheets (it should land on bare paper, then print again); a slow pan across a
wide sheet (the screen and grain must stay fixed to the sheet, not the lens). Framing: bands run full bleed;
text keeps a margin of about the title's left offset (7 %); the round subject sits off-centre on the band edge.

## 7. Sound palette (inferred: the references are silent)

The print studio and an unhurried mood: a soft drum-and-paper rhythm (a riso's thump and whirr) on each layer
pull, a dry paper slide, a light roller hiss for tints. Music, if any: warm, sparse, acoustic (marimba or kalimba,
nylon guitar, a soft pad), on the twos' gentle pulse. Ambience comes from the picture's subject, kept thin.
Silence under a slow rise is welcome. −14 LUFS, music forward, foley soft.

## 8. Native moves

- **Layer pull.** A full-bleed band of ink grows from one edge at constant speed, like a print pass. *Fits:* a
  landscape's ground; a progress or timeline bar; a section divider.
- **Rise from behind.** A disc or shape climbs out from behind a band edge, slow, power2.out. *Fits:* a sunrise or
  moonrise; a result rising into view; a head over a wall.
- **Overprint reflection.** A warm shape repeated under the cool band reads dark: reflections, shadows, a second
  meaning, with no new colour. *Fits:* water; a shadow on a field; a hidden figure in a crowd.
- **Snap-on tint.** A halftone band appears whole in one drawing. *Fits:* weather changing; a mood shift; a
  highlight on a map.
- **Misregistered title, printed on.** Letters print in small groups on twos, the plates a few pixels apart; the
  ink of the word may later swap. *Fits:* a title; a place name; a quote.

## 9. Pitfalls of the medium

- **Halftone moiré**: a 7 px screen rescaled or rotated by the camera beats against the pixel grid; keep it in
  design pixels on the sheet and render at the design size.
- **Grain lost in H.264**: fine stipple turns to mush at low bitrates; keep it inside the inks at the measured
  level and encode with enough bitrate.
- **Overprint drawn as a third flat colour** loses the riso logic: use multiply between ink layers.
- **Warm ink for text** fails contrast (2.58:1): text in the overprint dark or cool ink.
- **Misregistration that shimmers** frame to frame reads as a glitch: seed the offsets once per film.
- **Easing on ones** turns the print into smooth vector motion: step drawings with `step(t, 12)`.

## 10. Engine

What the kit needs:

- `kit/tokens.js`: `PALETTE` as measured, plus a named `overprint` (#084142) and the two tints; `TYPE.display` and
  `TYPE.text` set to the heavy geometric face (placeholders are a neo-grotesque); `TEXTURE` as measured
  (grain 3.265, mottle 4.1, halftone period 7, angle 104.8).
- `kit/motion.js`: `MOTION.enter.ease` is null: band pulls take `'none'` (linear), rises `power2.out`, both claimed;
  `MOTION.exit.ease` is unread: ease-in (inferred); `MOTION.on` 2, so every draw uses `step(t, 12)`.
- `kit/texture.js`: `paper()` for the stock, `screen()` for tints, `misregister()` for the plates; `grain()` is
  full-frame, so a style module should mask it to the inks.
- A style module `riso.js`: `ink(g, color, path)` (fill with multiply, grain inside the fill), `tint(g, color,
  path)` (screen fill), `pull(t, at, dur)` (linear band growth from an edge), `plates(g, draw, offsets)`.

Minimal example, a two-ink bar chart printed bar by bar (not in the references):

```js
// positions, sizes and times in this example are illustrative, not measured
const tt = step(t, 12);
[0.35, 0.6, 0.45, 0.8].forEach((v, i) => {
  const p = tween(tt, 1 + i * 0.5, 0.79, 'none');                        // linear pull, like the band
  ink(g, PALETTE.ink, rectPath(200 + i * 300, 980 - v * 700 * p, 220, v * 700 * p));
});
ink(g, PALETTE.accent, circlePath(1500, 300, 140 * tween(tt, 3.5, 2.44, 'power2.out'))); // overlaps print dark
```

## 11. Variation space

Each film decides its ink pair (any cool and warm pair that overprints dark: blue and fluorescent pink, green and
orange), the band layout (horizontal here; vertical or diagonal bands are open), how many subjects, whether type
is overprint-dark or cool, and the order of passes. Unseen and open: several sheets cut together on bare paper, a
pan across a long sheet, a second type size for a caption.

- **Structures**: one sheet assembled pass by pass to a finished poster; a series of small sheets, each printed
  then cleared to paper; a before/after where one ink swap changes the meaning.
- **Openings**: bare paper, then a tint snapped on; a single warm disc printed alone in the middle; a word printed
  before any picture exists.
- **Endings**: the subject wiped off, leaving bands and the word; the last pass a tint over everything; the sheet
  holding still after its final plate.
