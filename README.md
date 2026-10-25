# Moodreel

**Moodboard in, reel out.** Give Moodreel a few design images and a clip or two in one visual style. It measures
what makes that style recognisable — palette, materials, type, layout and, above all, *how things move* — and
writes it down as a **style pack**: rules a director can follow plus a code kit a film can import. An AI agent
then directs new films in that style, drawn entirely in code and rendered frame by frame.

[中文说明](README.zh-CN.md)

> **Status: v0.1.0, the MVP (pre-alpha).** The whole path works end to end: references in, measurements, a kit, a
> packed style, a film made in it, checked and delivered. Motion measurement passes its acceptance bench, and five
> example films survive the round trip and a blind distillation (below). Not yet done: calibration on real
> references and the human-judged evaluations; see [CHANGELOG.md](CHANGELOG.md).

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

Scored on 12 code-rendered test films with known motion ([bench/motion](bench/motion/README.md)), each also as a
degraded copy (3/4 size, 25 fps, moving grain, crf 30):

| | found | t50 within 1 frame | ease direction right | eases named / named wrong | transitions |
|---|---|---|---|---|---|
| clean | 96% | 85% | 96% | 30 / 0 | 13/14 |
| degraded | 92% | 87% | 82% | 10 / 0 | 13/14 |

Of the 15 moves the bench marks as beyond those readers, 13 are now found on the clean films: bars growing, an
underline and an axis drawn on, a card turning as it grows (its `power3.out` named exactly), a line of type
arriving letter by letter (11 letters, 0.04 s apart, each `power3.out`), and numbers counting (0 to 4,200 in
`power3.out`, $0.0M to $12.5M in `sine.inOut`, timed to the frame; read by OCR when tesseract is installed).
Ambient motion is read over whole shots: loops (a pulse, a bob, a spin, a breathing fade, each with its period and
swing) and particle fields (count, size, speed, direction), all five right on both versions.
Details: [docs/research/motion-extraction.md](docs/research/motion-extraction.md) (Chinese).

### The round trip

Five example films ([examples/](examples/README.md)), each made in code from a library style, distilled back as if
they were a user's references and compared with the values in their own code
([bench/roundtrip](bench/roundtrip/REPORT.md)). Then the kit's motion is replayed with neutral shapes
(`moodreel sketch`) and checked against the references, claim by claim:

| film (style) | static values | moves found | eases named / wrong | sketch motion claims | sections held |
|---|---|---|---|---|---|
| swiss-programme (Swiss motion) | 12/13, nothing fails | 24 / 40 | 0 / 0 | 10 / 10 | 5 / 5 |
| first-light (risograph) | 11/14, nothing fails | 2 / 11 | 1 / 0 | 5 / 6 | 5 / 5 |
| shipped (dark keynote) | 10/13, nothing fails | 6 / 11 | 0 / 0 | 5 / 5 | 5 / 5 |
| boot (ASCII CRT) | 10/14, the clear-screen cut missed | 3 / 11 | 1 / 0 | 5 / 6 | 4 / 5 |
| morning (pictogram motion) | 9/13, the black capitals read as bold | 12 / 24 | 0 / 0 | 4 / 4 | 4 / 5 |

Values that aren't "nothing fails" are left to the director (a curve the kit didn't read), never named wrong.
Every render of a film is now the same bit for bit, so these numbers repeat from run to run; first-light's rising
sun and swimmer start hidden (behind the horizon, off the edge), and whether their extrapolated start lands within
a quarter second of the truth turns on a grey level, so they are counted as missed.
Colours, surfaces, type and rhythm come back; so does the Swiss film's house curve, which has no GSAP name
(`bezier(0.73,−0.03,0.18,1.04)` against `0.7,0,0.2,1`), and its page turn on a plain ground, read as a camera pan.
"Sections held" counts the five STYLE.md sections the measurements speak for (materials, colour, type, motion,
camera); the other six are the director's judgement, tested blind: `moodreel bench blind` packs each film's
references and measurements for a director who hasn't read the style, and scores the judges' verdicts
([BLIND.md](bench/roundtrip/BLIND.md)). On the first blind run one style of five reached 8 of 11 sections judged the
same: the director turned what one film didn't do into "never". After the skill learned that unseen is not forbidden,
and Moodreel learned to read a beat grid from silent motion, a second blind run (new director, new judge) passes all
five: 10, 10, 8, 8 and 8 of 11.

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

See [docs/MVP-DESIGN.md](docs/MVP-DESIGN.md) (Chinese) for the full design. The manual test plan for v0.1.0 is [docs/MANUAL-TEST.md](docs/MANUAL-TEST.md) (Chinese).

## Try it

Needs [uv](https://docs.astral.sh/uv/), ffmpeg and Node 20+ (`npm install` brings Chrome and three.js); [tesseract](https://github.com/tesseract-ocr/tesseract)
is optional and reads numbers that count (`brew install tesseract`, `apt install tesseract-ocr`).

```bash
uv sync && npm install
```

Two downloads are optional and asked for by name, once: style embeddings for `frame-check` (the CSD model's weights,
CC BY 4.0, 2.4 GB fetched and kept as 0.6 GB) and the sampled instruments for scores (272 MB of CC0 recordings from
Versilian Studios Chamber Orchestra 2):

```bash
uv run moodreel csd setup
```

```bash
uv run moodreel samples fetch
```

Bring a few references into a project, check they share one style, and measure them (palette and colour roles,
surface, layout, type sizes and weights, motion grammar, rhythm). `MEASURE.md` is the summary a director reads first:

```bash
uv run moodreel intake out/projects/my-style refs/*.png refs/teaser.mp4 --source own
```

```bash
uv run moodreel measure out/projects/my-style
```

Score a style frame against the references (palette coverage, off-palette area, lightness, surface, and with style
embeddings the style itself: its CSD similarity to the references, against how well they agree with each other):

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

Replay a style's measured motion with neutral shapes, to check the kit before drawing a demo film:

```bash
uv run moodreel sketch out/projects/my-style
```

Make a film follow its song: the song as data (its beat grid, bars, kick, snare and hat hits, envelopes, and the
lyric's words as sung, from any aligner), read in the film through `kit/music.js`; render with motion blur. The rules,
learned from pdoom-video's source, are in [docs/MUSIC-SYNC.md](docs/MUSIC-SYNC.md):

```bash
uv run moodreel music song.wav --lyrics words.json --out films/my-film/music-data.js
node render/render.mjs video films/my-film --fps 60 --samples 8 --shutter 0.2
```

Match a remake to its reference shot by shot, not just in stills: `moodreel compare` measures each of the reference's
shots for picture, detail, tone, motion direction and speed, worst first. What a 2D canvas can't draw (ray-marched
bodies, lensing, dense line fields, engraving that follows a surface) goes through `kit/gl.js`, the GPU layer. See
[docs/GPU.md](docs/GPU.md):

```bash
uv run moodreel compare reference.mp4 remake.mp4
```

Read what the reference does on each beat, kick and sung word, and the camera through a 3D shot, before building
them: `moodreel sync` gives the beat-sync fingerprint (how big each response is, how late and how fast it decays, and
with `--against`, what a remake misses); `moodreel pose --track` follows a rectangle through the shot and writes the
camera as `cameraAt(t)`. Both were checked against pdoom-video's source: [docs/research/VISION-TO-CODE.md](docs/research/VISION-TO-CODE.md):

```bash
uv run moodreel sync reference.mp4 --music films/my-film/music-data.js --json ref-sync.json
```

```bash
uv run moodreel pose reference.mp4 --track 12.0,13.5 --at 12.4 --points 272,378,978,180,948,462,340,672 --fov 35 --up wall --module cam.js
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
the picture, or real footage and data. The score is now here (`moodreel score`: a film's tempo grid, sections and
cues, drawn as music by deterministic synthesised instruments or by sampled ones, upright piano, strings, pizzicato,
trumpets, horn, tuba, clarinet, marimba, glockenspiel, harp and timpani, with the cue times for the picture to land on), which
makes three more styles ready: game show, microgame and 1930s rubber hose. So is pixel art (`kit/pixel.js`: an
indexed framebuffer shown through a palette, scaled by whole pixels, with Bayer dither and palette tables; the
measurement reads a reference's pixel scale, native size, palette and dither), which makes the 16-bit pixel RPG ready. And painted marks (`kit/brush.js`: brush strokes with bristles, watercolour
washes that pool at the edge, palette-knife dabs with relief, crayon broken by paper tooth, ink that bleeds, and a
repaint that turns a flat illustration into strokes; the measurement reads visible marks' coverage, scale and
direction), which makes seven more styles ready, from impasto and watercolour to ink wash and 80s cel anime. And
3D (`kit/three.js`: a three.js scene set from t, rendered into its own WebGL canvas and laid on the 2D stage, type
pinned to points in the world; `film new` copies three.js into the film), which makes ten more ready, from low-poly
islands and glass product renders to tilt-shift and HD-2D. And real material (`moodreel media add`: footage stored
as one frame per film frame, stills and data, each with its source, licence and hash in a manifest and in CREDITS;
`kit/media.js` gives the picture the frame of its own time; `film check` fails material with no source or licence),
which makes the last 15 ready: every style in the library can now be made. Films can also be narrated
(`narration.json` → `moodreel voice`: lines placed at times or on cues, voiced, subtitled from `voice.js`, the music
ducked under them at delivery) and carry sound effects without music (a score of cues alone), and be delivered
as several variants of one picture code (`film.json` variants, read with `pick()`, `film deliver --all-variants`), or
exported as a HyperFrames composition (`moodreel export hyperframes`: a paused timeline whose every seek draws the
film's own frame) or a Remotion project (`moodreel export remotion`: one composition whose every frame is the film's
own). Only the documents are imported; Moodreel re-implements the techniques.

## Repository

| Path | What it is |
|---|---|
| `render/render.mjs` | Renders any page that exposes `window.DUR`, `window.render(t)` and `window.READY` to stills or video. Video has two engines: [FrameVelo](https://github.com/gnipbao/framevelo) (the default when installed, on macOS), which keeps each frame on the GPU and encodes it with the hardware H.264 encoder, 1.8-4.3x faster than the Chrome engine on the example films with 8-36x less CPU; and Chrome (headless Chrome on puppeteer-core, one per worker, frame pacing off, x264), whose renders are the same bit for bit, which the benches use ([docs/research/render-speed.md](docs/research/render-speed.md)) |
| `moodreel/` | The Python package: `intake.py`, `measure/` (palette, surface, layout, type, rhythm), `motion/` (shots, camera, tracking, ease fitting, grammar), `check/` (frame-check, motion-check), `pack/` (kit, scaffold, sketch, pack), `film/`, `library.py`, `bench/` (test films, scorer, round trip), `cli.py` |
| `skills/moodreel/` | The director's skill: distill and produce flows, how to read the evidence, write STYLE.md, the ledger, the checks |
| `kit/` | The primitives a film's code imports: page contract, eases, tweens, seeded noise, surfaces, type ([kit/README.md](kit/README.md)) |
| `styles/` | The style library |
| `examples/` | Example films made in library styles: five with the values their code uses, for the round trip, and six showing score, pixel, brush, 3D, footage and a sampled band ([examples/README.md](examples/README.md)) |
| `bench/motion/` | The motion test films (pages and truth) and the latest report |
| `bench/roundtrip/` | The round trip's latest report ([bench/roundtrip/README.md](bench/roundtrip/README.md)) |
| `tests/` | Unit tests on synthetic data (`uv run --group dev pytest`) |
| `scripts/import_lemo_styles.py` | Re-imports the style documents from a lemo-opuscar checkout |
| `docs/` | Design and research notes |

## Acknowledgements

Moodreel stands on ideas from these projects. Apart from the lemo-opuscar style documents in `styles/` and the parts
of pdoom-video adapted under its MIT license (see `NOTICE`), it uses none of their code.

- [pdoom-video](https://github.com/mexicat/pdoom-video) — a music video computed from its song's data: word-aligned lyrics, drum hits and a beat grid drive every cut, slam and camera move, and sub-frame motion blur. The model for `moodreel music`, `kit/music.js` and docs/MUSIC-SYNC.md; `kit/gl.js` and `kit/anim.js` are adapted from its engine (MIT).

- [FrameVelo](https://github.com/gnipbao/framevelo) — the video engine: frames kept on the GPU and encoded in hardware (a dependency, Apache-2.0).

- [REM](https://github.com/sidart10/rem) — fit eases by BIC and claim only clear winners; check a rebuild with the same measurement.
- [motiscope](https://github.com/KumarSashank/motiscope) — localized motion energy, percentile thresholds, numbers for *when* and frames for *what*.
- [MoVer](https://arxiv.org/abs/2502.13372) — motion properties as verifiable predicates fed back to the generator.
- [lemo-opuscar](https://github.com/lemomo-ai/lemo-opuscar) — a style written as invariants (essence, materials, colour, type, motion, camera, sound, native moves, pitfalls) kept apart from any one film; its 59 style documents are the start of our library.
- [HyperFrames](https://github.com/heygen-com/hyperframes) — video as a deterministic function of time, rendered in a browser.

## License

Moodreel is [MIT](LICENSE). The style documents in `styles/` that come from lemo-opuscar are MIT, Copyright (c)
2026 LemoLab ([`styles/LICENSE-lemo-opuscar`](styles/LICENSE-lemo-opuscar)); each one names its source commit.
