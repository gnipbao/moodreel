// Written by `moodreel kit` from the project's measurements. Edit freely: the comments say where each came from.

import { tween, stagger, value } from './core.js';

// measure/motion.json grammar
export const MOTION = {
  "enter": {
    "ease": null,
    "duration": 0.35,
    "count": 73,
    "unread": "no ease was read with confidence; take it from STYLE.md or the references by eye",
    "vocabulary": {
      "scale-pop": 7,
      "slide-in+rise-in": 2,
      "drift-x": 6,
      "scale+drop-in": 1,
      "slide-in+drop-in": 4,
      "scale-pop+drift-x+rise": 5,
      "slide-in+drop-in+turn": 1,
      "slide-in+rise-in+turn": 1,
      "turn": 3,
      "scale-pop+slide-in+drop-in": 1,
      "slide-in": 3,
      "scale-pop+rise-in": 1,
      "scale-pop+drift-x": 4,
      "scale-pop+rise": 1,
      "scale-pop+slide-in": 1,
      "drop-in": 2,
      "scale": 5,
      "scale+rise-in": 1,
      "rise-in": 1,
      "rise": 1,
      "scale+sink": 2,
      "drift-x+rise": 3,
      "scale+drift-x": 1,
      "sink": 4,
      "scale-pop+rise-in+turn": 1,
      "scale-pop+drift-x+sink": 1,
      "per-letter+fade": 4,
      "wipe-in": 2,
      "turn+fade": 1,
      "fade": 1,
      "scale+rise": 1,
      "grow-y": 1
    },
    "seen": {
      "classes": {
        "in": 2,
        "out+oscillate": 1
      },
      "of": 73,
      "curve": "bezier(0.629,0.091,0.842,-0.155)",
      "curve_class": "in"
    }
  },
  "exit": {
    "ease": null,
    "duration": 0.267,
    "count": 93,
    "unread": "no ease was read with confidence; take it from STYLE.md or the references by eye",
    "vocabulary": {
      "scale+drift-x+turn": 1,
      "scale-pop+drift-x": 5,
      "scale-pop": 8,
      "drift-x": 3,
      "scale+drift-x": 3,
      "drop-out": 3,
      "slide-out+drop-out+turn": 3,
      "scale+slide-out+drop-out": 2,
      "fade": 9,
      "draw-off": 3,
      "scale+drift-x+rise+fade": 1,
      "wipe-out": 4,
      "scale-pop+fade": 4,
      "sink": 1,
      "scale": 15,
      "scale+slide-out": 3,
      "scale+rise-out": 1,
      "scale-pop+rise-out+fade": 1,
      "rise+fade": 1,
      "scale-pop+sink": 1,
      "scale+sink": 2,
      "slide-out+drop-out+fade": 1,
      "slide-out": 1,
      "scale+rise": 2,
      "drift-x+rise": 4,
      "collapse-y": 1,
      "drift-x+sink": 1,
      "scale-pop+slide-out+rise-out+fade": 1,
      "rise-out": 1,
      "scale-pop+drop-out": 1,
      "per-letter+fade": 1,
      "drop-out+turn": 1,
      "drift-x+drop-out+turn": 1,
      "scale+drift-x+sink+turn": 1,
      "scale+drift-x+rise": 1,
      "rise": 1
    },
    "seen": {
      "classes": {
        "inOut": 1,
        "out+oscillate": 3,
        "in": 1
      },
      "of": 93,
      "curve": "bezier(0.6,1.638,0.0,0.344)",
      "curve_class": "out+oscillate"
    }
  },
  "move": {
    "ease": null,
    "duration": 0.217,
    "count": 154,
    "unread": "no ease was read with confidence; take it from STYLE.md or the references by eye",
    "vocabulary": {
      "scale-pop+move-x": 6,
      "scale-pop": 36,
      "scale-pop+move-x+move-y": 16,
      "move-y": 6,
      "scale-pop+move-y": 13,
      "scale": 18,
      "slide-in+rise-in": 2,
      "move-x": 17,
      "scale+move-x": 9,
      "drop-in": 1,
      "scale+move-x+move-y": 6,
      "scale-pop+move-y+turn": 1,
      "move-x+move-y": 10,
      "scale-pop+slide-in+drop-in": 1,
      "scale+move-y": 2,
      "rise-in": 1,
      "slide-in": 3,
      "scale+move-x+rise-in": 1,
      "scale+rise-in": 1,
      "scale+drop-in": 1,
      "scale-pop+slide-in+rise-in": 1,
      "scale+slide-in+drop-in": 1,
      "scale-pop+turn": 1
    },
    "seen": {
      "classes": {
        "out": 3,
        "in": 4,
        "out+oscillate": 4
      },
      "of": 154,
      "curve": "bezier(0.402,0.0,0.898,0.046)",
      "curve_class": "in"
    }
  },
  "count": {
    "ease": null,
    "duration": 0.433,
    "count": 7,
    "unread": "no ease was read with confidence; take it from STYLE.md or the references by eye",
    "vocabulary": {
      "count": 7
    },
    "seen": {
      "classes": {
        "linear": 1
      },
      "of": 7
    },
    "format": "#"
  },
  "stagger": null,
  "letters": {
    "interval": 0.0667,
    "order": "left-to-right"
  },
  "hold": 0.25,
  "shot": 2.933,
  "transitions": {
    "cuts": 13,
    "dissolves": 3,
    "dips": 0,
    "dissolve": 0.167,
    "dip": null,
    "dip_colours": []
  },
  "density": 0.589,
  "on": 1,
  "camera": null,
  "loop": {
    "period": 1.967,
    "scale": 0.534
  },
  "particles": null,
  "beat": null
};

const role = r => ({ ...MOTION?.[r], ease: MOTION?.[r]?.ease ?? 'power2.out' });

// progress (0-1) of an element's entrance / exit / move that starts at `at`; i staggers it within a group
export const enter = (t, at, i = 0) => tween(t, MOTION?.stagger ? stagger(at, MOTION.stagger.interval, i) : at,
  role('enter').duration ?? 0.5, role('enter').ease);
export const exit = (t, at, i = 0) => tween(t, MOTION?.stagger ? stagger(at, MOTION.stagger.interval, i) : at,
  role('exit').duration ?? 0.4, role('exit').ease);
export const move = (t, at) => tween(t, at, role('move').duration ?? 0.6, role('move').ease);
// a number counting from `from` to `to`, starting at `at`, on the references' counting curve (print it as
// MOTION.count.format says: '#,###' groups thousands, '#.#' keeps one decimal)
export const count = (t, at, from, to) => value(t, at, role('count').duration ?? 1.2, from, to, role('count').ease);
// an ambient loop, -1..1, at the references' period (MOTION.loop also has how far they bob, pulse or breathe)
export const loop = (t, period = MOTION?.loop?.period ?? 2, phase = 0) => Math.sin(2 * Math.PI * (t / period + phase));
// the time of beat n on the references' grid (n may be fractional: 2.5 is the off-beat after beat 2)
export const beat = n => (MOTION?.beat?.phase ?? 0) + n * (MOTION?.beat?.period ?? 0.5);
