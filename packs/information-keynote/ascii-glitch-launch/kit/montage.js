// The re-dressed object: one thing shown in a new dress every 5-6 frames (0.083-0.1 s) while what it says carries on,
// on its own frame clock, not the beat's. Slots shorter than 5 frames read as noise, longer than 8 as a slideshow.
//
//   import { slot, slotOf } from './kit/montage.js';
//   const k = slot(t, 1.35) % LOOKS.length;          // every GLITCH.slot frames from 1.35 s
//   const k = slotOf(t, [1.35, 1.433, 1.533]);        // or on measured cuts
import { GLITCH } from './tokens.js';

export const slot = (t, t0, frames = GLITCH.slot, fps = GLITCH.fps) => Math.max(0, Math.floor((t - t0) * fps / frames + 1e-6));
export const slotOf = (t, cuts) => Math.max(0, cuts.filter(x => x <= t + 1e-6).length - 1);
// a glitch lasts 2-12 frames and lands on a cut: true while t is inside one of [start, frames] (at the film's fps)
export const during = (t, glitches, fps = GLITCH.fps) => glitches.some(([s, n]) => t >= s && t < s + n / fps);
