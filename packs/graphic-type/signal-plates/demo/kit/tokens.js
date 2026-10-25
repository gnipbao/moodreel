// Written by `moodreel kit` from the project's measurements, then set by the director at gate 1 (DECISIONS.md) and
// STYLE.md: the comments say where each came from. Edit freely.

// intake.json default_size
export const SIZE = [1920, 1080];

// The ladder and the one hue (STYLE.md §3). Hexes from the reference's source (mexicat/pdoom-video, MIT:
// app/src/engine/palette.ts); `colors` is what measure/palette.json read off the compressed video (after its
// vignette and glow): the frame-check compares against those.
export const PALETTE = {
  ground: '#0A0A0B',          // the plate
  panel: '#151517',           // a panel one step lighter
  graphite: '#5E5B57',        // structure, unsung words, hatching
  ash: '#9C978F',             // notes
  bone: '#EEE9DF',            // what is read; the paper of the inverted plates
  signal: '#FF4D12',          // the one hue: the spark, the sung word, the value
  ember: '#FF8A3D',           // its hotter core
  blood: '#C21D0B',           // its shadow
  acid: '#D8FF3C',            // a second accent for one short moment, then gone
  ink: '#EEE9DF',             // the kit's generic "ink": bone
  accent: '#FF4D12',          // the kit's generic "accent": signal
  colors: [
    { hex: '#0e0c0c', area: 0.8412 }, { hex: '#2b1b1a', area: 0.052 }, { hex: '#524e4d', area: 0.0339 },
    { hex: '#3c3333', area: 0.0324 }, { hex: '#7c7572', area: 0.016 }, { hex: '#48241e', area: 0.0145 },
    { hex: '#732f1b', area: 0.0075 },
  ],
};

// Families from DECISIONS.md 3 (kit/fonts, SIL OFL), registered by FACES in kit/signal.js. Sizes are shares of the
// frame height (measure/type.json tiers): hooks 0.158-0.197, lyric lines 0.043-0.071, notes 0.008-0.031.
export const TYPE = {
  display: '"Archivo"',                   // the voice: width 62-125 (font-stretch), weight 100-900
  text: '"Plex Mono"',                    // the machine: tokens, labels, readouts, forms
  serif: '"Cormorant Garamond"',          // the prophetic register (italic), rare
  hook: 0.197, hookSmall: 0.158, line: 0.071, lineSmall: 0.0435, note: 0.0315, small: 0.013, tiny: 0.008,
  title: 0.197, body: 0.071,              // the kit's generic names
  titleWeight: 300, bodyWeight: 300,      // measured light on average; hooks slam in at 800-900
};

// measure/layout.json: left 7.8 %, right 29.5 % (left-weighted), density 0.128; lyric text >= 96 px from the edges
export const LAYOUT = { margin: 0.078, marginRight: 0.295, top: 0.056, bottom: 0.164, align: 'left', density: 0.128, safe: 96 };

// measure/texture.json read grain 0.335 levels ("none": the reference's compression ate it) and vignette 0.666 in the
// kit's measured scale; the finish itself runs in kit/gl.js's post with the source's settings (FINISH).
export const TEXTURE = { grain: 0.335, mottle: 3.355, vignette: 0.666, halftone: null, scanlines: null, edges: 'crisp',
  pixel: null, brush: null };

// The film post (STYLE.md §2; source app/src/engine/post.ts): only orange passes the glow threshold
// kickShake: px at 1920 wide; the reference's kicks shake its frame +1.65 px read at 640 wide (moodreel sync, z 7.4).
// 3 px reads as that in a film whose camera also steps on the beat (5 px read as 2.76 px in the demo).
// kickGlow: exposure gained on a hit; the reference brightens +0.9 levels on a kick, +1.5 on a downbeat (z 6.2, 5.1)
export const FINISH = { bloom: 0.55, bloomThreshold: 0.85, halation: 0.25, ca: 1.2, vignette: 0.35, grain: 0.055, kickShake: 3,
  kickGlow: 0.12 };
