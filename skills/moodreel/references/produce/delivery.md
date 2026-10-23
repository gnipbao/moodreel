# Checking and delivering

```bash
moodreel film check films/<name>
moodreel film deliver films/<name> --music track.wav
```

`film check` reports:

- **reading**: lines that leave before they can be read (needs window.TEXTS, see drawing.md);
- **black frames** inside the film (after a render exists in `out/video.mp4`);
- for a distilled style: **frames** (three stills scored against the style's references, as frame-check) and
  **motion** (the film's grammar against the style's, as motion-check);
- for a film with `media/`: **media**, every piece with a source and a licence, and nothing in `media/` without an
  entry in its manifest;
- for a film with a `score.json`: **cues**, whether the picture lands on the music: each cue wants a move starting or
  landing, a cut, or the picture settling within two frames of it (a `stop` wants nothing); at least 80 % of them must
  be hit, and the share of landings on the beat is reported against chance.

Fix everything it finds in one round, then check once more. What is still off after that, tell the user in one line.

**Variants.** Several versions of one film (another palette, seed, line of text, length; a cut-down for social)
go in `film.json` as `"variants": {"name": {"ground": "#c83228", "duration": 6}, ...}`; the page reads them with
`pick(key, default)` from `kit/variant.js`, so the picture code stays one. `film deliver --variant NAME` (or
`--all-variants`) writes `<name>-<variant>.mp4` and `poster-<variant>.jpg`; `film check --variant NAME` checks one.
A variant's `duration` and `poster` replace the film's.

With a `narration.json`, `film deliver` voices it first (the subtitles read `voice.js`), brings the speech to
−16 dBFS, sets the music 6 dB lower and ducks it further under each line, and mixes the two before the loudness pass.
`film deliver` renders the film, normalises the music to −14 LUFS (two-pass loudnorm, a 1 s fade at the end), muxes,
and writes `<name>.mp4` and `poster.jpg` (at `film.json → poster`). With no `--music` it uses the film's own score
(`score.json`, rendered first, so the picture reads the cue times it was written to); with neither, the film is
silent.

## Before handing over

- Watch the delivered file at full speed, with sound.
- `CREDITS` lists every third-party asset in the film (typefaces, images, data, music) with its source and licence.
- `TREATMENT.md` and the source stay with the film; `build.sh` rebuilds it with one command.

Tell the user, in their language: where the film and the poster are, what the treatment chose and why in two lines,
what you could not do (a `later` capability, a check that still fails), and that CREDITS lists the licences of what
the film uses.
