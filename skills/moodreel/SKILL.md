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
4. **Gate 1**: show the decisions in one message (each: choice, alternatives, evidence, cost) and wait for an OK.
5. **Look**: `moodreel kit <project>`, `moodreel scaffold <project>`; rewrite `look/main.js` into the style's own
   picture with the kit (`references/primitives.md`); render a still; `moodreel frame-check` it
   (`references/distill/checks.md`). Fix once, twice at most; then **gate 2**: show the frame beside the references.
   Save the approved frame as `<project>/styleframe.jpg`.
6. **Demo film**: 15–30 s in `<project>/demo/` (index.html, main.js, kit/, build.sh, CREDITS), every rule of STYLE.md
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

## Where to look

| Question | Read |
|---|---|
| Bringing references in, unity, the one round of questions | `references/distill/intake.md` |
| What each measurement means, what to trust, which evidence image answers what | `references/distill/reading-evidence.md` |
| STYLE.md section by section: sources and wording | `references/distill/writing-style-md.md` |
| The ledger's format and the observed / derived / inferred rule | `references/distill/ledger.md` |
| Reading frame-check and motion-check, and what to change for each failure | `references/distill/checks.md` |
| The kit's modules and recipes for common materials and moves | `references/primitives.md` |
| Brief, treatment, shots, beats, not repeating the demo | `references/produce/brief-and-treatment.md` |
| The page contract, determinism, type, texts for the reading check | `references/produce/drawing.md` |
| Checks before delivery, music and loudness, CREDITS, what to tell the user | `references/produce/delivery.md` |
| Commands and flags | `moodreel --help`, `moodreel <command> --help` |
