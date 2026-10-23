# Writing STYLE.md

STYLE.md holds what stays true in **every** film of the style, as rules a director can follow. No story, no shot
list, no durations of one film: those go in the demo's notes. Write it after ANALYSIS.md and before any drawing.
Start from `styles/_template/STYLE.md` for the section headings (their numbers are fixed; tools check them).

```
# <Name> — Style Prompt
<one line: Name · 中文名; size if not 1920×1080>
> One or two sentences: what the medium is and what it does on screen.
## 1. Essence, and what it is not        ## 7. Sound palette
## 2. Materials & rendering              ## 8. Native moves
## 3. Colour logic                       ## 9. Pitfalls of the medium
## 4. Type & subtitles                   ## 10. Engine
## 5. Motion quality                     ## 11. Variation space
## 6. Camera grammar
```

## Section by section

| § | Write | From |
|---|---|---|
| 1 | 3–5 traits that make a frame read as this style at a glance, each traceable to evidence; then the 2–3 styles it is easily confused with and the line between them (compare with the library: `moodreel styles`) | ANALYSIS.md |
| 2 | The medium and how code imitates it: surfaces, marks, layers, edges, texture, light; what must be procedural and stay fixed to the world, what lives in screen space | texture.json + your reading; kit `texture.js` recipes |
| 3 | Rules, not a palette: how many hues, the ground, what the accent is reserved for, the order of values, what is never coloured; one example palette with the measured hex | palette.json roles, structure, per_ref |
| 4 | Typeface classes and roles, size ranges as a share of the frame height, weights, case, alignment; how subtitles belong to the style; reading time ≥ CJK chars / 4.5 + other chars / 15 + 1.5 s | type.json, layout.json, type-lines.jpg |
| 5 | Frame rate and stepping; entrance, exit and move: duration ranges, ease class and named eases where claimed, overshoot (how often, how much); staggers (interval, order); holds; what never moves | motion.json |
| 6 | Shot lengths, transitions (types, durations, eases), camera moves and their rates, framing rules (margins, safe areas, where text lives) as a table of moves: what each expresses, what it can serve | motion.json shots/camera, layout.json |
| 7 | Instruments, density, silence, mix character; whether the edit follows the beat (rhythm.json) | rhythm.json, user, your proposal (gate 1) |
| 8 | Moments only this style does: what, how to build it, and three kinds of content it fits. The measured signature (e.g. "a left-to-right stagger of 0.12 s with a 10 % overshoot") becomes one | the motion that recurs across references |
| 9 | Mistakes the medium invites, each with its fix (an accent below 15 % opacity disappears in H.264; a 1 px rule vanishes at 1080p) | measurement + experience |
| 10 | The kit files and functions that draw the style (kit/tokens.js, kit/motion.js, the style's own modules), and a minimal example that draws something not in the demo | the kit you wrote |
| 11 | What each film decides; three structures, three openings and three endings, all far from the demo | your judgement |

## Wording

- **Ranges, not points**: "entrances 0.5–0.65 s, ease-out (power3.out)" rather than "0.567 s". The measured point goes
  in the ledger and the kit; the rule gives the director room.
- **Say why**: "exits are shorter than entrances (0.35 vs 0.55 s): things leave faster than they arrive."
- **Name the measured, mark the inferred**: a rule that rests on your judgement says so ("by eye: …") and is
  `inferred` in the ledger.
- Every number with a unit and every hex in STYLE.md must appear in LEDGER.md or the kit; `moodreel pack` checks.
- Keep it 6–11 KB. If a section grows past a screen, it is holding a film, not a style.
