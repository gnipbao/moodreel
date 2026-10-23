"""A beat grid in silent motion: whether the references' moves land on a steady pulse, and its tempo.

Code-made films are often cut to a tempo that has no sound yet (a track laid under them later): elements start or
land on beats, shots change on downbeats. The marks are when moves start and land (each element's main prop) and the
cuts. Every tempo from MIN_BPM to MAX_BPM is tried, with the beat starting at the film's start or on a cut (a code-made
film counts its beats from zero and cuts on downbeats; trying every phase would cost the test twenty times over); a
grid holds when far more marks fall within TOL frames of its beats than chance would put there: the binomial chance
of so many, times the number of grids tried, must stay under ALPHA.
A grid faster than BEAT_MAX is reported as subdivisions of the beat half as fast (moves landing on eighths of 120 BPM).
"""
from __future__ import annotations

import numpy as np
from scipy.stats import binom

MIN_BPM, MAX_BPM = 60, 240
BEAT_MAX = 180       # BPM: a faster grid is a subdivision of a beat
MIN_MARKS = 8
ALPHA = 0.01         # chance of finding so good a grid in marks with no tempo at all, after every grid tried
SHARE = 0.35         # ...and the share of marks on it
TOL = 1.5            # frames: how near a beat a measured start or landing must be


def marks(events: list[dict], transitions: list[dict], fps: float) -> np.ndarray:
    """When moves start and land and shots cut, one mark per frame."""
    from .profile import main_prop
    t = [ev["props"][main_prop(ev)][k] for ev in events if ev.get("props") and main_prop(ev) for k in ("t0", "t1")]
    t += [tr["t"] for tr in transitions if tr["type"] == "cut"]
    t = np.sort(np.array(t, float))
    if not len(t):
        return t
    keep = np.r_[True, np.diff(t) > 1 / fps]
    return t[keep]


def grid(events: list[dict], transitions: list[dict], fps: float) -> dict | None:
    m = marks(events, transitions, fps)
    n = len(m)
    if n < MIN_MARKS:
        return None
    tol = TOL / fps
    cuts = [tr["t"] for tr in transitions if tr["type"] == "cut"]
    found, tried = [], 0
    for bpm in range(MIN_BPM, MAX_BPM + 1):
        T = 60.0 / bpm
        p = min(1.0, 2 * tol / T)
        if p >= 0.6:
            continue
        for phase in sorted({0.0} | {round(c % T, 4) for c in cuts}):
            tried += 1
            off = (m - phase) / T
            miss = np.abs(off - np.round(off)) * T
            on = miss <= tol
            hits = int(on.sum())
            chance = float(binom.sf(hits - 1, n, p))           # so many or more, with no tempo
            if hits >= SHARE * n:
                found.append((chance, float(miss[on].mean()), bpm, float(phase), hits, p))
    if not found:
        return None
    # grids about as unlikely as the best (a tempo a beat per minute off fits a short film too): the one whose beats
    # fall nearest the marks
    least = min(f[0] for f in found)
    chance, _, bpm, phase, hits, p = min((f for f in found if f[0] <= 10 * least), key=lambda f: f[1])
    if chance * tried > ALPHA:
        return None
    sub = 1
    while bpm / sub > BEAT_MAX:
        sub *= 2
    return {"bpm": round(bpm / sub, 1), "subdivision": sub, "period_s": round(60.0 / bpm, 4), "phase_s": round(phase, 3),
            "on_grid": hits, "marks": n, "share": round(hits / n, 2), "chance": round(p, 2),
            "p_value": float(f"{min(1.0, chance * tried):.2g}")}
