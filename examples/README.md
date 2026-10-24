# Example films

Films made with Moodreel in library styles, each drawn entirely in code from its style's STYLE.md. They show what a
film's source looks like (a treatment, a kit filled in from the style, one `main.js`), and they are the round trip's
test material: `moodreel bench roundtrip` distils each one back and compares the result with the values in its code
([bench/roundtrip](../bench/roundtrip/README.md)).

| Film | Style | Length | What it shows |
|---|---|---|---|
| [swiss-programme](swiss-programme/TREATMENT.md) | Swiss Motion Graphics (`swiss-motion`) | 15 s, 1920×1080, 24 fps | a grid, two rules on two spreads, snaps landing on a 120 BPM beat grid, clip reveals, a page turn, one red exception moving linearly off the grid, a knife cut |
| [first-light](first-light/TREATMENT.md) | Risograph Print (`risograph`) | 12 s, 1920×1080, 24 fps | two spot inks multiplied on warm paper, their overprint, stepped halftone tints, misregistration, grain, drawings on twos, a roller wipe, a plate lifting away |
| [shipped](shipped/TREATMENT.md) | Dark Keynote (`dark-keynote`) | 10 s, 1920×1080, 24 fps | a near-black stage with a hairline grid, raised dark surfaces, a checklist ticking on the beat with back.out(1.3), a CRT-off squash, one lime accent |
| [boot](boot/TREATMENT.md) | ASCII CRT (`ascii-crt`) | 10 s, 1920×1080, 24 fps | amber phosphor glyphs on a cell grid with glow and scanlines, power on and off, machine typing, a clear-screen cut, a push-in by grid scale |
| [morning](morning/TREATMENT.md) | Pictogram Motion (`pictogram-motion`) | 12 s, 1920×1080, 24 fps | a disc pattern in five tones of one hue, a sun disc, a figure sliding into register band by band, 900-weight titles rising out of a slot, cuts on the downbeat |

## The later capabilities

One short film per capability added after the first 23 styles, each made properly in a library style and passing
`film check`; opening-night is the score again, played by sampled instruments. They are tutorials, not round-trip
material, so they carry no `truth.json`.

| Film | Style | Length | What it shows |
|---|---|---|---|
| [quiz-night](quiz-night/TREATMENT.md) | Game Show Flat (`game-show`) | 12 s, 1920×1080, 24 fps | music first: `score.json` holds a 120 BPM grid and a cue table, `score.js` gives `cue()` and `bar()`, and every drop, pop and stamp lands on a cue; a held breath where the band stops; the cue sync check |
| [first-save](first-save/TREATMENT.md) | 16-bit Pixel RPG (`pixel-rpg`) | 10 s, 1920×1080, 24 fps | `kit/pixel.js`: a 320×180 indexed framebuffer shown ×6, dithered shading, parallax ridges, a walk on 8 fps, a dialog box typing in its 5×7 font, night falling by palette steps while the UI keeps its colours |
| [harbour-dawn](harbour-dawn/TREATMENT.md) | Watercolor Brush (`watercolor`) | 10 s, 1920×1080, 24 fps | `kit/brush.js`: washes behind brush-edge wipes, bristled strokes and ink laid in slices of time, structure first, one accent, a hand-lettered label |
| [tide-town](tide-town/TREATMENT.md) | Low-poly Isometric Island (`lowpoly-island`) | 10 s, 1920×1080, 24 fps | `kit/three.js`: flat-shaded primitives under an orthographic camera, tiles rising, houses dropping with a squash, trees popping on a 1/8 s grid, a faceted sea displaced from t (three.js is vendored on `film new` and on delivery) |
| [every-style](every-style/TREATMENT.md) | Caption News (`caption-news`) | 12.5 s, 1920×1080, 24 fps | real material: the four films above taken in with `moodreel media add` (source and licence in `media/manifest.json`), drawn by time with `kit/media.js`, captions slammed in chunks with a keyword block, source tags and footage credits; `build.sh` delivers the four films first |
| [opening-night](opening-night/TREATMENT.md) | 1930s Rubber Hose Cartoon (`rubber-hose`) | 16 s, 1920×1080 (4:3 gate), 24 fps | sampled instruments: a score of stride piano, tuba oom-pah, trumpet and horn stabs, a clarinet and timpani (`moodreel samples fetch` first), each player entering when its part does; the band stops dead for one beat and everything freezes; all 12 cues land on a move; characters on twos with a boiling line, ink constant under squash, a worn print |

Render one (needs the setup in the main README):

```bash
uv run moodreel render video examples/first-light --fps 24 --size 1280x720 --workers 3
```

```bash
uv run moodreel film check examples/first-light
```

Each film's folder holds `TREATMENT.md` (brief, structures considered, beats), `main.js`, `kit/` (the shared
primitives plus `tokens.js` and `motion.js` filled in from the style), `CREDITS` (the system faces they use; a
published film sets an OFL face instead), `build.sh` and, for the first five, `truth.json`: the values the code uses, in screen
coordinates, for the round trip. Keep `truth.json` in step when you change a film. Footage frames (`media/*/`),
vendored libraries (`kit/vendor/`) and deliverables are not committed: `sh build.sh` makes them again.
