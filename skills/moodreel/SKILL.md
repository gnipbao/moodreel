---
name: moodreel
description: Distill a visual and motion style from a few reference images and videos into a style pack (STYLE.md, a measured code kit, a demo film), and make new films in any style of the library, drawn entirely in code and rendered frame by frame. Use when the user gives design images, screenshots or code-made videos and wants "this style" captured, reproduced, reverse-engineered or reused (风格蒸馏, 反推风格, 复刻这种风格, 做成风格包); when they ask for a video, promo, explainer or title sequence in a named style or one of their own (用某风格做一个片子); or when they ask which styles exist. Not for editing footage or generating video with diffusion models.
---

# Moodreel

You are the director. Moodreel's code measures and checks; you read the evidence, decide, write the rules and draw the
pictures. Two jobs, each with its own flow:

- **Distill**: references in, a style pack out (`references/distill/`).
- **Produce**: a topic and a style in, a finished film out (`references/produce/`).

Talk to the user in their language. Write STYLE.md, DECISIONS.md and LEDGER.md in English (they are prompts for any
director, any language), with the style's name in both languages.

## Ground rules

- **Measure before you describe.** Colours, surfaces, sizes and above all timing come from `moodreel measure`, not
  from looking. A vision model can name what it sees; it cannot time it (Animation2Code: appearance ~0.84, timing
  ≤ 0.31). Read MEASURE.md before any frame.
- **Every number has a source.** Each value you write into STYLE.md or the kit is in LEDGER.md with its basis:
  *observed* (read off the pictures), *derived* (computed from readings), *inferred* (your judgement). `unknown` is
  never written as a rule. `moodreel pack` refuses values it cannot trace (`--strict`).
- **Names, not guesses.** An ease is named (power3.out) only where the measurement claims it; otherwise write the class
  (ease-out) and the cubic-bezier. Equivalent families the data can't separate are named together.
- **Grammar, not content.** Take rhythm, palette logic, motion, framing rules. Never copy a reference's characters,
  layouts, logos, footage, music or typefaces, and never put its names in a film.
- **Code draws everything.** No image or video generation. Fonts, images, samples and data are the user's or openly
  licensed (OFL, CC0, CC BY), each listed in CREDITS.
- **Deterministic pages.** A film is `window.render(t)`: the whole frame from `t` alone. No `Date.now()`, no unseeded
  `Math.random()`, no state carried between frames (`references/produce/drawing.md`).
- **One round of questions.** Ask what only the user can answer, once, then decide the rest and say what you decided.
  The three gates in distill are the only other stops.

## Distill

```
intake ─► measure ─► read ─► write STYLE.md · LEDGER.md · DECISIONS.md ─◆ gate 1
       ─► kit + scaffold ─► style frame ─► frame-check ─◆ gate 2
       ─► demo film (15–30 s) ─► motion-check ─◆ gate 3 ─► pack
```

1. **Intake** (`references/distill/intake.md`): `moodreel intake <project> <refs…> --source own|web`. If the references
   split into palettes, ask which group is the style, or whether to mix them. Ask what films the style is for.
2. **Measure**: `moodreel measure <project>`. Read `MEASURE.md`, then the evidence it points to
   (`references/distill/reading-evidence.md`).
3. **Write** (`references/distill/writing-style-md.md`): `ANALYSIS.md` (3–5 traits that make the style recognisable,
   each tied to evidence; what it is not), then `STYLE.md` (11 sections), `LEDGER.md` (`references/distill/ledger.md`)
   and `DECISIONS.md` (choices the measurement can't make: typefaces, how materials are built, sound direction).
   What the references don't show is unseen, not forbidden: write "never" only where the evidence or the medium
   says so, and leave the rest open in §11 (the guide's "Few references" section).
4. **Gate 1**: show the decisions in one message (each: choice, alternatives, evidence, cost) and wait for an OK.
5. **Look**: `moodreel kit <project>`, `moodreel scaffold <project>`; rewrite `look/main.js` into the style's own
   picture with the kit (`references/primitives.md`); render a still; `moodreel frame-check` it
   (`references/distill/checks.md`). Fix once, twice at most; then **gate 2**: show the frame beside the references.
   Save the approved frame as `<project>/styleframe.jpg`.
6. **Demo film**: first, `moodreel sketch <project>` replays the kit's motion with neutral shapes; render it and
   `motion-check` it: if the sketch fails, fix the kit (or mark the curve `inferred`) before drawing the demo.
   Then 15–30 s in `<project>/demo/` (index.html, main.js, kit/, build.sh, CREDITS), every rule of STYLE.md
   on screen at least once, the signature move once. Render to `<project>/demo.mp4`; `moodreel motion-check` it; fix
   what fails (two rounds at most). **Gate 3**: show the film and the claims.
7. **Pack**: `moodreel pack <project> --slug … --name … --name-zh … --build`. Tell the user the style's name and how
   to use it ("make a film in my <name> style about …").

## Produce

```
find the style ─► brief (one round) ─► TREATMENT.md ─► film new ─► draw ─► stills ─► film check ─► deliver
```

1. `moodreel styles [query]` lists the library: the user's styles first, then the built-in ones. A built-in style
   marked `later` needs capabilities Moodreel doesn't have yet (painterly, 3d, pixel, music-led, real-material): say
   which, what you can still do, and let the user choose.
2. **Brief and treatment** (`references/produce/brief-and-treatment.md`): one round of questions, then
   TREATMENT.md with three candidate structures and your choice, shots and beats, before any drawing.
3. `moodreel film new <name> --style <style> --duration <s>`; write `main.js` with the style's kit
   (`references/produce/drawing.md`). Review with stills (`moodreel render still <film> t1 t2 …`) and a contact
   sheet before rendering the whole film.
4. `moodreel film check <film>` until it passes, then `moodreel film deliver <film> [--music track]`
   (`references/produce/delivery.md`).

**A film that follows a song** (a music or lyric video, a cut on the beat, a remake of one): before drawing, turn the
song into data with `moodreel music <song> [--lyrics words.json] --out <film>/music-data.js` and drive the picture from
it through `kit/music.js`: words appear when they are sung (`sung`, `letters`), never at times read off a contact
sheet; cuts on the beat before a line's first word; hits on the kicks and snares; cameras on `ct`. For motion blur put
`"motion_blur": {"samples": 8, "shutter": 0.2}` in film.json (deliver renders with it). Sound effects go in `sfx.json`
at the seconds the picture's events happen, read from the same data (a slam on each sung word, a key per letter typed);
deliver mixes them under the song. Measure the result against the song (and the reference) for motion and sync, not
just stills. The rules and their numbers: `docs/MUSIC-SYNC.md`.

**A remake** (a film matched to a reference shot by shot): read each shot before drawing it with `moodreel dossier`
(motion, linework, finish, colour, and which technique it needs), read the reference's beat-sync fingerprint with
`moodreel sync` (what the picture does on each kind of musical event, to the millisecond), and, for a 3D shot, track the
camera through it with `moodreel pose <video> --track`, and read every window's camera move (pan, push, roll) with
`moodreel camera <reference> --against <remake>`, which writes the reference's track for `kit/follow.js` to move the
remake's camera by; run each pass in one command with `moodreel pass <reference> <film> --shots scenes.json --name pN`
(render, parallel scoring, camera, contact sheet; `--jev --allow-text-upload` adds the opt-in Jev ranking of what to
fix first, `--vision --spec look.json --allow-image-upload` has Jev look at frames of both films, `moodreel look`);
for pixel-level placement box the reference's subjects with `moodreel track --js track-data.js` and solve the remake's
camera and subjects onto them with `kit/lock.js`; measure every pass with `moodreel compare <reference> <remake>`
and `moodreel sync <remake> --against <reference fingerprint>`, not only by stills. Reading by eye runs darker,
more saturated, sparser and slower than the reference, and guesses the camera: `references/distill/reading-shots.md`.
Before redrawing a shot, read its numbers with `moodreel probe <reference> --at t1,t2 --against <remake>` (lit share
and box, colour, detail, still grain, cell grid, a bar's angle, stroke weight, light map, scan lines, a turn's centre)
and move yours toward them; look for pictures behind glyph screens where a transition seems empty. The loop and what
it fixed: `references/distill/remaking.md`.
What a 2D canvas can't draw (ray-marched bodies, lensing, dense line fields, engraving that follows a surface) goes
through `kit/gl.js`. When the reference's source is public under a permissive licence, its own scenes can run here
through a compatibility layer: `docs/GPU.md`.

## Where to look

| Question | Read |
|---|---|
| Bringing references in, unity, the one round of questions | `references/distill/intake.md` |
| What each measurement means, what to trust, which evidence image answers what | `references/distill/reading-evidence.md` |
| STYLE.md section by section: sources and wording | `references/distill/writing-style-md.md` |
| The ledger's format and the observed / derived / inferred rule | `references/distill/ledger.md` |
| Reading frame-check and motion-check, and what to change for each failure | `references/distill/checks.md` |
| Remaking a film shot by shot: cut to the frame, score, probe, fix the lowest window | `references/distill/remaking.md` |
| The kit's modules and recipes for common materials and moves | `references/primitives.md` |
| Brief, treatment, shots, beats, not repeating the demo | `references/produce/brief-and-treatment.md` |
| The page contract, determinism, type, texts for the reading check | `references/produce/drawing.md` |
| Checks before delivery, music and loudness, CREDITS, what to tell the user | `references/produce/delivery.md` |
| Commands and flags | `moodreel --help`, `moodreel <command> --help` |
