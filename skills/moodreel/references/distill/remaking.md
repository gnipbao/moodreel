# Remaking a film shot by shot

A remake is matched to its reference shot by shot, then measured, then fixed where it is furthest off. Drawn from
what the eye reads, its first pass is a different film; each step below came from closing that gap on a 16 s launch
teaser (ASCII glitch, 20 scenes, 60 fps), where five rounds took the mean window score from 0.49 to 0.65 (median
0.69), and the third round the five shots it worked on from 0.38-0.60 to 0.57-0.84. Read `reading-shots.md` first for the tools that
read a shot as code.

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
4. **Render, score, compare with the last pass** window by window, and keep a change only if its window rose. Make a
   side-by-side video (reference above remake, the reference's audio) for the user's eyes.

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
