# Signal Plates · 信号图版

Graphic & Type · 图形与排版. Distilled with Moodreel on 2026-10-25; install with `python scripts/packs.py install signal-plates`, then `moodreel film new <name> --style signal-plates`.

| Kind · 类别 | Files | What it is |
|---|---|---|
| Rules · 规则 | `STYLE.md` | the style prompt: essence, materials, colour, type, motion, camera, sound, moves, pitfalls, engine, variation |
|  | `DECISIONS.md` | the choices the measurements could not make, approved at gate 1 |
|  | `style.json` | slug, names, size 1920x1080, 60 fps, needs: 3d, music-led |
| Evidence · 证据 | `evidence/LEDGER.md` | every number in STYLE.md with its basis (observed, derived, inferred) and source |
|  | `evidence/intake.json` | the references: kind, size, licence source, checksum (the files stay with their owner) |
|  | `evidence/measure/` (13) | frame-check, layout, motion-check-demo, motion-check-proxy1, motion-check-proxy2, motion-check-sketch, motion, palette, rhythm, shots, style, texture, type |
|  | `evidence/refs-sheet.jpg` | the references, one sheet (own work, so it may travel) |
| Kit · 代码: the style's own | `kit/engraved.js` | the engraved body |
| Kit · 代码: the style's own | `kit/form.js` | the paper form |
| Kit · 代码: the style's own | `kit/linefield.js` | the line field |
| Kit · 代码: the style's own | `kit/prompt.js` | the prompt field |
| Kit · 代码: the style's own | `kit/signal.js` | the style's own core |
| Kit · 代码: measured | `kit/tokens.js`, `kit/motion.js` | palette, type tiers, layout, texture; durations, eases, stagger, beat |
| Kit · 代码: shared | `brush.js`, `core.js`, `eases.js`, `pixel.js`, `stage.js`, `text.js`, `texture.js` | the kit every film gets (stage, core, eases, text, texture, ...) |
| Kit · 代码: fonts | `kit/fonts/Archivo-var.ttf`, `kit/fonts/CormorantGaramond-Italic-var.ttf`, `kit/fonts/IBMPlexMono-Bold.ttf`, `kit/fonts/IBMPlexMono-Medium.ttf`, `kit/fonts/IBMPlexMono-Regular.ttf` | with `kit/fonts/OFL.txt` |
| Demo · 演示片 | `demo/` | the demo film's source: `CREDITS`, `build.sh`, `film.json`, `index.html`, `lyrics.json`, `main.js`, `music-data.js`, `poster.jpg`, `score.js`, `score.json`, `sfx.json`, `sfx.mjs`, `timeline.js` |
|  | `demo.mp4` | not in the repository: rebuild with `sh demo/build.sh` (it writes `demo.mp4` beside `demo/`) |
|  | `styleframe.jpg` | the style frame approved at gate 2 (frame-check compares films with it) |
