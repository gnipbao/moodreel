"""`moodreel camera <reference> [--against <remake>]`: a film's camera, read off its picture, window by window.

A remake whose stills matched read wrong to its maker ("every camera move is off"): it held still where the reference
pushed in 34 %/s, panned left where it turned right, and never rolled through a whip of 74 degrees. The moves are in
the picture: a similarity fitted to the flow of the frame's own lines (measure/shot.py) gives, 15 times a second, where
the picture's centre goes (px/s at 1920 wide), how fast it grows (%/s, + pushes in) and turns (deg/s, + clockwise).
Per window this reports the travel, the push and the roll, and the camera turn and tilt they mean at a field of view
(the picture moving x px right is the camera turning left by atan(x / f), f = 540 / tan(fov / 2) at 1920 x 1080);
with --against, the remake's beside them and what is off. --js writes the reference's track as a film module
(camera-data.js) for kit/follow.js, which moves a remake's camera by it between a few anchors.

A move also has a shape: the picture's speed in the window's first, middle and last third (px/s at 1920, a push of 1 %/s
counted as the 9.6 px/s it moves the frame's edges) says whether it speeds into its end (a reveal), slows into it (a
hold), speeds up and settles, or keeps one pace. A remake whose camera glides between anchors at one pace reads as a
machine's beside a reference that rushes and settles; the verdict names it ("keeps one pace where the reference slows
into its end"), and kit/follow.js's anchor speed shapes it.

What the fit cannot see: a crane or a sideways move whose tilt keeps the subject in frame (little net motion), and a
dark frame full of falling pieces or a subject the camera tracks (the fit locks onto them: "still" though the camera
moves). Look at those windows; key them by hand. The remake's own fit reads "still" for the same reason when its
background is blurred out and its subject held in the centre: keep the background sharp enough to read.
"""
from __future__ import annotations

import json
import math
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

FPS = 15


def _window(args):
    from ..measure import shot
    path, t0, t1 = args
    m = shot.motion(shot._frames(path, t0, t1, fps=FPS))
    return {k: m.get(k) for k in ("moving", "speed", "pan", "zoom", "roll", "track")}


def read(path, windows, workers: int = 8) -> list[dict]:
    """Each window's motion: typical pan/zoom/roll and the frame-by-frame track (at FPS)."""
    jobs = [(str(path), t0, t1) for t0, t1, _ in windows]
    if workers > 1 and len(jobs) > 1:
        with ProcessPoolExecutor(min(workers, len(jobs))) as ex:
            rows = list(ex.map(_window, jobs))
    else:
        rows = [_window(j) for j in jobs]
    return [{"window": n, "t0": t0, "t1": t1, **r} for (t0, t1, n), r in zip(windows, rows)]


def totals(track) -> dict:
    """Over a window: travel x, y (px at 1920), push (% of size), roll (deg)."""
    a = np.array([x if x else [0, 0, 0, 0] for x in (track or [])], float) / FPS
    if not len(a):
        return {"x": 0.0, "y": 0.0, "push": 0.0, "roll": 0.0}
    return {"x": round(float(a[:, 0].sum()), 0), "y": round(float(a[:, 1].sum()), 0),
            "push": round(float(np.expm1(np.log1p(a[:, 2] / 100).sum()) * 100), 1), "roll": round(float(a[:, 3].sum()), 1)}


def turn(tot: dict, fov: float = 36.0) -> tuple[float, float]:
    """The camera turn (deg, + right) and tilt (deg, + up) that move the picture by tot's travel."""
    f = 540 / math.tan(math.radians(fov) / 2)
    return round(math.degrees(math.atan(-tot["x"] / f)), 1), round(math.degrees(math.atan(tot["y"] / f)), 1)


def shape(track) -> dict:
    """The move's speed in its first, middle and last third (px/s) and what that makes it."""
    a = np.array([x if x else [0, 0, 0, 0] for x in (track or [])], float)
    if len(a) < 6:
        return {"thirds": [0.0, 0.0, 0.0], "shape": "still"}
    s = np.hypot(np.hypot(a[:, 0], a[:, 1]), 9.6 * a[:, 2])
    th = [float(np.mean(p)) for p in np.array_split(s, 3)]
    first, mid, last = th
    if max(th) < 60:
        k = "still"
    elif last > 1.6 * first and last >= 0.9 * mid:
        k = "speeds up"
    elif first > 1.6 * last and first >= 0.9 * mid:
        k = "slows down"
    elif mid > 1.5 * max(first, last):
        k = "in and out"
    else:
        k = "one pace"
    return {"thirds": [round(x) for x in th], "shape": k}


SHAPED = {"speeds up": "speeds into its end", "slows down": "slows into its end", "in and out": "speeds up and settles"}


def verdict(r: dict, m: dict, rs: dict | None = None, ms: dict | None = None) -> list[str]:
    """What is off between the reference's window (r) and the remake's (m), both from totals(); with their shapes
    (rs, ms from shape()), a move whose speed curve differs."""
    out = []
    big = lambda v, lim: abs(v) >= lim  # noqa: E731
    if big(r["x"], 150) and (abs(m["x"]) < abs(r["x"]) * 0.3 or np.sign(m["x"]) != np.sign(r["x"])):
        out.append("pans the other way" if big(m["x"], 150) and np.sign(m["x"]) != np.sign(r["x"]) else "doesn't pan")
    if big(r["y"], 150) and (abs(m["y"]) < abs(r["y"]) * 0.3 or np.sign(m["y"]) != np.sign(r["y"])):
        out.append("tilts the other way" if big(m["y"], 150) and np.sign(m["y"]) != np.sign(r["y"]) else "doesn't tilt")
    if big(r["push"], 12) and (abs(m["push"]) < abs(r["push"]) * 0.3 or np.sign(m["push"]) != np.sign(r["push"])):
        out.append(("pushes in" if m["push"] > 0 else "pulls out") + (" where the reference pushes in" if r["push"] > 0 else " where the reference pulls out")
                   if big(m["push"], 12) else ("doesn't push in" if r["push"] > 0 else "doesn't pull out"))
    if big(r["roll"], 15) and abs(m["roll"]) < abs(r["roll"]) * 0.3:
        out.append("doesn't roll")
    if not out and (big(m["x"], 300) and not big(r["x"], 100) or big(m["push"], 25) and not big(r["push"], 8)):
        out.append("moves where the reference holds still")
    if rs and ms and rs["shape"] in SHAPED and ms["shape"] != rs["shape"] and ms["shape"] != "still":
        what = "keeps one pace" if ms["shape"] == "one pace" else SHAPED.get(ms["shape"], ms["shape"])
        out.append(f"{what} where the reference {SHAPED[rs['shape']]}")
    return out


def track_rows(rows: list[dict], duration: float) -> list[list[float]]:
    """The windows' tracks laid end to end at FPS, smoothed within each window (a 5-frame median, then a 5-frame mean)."""
    n = int(duration * FPS) + 2
    A = np.zeros((n, 4))
    seg = np.full(n, -1)
    for w, r in enumerate(rows):
        g0 = round(r["t0"] * FPS)
        for k, v in enumerate(r.get("track") or []):
            if g0 + k < n:
                if v:
                    A[g0 + k] = v
                seg[g0 + k] = w
    def pass_(X, f):
        Y = X.copy()
        for i in range(n):
            idx = [j for j in range(i - 2, i + 3) if 0 <= j < n and seg[j] == seg[i]]
            Y[i] = f(X[idx], axis=0)
        return Y
    C = pass_(pass_(A, np.median), np.mean)
    return [[round(float(x), 1) for x in row] for row in C]


def write_js(rows: list[list[float]], path, source: str = "") -> Path:
    path = Path(path)
    path.write_text(
        "// The reference's camera, read off its picture by `moodreel camera`" + (f" ({source})" if source else "") + ", 15 times a\n"
        "// second: where the picture's centre moves (px/s at 1920 wide, x right, y down), how fast it grows (%/s, + pushes\n"
        "// in) and turns (deg/s, + clockwise). kit/follow.js moves a remake's camera by it.\n"
        "export const MOTION = { fps: " + str(FPS) + ", rows: " + json.dumps(rows, separators=(",", ":")) + " };\n")
    return path


def report(res: dict) -> str:
    vs = res.get("remake") is not None
    w = max([8, *(len(r["window"]) for r in res["windows"])])
    head = f'{"window":>{w}} {"t0":>6} {"t1":>6} | reference: travel x    y  push%  roll  turn  tilt  shape'
    lines = [head + (" | remake: travel x    y  push%  roll  shape       off" if vs else "")]
    for r in res["windows"]:
        a = r["ref"]
        line = (f'{r["window"]:>{w}} {r["t0"]:6.2f} {r["t1"]:6.2f} | {a["x"]:+15.0f} {a["y"]:+5.0f} {a["push"]:+6.1f} {a["roll"]:+5.1f} '
                f'{r["turn"][0]:+5.1f} {r["turn"][1]:+5.1f}  {a.get("shape", ""):<10}')
        if vs:
            m = r["rem"]
            line += f' | {m["x"]:+12.0f} {m["y"]:+5.0f} {m["push"]:+6.1f} {m["roll"]:+5.1f}  {m.get("shape", ""):<10}  ' + ", ".join(r["off"])
        lines.append(line)
    if vs:
        n = sum(1 for r in res["windows"] if r["off"])
        lines.append(f"{len(res['windows']) - n} of {len(res['windows'])} windows move as the reference's does")
    return "\n".join(lines)


def run(reference, shots=None, every=None, against=None, js=None, out=None, fov: float = 36.0) -> dict:
    from .compare import duration, windows
    shots = json.loads(Path(shots).read_text()) if isinstance(shots, (str, Path)) else shots
    wins = windows(reference, shots, every)
    ref = read(reference, wins)
    rem = read(against, wins) if against else None
    res = {"reference": str(reference), "remake": str(against) if against else None, "fov": fov, "windows": []}
    for i, r in enumerate(ref):
        a, rs = totals(r["track"]), shape(r["track"])
        row = {"window": r["window"], "t0": r["t0"], "t1": r["t1"], "ref": a | rs, "turn": turn(a, fov)}
        if rem:
            m, ms = totals(rem[i]["track"]), shape(rem[i]["track"])
            row |= {"rem": m | ms, "off": verdict(a, m, rs, ms)}
        res["windows"].append(row)
    if js:
        write_js(track_rows(ref, duration(reference)), js, Path(reference).name)
    if out:
        Path(out).write_text(json.dumps(res, indent=1))
    return res
