"""Instruments drawn in numpy: every sound is a function of its parameters and a seed, so a score renders the same
every time. Each returns a mono float32 buffer at SR, starting at its onset; the score places and mixes them.

Drums (kick, snare, clap, hat), pitched parts (bass, pad, stab, pluck, lead), the pitched foley that picture events
call for (pop, boing, ding, whoosh, riser, hit, clack), and motion-graphics foley (slam, key, glitch, tear, stamp,
crackle, boom, tick, rewind, swish, click, zap, thud). Not samples of real instruments: a toy band, bright and dry,
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


# motion-graphics foley: the sounds a lyric or title film's picture makes (words slammed down, keys, glitches, sparks)

def slam(rng, level=1.0):
    """A word slammed down: a low thump and a short crack."""
    t = _t(0.5)
    thump = np.sin(2 * np.pi * np.cumsum(38 + 70 * np.exp(-t / 0.03)) / SR) * _env(len(t), 0.001, 0.12)
    crack = _highpass(_lowpass(_noise(len(t), rng), 6000), 600) * _env(len(t), 0.0005, 0.018)
    return (np.tanh(1.6 * (0.9 * thump + 0.5 * crack)) * 0.8 * level).astype(np.float32)


def key(rng, level=1.0):
    """A key of a mechanical keyboard: a click and a short plastic knock, a little different every time."""
    t = _t(0.05)
    click = _highpass(_noise(len(t), rng), 2500) * _env(len(t), 0.0002, 0.004)
    knock = np.sin(2 * np.pi * (900 + 300 * rng.uniform()) * t) * _env(len(t), 0.0005, 0.008)
    return ((0.6 * click + 0.35 * knock) * level).astype(np.float32)


def glitch(rng, level=1.0, dur=0.25):
    """Digital breakup: stepped noise, a buzz and gaps, cut in 8-40 ms pieces."""
    n, i = int(dur * SR), 0
    x = np.zeros(n)
    while i < n:
        seg = min(int(rng.uniform(0.008, 0.04) * SR), n - i)
        t, kind = np.arange(seg) / SR, rng.integers(3)
        if kind == 0:
            x[i:i + seg] = np.repeat(rng.uniform(-1, 1, seg // 24 + 1), 24)[:seg]
        elif kind == 1:
            x[i:i + seg] = 0.6 * _square(rng.uniform(80, 900), t)
        i += seg
    return (0.45 * x * level).astype(np.float32)


def tear(rng, level=1.0, dur=0.35):
    """Paper torn in two: a crackle that thickens into a rip."""
    t = _t(dur)
    n, u = len(t), t / dur
    crackle = (rng.uniform(0, 1, n) < 0.02 + 0.5 * u ** 2) * rng.uniform(-1, 1, n)
    x = _highpass(_lowpass(crackle + 0.3 * _noise(n, rng) * u, 7000), 800) * (0.3 + 0.7 * u) * np.clip((1 - u) / 0.1, 0, 1)
    return (0.7 * x * level).astype(np.float32)


def stamp(rng, level=1.0):
    """A rubber stamp slammed onto paper on a desk."""
    t = _t(0.3)
    thud_ = np.sin(2 * np.pi * np.cumsum(70 + 60 * np.exp(-t / 0.015)) / SR) * _env(len(t), 0.001, 0.06)
    slap = _highpass(_lowpass(_noise(len(t), rng), 3000), 300) * _env(len(t), 0.0005, 0.02)
    return (np.tanh(1.4 * (0.9 * thud_ + 0.6 * slap)) * 0.8 * level).astype(np.float32)


def crackle(rng, level=1.0, dur=1.0):
    """A burning fuse or a sparking wire: sparse sharp pops over a hiss, for `dur` s."""
    n = int(dur * SR)
    pops = lfilter([1.0], [1.0, -0.6], (rng.uniform(0, 1, n) < 0.0025) * rng.uniform(0.3, 1, n) * rng.choice([-1, 1], n))
    edge = np.minimum(1, np.minimum(np.arange(n) / (0.03 * SR), (n - np.arange(n)) / (0.05 * SR)))
    x = 0.8 * _highpass(pops, 1500) + 0.12 * _highpass(_noise(n, rng), 3000)
    return (x * edge * level).astype(np.float32)


def boom(rng, level=1.0):
    """An explosion: a sub drop, a blast of noise, a long rumbling tail."""
    t = _t(3.0)
    sub = np.sin(2 * np.pi * np.cumsum(28 + 60 * np.exp(-t / 0.08)) / SR) * _env(len(t), 0.002, 0.9)
    blast = _lowpass(_noise(len(t), rng), 1200 + 6000 * np.exp(-t / 0.15)) * _env(len(t), 0.001, 0.6)
    return (np.tanh(1.5 * (0.9 * sub + 0.7 * blast)) * 0.85 * level).astype(np.float32)


def tick(rng, level=1.0, note=96):
    """A counter's tick: dry, high, short."""
    t = _t(0.03)
    x = np.sin(2 * np.pi * hz(note) * t) * _env(len(t), 0.0002, 0.004) \
        + 0.3 * _highpass(_noise(len(t), rng), 4000) * _env(len(t), 0.0002, 0.002)
    return (x * level).astype(np.float32)


def rewind(rng, level=1.0, dur=0.35):
    """Tape rewinding: chirps sweeping down, stuttering."""
    t = _t(dur)
    u = t / dur
    f = 2400 * (1 - 0.85 * u) * (1 + 0.3 * np.sin(2 * np.pi * 38 * t))
    x = _lowpass(_saw(f, t), 5000) * (0.5 + 0.5 * (np.sin(2 * np.pi * 24 * t) > 0))
    return (0.4 * x * np.clip(u / 0.05, 0, 1) * np.clip((1 - u) / 0.1, 0, 1) * level).astype(np.float32)


def swish(rng, level=1.0, dur=0.25):
    """A whip pan: a quick, bright band of noise rising and falling."""
    t = _t(dur)
    shape = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 4
    x = _highpass(_lowpass(_noise(len(t), rng), 1500 + 9000 * shape), 400) * shape
    return (0.8 * x * level).astype(np.float32)


def click(rng, level=1.0):
    """A mouse button."""
    t = _t(0.03)
    x = (_highpass(_noise(len(t), rng), 3000) * _env(len(t), 0.0002, 0.003)
         + 0.5 * np.sin(2 * np.pi * 2200 * t) * _env(len(t), 0.0002, 0.004))
    return (x * level).astype(np.float32)


def zap(rng, level=1.0):
    """A flash: a bright electric snap."""
    t = _t(0.15)
    x = 0.4 * _square(3000 * np.exp(-t / 0.03) + 400, t) * _env(len(t), 0.0005, 0.03) \
        + _highpass(_noise(len(t), rng), 5000) * _env(len(t), 0.0005, 0.02)
    return (0.6 * x * level).astype(np.float32)


def thud(rng, level=1.0):
    """Something soft and heavy set down: a lid closing, a lamp switched on."""
    t = _t(0.25)
    x = np.sin(2 * np.pi * np.cumsum(60 + 40 * np.exp(-t / 0.02)) / SR) * _env(len(t), 0.001, 0.05) \
        + 0.5 * _lowpass(_noise(len(t), rng), 800) * _env(len(t), 0.001, 0.03)
    return (x * level).astype(np.float32)


FOLEY = {"pop": pop, "boing": boing, "ding": ding, "whoosh": whoosh, "riser": riser, "hit": hit, "clack": clack,
         "slam": slam, "key": key, "glitch": glitch, "tear": tear, "stamp": stamp, "crackle": crackle, "boom": boom,
         "tick": tick, "rewind": rewind, "swish": swish, "click": click, "zap": zap, "thud": thud}


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
