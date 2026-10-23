# Moodreel

**Moodboard in, reel out.** Give Moodreel a few design images and a clip or two in one visual style. It measures
what makes that style recognisable — palette, materials, type, layout and, above all, *how things move* — and
writes it down as a **style pack**: rules a director can follow plus a code kit a film can import. An AI agent
then directs new films in that style, drawn entirely in code and rendered frame by frame.

[中文说明](README.zh-CN.md)

> **Status: pre-alpha research.** The motion-measurement prototype works on synthetic test films with known
> ground truth. The style pack format, the director workflow and the CLI are designed, not built yet.

## Why measure motion?

Vision models can copy how a frame looks but not how it moves. On the Animation2Code benchmark (2026), the best
models reach 0.82–0.84 appearance similarity while temporal similarity stays at or below 0.31 for all of them.
So Moodreel measures timing, easing, overshoot, stagger and rhythm with deterministic code, and leaves the
model to understand and use those numbers.

The prototype finds every element a motion run changes, tracks its position, scale and opacity in one template
match, fits each change against the GSAP ease families, and only names an ease when the evidence is clear.

| Test film (18 animated properties, a cut, a dissolve) | found / false | t50 within 1 frame | ease direction right | eases named / named wrong |
|---|---|---|---|---|
| clean · 1280×720 · 30 fps | 18/18 · 0 | 94% | 94% | 10 / 0 |
| stress · 960×540 · 25 fps · grain · crf 30 | 18/18 · 0 | 89% | 78% | 4 / 0 |

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

## Try the prototype

Needs [uv](https://docs.astral.sh/uv/), ffmpeg and Node 20+.

```bash
uv sync && npm install
```

```bash
uv run research/motion-spike/fixtures/make_fixture.py research/motion-spike/fixtures/mg-basic
```

```bash
node render/render.mjs video research/motion-spike/fixtures/mg-basic --fps 30 --size 1280x720 --out research/motion-spike/fixtures/mg-basic/clean.mp4
```

```bash
uv run research/motion-spike/extract.py research/motion-spike/fixtures/mg-basic/clean.mp4 --out research/motion-spike/out/clean
```

```bash
uv run research/motion-spike/evaluate.py research/motion-spike/fixtures/mg-basic/truth.json research/motion-spike/out/clean/motion.json
```

## Repository

| Path | What it is |
|---|---|
| `render/render.mjs` | Renders any page that exposes `window.DUR`, `window.render(t)` and `window.READY` to stills or video (headless Chrome + ffmpeg) |
| `research/motion-spike/` | Motion measurement prototype (`motionx`), ground-truth fixtures and the scorer |
| `docs/` | Design and research notes |

## Acknowledgements

Moodreel stands on ideas from these projects; it uses none of their code.

- [REM](https://github.com/sidart10/rem) — fit eases by BIC and claim only clear winners; check a rebuild with the same measurement.
- [motiscope](https://github.com/KumarSashank/motiscope) — localized motion energy, percentile thresholds, numbers for *when* and frames for *what*.
- [MoVer](https://arxiv.org/abs/2502.13372) — motion properties as verifiable predicates fed back to the generator.
- [lemo-opuscar](https://github.com/lemomo-ai/lemo-opuscar) — a style written as invariants (essence, materials, colour, type, motion, camera, sound, native moves, pitfalls) kept apart from any one film.
- [HyperFrames](https://github.com/heygen-com/hyperframes) — video as a deterministic function of time, rendered in a browser.

## License

[MIT](LICENSE)
