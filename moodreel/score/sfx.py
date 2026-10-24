"""A film's sound effects at given seconds, under its music: `sfx.json` -> out/sfx.wav (stereo).

A score's cues are placed in bars and beats; a film cut to a song it did not write (a lyric video, a remake) has its
events at seconds instead, often read from the song's own data (kit/music.js: the words as sung, the hits). So:

  {"seed": 1, "gain_db": -9,
   "cues": [{"t": 22.76, "sound": "slam", "level": 0.8},
            {"t": 101.9, "sound": "crackle", "dur": 3.9, "level": 0.4, "pan": -0.3}, ...]}

`sound` is any of the synth's foley (synth.FOLEY); `dur` reaches the sounds that have a length (whoosh, riser, glitch,
tear, crackle, rewind, swish); `pan` runs from -1 (left) to 1 (right). A riser ends on its time; everything else starts
on it. `gain_db` sets the effects against the music before the delivery's loudness pass (the effects sit under it).
"""
from __future__ import annotations

import inspect
import json
from pathlib import Path

import numpy as np

from . import synth as S


def render(cfg: dict, duration: float | None = None) -> np.ndarray:
    """The effects as a stereo buffer at synth.SR, shape (n, 2)."""
    rng = np.random.default_rng(cfg.get("seed", 1))
    cues = sorted(cfg.get("cues", []), key=lambda c: c["t"])
    end = max([c["t"] + c.get("dur", 3.0) for c in cues] + [duration or 0.0]) + 2.0
    out = np.zeros((int(end * S.SR), 2), np.float32)
    for c in cues:
        fn = S.FOLEY.get(c["sound"])
        if fn is None:
            raise ValueError(f"sfx at {c['t']} s: {c['sound']!r} is not one of {', '.join(S.FOLEY)}")
        kw = {"dur": c["dur"]} if "dur" in c and "dur" in inspect.signature(fn).parameters else {}
        x = fn(rng, c.get("level", 0.7), **kw)
        t = c["t"] - (len(x) / S.SR if c["sound"] == "riser" else 0.0)
        i = max(0, int(round(t * S.SR)))
        j = min(len(out), i + len(x))
        a = (np.clip(c.get("pan", 0.0), -1, 1) + 1) * np.pi / 4          # constant-power pan
        out[i:j, 0] += x[: j - i] * np.cos(a) * np.sqrt(2)
        out[i:j, 1] += x[: j - i] * np.sin(a) * np.sqrt(2)
    wet = np.stack([S.reverb(out[:, k], 0.3, 0.12)[: len(out)] for k in range(2)], axis=1)
    if duration:
        wet = wet[: int(duration * S.SR)]
    return (np.tanh(wet) * 10 ** (cfg.get("gain_db", -9) / 20)).astype(np.float32)


def write(film: Path, duration: float | None = None) -> dict:
    from scipy.io import wavfile
    film = Path(film)
    cfg = json.loads((film / "sfx.json").read_text())
    audio = render(cfg, duration)
    (film / "out").mkdir(exist_ok=True)
    wav = film / "out" / "sfx.wav"
    wavfile.write(wav, S.SR, (np.clip(audio, -1, 1) * 32767).astype(np.int16))
    return {"wav": str(wav), "cues": len(cfg.get("cues", [])), "seconds": round(len(audio) / S.SR, 2)}
