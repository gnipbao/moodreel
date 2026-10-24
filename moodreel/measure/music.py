"""Music as data for a film to follow: the beat grid and bars, drum hits by kind, loudness envelopes, and (when given)
the lyric's words as sung. `moodreel music` writes it as a music-data.js module that kit/music.js reads.

The method follows mexicat/pdoom-video (MIT), a music video whose every motion is computed from aligned data: a
constant-tempo grid fitted over the whole song and its phase refined on the kicks; bars from the backbeat (snare on 2
and 4); kick, snare and hat onsets; 100 fps envelopes. pdoom-video separates stems (Demucs) and aligns the lyric
(forced alignment checked against Whisper); this works on the mix alone, by frequency band, and takes word timings
from a file (any aligner's, or pdoom-video's own JSON).

Measured against pdoom-video's data for its own song, see docs/MUSIC-SYNC.md for the numbers.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from .rhythm import load_audio, onset_envelope, tempo, SR

HOP, WIN = 256, 2048
FPS_ENV = SR / HOP
FPS_OUT = 100
BANDS = {"low": (30, 150), "mid": (300, 3000), "high": (6000, 11000)}
LATENCY = 0.0                       # the detector's lag behind the true attack, s (set from the calibration)


def _spectrum(y: np.ndarray) -> np.ndarray:
    n = 1 + (len(y) - WIN) // HOP
    idx = np.arange(WIN)[None, :] + HOP * np.arange(n)[:, None]
    return np.abs(np.fft.rfft(y[idx] * np.hanning(WIN), axis=1))


def _band(spec: np.ndarray, lo: float, hi: float) -> np.ndarray:
    f = np.fft.rfftfreq(WIN, 1 / SR)
    return spec[:, (f >= lo) & (f < hi)].sum(axis=1)


def _flux(e: np.ndarray) -> np.ndarray:
    le = np.log1p(e / (np.median(e) + 1e-9))
    return np.concatenate([[0.0], np.maximum(np.diff(le), 0)])


def _peaks(x: np.ndarray, gap_s: float, k: float = 2.5) -> list[tuple[int, float]]:
    """Local maxima above median + k * MAD, at least gap_s apart (the stronger kept), with strength 0..1."""
    med = np.median(x)
    thr = med + k * 1.4826 * np.median(np.abs(x - med)) + 1e-9
    gap = max(1, int(round(gap_s * FPS_ENV)))
    out: list[tuple[int, float]] = []
    for i in range(1, len(x) - 1):
        if x[i] <= thr or x[i] < x[i - 1] or x[i] < x[i + 1]:
            continue
        if out and i - out[-1][0] < gap:
            if x[i] > out[-1][1]:
                out[-1] = (i, float(x[i]))
            continue
        out.append((i, float(x[i])))
    if not out:
        return []
    top = np.percentile([v for _, v in out], 95)
    return [(i, float(min(1.0, v / top))) for i, v in out]


def _times(frames, win: int = WIN) -> np.ndarray:
    # the rise in a Hann-windowed frame's energy is steepest when an attack is three quarters of the way into the
    # window, so that is where the flux peaks (measured on synthetic drums: 0.754 of the window)
    return (np.asarray(frames, float) * HOP + 0.75 * win) / SR - LATENCY


def _grid(env: np.ndarray, bpm0: float, duration: float) -> tuple[float, float]:
    """Tempo and phase of the constant grid that collects the most onset strength over the whole song."""
    t = np.arange(len(env)) / FPS_ENV
    best = (-np.inf, bpm0, 0.0)
    for bpm in np.arange(bpm0 * 0.985, bpm0 * 1.015, 0.002):
        p = 60 / bpm
        phases = np.linspace(0, p, 96, endpoint=False)
        k = np.arange(int(duration / p) + 1)
        pts = phases[:, None] + k[None, :] * p
        s = np.interp(pts, t, env, right=0).sum(axis=1)
        j = int(np.argmax(s))
        if s[j] > best[0]:
            best = (float(s[j]), float(bpm), float(phases[j]))
    return best[1], best[2]


def analyse(path: str | Path, lyrics=None, grid: bool = True) -> dict:
    """The song at `path` as data: {duration, bpm, fps, beats, downbeats, sections, onsets, features} (+ lyrics).
    grid: a drum must sit where a 4/4 groove puts it (true of most pop and dance; pass False for anything else)."""
    y = load_audio(str(path))
    if y is None or len(y) < SR:
        raise ValueError(f"{path}: no audio, or under a second of it")
    duration = len(y) / SR
    spec = _spectrum(y)
    full = onset_envelope(y)
    bpm0, _ = tempo(full)
    bpm, phase = _grid(np.interp(np.arange(len(spec)) * HOP / SR, _times(np.arange(len(full)), 1024), full), bpm0, duration)
    bands = {k: _band(spec, *v) for k, v in BANDS.items()}
    flux = {k: _flux(v) for k, v in bands.items()}
    kick = _peaks(flux["low"], 0.12)
    snare = _peaks(np.maximum(flux["mid"] - 0.5 * flux["low"], 0), 0.15)
    hat = _peaks(flux["high"], 0.07)
    period = 60 / bpm
    kt = _times([i for i, _ in kick])
    near = [(t - phase) / period for t in kt]
    d = [(x - round(x)) * period for x in near if abs(x - round(x)) * period < 0.06]
    if d:                                                    # the phase, refined on the kicks' attacks
        phase += float(np.median(d))
    phase %= period
    beats = np.arange(phase, duration, period)
    st = _times([i for i, _ in snare])
    ss = np.array([s for _, s in snare])

    def backbeat(o):                                         # snares on beats 2 and 4 of bars starting at beat o
        if not len(st):
            return 0.0
        b = np.round((st - phase) / period).astype(int)
        on = np.abs((st - phase) / period - b) < 0.12
        return float(ss[on & (((b - o) % 4 == 1) | ((b - o) % 4 == 3))].sum() - ss[on & ((b - o) % 2 == 0)].sum())
    o = max(range(4), key=backbeat)
    downbeats = beats[o::4]
    # without separated stems the bands also catch bass, synths and voice: keep a hit only where the grid expects that
    # drum (kicks on beats, snares on 2 and 4, hats on eighths) and only when it is strong enough (thresholds and
    # windows from the calibration in docs/MUSIC-SYNC.md); grid=False keeps every hit above its threshold
    def keep(found, where, tol, thr):
        if not grid:
            return [x for x in found if x[1] >= thr]
        return [x for x in found if x[1] >= thr and len(where) and np.min(np.abs(where - x[0])) <= tol]
    idx = np.arange(len(beats))
    on = {"kick": (beats, 0.05, 0.30), "snare": (beats[(idx - o) % 2 == 1], 0.05, 0.45),
          "hat": (np.sort(np.concatenate([beats, beats + period / 2])), 0.04, 0.30)}
    hits = {name: keep(list(zip(_times([i for i, _ in p]), [s for _, s in p])), *on[name])
            for name, p in (("kick", kick), ("snare", snare), ("hat", hat))}
    tt = np.arange(int(round(duration * FPS_OUT))) / FPS_OUT
    tf = np.arange(len(spec)) * HOP / SR + WIN / 2 / SR

    def norm(e):
        v = np.interp(tt, tf, e)
        return [round(float(x), 3) for x in np.clip(v / (np.percentile(v, 99) + 1e-9), 0, 1)]
    rms = np.sqrt(np.convolve(y ** 2, np.ones(HOP) / HOP, mode="same")[::HOP][:len(spec)])
    data = {
        "duration": round(duration, 3), "bpm": round(bpm, 3), "fps": FPS_OUT,
        "beats": [round(float(b), 4) for b in beats], "downbeats": [round(float(b), 4) for b in downbeats],
        "sections": [],
        "onsets": {name: [[round(float(t), 4), round(float(s), 3)] for t, s in h if t >= 0] for name, h in hits.items()},
        "features": {"rms": norm(rms), **{k: norm(v) for k, v in bands.items()}},
    }
    data["onsets"]["vocal"] = []
    if lyrics:
        data["lyrics"] = lyrics
        data["onsets"]["vocal"] = [[w["start"], 0.8] for line in lyrics for w in line["words"]]
    return data


def load_lyrics(path: str | Path) -> list[dict]:
    """Word timings as lines [{text, start, end, words: [{w, start, end}]}]: pdoom-video's lyrics.json ({"lines": ...}),
    a list of such lines, or a flat list of words [{w, start, end}] (one line)."""
    j = json.loads(Path(path).read_text())
    lines = j["lines"] if isinstance(j, dict) else j
    if lines and "words" not in lines[0]:
        lines = [{"text": " ".join(w["w"] for w in lines), "start": lines[0]["start"], "end": lines[-1]["end"], "words": lines}]
    return [{"text": ln.get("text") or " ".join(w["w"] for w in ln["words"]), "start": ln["start"], "end": ln["end"],
             "words": [{"w": w["w"], "start": w["start"], "end": w["end"]} for w in ln["words"]]} for ln in lines]


def from_json(path: str | Path, lyrics=None, offset: float = 0.0) -> dict:
    """An analysis made elsewhere, in pdoom-video's audio.json shape (envelopes at the top level or under features),
    shifted by `offset` seconds."""
    a = json.loads(Path(path).read_text())
    sh = lambda xs: [round(x + offset, 4) for x in xs]   # noqa: E731
    feats = a.get("features") or {k: a[k] for k in ("rms", "low", "mid", "high", "vocal", "drums", "bass", "other") if k in a}
    data = {"duration": a["duration"], "bpm": a["bpm"], "fps": a.get("fps", FPS_OUT), "beats": sh(a["beats"]),
            "downbeats": sh(a.get("downbeats", [])),
            "sections": [{**s, "start": s["start"] + offset, "end": s["end"] + offset} for s in a.get("sections", [])],
            "onsets": {k: [[round(t + offset, 4), s] for t, s in v] for k, v in a.get("onsets", {}).items()},
            "features": {k: [round(x, 3) for x in v] for k, v in feats.items()}}
    if lyrics:
        data["lyrics"] = [{**ln, "start": ln["start"] + offset, "end": ln["end"] + offset,
                           "words": [{**w, "start": w["start"] + offset, "end": w["end"] + offset} for w in ln["words"]]}
                          for ln in lyrics]
    return data


def write_module(data: dict, out: str | Path, credit: str = "") -> Path:
    """music-data.js: `export const AUDIO = {...}; export const LYRICS = [...]` for kit/music.js."""
    out = Path(out)
    audio = {k: v for k, v in data.items() if k != "lyrics"}
    head = "// The song as data, written by `moodreel music`" + (f" ({credit})" if credit else "") + ". Read it with kit/music.js.\n"
    out.write_text(head + "export const AUDIO = " + json.dumps(audio, separators=(",", ":")) + ";\n"
                   + "export const LYRICS = " + json.dumps(data.get("lyrics", []), ensure_ascii=False, separators=(",", ":")) + ";\n")
    return out


def match(found, truth, tol: float = 0.035) -> dict:
    """Onsets found against true ones: recall, precision and the median offset of the matched pairs."""
    f, r = np.asarray([x[0] for x in found]), np.asarray([x[0] for x in truth])
    if not len(f) or not len(r):
        return {"recall": 0.0, "precision": 0.0, "offset_ms": None}
    d_r = np.abs(r[:, None] - f[None]).min(axis=1)
    d_f = np.abs(f[:, None] - r[None]).min(axis=1)
    j = np.abs(r[:, None] - f[None]).argmin(axis=1)
    off = (f[j] - r)[d_r <= tol]
    return {"recall": round(float((d_r <= tol).mean()), 2), "precision": round(float((d_f <= tol).mean()), 2),
            "offset_ms": round(float(np.median(off)) * 1000, 1) if len(off) else None}
