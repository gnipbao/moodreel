"""The camera: how each frame of a shot maps onto its first frame, so elements are measured in the world.

Dense optical flow (DIS) gives a displacement on a grid over the textured ground; a similarity fitted by RANSAC
ignores the elements that move on their own. Each frame is first chained from its predecessor, then corrected
straight against the shot's first frame, so the chain's error never accumulates (a pure chain drifts). Dense flow
copes with faint and repetitive grounds (paper, grids) where feature matching finds too few distinct points. It
needs a ground with texture across the frame: on a flat ground only the elements carry signal, and an element's
own motion would be taken for the camera's, so the camera is reported as unknown rather than guessed.

When the camera moves, the shot's frames are warped back onto the first frame (stabilised). Pixels the moved
frame no longer covers are filled from the first frame, so the borders don't look like motion.

On a flat ground a camera move can still be read when the whole layout moves as one: `layout_pan` takes a motion
run in which one translation carries every element, frame to frame, and nothing stays in place (a page turn
across a spread). A single element moving alone is the element's own move, however large.

Camera model, matching the fixtures and a page's 2D transform about the frame centre C:
  screen = C + pan + (world - C) * zoom
"""
from __future__ import annotations

import cv2
import numpy as np

from ..video import Clip

MOVES = {"zoom": 0.02, "pan": 0.01}       # smallest range that counts as a move: zoom ratio, pan in frame widths
TEXTURED_CELLS = 0.6                      # share of a 8 x 6 grid that must hold ground texture
SCALE = 1.0                               # align at the analysis size: fine ground texture tells grid cells apart
STILL = 0.5                               # a locked camera leaves at least half the frame unchanged


def _gray(img):
    g = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY).astype(np.float32)
    return cv2.resize(g, None, fx=SCALE, fy=SCALE, interpolation=cv2.INTER_AREA)


def textured(gray: np.ndarray) -> float:
    """Share of grid cells whose gradient energy says the ground itself has texture."""
    gx, gy = cv2.Sobel(gray, cv2.CV_32F, 1, 0), cv2.Sobel(gray, cv2.CV_32F, 0, 1)
    mag = np.hypot(gx, gy)
    h, w = mag.shape
    cells = mag[: h // 6 * 6, : w // 8 * 8].reshape(6, h // 6, 8, w // 8).mean(axis=(1, 3))
    return float((cells > 4.0).mean())


def _to3(M):
    return np.vstack([M, [0, 0, 1]])


class _Flow:
    """Similarity between two grey frames from DIS optical flow on the textured part of the first."""

    def __init__(self, step=8):
        self.dis = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
        self.step = step

    def __call__(self, a, b, mask):
        flow = self.dis.calc(a.astype(np.uint8), b.astype(np.uint8), None)
        ys, xs = np.nonzero(mask[self.step // 2::self.step, self.step // 2::self.step])
        ys, xs = ys * self.step + self.step // 2, xs * self.step + self.step // 2
        if len(xs) < 30:
            return None, 0.0
        src = np.float32(np.stack([xs, ys], 1))
        dst = src + flow[ys, xs]
        M, inl = cv2.estimateAffinePartial2D(src, dst, method=cv2.RANSAC, ransacReprojThreshold=1.0)
        return (M, float(inl.mean())) if M is not None else (None, 0.0)


def estimate(clip: Clip, shot: dict) -> dict:
    """Per-frame zoom, rotation and pan (source px) of the shot's frames relative to its first frame."""
    ref = _gray(clip.frames[shot["start"]])
    share = textured(ref)
    if share < TEXTURED_CELLS:
        # a flat ground can't be registered; if most of the frame never changes, the camera holds still
        small = cv2.resize(ref, None, fx=0.25, fy=0.25, interpolation=cv2.INTER_AREA)
        changed = max(float((np.abs(cv2.resize(_gray(clip.frames[f]), small.shape[::-1], interpolation=cv2.INTER_AREA)
                                    - small) > 4).mean()) for f in range(shot["start"], shot["end"], 2))
        if changed < STILL:
            return {"status": "locked", "why": f"flat ground, at most {changed:.0%} of the frame changes"}
        return {"status": "unknown", "why": f"flat ground ({share:.0%} of the frame has texture)"}
    flow = _Flow()
    tex = lambda g: cv2.dilate((np.hypot(cv2.Sobel(g, cv2.CV_32F, 1, 0), cv2.Sobel(g, cv2.CV_32F, 0, 1)) > 8)  # noqa: E731
                               .astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
    ref_mask = tex(ref)
    C = np.array([clip.w / 2, clip.h / 2])
    out = {"t": [], "zoom": [], "rot": [], "panx": [], "pany": [], "M": [], "ok": []}
    M, prev, good = np.eye(2, 3), ref, 0
    for f in range(shot["start"], shot["end"]):
        cur = _gray(clip.frames[f])
        ok = True
        if f > shot["start"]:
            step, _ = flow(prev, cur, tex(prev))                 # predecessor -> this frame
            if step is not None:
                M = (_to3(step) @ _to3(M))[:2]
            Minv = cv2.invertAffineTransform(M)
            aligned = cv2.warpAffine(cur, Minv, cur.shape[::-1], flags=cv2.INTER_LINEAR)
            covered = cv2.erode(cv2.warpAffine(np.ones_like(cur, np.uint8), Minv, cur.shape[::-1],
                                               flags=cv2.INTER_NEAREST), np.ones((9, 9), np.uint8)) > 0
            fix, share = flow(ref, aligned, ref_mask & covered)  # what is left against the first frame
            # a correction is small by construction; a large one means the flow lost the ground, not the chain
            ok = (fix is not None and share >= 0.5 and abs(np.hypot(fix[0, 0], fix[1, 0]) - 1) < 0.01
                  and np.abs(fix[:, 2]).max() < 3)
            if ok:
                M = (_to3(M) @ _to3(fix))[:2]
            else:
                ok = step is not None                            # the chain alone still holds this frame
        prev = cur
        good += ok
        S = M.copy()
        S[:, 2] /= SCALE                                         # back to analysis pixels
        z = float(np.hypot(S[0, 0], S[1, 0]))
        pan = S[:, 2] - C * (1 - z)
        out["t"].append(f / clip.fps)
        out["zoom"].append(z)
        out["rot"].append(float(np.degrees(np.arctan2(S[1, 0], S[0, 0]))))
        out["panx"].append(float(pan[0]) * clip.scale)
        out["pany"].append(float(pan[1]) * clip.scale)
        out["M"].append(S)
        out["ok"].append(ok)
    n = shot["end"] - shot["start"]
    # a real camera move is one that stabilising explains: the ground lines up with the first frame far better
    # after the warp than before it. Elements moving fast over a faint ground can fool the flow; this can't be
    # fooled the same way
    raw, stab = [], []
    for k in range(0, n, max(1, n // 12)):
        cur = _gray(clip.frames[shot["start"] + k])
        Minv = cv2.invertAffineTransform(out["M"][k] * np.array([[1, 1, SCALE], [1, 1, SCALE]]))
        warped = cv2.warpAffine(cur, Minv, cur.shape[::-1], flags=cv2.INTER_LINEAR)
        covered = cv2.warpAffine(np.ones_like(cur, np.uint8), Minv, cur.shape[::-1], flags=cv2.INTER_NEAREST) > 0
        m = ref_mask & covered
        raw.append(float(np.median(np.abs(cur - ref)[ref_mask])))
        stab.append(float(np.median(np.abs(warped - ref)[m])) if m.any() else 255.0)
    out["check"] = {"raw": round(float(np.mean(raw)), 2), "stabilised": round(float(np.mean(stab)), 2)}
    if good < 0.8 * n:
        return {"status": "unknown", "why": f"aligned {good} of {n} frames"}
    z, px, py = (np.array(out[k]) for k in ("zoom", "panx", "pany"))
    moving = (np.ptp(z) > MOVES["zoom"] or np.ptp(px) > MOVES["pan"] * clip.src_w
              or np.ptp(py) > MOVES["pan"] * clip.src_w) and np.mean(stab) < 0.7 * np.mean(raw)
    return {"status": "moving" if moving else "locked", **out}


def stabilise(clip: Clip, shot: dict, cam: dict) -> None:
    """Warp the shot's frames back onto its first frame, in place."""
    ref = clip.frames[shot["start"]].copy()
    h, w = ref.shape[:2]
    ones = np.full((h, w), 255, np.uint8)
    for k, f in enumerate(range(shot["start"], shot["end"])):
        Minv = cv2.invertAffineTransform(cam["M"][k])
        warped = cv2.warpAffine(clip.frames[f], Minv, (w, h), flags=cv2.INTER_LINEAR)
        valid = cv2.erode(cv2.warpAffine(ones, Minv, (w, h), flags=cv2.INTER_NEAREST), np.ones((5, 5), np.uint8)) > 0
        clip.frames[f] = np.where(valid[..., None], warped, ref)


LAYOUT_SPREAD = 0.4      # the layout that pans together spans at least this share of the frame width...
LAYOUT_PARTS = 3         # ...in at least this many separate elements
EXPLAINED = 0.85         # share of the content a step's translation must carry


def layout_pan(clip: Clip, a: int, b: int) -> dict | None:
    """Frames a..b of a run on a flat ground: the cumulative pan (source px) when one translation carries the whole
    layout at every step, else None."""
    a, b = max(1, a - 1), min(len(clip.frames) - 1, b + 1)
    first = clip.frames[a - 1]
    q = (first // 16).reshape(-1, 3).astype(np.int32)
    keys = q[:, 0] * 256 + q[:, 1] * 16 + q[:, 2]
    ground = np.median(first.reshape(-1, 3)[keys == np.bincount(keys).argmax()], axis=0)
    content = lambda img: np.abs(img.astype(np.float32) - ground).max(axis=2) > 28  # noqa: E731
    c0 = content(first).astype(np.uint8)
    k = max(3, int(0.012 * clip.w) | 1)
    n, _, stats, _ = cv2.connectedComponentsWithStats(cv2.morphologyEx(c0, cv2.MORPH_CLOSE, np.ones((k, k), np.uint8)))
    parts = stats[1:][stats[1:, 4] >= 0.0004 * clip.w * clip.h]
    if len(parts) < LAYOUT_PARTS or (parts[:, 0] + parts[:, 2]).max() - parts[:, 0].min() < LAYOUT_SPREAD * clip.w:
        return None
    t, px, py = [(a - 1) / clip.fps], [0.0], [0.0]
    for f in range(a, b + 1):
        prev, cur = clip.frames[f - 1], clip.frames[f]
        (dx, dy), _ = cv2.phaseCorrelate(_gray(prev).astype(np.float64), _gray(cur).astype(np.float64))
        if np.hypot(dx, dy) >= 1.0:
            # the step must carry the content: shifted, the previous frame lands on this one where it had content
            shifted = cv2.warpAffine(prev, np.float32([[1, 0, dx], [0, 1, dy]]), prev.shape[1::-1],
                                     flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
            moved = cv2.warpAffine(content(prev).astype(np.uint8), np.float32([[1, 0, dx], [0, 1, dy]]),
                                   prev.shape[1::-1], flags=cv2.INTER_NEAREST) > 0
            if not moved.any():
                return None
            diff = np.abs(shifted.astype(np.float32) - cur).max(axis=2)[moved]
            still = np.abs(prev.astype(np.float32) - cur).max(axis=2)[content(prev)]
            # and it must carry it far better than standing still (large flat shapes overlap themselves)
            if float((diff < 28).mean()) < EXPLAINED or diff.mean() > 0.5 * still.mean():
                return None
        else:
            dx = dy = 0.0
        t.append(f / clip.fps)
        px.append(px[-1] + dx)
        py.append(py[-1] + dy)
    px, py = np.array(px) * clip.scale, np.array(py) * clip.scale
    if max(np.ptp(px), np.ptp(py)) < MOVES["pan"] * clip.src_w:
        return None
    return {"t": np.array(t), "panx": px, "pany": py}
