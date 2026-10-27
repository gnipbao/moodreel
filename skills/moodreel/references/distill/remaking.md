# Remaking a film shot by shot

A remake is matched to its reference shot by shot, then measured, then fixed where it is furthest off. Drawn from
what the eye reads, its first pass is a different film; each step below came from closing that gap on a 16 s launch
teaser (ASCII glitch, 20 scenes, 60 fps), where five rounds took the mean window score from 0.49 to 0.65 (median
0.69), and the third round the five shots it worked on from 0.38-0.60 to 0.57-0.84. A second film, a 64 s one-take 3D
voxel world (a critter leaves a terminal, builds mountains, a river, a town of 128 houses, then lights it), went from
0.53 to 0.59 (mean of 36 windows) in seven passes, then to 0.61 in a second round on what its maker named, and a third
round rebuilt the landing, the building and the desk to the reference; what it added is in "One take in 3D", "The
camera, measured" and "The set laid out for the camera" below. Read `reading-shots.md`
first for the tools that read a shot as code.

## The loop

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
4. **Render, score, compare with the last pass** window by window, and keep a change only if its window rose:
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
- **Stand-ins, not copies.** Brands, logos, posts and footage become code-drawn stand-ins of the same size, colour and
  layout; the reference's audio is used for timing and the side-by-side review only.
