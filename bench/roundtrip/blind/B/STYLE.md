# Two-Ink Riso — Style Prompt

Two-Ink Riso · 双色孔版 · 1920×1080, 24 fps drawn on twos

> A risograph print brought to life: flat bands of teal and coral ink on cream paper, halftone skies, speckled ink,
> and type printed slightly out of register. Shapes are laid down as if by a roller pulled left to right, one ink
> at a time, in a single locked frame.
> References (grammar only): risograph and screen-printed travel posters. Take the limited inks, halftone as tone,
> misregistration and band composition; never a reference's scene, words or lettering.

## 1. Essence, and what it is not

1. **Two inks on paper.** Teal and coral (2 hue families) on a cream ground; every other colour is a tint or an
   overprint of those two.
2. **Halftone as the only gradient.** Tone is made with an angled dot screen (88 % of references; 7 design px period
   at 104.8°), never a smooth blend.
3. **Printed texture everywhere.** Visible grain (3.3 grey levels) and blotchy mottle (4.1) make inks speckle; edges
   stay crisp-ish (0.34), like ink on paper rather than vector on screen.
4. **Out of register.** Type is printed in two or three inks offset by a few px (by eye), so coloured fringes show.
5. **Full-bleed bands.** Horizontal bands of colour run edge to edge (margins 0 %, content 61 %, symmetry 0.83);
   a few simple geometric objects sit on them.

**Not** flat vector "corporate" illustration (that is clean, gradient-free but grain-free and in register).
**Not** a vintage-paper collage (no torn edges, no photos, no sepia). **Not** pop-art comic halftone (no black
outlines, no CMYK primaries, dots are a tone, not a pattern to admire).

## 2. Materials & rendering

- **Paper:** cream ground with mottle 4.1 (`paper()` with the measured value), no fibres visible, no vignette (0.00).
- **Inks:** each colour is a separate flat layer drawn with `multiply`, so where inks overlap they darken (by eye:
  halftone dots read darker over the coral disc). Ink areas speckle: a seeded, per-layer coverage noise fixed to the
  paper, not to the screen.
- **Halftone screen:** `screen()` with period 7 design px (4.67 px at 1280) at 104.8°; amplitude 23–27 grey levels.
  Dot size carries tone: denser near the top of a band, sparser lower (by eye); a stepped band of two densities is
  enough.
- **Knockout trap:** a small shape on a dark ink keeps a cream outline where the paper shows through (by eye).
- **Grain:** last, over the whole frame, at the measured 3.3 (stills read 2.3, video frames up to 5.9).
- **Rendering order:** paper → light ink bands → halftone → dark ink objects → overprinted type → grain.

## 3. Colour logic

- **Ground is cream paper** (light, L* 94.2), not white. It is the light, and it is what shows through gaps.
- **Teal is the workhorse** (#087a7a, 40 % of the frame): large fields, sea or floor, plain type (contrast 4.46:1).
- **Coral is the single warm event** (#f06c69, ~3 % of the frame, in 4 of 5 references): one disc, one small object,
  the misregistration fringe. It never fills a band and never carries text alone (contrast 2.58:1 on cream).
- **Tints by halftone only:** #99c2bb and #c6d8ce are teal dots on cream at two densities (13 % and 12 %).
- **Darkest value is an overprint** (#084142, deep teal): reflections, rules, the type's top ink. No black.
- **Value order:** cream (lightest) > halftone tints > coral > teal > deep teal. Saturated area stays small (3 %).

Example palette (measured): cream #f4eee2 · teal #087a7a · tint #99c2bb · coral #f06c69 · deep #084142.

## 4. Type & subtitles

- **One face: a heavy geometric sans, lowercase** (by eye from type-lines.jpg: single-storey g, flat terminals,
  round dots). Licence-free: Figtree 900, Outfit 800, League Spartan 800 (OFL). Weight black (measured 800).
- **Size:** a title line is ~15.7 % of frame height in ink (kit font size 0.174 H); only one tier was seen, so
  subtitles are a step down by eye (~5–6 % H) in the same face.
- **Placement:** flush left at ~7 % from the edge (measured title box x 0.070), riding a band boundary (the title
  box spans y 18.8–34.4 %), never centred.
- **Printing:** the type is overprinted: deep teal top ink, a teal copy and a coral copy offset a few px in opposite
  directions (by eye). Plain teal is the quiet version.
- **Subtitles** are printed on the paper band in teal, lowercase, short, left-aligned like the title; never a boxed
  caption. Hold ≥ max(1.8 s, speech + 0.6 s) and ≥ other chars / 15 + CJK chars / 4.5 + 1.5 s; CJK in a heavy
  OFL sans (e.g. Noto Sans SC Black) with the same overprint.

## 5. Motion quality

- **24 fps, drawn on twos** (every drawing held 2 frames, share 1.0): `step(t, 12)` for everything.
- **The roller pull** is the house entrance: a band or a word is revealed by a left-to-right wipe at constant speed
  (sea: grow-x anchored left, linear `none`, claimed, 0.79 s; title: wiped on in ~0.4 s from the motion run).
- **Rising objects ease out**: a disc rises out of a band edge (clip-rise) with **power2.out** (claimed), ~2.4 s in the one
  reading: slow and heavy, settling without overshoot (0 % of entrances).
- **Travel is linear**: a small object crosses at constant speed (claimed `none`, 2.9 s across 59 % of the width).
- **Re-inking**: an element can change ink by a second left-to-right pull over it (by eye: deep teal → teal, ~0.25 s
  run).
- **Exits are quick pulls the other way** (0.17–0.33 s; a disc wiped off in 0.17 s, best guess power4.in,
  unclaimed); small marks may pop (one reading: scale from 0.81 with 7.6 % overshoot).
- **Some layers simply print**: a halftone band appears in one step (a 0.08 s run), no fade.
- **Holds** 0.56–0.83 s between events (median 0.67); motion ~0.58 of the time.
- **Never moves:** the paper, its mottle, the halftone screen's angle, the horizon line. No fades, no blur.

## 6. Camera grammar

Locked frame (1 of 1 shots locked, 12 s, no cuts, dissolves or dips). The print stays on the table; things are
printed onto it, wiped off it, slid across it.

| Move | What it expresses | Can serve |
|---|---|---|
| Locked frame with bands | a poster being made, layer by layer | an introduction; a place; a calm statement |
| Roller pull (L→R wipe) | something being stated, laid down | a heading; a fact; the next step of a list |
| Re-ink pull | the same thing seen anew | a change of state; before/after; a second meaning |
| Rise from a band edge | arrival, growth, dawn of something | a result; a sun/moon/coin; a mood lifting |
| Linear crossing | time passing at an even pace | a journey; a process; waiting |

- **Transitions:** none measured beyond the locked shot. Change scenes by wiping the old layers off and pulling new
  ones on, or by a full-frame ink band pulled across. No dissolves, no cross-fades (inks don't fade).
- **Framing:** bands run full bleed; the horizon sits around 59 % of the height (measured sea top); the main object
  sits off-centre to the right (measured disc centre x 70 %); type sits top-left, the opposite side.

## 7. Sound palette

All inferred (silent references).

- **Print foley:** a soft roller swish on each pull, a dry paper slide on crossings, a muted stamp on the title.
- **Music:** gentle, warm, unhurried: marimba, kalimba or felt piano with a low pad; small plucked figures that land
  with the pulls.
- **Ambience** from the subject (sea and sky suggest distant waves), kept low; holds may be near-silent.
- **Mix:** dry, close, little reverb; −14 LUFS; music ducks under a voice. Voice: calm, warm, unhurried.

## 8. Native moves

- **Pull a band.** A full-width ink band is revealed left to right at constant speed. *Fits content like:* a
  timeline bar; a road or river; a chapter divider.
- **Rise from the edge.** A disc or block emerges from behind a band edge, power2.out, no bounce. *Fits content
  like:* a price rising; the moon; a new product coming up.
- **Halftone weather.** A band of dots appears in one printed step to set the tone. *Fits content like:* fog; a
  crowd; the night sky.
- **Out-of-register title.** A lowercase word pulled on, its coral and teal copies offset. *Fits content like:* a
  festival name; a chapter title; a slogan.
- **Re-ink.** A second pull changes a word's or shape's ink. *Fits content like:* "old → new"; a highlight; a mood
  turning.

## 9. Pitfalls of the medium

- **Smooth gradients or transparency.** Any alpha fade or blend makes colours outside the inks; tone only by
  halftone, presence only by pulls.
- **Halftone moiré.** A 7 px screen at 104.8° beats with H.264 and with scaling; keep the measured 7 design px
  period, never scale a halftone raster, render the screen at output resolution.
- **Grain or registration that jitters.** Grain changes on the drawing steps, not every frame; offsets are fixed
  per shot (seeded).
- **Coral overused.** More than one coral object, or coral type, flattens the one warm event.
- **Pure black or white.** The darkest is deep teal, the lightest is cream paper.
- **Eased pulls.** A wipe with an ease reads as a UI transition; rollers move at constant speed.

## 10. Engine

What the kit needs (`kit/tokens.js`, `kit/motion.js`, a style module `kit/riso.js` to write):

- `tokens.js` as measured: `PALETTE` (ground cream, ink teal, accent coral, secondary tints), `TEXTURE.halftone`
  `{ period_px: 7, angle: 104.8 }`, `grain` 3.265, `mottle` 4.1, `TYPE.title` 0.1739 at weight 800; replace the
  placeholder families with the chosen face.
- `motion.js`: enter ease is unread in the kit; set pulls to `'none'`, rises to `'power2.out'` (both claimed),
  exits `'power4.in'` (inferred); keep `on: 2` and wrap drawing time in `step(t, 12)`.
- `riso.js` (to write): `ink(g, color, draw)` a multiply layer with seeded speckle fixed to the paper;
  `pull(g, t, at, dur, draw)` a left-to-right clip at constant speed (and `unpull` for exits); `tint(g, rect,
  densityTop, densityBottom)` stepped halftone from `screen()`; `overprint(g, text, x, y, inks, offsets)` using
  `misregister()`; `trap(g, path, width)` the cream knockout outline.

Minimal example (not in the references: a bar chart printed bar by bar):

```js
draw: (g, t) => {
  const tt = step(t, 12);
  g.drawImage(paper(1920, 1080, { color: PALETTE.ground, mottle: TEXTURE.mottle }), 0, 0);
  [0.4, 0.7, 0.55].forEach((h, i) => pull(g, tt, 0.5 + i * 0.6, 0.5, g2 =>
    ink(g2, PALETTE.ink, q => q.fillRect(300 + i * 260, 900 - h * 600, 200, h * 600))));
  overprint(g, 'harvest', 130, 260, [PALETTE.secondary[0], PALETTE.accent, '#084142'], [[-4, -3], [4, 3], [0, 0]]);
  grain(g, TEXTURE.grain, Math.floor(tt * 12), { ground: PALETTE.ground });
}
```

## 11. Variation space

Each film decides the subject drawn in bands and discs, which ink is the field and which the event (within §3),
where the horizon sits, the words, and the order of pulls.

- **Structures:** (1) a poster assembled layer by layer, then one layer re-inked to change its meaning; (2) a
  vertical stack of bands like floors of a building, each pulled on with its label; (3) a strip of three small
  prints side by side, each finished in turn.
- **Openings:** (1) bare cream paper, one halftone band printed in a single step; (2) a word pulled on alone, the
  picture built under it; (3) a coral block already present, the teal field pulled around it.
- **Endings:** (1) everything wiped off but the title, re-inked; (2) a last band pulled over the whole frame, deep
  teal; (3) the main object slides out of frame and the empty bands hold.
