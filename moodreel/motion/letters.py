"""Text that arrives (or leaves) one letter after another.

A word whose letters each fade, rise or drop on their own staggered clock is, to the template tracker, one shape that
keeps changing. This reader splits the word at rest into its glyphs, follows each in its own column band (letters
keep to their columns while they rise or drop), and reads per glyph how much of its ink shows against the ground
(its opacity, which doesn't depend on where in the band it is) and where that ink sits (its height). Each glyph's
change is fitted like any tween; when the onsets march across the word at a steady interval, the word is a
per-letter entrance: the first letter's tween stands for the word's, with the stagger's count, interval and order.
A word that arrives whole is left to the tracker.
"""
from __future__ import annotations

import cv2
import numpy as np

from ..video import Clip
from .fit import fit_move

INK = 12.0          # grey levels from the ground that count as ink (low: a letter half faded in still shows)
MIN_GLYPHS = 3      # fewer pieces (kerned letters can join) and there is no stagger to read
STEADY = 0.35       # spread (IQR over median) of the onset intervals of a stagger
DRIFT = 1.5         # px (analysis): how far a letter's ink may wander sideways in its own band while it shows
MIN_HEIGHT = 14     # px (analysis): letters smaller than this are read as a word


def _glyphs(mask: np.ndarray) -> list[tuple[int, int, int, int]]:
    """Glyph boxes (x0, x1, y0, y1) at rest, left to right: pieces sharing columns are one glyph (an i and its dot)."""
    n, _, stats, _ = cv2.connectedComponentsWithStats(mask.astype(np.uint8), 8)
    boxes = sorted([s[0], s[0] + s[2], s[1], s[1] + s[3]] for s in stats[1:].tolist() if s[4] >= 6)
    out = []
    for b in boxes:
        if out and b[0] < out[-1][1] - 1:                 # overlapping columns: the same glyph
            out[-1] = [out[-1][0], max(out[-1][1], b[1]), min(out[-1][2], b[2]), max(out[-1][3], b[3])]
        else:
            out.append(b)
    return [tuple(b) for b in out]


def reading(clip: Clip, track: dict, t: np.ndarray, prefer=None) -> dict | None:
    """Per-letter fits and the stagger, or None when the element isn't a line of letters arriving one by one."""
    if track["kind"] not in ("appear", "disappear"):
        return None
    p, q = track["p"], track["q"]
    # a word that slides or pops in whole matches its own template while it moves; letters arriving apart don't
    rd = track.get("readings") or {}
    moving = [r for r in rd.values() if 0.15 < r.get("a", 0) < 0.95 or (r.get("ok") and abs(r.get("s", 1) - 1) > 0.02)]
    if moving and sum(r["ok"] and r["ncc"] >= 0.85 for r in moving) >= 0.75 * len(moving):
        return None
    rest_f = p if track["kind"] == "disappear" else q
    x, y, w, h = (int(round(v / clip.scale)) for v in track["box"])
    if h < 8 or w < 3 * h:
        return None                                       # a line of letters is several times wider than tall
    reach = int(1.5 * h)                                  # a letter rising or dropping into place stays within this
    X0, X1, Y0, Y1 = max(0, x - 2), min(clip.w, x + w + 2), max(0, y - reach), min(clip.h, y + h + reach)
    rest = clip.frames[rest_f][Y0:Y1, X0:X1].astype(np.float32)
    rim = np.concatenate([rest[0], rest[-1], rest[:, 0], rest[:, -1]])
    ground = np.median(rim, axis=0)
    ink = lambda img: np.abs(img - ground).max(axis=2)  # noqa: E731
    at_rest = ink(rest)
    own = np.zeros(at_rest.shape, bool)                   # the element's own rows at rest
    own[y - Y0:y - Y0 + h] = True
    glyphs = _glyphs((at_rest > 2 * INK) & own)
    # what is inked at rest outside those rows belongs to other elements (a line below): kept out of the bands
    others = cv2.dilate(((at_rest > INK) & ~own).astype(np.uint8), np.ones((5, 5), np.uint8)) > 0
    heights = np.array([g[3] - g[2] for g in glyphs], float)
    if len(glyphs) < MIN_GLYPHS or heights.max() > 2.5 * np.median(heights) or np.median(heights) < MIN_HEIGHT:
        return None                                       # small type: its column bands are too narrow to tell
    frames = range(p, q + 1)
    stack = np.stack([ink(clip.frames[f][Y0:Y1, X0:X1].astype(np.float32)) for f in frames])
    stack = np.where((stack > INK) & ~others, stack, 0.0)

    per, drift = [], []
    for gx0, gx1, gy0, gy1 in glyphs:
        band = stack[:, :, gx0:gx1]                       # the glyph's own columns, the whole reach of rows
        full = float(np.where((at_rest[:, gx0:gx1] > INK) & own[:, gx0:gx1], at_rest[:, gx0:gx1], 0).sum())
        if full <= 0:
            return None
        amount = band.sum(axis=(1, 2)) / full
        # a letter keeps to its columns: where it mostly shows, its ink sits where it rests (a word sliding in pushes
        # its neighbours' ink through the band, and the bands filling one by one would look like a stagger)
        cols = np.arange(gx1 - gx0, dtype=float)
        xc = (band.sum(axis=1) * cols).sum(axis=1) / np.maximum(band.sum(axis=(1, 2)), 1e-6)
        mostly = (amount > 0.5) & (amount < 1.2)
        drift.append(float(np.ptp(xc[mostly])) if mostly.sum() >= 2 else 0.0)
        rows = np.arange(band.shape[1], dtype=float)
        weight = band.sum(axis=2)
        cy = np.where(amount > 0.2, (weight * rows).sum(axis=1) / np.maximum(weight.sum(axis=1), 1e-6), np.nan)
        a = fit_move(t, np.clip(amount, 0, 1.2), clip.fps, monotone=True, prefer=prefer)
        if not a or abs(a["delta"]) < 0.5:
            return None                                   # a letter that neither fades nor shows up: not this
        moved = cy[~np.isnan(cy)]
        yf = fit_move(t, (cy + Y0) * clip.scale, clip.fps, prefer=prefer) if len(moved) >= 5 and np.ptp(moved) > 2 else None
        per.append({"x": (gx0 + gx1) / 2, "opacity": a, "y": yf})
    if np.median(drift) > DRIFT:
        return None
    onsets = np.array([g["opacity"]["checkpoints"]["t50"] for g in per])
    steps = np.diff(onsets)
    med = float(np.median(steps))
    # one after another at a steady interval, half a frame apart at least; letters arriving together are a whole word
    spread = float(np.percentile(steps, 75) - np.percentile(steps, 25))
    if abs(med) < 0.5 / clip.fps or spread > STEADY * abs(med) + 0.5 / clip.fps:
        return None
    first = per[int(np.argmin(onsets))]
    return {"count": len(per), "interval": round(abs(med), 4),
            "order": "left-to-right" if med > 0 else "right-to-left",
            "opacity": first["opacity"], "y": first["y"], "glyphs": per}
