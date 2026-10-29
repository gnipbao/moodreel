// Written by `moodreel score` from score.json: the music's grid and cues, for the picture to land on.
export const SCORE = {
 "bpm": 72,
 "meter": 4,
 "offset": 0.0,
 "beat_s": 0.833333,
 "bars": 8,
 "duration": 26.6667,
 "sections": [
  {
   "name": "source",
   "bar": 1,
   "start": 0.0,
   "end": 3.3333
  },
  {
   "name": "case",
   "bar": 2,
   "start": 3.3333,
   "end": 6.6667
  },
  {
   "name": "floor",
   "bar": 3,
   "start": 6.6667,
   "end": 13.3333
  },
  {
   "name": "flood",
   "bar": 5,
   "start": 13.3333,
   "end": 16.6667
  },
  {
   "name": "sea",
   "bar": 6,
   "start": 16.6667,
   "end": 23.3333
  },
  {
   "name": "end",
   "bar": 8,
   "start": 23.3333,
   "end": 26.6667
  }
 ],
 "cues": [
  {
   "name": "blow",
   "t": 8.3333,
   "sound": "timpani"
  },
  {
   "name": "breach",
   "t": 15.0,
   "sound": "roll",
   "beats": 2
  },
  {
   "name": "sea",
   "t": 16.6667,
   "sound": "harp"
  },
  {
   "name": "last",
   "t": 23.3333,
   "sound": "timpani"
  }
 ],
 "words": [],
 "lines": []
};
// the time of bar n (from 1), at beat b (from 1; 2.5 is the off-beat after 2)
export const bar = (n, b = 1) => SCORE.offset + ((n - 1) * SCORE.meter + (b - 1)) * SCORE.beat_s;
// the time of a named cue
export const cue = name => {
  const c = SCORE.cues.find(c => c.name === name);
  if (!c) throw new Error(`no cue ${name} in score.json`);
  return c.t;
};
