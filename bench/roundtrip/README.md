# Round trip

Does a style survive being distilled? Each film in [examples/](../../examples/README.md) is made in code from a
library style, so every value in it is known. `moodreel bench roundtrip` renders it (the video at 1280×720 and a
few stills at its design size), takes those in as references exactly as a user's would be, measures them, writes
the kit, and compares what a style pack would carry with the film's own values.

```bash
uv run moodreel bench roundtrip
```

```bash
uv run moodreel bench roundtrip --only first-light
```

It writes [REPORT.md](REPORT.md) here; the work folders (references, project, measurements, kit) stay under
`out/roundtrip/`.

## What is compared

| Group | Value | Passes when |
|---|---|---|
| palette | ground, ink, accent roles | CIEDE2000 ≤ 6 from the film's colour |
| surface | grain | both under 2.5 levels, or within ±50 % |
| | vignette | within 0.04 |
| | halftone period and angle (design px) | within 10 % and 3°; none when the film has none |
| type | title size (font size as a share of the height) | within ±25 % |
| | title weight | within 100 of the film's weight |
| motion | cuts, dissolves and dips | the same number |
| | drawings held on | the same (ones, twos) |
| kit eases | entrance, exit, move class | the kit's class is the film's; *unknown* when the kit leaves the curve unread (safe: the director picks it), *fail* only when it names a wrong one |

Then every move in the film, scored as the [motion bench](../motion/README.md) scores its test films (matched by
place and t50 within a quarter second) and grouped by the reader it needs: `move`, `scale` and `opacity` (the
template tracker, `mvp`); `clip`, `stretch` and `wipe` (the extent reader, added after the first round trip and
still marked `v1` in the truth); `draw-on` and a camera on a flat ground (not measured yet). A stretch and a wipe
match each other, since a solid shape can't tell them apart. Each move is *missed*, *claimed right* or *wrong* (the
ease family or class was claimed), or *guessed right* or *wrong* (timed, but the curve was left unread).

## Adding a film

Make it with `moodreel film new <name> --style <slug> --root examples`, then write `truth.json` next to `main.js`:
`W`, `H`, `fps`, `dur`; `stills` (times for the still references); `palette` (`ground`, `ink`, `accent`);
`surface` (`grain`, `vignette`, `halftone` as `{period_px, angle}` or null); `type` (`title` as a share of the
height, `weight` as a list of acceptable weights); `motion` (the dominant `entrance`, `exit` and `move` class, or
null); `transitions` and `stepping` as in the motion bench; and `events`, one per tween, with `element`, `prop`,
`t0`, `t1`, `ease` (a GSAP name or `bezier(x1,y1,x2,y2)`), `from`, `to`, `end_xy` (the element's centre at rest, in
screen pixels at the design size; a stretch may give its anchor instead), `scope` and `reader`. Props are `x`, `y`,
`scale`, `opacity`, `sx`, `sy`, `wipe` (the share shown), `draw` and `panx`. List what you leave out, and why, in `omitted`.
