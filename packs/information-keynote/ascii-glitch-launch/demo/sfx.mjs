// Tidepool's sound effects, from the same timeline as the picture: node sfx.mjs > sfx.json (build.sh does this).
import { b, TYPED, GLITCHES, FLASHES, ROLL, BREAK, letterTimes } from './timeline.js';

const cues = [];
const add = (t, sound, level, extra = {}) => cues.push({ t: +t.toFixed(4), sound, level, ...extra });
for (const k of ['year', 'request', 'radar', 'guess', 'liveson', 'name'])
  letterTimes(TYPED[k]).forEach(([c, at]) => { if (c.trim()) add(at, 'key', 0.28, { pan: -0.3 }); });
letterTimes(TYPED.sentence).forEach(([c, at], i) => { if (c.trim() && i % 4 === 0) add(at, 'key', 0.22, { pan: -0.3 }); });   // typed at 150 a second
add(ROLL[0], 'tick', 0.4); add(ROLL[1], 'tick', 0.45);              // the reel
add(BREAK, 'crackle', 0.3, { dur: 0.18, pan: 0.2 });                 // the year breaking into cells
for (const [s, n] of GLITCHES) add(s, 'glitch', 0.32, { dur: +(n / 60).toFixed(3) });
for (const [s] of FLASHES) add(s, 'clack', 0.5);
for (let k = 0; k < 5; k++) add(b(15.2) + k * 5 / 60, 'tick', 0.18, { pan: 0.4 });   // the badges cutting
add(b(16), 'riser', 0.5, { dur: 0.5 }); add(b(16), 'whoosh', 0.55, { dur: 0.5 });     // into the tunnel
add(b(17), 'zap', 0.45, { pan: 0.5 });                              // the neon comes on
add(b(18.5), 'swish', 0.5, { dur: 0.4, pan: -0.4 });                // the beam
add(b(20), 'whoosh', 0.45, { dur: 0.6 }); add(b(21.6), 'whoosh', 0.5, { dur: 0.5 });   // the ring arrives, then rushes out
add(b(22.45), 'ding', 0.35);                                        // the lamp
add(b(26.33), 'glitch', 0.4, { dur: 0.1 });
add(b(28), 'boom', 0.85);                                           // the mark on white
console.log(JSON.stringify({ seed: 5, gain_db: -9, cues: cues.sort((p, q) => p.t - q.t) }, null, 1));
