// Swiss Motion Graphics, filled in from styles/swiss-motion/STYLE.md §5-§6 for this film.
import { clamp } from './core.js';
import { bezier } from './eases.js';

// §5: two curves only: a precise ease for snaps, linear for lines being drawn and for the exception
const snapCurve = bezier(0.7, 0, 0.2, 1);
export const BPM = 120, BEAT = 60 / BPM;
export const MOTION = {
  enter: { ease: 'cubic-bezier(.7,0,.2,1)', duration: 0.75 * BEAT },     // a dotted eighth, landing on the beat
  exit: { ease: 'cubic-bezier(.7,0,.2,1)', duration: 0.5 * BEAT },
  stagger: { interval: BEAT / 2, order: 'left-to-right' },              // eighth notes
  hold: BEAT * 2,
};
// a snap that lands at `arrive`: it starts one note value early
export const snap = (t, arrive, dur = MOTION.enter.duration) => snapCurve(clamp((t - (arrive - dur)) / dur));
export const lin = (t, at, dur) => clamp((t - at) / dur);
export const enter = (t, at) => snap(t, at + MOTION.enter.duration);
export const exit = (t, at) => snap(t, at + MOTION.exit.duration, MOTION.exit.duration);
