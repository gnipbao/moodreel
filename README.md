# Moodreel

**Moodboard in, reel out.** Give Moodreel a few design images and a clip or two in one visual style. It measures
what makes that style recognisable — palette, materials, type, layout and, above all, *how things move* — and
writes it down as a **style pack**: rules a director can follow plus a code kit a film can import. An AI agent
then directs new films in that style, drawn entirely in code and rendered frame by frame.

[中文说明](README.zh-CN.md)

> **Status: pre-alpha.** The whole path works end to end: references in, measurements, a kit, a packed style, a
> film made in it, checked and delivered. Motion measurement passes its acceptance bench, and two example films
> survive the round trip (below). A camera on a plain ground, rotation and line draw-on are next.

## Why measure motion?

Vision models can copy how a frame looks but not how it moves. On the Animation2Code benchmark (2026), the best
models reach 0.82–0.84 appearance similarity while temporal similarity stays at or below 0.31 for all of them.
So Moodreel measures timing, easing, overshoot, stagger and rhythm with deterministic code, and leaves the
model to understand and use those numbers.

`moodreel motion` finds every element a motion run changes, tracks its position, scale and opacity in one template
match, fits each change against the GSAP ease families, and only names an ease when the evidence is clear. Where the
template can't follow, it measures how much of the element shows: a bar growing from its base, a word collapsing
to a line, type rising out of a slot, a shape wiped on. When the curve has no GSAP name, one cubic-bezier is fitted
through all the tweens whose class was read, so a style's own curve comes back as itself. It also
finds cuts, dissolves and fades through a colour, camera pushes and pans (and measures the elements in the world,
not on the moving screen), drawings held on twos, and staggers.

Scored on 10 code-rendered test films with known motion ([bench/motion](bench/motion/README.md)), each also as a
degraded copy (3/4 size, 25 fps, moving grain, crf 30):

| | found | t50 within 1 frame | ease direction right | eases named / named wrong | transitions |
|---|---|---|---|---|---|
| clean | 94% | 86% | 97% | 29 / 0 | 13/14 |
| degraded | 92% | 88% | 86% | 9 / 0 | 13/14 |

Of the 11 moves the bench marks as beyond those readers, 6 are now found on the clean films (bars growing, an
underline drawn out); rotation, line draw-on and per-letter text are not measured yet.
Details: [docs/research/motion-extraction.md](docs/research/motion-extraction.md) (Chinese).

### The round trip

Two example films ([examples/](examples/README.md)), each made in code from a library style, distilled back as if
they were a user's references and compared with the values in their own code
([bench/roundtrip](bench/roundtrip/REPORT.md)):

| film (style) | palette roles | surface | title | cuts, drawing rate | the kit's curves | moves found | eases named / named wrong |
|---|---|---|---|---|---|---|---|
| swiss-programme (Swiss motion) | ΔE 0.2 | no grain, vignette or screen | size −14 %, weight 700 | ✓ | entrances `bezier(0.73,−0.03,0.18,1.04)` (film: `0.7,0,0.2,1`) | 22 / 40 | 0 / 0 |
| first-light (risograph) | ΔE ≤ 4.4 | grain; halftone 7.0 px at 14.8° (film: 7 px at 15°) | size +25 %, weight | ✓ | left to the director | 4 / 11 | 3 / 0 |

Colour, surface, type and rhythm come back, and so does the Swiss film's house curve, which has no GSAP name. The
risograph sun is read rising behind its horizon with the film's exact `power2.out`. What is still missed is said
plainly in the report: type rising in a slot of its own size reads as a stretch, a camera on a plain ground as
elements moving together, and reflections nested in a sea that is being wiped on aren't seen apart from it.

## How it will work

```
references ─► measure ─► interpret ─► style frame ─► demo film ─► style pack ─► new films
             (code)      (director)    (check)        (motion check)              (director + renderer)
```

1. **Measure** — palette, texture, layout and motion grammar, each number tagged observed, derived or inferred.
2. **Interpret** — the director names the 3–5 traits that make the style, what it is not, and writes `STYLE.md`.
3. **Prove the look** — a style frame drawn with the kit, scored against the references.
4. **Demo film** — rendered, then measured again with the same code and checked rule by rule against the references.
5. **Produce** — any topic, same style: the director writes a treatment and draws the film with the kit.

See [docs/MVP-DESIGN.md](docs/MVP-DESIGN.md) (Chinese) for the full design.

## Try it

Needs [uv](https://docs.astral.sh/uv/), ffmpeg and Node 20+.

```bash
uv sync && npm install
```

Bring a few references into a project, check they share one style, and measure them (palette and colour roles,
surface, layout, type sizes and weights, motion grammar, rhythm). `MEASURE.md` is the summary a director reads first:

```bash
uv run moodreel intake out/projects/my-style refs/*.png refs/teaser.mp4 --source own
```

```bash
uv run moodreel measure out/projects/my-style
```

Score a style frame against the references (palette coverage, off-palette area, lightness, surface):

```bash
uv run moodreel frame-check out/projects/my-style frame.png
```

Write the style's kit (the shared primitives plus `tokens.js` and `motion.js` from the measurements), draw a first
style frame from it, and check a rendered film's motion against the references, claim by claim:

```bash
uv run moodreel kit out/projects/my-style && uv run moodreel scaffold out/projects/my-style
```

```bash
uv run moodreel motion-check out/projects/my-style film.mp4
```

Pack a finished style into your library (`~/.moodreel/styles`), list styles, and make a film in one:

```bash
uv run moodreel pack out/projects/my-style --slug my-style --name "My Style"
```

```bash
uv run moodreel styles
```

```bash
uv run moodreel film new launch --style swiss-motion && uv run moodreel film check films/launch
```

```bash
uv run moodreel film deliver films/launch --music track.wav
```

`film check` holds every line of text on screen long enough to read, finds black frames, and, for a distilled
style, scores frames and motion against it; `film deliver` renders, normalises the music to −14 LUFS and muxes.

Measure the motion grammar of a single video:

```bash
uv run moodreel motion path/to/video.mp4 --out out/my-video
```

Build, render and score the test films, and distil the example films back:

```bash
uv run moodreel bench make && uv run moodreel bench render && uv run moodreel bench motion
```

```bash
uv run moodreel bench roundtrip
```

## Use it with an agent

Moodreel is meant to be driven by an agent acting as director (Claude Code, Codex or any agent that reads
`SKILL.md`). Install the command line in editable mode, so it keeps finding the renderer, kit and styles in this
checkout, and link the skill:

```bash
uv tool install --editable .
```

```bash
ln -s "$PWD/skills/moodreel" ~/.claude/skills/moodreel
```

Then ask in plain words: "distill the style of these references into a style pack", "make a 20-second launch film
about X in my <style> style", "which styles are there?". [skills/moodreel/SKILL.md](skills/moodreel/SKILL.md) holds
the director's flows, gates and rules.

## Style library

[`styles/`](styles/README.md) holds 59 styles imported from [lemo-opuscar](https://github.com/lemomo-ai/lemo-opuscar):
each style's `STYLE.md` (the invariants a director follows), `DEMO.md` (how its demo film was made) and a
`style.json`. 23 of them are flat 2D styles the MVP draws (Swiss motion graphics, risograph, ukiyo-e, blueprint,
spy titles…); 36 need capabilities that come later: painterly brush engines, 3D, pixel art, a score that drives
the picture, or real footage and data. Only the documents are imported; Moodreel re-implements the techniques.

## Repository

| Path | What it is |
|---|---|
| `render/render.mjs` | Renders any page that exposes `window.DUR`, `window.render(t)` and `window.READY` to stills or video (headless Chrome + ffmpeg) |
| `moodreel/` | The Python package: `intake.py`, `measure/` (palette, surface, layout, type, rhythm), `motion/` (shots, camera, tracking, ease fitting, grammar), `check/` (frame-check, motion-check), `pack/` (kit, scaffold, pack), `film/`, `library.py`, `bench/` (test films, scorer, round trip), `cli.py` |
| `skills/moodreel/` | The director's skill: distill and produce flows, how to read the evidence, write STYLE.md, the ledger, the checks |
| `kit/` | The primitives a film's code imports: page contract, eases, tweens, seeded noise, surfaces, type ([kit/README.md](kit/README.md)) |
| `styles/` | The style library |
| `examples/` | Example films made in library styles, with the values their code uses ([examples/README.md](examples/README.md)) |
| `bench/motion/` | The motion test films (pages and truth) and the latest report |
| `bench/roundtrip/` | The round trip's latest report ([bench/roundtrip/README.md](bench/roundtrip/README.md)) |
| `tests/` | Unit tests on synthetic data (`uv run --group dev pytest`) |
| `scripts/import_lemo_styles.py` | Re-imports the style documents from a lemo-opuscar checkout |
| `docs/` | Design and research notes |

## Acknowledgements

Moodreel stands on ideas from these projects. Apart from the lemo-opuscar style documents in `styles/`, it uses
none of their code.

- [REM](https://github.com/sidart10/rem) — fit eases by BIC and claim only clear winners; check a rebuild with the same measurement.
- [motiscope](https://github.com/KumarSashank/motiscope) — localized motion energy, percentile thresholds, numbers for *when* and frames for *what*.
- [MoVer](https://arxiv.org/abs/2502.13372) — motion properties as verifiable predicates fed back to the generator.
- [lemo-opuscar](https://github.com/lemomo-ai/lemo-opuscar) — a style written as invariants (essence, materials, colour, type, motion, camera, sound, native moves, pitfalls) kept apart from any one film; its 59 style documents are the start of our library.
- [HyperFrames](https://github.com/heygen-com/hyperframes) — video as a deterministic function of time, rendered in a browser.

## License

Moodreel is [MIT](LICENSE). The style documents in `styles/` that come from lemo-opuscar are MIT, Copyright (c)
2026 LemoLab ([`styles/LICENSE-lemo-opuscar`](styles/LICENSE-lemo-opuscar)); each one names its source commit.
