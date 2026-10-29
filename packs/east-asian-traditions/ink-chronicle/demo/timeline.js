// 黄河: the edit, in beats of the score (72 BPM, a beat 0.833 s), and every event the picture and the sound share. No DOM
// here: sfx.mjs imports it too.
import { SCORE } from './score.js';

export const BEAT = SCORE.beat_s;
export const b = i => i * BEAT;
export const DUR = SCORE.duration;

export const SHOTS = [[0, 4, 'source'], [4, 8, 'course'], [8, 12, 'gorge'], [12, 16, 'falls'], [16, 20, 'flood'], [20, 28, 'delta'],
  [28, 32, 'end']].map(([a, z, kind]) => ({ kind, t0: b(a), t1: b(z) }));
export const shotAt = t => SHOTS.find(s => t >= s.t0 && t < s.t1) ?? SHOTS[SHOTS.length - 1];

export const T = {
  water: b(1.25), melt: b(2.4),                    // 水 lands, then runs
  bends: [b(5.2), b(6.2), b(7.2)],                 // places pop in as the stream reaches them
  blow: b(10),                                     // 壶口 lands; the camera lurches forward
  surge: b(14.6),                                  // into the cut
  breach: b(18),                                   // 决 lands, the dike bursts
  places: [b(20.4), b(23.4), b(26)], mouth: b(26), // the length counting by reaches; the mouth reached
  last: b(28), drift: b(29.6),                     // 海 lands, then becomes the sea
};
export const PLACES = ['兰州', '河套', '壶口'];
export const LENGTH_KM = 5464;
