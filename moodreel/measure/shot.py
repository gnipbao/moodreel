"""`moodreel dossier <video>`: read each shot of a video the way its code would have to be written.

Matching stills is not enough to rebuild a shot: a remake whose frames looked right ran at 0.6 of the reference's
speed with its motion pointing another way (flow agreement 0.1), drew a few dozen strokes where the reference drew
10^5 GPU hairlines, faked in 2D what was a 3D scene, and guessed the glow. Each of those can be read off the video:

  motion    the optical flow of the picture's own lines (dark, flat grounds included), fitted shot by shot with a
            similarity: pan (px/s at 1920 wide), zoom (%/s), roll (deg/s); the field's curl (a vortex, and which way
            it turns); surges; and how much more of the moving lines a perspective fit explains than a flat one (a
            camera moving through a 3D scene)
  linework  how much of the frame is line, how wide the lines are (px at 1920), how much of it is hatching (dense
            parallel lines), the spread of orientations, the spatial frequency, the length of line per frame
  finish    glow (the light around the brightest pixels), a colour fringe at the corners (px), grain (levels)
  colour    luma, highlight and saturated shares

and turned into technique hints (`hints`): the rules come from comparing a remake drawn from stills with the source
code of the same film (docs/research/VISION-TO-CODE.md). Images: each shot's keyframes, and the same frames with the
flow drawn as arrows, so the director sees which way things move before writing a camera.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import numpy as np

from .. import video

W, H = 640, 360            # analysis size; px figures are reported at 1920 wide
TO1920 = 1920 / W
FPS = 15


def _probe(path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True, check=True).stdout
    return float(out.strip())


def _frames(path, t0, t1, fps=FPS, w=W, h=H) -> np.ndarray:
    """[t0, t1) at fps, frame k the picture on screen at t0 + k / fps (video.window); a start before 0 reads from 0."""
    a = max(0.0, t0)
    return video.window(str(path), a, a + (t1 - t0), fps, w, h)


def _structure(g):
    """Where the picture has lines or edges: gradient above the noise, widened a little."""
    import cv2
    mag = np.hypot(cv2.Sobel(g, cv2.CV_32F, 1, 0, ksize=3), cv2.Sobel(g, cv2.CV_32F, 0, 1, ksize=3))
    return cv2.dilate((mag > 24).astype(np.uint8), np.ones((5, 5), np.uint8)) > 0


def motion(frames: np.ndarray, fps: float = FPS) -> dict:
    """The motion of a shot's picture, from flow on its own lines."""
    import cv2
    gray = [cv2.cvtColor(f, cv2.COLOR_BGR2GRAY) for f in frames]
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    rows = []
    for a, b in zip(gray, gray[1:]):
        mask = _structure(a)
        if mask.mean() < 0.002:
            rows.append(None)
            continue
        f = cv2.calcOpticalFlowFarneback(a, b, None, 0.5, 4, 21, 3, 5, 1.2, 0)
        mag = np.hypot(f[..., 0], f[..., 1])
        pts = np.flatnonzero(mask.ravel())
        if len(pts) > 6000:
            pts = pts[np.linspace(0, len(pts) - 1, 6000).astype(int)]
        src = np.stack([xx.ravel()[pts], yy.ravel()[pts]], 1)
        dst = src + f.reshape(-1, 2)[pts]
        speed = float(mag[mask].mean())
        M, inl = cv2.estimateAffinePartial2D(src, dst, method=cv2.RANSAC, ransacReprojThreshold=1.0)
        if M is None or speed < 0.2:                             # under ~9 px/s at 1920: codec noise, not motion
            rows.append({"speed": speed, "still": True})
            continue
        # a camera moving through a scene: a perspective (homography) fit explains much more of the moving lines than
        # a flat similarity does. Only the lines that move count (elements standing still would favour neither)
        mv = np.linalg.norm(dst - src, axis=1) > 0.3
        gain = None
        if mv.sum() >= 300:
            _, inS = cv2.estimateAffinePartial2D(src[mv], dst[mv], method=cv2.RANSAC, ransacReprojThreshold=0.7)
            Hm, inH = cv2.findHomography(src[mv], dst[mv], cv2.RANSAC, 0.7)
            if inS is not None and inH is not None:
                gain = float(inH.mean() - inS.mean())
        fit = src @ M[:, :2].T + M[:, 2]
        resid = float(np.linalg.norm(dst - fit, axis=1).mean())
        s, rot = float(np.hypot(M[0, 0], M[1, 0])), float(np.arctan2(M[1, 0], M[0, 0]))
        c = np.array([W / 2, H / 2])
        pan = (M[:, :2] @ c + M[:, 2]) - c                       # where the centre goes: the pan
        du_dy, du_dx = np.gradient(f[..., 0])
        dv_dy, dv_dx = np.gradient(f[..., 1])
        curl = float(((dv_dx - du_dy) / 2)[mask].mean())         # rad per frame, + is clockwise on screen (y down)
        div = float(((du_dx + dv_dy) / 2)[mask].mean())
        rows.append({"speed": speed, "still": False, "panx": float(pan[0]), "pany": float(pan[1]), "zoom": np.log(s),
                     "rot": rot, "resid": resid, "unexplained": resid / max(speed, 1e-6), "curl": curl, "div": div,
                     "gain": gain})
    live = [r for r in rows if r and not r["still"]]
    speeds = np.array([r["speed"] if r else 0.0 for r in rows]) * TO1920 * fps
    if not live:
        return {"moving": False, "speed": round(float(speeds.mean()) if len(speeds) else 0.0, 1), "profile": []}
    med = lambda k: float(np.median([r[k] for r in live]))  # noqa: E731
    tot = lambda k: float(np.sum([r[k] for r in live]))     # noqa: E731
    mot = np.array([r["speed"] for r in live])
    return {
        "moving": True,
        "speed": round(float(speeds.mean()), 1),                               # px/s at 1920 wide, all frames
        "pan": [round(med("panx") * TO1920 * fps, 1), round(med("pany") * TO1920 * fps, 1)],  # px/s, typical
        "travel": [round(tot("panx") * TO1920, 0), round(tot("pany") * TO1920, 0)],          # px over the shot
        "zoom": round(med("zoom") * fps * 100, 1),                             # %/s, + pushes in
        "zoom_total": round((float(np.exp(tot("zoom"))) - 1) * 100, 1),        # % over the shot
        "roll": round(float(np.degrees(med("rot"))) * fps, 1),                 # deg/s, + clockwise
        "spin": round(float(np.degrees(med("curl"))) * fps, 1),                # deg/s of the field's own rotation
        "unexplained": round(float(np.average([r["unexplained"] for r in live], weights=mot)), 2),
        "surges": round(float(np.percentile(speeds, 90) / max(np.median(speeds), 1e-6)), 2),  # peaky (>2.5) or smooth
        # how much more of the moving lines a perspective fit explains than a flat one (75th percentile of frame pairs)
        "perspective": round(float(np.percentile(g, 75)), 3) if (g := [r["gain"] for r in live if r["gain"] is not None]) else None,
        "profile": [round(float(x), 0) for x in speeds],
        # frame by frame (at FPS): pan px/s, zoom %/s, roll deg/s. A window's medians hide a move made in a few frames
        # (a fall between two holds reads as no fall): write camera paths from this, and the poses of `moodreel pose`
        "track": [None if not r or r["still"] else [round(r["panx"] * TO1920 * fps, 0), round(r["pany"] * TO1920 * fps, 0),
                                                     round(float(r["zoom"]) * fps * 100, 1), round(float(np.degrees(r["rot"])) * fps, 1)]
                  for r in rows],
    }


def linework(img) -> dict:
    """What the frame is drawn with: line density, width, orientations, hatching, spatial frequency. Read at 1280 wide
    (a 1-2 px hairline at 1080p is under a pixel at the motion's analysis size)."""
    import cv2
    k = 1920 / img.shape[1]
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)
    edges = cv2.Canny(img, 40, 120) > 0
    bg = cv2.GaussianBlur(g, (0, 0), 6)
    ink = ((g - bg) if np.median(g) < 128 else (bg - g)) > 16              # light lines on a dark ground, or dark on light
    dist = cv2.distanceTransform(ink.astype(np.uint8), cv2.DIST_L2, 3)
    ridge = dist[(dist > 0) & (cv2.dilate(dist, np.ones((3, 3))) == dist)]
    width = float(np.median(ridge) * 2 * k) if ridge.size else 0.0
    gx, gy = cv2.Sobel(g, cv2.CV_32F, 1, 0), cv2.Sobel(g, cv2.CV_32F, 0, 1)
    mag, ang = cv2.cartToPolar(gx, gy)
    strong = mag > 30
    h, _ = np.histogram(np.mod(ang[strong], np.pi), bins=16, range=(0, np.pi), weights=mag[strong])
    p = h / max(h.sum(), 1e-6)
    # hatching: windows dense with lines that run parallel, wherever they curve (structure-tensor coherence)
    jxx, jyy, jxy = (cv2.GaussianBlur(a, (0, 0), 5) for a in (gx * gx, gy * gy, gx * gy))
    coh = np.sqrt((jxx - jyy) ** 2 + 4 * jxy ** 2) / np.maximum(jxx + jyy, 1e-6)
    dens = cv2.blur(edges.astype(np.float32), (24, 24))
    F = np.abs(np.fft.rfft2(g - g.mean()))
    fr = np.sqrt(np.fft.rfftfreq(img.shape[1])[None, :] ** 2 + np.fft.fftfreq(img.shape[0])[:, None] ** 2)
    return {"lines": round(float(edges.mean()), 4),
            "width": round(width, 2),
            "orientations": round(float(-(p[p > 0] * np.log2(p[p > 0])).sum()), 2),
            "hatched": round(float(((dens > 0.14) & (coh > 0.55)).mean()), 4),
            "freq": round(float((F * fr).sum() / max(F.sum(), 1e-6)) / k, 3),      # cycles per px at 1920
            "line_px": int(edges.sum() / 2 * k)}                                    # length of line, px at 1920


def finish(img) -> dict:
    """Glow around the brightest pixels, the colour fringe at the corners, grain in the dark."""
    import cv2
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)
    hot = (g > 235).astype(np.uint8)
    glow = None
    if hot.sum() > 20:
        ring = cv2.dilate(hot, np.ones((25, 25))) - cv2.dilate(hot, np.ones((7, 7)))
        glow = round(float(g[ring > 0].mean() / 255), 3)
    shifts = []
    for y0, x0 in ((0, 0), (0, W - 200), (H - 120, 0), (H - 120, W - 200)):
        r, b = (img[y0:y0 + 120, x0:x0 + 200, k].astype(np.float32) for k in (2, 0))
        if r.std() < 6 or b.std() < 6:
            continue
        (dx, dy), resp = cv2.phaseCorrelate(cv2.Laplacian(b, cv2.CV_32F), cv2.Laplacian(r, cv2.CV_32F))
        if resp > 0.2:
            out = np.array([x0 + 100 - W / 2, y0 + 60 - H / 2])
            shifts.append(float(np.dot([dx, dy], out / np.linalg.norm(out))))   # radial: + red outward
    flat = (g < 40) & (np.hypot(cv2.Sobel(g, cv2.CV_32F, 1, 0), cv2.Sobel(g, cv2.CV_32F, 0, 1)) < 12)
    hp = g - cv2.GaussianBlur(g, (0, 0), 2)
    return {"glow": glow, "fringe": round(float(np.median(shifts)) * TO1920, 2) if shifts else None,
            "grain": round(float(hp[flat].std()), 2) if flat.sum() > 500 else None}


def colour(img) -> dict:
    import cv2
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    return {"luma": round(float(g.mean()), 1), "highlights": round(float((g > 235).mean()), 4),
            "saturated": round(float(((hsv[..., 1] > 120) & (hsv[..., 2] > 80)).mean()), 4)}


# technique hints: each rule what it saw and what to build; thresholds calibrated on pdoom-video (the remake drawn from
# stills against the source of the same film, docs/research/VISION-TO-CODE.md)
def hints(sig: dict) -> list[str]:
    m, lw, fn = sig["motion"], sig["linework"], sig["finish"]
    out = []
    if lw["lines"] >= 0.045 and lw["width"] <= 4.5:
        out.append(f"a line-heavy picture ({lw['lines']:.1%} of the frame is line, {lw['width']} px wide, about "
                   f"{lw['line_px']:,} px of line): draw it on the GPU (kit/gl.js lines, or lines a shader draws), not as a "
                   "few canvas strokes; the source drew 10^4-10^5 segments a frame")
    if lw["hatched"] >= 0.15:
        out.append(f"hatching: {lw['hatched']:.0%} of the frame is dense parallel lines: engraving, line width carrying the "
                   "shade (kit/gl.js hatch, engrave), the lines following the surface where they curve")
    if m.get("moving") and m["speed"] >= 30 and (m.get("perspective") or 0) >= 0.065:
        out.append(f"a camera moving through a scene (a perspective fit explains {m['perspective']:.0%} more of the moving "
                   "lines than a flat one): build it in 3D (kit/three.js, or a ray-marched kit/gl.js pass), not as 2D layers")
    if m.get("moving") and abs(m["spin"]) >= 20 and abs(m["spin"]) > abs(m["roll"]) * 1.5:
        out.append(f"the picture turns about a point at {abs(m['spin'])} deg/s, {'clockwise' if m['spin'] > 0 else 'counter-clockwise'}"
                   " on screen: a vortex or an orbit; keep the direction")
    if m.get("moving") and abs(m["roll"]) >= 8:
        out.append(f"the camera rolls {abs(m['roll'])} deg/s {'clockwise' if m['roll'] > 0 else 'counter-clockwise'}")
    if m.get("moving") and abs(m["zoom"]) >= 4:
        out.append(f"{'push in' if m['zoom'] > 0 else 'pull out'} at {abs(m['zoom'])} %/s ({m['zoom_total']:+}% over the shot)")
    if m.get("moving") and np.hypot(*m["pan"]) >= 40:
        out.append(f"pan {m['pan'][0]:+} x, {m['pan'][1]:+} y px/s (travel {m['travel'][0]:+.0f}, {m['travel'][1]:+.0f} px)")
    if m.get("moving") and m["surges"] >= 2.5:
        out.append(f"motion comes in surges (peaks {m['surges']}x the median): moves start and land on events, hold between")
    if fn["glow"] is not None and fn["glow"] >= 0.18:
        out.append(f"bright light blooms ({fn['glow']:.2f} of the highlight's level 6-24 px around it): colour past 1 and a "
                   "bloom pass, not a canvas shadow")
    if fn["fringe"] is not None and abs(fn["fringe"]) >= 0.3:
        out.append(f"a colour fringe of {abs(fn['fringe'])} px at the corners: chromatic aberration in the post")
    return out


def _sheet(frames, path, flows=False):
    import cv2
    pick = frames[np.linspace(0, len(frames) - 2, min(5, len(frames) - 1)).astype(int)] if len(frames) > 1 else frames
    tiles = []
    for k, f in enumerate(pick):
        t = cv2.resize(f, (384, 216))
        if flows:
            i = int(np.linspace(0, len(frames) - 2, len(pick)).astype(int)[k])
            a, b = (cv2.cvtColor(frames[j], cv2.COLOR_BGR2GRAY) for j in (i, i + 1))
            fl = cv2.calcOpticalFlowFarneback(a, b, None, 0.5, 4, 21, 3, 5, 1.2, 0)
            mask = _structure(a)
            for y in range(12, H, 24):
                for x in range(12, W, 24):
                    if not mask[y, x]:
                        continue
                    u, v = fl[y, x] * 4                           # arrows four frames long
                    if np.hypot(u, v) < 1:
                        continue
                    p0 = (int(x * 0.6), int(y * 0.6))
                    p1 = (int((x + u) * 0.6), int((y + v) * 0.6))
                    cv2.arrowedLine(t, p0, p1, (60, 220, 255), 1, cv2.LINE_AA, tipLength=0.3)
        tiles.append(t)
    cv2.imwrite(str(path), np.hstack(tiles))


def read_shot(video, t0: float, t1: float, out_dir: Path | None = None, name: str = "shot") -> dict:
    frames = _frames(video, t0, t1)
    if len(frames) < 2:
        return {"name": name, "t0": t0, "t1": t1, "frames": len(frames)}
    keys = [k for k in (_frames(video, t, t + 0.05, 20, 1280, 720)[:1] for t in np.linspace(t0 + 0.1, t1 - 0.1, 6)) if len(k)]
    keys = np.concatenate(keys) if keys else frames[:1]
    avg = lambda fn: {k: (round(float(np.mean(v)), 4) if v else None)  # noqa: E731
                      for k, v in _collect([fn(f) for f in keys]).items()}
    sig = {"name": name, "t0": round(t0, 3), "t1": round(t1, 3), "motion": motion(frames), "linework": avg(linework),
           "finish": avg(finish), "colour": avg(colour)}
    sig["linework"]["line_px"] = int(sig["linework"]["line_px"])
    sig["hints"] = hints(sig)
    if out_dir:
        out_dir.mkdir(parents=True, exist_ok=True)
        _sheet(frames, out_dir / f"{name}-keys.jpg")
        _sheet(frames, out_dir / f"{name}-flow.jpg", flows=True)
        if sig["motion"].get("track"):
            _chart(sig["motion"]["track"], FPS, out_dir / f"{name}-track.png")
    return sig


def _chart(track, fps, path):
    """The frame-by-frame track as a chart: pan x (blue), pan y (green), zoom (orange), roll (red) about zero."""
    import cv2
    w, h = max(240, 8 * len(track)), 220
    img = np.full((h, w, 3), 18, np.uint8)
    cv2.line(img, (0, h // 2), (w, h // 2), (70, 70, 70), 1)
    for k in range(0, len(track), int(fps)):
        cv2.line(img, (k * w // max(1, len(track)), 0), (k * w // max(1, len(track)), h), (40, 40, 40), 1)
    scales = [(0, 1200.0, (255, 160, 60)), (1, 1200.0, (90, 220, 90)), (2, 60.0, (40, 150, 255)), (3, 30.0, (60, 60, 255))]
    for j, s_, col in scales:
        pts = [(k * w // max(1, len(track)), int(h / 2 - (v[j] / s_) * (h / 2 - 6))) for k, v in enumerate(track) if v]
        for a, b in zip(pts, pts[1:]):
            cv2.line(img, a, b, col, 1, cv2.LINE_AA)
    cv2.imwrite(str(path), img)


def _collect(dicts):
    out = {}
    for d in dicts:
        for k, v in d.items():
            out.setdefault(k, [])
            if v is not None:
                out[k].append(v)
    return out


def dossier(video, shots=None, out=None, every=None) -> dict:
    """Every shot of a video read: [[t0, t1, name], ...], or the video's own cuts, or windows of `every` s."""
    from ..check.compare import windows
    out = Path(out) if out else None
    rows = [read_shot(video, a, b, out, n.replace(".", "_")) for a, b, n in windows(video, shots, every)]
    res = {"video": str(video), "shots": rows}
    if out:
        (out / "dossier.json").write_text(json.dumps(res, indent=1))
        (out / "DOSSIER.md").write_text(report(res))
    return res


KINDS = {"a line-heavy": "line-heavy", "hatching": "hatching", "a camera moving through": "3d camera",
         "the picture turns": "spin", "the camera rolls": "roll", "push in": "push in", "pull out": "pull out", "pan ": "pan",
         "motion comes in surges": "surges", "bright light blooms": "bloom", "a colour fringe": "fringe"}


def pooled(shots: list[dict]) -> dict:
    """Across a video's shots: how many need each technique, and the medians of finish and colour."""
    rows = [s for s in shots if "motion" in s]
    if not rows:
        return {}
    kinds = {v: 0 for v in KINDS.values()}
    for s in rows:
        for h in s["hints"]:
            for pre, k in KINDS.items():
                if h.startswith(pre):
                    kinds[k] += 1
    med = lambda sec, k: (round(float(np.median(v)), 3) if (v := [s[sec][k] for s in rows if s[sec].get(k) is not None]) else None)  # noqa: E731
    return {"shots": len(rows), "techniques": {k: round(n / len(rows), 2) for k, n in kinds.items()},
            "speed": round(float(np.median([s["motion"].get("speed", 0) for s in rows])), 1),
            "linework": {k: med("linework", k) for k in ("lines", "width", "hatched", "orientations", "freq")},
            "finish": {k: med("finish", k) for k in ("glow", "fringe", "grain")},
            "colour": {k: med("colour", k) for k in ("luma", "highlights", "saturated")}}


def pooled_lines(p: dict) -> list[str]:
    if not p:
        return []
    t = p["techniques"]
    order = sorted(t, key=lambda k: -t[k])
    return [f"{p['shots']} shots read as code (`moodreel dossier`; each shot's keyframes, flow arrows and track in evidence/).",
            "Techniques, share of shots: " + ", ".join(f"{k} {t[k]:.0%}" for k in order if t[k] > 0) + ".",
            f"Median speed {p['speed']} px/s at 1920 wide. Linework: {p['linework']['lines']} of the frame is line, "
            f"{p['linework']['width']} px wide, {p['linework']['hatched']} hatched. Finish: glow {p['finish']['glow']}, "
            f"fringe {p['finish']['fringe']} px, grain {p['finish']['grain']}. Colour: luma {p['colour']['luma']}, "
            f"highlights {p['colour']['highlights']}, saturated {p['colour']['saturated']} (match these: drawings made from "
            "stills ran darker and more saturated, with less line and glow, than their references)."]


def report(res: dict) -> str:
    lines = [f"# Shot dossier: {Path(res['video']).name}", "",
             "Each shot as its code would have to be written: motion, linework, finish, colour, and what to build.", ""]
    for s in res["shots"]:
        if "motion" not in s:
            continue
        m, lw, fn, c = s["motion"], s["linework"], s["finish"], s["colour"]
        lines += [f"## {s['name']} ({s['t0']}-{s['t1']} s)", "",
                  f"![keys]({s['name']}-keys.jpg)", f"![flow]({s['name']}-flow.jpg)",
                  *([f"![track: pan x blue, pan y green, zoom orange, roll red]({s['name']}-track.png)"] if m.get("track") else []), "",
                  f"- motion: speed {m.get('speed')} px/s"
                  + (f", pan {m['pan']}, zoom {m['zoom']} %/s, roll {m['roll']} deg/s, spin {m['spin']} deg/s, "
                     f"surges {m['surges']}, perspective {m['perspective']}" if m.get("moving") else ", still"),
                  f"- linework: {lw['lines']} of the frame, {lw['width']} px wide, hatched {lw['hatched']}, "
                  f"{lw['orientations']} bits of orientation, frequency {lw['freq']}, {lw['line_px']:,} px of line",
                  f"- finish: glow {fn['glow']}, fringe {fn['fringe']} px, grain {fn['grain']}; colour: luma {c['luma']}, "
                  f"highlights {c['highlights']}, saturated {c['saturated']}", ""]
        lines += [f"  - {h}" for h in s["hints"]] + [""]
    return "\n".join(lines)
