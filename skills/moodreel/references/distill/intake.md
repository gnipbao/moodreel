# Intake

## What to ask for

A style needs enough pictures to separate what is constant from what changed between them:

- **3–12 design images** of one visual system: posters, key frames, UI screens, slides. Long edge ≥ 1080 px.
- **0–3 videos**, 5–60 s each, ideally code-made motion graphics. Motion is measured only from video; with images
  alone, motion is inferred (see below).
- **Where they come from**: the user's own work (`--source own`) or found elsewhere (`--source web`). Only the user's own
  work may leave a contact sheet in the style pack; found references never leave the project folder.

```bash
moodreel intake <project> refs/*.png refs/teaser.mp4 --source own
```

Intake copies the references into `<project>/refs/` (PNG long edge 2048, H.264 at the source frame rate), writes
`intake.json` (hashes, sizes, frame rates, audio) and `evidence/refs-sheet.jpg`. Look at the sheet first.

## Do they share one style?

Intake compares the references' palettes (earth mover's distance in CIEDE2000, areas included: a light ground with dark
type and a dark ground with light type are far apart) and groups them. If `intake.json → unity.unified` is false, ask:

- which group is the style (re-run intake with that group only), or
- whether they want a mix: then decide which group is the base and which moves are borrowed, and say so in DECISIONS.md.

## The one round of questions

Ask in one message, only what the files can't tell you:

1. **What the films are for**: who watches, where they are posted. This sets the size (`intake.json → default_size`
   comes from the references' aspect; a vertical feed wants 1080×1920 or 1080×1350) and the variation space (§11).
2. **Brand material**: logo, typefaces they hold licences for, colours that must appear. A brand colour enters as the
   accent first, not the ground.
3. **Language** of on-screen text, so the typefaces cover it (CJK needs CJK glyphs).
4. **Name** for the style, in English and Chinese (or decide one and say so).
5. **Images only?** Then motion has nothing to measure. Offer three temperaments and take their pick: *restrained*
   (entrances 0.6–0.9 s, sine/power2 in-out, no overshoot, long holds), *balanced* (0.4–0.6 s, power3.out, a little
   overshoot on small elements), *lively* (0.25–0.4 s, back.out or expo.out, staggers ~0.06 s, cuts on beats). Every
   motion value is then `inferred` in the ledger.

Fill every other gap with a sensible default and say which default you took.
