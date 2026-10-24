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
   "name": "title",
   "bar": 1,
   "start": 0.0,
   "end": 2.0
  },
  {
   "name": "vamp",
   "bar": 2,
   "start": 2.0,
   "end": 4.0
  },
  {
   "name": "band",
   "bar": 3,
   "start": 4.0,
   "end": 8.0
  },
  {
   "name": "chorus",
   "bar": 5,
   "start": 8.0,
   "end": 12.0
  },
  {
   "name": "tag",
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
   "name": "title",
   "t": 0.0,
   "sound": "piano"
  },
  {
   "name": "tap1",
   "t": 1.0,
   "sound": "clack"
  },
  {
   "name": "tap2",
   "t": 1.5,
   "sound": "clack"
  },
  {
   "name": "curtain",
   "t": 3.0,
   "sound": "whoosh"
  },
  {
   "name": "tuba",
   "t": 4.0,
   "sound": "timpani"
  },
  {
   "name": "freeze",
   "t": 7.0,
   "sound": "stop",
   "beats": 1
  },
  {
   "name": "peek",
   "t": 7.25,
   "sound": "clack"
  },
  {
   "name": "leap",
   "t": 8.0,
   "sound": "brass"
  },
  {
   "name": "tada",
   "t": 12.0,
   "sound": "brass"
  },
  {
   "name": "reach",
   "t": 12.5,
   "sound": "whoosh"
  },
  {
   "name": "swell",
   "t": 14.0,
   "sound": "roll",
   "beats": 2
  },
  {
   "name": "end",
   "t": 14.0,
   "sound": "piano"
  },
  {
   "name": "end_brass",
   "t": 14.0,
   "sound": "brass"
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
