"""`moodreel compare <reference> <remake>`: how close a remake is to its reference, window by window.

A remake can match its reference frame by frame in stills and still feel wrong: too smooth, too slow, moving the other
way. So each window (a shot of the reference, by default) is measured on five counts and its grain, both videos at
the same small size:

  structure  SSIM of the luma, 0..1 (1: the same picture)
  detail     the remake's high-frequency energy over the reference's (1: as fine; under 0.8: softer, emptier)
  tone       mean luma difference, in levels of 255
  flow       optical-flow direction agreement, -1..1, cell by cell of a 4 x 4 grid where both move (1: the same way)
  speed      the remake's mean flow over the reference's (1: as fast)
  grain      the least median change between neighbouring frames of each, in levels: a reference at 0 holds its
             grain still, and a remake whose grain boils over it reads as motion going another way (freezing it took
             a still shot's flow agreement from 0.0 to 0.5)

and the worst windows are listed first, with what is wrong with each. The times are the reference's; --offset shifts the
remake's (remake time = reference time + offset).

Between passes: --against <last pass's --json> adds each window's change and the mean's, so a change is kept only where
its window rose; --sheet <file.jpg> puts the reference beside the remake at each window's middle, worst first, named
and scored, the picture to read before probing (the scores say where, the sheet says what).
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import numpy as np

W, H, FPS = 320, 180, 30
MOVING = 0.3          # px per frame at 320 x 180: a cell below this is still


def _frames(path, t0: float, t1: float, w=W, h=H, fps=FPS, gray=False) -> np.ndarray:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{max(0.0, t0):.3f}", "-i", str(path), "-t", f"{t1 - t0:.3f}",
                          "-vf", f"fps={fps},scale={w}:{h}:flags=area", "-pix_fmt", "gray" if gray else "bgr24",
                          "-f", "rawvideo", "-"], capture_output=True, check=True).stdout
    n = len(raw) // (w * h * (1 if gray else 3))
    return np.frombuffer(raw[:n * w * h * (1 if gray else 3)], np.uint8).reshape((n, h, w) if gray else (n, h, w, 3))


def duration(path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True, check=True).stdout
    return float(out.strip())


def cuts(path, threshold: float = 28.0, min_len: float = 1.0) -> list[float]:
    """The reference's cuts: frames whose mean luma change jumps past `threshold` levels, at least `min_len` apart."""
    f = _frames(path, 0, duration(path), 96, 54, 30, gray=True).astype(np.float32)
    d = np.abs(np.diff(f, axis=0)).mean(axis=(1, 2))
    out = []
    for i in np.flatnonzero(d > threshold):
        t = (i + 1) / 30
        if not out or t - out[-1] >= min_len:
            out.append(round(t, 3))
    return out


def windows(path, shots=None, every: float | None = None) -> list[tuple[float, float, str]]:
    """Shots given as [[t0, t1, name], ...], or fixed windows of `every` s, or the reference's own shots."""
    if shots:
        return [(float(a), float(b), str(n)) for a, b, n in shots]
    end = duration(path)
    marks = list(np.arange(every, end, every)) if every else cuts(path)
    edges = [0.0, *[float(m) for m in marks], end]
    return [(round(a, 3), round(b, 3), f"{a:.1f}") for a, b in zip(edges, edges[1:]) if b - a >= 0.2]


def _ssim(a, b):
    import cv2
    a, b = a.astype(np.float64), b.astype(np.float64)
    blur = lambda x: cv2.GaussianBlur(x, (7, 7), 1.5)  # noqa: E731
    ma, mb = blur(a), blur(b)
    va, vb, cov = blur(a * a) - ma ** 2, blur(b * b) - mb ** 2, blur(a * b) - ma * mb
    c1, c2 = (0.01 * 255) ** 2, (0.03 * 255) ** 2
    return float((((2 * ma * mb + c1) * (2 * cov + c2)) / ((ma ** 2 + mb ** 2 + c1) * (va + vb + c2))).mean())


def _detail(g):
    import cv2
    return float(np.abs(cv2.Laplacian(g.astype(np.float32), cv2.CV_32F, ksize=3)).mean())


def _cells(flow, n=4):
    h, w = flow.shape[:2]
    return np.array([flow[j * h // n:(j + 1) * h // n, i * w // n:(i + 1) * w // n].reshape(-1, 2).mean(axis=0)
                     for j in range(n) for i in range(n)])


def window(ref, ours, t0: float, t1: float, offset: float = 0.0) -> dict:
    import cv2
    R, Q = _frames(ref, t0, t1), _frames(ours, t0 + offset, t1 + offset)
    n = min(len(R), len(Q))
    if n < 3:
        return {"t0": t0, "t1": t1, "frames": n}
    gR = [cv2.cvtColor(x, cv2.COLOR_BGR2GRAY) for x in R[:n]]
    gO = [cv2.cvtColor(x, cv2.COLOR_BGR2GRAY) for x in Q[:n]]
    idx = range(0, n, 3)
    dR, dO = np.mean([_detail(gR[i]) for i in idx]), np.mean([_detail(gO[i]) for i in idx])
    agree, sR, sO = [], [], []
    for i in range(0, n - 1, 2):
        fR = _cells(cv2.calcOpticalFlowFarneback(gR[i], gR[i + 1], None, 0.5, 3, 15, 3, 5, 1.2, 0))
        fO = _cells(cv2.calcOpticalFlowFarneback(gO[i], gO[i + 1], None, 0.5, 3, 15, 3, 5, 1.2, 0))
        mR, mO = np.linalg.norm(fR, axis=1), np.linalg.norm(fO, axis=1)
        sR.append(mR.mean()), sO.append(mO.mean())
        both = (mR > MOVING) & (mO > MOVING)
        if both.any():
            agree.append(float(((fR[both] * fO[both]).sum(1) / (mR[both] * mO[both])).mean()))
        elif (mR > MOVING).any() or (mO > MOVING).any():
            agree.append(0.0)                                  # one moves, the other doesn't
    still = max(np.mean(sR), np.mean(sO)) < MOVING / 3 if sR else True
    grain = [round(float(np.min([np.median(np.abs(g[i + 1].astype(np.float32) - g[i])) for i in range(n - 1)])), 2)
             for g in (gR, gO)]                                 # the least change between neighbours: grain, not codec
    return {"t0": t0, "t1": t1, "frames": n, "grain": grain,
            "structure": round(float(np.mean([_ssim(gR[i], gO[i]) for i in idx])), 3),
            "detail": round(float(dO / max(dR, 1e-6)), 2),
            "tone": round(float(np.mean([abs(float(gR[i].mean()) - float(gO[i].mean())) for i in idx])), 1),
            "flow": None if still or not agree else round(float(np.mean(agree)), 2),
            "speed": None if still else round(float(np.mean(sO) / max(np.mean(sR), 1e-6)), 2)}


def problems(r: dict) -> list[str]:
    out = []
    if r.get("structure", 1) < 0.5:
        out.append("a different picture")
    if r.get("detail", 1) < 0.8:
        out.append("softer, less detail")
    if r.get("detail", 1) > 1.4:
        out.append("busier than the reference")
    if r.get("tone", 0) > 12:
        out.append("brighter or darker")
    if r.get("flow") is not None and r["flow"] < 0.5:
        out.append("moving another way" if r["flow"] < 0.2 else "motion partly off")
    if r.get("speed") is not None and not 0.7 <= r["speed"] <= 1.4:
        out.append("too slow" if r["speed"] < 0.7 else "too fast")
    if r.get("grain") and r["grain"][0] < 0.1 and r["grain"][1] > 0.3:
        out.append("grain boils where the reference's holds still")
    return out


def score(r: dict) -> float:
    """0..1, higher is closer: structure, detail and speed near 1, flow agreeing."""
    parts = [r.get("structure", 0)]
    if "detail" in r:
        parts.append(max(0.0, 1 - abs(np.log(max(r["detail"], 1e-3)))))
    if r.get("flow") is not None:
        parts.append((r["flow"] + 1) / 2)
    if r.get("speed") is not None:
        parts.append(max(0.0, 1 - abs(np.log(max(r["speed"], 1e-3)))))
    return round(float(np.mean(parts)), 3)


def _window(args):
    ref, ours, t0, t1, offset = args
    return window(ref, ours, t0, t1, offset)


def compare(ref, ours, shots=None, every=None, offset=0.0, workers: int = 8) -> dict:
    """Every window measured at once, a process each (36 windows of a 64 s film: 90 s one by one, about 15 s)."""
    wins = windows(ref, shots, every)
    jobs = [(str(ref), str(ours), t0, t1, offset) for t0, t1, _ in wins]
    if workers > 1 and len(jobs) > 1:
        from concurrent.futures import ProcessPoolExecutor
        with ProcessPoolExecutor(min(workers, len(jobs))) as ex:
            measured = list(ex.map(_window, jobs))
    else:
        measured = [_window(j) for j in jobs]
    rows = []
    for (t0, t1, name), m in zip(wins, measured):
        r = {"window": name, **m}
        r["score"], r["problems"] = score(r), problems(r)
        rows.append(r)
    med = lambda k: round(float(np.median([r[k] for r in rows if r.get(k) is not None])), 2) if rows else None  # noqa: E731
    return {"reference": str(ref), "remake": str(ours), "offset": offset, "windows": rows,
            "median": {k: med(k) for k in ("structure", "detail", "tone", "flow", "speed", "score")},
            "worst": [r["window"] for r in sorted(rows, key=lambda r: r["score"])[:5]]}


def against(res: dict, prev: dict) -> dict:
    """Each window's score change from a previous pass (matched by name and times), and the mean's."""
    before = {(r["window"], r["t0"], r["t1"]): r["score"] for r in prev.get("windows", [])}
    for r in res["windows"]:
        b = before.get((r["window"], r["t0"], r["t1"]))
        r["change"] = None if b is None else round(r["score"] - b, 3)
    mean = lambda rows: round(float(np.mean([r["score"] for r in rows])), 3) if rows else None  # noqa: E731
    res["mean"] = {"before": mean(prev.get("windows", [])), "now": mean(res["windows"])}
    return res


def report(res: dict) -> str:
    w = max([8, *(len(r["window"]) for r in res["windows"])])
    vs = any("change" in r for r in res["windows"])
    lines = [f'{"window":>{w}} {"t0":>7} {"t1":>7} {"struct":>6} {"detail":>6} {"tone":>5} {"flow":>5} {"speed":>5} {"score":>5}'
             + (f' {"change":>6}' if vs else "") + '  problems']
    fmt = lambda v: "-" if v is None else v  # noqa: E731
    for r in res["windows"]:
        ch = r.get("change")
        lines.append(f'{r["window"]:>{w}} {r["t0"]:7.2f} {r["t1"]:7.2f} {fmt(r.get("structure")):>6} {fmt(r.get("detail")):>6} '
                     f'{fmt(r.get("tone")):>5} {fmt(r.get("flow")):>5} {fmt(r.get("speed")):>5} {r["score"]:>5}'
                     + (f' {"-" if ch is None else f"{ch:+.3f}":>6}' if vs else "") + '  ' + ", ".join(r["problems"]))
    m = res["median"]
    lines.append(f"median: structure {m['structure']}, detail {m['detail']}, tone {m['tone']}, flow {m['flow']}, "
                 f"speed {m['speed']}, score {m['score']}")
    if res.get("mean"):
        lines.append(f"mean score: {res['mean']['before']} -> {res['mean']['now']}")
    lines.append("worst first: " + ", ".join(res["worst"]))
    return "\n".join(lines)


def sheet(res: dict, out, offset: float = 0.0, cols: int = 2, size=(480, 270)) -> Path:
    """The reference (left) beside the remake (right) at each window's middle, worst first, with its name and score."""
    from PIL import Image, ImageDraw
    w, h = size
    rows = sorted(res["windows"], key=lambda r: r["score"])
    tiles = []
    for r in rows:
        t = (r["t0"] + r["t1"]) / 2
        pair = Image.new("RGB", (w * 2, h))
        for k, (path, at) in enumerate(((res["reference"], t), (res["remake"], t + offset))):
            f = _frames(path, at, at + 0.04, w, h, 25)
            if len(f):
                pair.paste(Image.fromarray(f[0][:, :, ::-1]), (k * w, 0))
        d = ImageDraw.Draw(pair)
        label = f'{r["window"]}  {t:.2f}s  {r["score"]:.2f}'
        d.rectangle((0, 0, 8 + 7 * len(label), 20), fill=(0, 0, 0))
        d.text((5, 4), label, fill=(255, 230, 0))
        d.line((w, 0, w, h), fill=(0, 0, 0), width=2)
        tiles.append(pair)
    n = max(1, -(-len(tiles) // cols))
    board = Image.new("RGB", (w * 2 * cols, h * n), (0, 0, 0))
    for i, p in enumerate(tiles):
        board.paste(p, ((i % cols) * w * 2, (i // cols) * h))
    out = Path(out)
    board.save(out, quality=88)
    return out


def run(ref, ours, shots_path=None, every=None, offset=0.0, out=None, prev=None, pairs=None) -> dict:
    shots = json.loads(Path(shots_path).read_text()) if shots_path else None
    res = compare(ref, ours, shots, every, offset)
    if prev:
        against(res, json.loads(Path(prev).read_text()))
    if out:
        Path(out).write_text(json.dumps(res, indent=1))
    if pairs:
        sheet(res, pairs, offset)
    return res
