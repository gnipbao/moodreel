"""`moodreel origin <video>`: how each shot was made, before anything is rebuilt, and what to rebuild it with.

Each shot (cut by `cutlist`, or given as windows) is read for:

- **cadence**: how much of it holds still (`holds`, the share of frame steps that change nothing); the camera's move,
  read as the flow's global part, and what moves on top of it once that is taken away. Each is on ones (a new
  position every frame), twos or threes (`camera_on`, `subject_on`; None where nothing moves). A character on twos
  under a camera on ones is the mark of 3D animation made to look drawn.
- **texture**: the share of flat 8 x 8 blocks (`flat`), how many colours cover 95 % of the picture (`colours`), the
  noise left after smoothing (`noise`, Immerkaer's estimate), how much of the picture is smooth shading (`smooth`), and
  whether a fine texture stays put on the screen while the picture moves under it (`overlay`).
- **kind**: graphics (flat fills, few colours: drawn in code), render_3d (smooth shading and clean silhouettes over
  most of the frame), footage (texture and noise everywhere: filmed or generated video; telling the two apart takes
  eyes, the strip is there for that), still_pan (one picture moved rigidly), hold (nothing moves).
- **route**: canvas, three, three+assets (a 3D shot on twos or with painted materials: models built in a 3D tool, the
  film rendered in three.js with its subject stepped), footage (to be filmed or generated: outside a code renderer),
  still-pan, hold.

Writes origin.json, ORIGIN.md and strips/ (each shot's first, middle and last frame). Deterministic; nothing is sent
anywhere.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import cv2
import numpy as np

from . import cutlist
from ..video import probe

SMALL = 160
TEX = 320



def _stream(path: str, fps: float, w: int):
    p = probe(path)
    h = int(round(p["h"] * w / p["w"] / 2) * 2)
    proc = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(path), "-vf", f"setpts=PTS-STARTPTS,fps={fps},scale={w}:{h}:flags=area",
                             "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
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


def shots_of(cuts: dict) -> list[tuple[int, int]]:
    """Shot spans [start, end) from a cut list: cuts start shots; a dissolve or dip ends one and starts the next."""
    bounds = sorted([(c, c) for c in cuts["cuts"]] + [(a, b + 1) for a, b in cuts["dissolves"] + cuts["dips"]])
    out, start = [], 0
    for lo, hi in bounds:
        if lo - start >= 2:
            out.append((start, lo))
        start = max(start, hi)
    if cuts["n"] - start >= 2:
        out.append((start, cuts["n"]))
    return out or [(0, cuts["n"])]


def _steps(series: np.ndarray, floor: float) -> int | None:
    """On ones, twos or threes. A step that stands well above both its neighbours is a new drawing after a held one:
    when such peaks come every second (third) step through a good share of the shot, it is on twos (threes). Motion
    that flows (on ones), parallax included, makes no peaks."""
    if len(series) < 8:
        return None
    nb = np.maximum(np.r_[series[1:], 0.0], np.r_[0.0, series[:-1]])
    idx = np.nonzero((series > 1.6 * nb + 0.05) & (series > floor))[0]
    if len(idx) >= 4:
        gaps = np.diff(idx)
        cover = len(idx) / len(series)
        if (gaps == 2).mean() >= 0.6 and cover >= 0.25:
            return 2
        if (gaps == 3).mean() >= 0.6 and cover >= 0.18:
            return 3
    return 1 if float(np.median(series)) > floor else None


class _Motion:
    def __init__(self):
        self.dis = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_FAST)
        self.last = (0.0, 0.0)

    def step(self, a: np.ndarray, b: np.ndarray) -> tuple[float, float, float]:
        """camera (the flow's global affine part, px), subject (what moves once that is taken away: the mean of the
        busiest tenth, px), and the residual after the global move alone."""
        flow = self.dis.calc(a, b, None)
        h, w = a.shape
        ys, xs = np.mgrid[4:h - 4:6, 4:w - 4:6]
        src = np.stack([xs.ravel(), ys.ravel()], 1).astype(np.float32)
        dst = src + flow[ys.ravel(), xs.ravel()]
        m, _ = cv2.estimateAffinePartial2D(src, dst, method=cv2.RANSAC, ransacReprojThreshold=1.0)
        if m is None:
            m = np.array([[1, 0, 0], [0, 1, 0]], np.float32)
        glob = (src @ m[:, :2].T + m[:, 2]) - src
        local = np.linalg.norm((dst - src) - glob, axis=1)
        cam = float(np.median(np.linalg.norm(glob, axis=1)))
        k = max(1, len(local) // 10)
        subject = float(np.sort(local)[-k:].mean())
        self.last = (float(m[0, 2]), float(m[1, 2]))          # the camera's own shift this step
        return cam, subject, float(np.median(local))


def _immerkaer(g: np.ndarray) -> float:
    k = np.array([[1, -2, 1], [-2, 4, -2], [1, -2, 1]], np.float32)
    h, w = g.shape
    return float(np.sqrt(np.pi / 2) / (6 * (w - 2) * (h - 2)) * np.abs(cv2.filter2D(g.astype(np.float32), -1, k)[1:-1, 1:-1]).sum())


def texture(frames: list[np.ndarray]) -> dict:
    """Read after a 5 px median (grain and print texture laid over flat fills drop out): flat blocks, colours,
    texture density (`busy`: the share of pixels on an edge or a texture), straight edges (`straight`: the share of
    edge pixels on long straight lines, as in type, UI and drawn shapes); and on the raw frame the noise and the
    smooth share."""
    flat, colours, noise, smooth, busy, straight = [], [], [], [], [], []
    for f in frames:
        d = cv2.medianBlur(f, 5)
        g = cv2.cvtColor(d, cv2.COLOR_RGB2GRAY).astype(np.float32)
        raw = cv2.cvtColor(f, cv2.COLOR_RGB2GRAY).astype(np.float32)
        h, w = g.shape[0] // 8 * 8, g.shape[1] // 8 * 8
        blocks = g[:h, :w].reshape(h // 8, 8, w // 8, 8).std(axis=(1, 3))
        flat.append(float((blocks < 1.5).mean()))
        q = (d[:h, :w] // 8).reshape(-1, 3).astype(np.int32)
        keys = np.sort(np.bincount(q[:, 0] * 1024 + q[:, 1] * 32 + q[:, 2]))[::-1]
        colours.append(int(np.searchsorted(np.cumsum(keys), 0.95 * keys.sum()) + 1))
        noise.append(_immerkaer(raw))
        gm = cv2.magnitude(cv2.Sobel(g, cv2.CV_32F, 1, 0), cv2.Sobel(g, cv2.CV_32F, 0, 1))
        smooth.append(float((gm < 6).mean()))
        lo, hi = np.percentile(g, (2, 98))
        gn = ((g - lo) * (255.0 / max(hi - lo, 24.0))).astype(np.float32)   # contrast stretched: a dark film counts too
        gmn = cv2.magnitude(cv2.Sobel(gn, cv2.CV_32F, 1, 0), cv2.Sobel(gn, cv2.CV_32F, 0, 1))
        busy.append(float((gmn > 20).mean()))
        edges = cv2.Canny(g.astype(np.uint8), 40, 120)
        n_edges = int((edges > 0).sum())
        lines = cv2.HoughLinesP(edges, 1, np.pi / 180, 30, minLineLength=max(12, g.shape[1] // 16), maxLineGap=2)
        on = np.zeros_like(edges)
        for x0, y0, x1, y1 in (lines.reshape(-1, 4) if lines is not None else []):
            cv2.line(on, (int(x0), int(y0)), (int(x1), int(y1)), 255, 1)
        straight.append(float(((on > 0) & (edges > 0)).sum() / n_edges) if n_edges else 0.0)
    med = lambda xs: float(np.median(xs)) if xs else 0.0  # noqa: E731
    return {"flat": round(med(flat), 3), "colours": int(med(colours)), "noise": round(med(noise), 2), "smooth": round(med(smooth), 3),
            "busy": round(med(busy), 3), "straight": round(med(straight), 3)}


def _overlay(a: np.ndarray, b: np.ndarray, motion: _Motion) -> bool:
    """A fine texture fixed to the screen: between two frames whose picture moved, the 1-4 px band still lines up where
    it stands."""
    flow = motion.dis.calc(a, b, None)
    mag = np.linalg.norm(flow, axis=2)
    m = mag > 2
    if m.mean() < 0.2:
        return False
    band = lambda g: cv2.GaussianBlur(g.astype(np.float32), (0, 0), 1.0) - cv2.GaussianBlur(g.astype(np.float32), (0, 0), 4.0)  # noqa: E731
    x, y = band(a)[m], band(b)[m]
    x, y = x - x.mean(), y - y.mean()
    d = float(np.sqrt((x * x).sum() * (y * y).sum()))
    return bool(d > 0 and (x * y).sum() / d > 0.3)


def measure(path: str, spans: list[tuple[int, int]], fps: float, samples: int = 9) -> list[dict]:
    """One pass over the film: per frame step the camera, subject and residual motion and the whole-frame change; a few
    frames per shot at texture size (and the frame four on from each, for the overlay test)."""
    want = {}
    for k, (a, b) in enumerate(spans):
        idx = np.unique(np.linspace(a, b - 1, min(samples, b - a)).astype(int))
        for i in idx:
            want.setdefault(int(i), []).append(k)
            if i + 4 < b:
                want.setdefault(int(i) + 4, []).append(k)
    motion = _Motion()
    cam, sub, loc, change, shift = [0.0], [0.0], [0.0], [0.0], [(0.0, 0.0)]
    kept = {k: {} for k in range(len(spans))}
    prev = prevf = None
    for i, f in enumerate(_stream(path, fps, TEX)):
        g = cv2.cvtColor(cv2.resize(f, (SMALL, int(round(SMALL * f.shape[0] / f.shape[1]))), interpolation=cv2.INTER_AREA),
                         cv2.COLOR_RGB2GRAY)
        if prev is not None:
            c, s, r = motion.step(prev, g)
            shift.append(motion.last)
            cam.append(c)
            sub.append(s)
            loc.append(r)
            change.append(float(np.abs(f.astype(np.int16) - prevf).mean()))
        for k in want.get(i, []):
            kept[k][i] = f
        prev, prevf = g, f.astype(np.int16)
    cam, sub, loc, change = map(np.array, (cam, sub, loc, change))
    shift = np.array(shift)
    out = []
    for k, (a, b) in enumerate(spans):
        frames = kept[k]
        idx = sorted(frames)
        base = [frames[i] for i in idx if i - 4 not in frames or i < a + 4][:samples]
        pairs = [(frames[i], frames[i + 4]) for i in idx if i + 4 in frames]
        steps = slice(a + 1, b)
        c, s, ch = cam[steps], sub[steps], change[steps]
        v = shift[steps]
        speed = np.linalg.norm(v, axis=1)
        # how much the camera's path shakes: frame-to-frame change of its velocity against the velocity itself
        jitter = float(np.median(np.linalg.norm(np.diff(v, axis=0), axis=1)) / (np.median(speed) + 0.05)) if len(v) > 3 else 0.0
        moving_cam = len(c) and float(np.median(c)) > 0.15
        tex = texture(base)
        gray = lambda x: cv2.cvtColor(x, cv2.COLOR_RGB2GRAY)  # noqa: E731
        tex["overlay"] = any(_overlay(gray(p), gray(q), motion) for p, q in pairs[:3])
        out.append({
            "start": a, "end": b, "t0": round(a / fps, 3), "t1": round(b / fps, 3),
            "cadence": {"holds": round(float((ch < 0.2).mean()) if len(ch) else 1.0, 3),
                        "camera_on": _steps(c, 0.1) if moving_cam else None,
                        "subject_on": _steps(s, 0.15)},
            "texture": tex,
            "_motion": {"camera": round(float(np.median(c)) if len(c) else 0.0, 3),
                        "subject": round(float(np.median(s)) if len(s) else 0.0, 3),
                        "residual": round(float(np.median(loc[steps])) if len(c) else 0.0, 3),
                        "change": round(float(np.mean(ch)) if len(ch) else 0.0, 2), "jitter": round(jitter, 3)},
            "_frames": [frames[i] for i in (idx[0], idx[len(idx) // 2], idx[-1])] if idx else [],
        })
    return out


# what the texture and the cadence say, in the order they are asked (thresholds read off films whose making is known)
DRAWN_FLAT, DRAWN_COLOURS, DRAWN_STRAIGHT, PALETTE_FLAT = 0.75, 30, 0.45, 0.5
FOOT_BUSY, FOOT_STRAIGHT, FOOT_SMOOTH = 0.40, 0.08, 0.36
SMOOTH_PATH, MOVING = 0.2, 0.15
GRAIN_NOISE, STILL_HOLDS = 1.95, 0.7


def classify(shot: dict) -> tuple[str, list[str]]:
    t, c, m = shot["texture"], shot["cadence"], shot["_motion"]
    photographic = t["busy"] >= FOOT_BUSY and t["straight"] <= FOOT_STRAIGHT and t["smooth"] <= FOOT_SMOOTH
    if c["holds"] >= 0.98 and photographic:
        return "hold", [f"nothing moves ({c['holds']:.0%} of the steps hold) over a photographic picture"]
    if m["camera"] >= 0.3 and m["residual"] <= 0.03 and m["subject"] <= 0.1 and photographic:
        return "still_pan", [f"the whole picture moves as one ({m['camera']:.2f} px a frame, nothing on top): one picture moved"]
    if t["flat"] >= DRAWN_FLAT and t["colours"] <= DRAWN_COLOURS:
        return "graphics", [f"flat fills over {t['flat']:.0%} of the frame and {t['colours']} colours: drawn"]
    if t["straight"] >= DRAWN_STRAIGHT:
        return "graphics", [f"{t['straight']:.0%} of the edges on long straight lines: type, UI or drawn shapes"]
    if t["colours"] <= DRAWN_COLOURS and t["flat"] >= PALETTE_FLAT:
        return "graphics", [f"a palette of {t['colours']} colours over flat fills ({t['flat']:.0%}): a designed frame"]
    if photographic and c["subject_on"] != 2:
        if m["camera"] >= MOVING and m["jitter"] <= SMOOTH_PATH:
            return "render_3d", [f"texture everywhere (busy {t['busy']:.2f}) but a camera path too smooth for a hand or a "
                                 f"generator (jitter {m['jitter']:.2f}): a detailed 3D render"]
        return "footage", [f"texture everywhere (busy {t['busy']:.2f}), {t['straight']:.0%} straight edges, little smooth shading "
                           f"({t['smooth']:.0%}), moving on ones: filmed or generated video (the strip tells which)"]
    if t["noise"] >= GRAIN_NOISE:
        return "graphics", [f"grain or print texture over the picture (noise {t['noise']:.1f}) on a designed frame"]
    if c["holds"] >= STILL_HOLDS:
        return "graphics", [f"a designed frame that mostly holds ({c['holds']:.0%} of the steps)"]
    why = [f"smooth shading over {t['smooth']:.0%} of the frame, {t['colours']} colours, clean silhouettes: a 3D render"]
    if c["subject_on"] == 2:
        why.append("the subject moves on twos" + (" under a camera on ones" if c["camera_on"] == 1 else "")
                   + ": 3D animation made to look drawn")
    return "render_3d", why


def route(kind: str, shot: dict) -> str:
    if kind == "render_3d":
        t, c = shot["texture"], shot["cadence"]
        painted = t["busy"] >= 0.3 and t["colours"] >= 150
        return "three+assets" if c["subject_on"] == 2 or painted else "three"
    return {"graphics": "canvas", "footage": "footage", "still_pan": "still-pan", "hold": "hold"}[kind]


ROUTES = {
    "canvas": "draw it in 2D code (kit + canvas)",
    "three": "model it in three.js and render it as it is",
    "three+assets": "build the characters and sets as 3D assets (a 3D tool, painted materials), render in three.js, "
                    "the subject stepped on twos where the reference is",
    "footage": "film it or generate it: outside a code renderer; keep the reference only for timing",
    "still-pan": "one picture and the measured move",
    "hold": "one picture",
}


def run(path, shots=None, out=None) -> dict:
    path = str(path)
    fps = probe(path)["fps"]
    if shots:
        windows = json.loads(Path(shots).read_text()) if isinstance(shots, (str, Path)) else shots
        n = cutlist.find(path)["n"]
        spans = [(int(round(a * fps)), min(n, int(round(b * fps)))) for a, b, *_ in windows]
        names = [w[2] if len(w) > 2 else None for w in windows]
        cuts = None
    else:
        cuts = cutlist.find(path)
        n = cuts["n"]
        spans = shots_of(cuts)
        names = [None] * len(spans)
    feats = measure(path, spans, fps)
    res = {"video": path, "fps": fps, "frames": n, "duration": round(n / fps, 3),
           "cuts": cuts["cuts"] if cuts else None, "shots": []}
    for s, name in zip(feats, names):
        kind, why = classify(s)
        r = route(kind, s)
        shot = {k: v for k, v in s.items() if not k.startswith("_")}
        shot.update({"name": name, "kind": kind, "route": r, "evidence": why, "motion": s["_motion"]})
        res["shots"].append(shot)
    total = sum(s["t1"] - s["t0"] for s in res["shots"]) or 1
    res["summary"] = {k: round(sum(s["t1"] - s["t0"] for s in res["shots"] if s["kind"] == k) / total, 3)
                      for k in ("graphics", "render_3d", "footage", "still_pan", "hold")}
    if out:
        out = Path(out)
        (out / "strips").mkdir(parents=True, exist_ok=True)
        for k, s in enumerate(feats):
            if s["_frames"]:
                cv2.imwrite(str(out / "strips" / f"shot-{k:03d}.jpg"), cv2.cvtColor(np.hstack(s["_frames"]), cv2.COLOR_RGB2BGR),
                            [cv2.IMWRITE_JPEG_QUALITY, 85])
        (out / "origin.json").write_text(json.dumps(res, indent=1))
        (out / "ORIGIN.md").write_text(report(res))
    return res


def report(res: dict) -> str:
    sm = res["summary"]
    lines = ["# How it was made, shot by shot", "", f"`{res['video']}`: {res['duration']} s, {res['fps']:g} fps, "
             f"{len(res['shots'])} shots.", "",
             "In all: " + ", ".join(f"{k.replace('_', ' ')} {v:.0%}" for k, v in sm.items() if v), "",
             "| shot | from | to | kind | holds | camera on | subject on | route |", "|---|---|---|---|---|---|---|---|"]
    on = lambda v: "-" if v is None else f"{v}s" if v > 1 else "ones"  # noqa: E731
    for k, s in enumerate(res["shots"]):
        c = s["cadence"]
        lines.append(f"| {s['name'] or k} | {s['t0']:.2f} | {s['t1']:.2f} | {s['kind']} | {c['holds']:.0%} | "
                     f"{on(c['camera_on'])} | {on(c['subject_on'])} | {s['route']} |")
    lines += ["", "## Why", ""]
    for k, s in enumerate(res["shots"]):
        lines.append(f"- **{s['name'] or k}** ({s['t0']:.2f}-{s['t1']:.2f} s, strips/shot-{k:03d}.jpg): " + "; ".join(s["evidence"]))
    lines += ["", "## Routes", ""] + [f"- **{r}**: {ROUTES[r]}" for r in sorted({s["route"] for s in res["shots"]})]
    lines += ["", "Filmed or generated? The numbers can't tell (both are photographic); the strips can: hands, text, "
              "physics and textures that drift give a generated shot away."]
    return "\n".join(lines) + "\n"
