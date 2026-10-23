# Treatment: tide-town

Style: Low-poly Isometric Island (lowpoly-island, styles/lowpoly-island). Read its STYLE.md first; DEMO.md and the demo source only after this treatment exists.

## Brief

A 10 s title piece: a small island builds itself out of a faceted sea, then lives (a mill turns, the sea moves), and
a quiet title. 1920×1080, 24 fps, silent. Words: Tide Town. It exists to show 3D in Moodreel: kit/three.js with
three.js copied into the film, an orthographic camera, every object set from t.

## Three structures

1. A growth chart as a town: one district per data point (the style's data use; needs a data set).
2. An island rising out of the sea: tiles, then houses, then trees, then life, then a title.
3. Night on the island with searchlight beams (needs the style's beam ribbons and bloom).

Chosen: 2, the style's arrival curves in the order land, buildings, trees, life.

## Beats

Slots of 1/8 s; at most one piece per slot.

- 0.2–2.0 s: 37 hex columns rise from below, centre first (a cubic ease up, then a damped-sine overshoot).
- 2.25–3.25 s: five houses drop, one per two slots, and squash on landing (volume kept).
- 3.75–5.25 s: twelve trees pop, one per slot (scale 1 − e^(−9s)·cos(16s), about 25 % overshoot).
- 5.0–5.5 s: the mill pops; from 5.5 s its blades turn.
- Throughout: the sea's facets move (summed sines on the CPU, from t); the camera orbits slowly at a fixed
  elevation, the orthographic projection never changes.
- 7.5 s: the title opens left to right; hold to 10 s.

The style's post (GTAO between the tiles, haze, a light tilt-shift, bloom) needs three.js add-ons the kit doesn't
ship yet; soft shadows from one key light carry the shapes instead.

## Not the demo

Structure: one island in one take, not a schedule of districts on the music. Opening: an empty sea. Signature: the
rise-and-overshoot of the tiles. Ending: a turning mill and a title.
