# Blind distillation

Each example film's round-trip project, as a packet holding only its references and Moodreel's measurements, distilled into a STYLE.md by a director who has not read the style, then judged section by section against the library's STYLE.md (`moodreel bench blind`, see `moodreel/bench/blind.py`). §8 passes a style at 8 of 11 sections "same".

Judged: 5 of 5. ✓ same, ~ partly, ✗ different, — absent; * the round trip's own verdict on a section the measurements speak for, · not judged yet.

| code | film (style) | §1 | §2 | §3 | §4 | §5 | §6 | §7 | §8 | §9 | §10 | §11 | same | §8 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A | boot (ascii-crt) | ~ | ~ | ~ | ✓ | ~ | ✓ | ✓ | ✓ | ✓ | ✓ | ~ | 6/11 | fail |
| B | first-light (risograph) | ✓ | ~ | ✓ | ~ | ~ | ✓ | ✓ | ~ | ✓ | ~ | ~ | 5/11 | fail |
| C | morning (pictogram-motion) | ~ | ✓ | ~ | ~ | ~ | ~ | ~ | ✓ | ✓ | ~ | ~ | 3/11 | fail |
| D | shipped (dark-keynote) | ~ | ✓ | ~ | ✓ | ✓ | ✓ | ✓ | ✓ | ~ | ✓ | ~ | 7/11 | fail |
| E | swiss-programme (swiss-motion) | ✓ | ✓ | ✓ | ✓ | ~ | ~ | ✓ | ✓ | ✓ | ~ | ✓ | 8/11 | pass |

## The judge's notes

### A · boot (ascii-crt)

- §1 Essence (partly): Reduces the style to a text terminal. It drops the rule that every image is glyphs chosen by ink density on a grid whose scale is the only camera. Its 'one hue, light only means the phosphor is lit, no green' rule bans the original's green/white phosphors and its one warm surprise.
- §2 Materials & rendering (partly): Warm near-black glass, bloom and scanlines are right, but it forbids the original's glass (slight barrel curvature, rounded mask, fine noise) and prescribes smooth vector mono where the original uses a bitmap-style terminal face (VT323). No afterglow, flicker or phosphor luminance ramp.
- §3 Colour logic (partly): One phosphor with a dim/normal/bold ramp and inverse video is right, but 'never introduce a second hue' contradicts the original's one soft second colour reserved for the emotional object. Amber is fixed where the original allows green or white.
- §4 Type & subtitles (same): LOG-strip subtitles under a rule, typed titles and the hold rule match. The inverse-video tag only appears in §8.
- §5 Motion quality (partly): Constant-rate grid typing and the eased grid push are right. But status words 'stamp in' with an off-grid scale and fade, where the original keeps glyphs on the grid outside declared transformations. Typing as performance (even machine vs uneven human) is reduced to one constant rate.
- §6 Camera grammar (same): Locked screen, push to the title, and clear/power as on-screen transitions match. Pull-out, scroll, push into a glyph and text-becomes-image are absent but unshown.
- §8 Native moves (same): Log file, promote-to-title, power-off and cursor moves match. Picture-made-of-words is absent (unshown); the single colour change is excluded by §3.
- §9 Pitfalls of the medium (same): No overlap with the original's pitfalls, which are about glyph pictures and engine traps (unshown), but nothing here contradicts the style.
- §10 Engine (same): Covers typing on a grid, grid zoom, power on/off, bloom and scanlines. No density ramp or curved-glass phosphor post.
- §11 Variation space (partly): Structures, openings and endings fit the style, but '§3 fixes the palette' closes choices the original leaves open (the phosphor colour, and whether the second colour appears at all).

### B · first-light (risograph)

- §1 Essence (same): Close. Misregistration is framed around the type, and the inks are named as teal and coral rather than chosen per film.
- §2 Materials & rendering (partly): Multiply inks, stepped halftone, speckle fixed to the paper and the knockout trap are right. But misregistration is not a per-plate property of everything printed (only type is offset), plates get no separate screen angles, and the 'at most two plates per area, one of them a tint' rule is missing.
- §3 Colour logic (same): Riso colour logic holds: spot inks, tints by halftone, overprint as the darkest value, cream paper, no black. But it fixes teal + coral and confines coral to a ~3 % accent that never fills a field.
- §4 Type & subtitles (partly): Double-hit title and roller entrance match, but subtitles lose the paper-white knockout strip; 'never a boxed caption' contradicts it.
- §5 Motion quality (partly): On twos, fixed per-shot registration and the constant-speed roller are right. But the registration kick on accents and the drift/snap are missing, though the film kicks at 9.5 s. 'step(t, 12) for everything' would also step camera moves, which the original keeps on ones.
- §6 Camera grammar (same): Locked composition, roller transitions and no dissolves match. The moving-camera vocabulary (tracking, push into halftone, match cuts) is absent but unshown.
- §7 Sound palette (same): Consistent. The print machine's own sounds (drum ka-chunk, feed) are reduced to a roller swish.
- §8 Native moves (partly): The moves are generic pulls and rises. The plate moves the film used are missed or misread: the third colour where two inks meet (the sun's reflection over the sea), a plate lifting away to leave one ink (read as a 're-ink'), and the registration kick.
- §9 Pitfalls of the medium (same): Jitter, moiré, gradients and pure black/white match the original's concerns. The 'three halftones = mud' rule is missing.
- §10 Engine (partly): Shapes are built as multiply layers rather than plates with their own offsets, so only text misregisters. No kicks/drift and no per-plate gate.
- §11 Variation space (partly): Inks are fixed by §3 and subjects confined to bands and discs, while the original's first free choice is the inks and what each plate means. Plate-based structures (subtraction, one ink left) are missing.

### C · morning (pictogram-motion)

- §1 Essence (partly): The card, pictogram on a disc, bilingual type and tonal mosaic are right. But beat lock (every cut and key pose on a beat) becomes only 'equal-length cards', row shifts are absent, and 'one family, nothing warm' rules out the chapter-per-hue structure.
- §2 Materials & rendering (same): Close. The small motif cells and the light sweep on the disc are missing, and light mux grain is ruled out.
- §3 Colour logic (partly): Five tones of one hue, cream for type and depth by value are right, but 'never add a second hue' contradicts the original's set of five hues with one hue per chapter.
- §4 Type & subtitles (partly): Title, CJK line, mono HUD and progress ticks match. But subtitles become the CJK title line with 'never a running caption', which contradicts narration captions as a mono line on a chapter-hue band; the second language is hard-wired, not a switch.
- §5 Motion quality (partly): Mask slide-up type, the figure arriving in parts and fast-out pops are right. But timings are in seconds with no beat grid, 'the mosaic never moves within a card' contradicts the drifting and beat-jumping rows, and there are no grid transitions.
- §6 Camera grammar (partly): Locked frame and the text/stage split match, but 'hard cuts only' and 'the camera never moves' contradict the grid-snapped transitions (sliding rows, dropping columns, iris, tile flip) and the grid-aligned camera moves.
- §7 Sound palette (partly): Picture-locked cuts and per-element foley fit, but the percussion spine is missing (mallets and pizzicato only), and a voice line per card exceeds 'one line per chapter at most'.
- §8 Native moves (same): Step card, counter and bilingual pair match. Chapter = colour is excluded by §3; the pace ladder and long take are unshown.
- §9 Pitfalls of the medium (same): Consistent. The light-hue contrast and horizontal-pose pitfalls are unshown.
- §10 Engine (partly): Mosaic, figure, card and progress cover the parts, but timing is seconds per card with no beat-based edit list, and the mosaic is fixed per card, with no row shifts or grid transitions.
- §11 Variation space (partly): 'One hue only' removes the palette and chapter choices; the structures and endings otherwise fit the style.

### D · shipped (dark-keynote)

- §1 Essence (partly): Dark cool stage, UI as protagonist and one reserved accent are right. But 'almost empty, one object at a time' as the essence rules out the disorder-to-order drama of generated UI, and beat precision is not stated.
- §2 Materials & rendering (same): Close. The upper-centre lift and off-centre cool glow, 1 px borders with an inner top highlight, 2.5D depth and the light reveal are not described.
- §3 Colour logic (partly): Cool neutral ladder and one reserved accent are right. But 'no second accent; errors and categories by words and greys' contradicts the temporary problem colour and the category hues in motion, and lime is fixed rather than chosen per film.
- §4 Type & subtitles (same): Toast-style status pill with an accent dot, Inter plus mono filenames, and the number alone all match. One-line headlines are ruled out in §1.
- §5 Motion quality (same): Close. Fast-out small-overshoot spawns, slide-in rows, squash exits and a still stage match. Landing on the beat appears only in §7, and the accent's 13.6 % overshoot exceeds 'one small overshoot'.
- §6 Camera grammar (same): Locked frame, collapse/expand transitions and one focal element match. The 2.5D camera vocabulary is absent but unshown.
- §8 Native moves (same): Checklist, collapse, hero numeral, lime detail and status pill match the film. Generated accumulation, snap grid, freeze, light reveal and number scramble are unshown.
- §9 Pitfalls of the medium (partly): 'Busy stage: two objects at once breaks the density' contradicts generated accumulation and the snap grid. The original's perspective, glint and slot-filling pitfalls are absent.
- §10 Engine (same): Grid, card, row, pill, glow and collapse cover what was shown. No 2.5D camera, light reveal, scramble or trails (unshown).
- §11 Variation space (partly): 'Palette, density and the snap/collapse grammar stay' fixes the accent and the calm density, which the original leaves open. No problem image or camera path.

### E · swiss-programme (swiss-motion)

- §1 Essence (same): Close. Beat landing is not stated, the exception appears only in §3/§8, and 'data as solid shapes' leans toward the charts the original warns against.
- §2 Materials & rendering (same): Close. No spread (programme page / artifact page), no baseline grid, and no 2D camera matrix with scale and rotation.
- §3 Colour logic (same): Close. Red is fixed and the signal is confined to a square drawn above the type; the original lets it be red, orange, ultramarine or green, and allows black type on it.
- §4 Type & subtitles (same): Close. Word-by-word clip reveal of subtitles and optically flush-left numerals are missing.
- §5 Motion quality (partly): House bezier, no overshoot, clip-rise, baseline growth, fold and the linear exception are right. But durations are not note values landing on the beat, slots get a third curve (power4.out) against 'two curves only', and ripples run left to right rather than by distance from their cause.
- §6 Camera grammar (partly): Locked spread and page slide match, but 'never zoom, never rotate' and 'no wipes' contradict the original's rotate 90°, push/pull moves and wipe transitions.
- §8 Native moves (same): Close. The programme move and snap = beat are missing.
- §10 Engine (partly): Columns, guides, grow, slot, fold and caption cover the parts. But there is no snap that lands on a beat (timing is in seconds), no knife line or linear exception track, and slot bakes in a third curve.
- §11 Variation space (same): Close. Signal colour and 'the exception or none' are not listed as choices.

