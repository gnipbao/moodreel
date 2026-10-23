# Blind distillation

Each example film's round-trip project, as a packet holding only its references and Moodreel's measurements, distilled into a STYLE.md by a director who has not read the style, then judged section by section against the library's STYLE.md (`moodreel bench blind`, see `moodreel/bench/blind.py`). §8 passes a style at 8 of 11 sections "same".

Judged: 5 of 5. ✓ same, ~ partly, ✗ different, — absent; * the round trip's own verdict on a section the measurements speak for, · not judged yet.

| code | film (style) | §1 | §2 | §3 | §4 | §5 | §6 | §7 | §8 | §9 | §10 | §11 | same | §8 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A | boot (ascii-crt) | ✓ | ~ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 10/11 | pass |
| B | first-light (risograph) | ✓ | ✓ | ✓ | ✓ | ~ | ~ | ✓ | ~ | ✓ | ✓ | ✓ | 8/11 | pass |
| C | morning (pictogram-motion) | ✓ | ✓ | ✓ | ~ | ~ | ~ | ✓ | ✓ | ✓ | ✓ | ✓ | 8/11 | pass |
| D | shipped (dark-keynote) | ✓ | ✓ | ✓ | ✓ | ~ | ~ | ✓ | ✓ | ~ | ✓ | ✓ | 8/11 | pass |
| E | swiss-programme (swiss-motion) | ✓ | ✓ | ✓ | ✓ | ~ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | 10/11 | pass |

## The judge's notes

### A · boot (ascii-crt)

- §1 Essence (same): Close: the essence leaves out pictures built from glyph ink density and the curved glass. The references show only text on a flat screen.
- §2 Materials & rendering (partly): States a flat, uncurved tube with no reflection and a smooth outline grotesque mono (JetBrains/Plex 800). The original has slight barrel curvature, a rounded mask, a faint reflection and a bitmap-style terminal face (VT323). The glyph-density picture pipeline and text afterglow are also missing (unseen).
- §3 Colour logic (same): Close: no allowance for the single soft second colour switched on once. The film never used it. The one-phosphor brightness ramp and inverse video match.
- §4 Type & subtitles (same): Close: the LOG-strip subtitle matches (dim rule, inverse tag, prompt, typed on). It does not say subtitles are typed in sync with the voice. For the typeface, see §2.
- §6 Camera grammar (same): Close: the grid-scale camera becomes a zoom on one promoted word. Pull-out, push into a glyph, scroll and text-to-image are unseen.
- §7 Sound palette (same): Close: the inferred palette is consistent (analogue synth, relays, hum, silence). It calls the music dry, where the original uses long reverb on pads.
- §8 Native moves (same): Close: 'picture made of words' and the single colour change are absent (unseen). Power on/off, the log, the cursor wait and the promoted word are all moves from the original.
- §10 Engine (same): Close: no glyph atlas, density ramp or CRT post-process (curvature, multi-level bloom). The references never needed them.

### B · first-light (risograph)

- §1 Essence (same): Close: limits the style to two inks (the original allows 2-3) and generalises the film's full-bleed band layout.
- §2 Materials & rendering (same): Close: missing the paper knockout halo around figures, a screen angle per plate, and the 'two plates per area, at most one as a tint' rule.
- §5 Motion quality (partly): Registration is fixed for the whole film, with no kick or drift. The film's 12 px registration kick at 9.5 s was read as a 'pop' exit. 'Nothing moves on ones / step every draw' would also step camera moves, which the original keeps on ones.
- §6 Camera grammar (partly): The locked framing is right. But its rule for a pan keeps the halftone screen fixed to the sheet, which contradicts the original: the screen stays fixed and the image slides under it, as if each frame were printed anew. It also never rules out dissolves or soft wipes.
- §8 Native moves (partly): Overprint, layer pulls and the misregistered title are there. Missing: plates as narrative (the film ends with the warm plate lifting away, read here as a wipe or ink swap) and registration as rhythm (kick, drift).
- §9 Pitfalls of the medium (same): Close: missing the 'three halftones = mud' and one-plate-silhouette rules.
- §11 Variation space (same): Close: variation stays within a cool+warm pair and sheet assembly. A third ink and characters are not opened (unseen).

### C · morning (pictogram-motion)

- §1 Essence (same): Close: row shifts (the original's signature) and 'chapter = hue' are not in the essence; the film shows neither. 'No multi-hue palettes' should apply per card only.
- §3 Colour logic (same): Close: reads a single chapter. The five-hue chapter set, dark type on light hues and low-versus-full pattern contrast were never exercised.
- §4 Type & subtitles (partly): Title, translation line, mono corners and tick bar match. But subtitles are told to replace the translation line in its style. The original puts captions in a mono line on a hue band at the bottom and keeps the bilingual card intact.
- §5 Motion quality (partly): Beat lock, expo-out arrivals, mask slide-up with the second line about 0.08 s later, and the figure assembling from alternating sides all match. But it says the tile field never moves within a card, which contradicts the breathing rows (alternating drift, quarter-cell jumps on beats). No pace ladder.
- §6 Camera grammar (partly): The locked flat frame and the text/stage split match. But cards change by hard cuts, where the original uses rotating grid transitions (sliding rows, dropping columns, push, quarter-discs, iris, tile flip) and moves the camera along the grid.
- §8 Native moves (same): Close: chapter = colour, pace-ladder runs, long take, count-up and icon wall are unseen. 'One verb per item' is reduced to an idle bob.
- §11 Variation space (same): Close: every film is held to one hue and 8- or 16-beat cards. Chapter hues and half-length rapid-fire runs are not opened (unseen).

### D · shipped (dark-keynote)

- §1 Essence (same): Close: the essence leaves out precision-as-beat-lock and the disorder-to-order contrast (generated UI).
- §2 Materials & rendering (same): Close: says no borders brighter than the panel, where the original has a 1 px ~8% white border and an inner top highlight. 2.5D depth and light reveal are unseen.
- §3 Colour logic (same): Close: narrows the accent to success states only. The original reserves it for what the product is or does (protagonist, CTA, key number).
- §5 Motion quality (partly): Snap entrances with about 5% overshoot, short spawns and CRT-off squash exits match. Missing: 'everything lands on the beat'. The film runs on a 120 BPM grid; rows were noted 0.5 s apart, but the measurement flagged no beat.
- §6 Camera grammar (partly): The locked, centred, single-focus framing matches. But scenes change by implosion plus an empty beat of bare stage, and it opens cuts on bare ground. In the original every shot change is a UI expand or collapse, with no blank frames.
- §8 Native moves (same): Close: generated accumulation, snap grid, light reveal, glyph-noise number and freeze are absent (unseen). The numeral, the implosion and the status pill fit.
- §9 Pitfalls of the medium (partly): 'Busy frames: two panels at once break the one-object rule' contradicts the original's generated accumulation and full grids, whose pitfall is having too few elements. Adding grain against banding also goes against 'no grain'.

### E · swiss-programme (swiss-motion)

- §1 Essence (same): Close: 'every move lands on a beat' is not in the essence. The exception idea is carried by the red square in §3, §5 and §8.
- §3 Colour logic (same): Close: the signal is limited to one square and never a bar. The original lets any single element carry it and allows black type on it.
- §5 Motion quality (partly): The house curve (about .7,0,.2,1), clip-rise, midline collapse, knife strike and the linear exception all match. Missing: durations as note values that land on the beat. The film is on a 120 BPM grid; the 0.25 s staggers were seen, but no beat rule was drawn. Ripples are ordered left-to-right rather than by distance.
- §8 Native moves (same): Close: 'snap = beat', 'programme' and 're-flow' are absent, and the knife cut is folded into the collapse.

