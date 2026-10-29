# Ledger — Ink Chronicle

One reference (vid01, 83 s, 1280×720, 30 fps). Most values were measured during the eight-round remake with Moodreel's
own tools on the reference (`moodreel probe`, `review`, `camera`, `compare --motion`; out/challenge4) and confirmed by
the remake reaching them; `measure/` adds the library's standard readings. Evidence is one film: thin, and marked so.
STYLE.md keeps only the signature (user's note at gate 1); the measured specifics below are the kit's defaults and
examples, not rules a film must follow.

| value | used in | basis | source |
|---|---|---|---|
| paper #f5f2e9 (centre) | §2, §3 | observed | review-r8b ground: goose, learn, then, cards #f5f2e9–#f5f3e9 (16 of 37 windows on paper) |
| paper smooth, no fibres | §2 | observed | probe: the late paper's Laplacian 0.3, luma 243 (remake round 1) |
| night #0e0e0d | §2, §3 | observed | review-r8b ground: collapse, cannot change, useless, what now (10 windows near-black) |
| charcoal #262421 | §2, §3 | observed | review-r8b ground: wen ru #262421, three exiles #262420, moon #272421 (8 windows) |
| accent #fd5e23 (flash) | §3 | observed | probe on the full orange flash (four works, accent #ff5d23); lib.js C.orange |
| accent #f4683a (tiles) | §3 | observed | probe on the tiles' faces; review tiles accent #f97442 |
| accent #eb5925 (a defiant word) | §3 | observed | review-r5/r8b shui pa accent #eb5925 |
| accent on dark #93352b, #814d3e | §3 | observed | review-r8b accents: useless #93352b, wutai #814d3e |
| about a third of shots carry the accent | §3 | observed | review-r8b: 12 of 37 windows have an accent |
| ink #16130f | §3 | observed | probe on the paper's type; lib.js C.ink |
| type on dark #f4f2ee | §3 | observed | review-r8b ink on dark: wutai #f4f0e9, ke #f3f2e9 |
| one hue only | §3 | observed | review-r8b: every accent is an orange-red (hue 8–18°); thin (one film) |
| a blow 28–47 % of the height | §4 | observed | ink boxes: 废物 300 px (28 %), the year 330 px (31 %), 儋州 510 px (47 %) at 1080 |
| a title 14 % | §4 | observed | 乌台诗案 150 px |
| addressing lines 9–11 % | §4 | observed | 无法改变环境 100 px (9.3 %), 你会怎么办? 118 px (10.9 %) |
| a quotation 7–11 % | §4 | observed | 把一手烂牌 80 px (7.4 %), 也无风雨也无晴 108 px (10 %), 问汝平生功业 115 px (10.6 %) |
| the quiet voice 5–6.7 % | §4 | observed | 如果有一天 58 px (5.4 %), 然后 62 px, 当下好好感受 72 px (6.7 %) |
| rows 4.5 % | §4 | observed | 每天都很焦虑。 49 px, a row every 71 px |
| captions 3 %, labels 1.6 % | §4 | observed | the four works' captions 33 px; the distances 17 px |
| faces: Noto Serif SC, LXGW WenKai, IBM Plex Mono | §4 | inferred | type classes from type-lines.jpg and the remake (heavy Song, upright Kai, mono with a plain zero); DECISIONS §3 |
| reading time CJK / 4.5 + 1.5 s | §4 | derived | the library's rule (writing-style-md.md) |
| a blow holds 0.3–1.7 s | §4 | observed | 黄州 0.33 s, 惠州 0.38 s, 废物 0.44 s, the year 1.7 s |
| 30 fps on ones | §5 | observed | intake.json fps 30.0 |
| slam 1.6–2.6 times, 0.08–0.1 s | §5 | observed | motion review round 7 (motion-1…4.jpg): the year 2.6× at 10.03 s, settled by 10.07; 侧成峰 2×; places 2.2×; 废物 1.6× |
| slam full on its first frame | §5, §9 | observed | motion review: an opacity ramp halved the measured change (8 levels to 19 at 62.1 s) |
| colour split 36 px | §5 | observed | the year's red and cyan fringes at 10.03 s (5 px at 240 px wide) |
| typing every 0.05–0.25 s | §5 | observed | per-character times read at 0.1 s steps: 无法改变环境 0.05 s, 连你自己都觉得 0.07 s, 何妨吟啸且徐行 0.15–0.2 s, 问汝平生功业 0.15–0.25 s |
| fade 0.12–0.2 s, rise 0.15 em | §5 | inferred | by eye against the strips; the remake's typed() defaults that matched |
| grit gathers in 0.15 s | §5 | inferred | by eye (the scroll's grit, 莫听 at 0.25 s a character) |
| sand falls 0.9 s | §5 | inferred | by eye (16.8 s: the column of grit under the characters before) |
| shards 4600 px/s², gone in 0.6 s | §5 | derived | the reference's shards fell about 0.12 H in 0.23 s (62.62–62.85 s) and left the frame by 63.4 s |
| jumble 4–8°, 30°, over 0.3 s | §5 | observed | 60.65–60.95 s strips: the boxed line tilts about 8°, the others less; characters turned up to about 30° |
| a line flies up out in 0.1 s | §5 | observed | 侧成峰 leaves at 33.97–34.06 s |
| a step every 0.4 s | §5 | observed | rings born at 15.3, 15.7, 16.1 s |
| wings every 0.14 s | §5 | observed | the crows at 10.4–10.8 s, a beat about every four frames |
| twinkle about 12 times a second | §5 | inferred | the moon path's glints, by eye |
| shots 0.4–5 s | §6 | observed | scenes.json window lengths 0.43–5.03 s (37 windows) |
| cuts on the text's sense | §6 | observed | see MEASURE.md rhythm (cuts against beats) |
| columns a fifth of the width from the edge | §6 | observed | 问汝平生功业 at 0.207 W; 人生到处知何似 / 应似飞鸿踏雪泥 columns |
| camera moves | §6 | observed | moodreel camera: ink burst +69 %, mosaic −46 %, 也无风雨 −62 %; the moon held then −16 % (radius 0.045 to 0.036 W); the peak's height ×2.7 in 0.6 s |
| −14 LUFS | §7 | derived | the library's delivery standard |
| piano, low strings, a low drum under slams | §7 | inferred | proposal at gate 1 (DECISIONS §6) |
| grit points every 3–4 px, dots 2–4 px | §2 | inferred | the remake's matched particle moments (rounds 2 and 5) |
| floor words at half a tile by night | §2 | observed | round 8 fit: 0.035–0.04 W near the foot of the frame beside 0.1 W tiles |
| 15 % contrast floor for grey type | §9 | inferred | H.264 at caption sizes (library experience) |
| 30–120 s | §11 | inferred | the reference is 83 s; the style's use (DECISIONS §2) |
| achromatic film, one accent | §1, §3 | observed | MEASURE.md colour: neutral area 99 %, 1 chromatic colour, saturated area 1 %; the accent #f06d3d covers 0.5 % |
| paper #f4f1e9, night #16130f | §2, §3 | observed | MEASURE.md palette: #f4f1e9 62.9 %, #16130f 20.2 % (the film opens on night), mist #c9c5be 12.6 %, charcoal #3c3832 2.3 % |
| accent on dark #662b20 | §3 | observed | MEASURE.md palette 0.2 % |
| bloom on bright type and lights | §2 | observed | MEASURE.md shots read as code: bloom in 89 % of shots |
| edges fall into shadow | §2 | observed | MEASURE.md texture: vignette strong (0.52), mostly the night shots |
| crisp type | §2 | observed | MEASURE.md texture: edges crisp (0.390) |
| the slam is the commonest arrival | §1, §5 | observed | MEASURE.md motion: scale-pop leads the entrance and move vocabularies (36 of 154 moves, 20 of 73 entrances with it) |
| entrances about a third of a second, slight overshoot | §5 | observed | MEASURE.md motion: entrances 0.17–0.62 s, median 0.35 s; overshoot median 3 % |
| exits a little shorter | §5 | derived | exits median 0.27 s vs entrances 0.35 s (93 and 73 events) |
| moves brisk | §5 | observed | moves 0.13–0.33 s, median 0.22 s; overshoot in 45 %, median 10 % |
| typing intervals | §5 | observed | MEASURE.md staggers per letter: 0.0333, 0.0667, 0.0681, 0.1523 s |
| counters | §8 | observed | 7 counters, 0.22–0.51 s, e.g. 1299→1748 (km) |
| 3D camera in a third of the shots | §2, §6 | observed | MEASURE.md shots read as code: 3d camera 32 %, surges 68 %, pull out 11 %, pan 11 % |
| centred, full-bleed | §6 | observed | MEASURE.md layout: centroid [0.498, 0.497], symmetry 1.0, content to the edges |
| dissolves allowed | §6 | observed | MEASURE.md motion: 16 shots, 13 cuts, 3 dissolves |
| the edit ignores the beat | §6 | observed | MEASURE.md rhythm: 152 BPM (clarity 1.0); cuts on a beat 0.19 (chance 0.20), arrivals 0.15 (chance 0.20) |
| type tiers (the measure's 13 lines) | §4 | observed | MEASURE.md type: 12.4 %, 6.1 %, 4.9 %, 2.6 %, 1.7 % of the height (giant single words are not read as lines) |
| style frame passes at CSD 0.45 | gate 2 | observed | MEASURE.md style embedding: 4 pictures agree at 0.48–0.552 |
