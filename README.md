# Moodreel

**Moodboard in, reel out.** Give Moodreel a few design images and a clip or two in one visual style. It measures
what makes that style recognisable — palette, materials, type, layout and, above all, *how things move* — and
writes it down as a **style pack**: rules a director can follow plus a code kit a film can import. An AI agent
then directs new films in that style, drawn entirely in code and rendered frame by frame.

[中文说明](README.zh-CN.md)

> **Status: pre-alpha.** Motion measurement (`moodreel motion`) passes its acceptance bench on code-rendered test
> films. The style pack, the director workflow and the rest of the CLI are designed and being built.

## Why measure motion?

Vision models can copy how a frame looks but not how it moves. On the Animation2Code benchmark (2026), the best
models reach 0.82–0.84 appearance similarity while temporal similarity stays at or below 0.31 for all of them.
So Moodreel measures timing, easing, overshoot, stagger and rhythm with deterministic code, and leaves the
model to understand and use those numbers.

`moodreel motion` finds every element a motion run changes, tracks its position, scale and opacity in one template
match, fits each change against the GSAP ease families, and only names an ease when the evidence is clear. It also
finds cuts, dissolves and fades through a colour, camera pushes and pans (and measures the elements in the world,
not on the moving screen), drawings held on twos, and staggers.

Scored on 10 code-rendered test films with known motion ([bench/motion](bench/motion/README.md)), each also as a
degraded copy (3/4 size, 25 fps, moving grain, crf 30):

| | found | t50 within 1 frame | ease direction right | eases named / named wrong | transitions |
|---|---|---|---|---|---|
| clean | 94% | 86% | 97% | 29 / 0 | 13/14 |
| degraded | 92% | 88% | 86% | 9 / 0 | 13/14 |

Rotation, one-axis stretch (a bar growing), line draw-on and per-letter text are not measured yet.
Details: [docs/research/motion-extraction.md](docs/research/motion-extraction.md) (Chinese).

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

Measure the motion grammar of a single video:

```bash
uv run moodreel motion path/to/video.mp4 --out out/my-video
```

Build, render and score the test films:

```bash
uv run moodreel bench make && uv run moodreel bench render && uv run moodreel bench motion
```

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
| `moodreel/` | The Python package: `intake.py`, `measure/` (palette, surface, layout, type, rhythm), `motion/` (shots, camera, tracking, ease fitting, grammar), `check/` (frame-check), `bench/` (test films and scorer), `cli.py` |
| `styles/` | The style library |
| `bench/motion/` | The motion test films (pages and truth) and the latest report |
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
