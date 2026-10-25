# Remaking a film shot by shot

A remake is matched to its reference shot by shot, then measured, then fixed where it is furthest off. Drawn from
what the eye reads, its first pass is a different film; each step below came from closing that gap on a 16 s launch
teaser (ASCII glitch, 20 scenes, 60 fps), where three rounds took the mean window score from 0.49 to 0.59, and the
last round the five shots it worked on from 0.38-0.60 to 0.57-0.84. Read `reading-shots.md` first for the tools that
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
