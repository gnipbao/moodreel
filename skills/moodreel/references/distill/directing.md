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
| building | it makes the world | it stomps, and the camera pulls up and back fast as the mountains rise, easing into a wide hold; it skips at the tick as the camera pushes back in; it turns and pushes, and the river is cut from its feet out; it jumps, and the forest rises on the slope behind as the camera turns to it |
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
- **Every making is acted.** The subject does something the moment a thing appears (a stomp, a push, a jump) and the
  camera answers it (pulls back to show what rose, pushes in on the tick, turns to what grows). A thing that appears
  while the subject walks past with its back turned reads as a timer, not as its doing; read which way the subject
  faces (Jev's `facing` check) and keep it.

Building to the reading: the town laid in rows along the river (not a block), the sun set down the river, the camera
keyed at the reading's beats, the lock only where the layout already agrees (the aerial build: 0.54 to 0.68 at the
reference's speed). Over the round: compare 0.635 to 0.645, Jev's likeness 0.393 to 0.406; sunset 0.47 to 0.70, night
grass 0.49 to 0.58, crowd (Jev) 0.37 to 0.52. Jev's director's notes went from 83 to 79; most of those left are about
motion's shape: the reference speeds up, slows into holds and flies low, where the remake's camera glides at one pace
between anchors. That is ease curves per move, not positions. Check a reading's ease against the measured shape
(`moodreel camera --against` reads speed by thirds; three frames can mislead), pace the camera by the reference's
speed (`follow(..., { pace: true })`), and give a `speed` per anchor (or `[in, out]`) only where the measurement is
blind: a burst after a stomp, a stop at a tick.

## What a typography film's reading found (the fourth film)

The reference (Su Shi and 定风波, 83 s, Remotion) is words on paper and in the dark; the user named three shots that
the remake had right in pixels and wrong in meaning:

| Shot | What it is for | What the remake did | Built to the reading |
|---|---|---|---|
| 12 s, the poem seized | confinement, then the charge | a lit orange tableau of tiles | an iris onto the bound tile, dim; at 12.85 s it snaps open, 诗 slams in red at half the frame's height, the only colour, the camera lurching among grey fallen tiles; the rain wipes it |
| 58 s, a life collapsing | the words are the life, and it falls | the line scattered and vanished | a pulse traced in that goes flat; each character topples in its turn, falls and lands in a heap of rubble that stays a beat; a frame flashes as it gives way |
| 73 s, the goose | 人生到处知何似: a trace, then gone | one smooth diagonal across the page | 飞鸿 turns to grit and the grit is the goose; it lingers by its column facing back, then turns and leaves fast, up and away |

Its motion grammar:

- **A collapse is gravity.** Things that fall land, pile and stay a beat before they fade; a scatter that fades in
  the air reads as a dissolve, not a fall.
- **Confinement before release.** A small dim iris, held still, then a hard opening onto the full frame: the opening
  is the event.
- **One colour carries the meaning.** Where everything else is grey, the red word is the subject; keep its size (here
  half the frame) and don't let anything else take colour.
- **An exit lingers, then goes.** A creature that leaves holds near where it was born for a while, then accelerates
  away; one even glide reads as a sprite.
- **Particles are matter.** They come from something and become something (the scroll's grit gathers into the name,
  the name keeps its grain; 飞鸿's grit is the goose); a cloud that comes from nowhere reads as an effect.

Over the round: the 58 s window 0.49 to 0.60 (compare), the 12 s window's likeness 0.21 to 0.38 (Jev).

The fifth round's review read the rest of the film the same way (out/challenge4/review-r5/faults.md):

- **A transition can be the next shot seen from elsewhere.** The wall of text is the floor of words seen from above:
  the camera rises (one page, then a grid of pages) and tilts into the tiles' shot. Built as a push-in on a wall, it
  handed over to nothing.
- **A flight has a destination.** 大江东去 flies low over a sea of sand toward 赤壁, the cliff the poem is about, and
  surges through each character standing on the sea: slow as it nears, a blur as it passes. Without the cliff the
  flight was a screensaver.
- **Colour leaving is an event.** 盛, the tile of fame, hangs orange over 一〇七九 and drains to grey as 乌台诗案 is read.
- **Where the camera stands says where we are.** The seized poem is seen from the floor of a cell, low, a dark wall
  behind the one grey tile; seen from above it was a still life.

The seventh round read the motion frame by frame (`moodreel review`'s motion half, out/challenge4/review-r7/faults.md):

- **A name can be an image.** 乌台, the Crow Terrace, named for the crows in its cypresses: crows dart across the year
  of the trial as it lands. A pun made into a picture for a moment, invisible in any still at 40 % or 80 % of the shot.
- **An arrival is a blow.** Every line that matters lands in three frames from twice its size, the year with its colours
  split; the frame 谁怕? lands on is its negative, cyan on white. Fades read as hesitation where the film means force.
- **A shut world closes in a circle.** The floor of his fame goes dark in a circle closing on the red cords, the
  handcuffs, and only 盛 stays lit in its beam.
- **Weather is a beat.** Lightning lights the grove twice for a frame as the poem is said; the rows of 每天都很焦虑。
  tremble sideways every frame: anxiety as motion, not as text.
- **A walk is weight and water.** The monk walks in profile, the staff planted ahead at each step, a ring spreading
  where each foot lands: 竹杖芒鞋轻胜马 is in his gait, not in his outline.

## Limits

- Jev reads frames, not intentions: "the subject flies" can mean a camera flying low and fast. Read its answers as
  evidence for your reading, not as the reading.
- Three frames give a move's direction and a rough speed, not its curve; the curve is `camera`'s track.
- Ask about what a director would change; a remake drawn in code differs from its reference everywhere in detail.
