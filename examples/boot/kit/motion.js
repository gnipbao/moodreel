// ASCII CRT, filled in from styles/ascii-crt/STYLE.md §5-§6 for this film.
import { tween } from './core.js';

// §5: characters jump cell to cell; machine typing is even and fast; only the grid scale (the camera), CRT physics
// and particles move continuously. §6: power on/off and clear screen are the cuts
export const MOTION = {
  type: { perChar: 0.01 },                                  // machine output: even and fast
  title: { perChar: 0.05 },                                 // a title typed with key clicks
  push: { ease: 'power2.inOut', duration: 1.6, to: 5 },     // the grid scale: cells grow five times
  power: { ease: 'power2.out', duration: 0.25 },
  off: { ease: 'power2.in', duration: 0.15 },
  afterglow: 0.12,                                          // tau, seconds
};
export const typed = (t, at, text, per = MOTION.type.perChar) => text.slice(0, Math.max(0, Math.floor((t - at) / per + 1e-6)));
export const power = (t, at) => tween(t, at, MOTION.power.duration, MOTION.power.ease);
export const off = (t, at) => tween(t, at, MOTION.off.duration, MOTION.off.ease);
