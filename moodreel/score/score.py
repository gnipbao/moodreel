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

A section may write its lead out instead of drawing one: "melody": [{"bar": 1, "beat": 1, "beats": 0.5, "tone": 2,
"word": "save"}, ...], bars counted within the section, `tone` an index into the bar's chord tones an octave up (or
"note", a MIDI number), "oct" to move it. Notes carrying a "word" are the lyric as sung: the timeline lists them
(`words`, and `lines`, a new line after a rest of a beat or more, or where a note says "line": true), and `write` puts
them in lyrics.json for `moodreel music --lyrics`, so the picture lights each word on its note.

Bars and beats count from 1 (beat 2.5 is the off-beat after 2); one chord per bar, cycling. Grooves: four (a kick on
every beat), backbeat (kick 1 and 3, snare 2 and 4), halftime (kick 1, snare 3), oompah (bass on 1 and 3, a chord
stab on 2 and 4), none. Parts: kick, snare, clap, hat, bass, pad, stab, pluck (an arpeggio in eighths), lead (a
two-bar motif from the chord tones, seeded). Cue sounds: stab, hit, pop, boing, ding, whoosh, riser (it ends on the
cue), clack, and stop (the band falls silent for `beats`, reverb tails too; other cues still sound in it).

Sampled instruments (real recordings, samples.py; `moodreel samples fetch` first) are parts too: piano (stride on
oompah: bass notes on 1 and 3, chords on 2 and 4; else a held bass note under chords on the beat, or a broken chord
with no groove), strings (the chord held through the bar over its root), pizz (the chord walked a beat at a time),
brass (trumpets and a horn on the stab's beats), tuba (the bass's beats), clarinet and glock (the lead's motif, an
octave and two octaves up), marimba (the pluck's eighths), harp (the chord rising over two octaves in eighths) and
timpani (the root on each downbeat). Sampled cue sounds: brass, piano (a chord), timpani (the root), roll (a timpani
roll that ends on its cue, `beats` long), glock (the chord's top note) and harp (a glissando that ends on its cue).

`render` gives the audio and the timeline; `write` puts `out/score.wav` and `score.js` (the timeline as a module the
picture imports: SCORE, bar(n, beat), cue(name)) in the film folder, and for a score with a band, `music-data.js` for
kit/music.js: the beats, bars and drum hits exactly as written (an analysis of the rendered audio would only estimate
them) and the lyric as sung. The same seed draws the same music.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np

from . import samples
from . import synth as S

NOTES = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
QUALITIES = {"": (0, 4, 7), "m": (0, 3, 7), "7": (0, 4, 7, 10), "maj7": (0, 4, 7, 11), "m7": (0, 3, 7, 10),
             "dim": (0, 3, 6), "sus4": (0, 5, 7), "sus2": (0, 2, 7), "6": (0, 4, 7, 9), "m6": (0, 3, 7, 9)}
GROOVES = ("four", "backbeat", "halftime", "oompah", "none")
LEVEL = {"kick": 0.9, "snare": 0.6, "clap": 0.5, "hat": 0.35, "bass": 0.55, "pad": 0.3, "stab": 0.45, "pluck": 0.35,
         "lead": 0.4, "cue": 0.7, "piano": 0.5, "strings": 0.3, "pizz": 0.45, "brass": 0.45, "tuba": 0.6,
         "clarinet": 0.35, "glock": 0.25, "marimba": 0.4, "harp": 0.3, "timpani": 0.5}
SAMPLED_PARTS = ("piano", "strings", "pizz", "brass", "tuba", "clarinet", "glock", "marimba", "harp", "timpani")
SAMPLED_CUES = ("brass", "piano", "timpani", "roll", "glock", "harp")


def uses_samples(score: dict) -> list[str]:
    """The sampled parts and cue sounds a score asks for."""
    parts = {p for s in score.get("sections", []) for p in s.get("parts") or [] if p in SAMPLED_PARTS}
    cues = {c.get("sound") for c in score.get("cues", []) if c.get("sound") in SAMPLED_CUES}
    return sorted(parts | cues)


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
    words = []
    for s, sec in zip(score["sections"], sections):
        for m in s.get("melody") or []:
            if m.get("word"):
                t0 = bar_t(sec["bar"] + m["bar"] - 1, m.get("beat", 1))
                words.append({"w": m["word"], "start": round(t0, 4), "end": round(t0 + 0.9 * m.get("beats", 1) * beat_s, 4),
                              "line": bool(m.get("line"))})
    words.sort(key=lambda w: w["start"])
    lines = []
    for i, w in enumerate(words):
        if not lines or w["line"] or w["start"] - words[i - 1]["end"] >= 0.9 * beat_s:
            lines.append([])
        lines[-1].append({k: w[k] for k in ("w", "start", "end")})
    lines = [{"text": " ".join(w["w"] for w in ln), "start": ln[0]["start"], "end": ln[-1]["end"], "words": ln} for ln in lines]
    return {"bpm": score["bpm"], "meter": meter, "offset": offset, "beat_s": round(beat_s, 6), "bars": n - 1,
            "duration": round(bar_t(n), 4), "sections": sections, "cues": sorted(cues, key=lambda c: c["t"]),
            "words": [w for ln in lines for w in ln["words"]], "lines": lines}


def music_data(score: dict, tl: dict, audio: np.ndarray | None = None) -> dict:
    """The score as kit/music.js reads it (moodreel music's shape): beats and bars from the grid, the drum hits where
    the grooves put them (claps count as snares), none while a stop cue holds the band, the sung words as vocal hits,
    and the loudness envelope of the rendered audio."""
    beat_s, meter, offset = tl["beat_s"], tl["meter"], tl["offset"]
    hits = {"kick": [], "snare": [], "hat": []}
    for s, sec in zip(score["sections"], tl["sections"]):
        parts, groove = set(s.get("parts") or []), s.get("groove", "backbeat")
        for b in range(s["bars"]):
            for k in range(meter):
                t = sec["start"] + (b * meter + k) * beat_s
                if "kick" in parts and (groove == "four" or (groove == "backbeat" and k % 2 == 0) or (groove == "halftime" and k == 0)):
                    hits["kick"].append([t, 1.0])
                if ("snare" in parts and ((groove in ("backbeat", "four") and k % 2 == 1) or (groove == "halftime" and k == 2))) \
                        or ("clap" in parts and k % 2 == 1 and groove != "halftime"):
                    hits["snare"].append([t, 1.0 if "snare" in parts else 0.8])
                if "hat" in parts and groove != "oompah":
                    hits["hat"] += [[t, 0.6], [t + beat_s / 2, 1.0]]
                elif "hat" in parts and k % 2 == 1:
                    hits["hat"].append([t, 1.0])
    stops = [(c["t"], c["t"] + c.get("beats", 1) * beat_s) for c in tl["cues"] if c["sound"] == "stop"]
    keep = lambda t: not any(a <= t < b for a, b in stops)  # noqa: E731
    n = tl["bars"] * meter
    data = {"duration": tl["duration"], "bpm": tl["bpm"], "fps": 100,
            "beats": [round(offset + i * beat_s, 4) for i in range(n)],
            "downbeats": [round(offset + i * beat_s, 4) for i in range(0, n, meter)],
            "sections": [{"name": x["name"], "start": x["start"], "end": x["end"]} for x in tl["sections"]],
            "onsets": {k: [[round(t, 4), v] for t, v in sorted(h) if keep(t)] for k, h in hits.items()},
            "features": {}, "lyrics": tl["lines"]}
    data["onsets"]["vocal"] = [[w["start"], 0.8] for w in tl["words"]]
    if audio is not None and len(audio):
        hop = S.SR // 100
        rms = np.sqrt(np.convolve(audio.astype(np.float64) ** 2, np.ones(hop) / hop, mode="same")[::hop])
        data["features"]["rms"] = [round(float(x), 3) for x in np.clip(rms / (np.percentile(rms, 99) + 1e-9), 0, 1)]
    return data


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
        _sampled(buf, parts, groove, name, t0, beat_s, meter, lead_motif, b)
        if "pad" in parts:
            _place(buf, S.pad(tones, meter * beat_s, rng, LEVEL["pad"]), t0)
        if "lead" in parts and s.get("melody"):           # the lead as written
            for m in s["melody"]:
                if m["bar"] - 1 == b:
                    k = m.get("tone", 0)
                    note = m["note"] if "note" in m else tones[k % len(tones)] + 12 * (1 + m.get("oct", 0) + k // len(tones))
                    _place(buf, S.lead(note, 0.9 * m.get("beats", 1) * beat_s, rng, LEVEL["lead"]), t0 + (m.get("beat", 1) - 1) * beat_s)
        elif "lead" in parts:                              # the same two-bar motif over every pair of bars
            t, end = t0, t0 + meter * beat_s
            for deg, dur in lead_motif[(b % 2) * 4:(b % 2) * 4 + 4]:
                if t >= end:
                    break
                _place(buf, S.lead(tones[deg % len(tones)] + 12, min(dur * beat_s, end - t) * 0.9, rng, LEVEL["lead"]), t)
                t += dur * beat_s


def _sampled(buf, parts, groove, name, t0, beat_s, meter, motif, b):
    """One bar of the sampled parts."""
    if not parts & set(SAMPLED_PARTS):
        return
    N, C = samples.note, samples.chord
    tones, low, mid = _voicing(name, 60), _voicing(name, 36)[0], _voicing(name, 48)
    beat = lambda k: t0 + k * beat_s                       # noqa: E731
    bar = meter * beat_s
    if "piano" in parts:
        if groove == "oompah":                             # stride: bass notes on 1 and 3, the chord on 2 and 4
            for k in range(meter):
                x = N("piano", low + (7 if k == 2 else 0), 0.8 * beat_s, LEVEL["piano"]) if k % 2 == 0 else \
                    C("piano", tones, 0.6 * beat_s, LEVEL["piano"] * 0.9)
                _place(buf, x, beat(k))
        elif groove == "none":                              # a broken chord in eighths over a held bass note
            _place(buf, N("piano", low + 12, bar, LEVEL["piano"] * 0.8), t0)
            for e in range(2 * meter):
                _place(buf, N("piano", tones[e % len(tones)] + 12 * (e // len(tones) % 2), 0.9 * beat_s, LEVEL["piano"] * 0.7),
                       t0 + e * beat_s / 2)
        else:                                               # a held bass note, chords on the beat
            _place(buf, N("piano", low, bar, LEVEL["piano"]), t0)
            for k in range(meter):
                if groove == "four" or k % 2 == 0:
                    _place(buf, C("piano", tones, 0.9 * beat_s, LEVEL["piano"] * (1 if k == 0 else 0.8)), beat(k))
    if "strings" in parts:                                 # the chord held through the bar over its root
        _place(buf, C("strings", [mid[0] - 12, *tones], bar, LEVEL["strings"]), t0)
    if "pizz" in parts:                                    # the chord walked a beat at a time
        walk = [mid[0], mid[1], mid[2 % len(mid)], mid[1]]
        for k in range(meter):
            _place(buf, N("pizz", walk[k % 4], 0.5 * beat_s, LEVEL["pizz"]), beat(k))
    if "brass" in parts:                                   # trumpets on the chord, a horn on the root, on the stab's beats
        for k in range(meter):
            if (groove == "oompah" and k % 2 == 1) or (groove != "oompah" and k == 0):
                x = C("trumpet", tones, 0.35 * beat_s, LEVEL["brass"])
                h = N("horn", mid[0], 0.35 * beat_s, LEVEL["brass"] * 0.8)
                _place(buf, x, beat(k))
                _place(buf, h, beat(k))
    if "tuba" in parts:                                    # the bass's beats
        for k in range(meter):
            if k % 2 == 0:
                _place(buf, N("tuba", low + (7 if groove == "oompah" and k == 2 else 0), 0.7 * beat_s, LEVEL["tuba"]), beat(k))
    for inst, up in (("clarinet", 12), ("glock", 24)):     # the lead's motif
        if inst in parts:
            t, end = t0, t0 + bar
            for deg, dur in motif[(b % 2) * 4:(b % 2) * 4 + 4]:
                if t >= end:
                    break
                d = min(dur * beat_s, end - t) * (0.9 if inst == "clarinet" else 0.5)
                _place(buf, N(inst, tones[deg % len(tones)] + up, d, LEVEL[inst]), t)
                t += dur * beat_s
    if "marimba" in parts:                                 # the pluck's eighths
        for e in range(2 * meter):
            _place(buf, N("marimba", tones[e % len(tones)] + 12, 0.4 * beat_s, LEVEL["marimba"]), t0 + e * beat_s / 2)
    if "harp" in parts:                                    # the chord rising over two octaves in eighths
        rise = [m + 12 * o for o in (0, 1, 2) for m in mid]
        for e in range(2 * meter):
            _place(buf, N("harp", rise[e % len(rise)], 1.2 * beat_s, LEVEL["harp"]), t0 + e * beat_s / 2)
    if "timpani" in parts:                                 # the root on each downbeat
        _place(buf, N("timpani", 41 + (low - 41) % 12, beat_s, LEVEL["timpani"]), t0)


def _cue_sampled(snd: str, chord_name: str, beats: float, beat_s: float) -> tuple[np.ndarray, float]:
    """A sampled cue sound and how long before its cue it starts (a roll or glissando ends on it)."""
    tones, low, mid = _voicing(chord_name, 60), _voicing(chord_name, 36)[0], _voicing(chord_name, 48)
    lvl = LEVEL["cue"]
    if snd == "brass":
        x = samples.chord("trumpet", tones, 0.5 * beat_s, lvl)
        h = samples.note("horn", mid[0], 0.5 * beat_s, lvl * 0.8)
        n = max(len(x), len(h))
        return np.pad(x, (0, n - len(x))) + np.pad(h, (0, n - len(h))), 0.0
    if snd == "piano":
        x = samples.chord("piano", [low, *tones, tones[0] + 12], 1.5 * beat_s, lvl)
        return x, 0.0
    if snd == "timpani":
        return samples.note("timpani", 41 + (low - 41) % 12, 1.5 * beat_s, lvl), 0.0
    if snd == "roll":                                      # a roll that swells into its cue
        d = beats * beat_s
        x = samples.note("timpani_roll", 41 + (low - 41) % 12, d, lvl)[: int(d * S.SR)]
        return x * np.linspace(0.25, 1, len(x), dtype=np.float32) ** 1.5, d
    if snd == "glock":
        return samples.note("glock", tones[-1] + 24, beat_s, lvl * 0.7), 0.0
    if snd == "harp":                                      # a glissando up an octave and a half
        steps = [m + 12 * o for o in (0, 1) for m in mid] + [mid[0] + 24]
        d, out = 0.5, np.zeros(int((0.5 + 2.0) * S.SR), np.float32)
        for k, m in enumerate(steps):
            _place(out, samples.note("harp", m, 1.5, lvl * 0.7), k * d / (len(steps) - 1))   # the last on the cue
        return out, d
    raise ValueError(snd)


def render(score: dict) -> tuple[np.ndarray, dict]:
    tl = timeline(score)
    need = uses_samples(score)
    if need and not samples.ready():
        raise SystemExit(f"score.json uses sampled instruments ({', '.join(need)}): run `moodreel samples fetch` first "
                         "(downloads 272 MB of CC0 samples, once)")
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
        elif snd in SAMPLED_CUES:
            bar = int((t - tl["offset"]) / (meter * beat_s))
            names = [ch for s in score["sections"] for b in range(s["bars"]) for ch in [s["chords"][b % len(s["chords"])]]] or ["C"]
            x, lead_in = _cue_sampled(snd, names[min(bar, len(names) - 1)], c.get("beats", 2), beat_s)
            t -= lead_in
        elif snd in S.FOLEY:
            x = S.FOLEY[snd](rng, LEVEL["cue"])
        else:
            raise ValueError(f"cue {c['name']}: sound {snd!r} is not one of stop, stab, {', '.join(S.FOLEY)}, "
                             f"{', '.join(SAMPLED_CUES)}")
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
    if tl["lines"]:                                        # the lyric as sung, for `moodreel music --lyrics`
        (film / "lyrics.json").write_text(json.dumps(tl["lines"], indent=1))
    if any(s.get("parts") for s in score["sections"]):     # the music as data, exactly as written
        from ..measure.music import write_module
        write_module(music_data(score, tl, audio), film / "music-data.js", "the film's own score, from score.json")
    credits = film / "CREDITS"
    if uses_samples(score) and credits.exists() and samples.credit() not in credits.read_text():
        text = credits.read_text()
        credits.write_text(text + ("" if text.endswith("\n") else "\n") + f"- {samples.credit()}\n")
    return {"wav": str(wav), "js": str(film / "score.js"), **{k: tl[k] for k in ("bpm", "bars", "duration")},
            "cues": len(tl["cues"]), "words": len(tl["words"])}
