# Treatment: first-save

Style: 16-bit Pixel RPG (pixel-rpg, styles/pixel-rpg). Read its STYLE.md first; DEMO.md and the demo source only after this treatment exists.

## Brief

A 10 s opening for a story about starting out: a hero walks out at dusk, says two lines, and the game saves.
1920×1080 (320×180 native, ×6), 24 fps, silent. Words: THE ROAD STARTS HERE. / ONE STEP AT A TIME. / GAME SAVED.
It exists to show pixel art in Moodreel: kit/pixel.js, its 5×7 font, palette tables, protected UI colours.

## Three structures

1. A battle as a metaphor for a first day (party, enemy, windows; needs more than 10 s to read).
2. A side-scroll at dusk: a walk, a dialog box, the palette holding the change, a save window.
3. A save-file screen with three slots (a system speaking; little picture).

Chosen: 2, the style's "side-scroll with parallax" and "hold while the palette changes", in its plainest form.

## Beats

- 0.0–7.0 s: the camera scrolls at 24 px/s on integer pixels, far mountains at a quarter, near hills at half; the
  hero walks at 8 fps.
- 0.8 s: the dialog box slides up in 0.3 s (ease-out, integer px); 1.0 s and 2.3 s its two lines type at 20
  characters a second; 6.2 s it slides out.
- 6.4–6.9 s: night falls by palette steps (each scene colour one place down its ramp, twice), stars come out; the
  windows use protected duplicates, so they don't darken.
- 7.0 s: the hero stops and breathes (1 px); 7.5 s GAME SAVED slides down in a thin top window and holds to 10 s.

## Not the demo

Structure: one walk and a save, not a life told in eras. Opening: a dithered sky already scrolling. Signature: the
palette step to dusk while the windows keep their colours. Ending: a save window, not a credits roll.
