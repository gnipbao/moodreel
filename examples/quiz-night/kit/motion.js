// Fill in from STYLE.md §5 (motion) and §6 (camera and editing).
import { tween } from './core.js';
export const MOTION = { enter: { ease: 'power3.out', duration: 0.5 }, exit: { ease: 'power2.in', duration: 0.35 } };
export const enter = (t, at) => tween(t, at, MOTION.enter.duration, MOTION.enter.ease);
export const exit = (t, at) => tween(t, at, MOTION.exit.duration, MOTION.exit.ease);
