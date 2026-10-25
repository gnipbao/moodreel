# ASCII Glitch Launch · 字符故障发布片

Information & Keynote · 信息与发布. Distilled with Moodreel on 2026-10-25; install with `python scripts/packs.py install ascii-glitch-launch`, then `moodreel film new <name> --style ascii-glitch-launch`.

| Kind · 类别 | Files | What it is |
|---|---|---|
| Rules · 规则 | `STYLE.md` | the style prompt: essence, materials, colour, type, motion, camera, sound, moves, pitfalls, engine, variation |
|  | `DECISIONS.md` | the choices the measurements could not make, approved at gate 1 |
|  | `style.json` | slug, names, size 1920x1080, 60 fps, needs: 3d, music-led |
| Evidence · 证据 | `evidence/LEDGER.md` | every number in STYLE.md with its basis (observed, derived, inferred) and source |
|  | `evidence/intake.json` | the references: kind, size, licence source, checksum (the files stay with their owner) |
|  | `evidence/measure/` (11) | frame-check, layout, motion-check-demo, motion-check-sketch, motion, palette, rhythm, shots, style, texture, type |
| Kit · 代码: the style's own | `kit/cells.js` | The cell pass, the style's core device |
| Kit · 代码: the style's own | `kit/fields.js` | The hero lights |
| Kit · 代码: the style's own | `kit/glitch.js` | the style's own core |
| Kit · 代码: the style's own | `kit/grounds.js` | Grounds and light |
| Kit · 代码: the style's own | `kit/montage.js` | The re-dressed object |
| Kit · 代码: the style's own | `kit/plane.js` | A page in perspective, and a lens focused on one line of it |
| Kit · 代码: the style's own | `kit/tracker.js` | The tracker |
| Kit · 代码: measured | `kit/tokens.js`, `kit/motion.js` | palette, type tiers, layout, texture; durations, eases, stagger, beat |
| Kit · 代码: shared | `brush.js`, `core.js`, `eases.js`, `gl.js`, `pixel.js`, `stage.js`, `text.js`, `texture.js`, `three.js` | the kit every film gets (stage, core, eases, text, texture, ...) |
| Kit · 代码: fonts | `kit/fonts/Inter.woff2`, `kit/fonts/JetBrainsMono.ttf` | with `kit/fonts/OFL.txt` |
| Demo · 演示片 | `demo/` | the demo film's source: `CREDITS`, `build.sh`, `film.json`, `index.html`, `main.js`, `music-data.js`, `poster.jpg`, `scenes-end.js`, `scenes-mid.js`, `scenes-open.js`, `score.js`, `score.json`, `sfx.json`, `sfx.mjs`, `timeline.js` |
|  | `demo.mp4` | not in the repository: rebuild with `sh demo/build.sh` (it writes `demo.mp4` beside `demo/`) |
|  | `styleframe.jpg` | the style frame approved at gate 2 (frame-check compares films with it) |
