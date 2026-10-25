# Signal Plates — Style Prompt

Signal Plates · 信号图版

> A music film as plates from a deadpan illustrated treatise: warm near-black plates, one hazard orange, a lyric that
> slams into each plate as it is sung, and a picture that moves on the song's beat.
> **References (grammar only):** Swiss typographic posters (asymmetry, hairlines, small notes beside big type);
> 19th-century scientific plates (engraving hatch, captions, the straight face); lab instruments and terminals (mono
> readouts, scope traces, typed input); kinetic-type music videos (the word as the image, cut to the beat).

## 1. Essence, and what it is not

- **Near-black, one orange.** A warm near-black ground fills the frame; saturated colour is about 1 % of the area: the
  spark, the sung word, the rising value.
- **The lyric is the image.** Sung words, huge, in a tight grotesk, left-weighted, built into the plate's idiom (typed,
  stamped, riding a curve, written by a pen), never a caption band.
- **Everything counts in beats.** Cuts, slams and camera surges land on the song's grid; a shot lasts about a beat.
- **Many idioms, one finish.** Sections change instrument (engraving, scope, paperwork, blueprint, terminal,
  guilloché, a 3D room) under one palette, one type system, one finish.
- **A through-line object**, a spark dragging its line or a value that keeps rising, crosses every plate.

Not Dark Tech Keynote (no product UI, no cool neutrals; slams, not glides). Not Swiss Motion (black ground, filmic
finish, type that lands with weight). Not ASCII/CRT or a hologram HUD (no scanlines, no phosphor green or cyan; mono annotates).

## 2. Materials & rendering

- **The plate**: flat warm near-black, panels one step lighter, no gradient sky. Some plates invert to bone paper with
  ink lines (forms, blueprints, charts), about 9.1 % of the running time in short runs: a light/dark rhythm.
- **Marks**: hairlines (1–2 px at 1080p), engraving hatch, single-stroke plotter lettering. Edges crisp.
- **One idiom per plate**, procedural, in world space, moving with the camera, drawn on the GPU: in the reference about
  45 % of shots are hairline fields, 31 % engraving hatch, 29 % 3D scenes with a moving camera.
- **Light**: only orange glows (bloom over a 0.85 threshold); bone type stays crisp. Halation 0.25 on dark plates,
  none on paper; a chromatic fringe of about 1.2 px, more on hits.
- **Finish, once per frame after motion blur**: grain seeded by the frame, a strong vignette, the fringe, the glow;
  blotchy low mottle in the dark. Motion blur: 8 or more sub-frames over a shutter of 0.2 of a frame.

## 3. Colour logic

- One warm neutral ladder, ink to bone, and **one hue family**: an orange with a hotter core and a deeper shadow.
- Orange marks, it does not fill: the spark and its line, the sung word, the rising value, one highlight per plate.
- Values: ground darkest; graphite for structure and unsung words; ash for notes; bone for what is read. Paper plates
  flip the ladder; orange stays. Only orange passes the glow threshold.
- A second accent may own one short moment (the reference: an acid yellow-green for about two seconds), then is gone.
- Example palette (the reference's): ink #0A0A0B, panel #151517, graphite #5E5B57, ash #9C978F, bone #EEE9DF,
  signal #FF4D12, ember #FF8A3D, blood #C21D0B, one-moment acid #D8FF3C (measured after compression: ground #0e0c0c,
  accent #b95122). Another film may take another warning hue (sodium amber, hazard red), keeping one family.

## 4. Type & subtitles

- **The voice**: a width-axis grotesk (Archivo, OFL: widths 62–125, weights 300–900). Stretch on a held note,
  condense under pressure.
- **The machine**: IBM Plex Mono (OFL) for tokens, labels, readouts, forms, footnotes.
- **The prophetic register**, rare: Cormorant Garamond italic (OFL). **Written words**: single-stroke plotter fonts.
- Sizes as a share of the frame height: hooks 15.8–19.7 %, lyric lines 4.3–7.1 %, notes 0.8–3.1 %.
- Layout: Swiss grid, asymmetric, left-aligned; big type hugs one side (measured margins L 8 %, R 30 %); content covers
  about 13 % of the frame. Lyric text ≥ 96 px from the edges at 1080p.
- **Subtitles are the plate.** A word lights at its sung start and completes by its end; it may show dim (30–40 %
  bone) up to 0.4 s early, but lighting never runs ahead of the voice.
- Non-sung text holds ≥ CJK chars / 4.5 + other chars / 15 + 1.5 s. Kerned, typographic punctuation, no haloed type.

## 5. Motion quality

- **60 fps on ones, motion-blurred**; shake and flicker keyed to the frame index.
- **The beat is the clock.** Moves start and land on the grid. A shot runs about a beat (0.45 s at the reference's
  tempo), a hold half a beat (0.23 s), staggers step an eighth note (0.231 s), loops last one to two beats
  (0.45–1.02 s). Count in beats; at another tempo the numbers scale.
- **Entrances** 0.24–0.69 s, ease-out, half overshooting about 5 %. **Exits** faster, 0.12–0.54 s. **Moves** short,
  0.09–0.33 s, two thirds overshooting about 6 %.
- **Hits**: a kick shakes the frame (about 1.7 px as read at 640 wide; 3 px at 1080p), peaking a frame after it and dying
  with a 0.067 s half-life, widens the fringe and lifts the exposure a little (the glow breathes); a snare at 0.85 of
  that, a downbeat harder. A sung word brings a burst of motion 33 ms
  after it. Some plates also punch their own element 2–4 % on a kick (the hook, a packed slab); the frame itself does
  not zoom on every kick (the beat-sync fingerprint finds none, and adding one was the stills-built remake's clearest
  fault). Camera moves surge after each beat, then ease (69 % of shots move in surges; median speed about 213 px/s at
  1920 wide).
- **Letters** pop in from 1.2× over 0.16 s, no bounce. **Counters** roll fast (0.07–0.32 s), in mono.
- **Sparks**: a few dozen particles (radius about 2.3 px), fast (up to 432.1 px/s), short-lived.
- Nothing drifts aimlessly, no floaty screensaver motion: between hits things hold, then snap.

## 6. Camera grammar

Shots are short; 48 of the 54 measured transitions are cuts (5 dissolves, 1 dip). A section cuts on the beat at or
before its line's first word, never after it.

| Move | What it expresses | Can serve |
|---|---|---|
| Hard cut on the beat | the song turning a page | a new line; a new idea; a punchline |
| Slam push with shake | impact, insistence | a key word; a number; a refusal |
| Beat-clock creep | pressure building | a held note; a list; an escalation |
| Kick shake | the body of the song | any held frame under drums |
| Whip pan, motion-blurred | a jump between ideas | a change of plate; a montage |
| Inversion to paper | a change of register | a form; a chart; a definition |
| Follow the spark | a thread through time | a process; a trajectory; a fuse |
| Locked frame | deadpan, reading | a footnote; a joke |

Title-safe ≥ 96 px; left-weighted asymmetry. Cuts by default; a dissolve or dip marks a change of time; a flash or
inversion lands on a hit.

## 7. Sound palette

- A song with a steady pulse and a voice (electronic pop, four-on-the-floor or backbeat); the picture reads its data:
  beats, bars, drum hits, the words as sung.
- Synthesized, dry, percussive foley on the picture's events: a slam per hook word, a key click per letter, crackle
  for the spark, stamps, a paper tear, sub booms, ticks for counters, swishes for whips. Panned a little, a short room.
- The song leads; effects sit 2–11 dB under it. Loudness −14 LUFS. On a break the picture holds and effects stop.
- Voice: the singer; a spoken line only where the song leaves room.

## 8. Native moves

- **The slam.** Each sung word lands 14 % big, settles over 0.16 s on an exponential ease, creeps while held, shakes
  7–26 px with a 50 ms half-life. *Fits:* a manifesto; three promises; a chant; a countdown.
- **Typed as tokens.** A plea typed as sung, each token with a tiny bar chart of alternatives; Enter launches the next
  section. *Fits:* a support chat; a search history; a confession.
- **The rising value, in-world.** One number climbs whenever the lyric says so, shown in each plate's idiom (a contour
  label, a scope readout, a form field), then full screen. *Fits:* a price; a temperature; a battery level.
- **The spark and its line.** An orange point dragging a hairline writes a word, draws a curve, becomes a chart, a
  fuse, then detonates. *Fits:* a company's history; a deadline; a signal crossing a network.
- **Inversion on the beat.** A flip to bone paper for a bureaucratic or technical aside, and back. *Fits:* a contract;
  a spec sheet; a footnote.
- **The escalating hook.** The refrain returns as one slam whose look grows each time. *Fits:* a chorus; a running gag;
  a list that grows.

## 9. Pitfalls of the medium

- Word times read off a contact sheet are 60–130 ms off the voice: take them from the song's aligned data.
- Smooth multi-second eases and hand timing halve the motion energy: drive moves from beats and hits.
- Bloom on bone type halos it: threshold 0.85; no halation or glow on paper.
- Shake keyed to continuous time double-exposes under motion blur: key it to the frame index.
- Orange as a fill stops being a signal. Effects louder than the voice bury the lyric.
- Grain and motion blur at 60 fps make a heavy master (about 38 Mbit/s): also deliver a lighter copy.

## 10. Engine

- `kit/music.js`: `music(AUDIO, LYRICS)`: `beatAt`, `hit(kind, t)`, the beat clock `ct`, `line`, `sung`, `letters`,
  `slams(starts)`; `pop(age)`. Data: `moodreel music <song> --lyrics words.json --out <film>/music-data.js`.
- `kit/gl.js`: shader passes, GPU hairlines, `hatch`/`engrave`, the film post; `kit/three.js` for 3D plates;
  `kit/outline.js` for type as strokes. `kit/stage.js` (`finish`, `window.MOTION_BLUR`); film.json `"motion_blur"`;
  `sfx.json` for effects. `kit/tokens.js`: palette, type tiers, layout, the finish (`FINISH`).
- The style's own modules: `kit/signal.js` (the fonts in `kit/fonts`, OFL: `faces()` in `prepare`; `voice`, `machine`,
  `prophet`; `karaoke` lights a word as it is sung; `ticks`; `plate()`: a GPU frame with a type layer and a hot layer,
  and `end()` with the finish, no glow or fringe on paper); the idioms `kit/engraved.js` (a ray-marched body engraved
  with contour lines that widen in the light, its own glow), `kit/linefield.js` (thousands of hairlines through a curl
  flow, wound round or drawn into a point), `kit/prompt.js` (a plea typed as tokens with their alternatives) and
  `kit/form.js` (bone paper, ruled fields typed as sung, a stamp on the hit). Under motion blur, put grain in finish().
- Lines that fill a dark ground read as grain to the eye and to frame-check when they are 1 px and bright: keep a
  background field soft (2 px, about 20 % alpha) and the hairlines for the subject.
- Not in the demo, a price that steps up every bar and punches on kicks:

```js
const s = 1 + 0.03 * M.hit('kick', t), p = (19.9 + 3.1 * Math.floor(M.barAt(t))).toFixed(2);
g.setTransform(s, 0, 0, s, 160, 620); g.fillStyle = PALETTE.signal; g.font = `800 200px ${TYPE.display}`;
g.fillText(`$${p}`, 0, 0);
```

## 11. Variation space

Each film decides the song and tempo, the plates and their idioms, the through-line object, the rising value, how often
paper appears, the hue within one warning family, the HUD, the opening and the ending. Unseen here and open: a vertical
frame, a mostly-paper film, a spoken break, more 3D plates, dissolves as structure, a second singer as a second voice.

- **Structures**: a list song, one plate per item, the hook between; one long take following the spark through one
  world, cutting only on the hook; call and response, the machine (mono, paper) against the voice (grotesk, dark).
- **Openings**: a blinking cursor, the first word typed on the first syllable; a form stamped on the first downbeat; a
  flat scope trace that jumps with the first kick.
- **Endings**: the value overflows into a symbol, cut to black on the last beat; the plate prints out and tears;
  everything stops on the last word and only the spark's line stays, fading over two bars.

---

How our demo was made (story, shots, score, end card, build): [DEMO.md](DEMO.md). Read it after your treatment exists.
