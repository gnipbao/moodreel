# Treatment: every-style

Style: Caption News (caption-news, styles/caption-news). Read its STYLE.md first; DEMO.md and the demo source only after this treatment exists.

## Brief

A 12.5 s sound-off news short: every style in Moodreel's library can now be made. 1920×1080, 24 fps, silent. Words:
59 套风格, 过去只能做 23 套, 现在全部能做, 像素 笔触 3D 配乐, each with its English line. Brand: a fictional
channel, 画格快讯 FRAME WIRE. It exists to show real material in Moodreel: footage taken in with
`moodreel media add` (trimmed, scaled, its source and licence in media/manifest.json), drawn by time with
kit/media.js, and checked by `film check`. The footage is the four other example films, so the piece needs nothing
from outside this repository (build.sh rebuilds it).

## Three structures

1. A ledger card that counts the library up style by style, footage only as a closing montage (more data card than
   footage; the style says charts are inserts, not the film).
2. Four captioned shots on four example films: the number, what it used to be, the turn, what changed.
3. A split screen, "before" desaturated on the left and "after" on the right, one counter in each (needs footage of a
   film that failed, which there is none of).

Chosen: 2, the style's own order of a fact cut down to a short: footage under a number with its source, then the turn.

## Logline and arc

Moodreel's library holds 59 styles and every one of them can now be made. Setup: the number and its source.
Turn: until now only 23 could be made, now all of them. Ending: what made the difference, over the pixel film saving.

## Beats

- 0.0–3.0 s, quiz-night: the hook, a honey block with 59 rolling up from 0.15 s; the chunks slam 0.12 s apart;
  the source tag slides in at 0.2 s (styles/index.json).
- 3.0–6.0 s, harbour-dawn: 过去只能做 {23} 套, with its source tag (phase: mvp).
- 6.0–9.0 s, tide-town: the turn, a two-frame white flash on the cut; 现在 {全部} 能做.
- 9.0–12.5 s, first-save, from after its dialog box leaves (so its own words never sit under the caption): night falls
  and the game saves; 像素 笔触 {3D} 配乐.

Every cut is on the 120 BPM half-beat grid (3.0 s; the last shot holds 3.5 s), every caption is up at least 3 s,
the English line follows 0.1 s after the first chunk, and every shot carries its footage credit top right.

## Not the demo

Structure: four shots and one turn, no ledger cards, documents, map or freeze frame. Opening: the number over a game
show. Signature: captions over Moodreel's own films. Ending: the pixel game saving, not a verdict card.

## Left out

Sound: the style wants a 120 BPM pulse, foley on every slam and a narrator; this film is silent (sound-off first is the
style's own rule). `moodreel score` and `moodreel voice` would add them.
