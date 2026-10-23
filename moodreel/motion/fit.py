"""Fit one measured quantity as a single tween: v(t) = A + B * ease((t - t0) / (t1 - t0)).

Every candidate ease (eases.candidates) is fitted over a half-frame grid of t0 and t1; A and B are solved in
closed form (weighted least squares) for each (t0, t1), so the start level need not be visible: an element
fading in from 0 has no readable position at its start. A level that is known from outside the data can be
pinned instead (`start`, `end`: an element entering from off frame starts just outside it).
Families are ranked by BIC = n ln(RSS/n) + k ln n, with k = 4 + the ease's own parameters (3 with a pinned
level). As in REM, an ease is claimed only when it beats the best *other* family by EASE_GAP; otherwise the
result says `unknown` and still carries the nearest family and a fitted cubic-bezier for builders.
"""
from __future__ import annotations

import numpy as np
from scipy.optimize import least_squares

from . import eases

EASE_GAP = 10.0
MIN_SHAPED = 8           # readings in transition needed to name a family: fewer, and neighbours fit as well
EQUIVALENT = 0.03        # two families draw the same curve when their fits differ by at most this much of the travel


def _pairs(t0_lo, t0_hi, t1_hi, fps):
    step = 0.5 / fps
    t0s, t1s = [], []
    for a in np.arange(t0_lo, t0_hi + 1e-9, step):
        T1 = np.arange(a + 2 / fps, t1_hi + 1e-9, step)
        t0s.append(np.full(len(T1), a))
        t1s.append(T1)
    if not t0s:
        return np.array([]), np.array([])
    return np.concatenate(t0s), np.concatenate(t1s)


def _solve(E, v, w, start, end):
    """Best A, B and weighted RSS for every row of E. E: (pairs, n)."""
    sw = w.sum()
    if start is not None:
        x = v - start
        sxx, sex, see = (w * x * x).sum(), (E * (w * x)).sum(1), (E * E * w).sum(1)
        good = see > 1e-12
        B = np.where(good, sex / np.where(good, see, 1), 0)
        return np.full(len(E), start), B, np.where(good, sxx - sex ** 2 / np.where(good, see, 1), np.inf)
    if end is not None:
        G, x = E - 1, v - end
        sxx, sgx, sgg = (w * x * x).sum(), (G * (w * x)).sum(1), (G * G * w).sum(1)
        good = sgg > 1e-12
        B = np.where(good, sgx / np.where(good, sgg, 1), 0)
        return end - B, B, np.where(good, sxx - sgx ** 2 / np.where(good, sgg, 1), np.inf)
    Em = (E * w).sum(1, keepdims=True) / sw
    vm = (w * v).sum() / sw
    Ec, vc = E - Em, v - vm
    var, cov = (Ec * Ec * w).sum(1), Ec @ (w * vc)
    good = var > 1e-12
    B = np.where(good, cov / np.where(good, var, 1), 0)
    return vm - B * Em[:, 0], B, np.where(good, (w * vc * vc).sum() - cov ** 2 / np.where(good, var, 1), np.inf)


# When the data can't tell families apart, motion design practice can: entrances settle (ease-out), exits leave
# (ease-in), moves between two rests ease both ways. Among families that draw the same curve through the samples,
# the one whose class comes first for the element's role is reported.
PREFER = {
    "entrance": ["out", "out+overshoot", "inOut", "linear", "out+oscillate", "in"],
    "exit": ["in", "inOut", "linear", "out"],
    "move": ["inOut", "out", "in", "linear", "out+overshoot"],
}


def fit_move(t, v, fps, t0_range=None, t1_max=None, w=None, start=None, end=None, monotone=False,
             gap_needed=EASE_GAP, prefer: list[str] | None = None) -> dict | None:
    """monotone: skip eases that overshoot or oscillate (opacity can't go past fully opaque).
    gap_needed: the BIC margin to name the family; measured opacity bends under compression, so it asks more."""
    t, v = np.asarray(t, float), np.asarray(v, float)
    w = np.ones_like(v) if w is None else np.asarray(w, float)
    pinned_any = start is not None or end is not None
    ok = ~np.isnan(v) & (w > 0)
    t, v, w = t[ok], v[ok], w[ok]
    n = len(t)
    if n < 5 or np.ptp(v) <= 0:
        return None
    w = w * n / w.sum()                                    # weights sum to n, so BIC stays comparable
    lo, hi = t0_range if t0_range else (t[0] - 3 / fps, t[-1] - 2 / fps)
    t0s, t1s = _pairs(lo, hi, t1_max if t1_max is not None else t[-1] + 3 / fps, fps)
    if not len(t0s):
        return None
    U = np.clip((t[None, :] - t0s[:, None]) / (t1s - t0s)[:, None], 0, 1)
    pinned = start is not None or end is not None
    span = max(float(np.ptp(v)), abs((start if start is not None else end) - float(np.median(v))) if pinned else 0.0)
    fits = {}
    for name, extra in eases.candidates():
        if monotone and "+" in eases.shape_class(name):
            continue
        if pinned_any and eases.shape_class(name).endswith("oscillate"):
            continue                        # ringing from a start nobody saw is a guess on a guess
        A, B, rss = _solve(eases.get(name)(U), v, w, start, end)
        # a hidden start lets the travel exceed what was seen, but not by far: a fit that needs a huge jump
        # from an unseen place is explaining noise
        rss = np.where(np.abs(B) > 3 * span, np.inf, rss)
        j = int(np.argmin(rss))
        if not np.isfinite(rss[j]):
            continue
        k = (3 if pinned else 4) + extra
        fits[name] = {"bic": float(n * np.log(max(rss[j], 1e-12) / n) + k * np.log(n)),
                      "t0": float(t0s[j]), "t1": float(t1s[j]), "A": float(A[j]), "B": float(B[j]),
                      "pred": A[j] + B[j] * eases.get(name)(U[j])}
    if not fits:
        return None
    ranked = sorted(fits, key=lambda k: fits[k]["bic"])
    best = ranked[0]
    # families whose best fit draws (nearly) the same curve through these samples can't be told apart here,
    # whatever their BIC: they are named together, and the claim is measured against the nearest family that
    # draws a different curve
    scale_ = max(abs(fits[best]["B"]), 1e-9)
    same = {eases.family(r) for r in ranked[1:]
            if np.abs(fits[r]["pred"] - fits[best]["pred"]).max() / scale_ <= EQUIVALENT}
    same.discard(eases.family(best))
    other = next((r for r in ranked[1:] if eases.family(r) != eases.family(best) and eases.family(r) not in same), None)
    gap = fits[other]["bic"] - fits[best]["bic"] if other else float("inf")
    if prefer and same:
        rank = lambda r: prefer.index(eases.shape_class(r)) if eases.shape_class(r) in prefer else len(prefer)  # noqa: E731
        pool = [best] + [r for r in ranked[1:] if eases.family(r) in same]
        pick = min(pool, key=lambda r: (rank(r), fits[r]["bic"]))   # first by class, then by fit
        if rank(pick) < rank(best):
            same = (same | {eases.family(best)}) - {eases.family(pick)}
            best = pick
    f = fits[best]
    A, B, t0, t1 = f["A"], f["B"], f["t0"], f["t1"]
    cp = _checkpoints(best, t0, t1)
    # a curve can't be named from a handful of points, however clear the BIC: a 0.25 s fade at 25 fps has 5
    # readings in transition, and power1.out, sine.out and circ.out all pass through them. "In transition":
    # more than 2% from both levels, which counts a back.out's overshoot and an elastic's ringing
    Eb = eases.get(best)(np.clip((t - t0) / (t1 - t0), 0, 1))
    shaped = int(((t > t0) & (t < t1) & (Eb > 0.02) & (np.abs(Eb - 1) > 0.02)).sum())
    model = A + B * eases.get(best)(np.clip((t - t0) / (t1 - t0), 0, 1))
    after = t > cp["t50"]                                  # an elastic's overshoot comes long before mid-tween
    over = float(max(0.0, np.max((v[after] - (A + B)) * np.sign(B)) / abs(B))) if after.any() and B else 0.0
    # BIC counts every reading as independent evidence. Tracking errors come in runs (codec, frame-rate
    # conversion, a template slightly off), so the evidence is worth fewer readings: shrink the gap by the
    # effective sample size from the residuals' lag-1 autocorrelation
    r = (v - model) * np.sqrt(w)
    rho = float(np.clip(np.corrcoef(r[:-1], r[1:])[0, 1], 0, 0.95)) if len(r) > 3 and r.std() > 0 else 0.0
    gap_eff = gap * (1 - rho) / (1 + rho) if np.isfinite(gap) else gap
    claim = gap_eff >= gap_needed and shaped >= MIN_SHAPED and not pinned     # a pinned level is an assumption
    return {"ease": best if claim else "unknown", "best": best, "next": other, "equivalent": sorted(same),
            "shaped_samples": shaped,
            "bic_gap": round(gap, 1) if np.isfinite(gap) else None,
            "evidence": round(gap_eff, 1) if np.isfinite(gap_eff) else None, "rho": round(rho, 2),
            "t0": round(t0, 4), "t1": round(t1, 4), "dur": round(t1 - t0, 4),
            "from": round(A, 3), "to": round(A + B, 3), "delta": round(B, 3), "overshoot": round(over, 3),
            "pinned": "start" if start is not None else "end" if end is not None else None, "bic": round(f["bic"], 1),
            "resid": round(float(np.sqrt(np.average((v - model) ** 2, weights=w)) / max(abs(B), 1e-9)), 4), "n": n,
            "checkpoints": cp, "bezier": bezier_for(best)}


def _checkpoints(name, t0, t1):
    u = np.linspace(0, 1, 2001)
    y = eases.get(name)(u)
    out = {}
    for q in (0.1, 0.5, 0.9):
        idx = np.argmax(y >= q)
        out[f"t{int(q * 100)}"] = round(t0 + (t1 - t0) * float(u[idx]), 4)
    return out


def _bezier_y(params, x):
    x1, y1, x2, y2 = params
    s = x.copy()
    for _ in range(12):                                   # Newton on x(s) = x
        bx = 3 * (1 - s) ** 2 * s * x1 + 3 * (1 - s) * s ** 2 * x2 + s ** 3
        dx = 3 * (1 - s) ** 2 * x1 + 6 * (1 - s) * s * (x2 - x1) + 3 * s ** 2 * (1 - x2)
        s = np.clip(s - (bx - x) / np.where(np.abs(dx) < 1e-6, 1e-6, dx), 0, 1)
    return 3 * (1 - s) ** 2 * s * y1 + 3 * (1 - s) * s ** 2 * y2 + s ** 3


def bezier_for(name):
    """Nearest CSS cubic-bezier(x1, y1, x2, y2) to a named ease; None for oscillating eases."""
    if eases.shape_class(name).endswith("oscillate"):
        return None
    x = np.linspace(0, 1, 101)
    y = eases.get(name)(x)
    r = least_squares(lambda p: _bezier_y(p, x) - y, [0.33, 0.33, 0.67, 0.67],
                      bounds=([0, -2, 0, -2], [1, 3, 1, 3]))
    return [round(float(p), 3) for p in r.x]
