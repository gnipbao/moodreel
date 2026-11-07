"""Every cut in a film, to the frame: `find(path)` -> {fps, n, cuts, dissolves, dips, flashes}.

A cut is a frame the one before it cannot predict. Each frame is read small at the film's own rate (streamed, never the
whole film in memory at full size), the previous frame is warped onto it by its optical flow, and the two are compared
after normalising local contrast. Inside a shot that residual stays low whatever the shot does: a camera pan or push,
a character held on twos, light that brightens or dims. At a cut it jumps, and it has to jump against its
neighbourhood (animation on twos makes every other frame change a lot) and across most of the frame (a title popping
onto a plain ground changes one corner of it). A still picture that changes once and holds again is a cut too, however
little of it changes: a logo giving way to a wordmark on white (the old content gone, new content in its place), or an
empty grid ground turning into a plain one (a faint change spread over the whole frame). A change that comes back
within two frames is a flash, not a cut. Fades through a colour and dissolves come from `motion.shots` too, and no cut is
reported inside them.
"""
from __future__ import annotations

import subprocess

import cv2
import numpy as np

from ..motion import shots as S
from ..video import probe

W = 160                 # analysis width for the flow and the residual
RESID, RATIO, WHOLE, SIDES, CHANGE = 0.30, 3.0, 0.20, 2.2, 3.0
LIGHT_CHANGE, LIGHT_RATIO, LIGHT_COLOUR, LIGHT_STRUCT = 15.0, 2.5, 0.3, 0.75   # one set under other light, reframed
CALM = 0.2              # a step: the three frames either side change less than this share of the step itself
FLASH_BACK = 0.5        # a flash: the frame two on is this close to the one before, relative to the jump
NEIGHBOURS = 12
MIN_DISSOLVE = 0.25     # s


def _stream(path: str, fps: float, w: int = W):
    p = probe(path)
    h = int(round(p["h"] * w / p["w"] / 2) * 2)
    # frame 0 is the first frame decoded: a stream that starts late (an encoder's B-frame delay) is not padded at the front
    proc = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(path), "-vf", f"setpts=PTS-STARTPTS,fps={fps},scale={w}:{h}:flags=area",
                             "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    size = w * h * 3
    try:
        while True:
            b = proc.stdout.read(size)
            if len(b) < size:
                break
            yield np.frombuffer(b, np.uint8).reshape(h, w, 3)
    finally:
        proc.stdout.close()
        proc.wait()


def _norm(g: np.ndarray) -> np.ndarray:
    """Local contrast normalisation: brightness and contrast that change over the whole frame drop out."""
    g = g.astype(np.float32)
    m = cv2.GaussianBlur(g, (0, 0), 6)
    s = np.sqrt(cv2.GaussianBlur((g - m) ** 2, (0, 0), 6)) + 4
    return (g - m) / s


class _Predict:
    def __init__(self):
        self.dis = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_FAST)
        self.grid = None

    def residual(self, a: np.ndarray, b: np.ndarray) -> tuple[float, float]:
        """How badly frame a, warped by the flow, predicts frame b: mean normalised residual, and the share of the frame
        that it fails on."""
        if self.grid is None or self.grid[0].shape != b.shape:
            yy, xx = np.mgrid[0:b.shape[0], 0:b.shape[1]].astype(np.float32)
            self.grid = (xx, yy)
        flow = self.dis.calc(a, b, None)
        warped = cv2.remap(b, self.grid[0] + flow[..., 0], self.grid[1] + flow[..., 1], cv2.INTER_LINEAR)
        r = np.abs(_norm(a) - _norm(warped))
        r = cv2.blur(r, (5, 5))
        return float(r.mean()), float((r > 0.45).mean())


def _content(f: np.ndarray) -> np.ndarray:
    """What stands off the frame's commonest colour (its ground)."""
    q = (f // 16).reshape(-1, 3).astype(np.int32)
    keys = q[:, 0] * 256 + q[:, 1] * 16 + q[:, 2]
    ground = np.median(f.reshape(-1, 3)[keys == np.bincount(keys).argmax()], axis=0)
    return np.abs(f.astype(np.int16) - ground).max(axis=2) > 24


def signals(path: str) -> dict:
    """The per-frame signals for the step from frame i-1 to frame i (index 0 unused): residual, whole (the share of the
    frame the prediction fails on), change (mean |difference|), spread (the share of 8 x 8 blocks that changed at all),
    kept (the share of the old content still in place), new (the share of the new content that was not there) and
    structure (how well the edge maps of the two frames correlate) and colour (the colour histograms' distance);
    and the 64 x 36 thumbnails `motion.shots` reads."""
    fps = probe(path)["fps"]
    pred = _Predict()
    res, whole, change, spread, struct, colour = [0.0], [0.0], [0.0], [0.0], [1.0], [0.0]
    kept, new, content, th, gray = [1.0], [0.0], [], [], []
    prev = prevf = prevc = prevgm = prevh = None
    for f in _stream(path, fps):
        g = cv2.cvtColor(f, cv2.COLOR_RGB2GRAY)
        th.append(cv2.resize(f, (S.TW, S.TH), interpolation=cv2.INTER_AREA).astype(np.float32))
        gray.append(cv2.resize(g, (80, int(round(80 * g.shape[0] / g.shape[1]))), interpolation=cv2.INTER_AREA))
        c = _content(f)
        content.append(float(c.mean()))
        hist = cv2.calcHist([f], [0, 1, 2], None, [8, 8, 8], [0, 256] * 3)
        hist = cv2.normalize(hist, hist).flatten()
        gm = cv2.magnitude(cv2.Sobel(g, cv2.CV_32F, 1, 0), cv2.Sobel(g, cv2.CV_32F, 0, 1)).ravel()
        if prev is not None:
            r, w = pred.residual(prev, g)
            res.append(r)
            whole.append(w)
            d = np.abs(f.astype(np.int16) - prevf).max(axis=2)
            change.append(float(d.mean()))
            hb, wb = d.shape[0] // 8 * 8, d.shape[1] // 8 * 8
            spread.append(float((d[:hb, :wb].reshape(hb // 8, 8, wb // 8, 8).max(axis=(1, 3)) > 2).mean()))
            kept.append(float((prevc & c).sum() / prevc.sum()) if prevc.sum() else 1.0)
            new.append(float((c & ~prevc).sum() / c.sum()) if c.sum() else 0.0)
            sa, sb = prevgm.std(), gm.std()
            struct.append(float(np.corrcoef(prevgm, gm)[0, 1]) if sa > 1e-3 and sb > 1e-3 else (1.0 if sa <= 1e-3 and sb <= 1e-3 else 0.0))
            colour.append(float(cv2.compareHist(prevh, hist, cv2.HISTCMP_BHATTACHARYYA)))
        prev, prevf, prevc, prevgm, prevh = g, f.astype(np.int16), c, gm, hist
    thumbs = np.stack(th) if th else np.zeros((0, S.TH, S.TW, 3))
    return {"fps": fps, "residual": np.array(res), "whole": np.array(whole), "change": np.array(change), "spread": np.array(spread),
            "kept": np.array(kept), "new": np.array(new), "structure": np.array(struct), "colour": np.array(colour),
            "content": np.array(content), "thumbs": thumbs, "small": gray}


def _ratio(res: np.ndarray, i: int) -> float:
    lo, hi = max(1, i - NEIGHBOURS), min(len(res), i + NEIGHBOURS + 1)
    nb = np.r_[res[lo:max(lo, i - 1)], res[min(hi, i + 2):hi]]
    return float(res[i] / (np.median(nb) + 0.05)) if len(nb) else 0.0


def _step(sig: dict, i: int) -> bool:
    """A still picture that changes once and holds: calm on both sides, and either the old content swapped for new or a
    faint change spread over the whole frame."""
    ch = sig["change"]
    if ch[i] < 0.5 or i < 4 or i + 3 >= len(ch):
        return False
    before = ch[i - 3:i].max() < CALM * ch[i]
    after = ch[i + 1:i + 4].max() < CALM * ch[i]
    swap = sig["kept"][i] < 0.5 and sig["new"][i] > 0.5 and sig["content"][i - 1] > 0.003   # the new content may go on to move;
    # the old content has to be something: a dot that a title grows out of in one frame is an entrance
    faint = after and sig["spread"][i] > 0.5 and sig["structure"][i] < 0.5   # light that changes keeps the structure
    return bool(before and (swap or faint))


def _cut(sig: dict, i: int) -> bool:
    """The picture can't be predicted from the one before, against its neighbourhood (the residual is only trusted
    where the frame really changed: on a near-white frame normalising contrast blows up faint texture); or the
    picture's light and colour jump against both sides at once and its layout moves too (two shots of one set under
    other light; light that only changes keeps the edges where they were)."""
    res, ch = sig["residual"], sig["change"]
    if ch[i] >= CHANGE and res[i] >= RESID and sig["whole"][i] >= WHOLE and _ratio(res, i) >= RATIO and _sides(res, i) >= SIDES:
        return True
    if i < 4 or i + 3 >= len(ch):
        return False
    around = max(ch[i - 3:i].max(), ch[i + 1:i + 4].max())
    return bool(ch[i] >= LIGHT_CHANGE and ch[i] >= LIGHT_RATIO * around and sig["colour"][i] >= LIGHT_COLOUR
                and sig["structure"][i] < LIGHT_STRUCT)


def _sides(res: np.ndarray, i: int) -> float:
    """The jump against the steps two and three frames away on each side, the quieter side counting: animation on twos
    or threes changes as much on those steps as here, a cut stands out against at least one side."""
    if i < 3 or i + 3 >= len(res):
        return float(res[i] / 0.05)
    return float(res[i] / (min(res[i - 3:i - 1].max(), res[i + 2:i + 4].max()) + 0.05))


def _flash(small: list, i: int, pred: _Predict) -> int:
    """Frame i jumps away from frame i-1 and frame i+1 or i+2 comes back to it: how many frames on it came back (0: no
    flash)."""
    if i + 1 >= len(small):
        return 0
    jump, _ = pred.residual(small[i - 1], small[i])
    for k in (1, 2):
        if i + k < len(small):
            back, _ = pred.residual(small[i - 1], small[i + k])
            if back < FLASH_BACK * jump:
                return k
    return 0


def find(path: str) -> dict:
    sig = signals(str(path))
    fps, th, small = sig["fps"], sig["thumbs"], sig["small"]
    n = len(th)
    dips = S.dips(th, fps) if n > 2 else []
    spans = [(d["a"], d["b"]) for d in dips]
    pred = _Predict()
    cand, flashes = [], []
    back_from = set()
    for i in range(1, n):
        if i in back_from:
            continue                                   # the picture coming back from a flash
        if _cut(sig, i) or _step(sig, i):
            k = _flash(small, i, pred)
            if k:
                flashes.append(i)
                back_from.update(range(i + 1, i + k + 1))
            else:
                cand.append(i)
    cand = sorted(c for c in cand if not any(a - 1 <= c <= b + 1 for a, b in spans))
    # animation on twos can look like a two-frame blend: a dissolve lasts a quarter of a second at least
    dis = [d for d in (S.dissolves(th, cand, fps, spans) if n > 2 else []) if d["b"] - d["a"] >= max(4, round(MIN_DISSOLVE * fps))]
    cand = [c for c in cand if not any(d["a"] - 1 <= c <= d["b"] + 1 for d in dis)]
    return {"path": str(path), "fps": fps, "n": n, "cuts": cand,
            "dissolves": [[int(d["a"]), int(d["b"])] for d in dis],
            "dips": [[int(d["a"]), int(d["b"])] for d in dips],
            "flashes": flashes}
