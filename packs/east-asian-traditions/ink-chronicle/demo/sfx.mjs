// 黄河's sound effects, from the same timeline as the picture: node sfx.mjs > sfx.json (build.sh does this).
import { T, b, SHOTS } from './timeline.js';

const cues = [];
const add = (t, sound, level, extra = {}) => cues.push({ t: +t.toFixed(4), sound, level, ...extra });
add(T.water, 'slam', 0.75); add(T.water, 'ding', 0.2);                    // 水 lands
add(T.melt, 'crackle', 0.3, { dur: 1.2 });                                 // and runs as grit
const course = SHOTS.find(s => s.kind === 'course');
add(course.t0, 'whoosh', 0.3, { dur: 0.9 });                               // the pull back over the course
T.bends.forEach(at => add(at, 'tick', 0.3));                               // each place popping in
const gorge = SHOTS.find(s => s.kind === 'gorge');
add(gorge.t0, 'whoosh', 0.4, { dur: 1.4 });                                // into the gorge
add(T.blow, 'slam', 0.85); add(T.blow, 'whoosh', 0.45, { dur: 0.4 });      // 壶口, the lurch
const falls = SHOTS.find(s => s.kind === 'falls');
add(falls.t0, 'crackle', 0.35, { dur: 3.2 }); add(T.surge, 'riser', 0.4, { dur: falls.t1 - T.surge });   // the pour
add(T.breach, 'slam', 0.9); add(T.breach, 'boom', 0.6);                    // 决
add(T.breach + 0.08, 'crackle', 0.4, { dur: 0.6 });
for (let k = 0; k < 6; k++) add(T.breach + 0.35 + k * 0.09, 'thud', 0.25 + 0.05 * (k % 2), { pan: (k % 3 - 1) * 0.4 });   // blocks landing
for (let k = 0; k < 4; k++) add(b(20.3) + k * 1.5, 'whoosh', 0.12, { dur: 1.2, pan: k % 2 ? 0.4 : -0.4 });   // the sea's swell
T.places.slice(0, 2).forEach(at => add(at, 'tick', 0.25));                 // the length counting
add(T.mouth, 'ding', 0.4);                                                  // the mouth reached
add(T.last, 'stamp', 0.85);                                                 // 海
add(T.drift + 0.1, 'whoosh', 0.3, { dur: 1.4 });                            // becoming the sea
console.log(JSON.stringify({ seed: 7, gain_db: -9, cues: cues.sort((p, q) => p.t - q.t) }, null, 1));
