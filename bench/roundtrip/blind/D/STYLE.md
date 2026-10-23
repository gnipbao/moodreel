# Midnight Release — Style Prompt

Midnight Release · 午夜发布 · 1920×1080, 24 fps

> A dark product-launch interface drawn in code: a near-black navy stage with a faint grid and a soft pool of light,
> on which one small UI object at a time (a window, a list, a number, a status pill) snaps in with a small overshoot,
> collapses back to a line and gives way to the next. One acid-lime light is the only colour.
> References (grammar only): developer-tool launch films and changelog teasers, dark-mode UI. Take the restraint,
> the single accent, the snap-and-collapse rhythm and the sparse centred staging; never a reference's product names,
> files, wording or icons.

## 1. Essence, and what it is not

1. **Almost empty.** Content covers ~1 % of the frame; one object sits near the centre (centroid 0.50, 0.51;
   smallest margin 23 %). Darkness is the layout.
2. **Navy-black stage with light.** Ground #0e1017 (L* 4.9) under a strong vignette (0.73) that leaves a soft lit
   centre, and a faint square grid (by eye).
3. **One lime light.** A single acid-lime accent (#b3ed4a, chroma 81) on ~0.1 % of the frame, glowing; everything
   else is cool neutral.
4. **UI as objects.** Rounded cards, rows, checkboxes, a pill: dark navy surfaces (#1b2130) with soft shadows,
   lowercase sans labels and a mono filename.
5. **Snap in, collapse out.** Entrances ~0.3 s with a ~5 % overshoot; exits ~0.17 s, squashed into a line at the
   centre.

**Not** a glassmorphism or gradient-mesh SaaS hero (no blur panes, no purple-pink gradients, no 3D devices).
**Not** a terminal or hacker screen (no green text, no scanlines; mono is only for filenames). **Not** a keynote
slide (no headline sentences, no bullet text, one object at a time).

## 2. Materials & rendering

- **Ground:** flat #0e1017, then the kit's `vignette()` at the measured 0.73 (corners lose ~15–27 grey levels); the
  lit centre is what the vignette leaves (by eye). Mottle 3.1 is this falloff, not paper: no texture.
- **Grid:** hairlines one step above the ground, a square cell of ~48 design px (by eye), fixed to the stage, under
  everything, never animated, fading with the vignette.
- **UI surfaces:** rounded rectangles (radius ~1–2 % of height, by eye) in #1b2130, a slightly lighter title bar,
  rows a step darker than the card; a soft dark shadow around cards (by eye). Edges crisp (0.471).
- **Glow:** only the lime accent glows: a blurred copy of it in a darker lime (#455a2c / #7ea63c) under the
  shape, a few px wide.
- **Grain:** measured 1.17 is "fine" (codec): add none.
- **Order:** ground → grid → vignette light → shadow → surfaces → text → accent glow → accent.

## 3. Colour logic

- **Neutrals carry 99.9 %**: ground 90.8 %, surface #1b2130 8.1 %, then cool greys (#4e535e, #717681, #8e939e,
  #bcc0c9) for secondary text and unchecked boxes, and ink #e5e9f2 for primary text (15.63:1).
- **All neutrals lean cool** (Lab hue ~271–281°, chroma ≤ 11.4): never warm greys, never pure black or white.
- **Lime is reserved** for "done / live / now": a status dot, the one hero light, a completed state. One lime
  object on screen at most, plus its echo (a dot in a pill). Lime contrast 13.69:1 means it can also carry a word.
- **No second accent.** Errors, warnings or categories are told by words and greys, not by colour.

Example palette (measured): #0e1017 · #1b2130 · #8e939e · #e5e9f2 · #b3ed4a.

## 4. Type & subtitles

- **UI sans** (by eye: neo-grotesque, lowercase, medium weight): Inter or Geist (OFL), weight 500 measured.
- **Mono** for filenames and code only (by eye: lowercase, with extension): JetBrains Mono or Geist Mono (OFL),
  in a mid grey.
- **Sizes (ink height / frame height):** hero numeral or word ~19 % (kit font size 0.214 H), status pill ~3.5 %,
  list rows ~2.5 % (kit body 0.028 H), mono labels ~1.9 %. Nothing in between: a hero, or small UI.
- **Case:** lowercase for labels and words; numerals as they are (`2.0`-type version strings). No caps headlines.
- **Placement:** centred stage; list text left-aligned inside its card (rows start ~4 % in from the card edge, by
  eye); a status pill low, centred, ~84 % down (measured pill text at y 0.835).
- **Subtitles** appear as a status pill or a single centred line in grey under the object, lowercase, never a
  caption bar. Hold ≥ max(1.8 s, speech + 0.6 s) and ≥ other chars / 15 + CJK chars / 4.5 + 1.5 s; CJK in
  Noto Sans SC Medium.

## 5. Motion quality

- **24 fps on ones** (88 % of frames). Mostly still: motion ~0.23 of the time; holds 0.29–1.08 s (median 0.58).
- **Entrances 0.23–0.31 s**, class **out with overshoot** (every read: 2 of 2; median overshoot 5 %). The style's
  own curve, fitted through them: **cubic-bezier(0.343, 1.344, 0.676, 1.025)** (back.out(1.2) is the nearest guess,
  unclaimed).
- **Entrance vocabulary:** scale-pop from the centre (start scale ~0.19–0.45, median 0.38), and slide-in from the
  right for rows (travel 6–18 % of the frame). One row arrived tilted and settled (one reading: −26° to 0).
- **Lists build one item at a time**, about 0.5 s apart (row arrivals at 1.19, 1.75, 2.21 s in the reference), each
  row's checkbox filling after it lands.
- **Exits 0.14–0.20 s** (median 0.17), shorter than entrances (0.17 vs 0.31 s): everything squashes and drifts to
  the centre line together (scale to ~0.3–0.37); ease-in by guess (power3.in, expo.in), unclaimed.
- **Accent pop:** the lime object scales up from ~0.56 with a bigger overshoot (one reading: 13.6 %, 0.21 s).
- **Never moves:** the grid, the vignette, the light pool. No drift, no parallax, no idle bob.

## 6. Camera grammar

Locked (1 of 1 shots, 10 s, no cuts, dissolves or dips). Scenes change inside the shot: collapse, empty beat, pop.

| Move | What it expresses | Can serve |
|---|---|---|
| Pop from centre | a thing appearing on the stage | a feature; a number; a product |
| Row-by-row build | progress, a checklist being completed | steps; requirements; a changelog |
| Collapse to a line | "done, next" | ending a section; compressing a list into a result |
| Detail becomes object | one element turns into the next | a version becoming a launch; a dot becoming a light |
| Empty beat | a breath on the bare grid | suspense; reading time; before the reveal |

- **Transitions:** only the collapse → empty → pop cycle inside one locked frame; no dissolves, no wipes, no cuts
  measured. If a film needs cuts, cut on the empty beat.
- **Framing:** one object at a time inside the central half of the frame (by eye); nothing nearer the edge than 23 %
  except a status pill low and centred.

## 7. Sound palette

All inferred (silent references).

- **Foley as UI:** soft clicks on each row landing, a tight tick per checkbox, a short airy whoosh into each
  collapse, a clean bright chime or synth pluck for the lime light.
- **Music:** minimal electronic: a warm sub-bass pulse and a soft pad, sparse; the overshoot pops land on beats.
- **Silence:** the empty beats are near-silent (room tone only), so the next pop reads.
- **Mix:** clean, tight, little reverb, −14 LUFS; a voice, if any, is calm and low, music ducked under it.

## 8. Native moves

- **Checklist build.** A card pops, rows slide in from the right one by one, boxes fill. *Fits content like:* a
  packing list; onboarding steps; a pre-flight check.
- **Collapse to the next.** The whole object squashes into a line at the centre in ~0.17 s, a beat of empty grid,
  the next object pops. *Fits content like:* before/after; a list summed up in one number; chapter breaks.
- **Hero numeral.** One large number or word, medium weight, popped from the centre. *Fits content like:* a price;
  a date; a score.
- **The detail turns lime.** A small part of the current object (a dot, a box) stays, turns lime and grows into the
  hero light. *Fits content like:* "it's live"; a recording light; a notification.
- **Status pill.** A dark rounded pill with a lime dot and a lowercase word, low and centred. *Fits content like:*
  "online"; "approved"; "in stock".

## 9. Pitfalls of the medium

- **Banding in the dark.** Vignette and light pool on #0e1017 band in H.264; render the gradient at output size and
  let the encoder dither, never upscale it.
- **Grid too strong.** Grid lines more than a step above the ground turn it into graph paper; keep them barely
  visible at full brightness.
- **Lime overuse.** A second lime element, or lime text everywhere, kills the one-light rule.
- **Overshoot creep.** Overshoot is ~5 % on UI; only the single accent may go further.
- **Small type lost.** Mono labels at ~1.9 % H and grey on navy fall apart under compression; keep them ≥ #8e939e.
- **Busy stage.** Two objects at once breaks the 1 % density; collapse one before the next pops.

## 10. Engine

What the kit needs (`kit/tokens.js`, `kit/motion.js`, a style module `kit/stageui.js` to write):

- `tokens.js` as measured: `PALETTE` (ground, ink, accent lime, secondary surface), `TYPE.title` 0.2139 and
  `TYPE.body` 0.0278 of height (weight 500), `TEXTURE.vignette` 0.728; grain and mottle unused; families to the
  chosen sans and mono.
- `motion.js`: enter ease is `null`; set it to `'bezier(0.343,1.344,0.676,1.025)'` (measured, 2 tweens), duration
  0.312; exit 0.167 with `'power3.in'` (inferred); add `accent: { scale_from: 0.562, ease: 'back.out(2.2)' }`
  (one reading).
- `stageui.js` (to write): `grid(g, cell)` cached hairlines; `card(g, x, y, w, h, title)` with shadow and title
  bar; `row(g, label, checked)`; `pill(g, label)`; `glow(g, draw)` for the lime only; `collapse(t, at)` returning
  the y-scale for the squash-to-line exit applied about the stage centre.

Minimal example (not in the references: a price that pops, then its currency sign turns lime):

```js
draw: (g, t) => {
  g.fillStyle = PALETTE.ground; g.fillRect(0, 0, 1920, 1080);
  grid(g, 48); vignette(g, 1920, 1080, TEXTURE.vignette);
  const s = lerp(0.38, 1, enter(t, 0.5)) * (1 - 0.7 * exit(t, 3.0));
  g.save(); g.translate(960, 540); g.scale(s, s);
  g.font = `500 ${TYPE.title * 1080}px Inter`; g.fillStyle = PALETTE.ink; g.textAlign = 'center';
  g.fillText('49', 40, 80);
  glow(g, q => { q.fillStyle = t > 2 ? PALETTE.accent : PALETTE.ink; q.fillText('$', -140, 80); });
  g.restore();
}
```

## 11. Variation space

Each film decides the objects (window, list, number, pill, toggle, chart bar), their order, which detail becomes
the lime light, and how long each empty beat lasts. Palette, density and the snap/collapse grammar stay.

- **Structures:** (1) three numbers in turn, each collapsing into the next; (2) one card that grows a row for each
  feature, then folds to a single lime dot; (3) a toggle that flips off → on, the stage lighting up around it.
- **Openings:** (1) the bare grid and light pool held in silence; (2) a lime dot already blinking at the centre;
  (3) a mono filename alone, typed lowercase.
- **Endings:** (1) a status pill holding under nothing; (2) the last object collapses and the grid holds empty;
  (3) the lime light dims to grey: off.
