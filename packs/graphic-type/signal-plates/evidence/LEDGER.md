# Ledger — Signal Plates

One reference, `refs/vid01.mp4` (1280×720, 60 fps, 156.711 s). Bases: **observed** (read off the pictures by
`moodreel measure`, or by a stated pass over the video), **derived** (computed from observed values), **source** (read
from the reference's public source, mexicat/pdoom-video at fa164b7, MIT: file named), **inferred** (judgement or the
user's choice; what was looked at is said). Evidence from one film is thin by nature; rows that rest on few events say
so.

## Colour

| value | used in | basis | source |
|---|---|---|---|
| ground #0e0c0c, 84.1 % of the area | §3, ANALYSIS | observed | palette.json colours[0] (area 0.8412) |
| accent #b95122 | §3 | observed | palette.json: the one saturated colour (chroma 60.8, area 0.3 %) |
| saturated area about 1 %, neutral 92 % | §1, §3 | observed | MEASURE.md "Colour" |
| one hue family (orange) | §1, §3 | observed + source | MEASURE.md "1 hue families"; TREATMENT "Palette": "no other hues anywhere" |
| ink #0A0A0B, panel #151517, graphite #5E5B57, ash #9C978F, bone #EEE9DF | §3, tokens PALETTE | source | app/src/engine/palette.ts; TREATMENT "Palette" |
| signal #FF4D12, ember #FF8A3D, blood #C21D0B | §3, tokens PALETTE | source | palette.ts: the spark, P(doom), the sung word; hot cores; deep shadows |
| acid #D8FF3C, one moment of about two seconds | §3 | source | TREATMENT: "owned by one moment (the shrooms, ~2 s)" |
| orange marks, does not fill | §3, §9 | derived | saturated area 1 % with orange on the spark, words and number in every section (refs-sheet.jpg) |
| only orange glows; bloom threshold 0.85 | §2, §3, §9 | source | TREATMENT "Only signal/ember should exceed ~0.85 linear"; post.ts bloomThreshold 0.85 |
| paper plates 9.1 % of the running time, 11 runs | §2, ANALYSIS | observed | mean luma > 128 at 10 fps over the whole video (1567 frames) |
| unsung words at 30–40 % bone, up to 0.4 s early | §4 | source | TREATMENT "Karaoke rules" |
| other warning hues (sodium amber, hazard red) | §3, §11 | inferred | one film's palette is one example; the logic (one family, reserved) is what holds |

## Surface and light

| value | used in | basis | source |
|---|---|---|---|
| vignette strong (0.67 measured; 0.35 in the recipe) | §2, tokens POST | observed + source | texture.json vignette 0.67; post.ts vignette 0.35 (strength in its own units) |
| mottle blotchy, edges crisp | §2 | observed | texture.json mottle 3.35 "blotchy", sharpness 0.395 "crisp" |
| grain 0.055 (not readable in the reference: 0.34 levels) | §2, tokens POST | source | post.ts grain 0.055; texture.json grain 0.34 levels "none" after compression |
| bloom 0.55, radius 0.75, knee 0.5 | tokens POST | source | post.ts |
| halation 0.25 on dark plates, none on paper | §2, §9 | source + inferred | post.ts halation 0.25; paper rule by eye from the remake (halos on light frames) |
| chromatic fringe 1.2 px at rest, more on hits | §2 | source | post.ts ca 1.2; scenes add `2 * hit` (ascent.ts, hook.ts) |
| hairlines 1–2 px at 1080p | §2 | source | ENGINE.md: "a 1.2 px hairline", LineBatch hairline floor |
| motion blur: 8 sub-frames, shutter 0.2 of a frame | §2, §5, film.json | source + derived | ENGINE.md "--shutter 0.2"; 8 sub-frames from the remake (v5 matched the reference's streaks) |
| no gradient sky (flat ground, panels one step up) | §2 | observed + source | palette.json: ground 84 % in one colour; palette.ts ink, ink2 |
| idioms per plate (engraving, scope, form, blueprint, terminal, guilloché, 3D room) | §1, §2 | source + observed | TREATMENT "The idea"; refs-sheet.jpg |

## Type and layout

| value | used in | basis | source |
|---|---|---|---|
| Archivo, widths 62–125, weights 300–900, OFL | §4, tokens TYPE.display | source | TREATMENT "Typography"; app/public/fonts/src/OFL.txt |
| IBM Plex Mono, Cormorant Garamond italic, single-stroke fonts; OFL / public domain | §4, tokens TYPE | source | TREATMENT "Typography"; README "Credits" |
| hooks 15.8–19.7 % of the frame height | §4, tokens TYPE.hook | observed | type.json tiers 19.7 % ×1, 15.8 % ×3 |
| lyric lines 4.3–7.1 % | §4, tokens TYPE.line | observed | type.json tiers 7.1 % ×6, 4.3 % ×2 |
| notes 0.8–3.1 % | §4, tokens TYPE.note | observed | type.json tiers 3.1 % ×3, 1.3 % ×3, 0.8 % ×5 |
| margins L 8 %, R 30 %; left alignment | §4 | observed | layout.json medians; dominant alignment left |
| content covers 13 % | §4 | observed | layout.json coverage 0.13 |
| lyric ≥ 96 px from the edges | §4, §6 | source | TREATMENT "Karaoke rules": title-safe ≥ 96 px |
| a word lights at its sung start; never ahead of the voice | §4 | source + observed | TREATMENT "Karaoke rules"; remake: hand times 60–130 ms off |
| reading time ≥ CJK / 4.5 + other / 15 + 1.5 s | §4 | inferred | Moodreel's reading rule for non-sung text |
| no haloed type; typographic punctuation; kerned | §4 | source | TREATMENT "Craft (revision 5)"; ENGINE.md "Typography" |

## Motion

| value | used in | basis | source |
|---|---|---|---|
| 60 fps on ones | §5 | observed | intake: 60.0 fps; motion.json stepping on ones (share 0.86–0.92) |
| tempo 132.007 BPM, beat 0.4545 s | ANALYSIS, §5 (as "the reference's tempo") | source | data/audio.json bpm, beat_period |
| shot about a beat: median 0.45 s | §5, §6 | observed + derived | MEASURE.md shots median 0.45 s = 0.99 beat |
| hold half a beat: median 0.23 s | §5 | observed + derived | MEASURE.md median hold 0.23 s = 0.51 beat |
| stagger an eighth note: 0.231 s | §5 | observed + derived | MEASURE.md stagger 3 × 0.231 s = 0.51 beat (3 events: weak) |
| loops one to two beats: 0.45–1.02 s | §5 | observed | MEASURE.md loops (4 loops: weak) |
| moves on the beat grid: 50 % within 2 frames of a beat (chance 15 %), 67 % on the half-beat grid (chance 29 %) | §1, §5, ANALYSIS | derived | 60 scene changes (ffmpeg scene > 0.32 on refs/vid01.mp4) against data/audio.json beats |
| section cuts on the beat at or before the line's first word | §6 | source | app/src/timeline.ts `cut()` |
| entrances 0.24–0.69 s, ease-out, overshoot in 48 % (median 5 %) | §5, tokens MOTION.enter | observed | MEASURE.md entrances (213) |
| exits 0.12–0.54 s, median 0.30 s | §5, tokens MOTION.exit | observed | MEASURE.md exits (164) |
| moves 0.09–0.33 s, overshoot in 64 % (median 6 %) | §5, tokens MOTION.move | observed | MEASURE.md moves (711) |
| counters 0.07–0.32 s, mono | §5 | observed | MEASURE.md counters (71) |
| an element's punch 2–4 % on a kick, in a few plates | §5 | source | scenes `0.02 * hit` (dense-askew.ts, ascent.ts), `0.04 * hit` (hook.ts) |
| kick shake 1.7 px read at 640 wide (3 px at 1080p in the kit: 5 px read as 2.76 px in the demo, with the beat's own camera steps), +17 ms, half-life 0.067 s; snare 0.85 of it; a word's motion burst +33 ms; no frame-wide kick zoom | §5 | measured | `moodreel sync` on the reference: kick → shake +1.65 px, half-life 0.067 s (z 7.4); snare → shake +1.44 px (z 4.3); word → motion +33 ms (z 8.0); kick → zoom z 1.4 (none). Validated against the source's own post settings (docs/research/VISION-TO-CODE.md §5) |
| the glow breathes up on a hit (exposure +12 % on a kick), harder on a downbeat | §5 | measured | `moodreel sync` on the reference: kick → flash +0.88 levels (z 6.2), downbeat → flash +1.55 levels (z 5.1) |
| beat clock: moves surge after each beat | §5, §6 | source | TREATMENT "Tone": camera moves ease into downbeats; kit/music.js `ct` |
| letter pop from 1.2 over 0.16 s, outExpo | §5 | source | kit/music.js `pop` (after the source's letter pop) |
| sparks: about 34, radius 2.3 px, up to 432.1 px/s | §5 | observed | MEASURE.md particles (one shot: weak) |
| no floaty screensaver motion; hold, then snap | §5 | source | TREATMENT "Tone" |
| transitions: 48 cuts, 5 dissolves, 1 dip | §6 | observed | MEASURE.md shots |
| slam: 14 % over 0.16 s, creep 3.5 % a second, shake 7–26 px with a 50 ms half-life | §8 | source | app/src/scenes/hook.ts `slam(t, t0, amt = 0.14, dur = 0.16)`, `1 + 0.035 * …`, shake `[0, 7, 13, 0, 20]` and `[0, 10, 16, 0, 26]`, `pulse(…, 0.05)` |
| shake keyed to the frame index | §5, §9 | source | ENGINE.md "Motion blur and sampling": `frameIdx(t)` |
| word times read off a contact sheet 60–130 ms off | §9 | observed | remake v1–v4 against data/lyrics.json (median 66 ms) |
| hand timing halves the motion energy | §9 | observed | remake v3 vs reference: motion energy 0.5×, onset hits 0.43 vs 0.66 |

## Sound

| value | used in | basis | source |
|---|---|---|---|
| a song with a pulse and a voice, electronic pop | §7 | observed + inferred | the reference's song (sung electropop, 4/4 backbeat: data/audio.json); the rest a proposal (gate 1) |
| synthesized foley on picture events | §7 | inferred | the remake's 334 cues (sfx.json): slams, keys, crackle, stamps, tears, booms, ticks, swishes |
| effects 2–11 dB under the song | §7, §9 | observed | remake mix measured around each kind of cue |
| loudness −14 LUFS | §7 | inferred | Moodreel's delivery standard |
| a heavy master, about 38 Mbit/s | §9 | observed | remake master: 1080p60, grain + 8-sample blur, 38.6 Mbit/s |

## Engine example

| value | used in | basis | source |
|---|---|---|---|
| example price at 200 px, placed at 160, 620 | §10 | inferred | an example only, left-weighted per §4 |

## Shots read as code

| value | used in | basis | source |
|---|---|---|---|
| hairline fields in about 45 % of shots, engraving hatch 31 %, 3D scenes 29 % | §2, DECISIONS 4 | observed | measure/shots.json pooled techniques (42 shots, `moodreel dossier`; hints calibrated against the source: hatching 4/9 found, 0/13 false; 3D 6/10, 1/12) |
| motion in surges in 69 % of shots | §5 | observed | measure/shots.json techniques.surges |
| median speed about 213 px/s at 1920 wide | §5 | observed | measure/shots.json speed 212.9 |
| bloom in 95 % of shots, glow 0.42 | §2, DECISIONS 4 | observed | measure/shots.json techniques.bloom, finish.glow |
| line 4.6 % of the frame, 3.7 px wide at 1920 (a 720p reference: hairlines read wider) | §2 | observed | measure/shots.json linework |
| saturated area 2.9 % per shot (median) | §3 | observed | measure/shots.json colour.saturated |
| stills-built remake: luma 0.82x, accent 1.25x, line 0.79x, glow 0.63x, speed 0.63x | DECISIONS 4 | observed | docs/research/VISION-TO-CODE.md (46 shots) |
