# Example films

Films made with Moodreel in library styles, each drawn entirely in code from its style's STYLE.md. They show what a
film's source looks like (a treatment, a kit filled in from the style, one `main.js`), and they are the round trip's
test material: `moodreel bench roundtrip` distils each one back and compares the result with the values in its code
([bench/roundtrip](../bench/roundtrip/README.md)).

| Film | Style | Length | What it shows |
|---|---|---|---|
| [swiss-programme](swiss-programme/TREATMENT.md) | Swiss Motion Graphics (`swiss-motion`) | 15 s, 1920×1080, 24 fps | a grid, two rules on two spreads, snaps landing on a 120 BPM beat grid, clip reveals, a page turn, one red exception moving linearly off the grid, a knife cut |
| [first-light](first-light/TREATMENT.md) | Risograph Print (`risograph`) | 12 s, 1920×1080, 24 fps | two spot inks multiplied on warm paper, their overprint, stepped halftone tints, misregistration, grain, drawings on twos, a roller wipe, a plate lifting away |

Render one (needs the setup in the main README):

```bash
uv run moodreel render video examples/first-light --fps 24 --size 1280x720 --workers 3
```

```bash
uv run moodreel film check examples/first-light
```

Each film's folder holds `TREATMENT.md` (brief, structures considered, beats), `main.js`, `kit/` (the shared
primitives plus `tokens.js` and `motion.js` filled in from the style), `CREDITS` (the system faces they use; a
published film sets an OFL face instead), `build.sh` and `truth.json`: the values the code uses, in screen
coordinates, for the round trip. Keep `truth.json` in step when you change a film.
