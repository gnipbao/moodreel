// Written by `moodreel kit` from the project's measurements. Edit freely: the comments say where each came from.

import { tween, stagger, value } from './core.js';

// measure/motion.json grammar
export const MOTION = {
  "enter": {
    "ease": "power3.out",   // director (STYLE.md §5): ease-out; half the entrances overshoot ~5 %: enter() alternates with overshoot_ease
    "overshoot_ease": "back.out(1.2)",
    "duration": 0.62,   // power3.out settles early: 0.62 reads as the references' 0.45 (moodreel motion-check on the sketch)
    "count": 213,
    "unread": "no ease was read with confidence; take it from STYLE.md or the references by eye",
    "vocabulary": {
      "scale+drift-x+rise": 1,
      "drop-in": 3,
      "slide-in+drop-in": 8,
      "slide-in": 14,
      "scale-pop+slide-in+rise-in+fade": 4,
      "rise+fade": 2,
      "scale-pop": 10,
      "scale-pop+sink": 5,
      "fade": 27,
      "scale-pop+drift-x+drop-in": 4,
      "drift-x+sink": 8,
      "scale-pop+drift-x": 11,
      "rise": 7,
      "turn": 1,
      "slide-in+rise-in": 11,
      "sink": 3,
      "scale": 3,
      "drift-x": 7,
      "scale+slide-in": 1,
      "drift-x+fade": 1,
      "scale-pop+sink+fade": 2,
      "scale-pop+drift-x+sink": 4,
      "wipe-in": 3,
      "scale-pop+drift-x+rise-in": 1,
      "drift-x+drop-in": 1,
      "drift-x+rise": 8,
      "scale-pop+drift-x+sink+turn": 1,
      "scale-pop+drift-x+sink+fade": 3,
      "scale-pop+drift-x+fade": 3,
      "scale-pop+drift-x+rise": 6,
      "scale+drift-x+sink": 3,
      "grow-y": 1,
      "drift-x+sink+turn+fade": 1,
      "sink+fade": 4,
      "drift-x+sink+fade": 2,
      "scale-pop+slide-in": 2,
      "scale-pop+slide-in+rise-in": 4,
      "scale+drift-x+sink+fade": 2,
      "scale+sink+fade": 1,
      "draw-on": 3,
      "scale-pop+rise-in": 1,
      "rise-in": 5,
      "scale+rise": 1,
      "slide-in+fade": 1,
      "scale-pop+drift-x+rise+fade": 2,
      "scale-pop+slide-in+sink": 1,
      "drop-in+fade": 1,
      "scale-pop+slide-in+rise": 1,
      "scale+drift-x+rise+fade": 1,
      "rise-in+fade": 1,
      "scale-pop+slide-in+drop-in": 3,
      "scale+drift-x": 2,
      "scale-pop+slide-in+sink+fade": 1,
      "drift-x+rise+fade": 1,
      "slide-in+turn": 1,
      "turn+fade": 1,
      "scale+drift-x+fade": 1,
      "scale-pop+rise": 2
    },
    "seen": {
      "classes": {
        "out": 13,
        "in": 4,
        "linear": 2,
        "out+oscillate": 3,
        "inOut": 4,
        "out+overshoot": 1
      },
      "of": 213,
      "curve": "bezier(0.151,1.272,0.988,0.924)",
      "curve_class": "out"
    }
  },
  "exit": {
    "ease": "power1.in",   // director: exits leave faster, accelerating (power2.in hid most of its travel in its last frames)
    "duration": 0.33,   // power1.in over 0.33 s reads as the references' 0.296
    "count": 164,
    "unread": "no ease was read with confidence; take it from STYLE.md or the references by eye",
    "vocabulary": {
      "scale+drift-x": 4,
      "slide-out+turn": 1,
      "scale": 15,
      "scale+slide-out": 2,
      "scale-pop": 15,
      "scale-pop+sink": 1,
      "drift-x+rise+fade": 3,
      "scale+slide-out+drop-out": 2,
      "scale-pop+rise+fade": 2,
      "drift-x+sink+fade": 1,
      "drift-x+fade": 2,
      "drop-out": 1,
      "drift-x": 6,
      "collapse-y": 2,
      "slide-out+drop-out": 3,
      "scale-pop+fade": 7,
      "slide-out": 5,
      "rise-out": 3,
      "wipe-out": 4,
      "drift-x+rise": 3,
      "scale+sink": 4,
      "scale-pop+drift-x+sink": 2,
      "scale-pop+rise": 4,
      "scale+drift-x+rise": 12,
      "scale+rise": 3,
      "scale-pop+drop-out": 2,
      "slide-out+rise-out": 9,
      "scale-pop+slide-out": 3,
      "scale-pop+drift-x+rise+fade": 1,
      "scale-pop+rise-out": 1,
      "scale+sink+fade": 1,
      "scale+fade": 1,
      "fade": 18,
      "scale+drift-x+sink": 3,
      "scale+drift-x+rise+fade": 1,
      "scale-pop+sink+fade": 1,
      "drift-x+sink": 2,
      "scale-pop+slide-out+rise": 1,
      "drift-x+rise+turn": 1,
      "scale+rise-out": 1,
      "slide-out+rise-out+turn": 1,
      "scale-pop+drift-x+rise": 1,
      "rise": 1,
      "scale-pop+drift-x+fade": 1,
      "scale+drift-x+fade": 1,
      "scale-pop+drop-out+fade": 1,
      "clip-slide": 1,
      "scale-pop+slide-out+fade": 1,
      "drop-out+fade": 1,
      "draw-off": 1,
      "scale+rise+fade": 1
    },
    "seen": {
      "classes": {
        "inOut": 2,
        "out": 3,
        "out+oscillate": 2,
        "in": 4
      },
      "of": 164,
      "curve": "bezier(0.435,-0.108,0.986,0.487)",
      "curve_class": "in"
    }
  },
  "move": {
    "ease": "back.out(1.3)",   // director: moves are short and two thirds overshoot ~6 %
    "duration": 0.183,
    "count": 711,
    "unread": "no ease was read with confidence; take it from STYLE.md or the references by eye",
    "vocabulary": {
      "scale": 69,
      "scale-pop": 150,
      "move-y": 58,
      "move-x+move-y": 62,
      "scale-pop+move-x": 47,
      "scale-pop+move-x+move-y": 50,
      "scale-pop+move-y": 44,
      "scale-pop+slide-in": 8,
      "move-x": 69,
      "scale+move-x": 16,
      "scale+move-x+move-y": 21,
      "scale+move-y": 6,
      "scale-pop+slide-in+drop-in": 2,
      "rise-in": 10,
      "scale+slide-in": 3,
      "drop-in": 4,
      "scale+slide-in+rise-in": 1,
      "scale-pop+move-x+drop-in": 2,
      "scale-pop+move-x+rise-in": 1,
      "slide-in+drop-in": 9,
      "scale+move-x+rise-in": 3,
      "slide-in": 34,
      "move-x+rise-in": 2,
      "scale-pop+drop-in": 1,
      "scale-pop+rise-in": 5,
      "slide-in+rise-in": 19,
      "scale+rise-in": 1,
      "move-x+move-y+turn": 1,
      "scale-pop+turn": 2,
      "turn": 2,
      "scale+slide-in+drop-in+turn": 1,
      "move-x+turn": 1,
      "scale-pop+slide-in+rise-in": 5,
      "scale+slide-in+move-y": 1,
      "scale-pop+slide-in+move-y": 1
    },
    "seen": {
      "classes": {
        "out": 24,
        "linear": 3,
        "inOut": 6,
        "out+oscillate": 15,
        "out+overshoot": 6,
        "in": 12
      },
      "of": 711,
      "curve": "bezier(0.141,0.473,0.335,0.977)",
      "curve_class": "out"
    }
  },
  "count": {
    "ease": "power2.inOut",   // counters roll fast, in mono
    "duration": 0.108,
    "count": 71,
    "unread": "no ease was read with confidence; take it from STYLE.md or the references by eye",
    "vocabulary": {
      "count": 68,
      "count-in": 3
    },
    "seen": {
      "classes": {
        "inOut": 1
      },
      "of": 71
    },
    "format": "#"
  },
  "stagger": {
    "interval": 0.231,   // STYLE.md §5: an eighth note at the reference's tempo (motion.json read 1.04 s between whole groups)
    "order": "unordered"
  },
  "letters": null,
  "hold": 0.233,
  "shot": 0.45,
  "transitions": {
    "cuts": 48,
    "dissolves": 5,
    "dips": 1,
    "dissolve": 0.05,
    "dip": 0.15,
    "dip_colours": [
      "#3f3e3e"
    ]
  },
  "density": 0.586,
  "on": 1,
  "camera": {
    "panx": {
      "count": 1,
      "duration_s": {
        "n": 1,
        "median": 0.092,
        "p25": 0.092,
        "p75": 0.092
      },
      "eases": [
        "none"
      ],
      "range": {
        "n": 1,
        "median": 37.206,
        "p25": 37.206,
        "p75": 37.206
      }
    }
  },
  "loop": {
    "period": 0.904,
    "scale": 0.528,
    "x": 53.75
  },
  "particles": {
    "shot": 35,
    "count": 34,
    "radius_px": 2.3,
    "speed": {
      "p10": 22.7,
      "median": 64.9,
      "p90": 432.1
    },
    "vx": [
      -430.3,
      -1.3
    ],
    "vy": [
      -87.8,
      47.4
    ],
    "direction_deg": -166.7,
    "spread_deg": 48.9
  },
  "beat": null
};

const role = r => ({ ...MOTION?.[r], ease: MOTION?.[r]?.ease ?? 'power2.out' });

// progress (0-1) of an element's entrance / exit / move that starts at `at`; i staggers it within a group
export const enter = (t, at, i = 0) => tween(t, MOTION?.stagger ? stagger(at, MOTION.stagger.interval, i) : at,
  role('enter').duration ?? 0.5, i % 2 === 0 && MOTION?.enter?.overshoot_ease ? MOTION.enter.overshoot_ease : role('enter').ease);
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
