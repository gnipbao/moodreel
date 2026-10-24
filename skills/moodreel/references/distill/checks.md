# The checks

Both checks measure your picture with the same code that measured the references, so a pass means the numbers agree,
not that the picture is good. Look at the side-by-side sheets as well; judge with your eyes what the numbers can't.

## frame-check (a still against the references)

```bash
moodreel render still <project>/look 2.5 --size 1920x1080 --out <project>/look/stills
moodreel frame-check <project> <project>/look/stills/t_2.5.jpg
```

| Result | Means | Usual fix |
|---|---|---|
| coverage < 80 %, `missing_colours` | a reference colour covering ≥ 3 % of the pictures has no near match (CIEDE2000 > 6) | use the token, not a hand-picked hex; give that colour its area |
| off-palette > 5 %, `extra_colours` | colours far from every reference colour (> 12) | a gradient, shadow, blend mode or vignette made new colours; anti-aliasing can't reach 5 % |
| lightness EMD > 0.15 | the spread of light and dark differs | too much or too little ground; type too heavy or too light |
| grain off | grain differs (none and fine both count as clean) | `grain(g, TEXTURE.grain, frame, { ground: PALETTE.ground })` |
| vignette off | | `vignette(g, W, H, TEXTURE.vignette)`; no vignette on dark grounds unless measured |
| edge_sharpness off | edges crisper or softer than the references | blur, scaling a raster, or a brush where the references are vector |
| style < floor | the frame's CSD style vector is far from the references' centre (the floor is how well the references agree with each other, less 0.05, within 0.45-0.70); `nearest_reference` names the closest | the look as a whole is off even where the numbers pass: compare with the sheet for mark-making, shape language, composition and type treatment, not colour alone; a different subject in the right style scores 0.6 and up |
| style ? | the references were measured without style embeddings, or `moodreel csd setup` has not run here | ask the user before the one-time download (2.4 GB); without it, judge the look from the sheet |

The sheet (`evidence/frame-check-NN-*.jpg`) puts the frame beside three references. A frame can pass and still miss
the style's essence; it can fail on a number and still be right (say why at gate 2). After two rounds that don't
converge, revisit the materials decision instead of nudging numbers.

## motion-check (a film against the references' motion)

```bash
moodreel motion-check <project> <project>/demo.mp4
```

Each claim passes, fails or is unknown (unknown never passes; the film or the references lack the events):

| Claim | Tolerance | When it fails |
|---|---|---|
| `<role>.duration` | median within ±25 % (at least 0.05 s); unknown under 0.17 s, too short to time | entrances or exits too quick or too slow: use `MOTION.enter.duration` |
| `<role>.ease_class` | share of the dominant class within ±20 pts; unknown when the film reads no class | the wrong family of curve: use `MOTION.enter.ease` |
| `<role>.overshoot_share`, `.overshoot` | ±25 pts; median within the references' range | bounce where the references settle, or the reverse |
| `exit_shorter` | exits shorter than entrances when the references are | |
| `stagger` | a group staggered within ±30 % of the interval | groups enter together, or with the wrong spacing |
| `hold` | median hold ≥ 80 % of the references' | the film never rests |
| `shot_length` | median within ±35 % (references with ≥ 2 shots) | cutting too fast or too slow |
| `transition_types` | no transition type the references don't use | a dissolve in a style that only cuts |
| `density` | share of time in motion within ±0.15 | too busy or too static |
| `stepping` | drawings held on the same number of frames | animate on twos with `step(t, fps / 2)` from kit/core.js |

Fix what fails and re-render; two rounds at most. A demo must show enough events for the claims to be known: a few
entrances, an exit, a group, a cut if the references cut.

## The sketch (the kit's motion, before the demo)

```bash
moodreel sketch <project> && moodreel render video <project>/sketch --fps 24 --size 1280x720 --out <project>/sketch.mp4
```

```bash
moodreel motion-check <project> <project>/sketch.mp4
```

Three neutral shapes per shot enter the commonest way the references' elements do, one after another with the
measured hold (or stagger), with the kit's eases and durations, and leave the same way; shots change by cuts or
dissolves as the references' do. A failure here is the kit's, not the demo's. Ignore its density (three shapes move
less than a real film) and its curve claims where `motion.js` says `unread` (the sketch eases with a placeholder).
