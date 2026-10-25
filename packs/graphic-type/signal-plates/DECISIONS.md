# Decisions — Signal Plates (gate 1)

Choices the measurements can't make. Each: the choice, the alternatives, the evidence, the cost. Approved by the user
at gate 1 (2026-10-25).

## 1. Name

- **Choice**: Signal Plates · 信号图版, slug `signal-plates`. It names the two things a frame shows: the hazard orange
  (the signal) and the treatise's plates. It names neither the song nor the film it was learned from.
- **Alternatives**: Doom Treatise · 末日图志 (closer to the source's tone, ties the style to one subject); Hazard Lyric
  · 警示歌词 (says what it is for, loses the plates).
- **Cost**: none.

## 2. What films it is for

- **Choice**: music and lyric videos, and short films cut to a song: a launch teaser on a track, a manifesto, an
  explainer set to music. The style needs a song with a pulse; without one its clock is gone (§7).
- **Alternative**: also unscored explainers on a click track. Possible (the kit counts in beats from any grid), but
  the style would lose its strongest trait.
- **Evidence**: ANALYSIS trait 3; the remake (rhythm was what made it feel right).

## 3. Typefaces

- **Choice**: ship the source's own OFL fonts from the local clone, no download: Archivo variable (width and weight,
  658 KB), Cormorant Garamond Italic variable (716 KB), IBM Plex Mono Regular, Medium and Bold (410 KB); about 1.8 MB
  in `kit/fonts/` with each family's OFL text and copyright line, listed in CREDITS.
- **Alternatives**: (a) system fonts (Helvetica Neue, Menlo, Georgia), what the remake used: nothing to ship, but no
  width axis, macOS-only, and not licence-free to ship; (b) fetch the same families from Google Fonts: needs a download.
- **Evidence**: TREATMENT "Typography"; README "Credits" (SIL OFL); `app/public/fonts/src/OFL.txt`.
- **Cost**: Canvas 2D sets width by keyword, so the grotesk's width moves in the axis's seven steps (62.5–125 %);
  between steps the kit scales horizontally. Single-stroke plotter fonts are left out of the first kit (decision 6).

## 4. How the materials are built

- **Evidence** (MEASURE.md "Shots read as code", 42 shots; docs/research/VISION-TO-CODE.md): bloom in 95 % of shots,
  movement in surges in 69 %, line-heavy pictures (10^4-10^5 hairlines) in 45 %, engraving hatch in 31 %, a camera moving
  through a 3D scene in 29 %. The source draws these on the GPU; drawn as 2D canvas strokes from stills, the same film
  came out darker, more saturated, sparser and slower, and scored 0.53 against the reference instead of 0.94.
- **Choice**: build the style on the GPU kit that now exists. Finish and clock as before (`kit/gl.js` post: bloom 0.55
  over 0.85, halation 0.25, fringe 1.2 px; `kit/music.js`; motion blur from film.json). Materials: hairline fields with
  `kit/gl.js` lines; engraving with `hatch`/`engrave`, following a surface where there is one (a ray-marched body in a
  `kit/gl.js` pass); 3D plates with `kit/three.js` and type projected through the camera; type broken into strokes or
  particles with `kit/outline.js`. Idioms in the style's kit: the **prompt field**, the **paper form**, an **engraved
  body** (signed distances, smooth union, hatch along the surface) and a **line field** (flow lines in 3D).
- **Alternative**: the three 2D idioms proposed first (prompt field, paper form, flat hatch), every GPU look per film.
  Lighter, but the measurements say half the shots need what 2D can't draw.
- **Cost**: four idiom modules on top of the GPU kit, each with a test frame; the demo renders slower (GPU plates ran
  at about 9 frames a second with 8 sub-frames).

## 5. Sound for the demo

- **Choice**: an original 20–30 s track from `moodreel score` (synth kit at a pop tempo, a lead line), with the demo's
  words placed on the lead's notes, whose times the score knows exactly; `moodreel music` analyses it like any song;
  synthesized foley in `sfx.json`. The pack carries no third-party audio.
- **Alternatives**: (a) 25 s of the reference's song: the real thing, but it is not ours to ship in a style pack (its
  rights stay with its makers); (b) a system TTS voice speaking the words on the beat: draft quality.
- **Evidence**: §7; the song's licence (CREDITS of the remake).
- **Cost**: no singer, so "the words as sung" are the lead's notes; the sync rules are exercised all the same.

## 6. Left out of the first version

- **Single-stroke lettering** (the spark writing a word): needs the EMS/Hershey SVG fonts and a stroke renderer.
  Proposed for later; the demo writes with the spark as a hairline path instead.
- **3D plates**: possible with `kit/three.js`; not needed to show the style.

## 7. The demo (15–30 s, at gate 3)

- **Choice**: "Battery Low": a phone's battery falling from 20 % to 1 % is the rising (here falling) value staged in
  every plate; the plea "save your work" typed as tokens; a paper inversion (a power-saving settings form, stamped);
  the hook "SAVE IT" slammed and escalating; the charging cable as the spark's line; it ends on the last beat as the
  screen cuts to black. Far from the reference's subject, and every §8 move but the spark's writing appears once.
- **Alternatives**: a storm warning (a barometer falling, sirens as stamps); a deadline (a clock counting down to a
  launch).
- **Cost**: the demo is 1920×1080, 60 fps, motion-blurred; at the remake's speed (156.7 s in 4 min 20 s) 25 s
  renders in under a minute.
