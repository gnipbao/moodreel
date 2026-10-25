// Tidepool: the edit, in beats of the score (120 BPM, a beat 0.5 s), and every event the picture and the sound effects
// share: the typing, the glitches, the flashes, the mark. No DOM here: sfx.mjs imports it too.
import { SCORE } from './score.js';

export const BEAT = SCORE.beat_s;
export const b = i => i * BEAT;                                // beat index from 0 -> seconds
export const DUR = 32 * BEAT;                                  // 8 bars

// the shots: [from beat, to beat, kind]. Phrases change on beats; the montages run on their own frame clock inside.
export const SHOTS = [
  [0, 1.5, 'year'], [1.5, 3.2, 'tracked'], [3.2, 4, 'field'], [4, 7, 'console'], [7, 8.6, 'sentence'], [8.6, 9, 'dashes'],
  [9, 11, 'wall'], [11, 12.2, 'but'], [12.2, 12.5, 'mosaic'], [12.5, 14, 'radar'], [14, 15.2, 'guess'],
  [15.2, 16, 'harbours'], [16, 17, 'tunnel'], [17, 18.5, 'good'], [18.5, 20, 'data'], [20, 22.4, 'ring'],
  [22.4, 23.5, 'liveson'], [23.5, 26, 'name'], [26, 28, 'mark'], [28, 31, 'end'], [31, 32, 'black'],
].map(([a, z, kind], i) => ({ i, kind, t0: b(a), t1: b(z), a, z }));
export const shotAt = t => SHOTS.find(s => t >= s.t0 && t < s.t1) ?? SHOTS[SHOTS.length - 1];
export const shot = kind => SHOTS.find(s => s.kind === kind);

// what is typed, from when, how fast (characters a second)
export const TYPED = {
  year: { text: 'In 2025', t0: b(0.1), cps: 26 },
  request: { text: "Show tomorrow's tides at Kestrel Bay", t0: b(3.9), cps: 36 },
  sentence: { text: 'Every boat can read the sea.', t0: b(7.05), cps: 150 },
  radar: { text: 'Most still guess.', t0: b(12.6), cps: 45 },
  guess: { text: 'guess', t0: b(13.95), cps: 30 },
  liveson: { text: 'lives on', t0: b(22.45), cps: 34 },
  name: { text: 'Tidepool.', t0: b(23.55), cps: 40 },
};
// each letter's time, for the key ticks
export const letterTimes = ({ text, t0, cps }) => [...text].map((c, i) => [c, t0 + i / cps]);

// the glitches (start, frames at 60 fps) and the inverted flashes
export const GLITCHES = [[b(3.2), 24], [b(8.6), 12], [b(12.2), 9], [b(14), 6], [b(26), 6], [b(26.33), 6]];
export const FLASHES = [[b(14.75), 6], [b(15.0), 3], [b(21), 4]];
// the year rolls 5 -> 6 between these times; the year breaks into cells at this time
export const ROLL = [b(0.3), b(1.4)];
export const BREAK = b(2.6);
