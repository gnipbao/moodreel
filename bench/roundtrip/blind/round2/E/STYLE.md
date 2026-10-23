# Swiss Signal Grid — Style Prompt

Swiss Signal Grid · 瑞士信号网格 · 1920×1080

> International-style information design set in motion: black type, bars and squares on a warm grey sheet ruled
> into visible columns, with one red square as the only colour. Elements rise out of a shared baseline, grow from
> it in left-to-right order on a hard in-out curve, and leave by collapsing to their own centre lines; the page
> itself slides sideways to the next column.
> References (grammar only): Swiss/International Typographic Style posters and annual reports (a column grid
> shown, flush-left lowercase grotesque, numerals as images, asymmetric balance); statistical charts of the
> modernist era (plain bars on a baseline, no axes). Never copy a poster's layout, a firm's mark or a typeface.

## 1. Essence, and what it is not

1. **The grid is visible**: hairline vertical column rules over a warm light grey ground (#e9e8e4, L* 92.1, 89.5 %
   of the picture); bars and squares fill columns exactly (by eye, the rules are the light grey #c6c6c2).
2. **Black and one red**: near-black ink (#121212, 15.28:1) and a single pure red square (#e20713, chroma 91.6,
   0.3 % of the picture); everything else is neutral (99.6 %).
3. **Numerals as images**: one huge numeral per page (36.7–37.2 % of the frame height), standing on the same
   baseline as the bars (both end at 70.6 % of the height).
4. **Flush-left, lowercase, bold grotesque**: words and captions aligned left on column lines (dominant alignment
   left), asymmetric composition (symmetry 0.11, centroid at 40 % across, 59 % down).
5. **Hard in-out timing**: entrances 0.44–0.60 s on one house curve, cubic-bezier(0.71, 0, 0.191, 1) (12 tweens),
   no overshoot anywhere (0 %).

Not **corporate minimal** (no centred layouts, no rounded cards, no brand gradients), not **Bauhaus** (no primary
triad, no diagonals or circles as motifs), not a **dashboard** (no axes, legends, tooltips or multiple series
colours), not **brutalist web** (no monospace, no raw borders; everything is set with care on the grid).

## 2. Materials & rendering

- **Sheet**: a flat warm grey; no vignette (0.0), no paper fibres; mottle reads 1.69 and grain 1.80 (fine, codec):
  render it clean.
- **Column rules**: one-pixel hairlines in light grey, full height, evenly spaced (by eye about thirteen across the
  frame; bars pitch 7.6 % of the width, derived from bar positions in motion.json). They belong to the sheet and
  move with it when the page slides.
- **Solids**: bars, squares and numerals are flat ink with crisp edges (0.498); no strokes, no shadows, no
  rounding.
- **Rules under captions**: a thin black horizontal line, with a grey caption beneath it.
- World space only: everything, grid included, is drawn on the sheet; the camera moves the sheet.

## 3. Colour logic

- **Neutral by default**: ground → hairline grey (L* 79.7) → caption grey (#838280, L* 54.5) → ink (L* 5.4).
  Black carries all information; grey carries annotation.
- **Red is a signal, never a fill for data**: one red square at a time, off the data, annotated in grey (by eye
  "x … · off grid"); it marks the exception, the outlier, the one thing to remember. Red never sets text (4.01:1
  on the ground is too weak for small type) and never colours a bar.
- No second hue, no tints of red (the pinks measured, #e59395 and #e24f56, are only its anti-aliased edges), no
  gradients.

Example (the measured set): ground #e9e8e4 · hairline #c6c6c2 · greys #a5a4a1, #838280 · ink #121212 · signal
#e20713. Another single signal hue is open (§11) if it stays one square, rare.

## 4. Type & subtitles

- **One neo-grotesque, bold (700)**, lowercase for words, lining figures for numerals (by eye Helvetica-like): an OFL
  face such as Inter 700 or Inter Tight 700.
- **Sizes** (line ink, share of frame height): a word line 5.1–5.3 % without ascenders or descenders, 6.8–6.9 % with
  them (the same size: kit title 0.0761, body 0.0578 both come from it); captions 1.9–2.5 % in grey; the page numeral
  36.7–37.2 % (from its box in motion.json).
- **Placement**: words hang at the top of a block (their line at 22.8 % of the height), flush left on a column;
  captions low (87.6 %) under a short black rule; margins from 4.7 % (median left 5.5 %).
- **Subtitles** are captions: grey, small, flush left under a rule, never centred, never on a plate. Each stays ≥
  CJK chars / 4.5 + other chars / 15 + 1.5 s.

## 5. Motion quality

- **24 fps on ones** (share 0.97); smooth, exact.
- **Entrances** 0.44–0.60 s (median 0.52 s), class inOut (12 of 17 read), drawn by one curve,
  cubic-bezier(0.71, 0, 0.191, 1) (residual 0.004); best guesses expo.inOut and power4.inOut, family not claimed.
  Vocabulary: bars grow up from the baseline (13 of 17), numerals and words rise out of a slot at the baseline
  (clip-rise; best guess power4.out, about 0.3 s).
- **Order**: left to right; bars about 0.25 s apart, small squares about 0.13–0.19 s apart (derived from their start
  times; no stagger was measured as such).
- **Exits** 0.36–0.46 s (median 0.40 s), shorter than entrances, inOut, curve cubic-bezier(0.667, 0, 0.207, 1)
  (5 tweens): elements collapse to their own horizontal centre lines (6 of 8), a few shrink. A line may strike
  through a numeral before it goes (by eye).
- **The one linear move**: the signal square slides in from the right edge at constant speed (1.15 s, 'none'),
  slower than everything else, so it reads as arriving from outside the system.
- **No overshoot, no bounce, no rotation for effect.** Holds median 0.83 s (p75 1.13 s); motion 45 % of the time.
- **Never moves**: the baseline, the column rules relative to the sheet, the caption rules once drawn.

## 6. Camera grammar

One continuous shot (15 s, no cuts, dissolves or dips). The camera is still except for page slides.

| Move | What it expresses | Can serve |
|---|---|---|
| Locked sheet, elements building | a statement being set out precisely | a figure; a definition; a rule |
| Page slide (half a frame, under 0.5 s, inOut) | the next column of an argument | a second point; a comparison; a sequence |
| Collapse to centre lines | clearing a proof once made | a conclusion; a reset; a summary |
| Linear slide-in of the signal | something from outside the grid | an exception; a warning; the one highlight |

The measured slide: the whole layout moves 49.7 % of the frame width in 0.48 s, inOut (best guess power4.inOut).
Unseen and open: a vertical slide to a lower page, a cut on a clean sheet; each should keep the grid registered.
Framing: flush left on columns, asymmetric, text never centred; the numeral and bars share one baseline.

## 7. Sound palette (inferred: the references are silent)

Precise and sparse: a soft click as each bar lands, a pencil-tick for a rule drawn, a muted wooden or felt-piano
note for each numeral, a short air-swish for the page slide. Music, if any: minimal and metric (prepared piano,
marimba, a quiet pulse), with silence between statements. The red square gets its own single, higher tone.
Dry room, no reverb tails; −14 LUFS, effects at the level of the music.

## 8. Native moves

- **Rise from the baseline.** A numeral or word slides up out of an invisible slot at the baseline. *Fits:* a
  chapter number; a key word; a year.
- **Bar build.** Bars grow from the shared baseline left to right, about 0.25 s apart, on the house curve. *Fits:*
  a trend; a ranking; a budget split.
- **Square count.** A row of small squares grows left to right, one per unit. *Fits:* a count of people; days;
  steps done.
- **Page slide.** The sheet moves half a frame sideways, inOut, revealing the next column. *Fits:* the next rule;
  a before/after; a second case.
- **Signal square.** One red square slides in linearly from the edge and stops off-grid, with a grey note. *Fits:*
  an outlier; a warning; the single takeaway.
- **Collapse.** Everything squashes to its centre line in about 0.4 s, left elements first. *Fits:* a clean reset;
  the end of an argument; "only this remains".

## 9. Pitfalls of the medium

- **Hairlines vanish or shimmer** in H.264 when the sheet slides; draw the column rules at a whole-pixel position
  per frame and keep them light grey, not lighter.
- **Off-grid placement** breaks the style: snap every bar, word and square to a column; only the signal may sit
  off it.
- **Overshoot or springs** read as playful UI; keep the in-out curve with no overshoot.
- **Red overused** (red text, red bars, two squares) kills the signal; one square, about 0.3 % of the frame.
- **Centred type** turns it into corporate slides; stay flush left.
- **Captions too small**: 1.9 % of the height is the floor at 1080p; never smaller.

## 10. Engine

What the kit needs:

- `kit/tokens.js`: `PALETTE` as measured, with the hairline and caption greys named; `TYPE.display`/`TYPE.text` set
  to the chosen grotesque (placeholders are Helvetica); add a `GRID` token: column pitch 0.076 of the width, bar
  width about 0.065, baseline 0.706 of the height, word line 0.228, caption line 0.876 (derived from boxes).
- `kit/motion.js`: `MOTION.enter.ease` and `MOTION.exit.ease` are null though their class was read 12 and 5 times:
  set them to `'bezier(0.71,0,0.191,1)'` (0.52 s) and `'bezier(0.667,0,0.207,1)'` (0.40 s); add a bar stagger of
  about 0.25 s (derived); a `slide` for the camera (0.48 s, inOut, half a frame); the signal's linear slide (1.15 s).
- A style module `swiss.js`: `sheet(g, offsetX)` (ground and column rules, moved by the camera), `bar(g, col, h, p)`
  (stretch from the baseline), `riseText(g, text, x, baseline, p)` (clip at the baseline), `collapse(g, rect, p)`
  (scale y about the centre), `caption(g, text, x, y, ruleW)`.

Minimal example, a three-step timeline of years rising on the baseline, the middle one flagged (not in the
references):

```js
// positions, sizes and times in this example are illustrative, not measured
sheet(g, 0);
['1968', '1984', '2001'].forEach((y, i) =>
  riseText(g, y, colX(1 + i * 4), GRID.baseline * H, enter(t, 1 + i * 0.25)));    // left to right
const s = tween(t, 2.5, 1.15, 'none');                                             // the signal, linear
square(g, lerp(W + 40, colX(6) + 30, s), 0.33 * H, 0.0625 * W, PALETTE.accent);
caption(g, 'turning point', colX(5), GRID.caption * H, 0.2 * W);
```

## 11. Variation space

Each film decides how many pages it slides through, which figures (bars, squares, numerals, a single line), the
signal hue (one, rare), the words, and whether it ends on a collapse or a held page. Unseen and open: vertical
frames (columns become narrower, baseline lower), horizontal bars, a cut between sheets, a counting numeral (keep
the in-out curve).

- **Structures**: numbered rules, one page each, joined by slides; one chart built, then a single bar flagged red;
  a countdown of numerals 3-2-1, each collapsing before the next rises.
- **Openings**: a single dot on the bare sheet; the column rules alone, then the first numeral rising; a caption
  first, the figure after.
- **Endings**: everything collapsed except the red square and one word; a full page held still; the sheet sliding
  on to an empty column.
