<h1 align="center">
  <picture>
    <source media="(prefers-reduced-motion: reduce)" srcset="docs/assets/moodreel-cover.webp">
    <img src="docs/assets/moodreel-motion.webp" width="100%" alt="Moodreel — Moodboard in, reel out. Twenty-four violet-to-amber film frames fan open around a moving crescent.">
  </picture>
</h1>

<p align="center"><strong>Turn a reference film’s timing and camera moves into code you can reuse for your own film.</strong></p>
<p align="center">
  <a href="CHANGELOG.md"><img src="docs/assets/badge-version.svg" alt="Version 0.1.0, pre-alpha"></a>
  <a href="pyproject.toml"><img src="docs/assets/badge-python.svg" alt="Python 3.11 or newer"></a>
  <a href="package-lock.json"><img src="docs/assets/badge-node.svg" alt="Node.js 22.18 or newer"></a>
  <a href="#license-and-credits"><img src="docs/assets/badge-license.svg" alt="Core license MIT"></a>
</p>

<p align="center"><b>English</b> · <a href="README.zh-CN.md">简体中文</a></p>
<p align="center"><a href="#remake-comparisons">Remake comparisons</a> · <a href="#quickstart">Quickstart</a> · <a href="#showcase">Example source</a> · <a href="#make-a-film">Use with an agent</a> · <a href="#how-it-works">How it works</a> · <a href="#contributing">Contribute</a></p>

In Skillry’s launch film, each icon lasts **5–6 frames** and a prompt types at about **36 characters a second**. With Moodreel, you and a coding agent can measure those decisions and write them into drawing code. When we made *Tidepool*, a launch film for a fictional tide forecast API, the prompt asked for tomorrow’s tides and kept the same 36-character cadence. [See how the timing was measured](packs/information-keynote/ascii-glitch-launch/evidence/LEDGER.md) · [Read Tidepool’s typing timeline](packs/information-keynote/ascii-glitch-launch/demo/timeline.js)

Run `measure` locally on a reference, then keep the rules and JavaScript in a style pack. Once you have a draft, `compare` ranks the passages that differ most and `diff` tells you how many frames early or late a cut lands. Revise that shot and check it against the previous pass. [Style packs](packs/README.md) · [Shot-by-shot workflow](docs/workflows.md#compare-a-remake-with-its-reference)

## Remake comparisons

The reference plays on top and the remake below. Select a preview for the full comparison with sound. The timestamps below refer to those full films.

<p align="center">
  <a href="docs/assets/remakes/case2.mp4?raw=true"><picture><source media="(prefers-reduced-motion: reduce)" srcset="docs/assets/remakes/case2.jpg"><img src="docs/assets/remakes/case2.webp" width="250" alt="Artistic Butterflies. Silver wings turn amber in both halves of the frame."></picture></a>
  <a href="docs/assets/remakes/case1.mp4?raw=true"><picture><source media="(prefers-reduced-motion: reduce)" srcset="docs/assets/remakes/case1.jpg"><img src="docs/assets/remakes/case1.webp" width="250" alt="Skillry above, Knackly below. A wall of product cards gives way to type."></picture></a>
  <a href="docs/assets/remakes/case3.mp4?raw=true"><picture><source media="(prefers-reduced-motion: reduce)" srcset="docs/assets/remakes/case3.jpg"><img src="docs/assets/remakes/case3.webp" width="240" alt="Scarlet Sheath above, Ember Rift below. Curved trails of fire reveal a glowing eye."></picture></a>
</p>

- **Artistic Butterflies · Find the two seconds that run slow.** Split seconds 6–12 into three windows. `compare` ranks 6–8 s as the largest mismatch. Mean motion across the frame is **0.60×** the reference in that window. Pause at 7 s. The reference’s lower wings have scattered into a cloud while the remake still has two rounded lobes. [Full film · 53 s](docs/assets/remakes/case2.mp4?raw=true) · [Run the measurement](docs/assets/remakes/README.md#reproduce-the-measurements) · [Bee’s original](https://x.com/thtbee_/status/2123259795172212871)
- **Skillry → Knackly · Reconstruct a camera move.** Positions and widths of 14 cards at 3.7 s and 4.4 s gave the remake’s camera a path through a cylindrical wall of cards. The lower panel shows the fifth pass. The same pack’s montage and typing rules later carried over to *Tidepool*. [Full film · 16 s](docs/assets/remakes/case1.mp4?raw=true) · [Camera measurements](packs/information-keynote/ascii-glitch-launch/evidence/LEDGER.md)
- **Scarlet Sheath → Ember Rift · Check a cut to the frame.** At frame 559 (9.317 s), both films cut from a white flash back to a red eye. `diff` reports a **zero-frame offset** for that cut. With the timing accounted for, you can concentrate on the shape of the fiery lines around the eye. [Full film · 15 s](docs/assets/remakes/case3.mp4?raw=true) · [Run the cut check](docs/assets/remakes/README.md#reproduce-the-measurements)

[26-second highlights · silent MP4](docs/assets/remakes/highlights.mp4?raw=true) · [Original posts and credits](docs/assets/remakes/README.md) · [How to compare your own footage](docs/workflows.md#compare-a-remake-with-its-reference)

## Quickstart

Render *First Light*, a 12-second risograph sunrise, then use the MP4 as input to the measurement tools. The example includes its artwork and runs locally without an API key.

**Requirements** — Python 3.11+, uv, Node.js 22.18+ with npm, and FFmpeg with both `ffmpeg` and `ffprobe` on your path. The first install downloads dependencies and Puppeteer's Chrome. [Install uv](https://docs.astral.sh/uv/getting-started/installation/) · [Get FFmpeg](https://ffmpeg.org/download.html)

```sh
git clone https://github.com/gnipbao/moodreel.git
cd moodreel
uv sync --locked
npm ci
```

**1. Render the film.** Two spot inks print a sunrise. Where they overlap, a third colour appears. Open `out/first-light.mp4` to watch the result.

```sh
uv run moodreel render video examples/first-light --size 1280x720 --fps 24 --engine chrome --out out/first-light.mp4
```

**2. Measure the same film.** The report in `out/print-study/MEASURE.md` describes the colour roles, surface and motion it found. Compare it with the drawing code to see which choices the measurements recover. [First Light source](examples/first-light/main.js)

```sh
uv run moodreel intake out/print-study out/first-light.mp4
uv run moodreel measure out/print-study
```

## Showcase

Both films below include their treatment and JavaScript drawing source. Open a scene to change the timing or draw a new shot.

| Swiss Programme · Swiss Motion Graphics | First Save · 16-bit Pixel RPG |
| :--- | :--- |
| <picture><source media="(prefers-reduced-motion: reduce)" srcset="docs/assets/swiss-programme.jpg"><img src="docs/assets/swiss-programme.gif" width="480" alt="Swiss typography and bars snap into register on a measured grid."></picture> | <picture><source media="(prefers-reduced-motion: reduce)" srcset="docs/assets/first-save.jpg"><img src="docs/assets/first-save.gif" width="480" alt="A pixel-art character walks across a landscape with scrolling mountain layers."></picture> |
| A grid, two rules and one red exception in a 15-second title sequence. [Treatment](examples/swiss-programme/TREATMENT.md) · [Drawing code](examples/swiss-programme/main.js) | A 320 × 180 pixel world with parallax ridges, a walking character and a save prompt. [Treatment](examples/first-save/TREATMENT.md) · [Drawing code](examples/first-save/main.js) |

[Browse all example films](examples/README.md) · [Preview sources and credits](docs/assets/README.md)

### Style library

Browse 59 imported style guides and three packs distilled with Moodreel. Each of the three packs below includes a style guide, a ledger tracing its values to evidence, a drawing kit and the source for its demo film. [All styles](styles/README.md) · [Install a pack](packs/README.md)

| [Ink Chronicle](packs/east-asian-traditions/ink-chronicle/README.md) | [Signal Plates](packs/graphic-type/signal-plates/README.md) | [ASCII Glitch Launch](packs/information-keynote/ascii-glitch-launch/README.md) |
| :---: | :---: | :---: |
| ![Rows of ink characters recede toward a vanishing point](packs/east-asian-traditions/ink-chronicle/styleframe.jpg) | ![Orange contours wrap a cylinder on a dark field](packs/graphic-type/signal-plates/styleframe.jpg) | ![The word Tidepool dissolves into pixel lettering](packs/information-keynote/ascii-glitch-launch/styleframe.jpg) |

## Make a film

To start with a built-in style, create a film folder, write its treatment in `films/launch/TREATMENT.md` and draw the scenes in `films/launch/main.js`. The template points to the chosen style's rules. The examples show how to translate them into a finished film. [Example films and source](examples/README.md)

```sh
uv run moodreel styles swiss
uv run moodreel film new launch --style swiss-motion
```

Once the scenes are ready, run `uv run moodreel film deliver films/launch` to render the MP4 and poster, then `uv run moodreel film check films/launch` to check the rendered video for black frames and the text for reading time.

**With a coding agent**, open this checkout and give the agent a brief like the one below. The director skill covers the treatment, drawing, review and delivery. [Director skill](skills/moodreel/SKILL.md)

> Read `skills/moodreel/SKILL.md` and use `uv run moodreel`. Make a 15-second title sequence for a night train in the Swiss Motion Graphics style. Show me a style frame before rendering the film.

## How it works

1. **Measure the references.** The CLI reads palette, surface, type and layout from images. A clip also gives it timing, easing and stagger. The results go into `MEASURE.md`.
2. **Build the style pack.** The director describes the reusable rules in `STYLE.md` and records the evidence behind each value in `LEDGER.md`. A style frame and demo film put the drawing kit to the test. [Distillation workflow](docs/workflows.md#distill-a-style-pack)
3. **Draw new scenes.** A film's JavaScript function `window.render(t)` draws the frame at time `t`. The renderer can seek directly to a still or encode the frames to an MP4. [Drawing guide](skills/moodreel/references/produce/drawing.md) · [Renderer](render/render.mjs)

## Documentation

| I want to… | Start here |
| --- | --- |
| Distill my own references into a pack | [Distillation workflow](docs/workflows.md#distill-a-style-pack) |
| Add a score, footage or narration, or export to HyperFrames or Remotion | [Production and delivery](docs/workflows.md#produce-and-deliver-a-film) |
| Compare a remake with a reference, shot by shot | [Shot analysis](docs/workflows.md#compare-a-remake-with-its-reference) |
| Write a scene or a reusable drawing primitive | [JavaScript kit](kit/README.md) · [Drawing guide](skills/moodreel/references/produce/drawing.md) |

**Measurement accuracy.** On 12 code-rendered test films with known motion, the clean run found 95 of 99 target properties and reported 25 spurious detections. Calibration on real-world references and human evaluation are still open. [Benchmark results](bench/motion/REPORT.md) · [Evaluation and limits](docs/workflows.md#evaluate-the-measurements) · [Changelog](CHANGELOG.md)

## Contributing

Bug reports, documentation fixes and contributions are welcome. For a rendering issue, include the command, your OS and a small example others can run. [Open an issue](https://github.com/gnipbao/moodreel/issues) · [Contributor setup and pull requests](CONTRIBUTING.md)

## License and credits

Moodreel's core uses the MIT license. The imported style guides retain LemoLab's MIT notice. The optional `kit/3dcv/` port from 3DCodeVerse uses **CC BY-NC-SA 4.0**. Including it with `--with 3dcv` makes the resulting film non-commercial under the port's license. Credit the source and share adaptations of the port under the same terms. [Core license](LICENSE) · [Style credits](styles/LICENSE-lemo-opuscar) · [3DCodeVerse terms](kit/3dcv/LICENSE) · [Third-party notices](NOTICE) · [Acknowledgements](docs/workflows.md#acknowledgements)
