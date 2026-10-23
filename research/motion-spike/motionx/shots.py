"""Whole-frame signals: hard cuts, dissolves, the localized motion-energy curve and its motion runs.

Energy follows motiscope's lesson: a whole-frame mean hides a small element moving, so the energy of a frame is
the mean of its most active cells. Thresholds are anchored to percentiles, never to the peak, so one cut or
fade cannot hide every element animation in the clip.
"""
from __future__ import annotations

import cv2
import numpy as np

from .video import Clip

TW, TH = 64, 36            # thumbnail used for every whole-frame signal
CELL = (6, 8)              # cell size in thumbnail px -> a 6 x 8 grid
TOP_FRACTION = 0.10
CUT_FRAC, CUT_HIST = 0.5, 0.3
GAP_S, MIN_RUN_FRAMES = 0.15, 2


def thumbs(clip: Clip) -> np.ndarray:
    return np.stack([cv2.resize(f, (TW, TH), interpolation=cv2.INTER_AREA) for f in clip.frames]).astype(np.float32)


def _hist(img):
    h = cv2.calcHist([img.astype(np.uint8)], [0, 1, 2], None, [8, 8, 8], [0, 256] * 3)
    return cv2.normalize(h, h).flatten()


def cuts(th: np.ndarray) -> list[int]:
    """Frame indices that start a new shot after a hard cut."""
    hs = [_hist(t) for t in th]
    out = []
    for i in range(1, len(th)):
        diff = np.abs(th[i] - th[i - 1]).max(axis=2)
        if (diff > 30).mean() > CUT_FRAC and cv2.compareHist(hs[i - 1], hs[i], cv2.HISTCMP_BHATTACHARYYA) > CUT_HIST:
            out.append(i)
    return out


def _alpha(th, a, b, idx):
    A, B = th[a].ravel(), th[b].ravel()
    d = B - A
    nn = float(d @ d) + 1e-9
    al, res = [], []
    for i in idx:
        x = th[i].ravel() - A
        k = float(x @ d) / nn
        al.append(k)
        res.append(float(np.linalg.norm(x - k * d)) / np.sqrt(nn))
    return np.array(al), np.array(res)


def dissolves(th: np.ndarray, hard: list[int], fps: float) -> list[dict]:
    """Runs where nearly the whole frame changes a little each frame and every frame is a blend of the two ends."""
    n = len(th)
    wide = np.zeros(n, bool)
    for i in range(1, n):
        diff = np.abs(th[i] - th[i - 1]).max(axis=2)
        wide[i] = (diff > 1.2).mean() > 0.6
    out, i = [], 1
    while i < n:
        if not wide[i]:
            i += 1
            continue
        j = i
        while j < n and wide[j]:
            j += 1
        a, b = i - 1, min(j, n - 1)
        if b - a >= 2 and not any(a < c <= b for c in hard):
            # grow the ends while the frames keep moving along the A->B direction
            for _ in range(int(fps)):
                al, _r = _alpha(th, a, b, [a - 1]) if a > 0 else (np.array([0.0]), None)
                if a > 0 and al[0] < -0.004:
                    a -= 1
                else:
                    break
            for _ in range(int(fps)):
                al, _r = _alpha(th, a, b, [b + 1]) if b < n - 1 else (np.array([1.0]), None)
                if b < n - 1 and al[0] > 1.004:
                    b += 1
                else:
                    break
            big = (np.abs(th[b] - th[a]).max(axis=2) > 12).mean()
            al, res = _alpha(th, a, b, range(a, b + 1))
            if big > 0.5 and res.max() < 0.2 and np.all(np.diff(al) > -0.05):
                out.append({"type": "dissolve", "a": a, "b": b, "t0": a / fps, "t1": b / fps,
                            "alpha": al.round(4).tolist()})
                j = max(j, b + 1)
        i = j
    return out


def energy(th: np.ndarray, ranges=None) -> np.ndarray:
    """ranges: [(start, end)] frame ranges (shots) whose cells share a noise floor; the whole clip by default."""
    g = th.mean(axis=3)
    ch, cw = CELL
    gh, gw = TH // ch, TW // cw
    k = max(1, int(round(TOP_FRACTION * gh * gw)))
    cells = np.zeros((len(g), gh * gw))
    for i in range(1, len(g)):
        cells[i] = np.abs(g[i] - g[i - 1])[: gh * ch, : gw * cw].reshape(gh, ch, gw, cw).mean(axis=(1, 3)).ravel()
    # Noise is removed twice. The median cell of a frame: grain and codec pumping (a keyframe refreshing the
    # picture) lift every cell together. Each cell's own floor (its median over the clip): a codec flickers
    # sharp text edges between frame types, which lifts only the cells that hold text, all the time
    e = np.zeros(len(g))
    for a, b in ranges or [(0, len(g))]:
        a = max(a, 1)
        floor = np.median(cells[a:b], axis=0) if b - a > 2 else np.zeros(gh * gw)
        for i in range(a, b):
            c = np.maximum(0.0, cells[i] - np.median(cells[i]) - 2 * floor)
            e[i] = np.sort(c)[-k:].mean()
    return e


def shots(clip: Clip) -> tuple[list[dict], list[dict], np.ndarray, np.ndarray]:
    th = thumbs(clip)
    hard = cuts(th)
    dis = dissolves(th, hard, clip.fps)
    bounds = sorted([(c, c, "cut") for c in hard] + [(d["a"] + 1, d["b"], "dissolve") for d in dis])
    out, start = [], 0
    for lo, hi, _kind in bounds:
        out.append({"start": start, "end": lo})          # frames [start, end)
        start = hi
    out.append({"start": start, "end": clip.n})
    out = [s for s in out if s["end"] - s["start"] >= 2]
    for k, s in enumerate(out):
        s["id"] = k
        s["t0"], s["t1"] = s["start"] / clip.fps, s["end"] / clip.fps
    transitions = [{"type": "cut", "frame": c, "t": c / clip.fps} for c in hard] + dis
    e = energy(th, [(s["start"], s["end"]) for s in out])
    return out, sorted(transitions, key=lambda x: x.get("t", x.get("t0"))), e, th


def motion_runs(e: np.ndarray, shot: dict, fps: float) -> tuple[list[tuple[int, int]], float]:
    """Frame runs [m0, m1) inside a shot whose frames changed from their predecessor."""
    s0, s1 = shot["start"], shot["end"]
    seg = e[s0 + 1: s1]
    if not len(seg):
        return [], 0.0
    thr = max(0.25, 2.5 * float(np.percentile(seg, 20)), 0.12 * float(np.percentile(seg, 75)))
    m = np.zeros(s1, bool)
    m[s0 + 1: s1] = seg > thr
    gap = int(round(GAP_S * fps))
    runs, i = [], s0
    while i < s1:
        if m[i]:
            j = i
            while j < s1 and m[j]:
                j += 1
            if runs and i - runs[-1][1] < gap:
                runs[-1] = (runs[-1][0], j)
            else:
                runs.append((i, j))
            i = j
        else:
            i += 1
    return [r for r in runs if r[1] - r[0] >= MIN_RUN_FRAMES], thr
