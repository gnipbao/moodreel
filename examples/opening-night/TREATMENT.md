# Treatment: opening-night

Style: 1930s Rubber Hose Cartoon (rubber-hose, styles/rubber-hose). Read its STYLE.md first; DEMO.md and the demo source only after this treatment exists.

## Brief

A 16 s cartoon in which the band itself is the cast: an upright piano, a tuba and a clarinet, each a whole-object
character, play their opening night on a painted stage. 1920×1080 with the style's 4:3 gate, 24 fps. Words: Opening
Night, A Moodreel Cartoon, The End. It exists to show sampled instruments in Moodreel: the score is written first in
`score.json` with the sampled band (stride piano, tuba oom-pah, trumpet and horn stabs, a clarinet on the motif,
timpani, synthesised woodblock and whoosh as foley) and every picture hit lands on a cue from `score.js`.

## Three structures

1. A relay: a tune passed hand to hand across a town, each hand-off a new instrument (needs a town and many cast).
2. The band assembles: the piano starts alone, the tuba drops in, the clarinet steals the chorus, the band bows.
3. A singalong: lyrics on a card with the bouncing ball (needs a lyric worth remembering).

Chosen: 2, because the picture can add a player exactly when the score adds a part: what you see enter is what you
hear enter.

## Logline and arc

Three instruments play their first night. Setup: a title card over the piano's vamp, rolled up like a window shade.
Turn: the band stops dead and a clarinet peeks out of the wings, then leaps in on a brass hit. Ending: a ta-da, the
iris closes on the clarinet, and its glove pulls the iris shut.

## Shots

| # | time | framing | camera | duration | why |
|---|---|---|---|---|---|
| 1 | 0-4 s | the title card, full gate | locked | 4 s | the film is an object: the card rolls up like a shade |
| 2 | 4-13.5 s | stage-wide, a proscenium, the cast medium-full | locked; the stage squashes at the peak | 9.5 s | a group number |
| 3 | 13.5-16 s | The End card | locked | 2.5 s | the film ends as an object |

## Beats

120 BPM, one beat 12 frames (even, so every beat lands on a drawing of the twos); a bar is 2 s.

- Bar 1-2: the title card with sunburst rays; "Opening Night" lands on the downbeat with a piano chord (cue
  `title`), its letters hop in a travelling wave on every beat; the piano vamps alone (stride: bass on 1 and 3, chords
  on 2 and 4). Bar 2 beat 4: the card rolls up like a shade in half a beat (cue `shade`, a whoosh).
- Bar 3: the piano plays itself, gloves hammering the keys on 2 and 4, lid lifting on the chords. The tuba drops in
  from the flies and lands with a squash on the downbeat (cue `tuba`, a timpani hit); from there it hops oom-pah on 1
  and 3, the bell puffing scattered rings.
- Bar 4 beat 3: the band stops for one beat (cue `freeze`): everything freezes, breathing included. On the off-beat a
  clarinet peeks out of the right wing with a woodblock tick (cue `peek`). Beat 4: it crouches (anticipation).
- Bar 5 beat 1: it leaps to centre stage on a brass hit (cue `leap`) and the chorus starts: brass stabs on 2 and 4,
  the clarinet swaying on the motif it plays.
- Bar 6: the peak: every character breathes three times as wide and the painted stage squashes on the floor line.
- Bar 7 beat 1: ta-da, all arms up, on a brass hit (cue `tada`). The iris closes on the clarinet over two beats; a
  glove reaches out of the hole and pulls it shut on beat 4 (cue `shut`, a woodblock).
- Bar 8: a timpani roll swells into the downbeat (cue `swell`); The End card lands on it with a piano chord (cue
  `end`) and holds.

Everything idle breathes with cos(2π·beats), stretch on the beat, squash on the off-beat, sampled on twos.

## Not the demo

Structure: the band assembling on a stage, not the demo's story. Opening: a title card rolled up like a shade.
Signature: the instruments as the cast, each entering with its own part. Ending: the iris pulled shut by a glove.

## Left out

The samples have no banjo, trombone, xylophone, slide whistle, washboard or organ: the band here is piano, tuba,
trumpet, horn, clarinet and timpani, with woodblock and whoosh synthesised. There is no optical soundtrack pass (band
limit, wow and flutter, crackle) and the grain is drawn in the page, light, because delivery has no grain step.
