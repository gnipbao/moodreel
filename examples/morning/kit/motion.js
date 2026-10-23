// Pictogram Motion, filled in from styles/pictogram-motion/STYLE.md §5-§6 for this film.
import { tween } from './core.js';

// §5: one tempo; every shot starts on a beat and every key action lands on one. Exponential ease-out for entrances,
// exponential in-out for whips; type enters by mask slide-up, the second line ~0.08 s later; the figure arrives as
// bands sliding into register from alternating sides
export const BPM = 120, BEAT = 60 / BPM;
export const MOTION = {
  enter: { ease: 'expo.out', duration: 0.5 },
  pop: { ease: 'expo.out', duration: 0.4 },
  band: { interval: BEAT / 4, travel: 260 },
  second: 0.08,
  act: { ease: 'sine.inOut', duration: BEAT, lift: 20 },
};
export const land = (t, arrive, m = MOTION.enter) => tween(t, arrive - m.duration, m.duration, m.ease);
