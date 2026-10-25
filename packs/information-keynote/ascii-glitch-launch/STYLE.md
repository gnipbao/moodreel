# ASCII Glitch Launch — Style Prompt

ASCII Glitch Launch · 字符故障发布片

> A launch teaser in which the type is followed by a motion tracker and keeps breaking into data: glyphs boxed and
> labelled, letters turning to cells, dot-matrix and hatching, scenes passing through an ASCII field, the product shown
> in a montage at twelve cuts a second, the sentence told one short phrase at a time.

## 1. Essence, and what it is not

- **Tracked type.** Glyphs ride a dashed path, each in a thin red or violet box with a mono coordinate label above it and
  a green dot on its centre. The overlay is part of the image, not a debug layer left on.
- **Type that turns into data.** Letters break into square cells, become dot-matrix, fill with diagonal hatching; scenes
  pass through an ASCII field whose cells show colour plus a line glyph picked by brightness.
- **Twelve cuts a second, then a held phrase.** The product appears in a montage that re-dresses one object every 5–6
  frames; between bursts one phrase holds for half a second to a second.
- **One phrase, one scene, one light.** Sentence-case words in a neutral grotesk, each with a single hero light: a neon
  tube, a beam built of cells, a tunnel or ring of particles.
- **Neutral studio, colour from content.** Light grey studio or near-black grounds; colour arrives with what is shown.

Not ASCII / CRT Terminal (no phosphor screen of glyphs; ASCII is a transition and a texture here). Not Dark Tech Keynote
(the edit stutters, the type glitches, colour comes from many UIs). Not a glitch filter (no datamosh, RGB split or VHS:
every glitch is a designed cell, dot, hatch or ASCII field).

## 2. Materials & rendering

- **Grounds**: a light studio grey, 230 across the middle and 173 in the corners, brighter across the middle than a
  round vignette (a measured 16 x 9 light map, `GLITCH.studio`); or near-black carrying a screen-door dither (diagonals
  crossing every 14 px, about ±8 levels). Grain of about 5 levels that holds still: it never moves from frame to frame.
- **Scan lines over everything**: a 4 px row rhythm (rows 2 and 3 of every 4 darker) on almost every scene, strongest
  on light cards (10 levels), 5.5 on the studio, 1.7 on the end card; on cells and dither the rhythm is their own.
- **The cell field**: one pass over any picture, cells 20–28 px at 1080p for a field, 12–16 px on a light object or a
  dim picture. Modes: *ascii* (cell colour plus a glyph by brightness: dotted square, circle, crossed box, a stray
  filled triangle; strokes thinner than a cell still darken it; or the ramp of the beam and the dim eye: a grey ring in
  every dark cell, a slash, a cross, a dot in a box), *dots* (lit cells as rounded squares, a few flickering grey),
  *pixelate*, *hatch* (diagonal stripes inside lit cells), *lines* (line glyphs on black: nothing, a dot, a slash, a
  cross as the picture brightens).
- **Glyph screens**: a picture seen through line glyphs at a tenth of its light, for six frames between scenes, or
  under a whole scene (a dim eye behind "lives on"); a transition that reads black is often one of these.
- **The tracker**: glyph boxes in red #c3263a or violet, 2 px; labels in mono at 18–30 px; dashed paths (10 px dashes)
  with arrowheads; green #3ddc6a centre dots.
- **Light objects**: drawn in cells too (a neon tube's body is a stack of lit cells with a pink glow; a beam is a wedge
  of white cells with a pink edge). Glow only on these and on particles.
- **Content**: UI cards, prompt boxes, app tiles, posts, drawn in code (never real products), in true perspective: a
  page whose prompt grows a quarter from its first letter to its last (vanishing point far to the left), cards on the
  inside of a cylinder. Focus falls off below the line read: the card's near edge soft, the heading beyond it sharp.
- **Light looks**: the lens's light as an ellipse (the far corners at half the light), and on a light card a plateau
  at the light's limit (237–242) that only falls off at the card's edges.

## 3. Colour logic

- The grounds are neutral: near-black (#070607 measured, 48 % of the area) and light grey; neutral area 54 %.
- Colour belongs to content and light: UI, icons, particles, the hero light. Saturated area about 11 % across a film,
  most of it in the montages.
- One glow family per film for the hero lights: magenta to violet in the reference (#662c83 measured; pink #e2338f on
  edges and neon). The tracker's red and green are signals, not accents.
- Type is near-black on light grounds (#1b1b1b) and white on dark ones; inverted flashes swap them for a few frames.

## 4. Type & subtitles

- **The voice**: a neutral grotesk (Inter, OFL), sentence case. Weights read line by line: phrases and the prompt
  Medium (500), scene words Semibold (600), the year 550, a heavy word now and then (800, "starts with"). Hero lines 15–20 % of the frame
  height (measured tiers 15.1 % and 20.1 %), phrases 8.9 %, labels 1.7–2.8 %.
- **The machine**: a mono (JetBrains Mono, OFL) for coordinates and tracked labels; dot-matrix words in its Light
  (250), glyphs set wide apart (400 px a glyph at 610 px): the dots make them look heavier than they are.
- Phrases sit centred or left with generous space; one phrase per scene. Typed in fast: a prompt at about 36
  characters a second, a line at up to 150; a number may roll on a reel (the neighbours grey above and below).
- Subtitles are the phrases themselves, held at the music's pace: 0.5–1.8 s each (median about 0.7 s, measured), one
  to three words for half a second to a second, a sentence about two seconds across its scenes; montage text may
  flash. `moodreel film check` reads that as too short against the library's reading time (CJK chars / 4.5 + other
  chars / 15 + 1.5 s): right for this style, which is watched with its sound. A film that must be read without sound
  holds each line for the library's time instead.

## 5. Motion quality

- **60 fps on ones**; the montage runs on a frame clock of 5–6 frames a slot (0.083–0.1 s).
- **Entrances** short: 0.08–0.33 s, ease-out; typing and cell-breaking count as entrances. **Exits** shorter,
  0.05–0.21 s, or none: most things leave on a cut. **Moves** 0.09–0.29 s, ease-out, half of them overshooting about
  4 % (one curve draws them: bezier(0.433, 1.198, 1.0, 0.927)).
- **Glitches** last 2–12 frames and land on a cut: an ASCII field, a mosaic, an inverted flash.
- **Phrases follow the music's phrases** (120 BPM in the reference: a phrase every beat or two); the montage keeps its
  own frame clock. Kicks may punch a frame (in 20 % of kicks) and beats may flash (33 % of beats): accents, not a rule.
- **Ambient motion**: particle fields rush (a tunnel; a ring turning about 1 rad/s about a centre above its outline's
  middle, its near side fast and its far side slow), the card wall turns (a camera inside the cylinder dollying in and
  turning 0.43 rad over a second, easing out); type tracking creeps; the end card's mark turns 6° toward upright.
- Counters roll fast (0.17–0.32 s).

## 6. Camera grammar

Shots are very short (median 0.10 s, 68 in 15.8 s; 65 cuts, 2 dissolves).

| Move | What it expresses | Can serve |
|---|---|---|
| Slot montage (a cut every 5–6 frames) | abundance, everyone is doing it | many products; many users; many versions |
| Tracked type on a path | a machine reading the words | a date; a claim; a name |
| Break into cells | reality turning to data | a word turning; a scene ending |
| ASCII field | a jump between scenes | any transition |
| Pull back from a hatched close-up | a turn, a "but" | a contrast; a reveal |
| Inverted flash (2–6 frames) | a hit | a beat; a stressed word |
| Glyph screen (6 frames) | a scene dissolving into data | any transition; behind a quiet phrase |
| Slow turn of the mark on the end card | the last word, settled | the logo; the URL |

Text sits centred or left with ≥ 96 px from the edges; content cards may bleed off the frame.

## 7. Sound palette

- Electronic, 120 BPM in the reference: kick, hats, a bright synth; the picture's phrases follow its bars.
- Foley on the glitches: short digital stutters, key ticks for typing, a whoosh into particles, a sub hit on the logo.
- A silence or a single tone under the end card.

## 8. Native moves

- **The tracked word.** A word rides a dashed path, each glyph boxed and labelled with its coordinates, then breaks into
  cells. *Fits:* a year; a product name; a promise.
- **The re-dressed object.** One prompt, tile or post shown in a different design every 5–6 frames while its text keeps
  typing. *Fits:* many tools; many customers; many languages.
- **Hatched to cells.** A huge word, hatched, pulls back and becomes dot-matrix. *Fits:* a turn ("but"); a warning; a
  number.
- **The beam of cells.** A light built of cells sweeping toward a word. *Fits:* a skill; a feature; a moment of focus.
- **The ring and the flash.** A ring of streaks round a phrase, inverted for a few frames, then cooling to another hue.
  *Fits:* a community; a library; a release.

## 9. Pitfalls of the medium

- An ASCII pass that averages a cell loses thin type: take the darkest of the cell's taps so strokes stay as dashes.
- Montage slots shorter than 5 frames read as noise; longer than 8 frames read as a slideshow.
- Real product UIs, logos and posts are not ours to show: draw stand-ins.
- A light ground run through a tone shoulder loses its white: lift the exposure on light scenes.
- A cross dither under 4 % opacity disappears in H.264; above 15 % it reads as a pattern, not a texture.
- A grain that boils reads as motion going another way on a still scene: seed it once.
- A soft copy and a sharp copy of one picture must be added, not stacked, or the ground shows through between them.
- A 12 px cell grid sits on the sampling limit of a 320 px check: a 1 px shift changes its texture score by half.

## 10. Engine

- `kit/tokens.js`, `kit/motion.js`: palette, type tiers, the timings above.
- The style's own modules: `kit/glitch.js` (the voices, typing, the reel, the frame: layer, cell pass, over layer,
  scan lines, a still grain), `kit/cells.js` (ascii, dots, pixelate, hatch, lines; the rings ramp), `kit/tracker.js`
  (glyph boxes, labels, paths, glyph cells), `kit/grounds.js` (studio light map, dark dither, lens, halo, the end
  card's glyph ground), `kit/plane.js` (a page in perspective, focus below a line), `kit/fields.js` (tunnel, ring,
  neon, beam, ring ground), `kit/montage.js` (the slot clock, glitch windows); `GLITCH` in `kit/tokens.js`.

## 11. Variation space

Each film decides the product, the copy and its phrases, the hero lights and their hue family (cyan, lime or amber
instead of magenta), how long the montages run, and the ending mark. Unseen here and open: a vertical frame, a slower
film with fewer montages, voice-over, colour on the grounds, 3D type.

- **Structures**: problem, turn, answer (the reference's arc); a list of features, a montage each; a single tracked
  sentence across the whole film.
- **Openings**: a date typed and rolled; a cursor and an empty prompt; an ASCII field resolving into a face of the UI.
- **Endings**: a mark tracked, then held on white; the URL typed in mono; the name breaking into cells and gone.
