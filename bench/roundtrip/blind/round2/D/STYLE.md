# Lime Signal Dark UI — Style Prompt

Lime Signal Dark UI · 青柠信号暗色界面 · 1920×1080

> Product-interface motion on a near-black navy stage: one clean UI object at a time (a card, a checklist, a
> numeral, a status pill) pops into a spotlit centre, does its job with small snappy overshoots, implodes, and
> gives way to the next. A single acid-lime signal is the only colour, and it means "done".
> References (grammar only): dark-mode developer tools and changelog screens (panels a step above the ground,
> lowercase labels, monospaced file names); product launch micro-animations (spring pops, staggered rows, check
> ticks). Never copy a product's interface, icons, wordmark or typeface.

## 1. Essence, and what it is not

1. **A dark navy stage, spotlit**: the ground (#0e1017, L* 4.9) covers 91 % of the picture; a strong vignette
   (0.73; 15–27 grey levels lost at the corners) leaves a soft pool of light in the middle, with a faint square
   grid on the ground (by eye).
2. **One object, centred, small**: content covers about 1 % of the frame (median), centred (centroid 0.50, 0.51),
   with at least 23 % clear margin on every side.
3. **UI panels a step above the ground**: cards in #1b2130 with rounded corners, inset rows a step darker, grey
   checkboxes, a monospaced file name in the title bar (by eye).
4. **Lime means done**: #b3ed4a (chroma 81) covers 0.1 % of the pictures, glows, and appears only for success.
5. **Snap in, implode out**: entrances 0.23–0.31 s with a small overshoot (100 % of read entrances, median 5 %);
   exits 0.14–0.20 s, shrinking toward a line.

Not a **light SaaS explainer** (no white canvas, no illustrated people, no brand rainbow), not a **hacker terminal**
(monospace only for file names; text is a grotesque), not a **keynote device reveal** (no 3D devices, no photography,
no gradients beyond the vignette), not **glassmorphism** (no blur-through panels, no translucent stacks).

## 2. Materials & rendering

- **Stage**: flat navy ground, darkened toward the corners by a strong radial vignette (0.73, range 0.71–1.01) with
  its light centred a little above the middle (by eye); slow variation (mottle 3.10) from the vignette and grid.
- **Grid**: hairlines one step above the ground in a square lattice, barely visible, fixed to the stage (by eye).
- **Panels**: solid fills (#1b2130 for a card, darker inset rows), rounded corners, a soft dark drop shadow under
  the card (by eye). No borders brighter than the panel, no gradients inside panels.
- **Glow**: only the lime element glows: a blurred copy of itself in its own hue (the measured halo tones #7ea63c,
  #455a2c, #263023 are its falloff).
- **Edges** crisp (0.471). **Grain** fine (1.17): treat as codec; the stage reads clean.
- Layer order: ground → grid → vignette light → object (shadow, panel, content) → glow. The vignette and grid are
  screen- and stage-fixed; objects move over them.

## 3. Colour logic

- **Neutral navy everything**: 92 % of the picture is neutral; mean chroma 5.1; no hue family large enough to count.
- **Value steps carry the UI**: ground (L* 4.9) → panel (12.7) → borders and dim greys (23.6–35.3) → secondary
  labels (49.7–61.0) → light grey (77.6) → text (92.4, 15.63:1 on the ground).
- **One signal colour**: the lime accent (13.69:1 on the ground) appears only for a completed state: a filled box,
  a status dot. Never for text, never for decoration, never two lime objects competing.
- No warm colours, no white (#e5e9f2 is the lightest), no gradients except the vignette's light pool.

Example (the measured set): ground #0e1017 · panel #1b2130 · greys #353841, #4e535e, #717681, #8e939e, #bcc0c9 ·
text #e5e9f2 · signal #b3ed4a. Another single signal hue (a cyan, an orange) is open if it keeps this rarity (§11).

## 4. Type & subtitles

- **One neo-grotesque, medium weight, lowercase labels** (measured regular, 500; by eye Inter-like): an OFL face
  such as Inter 500. **Monospace** only for file names and code (by eye; JetBrains Mono 400), in a mid grey.
- **Sizes** (line ink, share of frame height): a hero numeral 19.2–19.3 % (kit 0.2139 font size); row labels
  2.4–2.6 % (3.1 % with descenders; kit body 0.0278); pill label 3.5–3.6 %; file name 1.8–1.9 %.
- **Placement**: everything centred on the stage; a status pill sits low (its label at 83.5 % of the height),
  centred under the object.
- **Subtitles** are UI text: a pill or a row in the same face, in text grey on a panel, never floating on the bare
  ground in bold. Each stays ≥ CJK chars / 4.5 + other chars / 15 + 1.5 s.

## 5. Motion quality

- **24 fps on ones** (share 0.88); smooth tweens, nothing stepped.
- **Entrances** 0.23–0.31 s (median 0.31 s), out with overshoot, median 5 % (two read at 4.9–5.0 %): the style's own
  curve, cubic-bezier(0.343, 1.344, 0.676, 1.025) (fitted through two tweens, residual 0.0049); family not claimed
  (best guess back.out(1.2)). Vocabulary: scale-pops from small (scale from 0.19–0.45, median 0.38) with a slight
  rise, and slides in from the right (travel median 11.8 % of the frame).
- **Sequential, not simultaneous**: list rows arrive one by one about 0.5 s apart (row arrivals at 0.69, 1.19, 1.75
  and 2.21 s); a row's box ticks as the next row lands (by eye).
- **Signal pop**: the lime element pops harder: 0.21 s from 0.56 of its size with a 13.6 % overshoot (one read;
  best guess back.out(2.2)).
- **Exits** 0.14–0.20 s (median 0.17 s), about half the entrance: things shrink to a third of their size
  (0.31–0.49) and squash toward a horizontal line at the centre (travel median 7.1 %). The ease is not claimed;
  most guesses are ease-in (power3.in, expo.in, back.in), so ease-in (inferred).
- **Holds**: median 0.58 s between events (p75 1.08 s); motion only 22.5 % of the time. The final state holds.
- **Never moves**: the ground, grid and vignette; the camera.

## 6. Camera grammar

Locked (1 of 1 shot, no camera move measured). One continuous take; scenes change by implosion and an empty beat
of bare stage, not by cuts (no cuts, dissolves or dips measured in the one shot).

| Move | What it expresses | Can serve |
|---|---|---|
| Locked stage, object popping in | focus on one thing at a time | a feature; a metric; a state |
| Implode to a line, empty beat | closing a chapter cleanly | before/after; "next"; collapsing complexity |
| Staggered rows | progress, a process completing | a checklist; a pipeline; onboarding steps |
| Signal pop with glow | success, a decision made | "done"; "live"; "approved" |

Framing: one object, centred, inside a 23 % margin; the status pill low and centred. Unseen and open: a cut on
bare ground between two stages, a slow push toward the object (keep the grid fixed to the stage so the push reads).

## 7. Sound palette (inferred: the references are silent)

Clean interface sound: a soft tick for each checkbox, a light airy swish for each row's slide, a muted "pop" for
card and numeral entrances, a short inhaled whoosh for the implosion and then real silence for the empty beat; the
lime signal gets the one bright, tonal sound (a pluck or chime). Under it a low, warm synth pad or sub drone; no
drums unless the film needs momentum. Dry, close, quiet; −14 LUFS, effects slightly forward of the pad.

## 8. Native moves

- **Checklist build.** A card pops from the centre, rows slide in from the right about 0.5 s apart, each box ticks
  as the next row lands. *Fits:* a release's tasks; a setup guide; a recipe's prep.
- **Implode.** Everything shrinks and squashes into a centre line in under 0.2 s, ease-in, then one empty beat.
  *Fits:* clearing a backlog; ending a phase; turning many things into one.
- **Numeral on stage.** A large medium-weight number pops alone into the light. *Fits:* a version; a price; a year.
- **Signal pop.** A small rounded lime square pops with a stronger overshoot and glows. *Fits:* a deploy going live;
  a goal reached; an "on" switch.
- **Status pill.** A low centred pill with a dot and a lowercase word confirms the state. *Fits:* "shipped";
  "online"; "paid".

## 9. Pitfalls of the medium

- **Banding in the vignette**: a smooth dark gradient bands in 8-bit H.264; add the measured fine grain (1.17) or
  dither, and encode with enough bitrate.
- **Grid moiré**: one-pixel hairlines flicker when anything scales over them; keep the grid fixed and faint.
- **Lime overuse**: more than one lime element, or lime text, kills the signal; keep it near 0.1 % of the frame.
- **Overshoot creep**: springs above about 5 % on ordinary entrances feel toy-like; save the stronger pop for the
  signal.
- **Glow that greys out**: a glow in white or another hue muddies the navy; glow the lime in its own hue only.
- **Busy frames**: two panels at once break the one-object rule; implode the first before the next arrives.

## 10. Engine

What the kit needs:

- `kit/tokens.js`: `PALETTE` as measured, plus the greys and a `surface` (#1b2130); `TYPE.display`/`TYPE.text` set to
  the chosen grotesque and a mono for file names (placeholders are Helvetica); `TEXTURE.vignette` 0.728 through
  `vignette()`, grain 1.165 optional.
- `kit/motion.js`: `MOTION.enter.ease` is null though the class was read twice: set it to
  `'bezier(0.343,1.344,0.676,1.025)'` at 0.31 s; `MOTION.exit` 0.167 s with an ease-in (inferred); add a row
  `stagger` of about 0.5 s (derived from the arrival times, not measured as a stagger) and a `signal` pop (0.21 s,
  from 0.56, back.out(2.2) as a guess).
- A style module `ui.js`: `stage(g)` (ground, grid, light pool, cached), `card(g, rect, title)` (panel, shadow, title
  bar with mono name), `row(g, y, label, checked)`, `pill(g, x, y, text)`, `glow(g, draw)` (blurred self-copy),
  `implode(g, t, at, draw)` (scale y to a line and x to a third about the centre).

Minimal example, a three-step progress bar filling and turning lime (not in the references):

```js
// positions, sizes and times in this example are illustrative, not measured
stageBg(g);
const p = enter(t, 1.0);                                             // card pops in on the house curve
card(g, centreRect(0.5 * W * lerp(0.38, 1, p), 0.12 * H), 'deploy.log');
[0, 1, 2].forEach(i => segment(g, i, tween(t, 1.5 + i * 0.5, 0.31, 'bezier(0.343,1.344,0.676,1.025)')));
if (t > 3.2) glow(g, g => roundSquare(g, W / 2, H / 2, value(t, 3.2, 0.21, 0.56, 1, 'back.out(2.2)'), PALETTE.accent));
```

## 11. Variation space

Each film decides which UI objects it shows (cards, rows, numbers, charts, toggles), their order, how many stages it
runs before the signal, the signal hue (one, rare), and how long the final hold lasts. Unseen and open: a cut
between stages on bare ground, a slow camera push, a vertical frame (the same centring and margins), a counting
number (keep the entrance curve for its arrival).

- **Structures**: a problem card imploding into one fix card; a pipeline of three stages, each built then
  imploded, ending on one signal; a list that grows, ticks off, and collapses into a single number.
- **Openings**: the bare spotlit stage with the grid for a beat; a single pill already on screen saying what is
  about to happen; a numeral popping in first.
- **Endings**: the signal alone, glowing, held; the status pill turning its dot lime; the stage emptying to the
  grid and light pool.
