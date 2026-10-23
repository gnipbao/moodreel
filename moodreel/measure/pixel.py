"""Pixel art: whether a reference is a low-resolution picture scaled up by whole pixels, and its palette and dither.

Scaled up by k with no smoothing, every edge of the picture falls on a multiple of k (plus one phase): along each
axis, the columns (rows) where the colour changes pile up at one phase of k, where a vector picture's edges fall
anywhere. The largest k that holds MOST of the changes on both axes is the scale; sampled at the centres of its
cells, the picture is its own native image, whose colours (merged within a codec's noise) are the palette, and whose
checkerboard pixels (unlike both neighbours, which agree, across and down) are ordered dither.
Read at the reference's own resolution: resizing first would smear the edges between cells.
"""
from __future__ import annotations

import numpy as np

CHANGE = 24          # grey levels between neighbours that count as an edge (codec ringing stays under it)
MIN_EDGES = 200 * 64 # change (steps over CHANGE, summed) along an axis needed to tell
MOST = 0.8           # share of the changes at one phase of k
MAX_SCALE = 16
NEAR = 14.0          # RGB distance within which two sampled colours are one palette entry (JPEG, H.264 noise)
MIN_SHARE = 0.0002   # a palette entry covers at least this much of the native image
DITHERS = 0.02       # share of checkerboard pixels for a picture to dither


def _changes(rgb: np.ndarray, axis: int) -> np.ndarray:
    """How much the picture changes at each position along `axis` (1: columns, 0: rows): the sum of the steps over
    CHANGE, so a cell's edge outweighs the codec's ringing beside it."""
    d = np.abs(np.diff(rgb.astype(np.int16), axis=axis)).max(axis=2)
    return np.where(d > CHANGE, d, 0).sum(axis=0 if axis == 1 else 1)


def _scale(counts: np.ndarray) -> tuple[int, int, float]:
    """The largest k (and its phase) that holds MOST of the changes; (1, 0, share) when none does."""
    total = counts.sum()
    best = (1, 0, 1.0)
    if total < MIN_EDGES:
        return 0, 0, 0.0
    pos = np.arange(len(counts)) + 1                      # a change between x-1 and x sits at x
    for k in range(2, MAX_SCALE + 1):
        shares = [counts[pos % k == ph].sum() / total for ph in range(k)]
        ph = int(np.argmax(shares))
        if shares[ph] >= MOST:
            best = (k, ph, float(shares[ph]))
    return best


def _palette(native: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """The native image's colours, merged within NEAR (most common first); and each pixel's entry."""
    flat = native.reshape(-1, 3).astype(np.float32)
    keys, inv, counts = np.unique((flat // 4).astype(np.int32), axis=0, return_inverse=True, return_counts=True)
    order = np.argsort(-counts)
    centres, of_key = [], np.empty(len(keys), int)
    for k in order:
        c = keys[k] * 4 + 2.0
        d = [np.linalg.norm(c - p) for p in centres]
        if d and min(d) <= NEAR:
            of_key[k] = int(np.argmin(d))
        else:
            of_key[k] = len(centres)
            centres.append(c)
    labels = of_key[inv.ravel()].reshape(native.shape[:2])
    return np.array(centres), labels


def read(rgb: np.ndarray) -> dict | None:
    kx, px, sx = _scale(_changes(rgb, 1))
    ky, py, sy = _scale(_changes(rgb, 0))
    if kx < 2 or ky < 2 or kx != ky:
        return None
    k = kx
    h, w = rgb.shape[:2]
    # the centre of each cell: cells start where the changes are (a change at x lies between x - 1 and x), k wide
    xs = np.arange(px % k + k // 2, w, k)
    ys = np.arange(py % k + k // 2, h, k)
    native = rgb[np.ix_(ys, xs)]
    centres, labels = _palette(native)
    share = np.bincount(labels.ravel(), minlength=len(centres)) / labels.size
    used = share >= MIN_SHARE
    c, l_, r, u, d = labels[1:-1, 1:-1], labels[1:-1, :-2], labels[1:-1, 2:], labels[:-2, 1:-1], labels[2:, 1:-1]
    checker = (l_ == r) & (u == d) & (l_ == u) & (c != l_)
    return {"scale": k, "native": [len(xs), len(ys)], "phase": [int(px), int(py)],
            "edges_on_grid": round(min(sx, sy), 2), "palette_size": int(used.sum()),
            "palette": ["#%02x%02x%02x" % tuple(int(v) for v in np.clip(p, 0, 255)) for p in centres[used][:32]],
            "dither_share": round(float(checker.mean()), 3), "dither": bool(checker.mean() >= DITHERS)}
