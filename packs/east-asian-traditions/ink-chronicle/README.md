# Ink Chronicle · 墨字列传

East Asian Traditions · 东方传统. Distilled with Moodreel on 2026-10-29; install with `python scripts/packs.py install ink-chronicle`, then `moodreel film new <name> --style ink-chronicle`.

| Kind · 类别 | Files | What it is |
|---|---|---|
| Rules · 规则 | `STYLE.md` | the style prompt: essence, materials, colour, type, motion, camera, sound, moves, pitfalls, engine, variation |
|  | `DECISIONS.md` | the choices the measurements could not make, approved at gate 1 |
|  | `style.json` | slug, names, size 1920x1080, 30 fps, needs: 3d, music-led |
| Evidence · 证据 | `evidence/LEDGER.md` | every number in STYLE.md with its basis (observed, derived, inferred) and source |
|  | `evidence/intake.json` | the references: kind, size, licence source, checksum (the files stay with their owner) |
|  | `evidence/measure/` (11) | frame-check, layout, motion-check-demo, motion-check-sketch, motion, palette, rhythm, shots, style, texture, type |
| Kit · 代码: the style's own | `kit/faces.js` | the type's faces |
| Kit · 代码: the style's own | `kit/marks.js` | the style's marks (STYLE §2), each taking any shape or region the film gives it |
| Kit · 代码: the style's own | `kit/paper.js` | the grounds (STYLE §2) |
| Kit · 代码: the style's own | `kit/space.js` | a space to stage type in (STYLE §2, §6) |
| Kit · 代码: the style's own | `kit/type.js` | type as matter (STYLE §1, §2, §5) |
| Kit · 代码: measured | `kit/tokens.js`, `kit/motion.js` | palette, type tiers, layout, texture; durations, eases, stagger, beat |
| Kit · 代码: shared | `anim.js`, `brush.js`, `core.js`, `eases.js`, `pixel.js`, `stage.js`, `text.js`, `texture.js`, `three.js` | the kit every film gets (stage, core, eases, text, texture, ...) |
| Kit · 代码: fonts | `kit/fonts/IBMPlexMono-Medium.ttf`, `kit/fonts/IBMPlexMono-Regular.ttf`, `kit/fonts/LXGWWenKai-Medium.ttf`, `kit/fonts/LXGWWenKai-Regular.ttf`, `kit/fonts/NotoSerifSC-wght.ttf` | with `kit/fonts/OFL-IBMPlexMono.txt`, `kit/fonts/OFL-LXGWWenKai.txt`, `kit/fonts/OFL-NotoSerifSC.txt`; `NotoSerifSC-wght.ttf`, `LXGWWenKai-Regular.ttf`, `LXGWWenKai-Medium.ttf`: not in the repository, `sh kit/fonts/fetch.sh` downloads them |
| Demo · 演示片 | `demo/` | the demo film's source: `CREDITS`, `build.sh`, `film.json`, `index.html`, `main.js`, `music-data.js`, `poster.jpg`, `score.js`, `score.json`, `sfx.json`, `sfx.mjs`, `timeline.js` |
|  | `demo.mp4` | not in the repository: rebuild with `sh demo/build.sh` (it writes `demo.mp4` beside `demo/`) |
|  | `styleframe.jpg` | the style frame approved at gate 2 (frame-check compares films with it) |
