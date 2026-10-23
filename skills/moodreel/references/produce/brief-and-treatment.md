# Brief and treatment

## The brief: one round

Read the style's STYLE.md (and for a distilled style, its kit) before asking anything. Then one message, only what you
can't decide yourself:

- the facts: names, numbers, claims, products that must appear (and that the user has the right to use);
- their material: logo, typefaces, images, data, a music track (or none: Moodreel can write the film's own score,
  below);
- length, size and language if not obvious (default: the style's size, the user's language, 15–30 s);
- whether they want to see a storyboard before production (default: no).

Then sum up the brief in a few lines and start. Don't come back with more questions.

## TREATMENT.md, before any drawing

`moodreel film new` writes the template. Fill it in this order:

1. **Three candidate structures**, a few lines each (a single journey, a before and after, a countdown, a list that
   turns, a problem and its reveal…), then the one you chose and why. The first idea for a style is usually its
   cliché: let the topic choose.
2. **Logline and arc**: one sentence; setup, turn, ending. One subject, one goal, one turn. A hook in the first 3 s.
3. **Shots**: framing, camera (from §6's vocabulary), duration and *why* each shot is shot that way.
4. **Beats**: second by second, what arrives, holds and leaves. Use the style's numbers: entrances last
   `MOTION.enter.duration`, groups stagger by `MOTION.stagger.interval`, holds last at least `MOTION.hold`, shots run
   about `MOTION.shot`. If the style cuts on beats, lay the beats on the music's grid first.
5. **Native move**: one moment only this style can do (§8), placed at the peak.
6. **Text**: every line, with how long it stays (≥ CJK chars / 4.5 + other chars / 15 + 1.5 s).
7. **Not the demo**: put the style's DEMO.md (and its demo film if there is one) beside this: structure, opening,
   signature shot, ending. At least three must differ. Read DEMO.md and the demo's source only after this treatment
   exists: they are for techniques, never for story.

## Built-in styles

The 59 built-in styles come with STYLE.md and DEMO.md but no kit: `film new` writes a fill-in `tokens.js` and
`motion.js`. Fill them from §3, §4, §5 and §6 before drawing, so the film's numbers have one home. Links in DEMO.md open
the original demo's source upstream: read them for how a texture or a move was built, then write your own.

Styles marked `later` need what Moodreel doesn't do yet (a painterly brush engine, 3D, pixel art, real footage or
data). Tell the user which, and what you can still make: often a flat 2D reading of the style that keeps its palette,
type and timing. Styles marked `ready` needed a score that drives the picture, which Moodreel now writes.

## The score first (music-led styles, or any film with its own music)

A music-led style times the picture to the music: the tempo grid and the cue table come before any animation, and
every picture hit lands on a listed cue. `film new` gives such a film a `score.json`; write it with the treatment:

- `bpm`, `meter`, `seed`; `sections` in order, each with `bars`, a chord loop (one chord per bar: `C`, `Am7`, `F#m`,
  `Bb7`, `Gsus4`...), a `groove` (four, backbeat, halftime, oompah, none) and its `parts` (kick, snare, clap, hat,
  bass, pad, stab, pluck, lead), as the style's §7 asks (a jingle into each round, an oom-pah under a gag);
- `cues`: every hit the picture lands on, by name, `bar` and `beat` (from 1; 2.5 is the off-beat after 2) and its
  `sound`: stab, hit, pop, boing, ding, whoosh, clack, riser (it ends on the cue), or stop (the band falls silent for
  `beats`: a held stare before a gag; other cues still sound in it).

`moodreel score <film>` renders it to `out/score.wav` and writes `score.js`, which the picture imports: `cue('title')`
is when the title lands, `bar(5, 3)` the time of bar 5, beat 3. Start each move so it lands there:
`tween(t, cue('title') - d, d, ease)`. The instruments are synthesised (a bright toy band and pitched foley); a style
whose §7 asks for an orchestra or a piano gets its grid and cues right and its timbre only roughly.
