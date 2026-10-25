// The demo's sound effects, from the same timeline as the picture: node sfx.mjs > sfx.json (build.sh does this).
import { b, BEAT, SHOTS, HOOKS, PLEA, RETYPE, REQUEST, FOOTNOTE, DROP_TIMES, letterTimes } from './timeline.js';

const cues = [];
const add = (t, sound, level, extra = {}) => cues.push({ t: +t.toFixed(4), sound, level, ...extra });
for (const typed of [...PLEA, ...RETYPE, REQUEST, { text: '00:04:12', t0: b(24.5), t1: b(25) }, FOOTNOTE])
  for (const [c, at] of letterTimes(typed)) if (c.trim()) add(at, 'key', 0.32, { pan: -0.35 });
for (const h of HOOKS) { add(h.save.start, 'slam', 0.55 + 0.08 * h.k); add(h.it.start, 'slam', 0.65 + 0.08 * h.k); }
for (const at of DROP_TIMES) add(at, 'tick', 0.35);
for (const s of SHOTS.filter(s => ['spark', 'cell', 'follow', 'last'].includes(s.kind)))
  add(s.t0, 'crackle', s.kind === 'last' ? 0.45 : 0.22, { dur: +(s.t1 - s.t0).toFixed(3), pan: 0.35 });
add(b(19.5), 'swish', 0.6, { dur: +(BEAT / 2).toFixed(3) });
add(b(24), 'click', 0.5); add(b(30), 'click', 0.5);                       // into paper and back
add(b(28), 'stamp', 0.9);
add(b(31), 'glitch', 0.3, { dur: +BEAT.toFixed(3) });
add(b(47), 'glitch', 0.35, { dur: +(BEAT * 0.9).toFixed(3) });
add(b(47.5), 'zap', 0.5, { pan: 0.4 });
add(b(48), 'boom', 0.9);
console.log(JSON.stringify({ seed: 3, gain_db: -9, cues: cues.sort((p, q) => p.t - q.t) }, null, 1));
