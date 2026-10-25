"""`moodreel pose <image>`: the 3D camera, read from a rectangle in the picture.

A flat rectangle seen in perspective (a tray, a page, a screen, a floor tile, a card) fixes the camera that sees it:
its two pairs of edges meet at two vanishing points, whose positions give the focal length (with the principal point
at the frame's centre), and the four corners then give the camera's rotation and distance (OpenCV's solvePnP on a
rectangle of the given aspect). So a camera written by eye ("looking down at about 40 degrees") becomes numbers:

  pitch   degrees the camera looks down onto the rectangle's plane (90: straight down onto it, 0: edge-on)
  yaw     degrees the rectangle is turned about the plane's normal, as seen
  roll    degrees the horizon tilts on screen
  dist    the camera's distance from the rectangle's centre, in rectangle heights
  fov     the vertical field of view, degrees: measured from the vanishing points, or the one given (a camera that
          keeps its lens: read it once from the clearest frame, then give it), or fov="shape": solved from the
          rectangle's known aspect, frame by frame (a lens that changes: a zoom, a dolly zoom)

Corners can be given (x,y in image px, in order round the rectangle) or found: `candidates()` lists the convex
quadrilaterals of the picture's edges, biggest first.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np


def _vp(p, q, r, s):
    """Where the line p-q meets the line r-s (homogeneous)."""
    a, b = np.cross([*p, 1], [*q, 1]), np.cross([*r, 1], [*s, 1])
    return np.cross(a, b)


# the rectangle's own frame (x along its first edge, y along its fourth, z = x cross y) to the world's, Y up: a wall's y
# runs down it and its z into it; a floor's z points down into it and its y toward the viewer
WORLD = {"wall": np.array([[1, 0, 0], [0, -1, 0], [0, 0, -1.0]]), "floor": np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0.0]])}


def world(rvec, tvec, up: str = "wall") -> dict:
    """The camera in the world of the rectangle (centred on it, in rectangle heights, Y up): position, forward and up
    vectors, and its pitch (degrees above the horizon, negative looking down), yaw (degrees, 0 looking along -Z, at a
    wall's face, + turning toward +X) and roll (degrees, the angle three.js's camera.rotateZ would turn it by)."""
    import cv2
    R, _ = cv2.Rodrigues(np.asarray(rvec, float))
    Wm = WORLD[up]
    pos = Wm @ (-R.T @ np.asarray(tvec, float).ravel())
    fwd, down, right = Wm @ R.T[:, 2], Wm @ R.T[:, 1], Wm @ R.T[:, 0]
    upv = -down
    pitch = float(np.degrees(np.arcsin(np.clip(fwd[1], -1, 1))))
    yaw = float(np.degrees(np.arctan2(fwd[0], -fwd[2])))
    roll = float(np.degrees(np.arctan2(right[1], upv[1])))
    return {"position": [round(float(x), 4) for x in pos], "forward": [round(float(x), 5) for x in fwd],
            "up": [round(float(x), 5) for x in upv], "cam_pitch": round(pitch, 2), "cam_yaw": round(yaw, 2), "cam_roll": round(roll, 2)}


def pose(corners, w: int, h: int, aspect: float | None = 1.0, fov: float | None = None, up: str | None = None) -> dict:
    """Camera from four corners (in order round the rectangle, image px) of a rectangle `aspect` wide per unit tall;
    aspect None: solve it too (it needs the vanishing points, so a rectangle seen at a slant both ways). `up`, "wall"
    or "floor": which way the rectangle stands, so the camera is also given in the world (see `world`)."""
    import cv2
    P = np.asarray(corners, np.float64).reshape(4, 2)
    c = np.array([w / 2, h / 2])
    f = None
    if fov is None:                               # the focal length from the two vanishing points
        v1, v2 = _vp(P[0], P[1], P[3], P[2]), _vp(P[0], P[3], P[1], P[2])
        if abs(v1[2]) > 1e-9 and abs(v2[2]) > 1e-9:
            a, b = v1[:2] / v1[2] - c, v2[:2] / v2[2] - c
            ff = -float(np.dot(a, b))
            if ff > 0:
                f = float(np.sqrt(ff))
    measured = f is not None and 0.3 * h < f < 20 * h
    if fov == "shape" and aspect:                 # the lens from the rectangle's known shape: the focal length at which
        best = None                               # it comes out `aspect` wide (needs no second vanishing point)
        Hs = cv2.getPerspectiveTransform(np.float32([[0, 0], [1, 0], [1, 1], [0, 1]]), np.float32(P))
        for deg in np.arange(8, 100, 0.25):
            ff = (h / 2) / np.tan(np.radians(deg) / 2)
            B = np.linalg.inv(np.array([[ff, 0, c[0]], [0, ff, c[1]], [0, 0, 1]])) @ Hs
            e = abs(np.log(np.linalg.norm(B[:, 0]) / np.linalg.norm(B[:, 1]) / aspect))
            if best is None or e < best[0]:
                best = (e, ff)
        f, measured = best[1], True
    elif not measured:                            # a film's camera keeps its lens: give the field of view when known
        f = (h / 2) / np.tan(np.radians(fov or 35.0) / 2)
    K = np.array([[f, 0, c[0]], [0, f, c[1]], [0, 0, 1]])
    if aspect is None:                            # the rectangle's own shape: its two sides' lengths seen through K
        Hs = cv2.getPerspectiveTransform(np.float32([[0, 0], [1, 0], [1, 1], [0, 1]]), np.float32(P))
        B = np.linalg.inv(K) @ Hs
        aspect = float(np.linalg.norm(B[:, 0]) / np.linalg.norm(B[:, 1])) if measured else 1.0
    obj = np.array([[-aspect / 2, -0.5, 0], [aspect / 2, -0.5, 0], [aspect / 2, 0.5, 0], [-aspect / 2, 0.5, 0]], np.float64)
    ok, rvec, tvec = cv2.solvePnP(obj, P, K, None, flags=cv2.SOLVEPNP_IPPE)
    if not ok:
        return {"ok": False}
    R, _ = cv2.Rodrigues(rvec)
    n = R[:, 2]                                   # the plane's normal, in camera coordinates (camera looks down +z)
    view = np.array([0, 0, 1.0])
    pitch = float(np.degrees(np.arcsin(min(1.0, abs(float(np.dot(n, view)))))))
    roll = float(np.degrees(np.arctan2(R[1, 0], R[0, 0])))
    yaw = float(np.degrees(np.arctan2(-R[2, 0], np.hypot(R[2, 1], R[2, 2]))))
    proj, _ = cv2.projectPoints(obj, rvec, tvec, K, None)
    err = float(np.abs(proj.reshape(4, 2) - P).max())
    return {"ok": True, "aspect": round(float(aspect), 3), "pitch": round(pitch, 1), "yaw": round(yaw, 1), "roll": round(roll, 1),
            "dist": round(float(np.linalg.norm(tvec)), 3), "fov": round(float(np.degrees(2 * np.arctan((h / 2) / f))), 1),
            "fov_measured": measured, "reprojection_px": round(err, 2),
            "rvec": [round(float(x), 5) for x in rvec.ravel()], "tvec": [round(float(x), 5) for x in tvec.ravel()],
            **(world(rvec, tvec, up) if up else {})}


def _video_frames(video, t0, t1, width=1280):
    import subprocess
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height,r_frame_rate",
                          "-of", "csv=p=0", str(video)], capture_output=True, text=True, check=True).stdout.strip().split(",")
    vw, vh = int(out[0]), int(out[1])
    a, b = (out[2].split("/") + ["1"])[:2]
    fps = float(a) / float(b)
    w = min(width, vw)
    h = int(round(vh * w / vw / 2)) * 2
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{max(0.0, t0):.4f}", "-i", str(video), "-t", f"{t1 - t0:.4f}", "-vf",
                          f"scale={w}:{h}", "-pix_fmt", "gray", "-f", "rawvideo", "-"], capture_output=True, check=True).stdout
    n = len(raw) // (w * h)
    return np.frombuffer(raw[:n * w * h], np.uint8).reshape(n, h, w), fps, w / vw


def track(video, at: float, corners, t0: float, t1: float, aspect: float = 1.0, fov: float | None = 35.0, up: str = "wall",
          smooth: int = 5) -> dict:
    """The camera through a shot, from a rectangle's four corners (video px) at time `at`: the rectangle's plane is
    followed frame by frame (points inside it tracked with forward-backward-checked optical flow, a homography fitted
    to them, the points re-seeded as they are lost) and the camera solved at every frame. Frames where the plane is
    lost are left out. `smooth`: a median over that many frames, on the camera's numbers."""
    import cv2
    frames, fps, k = _video_frames(video, t0, t1)
    n, H, W = frames.shape
    a = int(round((at - t0) * fps))
    a = min(max(a, 0), n - 1)
    quads = [None] * n
    quads[a] = np.asarray(corners, np.float32).reshape(4, 2) * k

    def seed(g, q):
        m = np.zeros_like(g)
        c = q.mean(axis=0)
        cv2.fillConvexPoly(m, ((q - c) * 0.94 + c).astype(np.int32), 255)
        p = cv2.goodFeaturesToTrack(g, 500, 0.005, 5, mask=m)
        return None if p is None else p.reshape(-1, 2).astype(np.float32)

    lk = {"winSize": (21, 21), "maxLevel": 3, "criteria": (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, 0.01)}
    for step in (1, -1):
        q, pts, since = quads[a].copy(), seed(frames[a], quads[a]), 0
        i = a
        while 0 <= i + step < n and pts is not None and len(pts) >= 12:
            j = i + step
            nxt, st, _ = cv2.calcOpticalFlowPyrLK(frames[i], frames[j], pts, None, **lk)
            back, st2, _ = cv2.calcOpticalFlowPyrLK(frames[j], frames[i], nxt, None, **lk)
            good = (st.ravel() == 1) & (st2.ravel() == 1) & (np.linalg.norm(back - pts, axis=1) < 1.0)
            if good.sum() < 12:
                break
            Hm, inl = cv2.findHomography(pts[good], nxt[good], cv2.RANSAC, 2.0)
            if Hm is None:
                break
            q = cv2.perspectiveTransform(q.reshape(-1, 1, 2), Hm).reshape(4, 2)
            area = cv2.contourArea(q.astype(np.float32))
            if not np.isfinite(q).all() or area < 0.002 * W * H or area > 50 * W * H:
                break
            quads[j] = q
            pts = nxt[good][inl.ravel() == 1]
            since += 1
            if since >= 8 or len(pts) < 60:                     # re-seed inside the plane where it is now
                fresh = seed(frames[j], q)
                if fresh is not None and len(fresh) >= 12:
                    pts = fresh
                since = 0
            i = j
    rows = []
    for i, q in enumerate(quads):
        if q is None:
            continue
        p = pose(q / k, int(W / k), int(H / k), aspect, fov, up)
        if p.get("ok"):
            rows.append({"t": round(t0 + i / fps, 4), "corners": [[round(float(x), 1) for x in c] for c in q / k], **p})
    if smooth > 1 and rows:
        for key in ("cam_pitch", "cam_yaw", "cam_roll", "dist"):
            v = np.array([r[key] for r in rows])
            half = smooth // 2
            for i, r in enumerate(rows):
                r[key] = round(float(np.median(v[max(0, i - half):i + half + 1])), 2)
    return {"video": str(video), "fps": fps, "anchor": at, "aspect": aspect, "fov": fov, "up": up, "frames": rows,
            "covered": round(len(rows) / max(n, 1), 3)}


def camera_module(res: dict) -> str:
    """The track as a module a shot imports: cameraAt(t) gives position, forward and up, in rectangle heights."""
    rows = [[r["t"], *r["position"], *r["forward"], *r["up"]] for r in res["frames"]]
    return (f"// A camera read off {Path(res['video']).name} by `moodreel pose --track`: the rectangle the camera was read from is "
            "centred at the origin,\n// 1 unit tall, Y up; positions in those units.\n"
            f"export const TRACK = {json.dumps(rows)};\n"
            "export function cameraAt(t) {\n"
            "  let i = TRACK.findIndex(r => r[0] > t);\n"
            "  if (i <= 0) i = i === 0 ? 1 : TRACK.length - 1;\n"
            "  const a = TRACK[i - 1], b = TRACK[i], u = Math.min(1, Math.max(0, (t - a[0]) / (b[0] - a[0] || 1)));\n"
            "  const v = a.map((x, k) => x + (b[k] - x) * u);\n"
            "  return { position: v.slice(1, 4), forward: v.slice(4, 7), up: v.slice(7, 10) };\n}\n")


def candidates(img, n: int = 6, min_area: float = 0.01) -> list[list[list[int]]]:
    """The biggest convex quadrilaterals among the picture's edges, each [[x, y] x 4] in order round it."""
    import cv2
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY) if img.ndim == 3 else img
    edges = cv2.dilate(cv2.Canny(g, 30, 90), np.ones((3, 3), np.uint8))
    cs, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    out = []
    for cnt in sorted(cs, key=cv2.contourArea, reverse=True):
        if cv2.contourArea(cnt) < min_area * g.size:
            break
        hull = cv2.convexHull(cnt)
        q = cv2.approxPolyDP(hull, 0.03 * cv2.arcLength(hull, True), True)
        if len(q) == 4:
            pts = q.reshape(4, 2).tolist()
            if all(np.abs(np.array(pts) - np.array(o)).max() > 6 for o in out):
                out.append(pts)
        if len(out) >= n:
            break
    return out


def run(image, points=None, aspect=1.0, fov=None, up=None) -> dict:
    import cv2
    img = cv2.imread(str(image))
    h, w = img.shape[:2]
    quads = [points] if points else candidates(img)
    return {"image": str(image), "size": [w, h], "aspect": aspect,
            "poses": [{"corners": q, **pose(q, w, h, aspect, fov, up)} for q in quads]}


def grid(image, out, step: int = 50):
    """The image with a labelled grid every `step` px, for reading coordinates off it by eye."""
    import cv2
    img = cv2.imread(str(image))
    h, w = img.shape[:2]
    for x in range(0, w, step):
        cv2.line(img, (x, 0), (x, h), (0, 200, 255) if x % (step * 4) == 0 else (0, 90, 120), 1)
        if x % (step * 2) == 0:
            cv2.putText(img, str(x), (x + 2, 12), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 220, 255), 1, cv2.LINE_AA)
    for y in range(0, h, step):
        cv2.line(img, (0, y), (w, y), (0, 200, 255) if y % (step * 4) == 0 else (0, 90, 120), 1)
        if y % (step * 2) == 0:
            cv2.putText(img, str(y), (2, y - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 220, 255), 1, cv2.LINE_AA)
    cv2.imwrite(str(out), img)
    return out


def parse_points(s: str):
    v = [float(x) for x in s.replace(";", ",").split(",")]
    if len(v) != 8:
        raise SystemExit("--points takes four corners: x1,y1,x2,y2,x3,y3,x4,y4 in order round the rectangle")
    return [v[i:i + 2] for i in range(0, 8, 2)]


def report(res: dict) -> str:
    out = [f"{res['image']} ({res['size'][0]} x {res['size'][1]})"]
    for p in res["poses"]:
        if not p.get("ok"):
            out.append(f"  {p['corners']}: no pose")
            continue
        out.append(f"  corners {p['corners']}: pitch {p['pitch']} deg, yaw {p['yaw']}, roll {p['roll']}, distance {p['dist']} "
                   f"(rectangle heights), fov {p['fov']} deg ({'measured' if p['fov_measured'] else 'given'}), aspect "
                   f"{p['aspect']}, reprojection {p['reprojection_px']} px"
                   + (f"; in the world: pitch {p['cam_pitch']}, yaw {p['cam_yaw']}, roll {p['cam_roll']}, at {p['position']}"
                      if "cam_pitch" in p else ""))
    return "\n".join(out)
