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
| 2 | The medium and how code imitates it: surfaces, marks, layers, edges, texture, light; what must be procedural and stay fixed to the world, what lives in screen space; the rendering techniques the shots need (GPU lines, hatching, 3D, bloom: `reading-shots.md`) | texture.json, shots.json + your reading; kit `texture.js`, `gl.js` recipes |
| 3 | Rules, not a palette: how many hues, the ground, what the accent is reserved for, the order of values, what is never coloured; one example palette with the measured hex. A palette seen in one film is one example: other hues the style may take go to §11 | palette.json roles, structure, per_ref |
| 4 | Typeface classes and roles, size ranges as a share of the frame height, weights, case, alignment; how subtitles belong to the style; reading time ≥ CJK chars / 4.5 + other chars / 15 + 1.5 s | type.json, layout.json, type-lines.jpg |
| 5 | Frame rate and stepping; entrance, exit and move: duration ranges, ease class and named eases where claimed, overshoot (how often, how much); staggers (interval, order); holds; numbers that count (duration, ease, how they are printed); ambient loops (periods, how far they bob, pulse, breathe or spin) and particle fields; the beat grid when moves start and land on one (MEASURE.md "Beat grid"): a timing rule here, not only in §7; what never moves | motion.json |
| 6 | Shot lengths, transitions (types, durations, eases), camera moves and their rates, framing rules (margins, safe areas, where text lives) as a table of moves: what each expresses, what it can serve. Cuts on the beat grid say so. Moves and transitions the references don't use are not banned for that | motion.json shots/camera, layout.json |
| 7 | Instruments, density, silence, mix character; what music the beat grid asks for (the grid itself is a §5/§6 rule) | rhythm.json, user, your proposal (gate 1) |
| 8 | Moments only this style does: what, how to build it, and three kinds of content it fits. The measured signature (e.g. "a left-to-right stagger of 0.12 s with a 10 % overshoot") becomes one | the motion that recurs across references |
| 9 | Mistakes the medium invites, each with its fix (an accent below 15 % opacity disappears in H.264; a 1 px rule vanishes at 1080p) | measurement + experience |
| 10 | The kit files and functions that draw the style (kit/tokens.js, kit/motion.js, the style's own modules), and a minimal example that draws something not in the demo | the kit you wrote |
| 11 | What each film decides, including what the references happen not to show (another hue, a busier or emptier frame, a camera move, a transition type); three structures, three openings and three endings, all far from the demo | your judgement |

## Few references: unseen is not forbidden

A user's references are often one film and a few frames. They show what the style does, not everything it allows,
and a director who reads "the references never do X" as "the style never does X" writes a narrower style than the
real one: a film made from it looks like the references, and a film the style would allow is ruled out.

- A rule says what the references always do: "one hue carries every frame here", "entrances rise out of slots".
- "Never", "only" and "no" need evidence that the thing was avoided where it would have been natural, or a reason in
  the medium itself: ten transitions that are all cuts support "cuts, not dissolves"; one film with one shot change
  supports nothing about dissolves. What one film's palette lacks, it hasn't ruled out.
- What the references don't show is unseen: say nothing about it in §1-§6, or say it in the style's terms as an open
  choice (what it would have to respect if a film used it) and list it in §11.
- One film's density, palette and structure are examples, not the style: its calm (or its bustle) is a choice that
  film made unless every reference makes it.
- Timing that locks to a pulse (MEASURE.md "Beat grid", or moves landing on an even beat in the evidence) is a motion
  rule: §5 says that moves start and land on the beat, §6 that cuts fall on downbeats, §10 that the kit counts in
  beats. §7 only says what sound would fit it.
- Before finishing, read every "never", "only", "no", "always" and "must" in your STYLE.md once more and keep only
  those that the evidence supports or the medium enforces.

## Wording

- **Ranges, not points**: "entrances 0.5–0.65 s, ease-out (power3.out)" rather than "0.567 s". The measured point goes
  in the ledger and the kit; the rule gives the director room.
- **Say why**: "exits are shorter than entrances (0.35 vs 0.55 s): things leave faster than they arrive."
- **Name the measured, mark the inferred**: a rule that rests on your judgement says so ("by eye: …") and is
  `inferred` in the ledger.
- Every number with a unit and every hex in STYLE.md must appear in LEDGER.md or the kit; `moodreel pack` checks.
- Keep it 6–11 KB. If a section grows past a screen, it is holding a film, not a style.
