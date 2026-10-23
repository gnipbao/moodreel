"""Instruments drawn in numpy: every sound is a function of its parameters and a seed, so a score renders the same
every time. Each returns a mono float32 buffer at SR, starting at its onset; the score places and mixes them.

Drums (kick, snare, clap, hat), pitched parts (bass, pad, stab, pluck, lead) and the pitched foley that picture events
call for (pop, boing, ding, whoosh, riser, hit, clack). Not samples of real instruments: a toy band, bright and dry,
which is what game-show, microgame and cartoon scores ask for; a sampled orchestra is a later step.
"""
from __future__ import annotations

import numpy as np
from scipy.signal import lfilter

SR = 48000
BLOCK = 256          # samples a moving filter keeps one cutoff for


def _t(dur: float) -> np.ndarray:
    return np.arange(int(dur * SR)) / SR


def _env(n: int, attack: float, decay: float, sustain: float = 0.0, release: float = 0.0, hold: float | None = None):
    """Attack, then exponential decay toward `sustain`, held for `hold` s, then released."""
    t = np.arange(n) / SR
    a = np.clip(t / max(attack, 1e-4), 0, 1)
    d = sustain + (1 - sustain) * np.exp(-np.maximum(t - attack, 0) / max(decay, 1e-4))
    e = a * d
    if hold is not None and release > 0:
        e *= np.clip(1 - (t - hold) / release, 0, 1)
    return e


def _lowpass(x: np.ndarray, cutoff) -> np.ndarray:
    """One-pole low-pass; `cutoff` in Hz, a number or one per sample (a filter that opens or closes, followed a
    block at a time with its state carried over)."""
    c = np.asarray(cutoff, float)
    if c.ndim == 0:
        k = 1 - np.exp(-2 * np.pi * float(c) / SR)
        return lfilter([k], [1, k - 1], x)
    y, zi = np.empty_like(x), np.zeros(1)
    for i in range(0, len(x), BLOCK):
        k = 1 - np.exp(-2 * np.pi * float(c[i]) / SR)
        y[i:i + BLOCK], zi = lfilter([k], [1, k - 1], x[i:i + BLOCK], zi=zi)
    return y


def _highpass(x: np.ndarray, cutoff: float) -> np.ndarray:
    return x - _lowpass(x, cutoff)


def _saw(f, t, phase=0.0):
    p = np.cumsum(np.broadcast_to(f, t.shape)) / SR + phase
    return 2 * (p % 1) - 1


def _square(f, t, duty=0.5):
    p = np.cumsum(np.broadcast_to(f, t.shape)) / SR
    return np.where(p % 1 < duty, 1.0, -1.0)


def _noise(n, rng):
    return rng.uniform(-1, 1, n)


def hz(midi: float) -> float:
    return 440.0 * 2 ** ((midi - 69) / 12)


# drums ---------------------------------------------------------------------------------------------------------------

def kick(rng, level=1.0):
    t = _t(0.45)
    f = 45 + 95 * np.exp(-t / 0.035)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * _env(len(t), 0.001, 0.16)
    return (np.tanh(2.2 * x) * level).astype(np.float32)


def snare(rng, level=1.0):
    t = _t(0.25)
    body = np.sin(2 * np.pi * 185 * t) * _env(len(t), 0.001, 0.05)
    hiss = _highpass(_noise(len(t), rng), 1800) * _env(len(t), 0.001, 0.09)
    return ((0.6 * body + 0.8 * hiss) * level).astype(np.float32)


def clap(rng, level=1.0):
    t = _t(0.3)
    burst = np.zeros(len(t))
    for k, at in enumerate((0.0, 0.011, 0.022)):
        i = int(at * SR)
        burst[i:] += _env(len(t) - i, 0.0005, 0.012 if k < 2 else 0.11)
    x = _highpass(_lowpass(_noise(len(t), rng), 5000), 900) * burst
    return (x * level).astype(np.float32)


def hat(rng, level=1.0, open_=False):
    t = _t(0.35 if open_ else 0.06)
    x = _highpass(_noise(len(t), rng), 7000) * _env(len(t), 0.0005, 0.12 if open_ else 0.018)
    return (0.5 * x * level).astype(np.float32)


# pitched parts -------------------------------------------------------------------------------------------------------

def bass(note, dur, rng, level=1.0):
    t = _t(dur + 0.05)
    x = 0.6 * _saw(hz(note), t) + 0.4 * _square(hz(note), t)
    x = _lowpass(x, 300 + 900 * np.exp(-t / 0.08)) * _env(len(t), 0.004, 0.25, 0.55, 0.04, dur)
    return (np.tanh(1.5 * x) * level).astype(np.float32)


def pad(notes, dur, rng, level=1.0):
    t = _t(dur + 0.3)
    x = sum(_saw(hz(n) * (1 + d), t, rng.uniform()) for n in notes for d in (-0.004, 0.0, 0.005))
    x = _lowpass(x / (3 * len(notes)), 1400) * _env(len(t), 0.25, 0.6, 0.8, 0.3, dur)
    return (x * level).astype(np.float32)


def stab(notes, dur, rng, level=1.0):
    """Brass-like: a saw chord whose filter snaps open and closes."""
    t = _t(max(dur, 0.18) + 0.1)
    x = sum(_saw(hz(n) * (1 + d), t, rng.uniform()) for n in notes for d in (-0.003, 0.003))
    x = _lowpass(x / (2 * len(notes)), 500 + 4500 * np.exp(-t / 0.07)) * _env(len(t), 0.006, 0.12, 0.35, 0.06, dur)
    return (np.tanh(1.8 * x) * level).astype(np.float32)


def pluck(note, dur, rng, level=1.0):
    """Karplus-Strong: a noise burst through a damped delay line."""
    n = int((dur + 0.3) * SR)
    period = max(2, int(round(SR / hz(note))))
    burst = np.zeros(n)
    burst[:period] = _noise(period, rng)
    a = np.zeros(period + 2)
    a[0], a[period], a[period + 1] = 1.0, -0.498, -0.498   # y[n] = x[n] + 0.996 * mean(y[n-p], y[n-p-1])
    out = lfilter([1.0], a, burst)
    return (0.6 * out * _env(n, 0.001, 0.6) * level).astype(np.float32)


def lead(note, dur, rng, level=1.0):
    t = _t(dur + 0.05)
    vib = 1 + 0.006 * np.sin(2 * np.pi * 5.5 * t) * np.clip((t - 0.12) / 0.2, 0, 1)
    x = _lowpass(_square(hz(note) * vib, t, 0.4), 3200) * _env(len(t), 0.01, 0.3, 0.6, 0.05, dur)
    return (0.45 * x * level).astype(np.float32)


# foley: what a picture event sounds like -----------------------------------------------------------------------------

def pop(rng, level=1.0, note=84):
    t = _t(0.09)
    f = hz(note) * (0.6 + 0.8 * np.clip(t / 0.03, 0, 1))
    return (np.sin(2 * np.pi * np.cumsum(f) / SR) * _env(len(t), 0.001, 0.025) * level).astype(np.float32)


def boing(rng, level=1.0, note=55):
    t = _t(0.5)
    f = hz(note) * (1 + 0.5 * np.exp(-t / 0.1) * np.sin(2 * np.pi * 14 * t))
    return (0.8 * np.sin(2 * np.pi * np.cumsum(f) / SR) * _env(len(t), 0.002, 0.18) * level).astype(np.float32)


def ding(rng, level=1.0, note=88):
    t = _t(1.2)
    x = sum(a * np.sin(2 * np.pi * hz(note) * r * t) * np.exp(-t / d)
            for r, a, d in ((1, 1, 0.6), (2.76, 0.4, 0.25), (5.4, 0.2, 0.1), (8.93, 0.1, 0.05)))
    return (0.5 * x * _env(len(t), 0.001, 10) * level).astype(np.float32)


def whoosh(rng, level=1.0, dur=0.4):
    t = _t(dur)
    shape = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 2
    x = _lowpass(_noise(len(t), rng), 400 + 5000 * shape) * shape
    return (0.8 * x * level).astype(np.float32)


def riser(rng, level=1.0, dur=1.0):
    t = _t(dur)
    u = t / dur
    x = 0.5 * _lowpass(_noise(len(t), rng), 300 + 8000 * u ** 2) + 0.3 * np.sin(2 * np.pi * np.cumsum(200 + 1200 * u ** 2) / SR)
    return (x * u ** 2 * level).astype(np.float32)


def hit(rng, level=1.0):
    k = kick(rng, 1.2)
    crash = _highpass(_noise(int(1.0 * SR), rng), 4000) * _env(int(1.0 * SR), 0.001, 0.35)
    out = np.zeros(len(crash))
    out[:len(k)] += k
    return ((out + 0.5 * crash) * level).astype(np.float32)


def clack(rng, level=1.0, note=79):
    t = _t(0.08)
    x = np.sin(2 * np.pi * hz(note) * t) * _env(len(t), 0.0005, 0.012) + 0.3 * _noise(len(t), rng) * _env(len(t), 0.0005, 0.004)
    return (x * level).astype(np.float32)


FOLEY = {"pop": pop, "boing": boing, "ding": ding, "whoosh": whoosh, "riser": riser, "hit": hit, "clack": clack}


def _room(size: float) -> np.ndarray:
    """The impulse response of a small Schroeder room (four combs in parallel, two all-passes in series), 1.5 s."""
    imp = np.zeros(int(1.5 * SR))
    imp[0] = 1.0
    wet = np.zeros_like(imp)
    for d in (1557, 1617, 1491, 1422):                    # comb: y[n] = x[n] + g y[n-d]
        delay, g = int(d * (0.6 + 0.8 * size)), 0.7 + 0.25 * size
        a = np.zeros(delay + 1)
        a[0], a[delay] = 1.0, -g
        wet += lfilter([1.0], a, imp)
    wet /= 4
    for d, g in ((225, 0.5), (556, 0.5)):                 # all-pass: y[n] = -g x[n] + x[n-d] + g y[n-d]
        b, a = np.zeros(d + 1), np.zeros(d + 1)
        b[0], b[d], a[0], a[d] = -g, 1.0, 1.0, -g
        wet = lfilter(b, a, wet)
    return wet * np.linspace(1, 0, len(wet)) ** 2          # its tail faded out within the 1.5 s


def reverb(x: np.ndarray, size: float = 0.5, mix: float = 0.2) -> np.ndarray:
    """x in a small room, with its 1.5 s tail; the room's response is convolved in (FFT), not run sample by sample."""
    from scipy.signal import fftconvolve
    xin = np.concatenate([x, np.zeros(int(1.5 * SR))]).astype(np.float64)
    wet = fftconvolve(xin, _room(size))[: len(xin)]
    return (xin * (1 - mix) + wet * mix).astype(np.float32)
