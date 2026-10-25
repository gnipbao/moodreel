// Written by `moodreel kit` from the project's measurements. Edit freely: the comments say where each came from.

// intake.json default_size
export const SIZE = [
  1920,
  1080
];

// measure/palette.json roles, colors
export const PALETTE = {
  "ground": "#070607",
  "ink": "#c6b6bc",
  "accent": "#662c83",
  "secondary": [
    "#131424",
    "#191a43",
    "#5a2b36",
    "#616c82",
    "#b86152",
    "#a37e5c",
    "#bb6193"
  ],
  "colors": [
    {
      "hex": "#070607",
      "area": 0.4817
    },
    {
      "hex": "#131424",
      "area": 0.1273
    },
    {
      "hex": "#191a43",
      "area": 0.0889
    },
    {
      "hex": "#5a2b36",
      "area": 0.0657
    },
    {
      "hex": "#c6b6bc",
      "area": 0.0574
    },
    {
      "hex": "#616c82",
      "area": 0.0479
    },
    {
      "hex": "#b86152",
      "area": 0.0388
    },
    {
      "hex": "#a37e5c",
      "area": 0.0379
    },
    {
      "hex": "#662c83",
      "area": 0.028
    },
    {
      "hex": "#bb6193",
      "area": 0.0264
    },
    {
      "hex": "#ac4757",
      "area": 0.0094
    },
    {
      "hex": "#e7a569",
      "area": 0.0037
    }
  ]
};

// measure/type.json line heights as font sizes (ink = 0.9 em); families are placeholders until the director picks licensed faces
export const TYPE = {
  "title": 0.2233,
  "body": 0.0994,
  "titleWeight": 500,
  "bodyWeight": 500,
  "display": "Inter",
  "text": "JetBrains Mono",
  "hero": 0.201,
  "line": 0.151,
  "phrase": 0.089,
  "label": 0.02
};

// measure/layout.json medians
export const LAYOUT = {
  "margin": 0.0,
  "align": "centre",
  "density": 0.438
};

// measure/texture.json medians (screen and scanline periods in design px)
export const TEXTURE = {
  "grain": 0.52,
  "mottle": 1.29,
  "vignette": 0.0,
  "halftone": {
    "share": 0.25,
    "period_px": 11.6,
    "angle": 28.9
  },
  "scanlines": {
    "share": 0.25,
    "period_px": 4.0
  },
  "edges": "soft",
  "pixel": {
    "scale": 2,
    "native": [
      960,
      540
    ],
    "palette_size": 314,
    "dither": false,
    "palette": [
      "#020202",
      "#020212",
      "#1a020a",
      "#020a1e",
      "#2e0212",
      "#1a021a",
      "#02122e",
      "#021a3e",
      "#3e060e",
      "#0e0a0a",
      "#0e0222",
      "#0e1636",
      "#2a0e1e",
      "#260202",
      "#1e0a26",
      "#4a0a1a",
      "#5a0a1a",
      "#360602",
      "#0a1e4a",
      "#1a0a36",
      "#2e1232",
      "#0e1222",
      "#3a0e1a",
      "#02022a",
      "#1a1a42",
      "#260e0e",
      "#320222",
      "#021212",
      "#1a0646",
      "#22229a",
      "#1a162e",
      "#4a123e"
    ]
  },
  "brush": {
    "spacing": 34.2,
    "angle": 0.202,
    "agreement": 0.14,
    "coverage": 0.94
  }
};


// The style's own numbers (STYLE.md §2-5, LEDGER.md), measured on the reference and its shot-by-shot remake
export const GLITCH = {
  fps: 60,
  slot: 5,                                   // montage frames a slot (5-6 measured, 0.083-0.1 s)
  cells: { ascii: 16, field: 24, dots: 26, lines: 10, rings: 12 },   // cell sizes at 1080p, by use
  track: { red: '#c3263a', violet: 'rgba(110,110,175,0.6)', cyan: 'rgba(80,196,214,0.9)', dot: '#3ddc6a' },
  scan: { studio: 0.095, card: 0.15, dark: 0.05, end: 0.045 },        // rows 2-3 of every 4 darkened: the 4 px rhythm
  grain: 0.075,                              // the post's grain, seeded once: the reference's never moves
  dither: { step: 14, alpha: 0.07 },         // the dark ground's screen door: diagonals crossing every 14 px
  // the studio's light, 16 x 9 cells of grey after the post (the sentence scene with its type taken out)
  studio: [[173, 182, 192, 199, 205, 209, 212, 213, 213, 212, 209, 205, 199, 191, 183, 173],
    [188, 199, 207, 215, 220, 223, 224, 225, 224, 224, 223, 220, 215, 208, 199, 189],
    [200, 210, 219, 224, 225, 226, 227, 227, 227, 227, 226, 225, 224, 219, 210, 200],
    [207, 217, 224, 225, 227, 228, 229, 230, 230, 229, 228, 227, 225, 224, 218, 207],
    [207, 217, 224, 225, 227, 228, 229, 229, 229, 229, 228, 227, 225, 224, 217, 207],
    [207, 217, 224, 225, 226, 228, 229, 229, 229, 229, 228, 227, 225, 224, 217, 207],
    [200, 210, 219, 224, 225, 226, 227, 227, 227, 227, 226, 225, 224, 219, 210, 200],
    [189, 199, 207, 215, 220, 223, 224, 225, 225, 224, 223, 220, 215, 208, 199, 189],
    [173, 182, 191, 199, 205, 209, 212, 213, 213, 212, 209, 205, 199, 191, 182, 173]],
  lens: [1155, 650, 1327, 769, 0.40, 2.35, 1.03],   // a light look's lens: centre, radii, strength, power, gain
  halo: [1000, 820, 800, 260, 0.45],                // a light card's clipped plateau: centre, radii, strength
  glow: { pink: '#e2338f', violet: '#662c83', neon: '#ff5fb8', cyan: '#2aa8e8' },
  ink: { dark: '#1b1b1b', light: '#ffffff' },
};
