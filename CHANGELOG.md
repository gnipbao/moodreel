# Changelog

## Unreleased: the set by night, the sea as water

- `remaking.md`, "The set by night, and the sea as water": the typography remake's eighth round, on four more notes
  (compare 0.689 to 0.695, Jev 0.608 to 0.616): a fall timed by its curve; a set by night is the set by day with the
  lights changed (a camera fitted to the reference's layout, per-shot settings for what shots share); a darkening matched
  by its curve; water as waves in perspective with a soft, twinkling path and no white-out the reference lacks; an
  inline comment that switched a scene's lights off. "The typography film, in sum" now counts eight rounds.

## Unreleased: the motion designer's review

- `moodreel review` reviews a cut as its motion designer too (motion.md, motion-N.jpg): the reference's snaps (frames
  where its picture changes at once: a cut, a slam, a shatter, a flash) and whether the remake meets each on time, late
  or early, weaker, eased into a fade, or misses it; the remake's snaps the reference lacks; every 0.6 s the pictures'
  speed (optical flow) and change in place, flagging spans still or slow where the reference moves and fast where it
  holds; each flagged moment frame by frame, the reference over the remake. `--only stills|motion` runs one half. The
  remake loop's fifth step is now both reviews.
- `remaking.md`, "The motion designer's review" and "The typography film, in sum (seven rounds)": the fourth manual
  test concluded at compare 0.689 and Jev 0.608 (from 0.529 and 0.506). A still review can't see how a thing arrives;
  name the film's arrival grammar and build it once; a move's shape before its size; a figure walks with weight;
  details kept in motion; a colour fixed from stills can break a motion; the layout was right from the first cut, and
  detail and speed made the gain; when a review's fixes move the means by about 0.01, review another way.
- `directing.md`: the seventh round's readings (a name as an image, crows over 乌台; an arrival as a blow; a shut world
  closing in a circle; weather as a beat; a walk as weight and water).

## Unreleased: the producer's review

- `moodreel review <reference> <remake> --shots f --out d`: every window at full size beside the reference (sheets)
  and its ground, ink and accent colours audited, reference against remake (CIE76 dE; review.md flags those a viewer
  sees as off). The remake loop's fifth step: review a cut before it is shown, list the faults, read each shot's purpose,
  then fix.
- `remaking.md`, "The producer's review": the typography remake's fifth round (27 faults found, compare 0.638 to
  0.662, Jev 0.556 to 0.586): review every window, not the weakest; colour per part of the palette; build what a shot
  is for; draw the subject as its makers would (ink bamboo, a monk); fit a 3D camera to the layout; read the pixels'
  parts when the eye's score and theirs part; tools that edit code need their own boundaries.
- `directing.md`: the fifth round's readings (a transition as the next shot seen from elsewhere, a flight with a
  destination, colour leaving as an event, where the camera stands).

## Unreleased: words as the picture

- `remaking.md`, "Words as the picture": the fourth manual test, an 83 s motion-typography film (Su Shi, 定风波), four
  rounds: compare 0.529 to 0.638, Jev 0.506 to 0.556. Type read as families and told apart by their marks (〇, an
  upright Kai, a dotted zero); sizes from measured ink, not contact sheets (wrong by 1.4-2.8 times); particles as
  matter with a source and a destination; the reference's camera in a flat film; no texture it doesn't have; the
  weakest windows read at 640 px; the flow by cells in a flat film; a ground per scene; a pull-back as a field; a 3D
  camera composed from the layout.
- `directing.md`, "What a typography film's reading found": the three named shots read for their meaning (confinement
  then the charge, a collapse as gravity, an exit that lingers), and the motion grammar they gave.

## Unreleased: speed, window by window

- `moodreel compare --motion <window>[,<window>]`: where those windows' pictures move, when and which way. It shows the
  speed every 0.2 s and each 4 x 4 cell's mean flow, the reference's beside the remake's. An orbit shows its far cells
  running one way and its near ones the other; a dive shows its near cells climbing. A camera fit can read either as
  still, or as the move it should have been.
- `remaking.md`, "Speed, window by window": the thirteenth round. The 3D remake's off-speed windows were retimed by
  where the camera is, not only how fast it goes (the march dove where the reference rises: 2.55 to 1.57; the crowd is
  an orbit, not a tilt: 0.55 to 0.81). Also: a lock that lets go throws the camera, a paced camera stops where its
  measurement drops out, and a lock couples the windows it spans. `compare` 0.657 to 0.673, Jev 0.418 to 0.420.

## Unreleased: Blender's look in WebGL

- `kit/gl.js`: `post({ agx: 1 })`, Blender's AgX tone curve (three.js's implementation) in place of the film shoulder.
- `remaking.md`, "Blender's look in WebGL": the twelfth round. The 3D remake's world brought to its Blender render window
  by window (mean dE 20.0 to 6.4): AgX, the sky as environment light with a ground bounce, ambient occlusion from depth,
  and a shader-cache key per voxel variant (three.js caches a shader by the text of `onBeforeCompile`: the trees and
  walls had run the terrain's shader for four rounds). Matching the colour cost detail against the reference (`compare`
  0.651 to 0.640); local contrast after the look gave it back (0.657, the best of the twelve rounds; dE 7.1).

## Unreleased: the renderer's share, measured

- `remaking.md`, "The renderer's share, measured": the 3D remake's forest window rebuilt in Blender EEVEE from the
  film's own data (same layout, camera, critter): tone error 21 to 8, compare 0.66 to 0.68, structure and Jev's
  likeness unchanged; the renderer owns the colour, not the picture.

## Unreleased: a lens that carried on

- `remaking.md`, "A lens that carried on": the eleventh round of the 3D remake (a re-keyed span ends where it found the
  camera; diff a round against the last one; measure before believing an impression). The keyboard and the close-up
  back (0.59 to 0.62, 0.55 to 0.60), compare 0.651.

## Unreleased: the desk hop, the night hill, colour in the light

- `remaking.md`, "The desk hop, the night hill, colour in the light": the tenth round of the 3D remake (a lock needs
  subjects that pin it; streaks are a camera move; light what the reference lights; a night shot as a slope, a brow
  and a line; colour is in the light; when the judges disagree, look). The desk hop 0.48 to 0.68.

## Unreleased: moves with a shape

- `kit/follow.js`: an anchor's `speed` (0 holds, above 1 rushes through) or `speed: [in, out]` (a burst away, a stop
  dead); `follow(..., { pace: true })` covers the path between anchors in step with the reference's measured speed,
  so each move takes the reference's shape instead of one even pace between anchors.
- `moodreel camera`: each window's shape, its speed by thirds (speeds up, slows down, in and out, one pace); with
  `--against`, a move whose shape differs is named ("keeps one pace where the reference slows into its end").
- `kit/gl.js`: `post({ saturation })`, colour against grey after the tone shoulder.
- `remaking.md`, "Colour, scenes in the keys, moves with a shape": the ninth round of the 3D remake (colour measured as
  saturation and value; one character, one material; a key as a staged scene; a move's shape measured, then paced;
  compare 0.649, move shapes agreeing 22 of 36).

## Unreleased: detail, and the making acted

- `remaking.md`, "Detail, and the making acted": the eighth round of the 3D remake. Detail as the reference's grain at
  its size (turf tufts, a lawn's speckle, trees in contrasting cubes, keys read by their light), what is made cut into
  what is there, every making a beat the subject acts and the camera answers, an interface on the reference's clock
  (compare 0.648, Jev's likeness 0.418, director's notes 77).
- `directing.md`: "Every making is acted" added to the motion grammar.

## Unreleased: a director's reading

- `moodreel direct <reference> --shots f [--against <remake>] [--md f] [--allow-image-upload]`: opt-in Jev vision. Each
  window read as a director and a motion designer would: shot size, angle, composition, light, where the eye goes;
  from its start, middle and end frames, the camera's move, speed and ease, the subject's action, a reveal. Against a
  remake: the notes where it reads differently.
- `skills/moodreel/references/distill/directing.md`: reading a film as its director and its motion designer before
  remaking or distilling it; the 3D film's reading and its motion grammar.
- `remaking.md`, "The director's reading": the seventh round (compare 0.645, Jev's likeness 0.406).

## Unreleased: the opening, the dive, the fall, the meadow

- `kit/lock.js`: a scattered subject (a river, a town, a crowd) as `{ cloud: points }`, boxed by its points inside the
  frame; `visibleOf(camera, subject)`.
- `remaking.md`, "The opening, the dive, the fall, the meadow": the sixth round of the 3D remake (Jev's likeness 0.393,
  disagreeing checks 1; a lock only helps subjects laid out like the reference's; one colour per light; a falling
  camera zooms the ground; keep the film under version control).

## Unreleased: Jev looks, and the remake is locked to what it sees

- `moodreel look <reference> <remake> --shots f --spec look.json [--allow-image-upload]` (and `pass --vision`): opt-in
  Jev vision (jev-1.14.0, TypeSafe-Danger-Zone-Images). Frames of both films at three moments a window: each named
  subject's place and size in the remake against the reference (px), the checks that disagree (legends, a face, a
  title), how alike the pair is; the reference's answers cached by frame. Frames go as 1280 x 720 JPEG only with the
  flag; otherwise only `image-transfer-preview.json` is written.
- `moodreel track <video> --spec f --subjects a,b --checks c [--every s] [--js f]`: each subject boxed frame by frame,
  and the checks answered (a face, a heading), as `TRACK` and `CHECKS` for a film.
- `kit/lock.js`: the remake's camera and moving subjects solved onto the reference's boxes (visible parts, absent
  subjects pushed out of frame, a subject on its surface, smoothed and held moment to moment so it adds no motion).
- `render.mjs report <film>`: a film's own diagnostics (`window.REPORT()`), the lock's errors before and after.
- `remaking.md`, "Jev looks": the fifth round of the 3D remake (compare 0.614 to 0.637, Jev's likeness 0.332 to 0.383,
  disagreeing checks 17 to 3; names and the logo as the reference's when the maker may use them).

## Unreleased: judging faster, with Jev as an option

- `moodreel pass <reference> <film> --shots f --name pN [--against passes/pM] [--jev --allow-text-upload]`: one pass of
  a remake in one command: render, every window scored, the camera read, a contact sheet; about two minutes for a
  64 s film.
- `moodreel compare` scores its windows in parallel (36 windows: 90 s to 16 s, the same numbers).
- `moodreel triage <compare.json> [--camera f] [--allow-text-upload]`: opt-in. Jev (TypeSafe's typed-judgment API,
  `TYPESAFE_API_KEY`) judges every window's measures against the rest of the film and ranks what to fix first, with
  the kind of fix (camera, framing, light, motion, detail), in about four seconds. Numbers only, never frames;
  without the flag only the transfer preview is written; answers checked, cached, and never replaced by a guess.
- `remaking.md`, "The night, and judging faster": the fourth round of the 3D remake (night grass 0.30 to 0.55,
  lights on 0.39 to 0.51, mean 0.614).

## Unreleased: the set laid out for the camera

- `kit/follow.js`: only the reference's measured growth moves the camera; two anchors that aim at different distances
  no longer push it forward between them (it flew past its subject).
- `remaking.md`, "The set laid out for the camera": the third round of the 3D remake (a landing hill, houses built
  as the reference builds them, the subject laid along the measured camera, what the fit can't read).

## Unreleased: the camera, measured

- `moodreel camera <reference> [--against <remake>] [--shots f] [--js camera-data.js]`: a film's camera read off its
  picture window by window (travel, push, roll, and the turn and tilt they mean at a field of view), a remake's beside
  it with what is off ("pans the other way", "pushes in where the reference pulls out", "doesn't roll"), and the
  reference's track as a film module.
- `kit/follow.js`: `follow(MOTION, anchors, end, { own })` moves a remake's camera by that track between a few anchors
  (push integrated along the view, roll from the anchors, hand-keyed spans where the fit reads the subject).
- `remaking.md`, "The camera, measured": the second round of the 3D remake (mean 0.586 to 0.607, windows moving as the
  reference's to 18 of 36): the logo on the reference's grid, a real keyboard layout, the hops counted, the camera
  driven by the reference's track and anchored where its path already goes.

## Unreleased: a 3D one-take remake

- `moodreel compare --against <last pass's --json>`: each window's score change and the mean's, so a change is kept
  only where its window rose; `--sheet <file.jpg>`: the reference beside the remake at each window's middle, worst
  first, named and scored. The report's window column widens to the longest name.
- `skills/moodreel/references/distill/remaking.md`: "One take in 3D", from remaking a 64 s voxel-world film (mean
  window score 0.53 to 0.59 in seven passes): phases instead of cuts, the camera and subject placed by the size in
  frame, keys that move their neighbours' windows, frames between keys, growth shaders and the shadow pass
  (`customDepthMaterial`), footprints of instances not yet grown, a daytime fill for walls, one schedule for a story's
  counts.

## Unreleased: the distilled packs in the repository

- `styles/README.md` is the one index of every style: the distilled packs are listed in their categories beside
  the imported lemo-opuscar styles (which stay where they are), with a Source column. Both
  `scripts/import_lemo_styles.py` and `scripts/packs.py export` write it; `packs/` folders take the library's eleven
  categories.
- `packs/`: Signal Plates (graphic and type) and ASCII Glitch Launch (information and keynote), each a complete pack
  in the layout the tools read, with a README that sorts its contents by kind (rules, evidence, the style's own
  modules, measured tokens, shared kit, fonts, demo source); `packs/README.md` lists them by the library's categories.
  Demo films and kit/vendor stay out (rebuilt from source; GitHub refuses files over 100 MB).
- `scripts/packs.py export|install`: the library's packs into `packs/<category>/<slug>/` and back, registering them,
  deleting nothing (an installed pack keeps its rendered demo.mp4).

## Unreleased: remakes measured shot by shot

- `moodreel probe <reference> --at t1,t2 [--against <remake>]`: a shot's numbers off full-size frames, the
  reference's beside a remake's (a video, or a film folder rendered as stills): mean colour, lit share and the box the
  light fills, detail, whether the grain holds still, the period, phase and strength of a cell grid, and the angle,
  length and width of a bar. `--region`, `--lit`, `--sheet` (a contact sheet, reference above remake), `--json`.
- `moodreel probe` also reads the light as 16 x 9 cells of grey (a vignette, an ellipse of light, a ground to draw
  back), the strength and phase of a 4 px scan-line rhythm, and a 3 x 3 optical-flow grid with where a turn's
  horizontal speed crosses zero.
- `moodreel probe --region` round a line of type reads its weight: the ink's box and height, the stroke width and
  their ratio.
- `moodreel compare` reads each window's grain (the least change between neighbouring frames) and says when a
  remake's grain boils where the reference's holds still: it reads as motion going another way.
- The skill: `references/distill/remaking.md`, the remake loop (cut to the frame, score, probe, fix the lowest
  window) and what it fixed on a 16 s ASCII-glitch teaser: a cylinder camera fitted to measured cards, particles
  matched on lit share, a frame of cells read for its grid and glyph ramp, a slow turn read every tenth of a second,
  a fixed grain.

## Unreleased: a film's own score, sung

- `moodreel sync` reads frame rates ffprobe prints with a trailing field (`60/1,` for a stream with side data).
- `moodreel pack` reads the demo for what films in the style need: its frame rate (`demo/film.json`), `3d` when the
  style's kit or demo draws with kit/gl.js or kit/three.js (a new film then gets three.js), `music-led` when the demo
  is cut to its own score (a new film then starts with one). It no longer copies the demo's renders (its delivered
  .mp4 and out/) into the pack: `demo.mp4` is the film.
- `moodreel film new` takes the style's frame rate unless `--fps` says otherwise, and lists the typefaces a style ships
  in `kit/fonts` (with their OFL.txt) in the film's CREDITS.
- `moodreel score`: a section can write its lead out (`"melody"`: notes by bar, beat, length and chord tone), and a
  note may carry a word: the timeline lists the words and lines as sung, `lyrics.json` holds them, and a score with a
  band writes `music-data.js` for kit/music.js itself, the beats, bars and drum hits exactly as written (analysing the
  rendered synth track read it at half tempo, a beat off).
- `moodreel sketch` no longer rewrites the project's kit: tokens and motion set by the director at gate 1 stay.
- `moodreel motion-check`: when the references stagger different groups differently, a film's stagger passes if it
  matches any of them (it used to be compared with the upper one only).
- `kit/gl.js` post: `edge: 1` shows black where a shake or whip pulls the picture in from outside the frame, instead
  of stretching its border across it.

## Unreleased: beat-sync fingerprints and tracked cameras

Both checked against the source of pdoom-video, whose plates' own post settings and cameras were recorded frame by
frame as the ground truth ([docs/research/VISION-TO-CODE.md](docs/research/VISION-TO-CODE.md) §5-6).

- `moodreel sync <video>`: what the picture does after each kind of musical event (beat, downbeat, kick, snare, hat,
  vocal, sung word, line): its cuts, motion energy, zoom rate, shake and flashes, averaged around the events with the
  peak, latency, half-life and z against chance; where cuts, surges, punches and flashes land and how far a cut leads a
  line. Written as a recipe with `kit/music.js` settings. `--against` lists what a remake misses, adds, sizes or times
  differently, with a similarity. On the source: 16 of 17 visible plate changes, shake to a frame at 0.94 of its size;
  a remake built from the source's plates scores 0.969, one drawn from stills 0.716, for the reasons it names.
- `moodreel pose <video> --track t0,t1 --at t --points ...`: the camera through a whole shot, tracking the rectangle
  read on one frame (LK with a forward-backward check, RANSAC homography, reseeding) and solving each frame;
  `--module cam.js` exports `cameraAt(t)`. On the source: pitch within 3.5 deg, yaw 4.2, roll 1.0, distance 0.8 % with
  the lens fixed.
- `moodreel pose --up wall|floor` gives the camera in the rectangle's world (position, forward, up, pitch, yaw, roll as
  three.js's `rotateZ`); `--fov shape` solves the lens from the rectangle's known aspect.
- A blind rebuild of one plate with the tracked camera: motion direction 0.15 to 0.48, structure 0.41 to 0.48; the
  score holds at 0.69 because detail (0.68x) is now what's missing.
- skills: `reading-shots.md` gains the sync and tracking steps and what they can't read.

## Unreleased: reading shots as code

Learned by setting a remake drawn from stills beside the source code of the same film
([docs/research/VISION-TO-CODE.md](docs/research/VISION-TO-CODE.md)): reading by eye ran darker (0.82 of the light),
more saturated (1.25x the accent), sparser (0.79x the line), with less glow (0.63x), slower (0.63x), and moved in
directions unrelated to the reference; it also missed which technique a shot needs.

- `moodreel dossier <video>`: each shot read as code. Motion from the flow of the picture's own lines (pan, zoom, roll,
  spin, surges, a perspective fit for a 3D camera, the frame-by-frame track and its chart), linework at 1280 wide
  (share of line, width, hatching, orientations), finish (glow, colour fringe, grain), colour, and technique hints
  calibrated against the source (hatching 4 of 9 plates found, no false alarms; 3D camera 6 of 10, 1 false of 12).
- `moodreel pose <frame>`: the 3D camera from a rectangle in the picture (pitch, yaw, roll, distance, field of view,
  the rectangle's aspect), with `--grid` to read corners off a frame.
- `moodreel measure` reads every video reference's shots and adds "Shots read as code" to MEASURE.md: which techniques
  the style needs and its camera vocabulary.
- skills: `references/distill/reading-shots.md`, what each hint means, what a picture usually is in code, and the
  rebuild loop; SKILL.md and the distill guides point to it.
- A blind rebuild of one plate from the video alone, with these tools, rose from the stills-built 0.61 to 0.69
  (`moodreel compare`); the source scores 0.94.

## Unreleased: remakes that match

A remake whose stills matched still moved wrong: shot by shot, its optical flow agreed with the reference's at a median
of 0.1 and ran at 0.6 of its speed. See [docs/GPU.md](docs/GPU.md).

- `moodreel compare <reference> <remake>`: window by window (the reference's own shots by default), structure (SSIM),
  detail, tone, motion direction (optical flow, cell by cell) and speed, the worst windows first with what is wrong.
- `kit/gl.js`: a GPU layer for pages. Full-screen shader passes into HDR targets (several outputs for a G-buffer),
  Canvas layers as textures, tens of thousands of anti-aliased hairlines a frame (2D or 3D), a GLSL library (noise,
  signed distances, smooth union, engraving hatch, a heat ramp) and a film post (bloom pyramid, halation, chromatic
  fringe, tone shoulder, vignette). Adapted from pdoom-video's engine (MIT).
- `kit/outline.js`: glyph outlines from TrueType files (simple and composite glyphs), for type broken into strokes or
  particles. `kit/anim.js`: pulse, spring, keyframes, frame-stable seeds, paths walked by length.
- `stage({ faces, prepare })`: font files registered by family name; a step after fonts and images load and before the
  first frame, for what measures text.
- `moodreel music` keeps an aligner's syllable timings, and `kit/music.js` `progress` follows them.
- `film deliver` brings three.js for a film that uses `kit/gl.js`.

## Unreleased: films that follow their song

Learned from the source of [mexicat/pdoom-video](https://github.com/mexicat/pdoom-video) (MIT) while remaking it shot by
shot: a music video lands on its song because every motion is computed from the song's data, not timed by hand. See
[docs/MUSIC-SYNC.md](docs/MUSIC-SYNC.md).

- `moodreel music`: a song as data (beat grid fitted over the whole song, bars from the backbeat, kick, snare and hat
  hits, 100 fps envelopes, word-level lyrics from any aligner) or another tool's analysis imported, written as
  `music-data.js`. On pdoom-video's song against its stem-separated data: 132.002 BPM (132.007), every beat within 15 ms,
  every bar right, kicks found with recall 0.88 and precision 0.97, snares 0.89 and 0.83.
- `kit/music.js`: drum hits, envelopes, a camera clock that surges on the beat, words looked up by text at the time they
  are sung, the word slam, the letter pop.
- Motion blur: `render.mjs --samples N --shutter s` and `stage({ finish })`: each frame the average of sub-frames over
  the shutter, finish run once on the result.
- `kit/texture.js`: `bloom`, `halation` and `aberrate` for a finish.
- `NOTICE`: the MIT notice for what is adapted from pdoom-video.
- `render.mjs --from s --to s`: render part of a film.
- `sfx.json`: a film's sound effects at seconds (a film cut to a song has its events in seconds, not bars), panned,
  rendered by `moodreel/score/sfx.py` and mixed under the music by `film deliver` before the loudness pass. Thirteen
  new foley sounds: slam, key, glitch, tear, stamp, crackle, boom, tick, rewind, swish, click, zap, thud.
- `film.json` `"motion_blur": {"samples", "shutter"}`: `film deliver` renders with motion blur.
- Fixed: a mix a little longer than the film came out of the loudness pass 0.1 s short (loudnorm's timestamps ran
  ahead of its samples), so the film lost its last six frames at 60 fps and the fade-out began early.

## v0.1.0: the MVP (2026-10-24, pre-alpha)

The whole design in [docs/MVP-DESIGN.md](docs/MVP-DESIGN.md) is built: milestones W1-W6 and every V1 item.

**Distil a style** from style-consistent pictures and code-made videos: `intake` (normalised references, a unity
check), `measure` (palette and colour roles, surface, layout, type, motion grammar, rhythm, counters, loops and
particles, a beat grid, pixel art, brush marks, CSD style embeddings), `frame-check` and `motion-check`, `kit` and
`scaffold`, `sketch`, and `pack` into the style library.

**Make films** in any of the 59 library styles or your own: `film new | check | deliver`, a kit of drawing primitives
(stage, eases, texture, type, pixel art, brushwork, three.js 3D, footage), a score written first (`score.json`,
synthesised or sampled instruments, cues the picture lands on), narration (`voice`), real material with its source and
licence (`media`), variants, and export to HyperFrames or Remotion. A puppeteer renderer that makes every frame
bit-identical, run to run.

**Measured against the plan's acceptance lines (§8):**

| Layer | Target | Result |
|---|---|---|
| Motion measurement | recall ≥ 0.9, t50 within a frame ≥ 0.85, direction ≥ 0.8, eases named wrongly ≤ 5 % | clean 0.96 / 0.853 / 0.958 / 0 %; stress 0.919 / 0.868 / 0.824 / 0 % |
| Round trip (5 library styles) | the measured sections hold | 23 of 25 |
| Blind distillation (5 styles) | ≥ 8 of 11 sections judged the same | 5 of 5 pass (10, 8, 8, 8, 10) |
| Style frames | ≥ 70 % through gate 2 in two rounds, frame-check agreeing with people | not run: needs human judgement |
| End to end | 3 topics in one style, ≥ 2 judged the same style blind | not run |

**Still to do, with the user:** calibrate the measurements on real reference sets (the plan's W2 and W3 asked for one
or two), run the two human-judged evaluations above, and settle the plan's open questions (§14: default aspect,
reference sources, the first real reference set, which agents to support). The repository is private.

**Examples:** eleven films, in [examples/](examples/README.md): five for the round trip, five for the later
capabilities (score, pixel art, brushwork, 3D, footage) and one played by the sampled band.

**Optional downloads**, each asked for by name: `moodreel csd setup` (the CSD weights, CC BY 4.0, 2.4 GB fetched, 0.6 GB
kept) and `moodreel samples fetch` (272 MB of CC0 instrument recordings). Remotion is not a dependency; an exported
project installs it, under Remotion's own licence.
