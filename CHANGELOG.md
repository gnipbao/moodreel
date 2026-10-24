# Changelog

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
