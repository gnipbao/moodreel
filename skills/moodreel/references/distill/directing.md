# Reading a film as its director and its motion designer

Measurements say where things are and how fast they move: `compare` (picture, motion, speed), `camera` (pan, push,
roll), `track` (where each subject is on screen), `look` (what Jev sees differ). None says why a shot is built as it is:
what it shows and what it holds back, where the eye goes, why the camera moves and how it eases, what the shot hands to
the next. A remake that copies positions without that reads stiff, and a style distilled from positions is a list of
coordinates. The reasons are what carries over to another film: read them first, then build, then measure.

## The reading

1. **Ask Jev the director's questions** (opt-in, frames to TypeSafe):
   `moodreel direct <reference> --shots scenes.json --md direction.md --allow-image-upload`. Per window, of its middle
   frame: how wide the shot is (extreme wide to extreme close-up), from where (overhead, high, eye level, low, the
   ground), how it is composed (centred, thirds, a leading line, symmetry, framed, a field of repeated things), the
   light, and where the eye goes first (a box). Of its start, middle and end frames together: how the camera moves (pan,
   tilt, push, pull, crane, orbit, follow, whip, roll), how fast, how it eases (steady, speeding up, slowing down, in and
   out, abrupt), what the subject does, and whether the end reveals what the start hid. Each answer is a distribution:
   a crane that also pulls out shows as both.
2. **Look yourself**, a contact strip of each sequence at four frames a second, and write per sequence: what it is
   for (the story beat), what the camera follows and why, the shape of its motion (where it speeds up, where it slows
   into a hold, where it whips), what the subject does on the way (anticipation, squash, overshoot), and how it hands
   over to the next sequence (a move, a flash, a cut on a beat). Jev's answers anchor the words; your reading joins
   them into intent.
3. **Check each claim against a measurement**: `camera` for the move and its speed, `sync` for the beat, `track` for
   where the eye's subject sits. A reading that a measurement contradicts is a guess.
4. **Turn it into the brief**, in this order: the layout (what stands where, so the shot's lines exist: a river, a road,
   a row of houses), the camera's anchors at the beats the reading names (start, reveal, hold), the motion between them
   (ease into holds, accelerate into reveals), and only then `kit/lock.js` to fine-tune onto Jev's boxes.
5. **After each pass**, `moodreel direct <reference> --against <remake>` gives the director's notes: where the remake
   reads as another shot size, angle, composition, move, ease or action. Fix the notes, not the pixels.

## What the 3D film's reading found (the seventh round)

The reference (`帮我造一个世界`, 64 s, one take) read as a director:

| Sequence | What it is for | Camera and motion |
|---|---|---|
| terminal, pour | the critter leaves the screen | the logo turns into cubes and turns; they pour down the screen to the desk |
| desk hop, keys | it explores, the keyboard wakes | low, close, following hops; keys light a few at a time round it |
| keyboard of worlds, dive | each key a world; it chooses one | a three-quarter view; it jumps from the space bar, the camera pushes in after it |
| fall, landing | arrival | it tumbles over a meadow; lands on a crest; a longer lens, the sun behind |
| building | the world grows | wide, eye level, orbiting the critter as mountains, river and forest rise |
| crowd, march, town | 128 of it, at work | one long crane: above the arcs, along the line to the river, up over the houses rising; slows into the valley |
| whip, sunset | the day ends | a fast whip over the town that slows into a view down the river: the river a line to the sun (Jev: leading line 0.98, slowing down) |
| dusk, lights on | time passes | one slow pan as the light turns from orange to blue; the town's lights come on in an extreme wide from high (0.96) |
| night, swoop | it watches, then the film lifts off | low on the rise, the lamp lines leading into the town; a swoop over the crest and the houses that speeds up and rolls (0.75) |

Its motion grammar (what a style distilled from it should keep):

- **One take.** Every transition is a camera move or a white flash; nothing cuts except on the two flashes.
- **Moves have a shape.** They accelerate into reveals and decelerate into holds (the whip slows into the sunset, the
  swoop speeds up into the town); a steady move reads as a machine's.
- **Lines compose the wide shots.** A river, a road, a lamp line, a line of critters lead the eye to the subject; a
  town packed as a block reads as a pattern, not a place.
- **Light changes inside a move.** Dusk is one pan, not a series of shots.
- **Each shot has one place for the eye**, and the next shot's starts near it.

Building to the reading: the town laid in rows along the river (not a block), the sun set down the river, the camera
keyed at the reading's beats, the lock only where the layout already agrees (the aerial build: 0.54 to 0.68 at the
reference's speed). Over the round: compare 0.635 to 0.645, Jev's likeness 0.393 to 0.406; sunset 0.47 to 0.70, night
grass 0.49 to 0.58, crowd (Jev) 0.37 to 0.52. Jev's director's notes went from 83 to 79; most of those left are about
motion's shape: the reference speeds up, slows into holds and flies low, where the remake's camera glides at one pace
between anchors. That is the next round's work: ease curves per move, not positions.

## Limits

- Jev reads frames, not intentions: "the subject flies" can mean a camera flying low and fast. Read its answers as
  evidence for your reading, not as the reading.
- Three frames give a move's direction and a rough speed, not its curve; the curve is `camera`'s track.
- Ask about what a director would change; a remake drawn in code differs from its reference everywhere in detail.
