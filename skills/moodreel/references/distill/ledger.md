# LEDGER.md

One row per value that STYLE.md or the kit uses. The point is that anyone can see which rules rest on measurement and
which on judgement, and re-check them.

```markdown
# Ledger — <Name>

| value | used in | basis | source |
|---|---|---|---|
| ground #0c0d13 | §3, tokens PALETTE.ground | observed | measure/palette.json roles.ground (all 4 references) |
| ink contrast 15.8:1 | §3 | derived | palette.json roles.ink_contrast |
| title line 8.1 % of frame height | §4, tokens TYPE.title | observed | type.json title_height (tier of 6 lines) |
| typeface Archivo 800 | §4, tokens TYPE.display | inferred | type-lines.jpg: geometric grotesque, tight caps; OFL |
| entrance 0.50–0.65 s | §5, motion MOTION.enter | observed | motion.json entrance duration p25–p75 (9 events, vid01) |
| entrance ease-out, power3.out | §5 | derived | 5 of 9 out; claimed on 2, equivalent families on 3 |
| exit shorter than entrance | §5 | derived | exit median 0.45 s vs entrance 0.57 s |
| no vignette | §2 | observed | texture.json vignette 0.0 (under 3 grey levels) |
| cuts every ~3 s | §6 | observed | motion.json shots length median 3.0 s (2 shots: weak) |
| marimba and soft kick | §7 | inferred | user's choice at gate 1 |
```

- **observed**: read off the pictures by `moodreel measure` (palette, texture, layout, type sizes, motion timings).
- **derived**: computed from observed values (contrast ratios, medians across references, a back.out(s) fitted to a
  measured overshoot, "exits shorter than entrances").
- **inferred**: your judgement or the user's choice (typefaces, sound, motion from images alone, anything read by eye
  from the evidence strips). Say what you looked at.
- Note when the evidence is thin (one reference, two shots, three events). A rule built on it may still be right; the
  next reference can overturn it.
- `unknown` is never a rule. If a section needs a value nobody measured, decide it, and mark it inferred.
