"""`moodreel pose <image>`: the 3D camera, read from a rectangle in the picture.

A flat rectangle seen in perspective (a tray, a page, a screen, a floor tile, a card) fixes the camera that sees it:
its two pairs of edges meet at two vanishing points, whose positions give the focal length (with the principal point
at the frame's centre), and the four corners then give the camera's rotation and distance (OpenCV's solvePnP on a
rectangle of the given aspect). So a camera written by eye ("looking down at about 40 degrees") becomes numbers:

  pitch   degrees the camera looks down onto the rectangle's plane (90: straight down onto it, 0: edge-on)
  yaw     degrees the rectangle is turned about the plane's normal, as seen
  roll    degrees the horizon tilts on screen
  dist    the camera's distance from the rectangle's centre, in rectangle heights
  fov     the vertical field of view, degrees: measured from the vanishing points, or the one given (a film's camera
          keeps its lens: read it once from the clearest frame, then give it for the rest)

Corners can be given (x,y in image px, in order round the rectangle) or found: `candidates()` lists the convex
quadrilaterals of the picture's edges, biggest first.
"""
from __future__ import annotations

import numpy as np


def _vp(p, q, r, s):
    """Where the line p-q meets the line r-s (homogeneous)."""
    a, b = np.cross([*p, 1], [*q, 1]), np.cross([*r, 1], [*s, 1])
    return np.cross(a, b)


def pose(corners, w: int, h: int, aspect: float | None = 1.0, fov: float | None = None) -> dict:
    """Camera from four corners (in order round the rectangle, image px) of a rectangle `aspect` wide per unit tall;
    aspect None: solve it too (it needs the vanishing points, so a rectangle seen at a slant both ways)."""
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
    if not measured:                              # a film's camera keeps its lens: give the field of view when known
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
            "rvec": [round(float(x), 5) for x in rvec.ravel()], "tvec": [round(float(x), 5) for x in tvec.ravel()]}


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


def run(image, points=None, aspect=1.0, fov=None) -> dict:
    import cv2
    img = cv2.imread(str(image))
    h, w = img.shape[:2]
    quads = [points] if points else candidates(img)
    return {"image": str(image), "size": [w, h], "aspect": aspect,
            "poses": [{"corners": q, **pose(q, w, h, aspect, fov)} for q in quads]}


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
                   f"{p['aspect']}, reprojection {p['reprojection_px']} px")
    return "\n".join(out)
