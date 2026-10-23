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
| palette | ground, ink, accent roles | CIEDE2000 ≤ 6 from the film's colour (or the nearest of several, for a ramp); no accent: the role holds a tone of the ground's or ink's hue |
| surface | grain | both under 2.5 levels, or within ±50 % |
| | vignette | within 0.04, or inside a range |
| | halftone period and angle (design px) | within 10 % and 3°; none when the film has none |
| | scanline period (design px) | within 10 % |
| type | title size (font size as a share of the height) | within ±25 % |
| | title weight | within 100 of the film's weight |
| motion | cuts, dissolves and dips | each found at its time (as the motion bench matches them), and no other |
| | drawings held on | the same (ones, twos) |
| kit eases | entrance, exit, move class | the kit's class is the film's; *unknown* when the kit leaves the curve unread (safe: the director picks it), *fail* only when it names a wrong one |

Then every move in the film, scored as the [motion bench](../motion/README.md) scores its test films (matched by
place and t50 within a quarter second) and grouped by the reader it needs: `move`, `scale` and `opacity` (the
template tracker, `mvp`); `clip`, `stretch` and `wipe` (the extent reader, added after the first round trip and
still marked `v1` in the truth); `draw-on` and a camera on a flat ground (not measured yet). A stretch and a wipe
match each other, since a solid shape can't tell them apart. Each move is *missed*, *claimed right* or *wrong* (the
ease family or class was claimed), or *guessed right* or *wrong* (timed, but the curve was left unread).

Then the kit's motion is replayed: `moodreel sketch` draws three neutral shapes per shot that enter and leave with
the kit's eases, durations, holds and staggers, and `motion-check` compares that film's grammar with the
references', claim by claim (the sketch's density, and its curve claims where the kit left the curve unread, are
unknown: they say nothing about the kit). §8 of the design asks four in five to pass.

Last, the five STYLE.md sections the measurements speak for are judged from all of the above: §2 materials (the
surface), §3 colour (the palette), §4 type, §5 motion (the kit's eases, and the sketch's claims), §6 camera and
editing (transitions, the drawing rate, camera moves). The other six sections are the director's judgement; a
fair test of them needs a director distilling real references without having read the style.

## Blind distillation (the other six sections)

```bash
uv run moodreel bench blind make
```

turns each round-trip project into a packet under a neutral code (`out/blind/A/packet`, `B`, ...): the references,
`MEASURE.md`, `measure/`, `evidence/`, the kit, the STYLE.md template and `BRIEF.md`, with every path or file name
that could name the film left out. A director who has read neither the style nor this repository's examples (an
agent started fresh, or a person) works only from the packet and writes `STYLE.md` there. A judge then follows
`out/blind/JUDGE.md`, comparing it with the library's STYLE.md section by section into
`out/blind/<code>/verdict.json`, and

```bash
uv run moodreel bench blind score
```

writes [BLIND.md](BLIND.md): the eleven verdicts per film beside the round trip's own five, the judge's notes, and
§8's line (at least 8 of 11 "same"); the distilled STYLE.md files and the verdicts are kept in [blind/](blind/).
Whoever made the films can't be the director: they have read the styles.

First run (2026-10-23; the director and the judge were each a freshly started agent, the director reading only the
packets and the skill): only swiss-motion passes (8 of 11 "same"); dark-keynote 7, ascii-crt 6, risograph 5,
pictogram-motion 3. No section was judged "different" or "absent": every miss is "partly". The director gets each
film's surface right and then turns what that one film didn't do into a rule (no second hue, no green phosphor,
never rotate or zoom, the mosaic never moves), and puts the beat lock under sound instead of motion.

## Adding a film

Make it with `moodreel film new <name> --style <slug> --root examples`, then write `truth.json` next to `main.js`:
`W`, `H`, `fps`, `dur`; `stills` (times for the still references); `palette` (`ground`, `ink`, `accent`);
`surface` (`grain`, `vignette`, `halftone` as `{period_px, angle}` or null); `type` (`title` as a share of the
height, `weight` as a list of acceptable weights); `motion` (the dominant `entrance`, `exit` and `move` class, or
null); `transitions` and `stepping` as in the motion bench; and `events`, one per tween, with `element`, `prop`,
`t0`, `t1`, `ease` (a GSAP name or `bezier(x1,y1,x2,y2)`), `from`, `to`, `end_xy` (the element's centre at rest, in
screen pixels at the design size; a stretch may give its anchor instead), `scope` and `reader`. Props are `x`, `y`,
`scale`, `opacity`, `sx`, `sy`, `wipe` (the share shown), `draw` and `panx`. List what you leave out, and why, in `omitted`.
