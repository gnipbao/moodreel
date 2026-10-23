// Risograph Print, filled in from styles/risograph/STYLE.md §5-§6 for this film.
import { clamp, tween, step } from './core.js';

// §5: drawings on twos, the camera (locked here) on ones; prints don't fade: wipes, cuts, a roller sweep
export const ON = 2, FPS = 24;
export const MOTION = {
  enter: { ease: 'power2.out', duration: 2.0 },          // the sun's rise
  sweep: { ease: 'none', duration: 0.5 },                // a plate arriving or lifting under the roller
  kick: { px: 12, decay: 0.08, period: 0.2 },            // registration kick on an accent, gone in ~0.25 s
};
export const drawn = t => step(t, FPS / ON);              // time for anything drawn
export const enter = (t, at, dur = MOTION.enter.duration) => tween(drawn(t), at, dur, MOTION.enter.ease);
export const sweep = (t, at, dur = MOTION.sweep.duration) => clamp((t - at) / dur);
export const kick = (t, at) => (t < at ? 0 : MOTION.kick.px * Math.exp(-(t - at) / MOTION.kick.decay) * Math.cos((2 * Math.PI * (t - at)) / MOTION.kick.period));
