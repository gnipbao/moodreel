# Checking and delivering

```bash
moodreel film check films/<name>
moodreel film deliver films/<name> --music track.wav
```

`film check` reports:

- **reading**: lines that leave before they can be read (needs window.TEXTS, see drawing.md);
- **black frames** inside the film (after a render exists in `out/video.mp4`);
- for a distilled style: **frames** (three stills scored against the style's references, as frame-check) and
  **motion** (the film's grammar against the style's, as motion-check).

Fix everything it finds in one round, then check once more. What is still off after that, tell the user in one line.

`film deliver` renders the film, normalises the music to −14 LUFS (two-pass loudnorm, a 1 s fade at the end), muxes,
and writes `<name>.mp4` and `poster.jpg` (at `film.json → poster`). Without music the film is silent.

## Before handing over

- Watch the delivered file at full speed, with sound.
- `CREDITS` lists every third-party asset in the film (typefaces, images, data, music) with its source and licence.
- `TREATMENT.md` and the source stay with the film; `build.sh` rebuilds it with one command.

Tell the user, in their language: where the film and the poster are, what the treatment chose and why in two lines,
what you could not do (a `later` capability, a check that still fails), and that CREDITS lists the licences of what
the film uses.
