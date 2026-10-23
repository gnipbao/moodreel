// Written by `moodreel score` from score.json: the music's grid and cues, for the picture to land on.
export const SCORE = {
 "bpm": 120,
 "meter": 4,
 "offset": 0.0,
 "beat_s": 0.5,
 "bars": 6,
 "duration": 12.0,
 "sections": [
  {
   "name": "round1",
   "bar": 1,
   "start": 0.0,
   "end": 6.0
  },
  {
   "name": "round2",
   "bar": 4,
   "start": 6.0,
   "end": 12.0
  }
 ],
 "cues": [
  {
   "name": "drop1",
   "t": 0.5,
   "sound": "pop"
  },
  {
   "name": "drop2",
   "t": 1.0,
   "sound": "pop"
  },
  {
   "name": "drop3",
   "t": 1.5,
   "sound": "pop"
  },
  {
   "name": "card",
   "t": 2.0,
   "sound": "stab"
  },
  {
   "name": "think",
   "t": 3.0,
   "sound": "stop",
   "beats": 1
  },
  {
   "name": "answer",
   "t": 3.5,
   "sound": "ding"
  },
  {
   "name": "correct",
   "t": 4.0,
   "sound": "hit"
  },
  {
   "name": "round2",
   "t": 6.0,
   "sound": "whoosh"
  },
  {
   "name": "board",
   "t": 7.0,
   "sound": "stab"
  },
  {
   "name": "point",
   "t": 8.0,
   "sound": "boing"
  },
  {
   "name": "build",
   "t": 10.0,
   "sound": "riser",
   "beats": 4
  },
  {
   "name": "winner",
   "t": 10.0,
   "sound": "hit"
  }
 ]
};
// the time of bar n (from 1), at beat b (from 1; 2.5 is the off-beat after 2)
export const bar = (n, b = 1) => SCORE.offset + ((n - 1) * SCORE.meter + (b - 1)) * SCORE.beat_s;
// the time of a named cue
export const cue = name => {
  const c = SCORE.cues.find(c => c.name === name);
  if (!c) throw new Error(`no cue ${name} in score.json`);
  return c.t;
};
