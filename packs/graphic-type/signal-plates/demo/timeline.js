// Battery Low: the edit, in beats of the score (128 BPM, a beat 0.469 s), and every event the picture and the sound
// effects share: the falling value, the typing, the slams. No DOM here: sfx.mjs imports it too.
import { AUDIO, LYRICS } from './music-data.js';

export const BEAT = 60 / AUDIO.bpm;
export const b = i => i * BEAT;                          // beat index from 0 -> seconds
export const DUR = 52 * BEAT;                            // 13 bars

// the lyric as sung (score.json melody): find a word near a beat
export const WORDS = LYRICS.flatMap(l => l.words);
export const word = (w, near) => {
  const x = WORDS.filter(x => x.w === w).sort((p, q) => Math.abs(p.start - b(near)) - Math.abs(q.start - b(near)))[0];
  if (!x) throw new Error(`no sung word ${w} near beat ${near}`);
  return x;
};
export const line = (first, near) => LYRICS.find(l => l.words[0].w === first && Math.abs(l.start - b(near)) < BEAT);

// the shots: [from beat, to beat, kind]. Cuts land on beats (the whip on the off-beat before its beat).
export const SHOTS = [
  [0, 2, 'cursor'], [2, 6, 'field'], [6, 7, 'band'], [7, 8, 'readout'],
  [8, 10, 'cell'], [10, 11, 'band'], [11, 12, 'spark'], [12, 14, 'drain'], [14, 15, 'dim'], [15, 16, 'idle'],
  [16, 19.5, 'prompt'], [19.5, 20, 'whip'], [20, 22, 'follow'], [22, 23, 'readout'], [23, 24, 'band'],
  [24, 26, 'form'], [26, 28, 'formClose'], [28, 30, 'stamp'], [30, 31, 'readout'], [31, 32, 'band'],
  [32, 34, 'hook'], [34, 35, 'band'], [35, 36, 'drain'], [36, 38, 'hook'], [38, 39, 'readout'], [39, 40, 'retype'],
  [40, 42, 'hook'], [42, 43, 'band'], [43, 44, 'spark'], [44, 46, 'hook'], [46, 47, 'readout'], [47, 48, 'last'],
  [48, 52, 'black'],
].map(([a, z, kind], i) => ({ i, kind, t0: b(a), t1: b(z), a, z }));
export const shotAt = t => SHOTS.find(s => t >= s.t0 && t < s.t1) ?? SHOTS[SHOTS.length - 1];

// the battery, falling a percent at a time on the song's events
const DROPS = [[0, 20], [7.5, 19], [10, 18], [11, 17], [14, 15], [18, 12], [22, 10], [24, 9], [28, 8], [30, 7], [34, 6],
  [36, 5], [38, 4], [42, 3], [44, 2], [46, 1]].map(([i, v]) => [b(i), v]);
export const value = t => DROPS.filter(([at]) => at <= t).pop()?.[1] ?? 20;
export const dropAt = t => DROPS.filter(([at]) => at <= t).pop()?.[0] ?? 0;   // when the current value arrived
export const DROP_TIMES = DROPS.slice(1).map(([at]) => at);

// the hooks: each "SAVE IT" (score bars 9-12)
export const HOOKS = [32, 36, 40, 44].map((a, k) => ({ k, save: word('SAVE', a), it: word('IT', a + 1) }));

// typed text: each letter's time. A sung token types across its note; the rest types on sixteenths.
export const PLEA = ['save', 'your', 'work'].map((w, k) => { const x = word(w, 16 + k); return { text: w, t0: x.start, t1: x.end }; });
export const RETYPE = ['save', 'it', 'save', 'it'].map((w, k) => ({ text: w, t0: b(39) + k * BEAT / 4, t1: b(39) + (k + 0.6) * BEAT / 4 }));
export const REQUEST = (() => { const a = word('please,', 24), z = word('time', 26); return { text: 'please, more time', t0: a.start, t1: z.end }; })();
export const FOOTNOTE = { text: 'autosave: off', t0: b(49), t1: b(49) + 13 * BEAT / 8 };
export const letterTimes = ({ text, t0, t1 }) => [...text].map((c, i) => [c, t0 + (t1 - t0) * i / Math.max(1, text.length)]);

// the spark runs up the charging cable from beat 5 and reaches the terminal on beat 47
export const sparkU = t => Math.min(1, Math.max(0, (t - b(5)) / (b(47) - b(5))));
