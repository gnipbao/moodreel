"""Ambient motion: loops that never settle and particles that drift through a shot.

A tween goes somewhere and stops; ambient motion keeps going. The tracker, which compares a run's frames before and
after, sees a loop as an element that keeps changing a little (a pulse, a bob, a spinner turning) and reports pieces
of it as moves; particles are too small and too many for it to see at all. This reader looks at whole shots.

Loops: on a coarse grid, a cell whose brightness repeats (its autocorrelation peaks again at some lag between
MIN_PERIOD and half the shot) belongs to a loop; neighbouring cells with one period are one looping element. Inside
its box the element's ink (against the box's rim, frame by frame) gives its centre, area, strength and long axis;
each is fitted with a sine at that period. A sine on the centre is a bob or a sway, on the area a pulse, on the
strength (opacity) a breathing fade; a long axis that keeps turning one way is a spin, with its rate.

Particles: against the shot's median frame (the particles move, so the median is the scene without them), small
round blobs, many per frame, matched frame to frame by their nearest neighbour; the field is their count, size,
speed range and direction.
"""
from __future__ import annotations

import cv2
import numpy as np

from ..video import Clip

CELL = 4             # analysis px per grid cell
MIN_PERIOD = 0.3     # s: faster is flicker, not a loop
REPEATS = 2.0        # a loop must be seen to repeat at least this many times in the shot
PERIODIC = 0.55      # autocorrelation at the period, for a cell to count as looping
VARIES = 6.0         # grey levels a looping cell's brightness swings by (its std), at least
SAME_PERIOD = 0.1    # cells within this share of each other's period are one loop
MIN_CELLS = 4
INK = 25.0           # grey levels from the ground that count as an element's ink
FITS = 0.6           # share of a property's variance a sine (or a steady turn) must explain
CLEAR = 0.9          # ...and when one property fits this well, weaker ones are side effects of it
MOVES = 1.5          # px (analysis): the least sway or bob worth reporting
SCALES = 0.03        # the least pulse (of scale)
BREATHES = 0.12      # the least swing of opacity (low / high below 1 - this)
SPINS = 10.0         # deg/s: the least steady turn
DOT_MAX = 60         # analysis px: a particle is a small blob...
DOT_ROUND = 0.55     # ...filling this much of its bounding box (a dot, not a stroke or a letter)
MIN_DOTS = 12        # blobs per frame for a field of particles
STEP_MAX = 12.0      # analysis px a particle may move between frames
TRACK = 6            # frames a particle is followed for, at least, to time its drift
AGREE = 60.0         # deg: particles share a drift (snow, dust, bubbles); specks going every way are grain


def _period(series: np.ndarray, fps: float) -> tuple[np.ndarray, np.ndarray]:
    """Per cell (columns of `series`, time down): the lag (frames) of the autocorrelation's first strong peak and its
    height."""
    n = len(series)
    x = series - series.mean(axis=0)
    spec = np.fft.rfft(x, 2 * n, axis=0)
    ac = np.fft.irfft(spec * np.conj(spec), axis=0)[:n]
    ac = ac / np.maximum(ac[0], 1e-9)
    ac = ac / (1 - np.arange(n) / n)[:, None]             # unbiased: long lags have fewer pairs
    lo, hi = max(2, int(MIN_PERIOD * fps)), int(n / REPEATS)
    if hi <= lo + 1:
        return np.zeros(x.shape[1], int), np.zeros(x.shape[1])
    seg = ac[lo:hi]
    peak = (seg[1:-1] > seg[:-2]) & (seg[1:-1] >= seg[2:])
    seg = np.where(np.vstack([np.zeros((1, seg.shape[1]), bool), peak, np.zeros((1, seg.shape[1]), bool)]), seg, -1)
    # the first peak that is nearly as high as the highest: a multiple of the period peaks as high
    top = seg.max(axis=0)
    first = np.argmax(seg >= 0.9 * top[None, :], axis=0)
    return lo + first, np.take_along_axis(seg, first[None, :], 0)[0]


def _sine(t, v, period):
    """Amplitude, mean and share of variance explained by v = c + a sin(2 pi t / period + phi)."""
    X = np.column_stack([np.sin(2 * np.pi * t / period), np.cos(2 * np.pi * t / period), np.ones_like(t)])
    coef, *_ = np.linalg.lstsq(X, v, rcond=None)
    resid = v - X @ coef
    var = float(np.var(v))
    return float(np.hypot(coef[0], coef[1])), float(coef[2]), (1 - float(np.var(resid)) / var) if var > 0 else 0.0


def _shape(clip: Clip, a: int, b: int, box) -> dict:
    """The element's ink inside `box` (analysis px) on frames a..b-1: centre, area, strength and long axis.
    Strength is read on the core (what is ink on nearly every frame): there it follows the opacity alone, where
    a pulse or a bob only moves the edges."""
    x0, y0, x1, y1 = box
    out = {k: [] for k in ("cx", "cy", "area", "strength", "axis")}
    diffs = []
    for f in range(a, b):
        img = clip.frames[f][y0:y1, x0:x1].astype(np.float32)
        rim = np.concatenate([img[0], img[-1], img[:, 0], img[:, -1]])
        diffs.append(np.abs(img - np.median(rim, axis=0)).max(axis=2))
    diffs = np.stack(diffs)
    core = (diffs > INK).mean(axis=0) >= 0.95
    for diff in diffs:
        ink = diff > INK
        n = ink.sum()
        if n < 4:
            for k in out:
                out[k].append(np.nan)
            continue
        ys, xs = np.nonzero(ink)
        cx, cy = xs.mean(), ys.mean()
        mu20, mu02, mu11 = ((xs - cx) ** 2).mean(), ((ys - cy) ** 2).mean(), ((xs - cx) * (ys - cy)).mean()
        elong = np.hypot(mu20 - mu02, 2 * mu11) / max(mu20 + mu02, 1e-9)
        out["cx"].append(x0 + cx)
        out["cy"].append(y0 + cy)
        out["area"].append(float(n))
        out["strength"].append(float(diff[core].mean()) if core.any() else np.nan)
        # the long axis, clockwise from horizontal as CSS turns (image y points down); none for a round shape
        out["axis"].append(np.degrees(0.5 * np.arctan2(2 * mu11, mu20 - mu02)) if elong > 0.3 else np.nan)
    return {k: np.array(v, float) for k, v in out.items()}


def _loop_props(t, S, period, scale) -> list[dict]:
    props = []
    ok = ~np.isnan(S["area"])
    if ok.sum() < 0.8 * len(t):
        return props
    t, S = t[ok], {k: v[ok] for k, v in S.items()}
    for k, prop in (("cx", "x"), ("cy", "y")):
        amp, mid, r2 = _sine(t, S[k], period)
        if r2 >= FITS and amp >= MOVES:
            props.append({"prop": prop, "amplitude": round(amp * scale, 1), "unit": "px", "fit": round(r2, 2)})
    amp, mid, r2 = _sine(t, np.sqrt(S["area"]), period)       # sqrt(area) goes with the scale
    if r2 >= FITS and amp / mid >= SCALES:
        props.append({"prop": "scale", "amplitude": round(amp / mid, 3), "unit": "share", "fit": round(r2, 2)})
    amp, mid, r2 = _sine(t, S["strength"], period) if not np.isnan(S["strength"]).any() else (0.0, 1.0, 0.0)
    if r2 >= FITS and (mid - amp) / (mid + amp) <= 1 - BREATHES:
        props.append({"prop": "opacity", "low": round((mid - amp) / (mid + amp), 2), "unit": "of its peak",
                      "fit": round(r2, 2)})
    if any(p["fit"] >= CLEAR for p in props):            # a fade's soft edge also swells the ink a little
        props = [p for p in props if p["fit"] >= CLEAR]
    return props


def _spin(t, S) -> dict | None:
    """A long axis turning steadily one way: the rate (deg/s, clockwise positive)."""
    ok = ~np.isnan(S["axis"])
    if ok.sum() < 0.8 * len(t):
        return None
    ang = np.degrees(np.unwrap(np.radians(2 * S["axis"][ok]))) / 2  # an axis repeats every 180 degrees
    tt = t[ok]
    rate, c = np.polyfit(tt, ang, 1)
    resid = ang - (rate * tt + c)
    if abs(rate) < SPINS or np.var(ang) <= 0 or 1 - np.var(resid) / np.var(ang) < 0.9:
        return None
    return {"prop": "rot", "rate": round(float(rate), 1), "unit": "deg/s"}


def loops(clip: Clip, shot: dict) -> list[dict]:
    a, b = shot["start"], shot["end"]
    n = b - a
    if n / clip.fps < REPEATS * MIN_PERIOD * 2:
        return []
    gh, gw = clip.h // CELL, clip.w // CELL
    grey = clip.frames[a:b, : gh * CELL, : gw * CELL].astype(np.float32).mean(axis=3)
    cells = grey.reshape(n, gh, CELL, gw, CELL).mean(axis=(2, 4)).reshape(n, -1)
    lag, height = _period(cells, clip.fps)
    live = (height >= PERIODIC) & (cells.std(axis=0) >= VARIES)
    regions = []                                          # (cells, period in frames, box in cells)
    taken = np.zeros(gh * gw, bool)
    for c in np.argsort(-height):
        if not live[c] or taken[c]:
            continue
        same = live & ~taken & (np.abs(lag - lag[c]) <= SAME_PERIOD * lag[c])
        mask = same.reshape(gh, gw).astype(np.uint8)
        _, lab = cv2.connectedComponents(cv2.dilate(mask, np.ones((3, 3), np.uint8)))
        region = (lab == lab.reshape(-1)[c]) & (mask > 0)
        taken |= region.ravel()
        if region.sum() < MIN_CELLS:
            continue
        ys, xs = np.nonzero(region)
        regions.append([region.ravel(), float(np.median(lag[region.ravel()])), [xs.min(), ys.min(), xs.max() + 1, ys.max() + 1]])
    # a flat shape loops only at its edges: edges with one period that one piece of ink joins are one element
    mid = clip.frames[a + n // 2].astype(np.float32)

    def joined(bi, bj, pad=2):
        x0, y0 = max(0, (min(bi[0], bj[0]) - pad) * CELL), max(0, (min(bi[1], bj[1]) - pad) * CELL)
        x1, y1 = min(clip.w, (max(bi[2], bj[2]) + pad) * CELL), min(clip.h, (max(bi[3], bj[3]) + pad) * CELL)
        img = mid[y0:y1, x0:x1]
        rim = np.concatenate([img[0], img[-1], img[:, 0], img[:, -1]])
        _, lab = cv2.connectedComponents((np.abs(img - np.median(rim, axis=0)).max(axis=2) > INK).astype(np.uint8))
        def part(b):                                      # the ink pieces in a region's (padded) box
            r0, r1 = max(0, (b[1] - pad) * CELL - y0), (b[3] + pad) * CELL - y0
            c0, c1 = max(0, (b[0] - pad) * CELL - x0), (b[2] + pad) * CELL - x0
            return set(np.unique(lab[r0:r1, c0:c1])) - {0}
        return bool(part(bi) & part(bj))
    merged = True
    while merged:
        merged = False
        for i in range(len(regions)):
            for j in range(i + 1, len(regions)):
                (ri, pi, bi), (rj, pj, bj) = regions[i], regions[j]
                reach = max(bi[3] - bi[1], bi[2] - bi[0], bj[3] - bj[1], bj[2] - bj[0])
                near = (bj[0] - bi[2] <= reach and bi[0] - bj[2] <= reach and bj[1] - bi[3] <= reach
                        and bi[1] - bj[3] <= reach)
                if near and abs(pi - pj) <= SAME_PERIOD * pi and joined(bi, bj):
                    regions[i] = [ri | rj, (pi * ri.sum() + pj * rj.sum()) / (ri.sum() + rj.sum()),
                                  [min(bi[0], bj[0]), min(bi[1], bj[1]), max(bi[2], bj[2]), max(bi[3], bj[3])]]
                    del regions[j]
                    merged = True
                    break
            if merged:
                break
    out = []
    for region, lag_f, (cx0, cy0, cx1, cy1) in regions:
        pad = 2
        box = (max(0, (cx0 - pad) * CELL), max(0, (cy0 - pad) * CELL), min(clip.w, (cx1 + pad) * CELL),
               min(clip.h, (cy1 + pad) * CELL))
        period = lag_f / clip.fps
        t = np.arange(a, b) / clip.fps
        S = _shape(clip, a, b, box)
        spin = _spin(t, S)
        props = [spin] if spin else _loop_props(t, S, period, clip.scale)
        if not props:
            continue
        s = clip.scale
        item = {"shot": shot["id"], "box": [round(box[0] * s, 1), round(box[1] * s, 1), round((box[2] - box[0]) * s, 1),
                                           round((box[3] - box[1]) * s, 1)], "props": props}
        if not spin:
            item["period_s"] = round(float(period), 3)
        out.append(item)
    return out


def particles(clip: Clip, shot: dict) -> dict | None:
    a, b = shot["start"], shot["end"]
    if b - a < 10:
        return None
    frames = clip.frames[a:b].astype(np.float32)
    ground = np.median(frames[:: max(1, (b - a) // 40)], axis=0)
    dots = []
    for img in frames:
        ink = (np.abs(img - ground).max(axis=2) > INK).astype(np.uint8)
        n, _, st, cen = cv2.connectedComponentsWithStats(ink, 8)
        keep = [(cen[i], st[i, 4]) for i in range(1, n) if 2 <= st[i, 4] <= DOT_MAX
                and st[i, 4] >= DOT_ROUND * st[i, 2] * st[i, 3] and max(st[i, 2], st[i, 3]) <= 2 * min(st[i, 2], st[i, 3]) + 1]
        dots.append(keep)
    counts = np.array([len(d) for d in dots])
    if np.median(counts) < MIN_DOTS:
        return None
    def pairs(d0, d1):
        """Mutual nearest neighbours, near enough: {index in d0: index in d1}."""
        if not d0 or not d1:
            return {}
        p0, p1 = np.array([c for c, _ in d0]), np.array([c for c, _ in d1])
        dist = np.linalg.norm(p0[:, None] - p1[None], axis=2)
        j, i = dist.argmin(axis=1), dist.argmin(axis=0)
        return {k: int(j[k]) for k in range(len(p0)) if i[j[k]] == k and dist[k, j[k]] <= STEP_MAX}
    links = [pairs(d0, d1) for d0, d1 in zip(dots[:-1], dots[1:])]
    # each dot followed while it keeps its step (a speck of grain matched by chance breaks it); its drift is the
    # whole way it went over the whole time, so a frame-rate change that skips a frame now and then evens out
    drifts, seen = [], set()
    for f0 in range(len(links)):
        for k in links[f0]:
            if (f0, k) in seen:
                continue
            path, f, cur = [dots[f0][k][0]], f0, k
            while f < len(links) and cur in links[f]:
                nxt = links[f][cur]
                step = dots[f + 1][nxt][0] - path[-1]
                mean = (path[-1] - path[0]) / max(len(path) - 1, 1)
                if len(path) > 2 and np.linalg.norm(step - mean) > max(2.5, 0.8 * np.linalg.norm(mean)):
                    break
                seen.add((f + 1, nxt))
                path.append(dots[f + 1][nxt][0])
                f, cur = f + 1, nxt
            if len(path) >= TRACK:
                drifts.append((path[-1] - path[0]) / (len(path) - 1))
    if len(drifts) < MIN_DOTS:
        return None
    v = np.array(drifts) * clip.fps * clip.scale               # source px per second
    speed = np.hypot(v[:, 0], v[:, 1])
    moving = speed > 0.02 * clip.src_h                         # a dot standing still is a speck, not a particle
    if moving.mean() < 0.6:
        return None
    v, speed = v[moving], speed[moving]
    ang = np.arctan2(v[:, 1], v[:, 0])
    R = np.hypot(np.cos(ang).mean(), np.sin(ang).mean())
    if np.degrees(np.sqrt(-2 * np.log(max(R, 1e-9)))) > AGREE:
        return None
    areas = [s for d in dots for _, s in d]
    return {"shot": shot["id"], "count": int(np.median(counts)),
            "radius_px": round(float(np.sqrt(np.median(areas) / np.pi)) * clip.scale, 1),
            "speed": {k: round(float(np.percentile(speed, q)), 1) for k, q in (("p10", 10), ("median", 50), ("p90", 90))},
            "vx": [round(float(np.percentile(v[:, 0], q)), 1) for q in (10, 90)],
            "vy": [round(float(np.percentile(v[:, 1], q)), 1) for q in (10, 90)],
            # the way they drift, as screen angles (0 = right, 90 = down), and how much they agree on it
            "direction_deg": round(float(np.degrees(np.arctan2(np.sin(ang).mean(), np.cos(ang).mean()))), 1),
            "spread_deg": round(float(np.degrees(np.sqrt(-2 * np.log(max(R, 1e-9))))), 1)}


def grammar(loops_: list[dict], fields: list[dict]) -> dict:
    """The style's ambient motion: how often things loop, at what periods and by how much; its particle fields."""
    def stats(xs):
        return {"n": len(xs), "median": round(float(np.median(xs)), 3), "min": round(float(min(xs)), 3),
                "max": round(float(max(xs)), 3)} if xs else None
    props = [p for L in loops_ for p in L["props"]]
    by = {}
    for p in props:
        by.setdefault(p["prop"], []).append(p.get("amplitude", p.get("low", p.get("rate"))))
    return {"loops": {"count": len(loops_), "period_s": stats([L["period_s"] for L in loops_ if "period_s" in L]),
                      "props": {k: stats(v) for k, v in by.items()}} if loops_ else None,
            "particles": fields or None}


def absorb(items: list[dict], tracks: list[dict]) -> list[dict]:
    """The tracks that aren't a loop's pieces (their centre inside its box)."""
    def inside(b, x, y):
        return b[0] <= x <= b[0] + b[2] and b[1] <= y <= b[1] + b[3]
    return [tr for tr in tracks if not any(inside(L["box"], tr["box"][0] + tr["box"][2] / 2, tr["box"][1] + tr["box"][3] / 2)
                                           for L in items)]
