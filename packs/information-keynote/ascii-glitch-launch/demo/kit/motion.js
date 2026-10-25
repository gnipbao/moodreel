// Written by `moodreel kit` from the project's measurements. Edit freely: the comments say where each came from.

import { tween, stagger, value } from './core.js';

// measure/motion.json grammar
export const MOTION = {
  "enter": {
    "ease": null,
    "duration": 0.15,
    "count": 15,
    "unread": "no ease was read with confidence; take it from STYLE.md or the references by eye",
    "vocabulary": {
      "drift-x": 2,
      "rise": 1,
      "rise+fade": 1,
      "scale-pop+rise-in": 1,
      "scale+drift-x+rise": 1,
      "slide-in+rise-in": 1,
      "drift-x+rise": 1,
      "draw-on": 1,
      "scale-pop": 2,
      "drop-in": 1,
      "scale-pop+slide-in": 1,
      "wipe-in": 2
    },
    "seen": {
      "classes": {
        "out": 1
      },
      "of": 15
    }
  },
  "exit": {
    "ease": null,
    "duration": 0.104,
    "count": 10,
    "unread": "no ease was read with confidence; take it from STYLE.md or the references by eye",
    "vocabulary": {
      "rise-out": 1,
      "wipe-out": 2,
      "scale-pop": 3,
      "scale-pop+slide-out": 1,
      "scale+fade": 1,
      "slide-out": 1,
      "scale+drift-x+sink": 1
    }
  },
  "move": {
    "ease": null,
    "duration": 0.171,
    "count": 44,
    "unread": "no ease was read with confidence; take it from STYLE.md or the references by eye",
    "vocabulary": {
      "move-y": 12,
      "scale": 2,
      "scale-pop": 2,
      "scale+move-x+move-y": 1,
      "scale+move-x": 2,
      "scale-pop+move-x+move-y": 2,
      "move-x+move-y": 3,
      "scale-pop+move-x": 3,
      "scale-pop+move-y": 3,
      "slide-in": 5,
      "drop-in": 2,
      "slide-in+move-y": 1,
      "move-x": 2,
      "slide-in+drop-in": 2,
      "slide-in+rise-in": 1,
      "scale+move-y": 1
    },
    "seen": {
      "classes": {
        "out": 4
      },
      "of": 44,
      "curve": "bezier(0.433,1.198,1.0,0.927)",
      "curve_class": "out"
    }
  },
  "count": {
    "ease": null,
    "duration": 0.275,
    "count": 3,
    "unread": "no ease was read with confidence; take it from STYLE.md or the references by eye",
    "vocabulary": {
      "count": 3
    },
    "seen": {
      "classes": {
        "out": 1
      },
      "of": 3
    },
    "format": "#"
  },
  "stagger": null,
  "letters": null,
  "hold": 0.1,
  "shot": 0.1,
  "transitions": {
    "cuts": 65,
    "dissolves": 2,
    "dips": 0,
    "dissolve": 0.033,
    "dip": null,
    "dip_colours": []
  },
  "density": 0.212,
  "on": 1,
  "camera": {
    "panx": {
      "count": 1,
      "duration_s": {
        "n": 1,
        "median": 0.533,
        "p25": 0.533,
        "p75": 0.533
      },
      "eases": [
        "none"
      ],
      "range": {
        "n": 1,
        "median": 44.905,
        "p25": 44.905,
        "p75": 44.905
      }
    },
    "pany": {
      "count": 1,
      "duration_s": {
        "n": 1,
        "median": 0.558,
        "p25": 0.558,
        "p75": 0.558
      },
      "eases": [
        "none"
      ],
      "range": {
        "n": 1,
        "median": 136.04,
        "p25": 136.04,
        "p75": 136.04
      }
    },
    "zoom": {
      "count": 1,
      "duration_s": {
        "n": 1,
        "median": 0.067,
        "p25": 0.067,
        "p75": 0.067
      },
      "eases": [
        "sine.in"
      ],
      "range": {
        "n": 1,
        "median": 0.023,
        "p25": 0.023,
        "p75": 0.023
      }
    }
  },
  "loop": null,
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
