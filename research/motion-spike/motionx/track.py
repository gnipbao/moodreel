"""Find the elements a motion run changes, and track each one's position, scale and opacity through the run.

Rest-anchored tracking, made for motion graphics:
  1. A motion run sits between two rests: P (the frame before it) and Q (the settled frame after it).
  2. |Q - P| marks every region the run changed. Inside each region, the pixels that differ from the local
     background (the median of a ring around it) in Q are what is there after the run, in P what was there
     before. Q only: the element appeared. P only: it left. Both, overlapping: it changed in place (tracked on
     raw pixels). Both, apart: it moved, and the two halves are tracked separately, then joined (_dedupe).
  3. The element's look at its rest is the template: T = Q - P inside its mask (a signed difference, so the
     background cancels), padded with a ring of zeros so a smaller copy can't sit inside a flat shape.
  4. Walk away from the rest, frame by frame: match T over a scale range with normalised correlation on
     (frame - P), in a window around a constant-velocity prediction; the peak gives the centre, a parabola over
     neighbouring scales gives the scale, and the projection onto T gives the opacity.
"""
from __future__ import annotations

import cv2
import numpy as np

from .video import Clip

DIFF_THR = 28.0          # colour distance (0-255, max channel) that marks a changed or foreground pixel
MIN_AREA = 0.0012        # of the frame
GROUP_PX = 0.022         # closing kernel as a fraction of width: letters of one word join, cards 20 px apart don't
SCALES = np.exp(np.linspace(np.log(0.55), np.log(1.15), 21))
MIN_NCC, MIN_ALPHA = 0.55, 0.08


def _masks(P, Q, w):
    H, W = P.shape[:2]
    changed = (np.abs(Q - P).max(axis=2) > DIFF_THR).astype(np.uint8)
    changed = cv2.morphologyEx(changed, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
    k = max(3, int(GROUP_PX * w) | 1)
    ell = lambda n: cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (n, n))  # noqa: E731
    grouped = cv2.morphologyEx(changed, cv2.MORPH_CLOSE, ell(k))
    n, lab = cv2.connectedComponents(grouped, connectivity=8)
    area_min = MIN_AREA * H * W
    out = []
    for i in range(1, n):
        comp = (lab == i).astype(np.uint8)
        if comp.sum() < area_min:
            continue
        near = cv2.dilate(comp, ell(k)) > 0
        ring = (cv2.dilate(comp, ell(3 * k)) > 0) & ~near
        if not ring.any():
            continue
        p_fg = (np.abs(P - np.median(P[ring], axis=0)).max(axis=2) > DIFF_THR) & near
        q_fg = (np.abs(Q - np.median(Q[ring], axis=0)).max(axis=2) > DIFF_THR) & near
        ap, aq, inter = p_fg.sum(), q_fg.sum(), (p_fg & q_fg).sum()
        if aq and ap < 0.15 * aq:
            out.append(("appear", q_fg))
        elif ap and aq < 0.15 * ap:
            out.append(("disappear", p_fg))
        elif inter / max(1, (p_fg | q_fg).sum()) > 0.5:
            out.append(("change", q_fg))
        else:                                   # moved: follow where it arrived back to where it left, on raw pixels
            out += [("move", m) for m in _split(q_fg & ~p_fg, area_min)]
    return out


def _split(mask, area_min):
    n, lab = cv2.connectedComponents(cv2.morphologyEx(mask.astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8)))
    return [lab == i for i in range(1, n) if (lab == i).sum() >= area_min]


def _box(mask):
    ys, xs = np.nonzero(mask)
    return int(xs.min()), int(ys.min()), int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1)


def _template(src, bg, mask, box):
    x, y, bw, bh = box
    m = cv2.dilate(mask[y:y + bh, x:x + bw].astype(np.uint8), np.ones((3, 3), np.uint8))[..., None]
    if bg is None:                                     # in-place change: raw pixels, real surroundings as the ring
        ring = max(4, int(0.15 * max(bw, bh)))
        H, W = src.shape[:2]
        x0, y0, x1, y1 = max(0, x - ring), max(0, y - ring), min(W, x + bw + ring), min(H, y + bh + ring)
        return src[y0:y1, x0:x1].astype(np.float32), (x0, y0, x1 - x0, y1 - y0)
    T = (src[y:y + bh, x:x + bw] - bg[y:y + bh, x:x + bw]) * m
    ring = max(4, int(0.15 * max(bw, bh)))
    T = cv2.copyMakeBorder(T.astype(np.float32), ring, ring, ring, ring, cv2.BORDER_CONSTANT, value=0)
    return T, (x - ring, y - ring, bw + 2 * ring, bh + 2 * ring)


def _para(a, b, c):
    d = a - 2 * b + c
    return 0.0 if abs(d) < 1e-12 else float(np.clip(0.5 * (a - c) / d, -0.5, 0.5))


def _follow(clip: Clip, bg, T, tbox, frames):
    """Track the template through `frames` (ordered away from the rest frame). Returns per-frame readings."""
    x, y, bw, bh = tbox
    th, tw = T.shape[:2]
    pad = max(th, tw)
    raw = bg is None
    method = cv2.TM_CCOEFF_NORMED if raw else cv2.TM_CCORR_NORMED
    inside = cv2.copyMakeBorder(np.ones((clip.h, clip.w), np.float32), pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=0)
    pos, s, misses, out = [(x + bw / 2, y + bh / 2)], 1.0, 0, {}
    for f in frames:
        F = clip.frames[f].astype(np.float32)
        D = cv2.copyMakeBorder(F if raw else F - bg, pad, pad, pad, pad,
                               cv2.BORDER_REPLICATE if raw else cv2.BORDER_CONSTANT, value=0)
        vel = np.subtract(pos[-1], pos[-2]) if len(pos) > 1 else np.zeros(2)
        pcx, pcy = np.add(pos[-1], vel)
        reach = (0.06 * clip.w if len(pos) < 3 else 0.015 * clip.w) + 1.6 * float(np.hypot(*vel))
        per_scale = []
        for k in s * SCALES:
            sw, sh = int(round(tw * k)), int(round(th * k))
            if min(sw, sh) < 6 or k > 3:
                per_scale.append(None)
                continue
            Ts = cv2.resize(T, (sw, sh), interpolation=cv2.INTER_AREA)
            X0, Y0 = int(max(0, pcx + pad - reach - sw / 2)), int(max(0, pcy + pad - reach - sh / 2))
            X1 = int(min(D.shape[1], pcx + pad + reach + sw / 2 + 1))
            Y1 = int(min(D.shape[0], pcy + pad + reach + sh / 2 + 1))
            win = D[Y0:Y1, X0:X1]
            if win.shape[0] < sh or win.shape[1] < sw:
                per_scale.append(None)
                continue
            res = cv2.matchTemplate(win, Ts, method)
            _, mx, _, (lx, ly) = cv2.minMaxLoc(res)
            per_scale.append((float(mx), k, res, lx, ly, X0, Y0, Ts, sw, sh))
        scored = [(c[0], i) for i, c in enumerate(per_scale) if c is not None]
        if not scored:
            break
        _, i = max(scored)
        mx, k, res, lx, ly, X0, Y0, Ts, sw, sh = per_scale[i]
        if 0 < i < len(SCALES) - 1 and per_scale[i - 1] and per_scale[i + 1]:
            d = _para(per_scale[i - 1][0], mx, per_scale[i + 1][0])
            k = float(np.exp(np.log(k) + d * (np.log(SCALES[1]) - np.log(SCALES[0]))))
        px = lx + _para(res[ly, lx - 1], res[ly, lx], res[ly, lx + 1]) if 0 < lx < res.shape[1] - 1 else lx
        py = ly + _para(res[ly - 1, lx], res[ly, lx], res[ly + 1, lx]) if 0 < ly < res.shape[0] - 1 else ly
        patch = D[Y0 + ly: Y0 + ly + sh, X0 + lx: X0 + lx + sw]
        vis = inside[Y0 + ly: Y0 + ly + sh, X0 + lx: X0 + lx + sw][..., None]
        Tv = Ts * vis                                   # opacity from the part inside the frame only
        alpha = 1.0 if raw else float((patch * Tv).sum() / max((Tv * Tv).sum(), 1e-6))
        ncx, ncy = X0 + px + sw / 2 - pad, Y0 + py + sh / 2 - pad
        edge = bool(vis.min() < 1)
        ok = mx >= MIN_NCC and alpha >= MIN_ALPHA and (Tv * Tv).sum() > 0.15 * (Ts * Ts).sum()
        out[f] = {"cx": ncx, "cy": ncy, "s": float(k), "a": alpha, "ncc": float(mx), "ok": bool(ok), "edge": edge}
        if ok:
            pos.append((ncx, ncy))
            s, misses = float(k), 0
        else:
            misses += 1
            if misses >= 3:
                break
    return out


def track_run(clip: Clip, shot: dict, run: tuple[int, int], next_start: int | None,
              prev_end: int | None = None) -> list[dict]:
    """Rests are taken a little outside the run: energy misses the slow start of an ease-in and the long tail
    of an ease-out, and a fit needs to see the levels it starts from and settles on."""
    m0, m1 = run
    pre, settle = int(round(0.2 * clip.fps)), int(round(0.3 * clip.fps))
    p = max(shot["start"], prev_end if prev_end is not None else 0, m0 - 1 - pre)
    q = min(m1 - 1 + settle, (next_start - 1) if next_start else shot["end"] - 1, shot["end"] - 1)
    P, Q = clip.frames[p].astype(np.float32), clip.frames[q].astype(np.float32)
    tracks = []
    for kind, mask in _masks(P, Q, clip.w):
        box = _box(mask)
        if kind == "disappear":
            T, tbox = _template(P, Q, mask, box)
            readings = _follow(clip, Q, T, tbox, range(p, q + 1))
        elif kind in ("change", "move"):
            T, tbox = _template(Q, None, mask, box)
            readings = _follow(clip, None, T, tbox, range(q, p - 1, -1))
        else:
            T, tbox = _template(Q, P, mask, box)
            readings = _follow(clip, P, T, tbox, range(q, p - 1, -1))
        x, y, bw, bh = box
        tracks.append({"kind": kind, "shot": shot["id"], "run": [m0, m1], "p": p, "q": q,
                       "box": [x * clip.scale, y * clip.scale, bw * clip.scale, bh * clip.scale],
                       "tbox": [v * clip.scale for v in tbox], "readings": readings})
    return _dedupe(tracks)


def _dedupe(tracks):
    """An element that moves A->B shows up twice (it left A, it arrived at B); both tracks follow the same thing."""
    keep = []
    for t in sorted(tracks, key=lambda t: -sum(r["ok"] for r in t["readings"].values())):
        dup = False
        for k in keep:
            common = [f for f in t["readings"] if f in k["readings"] and t["readings"][f]["ok"] and k["readings"][f]["ok"]]
            if len(common) >= 3:
                d = np.median([np.hypot(t["readings"][f]["cx"] - k["readings"][f]["cx"],
                                        t["readings"][f]["cy"] - k["readings"][f]["cy"]) for f in common])
                if d < 6:
                    dup = True
                    if {k["kind"], t["kind"]} == {"appear", "disappear"}:
                        k["kind"] = "move"
                    break
        if not dup:
            keep.append(t)
    return keep


def series(clip: Clip, track: dict) -> dict:
    """Per-frame quantities in source px / seconds, with a reliability weight per reading.

    Opacity is 0 where an appearing element is not found yet (or a leaving one is gone); a position, scale or
    opacity read while the element is tiny, faint or cut by the frame edge gets a low weight."""
    rd = track["readings"]
    frames = list(range(track["p"], track["q"] + 1))
    t = np.array([f / clip.fps for f in frames])
    ok = np.array([f in rd and rd[f]["ok"] for f in frames])
    a = np.array([rd[f]["a"] if ok[i] else np.nan for i, f in enumerate(frames)])
    if track["kind"] in ("appear", "disappear"):
        a = np.where(np.isnan(a), 0.0, a)
    vis = ok & (a > 0.15)
    get = lambda k: np.array([rd[f][k] if vis[i] else np.nan for i, f in enumerate(frames)])  # noqa: E731
    s = get("s")
    edge = np.array([bool(rd[f].get("edge")) if ok[i] else False for i, f in enumerate(frames)])
    w = np.where(vis, np.clip(a, 0.05, 1) ** 2, 0.0)
    # trustworthy opacity: big enough, well matched, fully inside the frame, actually in between
    good_a = vis & (np.nan_to_num(s) >= 0.3) & ~edge & np.array([rd[f]["ncc"] >= 0.75 if ok[i] else False
                                                                  for i, f in enumerate(frames)])
    seen = [f for f in frames if f in rd and rd[f]["ok"]]
    far = (seen[-1] if track["kind"] == "disappear" else seen[0]) if seen else None
    side = None
    if far is not None and rd[far].get("edge"):
        r, bw, bh = rd[far], track["box"][2] / clip.scale * rd[far]["s"], track["box"][3] / clip.scale * rd[far]["s"]
        gaps = {"left": r["cx"] - bw / 2, "right": clip.w - (r["cx"] + bw / 2),
                "top": r["cy"] - bh / 2, "bottom": clip.h - (r["cy"] + bh / 2)}
        side = min(gaps, key=gaps.get)
    return {"t": t, "cx": get("cx") * clip.scale, "cy": get("cy") * clip.scale, "s": s, "a": np.clip(a, 0, 1.2),
            "w": w, "intermediate_a": int((good_a & (a > 0.15) & (a < 0.85)).sum()), "edge_side": side}
