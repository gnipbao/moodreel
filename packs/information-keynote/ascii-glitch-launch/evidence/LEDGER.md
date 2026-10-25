# Ledger — ASCII Glitch Launch

One reference (vid01, 15.8 s). "remake" = measured from the reference during the shot-by-shot remake
(`out/challenge2`, five rounds): per-frame brightness and cut frames, flat-patch noise, frame strips, and from round 3
`moodreel probe` (light, scan, cells, type, turn).

| value | used in | basis | source |
|---|---|---|---|
| ground #070607, 48 % of the area | §3 | observed | measure/palette.json colours[0] |
| neutral area 54 %, saturated area 11 % | §3 | observed | palette.json structure |
| accent #662c83 | §3 | observed | palette.json roles.accent |
| pink #e2338f on beam edges and neon | §2, §3 | inferred | remake: the beam's edge and the neon tube read by eye and matched in colour |
| type near-black #1b1b1b on light grounds | §3 | observed | remake: ink of the typed year, sampled |
| studio 230 across the middle, 173 in the corners (16 x 9 light map) | §2 | observed | remake round 5: `moodreel probe` light at 2.95 s, the line removed; kit `GLITCH.studio` |
| grain about 5 levels on light grounds | §2 | observed | remake: flat-patch high-pass std 4.7–5.7 (0.2 s, 15.0 s) |
| grain holds still | §2, §9 | observed | remake round 3: median frame-to-frame change 0.00 in every still region; ours 0.67 cost flow |
| scan lines: a 4 px row rhythm, 10 levels on light cards, 5.5 on the studio, 1.7 on the end card | §2 | observed | remake round 5: `probe` scan on all 20 scenes (texture.json read 2.67 px in 25 % of pictures at its sampling) |
| screen-door dither every 14 px, about ±8 levels | §2 | observed | remake: dark grounds at 8.5 s and 9.3 s (values 14–30 around 19, period 12–16 px); texture.json halftone period 7.73 px at 28.9° in 25 % |
| cells 20–28 px at 1080p | §2 | observed | remake: ASCII fields at 1.2 s and 3.5 s, cells counted |
| cells 16 px on the beam, 12 px on the dim eye and end card, 10 px on a glyph screen; grid from the frame's corner | §2 | observed | remake rounds 3–4: `probe` cells period and phase |
| the rings ramp (ring, slash, cross, dot in a box) and the lines ramp (dot, slash, cross) | §2 | observed | remake rounds 3–4: crops at 9.0 s, 11.3 s, 6.22 s, 14.8 s |
| glyph screens for 6 frames (6.167–6.267 s, 13.167–13.267 s) and under "lives on" | §2, §6 | observed | remake round 4: a region's mean frame by frame |
| a page's prompt grows 1.25–1.33x along its line, baseline slope 0.049, vanishing point near (-5000, 260) | §2 | derived | remake round 4: glyph heights at both ends on all eight looks |
| focus falls off below the line read | §2 | observed | remake round 4: the card's lower half soft, the heading sharp, on six of eight looks |
| lens ellipse, the far corners at half the light; a light card's plateau 237–242 | §2 | derived | remake round 5: reference over a remake without it, blurred, fitted per look (rms 0.04–0.09) |
| cards inside a cylinder, camera dollying 0.9 → 0.23 radii behind the axis, turning 0.43 rad, ease-out | §2, §5 | derived | remake round 3: 14 card centres and widths at 3.7 s and 4.4 s, least squares, 3 px rms |
| tracker red #c3263a, green #3ddc6a, 2 px boxes, 10 px dashes | §2 | inferred | remake: frames at 0.6–1.0 s sampled and matched |
| labels 18–30 px mono | §2 | observed | remake: label heights at 0.62 s; type.json tiers 1.7 % and 2.8 % |
| hero lines 15–20 % of the height (tiers 15.1 %, 20.1 %), phrases 8.9 %, labels 1.7–2.8 % | §4 | observed | type.json tiers |
| Inter and JetBrains Mono (OFL) | §4 | inferred | DECISIONS.md 3; type-lines.jpg: neutral grotesk, geometric mono |
| weights: phrases and prompt 500, words 600, year 550, "starts with" 800, dot-matrix mono 250 at 610 px, 400 px a glyph | §4 | observed | remake round 4: `probe --region` stroke and box on each line |
| typing about 36 characters a second (prompt), up to 150 (line) | §4 | observed | remake: prompt 1.33–2.2 s for 33 characters; line complete in 0.18 s at 2.87 s |
| 60 fps on ones | §5 | observed | intake.json fps 60; motion.json stepping 1 |
| slot 5–6 frames (0.083–0.1 s) | §1, §5, §6 | observed | remake: cut frames of the prompt (16 slots), icons (10), posts (11) |
| entrances 0.08–0.33 s, ease-out | §5 | observed | motion.json entrance range (15 events; class out on 1: weak) |
| exits 0.05–0.21 s | §5 | observed | motion.json exit range (10 events) |
| moves 0.09–0.29 s, half overshooting about 4 %, bezier(0.433, 1.198, 1.0, 0.927) | §5 | observed | motion.json move (44 events; curve shared by 4 tweens) |
| glitches 2–12 frames | §5 | observed | remake: ASCII 1.10–1.28 s (11 f), mosaic 5.33–5.45 s (7 f), inverted flashes 3–6 f |
| 120 BPM | §5, §7 | observed | rhythm.json 120.2 BPM; moodreel music 119.98 |
| punches on 20 % of kicks, flashes on 33 % of beats | §5 | observed | moodreel sync on the reference (chance 5 % and 7 %) |
| counters 0.17–0.32 s | §5 | observed | motion.json counters (3 events) |
| shots median 0.10 s, 68 in 15.8 s; 65 cuts, 2 dissolves | §6 | observed | motion.json shots |
| inverted flash 2–6 frames | §6 | observed | remake: 3.47 s, 6.567–6.667 s (6 f), 6.767–6.817 s (3 f), 10.33–10.40 s |
| end card: the mark turns 28.3° → 22.3° from vertical (smoothstep 13.7–15.35 s), 316 → 330 px long | §5, §6 | observed | remake round 3: the slash's angle and length every 0.1 s |
| the ring turns about 1 rad/s about a pivot 180 px above its outline's middle (blue: 1.06 rad/s) | §5 | observed | remake round 5: `probe` turn, 3 x 3 flow grid at 10.0–10.5 s |
| ≥ 96 px from the edges | §6 | inferred | the library's title-safe default; type in the reference keeps it |
| phrases held 0.5–1.8 s, median about 0.7 s | §4 | observed | remake: the reference's scene table (0.53, 1.83, 0.63, 0.67, 0.65, 0.73, 0.5, 0.88, 0.9, 1.15, 0.5, 1.45 s) |
| a silent film holds a line ≥ CJK / 4.5 + other / 15 + 1.5 s | §4 | inferred | the library's reading-time rule, for films read without sound |
| cross dither under 4 % disappears, above 15 % reads as pattern | §9 | inferred | remake: 5 % was invisible after encoding; 11 % matched |
| 5 frames minimum, 8 frames maximum a slot | §9 | inferred | the reference's slots are 5–6 frames; by eye at 3–4 and 9–10 frames |
| a 12 px cell grid on a 320 px check: a 1 px shift changes its texture score by half | §9 | observed | remake round 4: `moodreel compare` reads 320 x 180; the "lives on" window's detail went 1.2 → 2.1 with the grid moved 1 px |
