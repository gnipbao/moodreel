// Music as data, for a film that follows its song: the beat grid, the bars, drum and vocal hits, loudness envelopes, and
// the lyric's words with the times they are sung. `moodreel music` writes the data (a music-data.js beside main.js);
// music() turns it into answers a shot asks for by time:
//
//   import { AUDIO, LYRICS } from './music-data.js';
//   import { music, pop } from './kit/music.js';
//   const M = music(AUDIO, LYRICS);
//   M.hit('kick', t)            1 on a kick, decaying (half-life 0.11 s), scaled by its strength: a punch
//   M.ct(t)                     a camera clock that surges just after each beat: keys(cameraKeys, M.ct(t))
//   M.sung('upping', 23)        when the word is actually sung near that time (a time read off a contact sheet is
//                               typically 60-130 ms off; the vocal is not)
//   M.letters('upping', 23)     i => when letter i lights, the letters sharing the sung time
//   M.slams(starts)             t => { s, x, y }: each word landing 14% big and settling, with a short shake
//
// The method, and the hit and slam recipes, follow mexicat/pdoom-video (MIT, Copyright (c) 2026 Giacomo Magnanini), a
// music video whose every motion is computed from aligned data rather than timed by hand. See docs/MUSIC-SYNC.md.

const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
// index of the last element of a sorted array that is <= t (-1 before the first)
function last(arr, t, key = x => x) {
  let lo = 0, hi = arr.length - 1;
  if (!arr.length || t < key(arr[0])) return -1;
  while (lo < hi) { const m = (lo + hi + 1) >> 1; if (key(arr[m]) <= t) lo = m; else hi = m - 1; }
  return lo;
}
const norm = s => String(s).toLowerCase().replace(/[’‘]/g, "'").replace(/[^\p{L}\p{N}']/gu, '').replace(/^'+|'+$/g, '');
const outExpo = u => (u >= 1 ? 1 : 1 - 2 ** (-10 * u));
const hash1 = (n, k) => { const x = Math.sin(n * 127.1 + k * 311.7) * 43758.5453; return x - Math.floor(x); };

// a letter or word arriving: it lands big and settles on an exponential ease (no bounce), dropping a little as it does
export function pop(age, dur = 0.16, from = 1.2) {
  if (age < 0 || age >= dur * 1.5) return { s: 1, dy: 0 };
  const e = outExpo(clamp(age / dur));
  return { s: from + (1 - from) * e, dy: -(1 - e) };
}

export function music(AUDIO, LYRICS = []) {
  const B = AUDIO.beats, DB = AUDIO.downbeats?.length ? AUDIO.downbeats : B.filter((_, i) => i % 4 === 0);
  const PERIOD = 60 / AUDIO.bpm, ONS = AUDIO.onsets ?? {}, FEAT = AUDIO.features ?? {}, FPS = AUDIO.fps ?? 100;
  const along = (grid, t) => {                             // continuous index into a grid, extrapolated at both ends
    const n = grid.length;
    if (n < 2) return t / PERIOD;
    if (t <= grid[0]) return (t - grid[0]) / (grid[1] - grid[0]);
    if (t >= grid[n - 1]) return n - 1 + (t - grid[n - 1]) / (grid[n - 1] - grid[n - 2]);
    const i = last(grid, t);
    return i + (t - grid[i]) / (grid[i + 1] - grid[i]);
  };
  const beatAt = t => along(B, t), barAt = t => along(DB, t);
  function timeOfBeat(i) {
    if (B.length < 2) return i * PERIOD;
    if (i <= 0) return B[0] + i * PERIOD;
    if (i >= B.length - 1) return B[B.length - 1] + (i - B.length + 1) * PERIOD;
    const k = Math.floor(i);
    return B[k] + (B[k + 1] - B[k]) * (i - k);
  }
  // an envelope (rms, low, mid, high, and any stems the data has) at t, 0..1
  function env(name, t) {
    const a = FEAT[name], x = t * FPS, i = Math.floor(x);
    if (!a || !a.length) return 0;
    if (i < 0) return a[0];
    if (i >= a.length - 1) return a[a.length - 1];
    return a[i] + (a[i + 1] - a[i]) * (x - i);
  }
  // kick, snare, hat, vocal: the strongest recent hit of a kind, decaying with half-life `half`, scaled by its strength
  function hit(kind, t, half = 0.11) {
    const list = ONS[kind] ?? [];
    let v = 0;
    for (let i = last(list, t, o => o[0]); i >= 0; i--) {
      const [ot, s] = list[i], dt = t - ot;
      if (dt > half * 8) break;
      v = Math.max(v, s * 0.5 ** (dt / half));
    }
    return v;
  }
  const events = (kind, t0, t1) => (ONS[kind] ?? []).filter(([t]) => t >= t0 && t < t1);
  const lastHit = (kind, t) => { const list = ONS[kind] ?? [], i = last(list, t, o => o[0]); return i < 0 ? null : list[i]; };

  // the camera clock: within each beat it covers most of the beat early on (amount 0 is real time), so a move keyed
  // smoothly arrives in surges on the beat
  function ct(t, amount = 0.6) {
    const b = beatAt(t), i = Math.floor(b), u = b - i;
    return timeOfBeat(i + (1 - amount) * u + amount * (1 - (1 - u) ** 3));
  }
  // the slam: each word lands `amt` big and settles over `dur`, a held word creeps toward the camera, and a shake of
  // `shake` px dies with a 50 ms half-life (seeded by the frame, so a frame shows one state across its shutter)
  function slams(starts, { amt = 0.14, dur = 0.16, shake = 10, creep = 0.035, fps = 60 } = {}) {
    return t => {
      let t0 = null;
      for (const x of starts) if (t >= x) t0 = x;
      if (t0 == null) return { s: 1, x: 0, y: 0 };
      const age = t - t0, s = (1 + creep * age) * (1 + amt * (1 - outExpo(clamp(age / dur))));
      const sh = shake * 0.5 ** (age / 0.05), f = Math.round(t * fps);
      return { s, x: (hash1(f, 1) - 0.5) * 2 * sh, y: (hash1(f, 2) - 0.5) * 2 * sh };
    };
  }

  // the lyric
  const WORDS = LYRICS.flatMap((l, li) => l.words.map((w, wi) => ({ ...w, key: norm(w.w), line: li, index: wi })));
  // the n-th line containing the words of q
  function line(q, nth = 0) {
    const k = String(q).split(/\s+/).map(norm).filter(Boolean).join(' ');
    return LYRICS.filter(l => l.words.map(w => norm(w.w)).join(' ').includes(k))[nth] ?? null;
  }
  // the sung word `text` nearest to t (within `win` s) as {w, start, end}; several words run from the first one's start
  // to the last one's end. null when the text is not sung near t (a label, a caption): keep your own time then.
  function span(text, t, win = 0.45) {
    const parts = String(text).split(/\s+/).map(norm).filter(Boolean);
    if (!parts.length) return null;
    let best = -1;
    for (let i = 0; i < WORDS.length; i++) {
      const w = WORDS[i];
      if (w.key === parts[0] && Math.abs(w.start - t) <= win && (best < 0 || Math.abs(w.start - t) < Math.abs(WORDS[best].start - t))) best = i;
    }
    if (best < 0) return null;
    let end = WORDS[best].end, j = best;
    for (const p of parts.slice(1)) {
      if (WORDS[j + 1]?.key !== p) break;
      end = WORDS[++j].end;
    }
    return { w: text, start: WORDS[best].start, end };
  }
  const sung = (text, t, win) => span(text, t, win)?.start ?? t;
  // letter i lights at an even share of the sung time; a held note does not drag them out (at most `max` s apart)
  function letters(text, t, per = 0.05, { win, max = 0.09 } = {}) {
    const s = span(text, t, win), n = [...String(text)].length;
    return s ? i => s.start + Math.min(s.end - s.start, max * n) * i / n : i => t + i * per;
  }
  const progress = (w, t) => clamp((t - w.start) / Math.max(0.01, w.end - w.start));

  return { bpm: AUDIO.bpm, beats: B, downbeats: DB, sections: AUDIO.sections ?? [], lines: LYRICS,
    beatAt, barAt, timeOfBeat, nearestBeat: t => timeOfBeat(Math.round(beatAt(t))),
    section: t => (AUDIO.sections ?? []).find(s => t >= s.start && t < s.end) ?? null,
    env, hit, events, lastHit, ct, step: (t, at, dur) => clamp((ct(t) - at) / dur), slams,
    line, span, sung, letters, progress };
}
