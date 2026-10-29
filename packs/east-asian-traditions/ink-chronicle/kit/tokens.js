// Written by `moodreel kit` from the project's measurements. Edit freely: the comments say where each came from.

// intake.json default_size
export const SIZE = [
  1920,
  1080
];

// measure/palette.json roles, colors
export const PALETTE = {
  "ground": "#16130f",
  "ink": "#f4f1e9",
  "accent": "#f06d3d",
  "secondary": [
    "#c9c5be",
    "#3c3832"
  ],
  "colors": [
    {
      "hex": "#f4f1e9",
      "area": 0.6291
    },
    {
      "hex": "#16130f",
      "area": 0.2023
    },
    {
      "hex": "#c9c5be",
      "area": 0.1259
    },
    {
      "hex": "#3c3832",
      "area": 0.0227
    },
    {
      "hex": "#76736e",
      "area": 0.0094
    },
    {
      "hex": "#f06d3d",
      "area": 0.0052
    },
    {
      "hex": "#f3a384",
      "area": 0.003
    }
  ]
};

// measure/type.json line heights as font sizes (ink = 0.9 em); families are placeholders until the director picks licensed faces
export const TYPE = {
  "title": 0.1378,
  "body": 0.0289,
  "titleWeight": 300,
  "bodyWeight": 400,
  "display": "\"InkSong\"",
  "text": "\"InkKai\""
};

// measure/layout.json medians
export const LAYOUT = {
  "margin": 0.0,
  "align": "centre",
  "density": 1.0
};

// measure/texture.json medians (screen and scanline periods in design px)
export const TEXTURE = {
  "grain": 1.83,
  "mottle": 3.44,
  "vignette": 0.517,
  "halftone": null,
  "scanlines": null,
  "edges": "crisp",
  "pixel": null,
  "brush": {
    "spacing": 21.1,
    "angle": 3.033,
    "agreement": 0.53,
    "coverage": 0.64
  }
};


// Ink Chronicle: the style's own values (STYLE.md, LEDGER.md). Defaults and examples, not rules: a film may change any.
export const INK = {
  paper: '#f4f1e9', night: '#16130f', charcoal: '#262421', mist: '#c9c5be', ink: '#16130f', white: '#f4f2ee',
  accent: '#f06d3d', accentFlash: '#fd5e23', accentTile: '#f4683a', accentDeep: '#93352b', accentDark: '#662b20',
  // share of the frame height for each voice (measured: a blow 28-47 %, a title 14 %, a line that addresses the viewer
  // 9-11 %, a quotation 7-11 %, the quiet voice 5-6.7 %, rows 4.5 %, captions 3 %, labels 1.6 %)
  voice: { blow: [0.28, 0.47], title: 0.14, address: [0.09, 0.11], quote: [0.07, 0.11], quiet: [0.05, 0.067], rows: 0.045, caption: 0.03, label: 0.016 },
  // the slam: arriving at 1.6-2.6 times the size, settling in 0.08-0.1 s, its colours split by 36 px on a dark ground
  slam: { from: [1.6, 2.6], settle: [0.08, 0.1], split: 36 },
  // typing: a character every 0.033-0.25 s, each fading in over 0.12-0.2 s and rising 0.15 em
  type: { every: [0.033, 0.25], fade: [0.12, 0.2], rise: 0.15 },
};
