"""Whole-frame signals: hard cuts, dissolves, the localized motion-energy curve and its motion runs.

Energy follows motiscope's lesson: a whole-frame mean hides a small element moving, so the energy of a frame is
the mean of its most active cells. Thresholds are anchored to percentiles, never to the peak, so one cut or
fade cannot hide every element animation in the clip.
"""
from __future__ import annotations

import cv2
import numpy as np

from ..video import Clip

TW, TH = 64, 36            # thumbnail used for every whole-frame signal
CELL = (6, 8)              # cell size in thumbnail px -> a 6 x 8 grid
TOP_FRACTION = 0.10
CUT_FRAC, CUT_HIST = 0.5, 0.3
KEPT = 0.5                # share of the old content still in place above which a one-frame change is no cut
GAP_S, MIN_RUN_FRAMES = 0.15, 2


def thumbs(clip: Clip) -> np.ndarray:
    return np.stack([cv2.resize(f, (TW, TH), interpolation=cv2.INTER_AREA) for f in clip.frames]).astype(np.float32)


def _hist(img):
    h = cv2.calcHist([img.astype(np.uint8)], [0, 1, 2], None, [8, 8, 8], [0, 256] * 3)
    return cv2.normalize(h, h).flatten()


def _kept(before: np.ndarray, changed: np.ndarray) -> float:
    """Share of the content in `before` (what differs from its commonest colour, the ground) left unchanged."""
    q = (before // 16).reshape(-1, 3).astype(np.int32)
    keys = q[:, 0] * 256 + q[:, 1] * 16 + q[:, 2]
    ground = np.median(before.reshape(-1, 3)[keys == np.bincount(keys).argmax()], axis=0)
    content = np.abs(before - ground).max(axis=2) > 12
    return float((content & ~changed).sum() / content.sum()) if content.any() else 0.0


def cuts(th: np.ndarray, skip=()) -> list[int]:
    """Frame indices that start a new shot after a hard cut: a large change to most of the frame that its
    neighbours don't share (a fast fade changes as much per frame, but on every frame)."""
    hs = [_hist(t) for t in th]
    dm = np.array([0.0] + [float(np.abs(th[i] - th[i - 1]).mean()) for i in range(1, len(th))])
    out = []
    for i in range(1, len(th)):
        if any(a <= i <= b for a, b in skip):
            continue
        diff = np.abs(th[i] - th[i - 1]).max(axis=2)
        iso = dm[i] / (max(dm[i - 1] if i > 1 else 0.0, dm[i + 1] if i + 1 < len(th) else 0.0) + 0.05)
        hist = cv2.compareHist(hs[i - 1], hs[i], cv2.HISTCMP_BHATTACHARYYA)
        whole = (diff > 30).mean() > CUT_FRAC and hist > CUT_HIST and iso > 2.5
        # a content swap over a ground that stays: part of the frame takes new colours in one frame alone (a
        # drawing held on twos also changes in one frame, but only where a small element moved, in its own colours).
        # The old content has to go: when most of what stood on the ground is still there, a shape printed onto an
        # empty stretch of it in one frame is an entrance, not a new shot
        changed = diff > 12
        swap = changed.mean() > 0.06 and hist > 0.2 and iso > 8 and _kept(th[i - 1], changed) < KEPT
        if whole or swap:
            out.append(i)
    return out


def _global(th, k, frac=0.6):
    return (np.abs(th[k] - th[k - 1]).max(axis=2) > 1.0).mean() > frac


def dips(th: np.ndarray, fps: float) -> list[dict]:
    """A fade through one flat colour: the picture fades to (near) a single colour, the next shot fades in from it.
    Both sides must change the whole frame on every step, so an element arriving on a plain ground is not a dip."""
    n = len(th)
    flat = th.reshape(n, -1, 3).std(axis=1).max(axis=1) < 3.0
    out, i = [], 0
    while i < n:
        if not flat[i]:
            i += 1
            continue
        j = i + 1                                 # one flat colour: a fade through it changes the colour
        while j < n and flat[j] and np.abs(th[j].mean(axis=(0, 1)) - th[j - 1].mean(axis=(0, 1))).max() < 1.5:
            j += 1
        U = th[i:j].mean(axis=0)
        dist = lambda k: float(np.abs(th[k] - U).mean())  # noqa: E731
        a = i
        while a > 0 and dist(a - 1) > dist(a) + 0.5 and _global(th, a):
            a -= 1
        b = j - 1
        while b < n - 1 and dist(b + 1) > dist(b) + 0.5 and _global(th, b + 1):
            b += 1
        # a dip passes through a colour that is not a mix of its two ends; a dissolve between plain shots does
        # (mean distance, in levels, from the centre to the nearest mix of the two ends)
        d = th[b] - th[a]
        k = float(np.clip(((U - th[a]) * d).sum() / max(float((d * d).sum()), 1e-9), 0, 1))
        off = float(np.abs(U - th[a] - k * d).mean())
        if i - a >= 2 and b - (j - 1) >= 2 and off >= 8:
            if out and out[-1]["a"] <= b and a <= out[-1]["b"]:     # one dip per span: the most off-line centre
                if off <= out[-1]["off"]:
                    i = j
                    continue
                out.pop()
            rgb = U.reshape(-1, 3).mean(axis=0)
            out.append({"type": "dip", "a": a, "b": b, "t0": a / fps, "t1": b / fps, "off": round(off, 3),
                        "color": "#%02x%02x%02x" % tuple(int(round(c)) for c in rgb),
                        "fade_out": [1 - dist(k) / dist(a) for k in range(a, i + 1)],
                        "fade_in": [1 - dist(k) / dist(b) for k in range(j - 1, b + 1)]})
        i = j
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


def dissolves(th: np.ndarray, hard: list[int], fps: float, skip=()) -> list[dict]:
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
        if b - a >= 2 and not any(a < c <= b for c in hard) and not any(x <= b and a <= y for x, y in skip):
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


def energy(th: np.ndarray, ranges=None, lag: int = 1) -> np.ndarray:
    """ranges: [(start, end)] frame ranges (shots) whose cells share a noise floor; the whole clip by default.
    lag 2 compares the frames either side of each frame: a codec that alternates frame quality flickers with a
    period of two frames, and that flicker cancels out, while motion (also drawings held on twos) does not."""
    g = th.mean(axis=3)
    ch, cw = CELL
    gh, gw = TH // ch, TW // cw
    k = max(1, int(round(TOP_FRACTION * gh * gw)))
    cells = np.zeros((len(g), gh * gw))
    for i in range(1, len(g)):
        a, b = (i - 1, i) if lag == 1 or i + 1 >= len(g) else (i - 1, i + 1)
        cells[i] = np.abs(g[b] - g[a])[: gh * ch, : gw * cw].reshape(gh, ch, gw, cw).mean(axis=(1, 3)).ravel() / (b - a)
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
    dip = dips(th, clip.fps)
    spans = [(d["a"], d["b"]) for d in dip]
    hard = cuts(th, spans)
    dis = dissolves(th, hard, clip.fps, spans)
    bounds = sorted([(c, c, "cut") for c in hard] + [(d["a"] + 1, d["b"], d["type"]) for d in dis + dip])
    out, start = [], 0
    for lo, hi, _kind in bounds:
        out.append({"start": start, "end": lo})          # frames [start, end)
        start = hi
    out.append({"start": start, "end": clip.n})
    out = [s for s in out if s["end"] - s["start"] >= 2]
    for k, s in enumerate(out):
        s["id"] = k
        s["t0"], s["t1"] = s["start"] / clip.fps, s["end"] / clip.fps
    transitions = [{"type": "cut", "frame": c, "t": c / clip.fps} for c in hard] + dis + dip
    e = energy(th, [(s["start"], s["end"]) for s in out], lag=2)
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
            if j - i < MIN_RUN_FRAMES and e[i:j].max() < 2 * thr:
                i = j                                     # a blip of noise just over the line: no motion
                continue
            if runs and i - runs[-1][1] < gap:
                runs[-1] = (runs[-1][0], j)
            else:
                runs.append((i, j))
            i = j
        else:
            i += 1
    return [r for r in runs if r[1] - r[0] >= MIN_RUN_FRAMES], thr


def stepping(e: np.ndarray, runs: list[tuple[int, int]]) -> dict | None:
    """Drawings held for two or three frames (animation on twos or threes): inside the motion runs the picture
    changes only every n-th frame. `on` is the commonest gap between changed frames when it holds for most of them."""
    gaps = []
    for a, b in runs:
        seg = e[a:b]
        if len(seg) < 6:
            continue
        changed = np.nonzero(seg > 0.15 * np.percentile(seg, 90))[0]
        gaps += np.diff(changed).tolist()
    if len(gaps) < 6:
        return None
    vals, counts = np.unique(gaps, return_counts=True)
    share = float(counts.max() / len(gaps))
    on = int(vals[np.argmax(counts)])
    return {"on": on if share >= 0.6 else 1, "share": round(share, 2), "gaps": len(gaps)}
