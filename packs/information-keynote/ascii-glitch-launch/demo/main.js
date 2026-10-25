// Tidepool: the ASCII Glitch Launch demo, a 16 s teaser for an invented tide-forecast API, cut to its own 120 BPM score
// (score.json). Every product, card, badge, post and mark is drawn here; the edit is timeline.js. Each shot draws on the
// frame's layer and says how it is finished: through the cell pass or not, what sits over it, how strong the scan
// lines are (measured per scene on the reference: GLITCH.scan, and below).
import { stage } from './kit/stage.js';
import { faces, frame, typed } from './kit/glitch.js';
import { DUR, shotAt, TYPED } from './timeline.js';
import { year, tracked, field, console_, sentence, dashes, wall } from './scenes-open.js';
import { but, mosaic, radarScene, guess, harbours } from './scenes-mid.js';
import { tunnel, good, data, ring, liveson, name, markScene, end, black } from './scenes-end.js';

const F = frame();
const SCENES = { year, tracked, field, console: console_, sentence, dashes, wall, but, mosaic, radar: radarScene, guess,
  harbours, tunnel, good, data, ring, liveson, name, mark: markScene, end, black };
// rows 2-3 of every 4 darkened by this much, by shot: the reference's 4 px rhythm in the scene of the same kind
const SCAN = { year: 0.1, tracked: 0.17, field: 0.14, console: 0.15, sentence: 0.091, dashes: 0.096, wall: 0.094, but: 0.05,
  mosaic: 0.06, radar: 0.19, guess: 0.18, harbours: 0.15, tunnel: 0.13, good: 0.03, data: 0.12, ring: 0.015, liveson: 0.1,
  name: 0.13, mark: 0.01, end: 0.045, black: 0 };

// what is on screen to be read, for the film check's reading test: each line with its box, as typed so far
const LINES = { year: ['year', 400, 420, 1320, 660], tracked: ['In 2026', 150, 280, 1860, 820],
  console: ['request', 430, 500, 1910, 680], sentence: ['sentence', 100, 500, 1420, 600], wall: ['sentence', 0, 480, 1800, 620],
  but: ['BUT', 300, 300, 1620, 800], radar: ['radar', 600, 500, 1320, 600], guess: ['guess', 150, 330, 1850, 960],
  harbours: ['every port worth sailing', 970, 490, 1880, 590], tunnel: ['it starts with', 500, 500, 1420, 680],
  good: ['Good', 550, 500, 900, 620], data: ['data', 1230, 480, 1500, 600], ring: ['and every good forecast', 520, 490, 1400, 600],
  liveson: ['liveson', 990, 490, 1340, 600], name: ['name', 100, 490, 600, 610] };
const shown = (key, t) => (TYPED[key] ? typed(TYPED[key].text, t, TYPED[key].t0, TYPED[key].cps) : key);
window.TEXTS = t => {
  const s = shotAt(t), L = LINES[s.kind];
  if (!L) return [];
  const [key, x0, y0, x1, y1] = L, text = shown(key, t), full = TYPED[key]?.text ?? key;
  return text === full ? [{ id: s.kind === 'wall' ? 'sentence' : key, text, x0, y0, x1, y1 }] : [];   // once typed in full
};

stage({
  width: F.W, height: F.H, duration: DUR, background: '#000', prepare: faces,
  draw: (g, t) => {
    const s = shotAt(t), q = F.begin('#000');
    const fin = SCENES[s.kind](q, t, t - s.t0, s.t1 - s.t0) ?? {};
    F.end(g, t, { cells: fin.cells, over: fin.over, scan: fin.scan ?? SCAN[s.kind], post: fin.post });
  },
});
