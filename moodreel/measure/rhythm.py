"""Rhythm: the tempo of a reference's soundtrack, and whether its cuts and arrivals land on the beat.

Onsets come from spectral flux; the tempo from the onset envelope's autocorrelation (60-200 BPM); the beats from
the phase of that tempo that collects the most onset strength. Whether the picture follows the music is judged
against chance: with a +/- tolerance around each beat, a random event lands "on a beat" 2 * tol / period of the time.
"""
from __future__ import annotations

import subprocess

import numpy as np

SR, HOP, WIN = 22050, 256, 1024


def load_audio(path: str) -> np.ndarray | None:
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vn", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                       capture_output=True)
    if r.returncode or not r.stdout:
        return None
    return np.frombuffer(r.stdout, np.float32)


def onset_envelope(y: np.ndarray) -> np.ndarray:
    n = 1 + (len(y) - WIN) // HOP
    if n < 8:
        return np.zeros(0)
    idx = np.arange(WIN)[None, :] + HOP * np.arange(n)[:, None]
    spec = np.log1p(np.abs(np.fft.rfft(y[idx] * np.hanning(WIN), axis=1)) * 10)
    flux = np.maximum(np.diff(spec, axis=0), 0).sum(axis=1)
    flux = np.concatenate([[0], flux])
    return (flux - flux.mean()) / (flux.std() + 1e-9)


def tempo(env: np.ndarray) -> tuple[float, float]:
    fps = SR / HOP
    lags = np.arange(int(fps * 60 / 200), int(fps * 60 / 60) + 1)
    e = env - env.mean()
    ac = np.array([float((e[:-L] * e[L:]).mean()) if L < len(e) else 0.0 for L in lags])
    prior = np.exp(-0.5 * (np.log2((60 * fps / lags) / 110)) ** 2)      # a mild preference for moderate tempos
    k = int(np.argmax(ac * prior))
    return 60 * fps / lags[k], float(ac[k] / (ac.max() + 1e-9))


def beats(env: np.ndarray, bpm: float) -> np.ndarray:
    fps = SR / HOP
    period = 60 * fps / bpm
    best, best_phase = -np.inf, 0.0
    for phase in np.linspace(0, period, 48, endpoint=False):
        idx = np.round(np.arange(phase, len(env), period)).astype(int)
        idx = idx[idx < len(env)]
        s = env[idx].sum()
        if s > best:
            best, best_phase = s, phase
    return np.arange(best_phase, len(env), period) / fps


def on_beat(times, beat_times, tol: float) -> dict:
    times = np.asarray([t for t in times if t is not None], float)
    if not len(times) or len(beat_times) < 2:
        return {"events": int(len(times)), "share": None, "chance": None}
    d = np.abs(times[:, None] - np.asarray(beat_times)[None]).min(axis=1)
    period = float(np.median(np.diff(beat_times)))
    return {"events": int(len(times)), "share": round(float((d <= tol).mean()), 2),
            "chance": round(min(1.0, 2 * tol / period), 2)}


def rhythm(path: str, cut_times=(), event_times=(), fps: float = 30.0) -> dict:
    y = load_audio(path)
    if y is None or len(y) < SR:
        return {"audio": False}
    env = onset_envelope(y)
    bpm, clarity = tempo(env)
    bt = beats(env, bpm)
    tol = max(1.0 / fps, 0.04)
    return {"audio": True, "bpm": round(bpm, 1), "clarity": round(clarity, 2), "beats": len(bt),
            "loudness_rms_db": round(float(20 * np.log10(np.sqrt(np.mean(y ** 2)) + 1e-9)), 1),
            "cuts_on_beat": on_beat(cut_times, bt, tol), "arrivals_on_beat": on_beat(event_times, bt, tol)}
