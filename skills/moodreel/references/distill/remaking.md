# Remaking a film shot by shot

A remake is matched to its reference shot by shot, then measured, then fixed where it is furthest off. Drawn from
what the eye reads, its first pass is a different film; each step below came from closing that gap on a 16 s launch
teaser (ASCII glitch, 20 scenes, 60 fps), where five rounds took the mean window score from 0.49 to 0.65 (median
0.69), and the third round the five shots it worked on from 0.38-0.60 to 0.57-0.84. A second film, a 64 s one-take 3D
voxel world (a critter leaves a terminal, builds mountains, a river, a town of 128 houses, then lights it), went from
0.53 to 0.59 (mean of 36 windows) in seven passes, then to 0.61 in a second round on what its maker named, and a third
round rebuilt the landing, the building and the desk to the reference, a fourth the night (0.614), a fifth locked
camera and critter to where Jev's vision saw them in the reference (0.637), a sixth rebuilt the opening, the dive, the
fall, the meadow and the trees (Jev's likeness 0.393), and a seventh read the film as its director first and laid the
town out to that reading (0.645, Jev 0.406); what it added is in "One take in 3D", "The camera, measured", "The set
laid out for the camera", "The night, and judging faster", "Jev looks", "The opening, the dive, the fall, the meadow"
and "The director's reading" below, and in `directing.md`. Read `reading-shots.md`
first for the tools that read a shot as code.

## The loop

0. **Read it as its director and its motion designer first** (`directing.md`): what each shot is for, where the eye
   goes, why the camera moves and how it eases; `moodreel direct` asks Jev those questions. Build to the reading.
1. **Cut the reference into its scenes to the frame.** A mean-luma or mean-colour timeline at the video's own frame
   rate gives every cut, flash and phase change exactly (a montage slot of 5 frames, a one-frame inverted flash, a
   glitch in three phases of 5, 3 and 5 frames). Write them as the scene table; `moodreel compare --shots` scores the
   same windows.
2. **Build every scene once**, then score: `moodreel compare <reference> <remake> --shots scenes.json --json pass.json`.
   Work on the lowest windows and on what the user names, not on what looks worst to you.
3. **Measure the reference's shot before redrawing it**: `moodreel probe <reference> --at t1,t2,... --against <remake>`
   for each window you fix (a film folder renders its stills, a video is read directly). Change the drawing so the
   numbers move toward the reference's, probe again, and render the film only when they agree. Two or three probes
   settle a shot; renders and contact sheets alone don't.
4. **Render, score, compare with the last pass** in one command: `moodreel pass <reference> <film> --shots scenes.json
   --name p21 --against passes/p20` renders, scores every window in parallel, reads the camera and writes a contact
   sheet (under two minutes for a 64 s film). With `--jev --allow-text-upload` (opt-in, `TYPESAFE_API_KEY`), Jev
   ranks the windows and names the kind of fix each needs (camera, framing, light, motion, detail) in about four
   seconds: it reads numbers only, so look at the top windows' pictures before changing them. With `--vision
   --spec look.json --allow-image-upload` Jev also looks at frames of both films (`moodreel look`): where each named
   subject sits in the remake against the reference, in px, the checks that disagree (legends on the keys, the
   critter's face, the title's name) and how alike each pair is. Keep a change only if its window rose:
   `moodreel compare ... --json pass2.json --against pass1.json --sheet pairs.jpg` prints each window's change and the
   mean's, and lays the reference beside the remake at each window's middle, worst first (read the sheet before
   probing: the scores say where, the sheet says what). Make a side-by-side video (reference above remake, the
   reference's audio) for the user's eyes.

## What to measure, and what it fixed

| The eye said | The numbers said | Build |
|---|---|---|
| "a curved wall of cards turning" | fourteen card centres and widths at two times fit a camera inside a cylinder (3 px rms): focal 1095 px, cards 0.42 rad wide and 0.48 apart, the camera dollying from 0.9 to 0.23 radii behind the axis while turning 0.43 rad, easing out | each card cut into vertical strips, every strip mapped onto its own projected corners; one affine per card shows no foreshortening (0.55 to 0.75) |
| "the ring isn't intense enough" | lit share 19 % of the frame, mean colour (33, 15, 32), streaks 3-8 px wide and 20-90 long (run lengths); the blue ring 9.5 % lit, growing 1 + 4 s² and gone in 0.35 s | additive streaks matched on those numbers: the first "more intense" pass lit 54 % and was 3.5 times too bright (0.60 to 0.67) |
| "a beam of cells on a dithered ground" | the whole frame is 16 px ASCII cells starting at the frame's corner: every dark cell a grey ring (p95 91 on a ground of 19), the beam white cells with a dot on a grey grid, its edge one hot pink cell with a cross, then one dark pink | the ground drawn as cells too, rings as bright as measured (0.43 to 0.84) |
| "the slash slowly pushes in" | its angle every 0.1 s: 28.3 to 22.3 deg from vertical by a smoothstep over 13.7-15.35 s, 316 px long +6.5 px/s; the ground a clean disc with 12 px glyph cells outside it (dot, slash, cross, ring), 4 px scan lines of ±1.7 | the slash turned, not scaled; the glyph vignette and scan lines as a still texture (0.38 to 0.57) |
| "icons on tilted tiles" | the tile 790 px centred at (485, 478); the line of text 869 px wide at x 978; the name 118 px, out of focus, at the bottom left | the layout set from the boxes (0.48 to 0.59) |

## Weight, masks and focus (the fourth round)

The user named what still read wrong: "some letters bold" and "a transparent mask not picked up". Both were there in
the numbers once they were read for them.

| The eye said | The numbers said | Build |
|---|---|---|
| the type looks right | `probe --region` round each line: the prompt is Medium (strokes 8 px at 72 px high, ours 6 at 60), "starts with" 800 not 600, the year 550, and "slop" a light mono (250) wide apart, 400 px a glyph, that only looks heavy once drawn as dots; ours had set it bold | each line set to its measured stroke and box; "slop" 0.52 to 0.67 |
| the prompt card is a tilted card | the prompt grows a quarter from its first letter to its last and its baseline falls 0.049: a page in perspective, vanishing point near (-5000, 260); the card's lower half is soft, the heading beyond it sharp | the page drawn flat, projected by tiles through a homography (with its inverse to place the heading where it was measured), a soft copy under a sharp one cut by a gradient along the baseline (0.53 to 0.67) |
| black between scenes | a region's mean frame by frame shows short plateaus: 25.5 for six frames between 48 and 2.4. Zoomed, the plateau is the last picture shown through line glyphs (a dot, a slash, a cross by brightness, 10 px, dim grey ink); a dim eye under 12 px cells with a grey ring in every dark cell; a black disc over a field of glyphs round the slash | a `lines` cells mode and the measured ring ramp; each mask for its measured frames ("lives on" 0.74 to 0.84) |

- **Look for masks where the picture seems empty.** A transition frame that reads black or flat in a contact sheet
  is often a picture through a glyph screen at a tenth of its light: plot a region's mean at the video's frame rate
  and zoom into any plateau. The same screens recur through a film (here the beam, the dim eye, the end card).
- **A soft copy under a sharp one halos** unless the soft copy is cut by the inverse of the sharp one's mask.
- **The scorer has a sampling limit.** `compare` reads 320 x 180: a 12 px grid falls on its Nyquist rate, and a
  1 px shift of the grid moved one window's detail from 1.2 to 2.1 (0.84 to 0.55). Align the grid with `probe`'s
  phase, then try the neighbouring pixel phases on that window and keep the best.
- **A still window's flow is noise**: the white end card's flow read 0.5, 0.33 and 0.0 over three renders with no
  change to it. Don't chase it.

## Light, speed and the lines over everything (the fifth round)

The user pointed at an ellipse of light on the white card and at a ring that "turns much slower than the original".
Both were measurable; a third thing, which nobody named, was worth more than either.

| The eye said | The numbers said | Build |
|---|---|---|
| a halo on the white card | the reference over a remake without it, both blurred to 32 x 18, fits an elliptical lens light per look (light = gain x (1 - strength x d^power), corners at half); on the card itself a flat plateau at 237-242 that only falls off at its edges, as if the card clipped before the lens darkened the frame | the lens as an elliptical gradient over the look, then a halo added after it to the page alone; the prompt 0.67 to 0.71 |
| the ring is too slow | `probe` turn: a 3 x 3 flow grid. The streaks run +900 px/s along the bottom, -150 to -300 along the top and +450 across the middle: their speed crosses zero at y 470 while the outline's middle is at 650 | a field turning on 2:1 ellipses about a pivot above the middle, at about 1 rad/s, seen through an elliptical window (the blue ring: the same through a ring-shaped window); the ring 0.67 to 0.75 |
| nothing | `probe` scan: a 4 px row rhythm of 5.5 levels on the year, 10 on the light prompt looks, 1.7 on the end card; ours had none | rows 2 and 3 of every 4 darkened per scene, set so the rhythm comes out at the measured level: the year 0.64 to 0.79, the sentence 0.51 to 0.67, the icons 0.59 to 0.68; the mean 0.613 to 0.646 |

- **Scan lines are a texture of the whole film.** Read the 4 px rhythm in every scene, and its phase: "BUT" and
  "Great" had a rhythm out of phase with the others, from their cells and dither; lining them added nothing but
  busyness and cost score.
- **Two layers that share an alpha must be added, not stacked.** Drawing a soft copy (masked by 1 - m) and a sharp
  copy (masked by m) one over the other lets the ground through where both are partly transparent: a band of sky
  across the card. Add them on their own canvas ('lighter'), then lay the sum down.
- **Tiles mapped through a homography need a few pixels of overlap**, or the ground shows through their seams as a
  row of specks along the perspective.
- **A turning thing's centre is where its speed crosses zero**, not the middle of its outline. Read it before
  building the turn.

## One take in 3D (the second film)

A continuous camera through three sets (a desk, a world, the desk at night), lit by a time of day, the world grown by
shaders: three.js scenes into an HDR target with depth, depth of field gathered from the depth, the 2D layers on top.
Nothing in the first film's rules was wrong here; these were new.

| The eye said | The numbers said | Build |
|---|---|---|
| the critter lands, then hops over the keyboard | the reference's critter fills 17-20 % of the width on open desk, nothing between it and a low camera, the dim monitor a dark band behind; ours filled 45 %, behind the keyboard | the landing moved beside the keyboard and the camera back to the distance the width gives (width / (share x 2 tan(fov/2) x aspect)); assemble 0.31 to 0.60, the hop 0.43 to 0.68 |
| the desk goes blue while the voxels pour | lit share 57 %, mean (47, 46, 59), corners 70 / middle 87; ours 24 %, a hot pool | a broad directional "screen light" over the desk instead of a spotlight |
| it falls through the sky | the reference: a teal sea far below, a pink horizon a quarter down, the critter below the horizon; ours showed the land a second early | a set of its own (sea, dawn dome, clouds), the camera above the critter looking down at it; the white 0.45 to 0.78, the fall 0.27 to 0.55 |
| the town goes up | at 36.6 s the reference has five houses; ours had thirty | the clones march slower (each house is built when its clone arrives); the aerial 0.36 to 0.54 |
| the night | the reference (31, 49, 61), teal; ours (48, 44, 35), warm from a town light | the warm fill down to a third, the moon and sky bluer |

- **A one-take film has phases, not cuts.** `compare` finds only its hard cuts (two here). Write the windows from
  frames labelled with their own time every 0.5-2 s (a tiled `fps=0.5` sheet shows t = 1, 3, 5 ..., not 0, 2, 4).
- **Where the camera stands decides most windows.** The big gains were the camera and the subject put where the
  reference has them (size in frame gives distance), not materials. Read the reference's layout first: what fills
  the frame, what is between the camera and the subject, what is behind it.
- **A key moves its neighbours' windows.** A keyframed path bends around every key: one settling key took a
  neighbouring window from 0.54 to 0.48. Score every camera change with `--against` and keep it only where the sum
  rose. A look target that jumps from a near subject to the horizon overshoots the frames before it: hold the key.
- **Look at the frames between the keys.** A camera between two keys passed through houses (black frames at 49,
  51 and 53 s); keep it above the ground at least.
- **The shadow pass ignores a material's vertex code.** Instances grown in `onBeforeCompile` cast their full-size
  shadows unless `customDepthMaterial` grows them too: the river came out as tiles of shadow from the grass that
  covered it before it was cut, the valley darkened by mountains that had not risen.
- **Shrinking to zero on one axis leaves a footprint.** Houses not yet built showed as coloured rectangles: collapse
  an instance that has not started to a point.
- **Walls read grey under a hemisphere light.** Sideways faces get half the sky; the reference's walls are white.
  Add albedo x 0.22 as a daytime fill on walls and roofs.
- **Make the story's numbers true and let one schedule drive both.** 128 clones build 128 houses: each clone goes to
  its house, and the house rises when the clone arrives, so the town grows at the march's pace.

## The camera, measured (the second round of the 3D film)

The maker looked at the first round and named four things: the logo in the first frame not aligned, every camera move
wrong, the keyboard not like the reference's, too few hops. The stills had matched; the motion had not. Each one was
measurable, and the camera most of all.

| The eye said | The numbers said | Build |
|---|---|---|
| every camera move is wrong | `moodreel camera <reference> --against <remake>`, window by window: the reference pushes in 34 %/s over the keyboard where ours held still, turns right 17 degrees where ours turned left, pulls out 65 %/s over the crowd, rolls 74 degrees through a whip | the reference's track as `camera-data.js`, and the camera moved by it (`kit/follow.js`) between a few anchors; windows moving as the reference's from about none to 18 of 36, the flow agreement's median 0.20 to 0.33, the mean 0.586 to 0.607 |
| the logo isn't aligned | the reference's mark on a 30 px grid (not 40), 16 x 10 cells from (196, 126): a 12 x 8 body, an arm a side on rows 4-5, four legs on rows 8-9; the name 697 px wide on baseline 268, the subtitle on 354; the conversation's lines 5 and 7 px off | the stand-in on the same grid and footprint with a face of its own, the name set to the measured width by letter spacing (a stand-in name of another length), the lines moved; typing 0.88 to 0.90, the reply 0.87 to 0.94 |
| the keyboard is wrong | a tenkeyless layout with keys of their real widths (shift, enter, space, the arrow and page clusters with their gap), sculpted caps with legends; one key 1/2.3 of the critter's width (ours 1/3.4, a grid of equal squares); the glow leaking up the caps' sides | the layout built from rows of key widths, tapered caps, an atlas of legends, the glow on the caps' lower part; each glass cap a diorama of its own (village, forest, lake, fields, maze, desert, town) |
| too few hops | the critter's lowest point, normalised by its size, frame by frame: nine hop tops in 8-14.4 s, about every half second with rests, three high ones; ours five | the hops as [start, end, from, to, height] with rests between; eight read back |

How the camera was rebuilt, and what the measurement can't see:

- **Read the picture's motion, then turn it into the camera's.** The picture moving x px right (at 1920 wide) is the
  camera turning left by atan(x / f), f = 540 / tan(fov / 2); growing is moving along the view. `moodreel camera`
  prints both, per window, beside the remake's, and names what is off ("pans the other way", "pushes in where the
  reference pulls out", "doesn't roll"). Re-measure after every change; it is the camera's `--against`.
- **Drive the camera by the track, anchor it sparsely.** `follow(MOTION, anchors, end, { own })` adds the measured turn
  and push to a smooth path through anchors. Every anchor adds its own turn on top (the difference it must make up):
  print what each adds before rendering, and put anchors where the measured path already goes. One that fought it
  (a 165-degree turn, a 244-unit jump) turned the window's pan the other way.
- **Let the measurement place the world.** The measured path swept the camera west after the bank, so the sunset went
  west too, through a notch cut in the mountains for it; the night was turned to look west across the town. Cheaper
  than fighting the reference's moves, and it keeps them.
- **Integrate the push along the path.** A push moves the camera along its view at that moment; after a long pull-back
  a pan turns where the camera stands, not where it began (computed in one go from the start, the camera orbited
  its first position).
- **Don't sum the measured roll.** A motion-blurred whip reads as a turn it never undoes; summed, the roll reached 96
  degrees by the end with the reference's horizon level. Roll comes from the anchors.
- **What the fit can't see, key by hand.** A crane or a sideways move whose tilt keeps the subject in frame nets out
  (the reference rose over the crowd, the fit read it still); a dark frame full of falling pieces reads as the pieces
  (the pour read "still" while the camera pushed in and tilted down). Look at those windows' frames and key them.
- **The remake's fit has the same blind spot.** Ours read "still" over the keyboard where the camera turned 17
  degrees: the critter held in the centre, the keys blurred out by the depth of field. Keep the background sharp
  enough for the fit, and for the eye.
- **A camera move needs the set laid out for it.** The reference's camera turns right as its critter hops right and
  toward it; laid out otherwise, the measured turn looked away from the subject. Put the subject's path along the
  measured look and its distance where the push leaves it.

## The set laid out for the camera (the third round of the 3D film)

The maker named the shots still off: the keyboard's camera, the night grass, the lights coming on, the swoop. Then:
"the landing is on a hillside, and the building's details don't match". The score hardly moved (0.607 to 0.608); the
pictures did. The third round was about what stands in front of the camera.

| The eye said | The reference showed | Build |
|---|---|---|
| the landing is on a hill | a grassy dome against the sunrise, a few puffs of cloud high up; the stomp throws turf, earth and flowers; then the critter walks down the slope | the valley floor raised into a dome (columns of fractional height, steps hidden under the grass), a burst of 160 cubes from round its feet, a dozen small clouds high and wide (a dense low layer read as a ceiling) |
| the building doesn't match | a road and lamps first; each house a white scaffold, walls rising from the ground, critters on the roof as stepped tiles go on; doors, timber bands, chimneys | the scaffold as the house's twelve edges, taken down after (a per-voxel take-down time, in the shadow pass too); walls grown from the ground, windows appearing as the wall reaches them; a stepped roof of four courses; the clone rides up the rising walls and stands on the roof, then hops down to the door |
| the keyboard's camera | the critter lands on the desk in front of the keyboard (a dark band behind it); the measured pull-back and rise reveal the keys as it jumps over them; then it hops back across them toward the camera | that layout, the camera from the measured track, each hop landed on the camera's view at the distance that gives the critter the reference's size there |

- **Lay the subject along the measured camera.** Work out where the measured path looks at each landing time, and put
  the subject there, at the distance its size in the reference gives. Moving the camera to the subject puts your turns
  back on top of the reference's.
- **A change of aim between anchors is not a push.** Anchors that look at different distances made the path move the
  camera forward between them; it flew past its subject at 24 s. Only the measured growth moves the camera
  (`kit/follow.js`).
- **Ask what the reference's camera reveals.** A pull-back with a tilt up while the subject jumps away is a reveal:
  the keyboard comes into the foreground. Read the move, then place the set so it reveals the same thing.
- **The fit can't read a tracked subject on a dark ground**, the remake's or the reference's: the desk windows read
  "still" though the camera turns 17 degrees. There, judge the pictures side by side; don't chase the number.
- **Build things the way the reference builds them.** Dropping finished houses into place read as wrong although
  each house matched. Scaffold, walls, roof and the critters on it are the shot.

## The night, and judging faster (the fourth round of the 3D film)

The maker asked for the two weakest windows, the lights coming on and the night grass, and then said the loop was
too slow: could Jev (their typed-judgment API) speed up the judging and make it more accurate?

| The eye said | The reference showed | Build |
|---|---|---|
| the night windows are wrong | both from a grassy rise on the river bank just north of the town: lights on from over the rise, the lamp line receding on the right and lighting lamp by lamp, the lit town beyond; then down on the ridge, one critter close, a few small ones across the slope | the rise added (gentle: steeper, its 1-unit columns showed as terraces of grass), the lamp line carried past the town onto it, one critter in eight sent up at dusk, the hero a few steps in front of the camera; night grass 0.30 to 0.55, lights on 0.39 to 0.51 |
| the loop is too slow | a pass was five commands and minutes of reading 36 windows of numbers and sheets | `moodreel pass` (render, parallel scoring, camera, sheet; scoring 90 s to 16 s) and opt-in `moodreel triage` / `pass --jev`: Jev ranks the windows and names the fix in 4 s |

- **A shot's setting is part of its camera.** Both night shots failed on where the camera stood (inside the town,
  then behind a crest), not on how it moved. Find the place the reference films from, then build it.
- **Look down on a crowd.** A camera at critter height among them filled the frame with backs; the reference looks
  down from above a crest, with only the hero close.
- **Ask Jev relative questions.** Asked whether each window "would be accepted as the same shot", Jev said no to 34
  of 36: a code-drawn remake differs everywhere. Given the film's medians and quartiles and asked how each window
  sits among the others, it ranked them from 0.22 to 0.93 and named fixes that matched what the eye had found.
- **Jev judges numbers, not pictures.** It points at the windows to look at and the kind of fix; the pictures
  decide what to change. Its answers are cached per request, so re-running a pass costs only the changed windows.

## Jev looks: the subjects where the reference has them (the fifth round of the 3D film)

The maker said the keys had no digits, the product had been renamed, and asked for pixel-level accuracy before speed,
with Jev's new vision reading the frames (the film made with its makers' leave, so frames may be sent).

| The eye said | Jev saw | Build |
|---|---|---|
| no digits on the keys | legends on the reference's keys 0.84-0.88, the remake's 0.05-0.30 | the legends were drawn but hidden: caps and legends both transparent, neither writing depth, the caps drew last. A render order (legends after caps) |
| the name changed | "reference claude (1.00), remake other (1.00)" | the name, the model line and the logo as the reference has them, the logo cell for cell off its frame (12 x 8, one-by-two eyes, the grid a shade darker, a faint glow), no bloom on the flat terminal's type: typing 0.58 to 0.85 in Jev's likeness |
| (pixel-level) | the critter 100-300 px from the reference's in most desk windows; its face slits most of the time and ^ ^ when it stands happy; facing the camera | `moodreel track` boxes the critter, keyboard, plant, monitor, space bar and Esc in the reference 8 times a second, with its face and its heading; `kit/lock.js` solves camera and critter onto those boxes: the critter 99 to 21 px, the plant 512 to 26, the keyboard 102 to 37 (RMS of the box sides, px at 1080); the face and heading read off the track |

Over p21 to p27: compare's mean 0.614 to 0.637, Jev's likeness 0.332 to 0.383, its disagreeing checks 17 to 3.

- **Box the reference's subjects, then solve the remake onto them.** `moodreel track --spec look.json --js
  track-data.js` gives every subject's box through time; `kit/lock.js` moves the camera (5 numbers) and the subjects
  that may move (along their axes) as little as it takes to put them there, one moment at a time. The report (`node
  render/render.mjs report <film>`) prints each subject's error before and after; read it before rendering.
- **Compare what the frame shows.** A box of a keyboard's corners, half out of the frame, read as filling it; compare
  the visible part (clipped at the near plane, its hull clipped to the frame), and push out of the frame what Jev does
  not see in the reference: the monitor and keyboard behind the critter at 8.5 s went.
- **A critter stands on something.** Moved freely it matched its box to 9 px, then floated off the keys and, once, 12
  units under the desk. On its surface (x and z; height only in the air) it matches to 15-20 px and stays standing.
- **A lock must not add motion.** Corrections smoothed over 0.12 s made the camera swim (2.7 times the reference's
  motion in the keyboard of worlds); over 0.3 s, with each moment held near the one before, it holds. Where camera and
  critter could trade places, a moment solved alone picked either, and the critter flew 31 units in a second.
- **Boxes don't see a mirror.** The keyboard of worlds matched box for box from the front left; the reference films it
  from the front right. Two keys (the space bar and Esc) give the turn; use them where the remake's keyboard agrees
  with the reference's (before the three-quarter view this wider keyboard's Esc is further out, and chasing it turned
  the camera onto the desk).
- **Lay the base camera near the reference's first.** A lock fine-tunes; from a base 30 units off (a measured pull-out
  run free) it found a camera looking down at the desk. Key the base off the reference's frames, then lock.
- **Ask Jev about the eyes and the heading, frame by frame.** "Slits or ^ ^" and "toward the camera, partly or wholly
  to one side" gave the critter's face and turn through the film; a partial turn is about 17 degrees.
- **Colour inside the box.** The critter read (198, 33, 3) inside Jev's box in the reference and (253, 108, 41) in
  the remake; a deeper, more saturated base brought it to (207-221, 41-47, 19-22).

## The opening, the dive, the fall, the meadow (the sixth round of the 3D film)

The maker named the moments: the logo turns and becomes cubes at 5 s; at 7 s it lands between the keyboard and the
computer; at 18 s the keyboard is brighter, a few keys light, and it jumps from the space bar; it flips on the way down
and lands on a hill, not a plain, filmed from elsewhere; the trees are not real enough; the modelling is rough; and over
the town, lock to the houses and the crowd.

| The eye said | The reference showed | Build | Moved |
|---|---|---|---|
| turns, cubes | the logo's cells become cubes from the bottom row up and the block turns a third round on the screen; the cubes pour down the screen and land formed by 7.0 s | cubes 2 x 2 x 12 a cell, darker toward their edges (the grid), little glow so faces shade | assemble 0.61 to 0.72 |
| lands between keyboard and computer | a small critter alone on a blue-grey desk, no keys before it | landing behind the keyboard; filmed along the gap from the side (the only 28-unit view without keys); the landing lit blue-grey | (desk hop fell: see below) |
| keys light, from the space bar | keys lit from below a few at a time, round the critter, each just before it turns to glass; onto the space bar, up, over and down into it, legs up | per-key glow in the 0.65 s before its turn, a ring from the critter; the last hops to the space bar with a forward flip; the light warm white, its mean colour measured | keys glow 0.63 to 0.67, dive 0.62 to 0.64 |
| flips, falls, lands on a hill | out of the dive upside down, turned over, swaying; green land far below, a horizon a third down; a rounded crest, short grass, a longer lens | the flip; a meadow, not a sea; the drop tuned by the window's measured speed; a crest; a smooth meadow over the columns; turf thrown at the landing | fall 0.52 to 0.64 (Jev 0.23 to 0.48), sunrise 0.67 to 0.71 (Jev 0.48 to 0.58) |
| trees, rough models | conifers of small cubes in stacked tiers, ragged, four greens; round trees of light greens; the crowd a 4 x 8 block that bends into arcs, salmon in the sun | trees from 0.42-unit cubes; the crowd's slots as arcs; the clones' and the hero's colours measured in the world | march 0.48 to 0.53, clones row Jev 0.41 to 0.46 |

Over p27 to p31: compare 0.637 to 0.635, Jev's likeness 0.383 to 0.393, its disagreeing checks 3 to 1.

- **Lock only what is laid out like the reference.** Locked to Jev's boxes of the town, its nearest house, the river and
  the crowd, the swoop lost its motion (0.31 times the reference's: the lock held the town still while the reference's
  camera flies) and Jev rated the march, the building and dusk further off. The town and the crowd stood elsewhere than
  the reference's; a camera cannot fix that. Rebuild the layout (here the crowd's arcs), then lock. The tracks stay:
  they say where the layout is wrong.
- **A scattered subject is a cloud, not a solid.** A river's or a town's hull fills the frame; their box is the box of
  their points inside it (`{ cloud: points }` in `kit/lock.js`).
- **What the camera must not show places it.** The landing between the keyboard and the monitor, filmed a fifth of the
  frame wide with no keys before it, has one camera: along the gap. Jev's "not seen" and the critter's measured size
  settle it, not the eye.
- **One object, one colour per light.** The same critter reads (198, 33, 3) under the desk's light and (110-150, 23-42,
  2-4) in the sun, its clones (211, 127, 79) from above at noon: measure each inside Jev's boxes and set each scene's.
- **A falling camera zooms the ground.** From 70 units the meadow below zoomed fourfold and the window read 2.2 times
  the reference's motion; from 38, 0.6 times. Tune the drop by the measured speed.
- **A meadow of 1-unit columns is terraced.** A dome of columns shows rings of steps; a smooth surface a third of a unit
  over them, and everything standing on it, is the reference's meadow.
- **Keep the remake under version control.** One slip (a write that truncated the file it was reading) emptied the
  film's main script; it was rebuilt from earlier reads and checked against the lock's report, number for number. Give
  the film folder a git history, or snapshot it before every pass.
- Still off: the desk hop (0.63 to 0.53: the critter's size against the keyboard does not allow the reference's
  framing on both sides of it), the white flash (0.79 to 0.62), sunset and the night grass (the town and its
  crowd stand elsewhere).

## The director's reading (the seventh round of the 3D film)

The maker asked for the town and the crowd laid out as the reference's, the camera locked by Jev after, a shorter lawn
on the landing slope, and a director's and a motion designer's way of reading the film: "pure visual copying without a
layer of understanding can hardly flow like the original; what we want to distill later is the style, not a copy".
`moodreel direct` asks Jev a director's questions per window; the reading, the method and what it found are in
`directing.md`. Built to it: the town in rows along a longer river (packed four deep it read as "a field of repeated
things"), the sun setting down the river (the reference's leading line to the sun), the camera keyed at the reading's
beats (between anchors 4.5 s apart the measured tilt had turned it into the grass), the lock only over the aerial
build. Compare 0.635 to 0.645, Jev's likeness 0.393 to 0.406.

- **Read before you lay out.** The scores said "different picture"; the reading said "a leading line where yours is a
  pattern", "high where yours is the ground", "slows into the view where yours is steady". Those are fixable.
- **A lock follows the layout, never leads it.** With the town in rows the aerial build locked well (0.54 to 0.68, at
  the reference's speed); the march next to it, whose line still runs elsewhere, got worse (Jev 0.40 to 0.15).
- **Motion has a shape.** Most of Jev's remaining notes are about it: accelerations into reveals, decelerations into
  holds. Anchors joined by one smooth curve glide at one pace.

## Rules that came out of it

- **Does the reference's grain move?** `probe` prints `still`: the least change between neighbouring frames. Here it
  was 0.00 everywhere: a fixed grain. A remake whose grain boils over it reads as motion going another way;
  `compare` names it ("grain boils where the reference's holds still"). Seed the post's grain with a constant.
- **Cells have a period and a phase.** `probe` reads both from the row and column profiles. Draw the grid from the same
  origin (in a GPU pass, y counts from the bottom: offset by the height mod the cell), and read the glyph ramp per
  scene: which glyph the dark, middle and bright cells carry, and their colours. Often the whole frame is cells, not
  only the subject.
- **Brightness is a share, not an impression.** Match lit share and mean colour first, then the size distribution of
  the marks (horizontal and vertical run lengths of lit pixels), then their colour across the frame.
- **Slow moves are curves.** Read an angle, a length or a box every 0.1 s and fit the curve (a smoothstep, an ease-out
  with its span) instead of guessing a rate. `compare`'s flow sign says when a move runs the wrong way.
- **Fit a camera when things move in depth.** Measure a handful of objects at two times and solve the camera by least
  squares; when two cameras fit equally, pick the one whose foreshortening matches the nearest object's taper.
- **White needs exposure.** A post with a tone shoulder greys a white ground: lift exposure until the centre reads
  as the reference's (249 here), and check the corners separately.
- **Names and characters as the reference has them, when the maker may use them.** A remake made with its makers'
  leave keeps the product's name, its logo cell for cell and its character: a renamed title reads as another film,
  and Jev says so ("reference claude (1.00), remake other (1.00)"). Without that leave, brands, logos, posts and
  footage become code-drawn stand-ins of the same size, colour and layout. The reference's audio is for timing and the
  side-by-side review only.
