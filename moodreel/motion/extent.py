"""How much of an element shows, frame by frame, and what that says about how it arrives or leaves.

The template tracker reads position, uniform scale and opacity. Flat design also grows bars from a baseline,
collapses words to a line, raises type out of a slot and sweeps shapes on with a mask: there the visible extent
changes along one axis, and a template of the whole element matches badly. This reader measures the visible extent
(the rows and columns that differ from the rest frame on the far side of the change, in one contiguous run seeded
by the element's own box) and compares its edges with where they rest:
  clip     the element shows beyond its rest edge, or keeps travelling once whole: a slot or mask hides its
           leading part, and the edge that moves is its own (type rising out of a slot)
  stretch  one edge (or the centre) holds at rest while the other travels and the whole element shows, squashed
           (also a solid shape, which can't tell a stretch from a wipe: the plain reading)
  wipe     one edge holds at rest and the part that shows is the element's own, in place (a roller, a mask)
A stretch or a wipe is read as the share shown (sy, sx, wipe: 0 to 1); a clip as the element's position, from the
edge that moves with it, and fitted like any move. A thin stroke drawn along its path, straight or curved, is read
as the share of its own path that shows (draw); a flat elongated shape's turn, from its silhouette's long axis.
"""
from __future__ import annotations

import cv2
import numpy as np

from ..video import Clip
from .track import DIFF_THR

FILL = 0.05          # share of a row (column) that must differ for it to count as part of the element
MARGIN = (0.6, 8)    # searched around the rest box: this share of the element's size plus px (a slot sits below)
ONE_AXIS = 0.3       # the shown share changes by at least this along one axis...
OTHER_AXIS = 0.12    # ...and by less than this along the other, once something shows
STILL = 1.5          # px (analysis): an edge this close to its rest place holds there
SHOWN, WHOLE = 0.15, 0.97
FLAT = 0.12          # a template this even (colour spread over its mean difference from the ground) is a solid shape
CLEAR = 0.05         # NCC margin a reading needs over the next to be told apart
TRUSTED = 0.75       # share of the partly shown frames where the template read the element well: the tracker's
TRUST_NCC = 0.85     # ...matched this well (a fading word does; a word half hidden in its slot doesn't)
UNIFORM = 0.06       # both sizes within this of each other, partly shown: a uniform scale
FULL_COLOUR = 0.7    # share of the changed pixels in the element's own colours, partly shown: less is a fade
LEADS = 0.5          # NCC of what shows of a clip reveal with the element's own leading part
ELONGATED = 1.5      # long over short axis of a silhouette whose turn can be read from its shape
STROKE = 5.0         # px (analysis): a stroke no wider than this, running at least eight times its width, is a line
OFF_PATH = 0.05      # share of what shows that may lie off the stroke's own path while it is drawn
LEVEL = 24           # colour quantisation for telling the element's own colours


def _rest(clip: Clip, a: int, b: int) -> np.ndarray:
    a, b = max(0, a), min(len(clip.frames) - 1, b)
    return np.median(clip.frames[a:b + 1].astype(np.float32), axis=0)


def _ncc(a: np.ndarray, b: np.ndarray) -> float | None:
    a, b = a.ravel() - a.mean(), b.ravel() - b.mean()
    d = float(np.sqrt((a * a).sum() * (b * b).sum()))
    return float((a * b).sum() / d) if d > 1e-6 else None


def _run(on: np.ndarray, lo: int, hi: int) -> tuple[int, int] | None:
    """The contiguous run of True overlapping [lo, hi), else the nearest one: a neighbour beyond a gap is not
    part of the element."""
    idx = np.nonzero(on)[0]
    if not len(idx):
        return None
    cut = np.nonzero(np.diff(idx) > 1)[0]
    runs = [(int(a), int(b) + 1) for a, b in zip(np.r_[idx[0], idx[cut + 1]], np.r_[idx[cut], idx[-1]])]
    gap = lambda r: max(0, r[0] - hi, lo - r[1])  # noqa: E731
    return min(runs, key=lambda r: (gap(r), -(r[1] - r[0])))


def _keys(img: np.ndarray) -> np.ndarray:
    q = np.clip(img // LEVEL, 0, 255 // LEVEL).astype(np.int32)
    n = 255 // LEVEL + 1
    return (q[..., 0] * n + q[..., 1]) * n + q[..., 2]


def _colours(img: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """The element's colours at rest, with their neighbouring levels (anti-aliasing, grain, codec)."""
    n = 255 // LEVEL + 1
    q = np.unique(np.clip(img[mask] // LEVEL, 0, n - 1).astype(np.int32), axis=0)
    near = np.array([(a, b, c) for a in (-1, 0, 1) for b in (-1, 0, 1) for c in (-1, 0, 1)])
    q = np.clip((q[:, None, :] + near[None]).reshape(-1, 3), 0, n - 1)
    return np.unique((q[:, 0] * n + q[:, 1]) * n + q[:, 2])


def extents(clip: Clip, track: dict) -> dict | None:
    """Visible extent per frame (top, bottom, left, right in window px, or None), in a window around the rest box."""
    if track["kind"] not in ("appear", "disappear"):
        return None
    p, q = track["p"], track["q"]
    P, Q = _rest(clip, p - 2, p), _rest(clip, q, q + 2)
    ref, rest_img = (P, Q) if track["kind"] == "appear" else (Q, P)
    x, y, w, h = (int(round(v / clip.scale)) for v in track["box"])
    if min(w, h) < 3:
        return None
    mx, my = int(MARGIN[0] * w) + MARGIN[1], int(MARGIN[0] * h) + MARGIN[1]
    X0, Y0, X1, Y1 = max(0, x - mx), max(0, y - my), min(clip.w, x + w + mx), min(clip.h, y + h + my)
    bx, by = (x - X0, x - X0 + w), (y - Y0, y - Y0 + h)          # the rest box in window px
    base = ref[Y0:Y1, X0:X1]
    at_rest = rest_img[Y0:Y1, X0:X1]
    box = np.zeros(base.shape[:2], bool)
    box[by[0]:by[1], bx[0]:bx[1]] = True
    mine = _colours(at_rest, box & (np.abs(at_rest - base).max(axis=2) > DIFF_THR))

    def edges(img):
        img = img[Y0:Y1, X0:X1].astype(np.float32)
        # what changed, in the element's own colours: another element changing beside it (a sea arriving under
        # a rising sun) touches it but is not it
        changed = np.abs(img - base).max(axis=2) > DIFF_THR
        fg = changed & np.isin(_keys(img), mine)
        rows = _run(fg[:, bx[0]:bx[1]].mean(axis=1) >= FILL, *by)     # within the element's own columns
        if rows is None:
            return None, 0.0
        cols = _run(fg[rows[0]:rows[1]].mean(axis=0) >= FILL, *bx)    # over the rows that show
        if not cols:
            return None, 0.0
        # how much of what changed there is in full colour: a clip, a stretch or a wipe shows the element's own
        # colours; a fade shows them mixed with the ground
        part = (slice(rows[0], rows[1]), slice(cols[0], cols[1]))
        return (*rows, *cols), float(fg[part].sum() / max(changed[part].sum(), 1))

    rest, _ = edges(rest_img)
    if rest is None:
        return None
    seen = {f: edges(clip.frames[f]) for f in range(p, q + 1)}
    return {"roi": (X0, Y0, X1, Y1), "rest": rest, "base": base, "T": rest_img[Y0:Y1, X0:X1] - base,
            "frames": {f: v[0] for f, v in seen.items()}, "colour": {f: v[1] for f, v in seen.items()}}


def _leads(clip, ext, f, axis, held_by) -> bool:
    """Is the part that shows the element's own leading part, at its own size? (A solid shape can't say: yes.)"""
    X0, Y0, X1, Y1 = ext["roi"]
    top, bot, left, right = ext["frames"][f]
    rt, rb, rl, rr = ext["rest"]
    T = ext["T"]
    V = clip.frames[f][Y0:Y1, X0:X1].astype(np.float32) - ext["base"]
    if axis == "y":
        n = bot - top
        V, lead = V[top:bot, rl:rr], (T[rt:rt + n, rl:rr] if held_by == "high" else T[rb - n:rb, rl:rr])
    else:
        n = right - left
        V, lead = V[rt:rb, left:right], (T[rt:rb, rl:rl + n] if held_by == "high" else T[rt:rb, rr - n:rr])
    px = T[rt:rb, rl:rr].reshape(-1, 3)
    if np.linalg.norm(px.std(axis=0)) < FLAT * max(float(np.linalg.norm(px.mean(axis=0))), 1e-3):
        return True
    s = _ncc(V, lead) if V.shape == lead.shape and min(V.shape[:2]) >= 2 else None
    return s is not None and s >= LEADS


def _axis(mask: np.ndarray) -> tuple[float, float] | None:
    """The silhouette's long axis (degrees, clockwise from the x axis, as CSS turns) and how elongated it is."""
    m = cv2.moments(mask.astype(np.uint8), binaryImage=True)
    if m["m00"] < 20:
        return None
    a, b, c = m["mu20"] / m["m00"], m["mu11"] / m["m00"], m["mu02"] / m["m00"]
    spread = np.sqrt(4 * b * b + (a - c) ** 2)
    long, short = (a + c + spread) / 2, (a + c - spread) / 2
    return float(np.degrees(0.5 * np.arctan2(2 * b, a - c))), float(np.sqrt(long / max(short, 1e-6)))


def turn(clip: Clip, track: dict) -> np.ndarray | None:
    """Per frame, how far an elongated element's silhouette is turned from its rest (degrees, clockwise), where it
    shows whole and as elongated as at rest; None when it isn't elongated enough to tell. For flat shapes, whose
    template can't tell a turn from a change of size. The silhouette is the element's own colours against the
    ground around it, so it is read the same whether the element arrives, leaves or turns in place."""
    p, q = track["p"], track["q"]
    rest_img = _rest(clip, p - 2, p) if track["kind"] == "disappear" else _rest(clip, q, q + 2)
    x, y, w, h = (int(round(v / clip.scale)) for v in track["box"])
    if min(w, h) < 8:
        return None
    mx, my = int(MARGIN[0] * w) + MARGIN[1], int(MARGIN[0] * h) + MARGIN[1]
    X0, Y0, X1, Y1 = max(0, x - mx), max(0, y - my), min(clip.w, x + w + mx), min(clip.h, y + h + my)
    at_rest = rest_img[Y0:Y1, X0:X1]
    rim = np.concatenate([at_rest[0], at_rest[-1], at_rest[:, 0], at_rest[:, -1]])
    ground = np.median(rim, axis=0)
    box = np.zeros(at_rest.shape[:2], bool)
    box[y - Y0:y - Y0 + h, x - X0:x - X0 + w] = True
    mine = _colours(at_rest, box & (np.abs(at_rest - ground).max(axis=2) > DIFF_THR))

    def silhouette(img):
        img = img[Y0:Y1, X0:X1].astype(np.float32)
        fg = (np.abs(img - ground).max(axis=2) > DIFF_THR) & np.isin(_keys(img), mine)
        n, lab, stats, _ = cv2.connectedComponentsWithStats(fg.astype(np.uint8), 8)
        if n < 2:
            return None
        k = 1 + int(np.argmax(stats[1:, 4]))
        bx, by, bw, bh, area = stats[k]
        inside = bx > 0 and by > 0 and bx + bw < X1 - X0 and by + bh < Y1 - Y0
        return (_axis(lab == k), area) if inside else None

    rest = silhouette(rest_img)
    if not rest or not rest[0] or rest[0][1] < ELONGATED:
        return None
    (a0, e0), area0 = rest
    out = []
    for f in range(p, q + 1):
        sil = silhouette(clip.frames[f])
        # a rigid turn keeps the silhouette whole, inside the window and as elongated as at rest
        if not sil or not sil[0] or sil[1] < 0.4 * area0 or abs(sil[0][1] / e0 - 1) > 0.15:
            out.append(np.nan)
            continue
        out.append((sil[0][0] - a0 + 90) % 180 - 90)
    return np.array(out)


def drawn(clip: Clip, track: dict) -> np.ndarray | None:
    """Per frame, the share of a thin stroke's own path that shows (0 to 1), for a line drawn on (or off) along
    any path; None when the element isn't a thin stroke, or what shows strays off its path (a stroke that moves,
    or grows thicker, is not being drawn)."""
    if track["kind"] not in ("appear", "disappear"):
        return None
    p, q = track["p"], track["q"]
    rest_img = _rest(clip, p - 2, p) if track["kind"] == "disappear" else _rest(clip, q, q + 2)
    x, y, w, h = (int(round(v / clip.scale)) for v in track["box"])
    m = 1                                                # tight: a line's neighbours (bars standing on it) stay out
    X0, Y0, X1, Y1 = max(0, x - m), max(0, y - m), min(clip.w, x + w + m), min(clip.h, y + h + m)
    at_rest = rest_img[Y0:Y1, X0:X1]
    rim = np.concatenate([at_rest[0], at_rest[-1], at_rest[:, 0], at_rest[:, -1]])
    ground = np.median(rim, axis=0)
    stroke = np.abs(at_rest - ground).max(axis=2) > DIFF_THR
    if stroke.sum() < 20:
        return None
    mine = _colours(at_rest, stroke)
    # thin: twice the median distance to the edge is a few pixels, and the stroke runs far longer than that
    dist = cv2.distanceTransform(np.pad(stroke, 1).astype(np.uint8), cv2.DIST_L2, 3)[1:-1, 1:-1]
    ridge = stroke & (dist >= cv2.dilate(dist, np.ones((3, 3), np.uint8)) - 1e-6)
    width = 2 * float(np.median(dist[ridge]))
    ys, xs = np.nonzero(stroke)
    if width > STROKE or max(np.ptp(ys), np.ptp(xs)) + 1 < 20 * width:
        return None                                      # a line runs far longer than it is wide; a label doesn't
    # one path (a rule, a curve, a joined hand), not a word's many glyphs
    n, _, stats, _ = cv2.connectedComponentsWithStats(stroke.astype(np.uint8), 8)
    if n < 2 or np.sort(stats[1:, 4])[::-1][:2].sum() < 0.9 * stroke.sum():
        return None
    path = cv2.dilate(stroke.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
    ys, xs = np.nonzero(stroke)
    full = float((np.ptp(ys) + 1) * (np.ptp(xs) + 1))
    out, spread = [], []
    for f in range(p, q + 1):
        img = clip.frames[f][Y0:Y1, X0:X1].astype(np.float32)
        changed = np.abs(img - ground).max(axis=2) > DIFF_THR
        fg = changed & np.isin(_keys(img), mine)
        on, off = (fg & path).sum(), (fg & ~path).sum()
        if off > OFF_PATH * max(on, 1) + 4:
            return None                                  # it shows somewhere its path doesn't run: it moved
        if (changed & path).sum() > 20 and on < FULL_COLOUR * (changed & path).sum():
            return None                                  # what shows is mixed with the ground: a fade
        share = min(1.0, on / stroke.sum())
        out.append(share)
        if 0.2 <= share <= 0.8:                          # how far over the stroke the part that shows spreads
            ys, xs = np.nonzero(fg & path)
            spread.append((np.ptp(ys) + 1) * (np.ptp(xs) + 1) / full - share)
    out = np.array(out)
    # drawn, the part that shows covers about its share of the stroke; faded in, all of it from the start
    if np.ptp(out) < ONE_AXIS or (spread and np.median(spread) > 0.35):
        return None
    # and it grows from nothing: its first glimpse (its last, drawn off) is a small part, not half at once
    seen = out[out > 0.02]
    if not len(seen) or (seen[-1] if track["kind"] == "disappear" else seen[0]) > 0.25:
        return None
    return out


def _content(clip, ext, f, axis) -> str:
    """With one edge held at rest: is the part that shows the whole element squashed, or its own part in place?"""
    X0, Y0, X1, Y1 = ext["roi"]
    top, bot, left, right = ext["frames"][f]
    rt, rb, rl, rr = ext["rest"]
    T = ext["T"]
    V = clip.frames[f][Y0:Y1, X0:X1].astype(np.float32) - ext["base"]
    if axis == "y":
        V, whole, place, size = V[top:bot, rl:rr], T[rt:rb, rl:rr], T[top:bot, rl:rr], (rr - rl, bot - top)
    else:
        V, whole, place, size = V[rt:rb, left:right], T[rt:rb, rl:rr], T[rt:rb, left:right], (right - left, rb - rt)
    px = whole.reshape(-1, 3)
    flat = np.linalg.norm(px.std(axis=0)) < FLAT * max(float(np.linalg.norm(px.mean(axis=0))), 1e-3)
    if min(V.shape[:2]) < 2 or flat:
        return "stretch"                                  # a solid shape: grown and wiped look alike
    shown = {"stretch": cv2.resize(whole, size, interpolation=cv2.INTER_AREA)}
    if place.shape == V.shape:
        shown["wipe"] = place
    scores = sorted(((s, m) for m, a in shown.items() if a.shape == V.shape for s in [_ncc(V, a)] if s is not None),
                    reverse=True)
    if not scores or (len(scores) > 1 and scores[0][0] - scores[1][0] < CLEAR):
        return "stretch"
    return scores[0][1]


def reading(clip: Clip, track: dict) -> dict | None:
    """The one-axis reading of an element that arrives or leaves, or None when the tracker's reading stands."""
    ext = extents(clip, track)
    if not ext:
        return None
    frames = sorted(ext["frames"])
    rt, rb, rl, rr = ext["rest"]
    e = np.array([ext["frames"][f] if ext["frames"][f] else (np.nan,) * 4 for f in frames], float)
    X0, Y0, X1, Y1 = ext["roi"]
    for axis, (i0, i1), (r0, r1), (o0, o1), limit, off in (("y", (0, 1), (rt, rb), (2, 3), Y1 - Y0, Y0),
                                                            ("x", (2, 3), (rl, rr), (0, 1), X1 - X0, X0)):
        size = r1 - r0
        main = np.nan_to_num((e[:, i1] - e[:, i0]) / size)
        other = np.nan_to_num((e[:, o1] - e[:, o0]) / ((rr - rl) if axis == "y" else (rb - rt)))
        shows, partial = main > SHOWN, (main > SHOWN) & (main < WHOLE)
        if np.ptp(main) < ONE_AXIS or not partial.any():
            continue
        # both sizes growing together is a scale, and colours mixed with the ground a fade: the template's to read
        if np.median(np.abs(other[partial] - main[partial])) < UNIFORM or \
                np.median([ext["colour"][f] for f, part in zip(frames, partial) if part]) < FULL_COLOUR:
            return None
        # a fade, a slide or a pop the template follows well also shows a growing extent (thresholds, the window):
        # that reading stands. This one is for what the template can't follow
        rd = track["readings"]
        good = [f for f, part, m, o in zip(frames, partial, main, other)
                if part and f in rd and rd[f]["ok"] and rd[f]["ncc"] >= TRUST_NCC and not rd[f].get("edge")
                and (abs(rd[f]["s"] - 1) <= 0.08 or (abs(rd[f]["s"] - m) <= 0.1 and abs(rd[f]["s"] - o) <= 0.1))]
        if len(good) >= TRUSTED * partial.sum():
            return None
        # across the axis, while partly shown (medians: one stray frame aside): a stretch keeps its size; a clip or
        # a wipe of a round shape may not (a disc rising behind a horizon widens), but it stays centred and never
        # outgrows its rest size
        mid = (e[partial, o0] + e[partial, o1]) / 2
        still = np.median(np.abs(other[partial] - 1)) <= OTHER_AXIS
        centred = np.median(np.abs(mid - np.median(mid))) <= STILL and float(np.percentile(other[partial], 90)) <= 1.05
        if not (still or centred):
            continue
        lo, hi = e[partial, i0], e[partial, i1]
        # how the partly shown element sits against its rest place: an edge held there, or beyond it (a slot)
        at = {"low": np.all(np.abs(lo - r0) <= STILL), "high": np.all(np.abs(hi - r1) <= STILL),
              "centre": np.all(np.abs((lo + hi) / 2 - (r0 + r1) / 2) <= STILL)}
        past_high = np.all(hi > r1 + STILL) and np.all(lo > r0 + STILL) and np.ptp(hi) <= STILL
        past_low = np.all(lo < r0 - STILL) and np.all(hi < r1 - STILL) and np.ptp(lo) <= STILL
        centre = np.where(shows, (e[:, i0] + e[:, i1]) / 2, np.nan)
        whole = shows & ~partial
        travels_on = whole.sum() >= 2 and np.nanmax(centre[whole]) - np.nanmin(centre[whole]) > 2 * STILL
        if centred and (past_high or past_low or ((at["low"] or at["high"]) and travels_on)):
            held_by = "high" if past_high or (at["high"] and not at["low"]) else "low"
            slot = hi.mean() if held_by == "high" else lo.mean()
            if slot <= 0.5 or slot >= limit - 0.5:
                continue                                  # held by the window or the frame: a plain slide
            f_mid = frames[int(np.nonzero(partial)[0][np.argmin(np.abs(main[partial] - 0.5))])]
            if not _leads(clip, ext, f_mid, axis, held_by):
                continue                                  # something else shows there (a turn, a morph)
            # the edge that moves is the element's own: its position follows from it and the rest size
            lead = e[:, i0] + size / 2 if held_by == "high" else e[:, i1] - size / 2
            return {"mode": "clip", "axis": axis, "anchor": {"y": {"high": "bottom", "low": "top"},
                                                              "x": {"high": "right", "low": "left"}}[axis][held_by],
                    "prop": axis, "series": np.where(shows, lead + off, np.nan) * clip.scale}
        anchor = next((k for k in ("high", "low", "centre") if at[k]), None)
        if anchor is None:
            continue                                      # both edges travel: a move, the tracker's to read
        f_mid = frames[int(np.nonzero(partial)[0][np.argmin(np.abs(main[partial] - 0.5))])]
        mode = _content(clip, ext, f_mid, axis)
        if (mode == "stretch" and not still) or (mode == "wipe" and not centred):
            continue
        names = {"y": {"high": "bottom", "low": "top", "centre": "centre"},
                 "x": {"high": "right", "low": "left", "centre": "centre"}}[axis]
        return {"mode": mode, "axis": axis, "anchor": names[anchor], "prop": "wipe" if mode == "wipe" else f"s{axis}",
                "series": main}
    return None
