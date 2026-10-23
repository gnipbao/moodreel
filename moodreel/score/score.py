"""A film's original score, from `score.json`: the tempo grid and cue table first, then the music drawn on it.

Music-led styles time the picture to the music: a tempo grid and a cue table come before any animation, and every
picture hit lands on a listed cue. `score.json` holds both, and the music's arrangement:

  {"bpm": 120, "meter": 4, "offset": 0.0, "seed": 7, "key": "C",
   "sections": [{"name": "intro", "bars": 2, "chords": ["C", "Am", "F", "G"], "groove": "backbeat",
                 "parts": ["kick", "snare", "hat", "bass", "pad", "lead"]}, ...],
   "cues": [{"name": "title", "bar": 3, "beat": 1, "sound": "stab"},
            {"name": "gasp", "bar": 6, "beat": 1, "sound": "stop", "beats": 2}, ...]}

With no sections (or sections with "parts": []) a score is the film's sound effects alone, its cues placed in bars
and beats of the tempo all the same.

Bars and beats count from 1 (beat 2.5 is the off-beat after 2); one chord per bar, cycling. Grooves: four (a kick on
every beat), backbeat (kick 1 and 3, snare 2 and 4), halftime (kick 1, snare 3), oompah (bass on 1 and 3, a chord
stab on 2 and 4), none. Parts: kick, snare, clap, hat, bass, pad, stab, pluck (an arpeggio in eighths), lead (a
two-bar motif from the chord tones, seeded). Cue sounds: stab, hit, pop, boing, ding, whoosh, riser (it ends on the
cue), clack, and stop (the band falls silent for `beats`, reverb tails too; other cues still sound in it).

`render` gives the audio and the timeline; `write` puts `out/score.wav` and `score.js` (the timeline as a module the
picture imports: SCORE, bar(n, beat), cue(name)) in the film folder. The same seed draws the same music.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np

from . import synth as S

NOTES = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
QUALITIES = {"": (0, 4, 7), "m": (0, 3, 7), "7": (0, 4, 7, 10), "maj7": (0, 4, 7, 11), "m7": (0, 3, 7, 10),
             "dim": (0, 3, 6), "sus4": (0, 5, 7), "sus2": (0, 2, 7), "6": (0, 4, 7, 9), "m6": (0, 3, 7, 9)}
GROOVES = ("four", "backbeat", "halftime", "oompah", "none")
LEVEL = {"kick": 0.9, "snare": 0.6, "clap": 0.5, "hat": 0.35, "bass": 0.55, "pad": 0.3, "stab": 0.45, "pluck": 0.35,
         "lead": 0.4, "cue": 0.7}


def chord(name: str) -> tuple[int, tuple[int, ...]]:
    """'F#m7' -> (6, (0, 3, 7, 10)): the root's pitch class and the intervals."""
    m = re.fullmatch(r"([A-G])([#b]?)(.*)", name.strip())
    if not m or m[3] not in QUALITIES:
        raise ValueError(f"chord {name!r}: a root A-G, # or b, then one of {sorted(QUALITIES)}")
    return (NOTES[m[1]] + {"#": 1, "b": -1, "": 0}[m[2]]) % 12, QUALITIES[m[3]]


def _voicing(name: str, low: int) -> list[int]:
    root, iv = chord(name)
    base = low + (root - low) % 12
    return [base + i for i in iv]


def timeline(score: dict) -> dict:
    """Where every section and cue falls, in seconds."""
    beat_s, meter, offset = 60.0 / score["bpm"], score.get("meter", 4), score.get("offset", 0.0)
    bar_t = lambda n, beat=1: offset + ((n - 1) * meter + (beat - 1)) * beat_s  # noqa: E731
    sections, n = [], 1
    for s in score["sections"]:
        sections.append({"name": s["name"], "bar": n, "start": round(bar_t(n), 4), "end": round(bar_t(n + s["bars"]), 4)})
        n += s["bars"]
    cues = [{"name": c["name"], "t": round(bar_t(c["bar"], c.get("beat", 1)), 4), "sound": c.get("sound", "hit"),
             **({"beats": c["beats"]} if "beats" in c else {})} for c in score.get("cues", [])]
    return {"bpm": score["bpm"], "meter": meter, "offset": offset, "beat_s": round(beat_s, 6), "bars": n - 1,
            "duration": round(bar_t(n), 4), "sections": sections, "cues": sorted(cues, key=lambda c: c["t"])}


def _place(buf: np.ndarray, x: np.ndarray, t: float) -> None:
    i = int(round(t * S.SR))
    if i >= len(buf):
        return
    j = min(len(buf), i + len(x))
    buf[i:j] += x[: j - i]


def _section(buf, s, start, beat_s, meter, rng):
    parts = set(s.get("parts") or {"four": ["kick", "clap", "hat", "bass", "pad"], "backbeat": ["kick", "snare", "hat", "bass", "pad"],
                                    "halftime": ["kick", "snare", "hat", "bass", "pad"], "oompah": ["bass", "stab", "hat"],
                                    "none": ["pad"]}[s.get("groove", "backbeat")])
    groove = s.get("groove", "backbeat")
    if groove not in GROOVES:
        raise ValueError(f"groove {groove!r}: one of {GROOVES}")
    chords = s["chords"]
    lead_motif = [(rng.integers(0, 4), rng.choice([0.5, 1.0, 1.0, 1.5])) for _ in range(8)]
    for b in range(s["bars"]):
        t0 = start + b * meter * beat_s
        name = chords[b % len(chords)]
        tones, root = _voicing(name, 60), _voicing(name, 36)[0]
        beats = range(meter)
        for k in beats:
            t = t0 + k * beat_s
            if "kick" in parts and (groove == "four" or (groove == "backbeat" and k % 2 == 0) or (groove == "halftime" and k == 0)):
                _place(buf, S.kick(rng, LEVEL["kick"]), t)
            if "snare" in parts and ((groove in ("backbeat", "four") and k % 2 == 1) or (groove == "halftime" and k == 2)):
                _place(buf, S.snare(rng, LEVEL["snare"]), t)
            if "clap" in parts and k % 2 == 1 and groove != "halftime":
                _place(buf, S.clap(rng, LEVEL["clap"]), t)
            if "hat" in parts:
                if groove == "oompah":
                    if k % 2 == 1:
                        _place(buf, S.hat(rng, LEVEL["hat"]), t)
                else:
                    _place(buf, S.hat(rng, 0.6 * LEVEL["hat"]), t)
                    _place(buf, S.hat(rng, LEVEL["hat"], open_=k == meter - 1), t + beat_s / 2)
            if "bass" in parts:
                if groove == "oompah":
                    if k % 2 == 0:
                        _place(buf, S.bass(root + (7 if k == 2 else 0), 0.8 * beat_s, rng, LEVEL["bass"]), t)
                elif groove == "four" or k % 2 == 0:
                    _place(buf, S.bass(root, 0.85 * beat_s, rng, LEVEL["bass"]), t)
                    if groove != "four" and k == meter - 2:
                        _place(buf, S.bass(root + 7, 0.4 * beat_s, rng, LEVEL["bass"]), t + 1.5 * beat_s)
            if "stab" in parts and ((groove == "oompah" and k % 2 == 1) or (groove != "oompah" and k == 0)):
                _place(buf, S.stab(tones, 0.3 * beat_s, rng, LEVEL["stab"]), t)
            if "pluck" in parts:
                for h in (0, 1):
                    _place(buf, S.pluck(tones[(2 * k + h) % len(tones)] + 12, 0.45 * beat_s, rng, LEVEL["pluck"]), t + h * beat_s / 2)
        if "pad" in parts:
            _place(buf, S.pad(tones, meter * beat_s, rng, LEVEL["pad"]), t0)
        if "lead" in parts:                                # the same two-bar motif over every pair of bars
            t, end = t0, t0 + meter * beat_s
            for deg, dur in lead_motif[(b % 2) * 4:(b % 2) * 4 + 4]:
                if t >= end:
                    break
                _place(buf, S.lead(tones[deg % len(tones)] + 12, min(dur * beat_s, end - t) * 0.9, rng, LEVEL["lead"]), t)
                t += dur * beat_s


def render(score: dict) -> tuple[np.ndarray, dict]:
    tl = timeline(score)
    rng = np.random.default_rng(score.get("seed", 0))
    beat_s, meter = tl["beat_s"], tl["meter"]
    last = max([c["t"] for c in tl["cues"]] + [0.0])     # a score of cues alone (sound effects) runs past its last
    band = np.zeros(int((max(tl["duration"], last + 2.0) + 1.0) * S.SR), np.float32)
    for s, at in zip(score["sections"], tl["sections"]):
        _section(band, s, at["start"], beat_s, meter, rng)
    cues = np.zeros_like(band)
    for c, at in zip(sorted(score.get("cues", []), key=lambda c: timeline({**score, "cues": [c]})["cues"][0]["t"]), tl["cues"]):
        snd, t = at["sound"], at["t"]
        if snd == "stop":
            continue
        if snd == "stab":
            bar = int((t - tl["offset"]) / (meter * beat_s))
            names = [ch for s in score["sections"] for b in range(s["bars"]) for ch in [s["chords"][b % len(s["chords"])]]]
            x = S.stab(_voicing(names[min(bar, len(names) - 1)], 60), 0.4 * beat_s, rng, LEVEL["stab"] * 1.3)
        elif snd == "riser":
            x = S.riser(rng, LEVEL["cue"], dur=c.get("beats", 2) * beat_s)
            t -= len(x) / S.SR                                     # a riser ends on its cue
        elif snd in S.FOLEY:
            x = S.FOLEY[snd](rng, LEVEL["cue"])
        else:
            raise ValueError(f"cue {c['name']}: sound {snd!r} is not one of stop, stab, {', '.join(S.FOLEY)}")
        _place(cues, x, max(0.0, t))
    band = S.reverb(band, 0.4, 0.15)
    cues = np.concatenate([cues, np.zeros(len(band) - len(cues), np.float32)])
    gate = np.ones(len(band), np.float32)
    fade = int(0.005 * S.SR)
    for at in tl["cues"]:
        if at["sound"] == "stop":                          # the band falls silent, its reverb tail too
            i, j = int(at["t"] * S.SR), int((at["t"] + at.get("beats", 1) * beat_s) * S.SR)
            gate[i:j] = 0
            gate[max(0, i - fade):i] = np.minimum(gate[max(0, i - fade):i], np.linspace(1, 0, i - max(0, i - fade)))
            gate[j:j + fade] = np.minimum(gate[j:j + fade], np.linspace(0, 1, len(gate[j:j + fade])))
    mix = band * gate + S.reverb(cues, 0.3, 0.1)[: len(band)]
    mix = np.tanh(1.2 * mix / max(1e-6, float(np.percentile(np.abs(mix), 99.9)))) * 0.9
    return mix.astype(np.float32), tl


JS = """// Written by `moodreel score` from score.json: the music's grid and cues, for the picture to land on.
export const SCORE = {score};
// the time of bar n (from 1), at beat b (from 1; 2.5 is the off-beat after 2)
export const bar = (n, b = 1) => SCORE.offset + ((n - 1) * SCORE.meter + (b - 1)) * SCORE.beat_s;
// the time of a named cue
export const cue = name => {{
  const c = SCORE.cues.find(c => c.name === name);
  if (!c) throw new Error(`no cue ${{name}} in score.json`);
  return c.t;
}};
"""


def write(film: Path) -> dict:
    from scipy.io import wavfile
    film = Path(film)
    score = json.loads((film / "score.json").read_text())
    audio, tl = render(score)
    (film / "out").mkdir(exist_ok=True)
    wav = film / "out" / "score.wav"
    wavfile.write(wav, S.SR, (np.clip(audio, -1, 1) * 32767).astype(np.int16))
    (film / "score.js").write_text(JS.format(score=json.dumps(tl, indent=1)))
    return {"wav": str(wav), "js": str(film / "score.js"), **{k: tl[k] for k in ("bpm", "bars", "duration")},
            "cues": len(tl["cues"])}
