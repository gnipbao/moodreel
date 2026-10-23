# Grid & Signal — Style Prompt

Grid & Signal · 网格与信号 · 1920×1080, 24 fps

> Swiss-style information design in motion: black grotesque type, giant numerals and solid bars on a warm light grey
> ground ruled by faint column lines, with one red square as the only colour. Elements grow from their baselines and
> rise out of slots on a hard in-out curve, the page slides sideways as a whole, and sections end by folding flat.
> References (grammar only): the International Typographic Style, modernist posters and annual-report charts. Take
> the column grid, the asymmetric left-aligned layout, the one signal colour and the data-as-shape; never a
> reference's words, figures or compositions.

## 1. Essence, and what it is not

1. **Neutral page, one signal.** 99.6 % neutral (light grey ground, near-black ink, greys); a single saturated red
   (#e20713) on ~0.3 % of the frame.
2. **Visible column grid.** Faint vertical guides run the full height (by eye: 13 columns of ~146 design px); bars,
   squares and type snap to them.
3. **Type as structure.** Bold lowercase neo-grotesque headings, huge numerals as section marks, tiny grey captions
   under hairline rules.
4. **Data as solid shapes.** Bars and rows of squares in solid ink, no axes, no gridlines, no labels on the bars.
5. **Hard in-out motion.** Everything moves on a steep in-out curve without overshoot; things grow from a baseline
   and fold flat to a centre line.

**Not** corporate infographic (no icons, no gradients, no rounded corners, no multiple colours). **Not** brutalist web
(the grid is strict and quiet, type is refined, no raw borders). **Not** a minimal Apple-style keynote (asymmetric,
left-aligned, numerals and data shapes rather than product renders).

## 2. Materials & rendering

- **Paper-like ground:** flat #e9e8e4; measured mottle 1.69 is the column guides and layout, not texture (by eye
  the ground is flat). Grain 1.80 is "fine" (codec): add none. No vignette (0.00).
- **Ink:** solid #121212 fills with crisp edges (0.498), no strokes except hairline rules.
- **Guides:** 1 px vertical lines in a light grey (#c6c6c2) across the whole height, under everything. They are part
  of the world: they move with the page when the camera pans.
- **Captions** are a mid grey with a thin rule above them, set small.
- **Layering:** ground → guides → shapes → type → signal square. No transparency, no shadows, no blend modes.

## 3. Colour logic

- **Ground is warm light grey** (L* 92.1), not white. Ink is near-black (#121212, contrast 15.28:1), not black.
- **Value order:** ground > guide grey #c6c6c2 > caption greys (#a5a4a1, #838280) > ink. Greys are for structure
  and small text only.
- **Red is the signal** (#e20713, chroma 91.6, contrast 4.01:1): one solid square per film section, never text,
  never a bar in a chart, never a tint. It may sit off the grid (by eye, its caption says so): the one element
  allowed to break the system.
- **Nothing else is coloured.** Data series differ by height and position, never by hue.

Example palette (measured): #e9e8e4 · #c6c6c2 · #838280 · #121212 · #e20713.

## 4. Type & subtitles

- **One family, a neo-grotesque** (by eye: Helvetica-like, tight, lowercase headings). Licence-free: Inter Tight,
  TeX Gyre Heros (GUST), Arimo (Apache). Bold (700 measured) for headings and numerals, regular for captions.
- **Sizes (ink height / frame height):** headings 5.2–6.9 % (kit font sizes 0.058–0.076 H; a word without
  ascenders reads ~5.2 %, one with descenders ~6.9 %); captions 1.9–2.5 %; section numerals huge (by eye ~37 % H).
- **Case:** lowercase headings and captions; numerals as section marks; captions may use an em dash and a middle dot
  (`rule 2 — …`, `x 1460 · …` by eye).
- **Alignment:** flush left, ragged right, always on a column line; heading top at ~23 % H or bottom-left near 88 %
  (measured boxes at y 0.228 and 0.876); left margin ~5 % (smallest 4.7 %).
- **Subtitles** are captions: small grey lowercase text on a column, with a hairline rule above, placed under the
  element they describe; never centred, never boxed. Hold ≥ max(1.8 s, speech + 0.6 s) and ≥ other chars / 15 +
  CJK chars / 4.5 + 1.5 s; CJK in Noto Sans SC (OFL), same rule.

## 5. Motion quality

- **24 fps on ones** (97 % of frames). Motion ~0.45 of the time; holds 0.25–1.13 s (median 0.83).
- **The house curve:** entrances on **cubic-bezier(0.71, 0, 0.191, 1)** (one curve through 12 tweens, class in-out;
  nearest names expo.inOut / power4.inOut, unclaimed). Exits on cubic-bezier(0.667, 0, 0.207, 1) (5 tweens). No
  overshoot anywhere (0 %).
- **Entrances 0.44–0.60 s** (median 0.52): bars and squares **grow up from their baseline** (13 of 17); headings and
  numerals **rise out of a slot** (clip-rise, ~0.3 s, fast-out by guess power4.out); the signal square **slides in**
  from the frame edge at constant speed (one reading, 1.15 s).
- **Staggers left to right:** bars start one after another ~0.25 s apart, squares ~0.15 s apart (derived from
  start times; no grammar stagger was claimed).
- **Exits 0.36–0.46 s** (median 0.40), shorter than entrances: elements **fold flat** to their own centre line
  (collapse-y, 6 of 8), staggered; a number can be struck through with a hairline, then shrink away.
- **Never moves:** the guides relative to the page, the red square once placed (by eye, it survives section changes), the
  ground. No wobble, no float, no bounce.

## 6. Camera grammar

One shot (15 s, no cuts, dissolves or dips). The camera is a page: it stays locked, and moves only as a whole-layout
slide.

| Move | What it expresses | Can serve |
|---|---|---|
| Locked page | reading, a statement held | a figure; a rule; a definition |
| Page slide (pan-x) | the next column of thought | a sequence; a comparison; "and then" |
| Fold to centre lines | a section closing cleanly | a summary; clearing for a conclusion |
| Signal square held across a change | continuity, the one constant | the key idea; the brand; the thread |

- **Page slide:** the whole layout, guides included, moves sideways about half a frame (one reading: 636 px at 1280,
  0.48 s, in-out, best power4.inOut). Only horizontal; never zoom, never rotate.
- **Transitions:** none but the fold and the slide; no dissolves, no wipes, no cuts measured.
- **Framing:** asymmetric (symmetry 0.11), weight left of centre (centroid 0.40, 0.59); content ~12 % of the frame;
  margins ~5 % left and 9 % right, ~24 % empty above the first heading.

## 7. Sound palette

All inferred (silent references).

- **Instruments:** dry, precise: muted piano or a single analog synth, short notes; or a clean click track.
- **Foley:** a crisp paper/pen tick as each bar lands, a soft mechanical "thunk" for numerals rising, a short
  slide-rule swish on the page slide, a tight fold sound on collapses.
- **Rhythm:** staggers can follow an even subdivision (each bar a sixteenth); suggested by the regular start times.
- **Silence:** holds are allowed to be quiet; the red square's arrival can be the one tonal note.
- **Mix:** dry, close, no reverb tails, −14 LUFS; voice neutral, measured, unhurried.

## 8. Native moves

- **Baseline growth.** Bars rise from a shared baseline one after another, left to right, on the house curve.
  *Fits content like:* yearly growth; votes per region; a training log.
- **Numeral from the slot.** A huge numeral rises out of an invisible slot to mark a section. *Fits content like:*
  chapter numbers; a ranking; a date.
- **Square counter.** A row of small squares fills in one by one, the count is the message. *Fits content like:*
  eight of ten; days left; seats taken.
- **Signal arrives.** The red square slides in from the edge and stays while the rest folds away. *Fits content
  like:* the one exception; the takeaway; a brand mark.
- **Strike and fold.** A hairline crosses an element, then it folds flat. *Fits content like:* a myth debunked; an
  old price; a cancelled step.

## 9. Pitfalls of the medium

- **Hairlines vanish.** 1 px guides and rules disappear in H.264 at 1080p; draw guides a little heavier than
  1 px (inferred: ~1.5 design px) in #c6c6c2 and check at the delivery size.
- **Red spreading.** Red text, red bars or a second red element destroys the single signal.
- **Ease drift.** A default power2.out reads soft and generic; always the measured bezier, never overshoot.
- **Off-grid by accident.** Only the signal may break the grid; snap everything else to column lines.
- **Centred layouts.** Centring a heading or a chart turns it into a slide deck; keep left alignment and asymmetry.
- **Too much at once.** Content stays near 12 % of the frame; fold one section before building the next.

## 10. Engine

What the kit needs (`kit/tokens.js`, `kit/motion.js`, a style module `kit/swiss.js` to write):

- `tokens.js` as measured: `PALETTE` (ground, ink, accent red, greys in `colors`), `TYPE.title` 0.0761 and
  `TYPE.body` 0.0578 of height at 700, `LAYOUT.margin` 0.047 and `align: 'left'`; grain, mottle and vignette off;
  families to the chosen grotesque.
- `motion.js` is already right for this style: `MOTION.enter.ease` is the measured bezier (0.395 s curve; use
  0.44–0.60 s for growths), `MOTION.exit.ease` the exit bezier, `MOTION.camera.panx` the page slide. Add
  `stagger: { interval: 0.25, order: 'left-to-right' }` (derived) and `slot` (0.3 s, `'power4.out'`, inferred).
- `swiss.js` (to write): `columns(n, pitch, gutter)` the grid in design px and `col(i)` to snap; `guides(g, panX)`;
  `grow(g, x, base, w, h, p)` a bar from its baseline; `slot(g, draw, x, y, w, h, p)` a clip-rise; `fold(g, cy, p)`
  the collapse to a centre line; `caption(g, text, x, y, w)` grey text with its rule.

Minimal example (not in the references: a row of three percentages as growing columns):

```js
draw: (g, t) => {
  g.fillStyle = PALETTE.ground; g.fillRect(0, 0, 1920, 1080); guides(g, 0);
  [0.42, 0.67, 0.18].forEach((v, i) => {
    const p = enter(t, 1 + i * 0.25);
    grow(g, col(2 + i * 2), 820, col(1) - col(0) - 24, 520 * v, p);
  });
  slot(g, q => { q.font = `700 ${TYPE.title * 1080}px Inter Tight`; q.fillText('share', col(0), 250); }, col(0), 180, 600, 90, enter(t, 0.4));
  if (t > 3) { g.fillStyle = PALETTE.accent; g.fillRect(col(9) - 12, 300, 120, 120); }
}
```

## 11. Variation space

Each film decides the data, the headings, how many sections, where the signal square lives, the direction of the
page slides (left or right), and whether a section ends with a fold or a slide.

- **Structures:** (1) a long horizontal page read by repeated slides, one figure per column; (2) a single page that
  builds, folds and rebuilds three times with the same square kept; (3) a countdown of numerals, each with one
  small chart beneath.
- **Openings:** (1) the empty grid, guides drawing down from the top one by one; (2) the red square alone, then the
  page builds around it; (3) a caption line first, its rule extending, before any heading.
- **Endings:** (1) everything folds and only one bold word remains bottom-left; (2) the page slides away entirely,
  leaving guides only; (3) the last bar grows past the frame top.
