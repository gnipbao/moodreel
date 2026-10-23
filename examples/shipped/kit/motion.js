// Dark Keynote, filled in from styles/dark-keynote/STYLE.md §5-§6 for this film.
import { tween } from './core.js';

// §5: on ones, everything lands on the beat; fast-out with one small overshoot (back, s ~ 1.3); spawns are short
// (0.2-0.3 s); nothing just fades: disappearing is a CRT-off squash
export const BPM = 120, BEAT = 60 / BPM;
export const MOTION = {
  enter: { ease: 'back.out(1.3)', duration: 0.25 },
  expand: { ease: 'back.out(1.3)', duration: 0.3 },
  exit: { ease: 'power2.in', duration: 0.15 },
  toast: { ease: 'power2.out', duration: 0.16, rise: 16 },
};
// a move that lands on `arrive`: it starts its own duration early
export const land = (t, arrive, m = MOTION.enter) => tween(t, arrive - m.duration, m.duration, m.ease);
export const go = (t, at, m = MOTION.exit) => tween(t, at, m.duration, m.ease);
