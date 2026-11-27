# Moodreel workflows

[Project README](../README.md) · [简体中文](workflows.zh-CN.md)

Run the commands from the repository root after setup. The distillation examples use your own images and a clip in `refs/`. The production examples use a film you have created in `films/launch/`.

## Distill a style pack

### Read the references

```sh
project=out/projects/my-style
uv run moodreel intake "$project" refs/*.png refs/teaser.mp4 --source own
uv run moodreel measure "$project"
```

Start with `MEASURE.md` in the project folder. It names the background, ink and accent colours and describes surface marks, type sizes, layout, motion and rhythm. Follow its links to the measurements and frame strips in `measure/` and `evidence/`. If intake finds two distinct palettes, decide which references belong together before deriving a rule.

In `ANALYSIS.md`, identify the three to five traits that give this style its character and list compositions that belong to the source material. Write the eleven sections of `STYLE.md`, record each value and its basis (observed, derived or inferred) in `LEDGER.md`, and put choices such as typefaces and sound in `DECISIONS.md`. A single clip can show how a style handles a cut and still leave its broader editing choices open. Review these decisions before drawing. [Writing a style](../skills/moodreel/references/distill/writing-style-md.md) · [Evidence ledger](../skills/moodreel/references/distill/ledger.md)

### Check the look and the motion

```sh
uv run moodreel kit "$project"
uv run moodreel scaffold "$project"
```

`kit/tokens.js` and `kit/motion.js` carry the measured values. Draw an original composition in `look/main.js`, then compare it to the references. These render examples assume a 16:9 frame. For a portrait or square project, use `--size` with the dimensions reported by intake.

```sh
uv run moodreel render still "$project/look" 2.5
uv run moodreel frame-check "$project" "$project/look/stills/t_2.5.jpg"
uv run moodreel scene-check "$project" "$project/look/stills/t_2.5.jpg"
```

`frame-check` reports colour coverage, off-palette area, lightness and surface differences. Optional CSD embeddings compare the frame with the references' own degree of agreement. To include them, run `uv run moodreel csd setup` before `measure` (or measure again). Setup downloads 2.4 GB and stores about 0.6 GB of CC BY 4.0 model weights. `scene-check` compares compositions and makes a contact sheet of close matches. Review that sheet alongside the list in `ANALYSIS.md`. [How to read the checks](../skills/moodreel/references/distill/checks.md)

Test the kit's timing with neutral shapes before drawing the demo. The sketch makes an easing or stagger error easier to isolate.

```sh
uv run moodreel sketch "$project"
uv run moodreel render video "$project/sketch" --fps 24 --size 1280x720 --out "$project/sketch.mp4"
uv run moodreel motion-check "$project" "$project/sketch.mp4"
```

`motion-check` tests move durations, easing, overshoot, stagger and drawing cadence. It reports shot length, holds and density as editing advice. A claim marked unknown needs more evidence. With several reference clips, use `--reference vid01` to select one.

### Build the demo and install the pack

Save the approved still as `styleframe.jpg` at the project root. Write an original 15–30 second demo in `demo/`, including a `build.sh` and asset credits, and render it to `demo.mp4`. Review the rendered film before installing the pack.

```sh
uv run moodreel motion-check "$project" "$project/demo.mp4"
uv run moodreel scene-check "$project" "$project/demo.mp4"
uv run moodreel pack "$project" --slug my-style --name "My Style" --strict --build
```

`--strict` makes untraced values in the style guide an error. `--build` runs the demo build script in a scratch output directory. Installed packs live in `~/.moodreel/styles` by default. The pack records reference hashes and includes the reference contact sheet only when all inputs are marked as your own work.

To use a finished example, run `uv run python scripts/packs.py install signal-plates`. The same script's `export` command copies library packs back to the repository and refreshes its index. Each pack documents demo rebuilds and any fonts to fetch. [Pack directory](../packs/README.md) · [Style catalogue](../styles/README.md)

## Produce and deliver a film

If your coding agent calls `moodreel` directly, run `uv tool install --editable .` from this checkout and point the agent to `skills/moodreel/SKILL.md`. The editable install keeps the renderer, kit and style library available from this checkout when working on another film.

Start from a treatment with the subject, shots and beats. The film's `main.js` draws each frame at time `t` with the style's kit. Keep the treatment, source and credits with the film. [Brief and treatment](../skills/moodreel/references/produce/brief-and-treatment.md) · [Drawing a film](../skills/moodreel/references/produce/drawing.md)

| Task | Input and result |
| --- | --- |
| Draw in a medium | Use `kit/pixel.js` for indexed pixels and Bayer dithering, `kit/brush.js` for bristles, washes and ink, or `kit/three.js` for a 3D scene using the same clock. [Kit reference](../kit/README.md) |
| Use existing material | `media add` imports footage, stills or data and records source, licence and hash. `kit/media.js` reads the appropriate frame at time `t`. [Film using credited footage](../examples/every-style/TREATMENT.md) |
| Score and narrate | `score.json` defines musical sections and cues. `moodreel score` writes `score.js` and a WAV. Synthesised instruments work locally. `uv run moodreel samples fetch` adds 272 MB of CC0 orchestral samples. On macOS, `moodreel voice` places draft narration from `narration.json` on the timeline and writes subtitle timings in `voice.js`. [Scored example](../examples/quiz-night/TREATMENT.md) |
| Deliver variants | Define each variant in `film.json` and read its values with `pick()` in `kit/variant.js`. `film deliver --all-variants` writes a video and poster per variant. [Delivery guide](../skills/moodreel/references/produce/delivery.md) |

```sh
uv run moodreel film deliver films/launch --music track.wav
uv run moodreel film check films/launch
uv run moodreel export hyperframes films/launch
uv run moodreel export remotion films/launch
```

Delivery renders the picture, mixes the available score, narration and effects, targets −14 LUFS for the audio and writes the MP4 and poster. Running `film check` after delivery lets it inspect the render for black frames and musical cue timing. The check also examines declared text hold times, media credits and, for a distilled style, agreement with its measurements. Both export formats call the film's drawing function at the target time. On macOS the video renderer selects FrameVelo when available. Use `--engine chrome` on delivery when comparing renders for reproducibility. [Renderer measurements](research/render-speed.md)

### Cut to a song

Supply word timings from your aligner if the picture follows lyrics. The generated module contains the beat grid, bars, drum hits, envelopes and any timed words. Read it through `kit/music.js` to place cuts, text and camera moves. `sync` measures how the picture responds to beats, kicks and sung words. [Music sync guide](MUSIC-SYNC.md)

```sh
uv run moodreel music song.wav --lyrics words.json --out films/launch/music-data.js
uv run moodreel sync reference.mp4 --music films/launch/music-data.js --json reference-sync.json
uv run moodreel sync remake.mp4 --music films/launch/music-data.js --against reference-sync.json
```

For subframe motion blur, set `"motion_blur": {"samples": 8, "shutter": 0.2}` in `film.json` or pass `--samples 8 --shutter 0.2` to `render video`. Each output frame averages eight samples across a fifth of a frame interval.

### Draw an illustrated 3D shot

`kit/look3d.js` shades surfaces with a colour ramp and stippling attached to the geometry. `kit/post3d.js` adds tinted occlusion, depth of field, bloom and grain. Hold a character pose for two frames with `look3d.held(t, fps, 2)` while moving the camera every frame. To build a character from signed distance fields, start with the bundled mannequin. [Illustrated 3D drawing](../skills/moodreel/references/produce/drawing.md) · [GPU tools](GPU.md)

```sh
uv run moodreel model build mannequin
uv run moodreel model check mannequin --model out/model/mannequin/mannequin.json
uv run moodreel model sheet out/model/mannequin/mannequin.json --out out/model/mannequin/sheet.png
```

The build outputs a mesh and rig for `kit/figure.js`. The check reports whether parts are closed, which ones float and how deeply each tested pair intersects in each pose. The sheet shows the same poses from four views. The changelog records the tests behind this workflow, including whether the stipple stays on a surface as the camera moves. [3D implementation and measurements](../CHANGELOG.md)

### Make a social wall

```sh
uv run moodreel wall search YouMind
uv run moodreel wall record out/walls/youmind --pick 3,5,8,11
uv run moodreel wall make out/walls/youmind
```

Search returns a numbered sheet and `CANDIDATES.md` for public YouTube and Bilibili posts. Choose posts by their actual numbers and review author, promotion and reuse flags. Recording keeps the platform appearance and skips pages that require sign-in. The final command builds a 4K wall with a credit for each card. [Social wall guide](../skills/moodreel/references/produce/social-wall.md)

## Compare a remake with its reference

`origin` identifies cuts and estimates how each shot was made from its motion and drawing cadence. `dossier` collects keyframes and measurements for each shot. For a targeted comparison, create `scenes.json` as an array of time windows in seconds, such as `[[0, 2.5, "opening"], [2.5, 5, "title"]]`. Use times that match your reference.

```sh
uv run moodreel origin reference.mp4 --out origin
uv run moodreel dossier reference.mp4 --shots scenes.json --out dossier
uv run moodreel compare reference.mp4 remake.mp4 --shots scenes.json --json pass1.json --sheet pairs.jpg
uv run moodreel review reference.mp4 remake.mp4 --shots scenes.json --out review
uv run moodreel diff reference.mp4 remake.mp4 --shots scenes.json --out diff
```

| Question | What to inspect |
| --- | --- |
| Which shot should I revisit? | `compare` ranks differences in structure, detail, tone, direction and speed. Compare a new render with `--against pass1.json`. Use `--motion opening` to inspect motion within one named window. |
| Where does timing drift? | `diff` lists early, late, missing and extra cuts, audio offset and black, flat or frozen stretches. `review` puts reference and remake side by side for colour and frame-by-frame motion review. |
| How did the camera move? | `camera --against` compares pan, push and roll. Its `--js` track drives `kit/follow.js`. For a 3D shot with a visible rectangle, `pose --track` can estimate the camera from its corners and write `cameraAt(t)`. [Camera and music measurements](research/VISION-TO-CODE.md) |
| How do I repeat the comparison? | `uv run moodreel pass reference.mp4 films/launch --shots scenes.json --name p1` renders, scores and writes the contact sheet and diff in `films/passes/p1/`. On the next pass, add `--against films/passes/p1`. |

Optional Jev analysis uses `TYPESAFE_API_KEY`. On a pass, `--jev --allow-text-upload` sends window names and measurements for ranking. `--vision --allow-image-upload` sends sample frames for visual comparison. `look`, `direct` and `track` also support frame-based analysis. `track --js` can supply subject boxes to `kit/lock.js`. [Shot-by-shot workflow](../skills/moodreel/references/distill/remaking.md)

## Evaluate the measurements

To inspect one clip, run `uv run moodreel motion clip.mp4 --out out/clip` and open `out/clip/motion.json`. The reader tracks position, scale, opacity and visible extent, fits easing curves and looks for stagger, camera motion, transitions, held drawings and ambient loops. It names an ease family only when the evidence separates it from alternatives. Optional Tesseract OCR lets it follow changing numbers. [Motion extraction methods](research/motion-extraction.md)

The checked-in motion benchmark compares 12 code-drawn films with known values, each clean and degraded (¾ size, reduced contrast, grain, 25 fps, CRF 30). Midpoint timing measures when a move reaches half its travel. [Per-film motion results](../bench/motion/REPORT.md)

| Input | Target properties found | Extra detections | Midpoint within one frame | Easing direction correct | Eases named / wrong |
| --- | ---: | ---: | ---: | ---: | ---: |
| Clean | 95/99 | 25 | 85% | 96% | 30 / 0 |
| Degraded | 91/99 | 19 | 87% | 82% | 10 / 0 |

Both sets identified 13 of 14 transitions and all five loop and particle tests. Overlapping motion can add false detections, and frame-rate conversion can obscure drawings held on twos. The separate round trip recovers five example films' style rules and compares them with their source. It missed the clear-screen cut in *Boot* and estimated the wrong title weight in *Morning*. In the second blind run, a fresh agent director and judge agreed on at least eight of eleven style sections for all five films. Calibration on real-world references and human evaluation remain open. [Round-trip results](../bench/roundtrip/REPORT.md) · [Blind verdicts](../bench/roundtrip/BLIND.md) · [Manual evaluation plan](MANUAL-TEST.md)

```sh
uv run moodreel bench make
uv run moodreel bench render
uv run moodreel bench motion
uv run moodreel bench roundtrip
```

The benchmark commands regenerate the fixture pages or reports in the checkout. For a blind run, `bench blind make` prepares anonymised packets after the round trip. A director and judge supply the new guides and verdicts, then `bench blind score` writes their results. [Blind run instructions](../bench/roundtrip/README.md)

## Acknowledgements

| Project | Contribution |
| --- | --- |
| REM and motiscope | Comparing ease fits and checking a reconstruction with the same measurement come from REM. Local motion energy and percentile thresholds draw on motiscope. [REM](https://github.com/sidart10/rem) · [motiscope](https://github.com/KumarSashank/motiscope) |
| MoVer | Verifiable motion properties inform the checks that feed back into production. [MoVer paper](https://arxiv.org/abs/2502.13372) |
| lemo-opuscar | The library imports 59 style documents, each describing reusable visual rules. The files retain their source commit and MIT attribution. [Upstream project](https://github.com/lemomo-ai/lemo-opuscar) · [LemoLab licence](../styles/LICENSE-lemo-opuscar) |
| HyperFrames and rea-video | HyperFrames inspired deterministic browser rendering, frame-exact timing and the comparison checklist. rea-video inspired classifying how a shot was made before reconstructing it. [HyperFrames](https://github.com/heygen-com/hyperframes) · [rea-video](https://github.com/JuneYaooo/rea-video) |
| pdoom-video | Song-driven timing, word-aligned lyrics and subframe motion blur informed the music workflow. The adapted kit modules and documentation retain the upstream MIT notice. [Upstream project](https://github.com/mexicat/pdoom-video) · [Third-party notices](../NOTICE) |
| FrameVelo | This Apache-2.0 dependency provides GPU-resident frames and hardware H.264 encoding. [FrameVelo](https://github.com/gnipbao/framevelo) |
| 3DCodeVerse | The framework and showcase informed Moodreel's own colour-ramp materials, surface stipple, SDF characters, pose checks and multi-view sheets. The optional `kit/3dcv/` ports the showcase's look engine and shot runtime under CC BY-NC-SA 4.0. A film created with `--with 3dcv` carries the attribution and non-commercial terms. [Framework](https://github.com/gaoypeng/3dcodeverse) · [Showcase](https://huggingface.co/datasets/3dcodeverse/3dcodeverse-awesome-showcase) · [Port licence and changes](../kit/3dcv/LICENSE) |
