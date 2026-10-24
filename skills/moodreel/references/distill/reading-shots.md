# Reading shots as code

A frame that looks right can still be built wrong. Remaking a film from stills, then comparing with its source code,
showed what reading by eye gets wrong (docs/research/VISION-TO-CODE.md): the stills-built version ran darker (0.82 of
the reference's light), more saturated (1.25x the accent's area), with less line (0.79x) and glow (0.63x), slower
(0.63x), and moving in directions unrelated to the reference (flow agreement 0.11). It drew a few dozen canvas strokes
where the source drew 10^4-10^5 GPU segments, faked in 2D what was a 3D scene, and missed ray-marching, engraving hatch
and type projected through the camera. All of that can be read off the video before writing a line.

## The tools

- `moodreel dossier <video> [--shots shots.json] --out dir`: each shot's motion (pan px/s, zoom %/s, roll and spin
  deg/s, surges, the frame-by-frame track), linework (share of line, width, hatching, orientations), finish (glow,
  colour fringe, grain) and colour (luma, highlights, saturated share), with keyframes, flow arrows and a track chart,
  and technique hints. `moodreel measure` runs it on every video reference: MEASURE.md "Shots read as code".
- `moodreel pose <frame> --points x1,y1,...,x4,y4 [--aspect a] [--fov deg]` (or `--grid` to read coordinates off a
  frame): the 3D camera from a rectangle in the picture: pitch, yaw, roll, distance, field of view.
- `moodreel compare <reference> <remake>`: the score after every pass.

## What the hints mean (calibrated against the source of one film)

| Hint | Fires when | Build with | Reliability |
|---|---|---|---|
| line-heavy | line ≥ 4.5 % of the frame, ≤ 4.5 px wide | GPU lines (`kit/gl.js` lines), or lines a shader draws; budget 10^4-10^5 segments | 3 of 7 hits, false alarms only on shader-drawn lines |
| hatching | ≥ 15 % of the frame is dense parallel line | `hatch`/`engrave`, line width carrying the shade, following the surface | 4 of 9 hits, no false alarms |
| 3D camera | a perspective fit explains ≥ 6.5 % more of the moving lines than a flat one | a 3D scene (`kit/three.js`, or a ray-marched `kit/gl.js` pass) and a camera through it | 6 of 10 hits, 1 of 12 false |
| spin / roll / push / pull / pan / surges | the motion's own numbers | the camera's moves, with their direction and rate | measured |
| bloom / fringe | glow ≥ 0.18, fringe ≥ 0.3 px | HDR colour past 1 and `kit/gl.js` post | measured |

A hint that fires is trustworthy; one that doesn't fire proves nothing (a technique used in a corner of the frame
doesn't register).

## What you see, and what it usually is

| In the picture | Usually | Not |
|---|---|---|
| fine contour lines wrapping organic forms, thicker in the light, forms melting into each other | a signed-distance body ray-marched, smooth union, hatch along surface coordinates | spheres with stripes |
| lines bending continuously into a dark disc with a bright ring, text bent round it, a flipped ghost inside | a per-pixel lens (inverse mapping) in a full-screen pass | a warped 2D grid and circles |
| thousands of thin lines streaming one way | integrated flow lines on the GPU, in 3D through a camera | a few hundred arcs |
| type foreshortened with the floor, grid or trays | glyphs projected through the scene camera, glyph by glyph | a 2D skew |
| parallel lines whose width carries the tone; banknote rosettes | `hatch`, `engrave` in a shader | flat fills with outlines |
| paper with fibres, ink grain, stamp texture | ink on a Canvas layer composited on procedural paper in a shader | a flat paper colour |
| only the accent glows, past white, spilling | HDR colour over 1, bloom over a threshold, a tone shoulder | canvas shadows |
| repeated objects receding into the dark | 3D instances with fog | stacked 2D layers |
| a word written by a moving point | single-stroke fonts drawn along their length | a fill revealed by a mask |

## How to rebuild a shot

1. Run the dossier on the reference. Read the hints, the numbers and the flow arrows before choosing a technique.
2. A 3D shot: read the camera at two or three keyframes with `moodreel pose` (four corners of something rectangular).
   Read the field of view once from the clearest frame and give it for the others; solve the rectangle's aspect
   there too. Measure spacings the same way (project a neighbour through the read camera) rather than by eye.
3. Write the camera from those poses and the frame-by-frame track, landing moves on beats and events. A window's
   median hides a move made in a few frames.
4. Match the totals the eye gets wrong: luma, accent area, amount of line, glow, against the dossier's numbers.
5. Give the shot its detail: a source plate ran about 1,100 lines with several layers (diagram, type, HUD, spark,
   annotations); the small labels and ticks are what makes a frame read as "fine".
6. Render, run `compare` and the dossier on the remake, diff the two dossiers window by window, fix the biggest gap.
   Stop when the score stops rising, and keep the best pass.

## For a style

The pooled "Shots read as code" section of MEASURE.md says which techniques the style lives on and how its camera
moves. Carry them into STYLE.md: §2 names the rendering techniques the hints found (with their share of shots), §3 the
measured luma and accent area as targets, §5 the speed and surges, §6 the camera vocabulary (push, roll, spin, pan,
3D), §10 the kit modules that build them (`kit/gl.js`, `kit/three.js`, `kit/outline.js`).
