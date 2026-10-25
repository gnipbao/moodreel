// Written by `moodreel score` from score.json: the music's grid and cues, for the picture to land on.
export const SCORE = {
 "bpm": 120,
 "meter": 4,
 "offset": 0.0,
 "beat_s": 0.5,
 "bars": 8,
 "duration": 16.0,
 "sections": [
  {
   "name": "open",
   "bar": 1,
   "start": 0.0,
   "end": 2.0
  },
  {
   "name": "build",
   "bar": 2,
   "start": 2.0,
   "end": 4.0
  },
  {
   "name": "verse",
   "bar": 3,
   "start": 4.0,
   "end": 8.0
  },
  {
   "name": "drop",
   "bar": 5,
   "start": 8.0,
   "end": 12.0
  },
  {
   "name": "name",
   "bar": 7,
   "start": 12.0,
   "end": 14.0
  },
  {
   "name": "end",
   "bar": 8,
   "start": 14.0,
   "end": 16.0
  }
 ],
 "cues": [
  {
   "name": "drop",
   "t": 8.0,
   "sound": "hit"
  },
  {
   "name": "flash",
   "t": 10.5,
   "sound": "stab"
  },
  {
   "name": "stop",
   "t": 13.0,
   "sound": "stop",
   "beats": 2
  },
  {
   "name": "mark",
   "t": 14.0,
   "sound": "hit"
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
