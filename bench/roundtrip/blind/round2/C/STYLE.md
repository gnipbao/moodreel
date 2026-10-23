# Isotype Tile Grid — Style Prompt

Isotype Tile Grid · 几何砖格图标 · 1920×1080

> Flat geometric graphics on a full-bleed field of tiles (circles, half and quarter circles, squares) in one hue's
> ramp, with a capsule-limbed pictogram inside a large pale disc and a heavy capital word beside it. Every shot is
> a card that assembles on the beat, holds, and is cut away on a downbeat.
> References (grammar only): Bauhaus and mid-century modular pattern design (a square grid, each cell one
> geometric primitive); isotype pictograms (a figure from circles and rounded bars, no face); Swiss editorial
> layout (big word, small labels at the corners). Never copy a pattern sheet, a sign system's figures or a typeface.

## 1. Essence, and what it is not

1. **A tile field fills the frame**: margins 0 on every side, content 67 % of the frame; each cell holds one
   primitive (circle, half or quarter circle, square, or nothing) in one of three tones of a single hue (by eye).
2. **One hue ramp plus a warm cream**: the teal ramp carries over 90 % of the picture (L* 22.8 to 71.8, hues 206–221°);
   cream (#f2eadb, 4.3 %) is reserved for type and the figure. Saturated area 0 %.
3. **A pictogram in a disc**: a figure built from a circle head and capsule limbs, near limbs in cream and far limbs
   in a pale tone, standing in a large disc of the lightest tone (by eye; the disc spans 62.5 % of the frame height).
4. **Big word, small corners**: one capitalised word in a heavy grotesque at the left, its translation under it,
   tiny monospaced labels in the top corners and a step indicator at the bottom left.
5. **On the beat**: moves start and land, and shots cut, on a 0.5 s grid (20 of 33 marks within a frame and a
   half; chance 25 %, p 0.0081).

Not a **corporate flat explainer** (no gradients, no faces, no multi-hue palettes, no drop shadows), not a **Swiss
type poster** (the pattern and the figure carry as much as the word), not **Memphis** (no squiggles, no clashing
hues).

## 2. Materials & rendering

- **Flat vector**: solid fills, crisp edges (0.457), no grain (0.09), no vignette (0.0), no halftone, no texture.
  Mottle reads 1.68 because the tile field itself varies; do not add paper.
- **Tile field**: a square grid of cells (by eye about six to the frame height), each cell drawn as one primitive
  in one of the ramp's tones; neighbouring primitives touch so half and quarter circles join into larger blobs and
  bands. Seeded per shot: a new shot may deal a new arrangement.
- **Disc and figure** sit above the field; the figure's limbs are stadium shapes (rectangles with fully round ends);
  depth comes from tone (far limbs pale), never from shadow or perspective.
- Layers: field → disc → figure → type → corner labels (screen-fixed).

## 3. Colour logic

- **One hue, ordered by value**: three field tones, deep (L* 22.8) → ground (36.6) → mid (52.2), then light (71.8)
  for the hero disc (by eye). The ground tone is the largest area (34 %); the disc's tone covers 13.5 %.
- **Warm cream is for meaning only**: type, the figure's near side, the active step. It is the only warm colour
  and the highest value (L* 93.0); on the ground it reads 6.09:1.
- **Pale (#b5d2cd) for what is behind**: the figure's far limbs, inactive steps.
- No saturated colour, no second hue in the field, no black, no gradients.

Example (the measured ramp): deep #0e3c45 · ground #175f6b · #217480 · mid #208995 · light #6dbcc3 · pale #b5d2cd ·
cream #f2eadb. Another single-hue ramp with the same value order is open (§11).

## 4. Type & subtitles

- **Title**: one word or two, capitals, a heavy grotesque (measured bold 600; a line of capitals reads a step
  light, by eye extra-bold): an OFL face such as Inter 800 or Archivo 800. Cap height 15.4–15.6 % of the frame
  height (four readings; two at 18.9–21.7 % caught a line mid-move). Left edge at 7.5–7.9 %, block upper edge at
  36.5 % of the height.
- **Translation line**: directly under the title (top at 57.2 %), CJK in a bold sans (by eye; Noto Sans SC 700),
  ink 6.7 % of the height, left-aligned with the title.
- **Corner labels**: monospaced capitals at 1.8–2.1 % of the height: a running header, wide-tracked, at the top
  left (7.3 %, 7.2 %); a counter "n / N" at the top right, ending at 92.4 % of the width. By eye an OFL mono
  such as JetBrains Mono 500.
- **Step indicator**: small vertical bars bottom-left, the current one taller and cream (by eye).
- **Subtitles** take the translation line's place and style. Each line stays ≥ CJK chars / 4.5 + other chars / 15
  + 1.5 s; text arriving on beat 2 of an 8-beat card has 3 s, so longer lines need a longer card.

## 5. Motion quality

- **24 fps on ones** (share 0.97–1.0). The beat grid is 0.5 s from 0.00 s: cards start, assemble, idle and cut on it.
- **Arrivals**: 0.31–0.50 s (median 0.42 s), mostly short travel (median 3.5 % of the frame, p75 16.9 %); scale-ins
  start at 0.69–0.87 of size (median 0.80). The ease was not claimed for any move; by eye arrivals snap fast and
  settle (best guesses expo.out, power4.out), with tiny overshoot on the disc (1–2 %).
- **The disc pops** at the cut, from about 0.65–0.74 of its size to full in 0.29–0.31 s; the figure's pieces fly in
  from beside it and click together within the next beat.
- **The word rises out of a slot** on beat 2 (by eye, clipped at its baseline), its translation a frame or two
  after: a fast lateral slide of 0.08–0.10 s, then a settle of 0.44–0.52 s (best guess expo.out). One word took a
  back.out(3) with a 29 % overshoot: an accent, not the rule.
- **Idle on the beat**: once assembled the figure dips and rises with the beat (about 1.8 % of the frame height,
  0.46–0.5 s, best guess sine.inOut).
- **No exits**: no element was seen leaving; a card ends complete and is cut away (2 of 2 transitions).
- **Holds** short (median 0.29 s, p75 0.66 s); motion 44 % of the time.
- **Never moves**: the tile field within a card, the corner labels, the step indicator (it changes at the cut).

## 6. Camera grammar

Locked (3 of 3 shots, no camera move measured). Cards of 4.0 s (eight beats) joined by hard cuts on the downbeat.

| Move | What it expresses | Can serve |
|---|---|---|
| Hard cut on the downbeat to a new card | the next item in a series, crisp | a list; steps of a routine; chapters |
| Locked card, pieces assembling on beats | building an idea from parts | a definition; a how-to; a product's parts |
| Idle bob on the beat | life, waiting, rhythm | reading time; a pause before the next step |
| Counter and step indicator advancing | progress through a known whole | a countdown; a checklist; a tour |

Measured: 2 cuts, no dissolves, no dips; shot lengths all 4.0 s. Unseen and open: a card of 16 beats, a slide
of the tile field as a page turn (it should move by whole cells, on the beat). Framing: text and labels inside a
7.5 % margin; the word in the left half, the disc in the right (centre about 73 % across, 56 % down); the field
always runs full bleed.

## 7. Sound palette (inferred: the references are silent)

The grid asks for music with a steady pulse on its 0.5 s beat: light, clean, rhythmic (plucked synths or
marimba, a soft kick on downbeats, a hand-clap or rim on the backbeat). Foley is graphic, not physical: a round
pop for the disc, small clicks as pictogram parts lock, a short swish under the word's slide. The cut lands on a
downbeat with a fresh hit. Silence is rare; when used, let one beat drop before a card. −14 LUFS, music forward,
effects tight to the frame.

## 8. Native moves

- **Card on eight beats.** Disc pops on 1, figure assembles by 2, word rises on 2, idle bobs to 8, cut. *Fits:* a
  routine's steps; a list of features; a set of rules.
- **Pictogram assembly.** Head drops in, torso and arms slide from one side, legs from the other, all locking
  within a beat. *Fits:* an instruction; an exercise; a safety step.
- **Bilingual stack.** The word in capitals, its translation directly under it, arriving a frame or two apart.
  *Fits:* a vocabulary card; a menu; a signage system.
- **Counter and steps.** "n / N" and the bars advance at each cut. *Fits:* a countdown; a tutorial; a tour of rooms.
- **Re-dealt field.** At a cut the tiles change arrangement while the layout stays. *Fits:* a new day; a new place;
  variations on a theme.

## 9. Pitfalls of the medium

- **Tones too close**: the field tones must keep their value steps, or the pattern turns to noise behind the
  word; check the word on its busiest cells (cream on deep and on light).
- **Moves off the grid** feel sloppy: start and land on beats (`beat(n)`), cut on downbeats.
- **Easing that floats**: long in-out curves on arrivals lose the snap; keep arrivals near 0.3–0.5 s, out-class.
- **A figure with details** (faces, fingers, shading) breaks the pictogram; keep circle and capsules only.
- **Small tiles** alias and buzz in H.264; keep cells large.
- **Too much cream** steals focus from the word: cream only on type, figure and active step.

## 10. Engine

What the kit needs:

- `kit/tokens.js`: `PALETTE` as measured, with the ramp named in value order; `TYPE.display` (heavy grotesque),
  `TYPE.text` (mono for labels) and a CJK face replacing the placeholders. `TYPE.title` 0.2256 comes from the
  20.3 % tier: keep it only if the chosen face's capitals then measure 15.4–15.6 % of the height.
- `kit/motion.js`: `MOTION.beat` is null: set `{ period: 0.5, phase: 0 }` so `beat(n)` places every start; `enter`
  and `exit` are null: arrivals 0.42 s with an out ease (inferred, expo.out-like), the disc 0.3 s from 0.7 scale;
  `MOTION.shot` 4.0 s is eight beats.
- A style module `tiles.js`: `field(g, seed, { cell, tones })` dealing one primitive per cell (seeded `rng`), cached
  per seed; `pictogram(g, pose, { near, far })` from a circle and capsules; `slot(g, rect, p, draw)` (clip reveal);
  `steps(g, i, n)` and `counter(g, i, n)` for the corners.

Minimal example, a pictogram raising both arms on beat 6 (a pose not in the references):

```js
// positions, sizes and times in this example are illustrative, not measured
field(g, 7, { cell: H / 6, tones: [PALETTE.secondary[0], PALETTE.ground, PALETTE.secondary[1]] });
const pop = value(t, beat(0), 0.3, 0.7, 1, 'expo.out');
disc(g, 0.73 * W, 0.56 * H, 0.3125 * H * pop, PALETTE.accent);
const lift = tween(t, beat(6), 0.42, 'expo.out');                        // arms swing up on the beat
pictogram(g, { arms: lerp(0, -160, lift) }, { near: PALETTE.ink, far: '#b5d2cd' });
```

## 11. Variation space

Each film decides its hue ramp (any single hue with the same value order: three field tones, a light disc tone,
plus a warm light for type), the figure's poses, how many cards and their length in beats (8 or 16), the corner labels' words, the
language pair, and whether the field is re-dealt at each cut. Unseen and open: vertical frames (the word above
the disc), two figures in one disc, a field that slides by whole cells on the beat.

- **Structures**: a numbered routine, one card per step; a question card answered by three cards; a vocabulary
  run of word pairs ending on a summary card with all figures small.
- **Openings**: the bare field for two beats, then the disc pops; the word first with no figure; the counter
  alone ticking to "1 / N".
- **Endings**: the last card's figure holds a final pose to the downbeat; every figure from the run side by side;
  the step indicator filled, cut to the bare field.
