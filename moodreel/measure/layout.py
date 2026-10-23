"""Layout: where content sits on the ground. Margins, density, balance, symmetry and alignment lines."""
from __future__ import annotations

import cv2
import numpy as np

from .color import delta_e, rgb_to_lab

GRID = 256          # analysis long edge


def content_mask(rgb: np.ndarray, ground_hex: str) -> np.ndarray:
    h, w = rgb.shape[:2]
    k = GRID / max(h, w)
    small = cv2.resize(rgb, (max(1, round(w * k)), max(1, round(h * k))), interpolation=cv2.INTER_AREA)
    g = rgb_to_lab(np.array([int(ground_hex[i:i + 2], 16) for i in (1, 3, 5)], np.float64))
    mask = (delta_e(rgb_to_lab(small.astype(np.float64)), g) > 12).astype(np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
    return cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8)) > 0


def _clusters(xs, tol):
    xs = sorted(xs)
    groups, cur = [], [xs[0]] if xs else []
    for x in xs[1:]:
        if x - cur[-1] <= tol:
            cur.append(x)
        else:
            groups.append(cur)
            cur = [x]
    if cur:
        groups.append(cur)
    return [g for g in groups if len(g) >= 2]


def layout(rgb: np.ndarray, ground_hex: str) -> dict:
    m = content_mask(rgb, ground_hex)
    h, w = m.shape
    out = {"density": round(float(m.mean()), 3)}
    if m.sum() < 10:
        return {**out, "empty": True}
    ys, xs = np.nonzero(m)
    out["margins"] = {"left": round(xs.min() / w, 3), "right": round(1 - (xs.max() + 1) / w, 3),
                      "top": round(ys.min() / h, 3), "bottom": round(1 - (ys.max() + 1) / h, 3)}
    out["centroid"] = [round(float(xs.mean() / w), 3), round(float(ys.mean() / h), 3)]
    out["symmetry"] = round(float((m & m[:, ::-1]).sum() / max(1, (m | m[:, ::-1]).sum())), 3)
    n, _lab, stats, _ = cv2.connectedComponentsWithStats(m.astype(np.uint8), 8)
    boxes = [s for s in stats[1:] if s[4] >= 0.001 * h * w]
    out["blocks"] = len(boxes)
    tol = 0.015 * w
    lines = {"left": _clusters([b[0] for b in boxes], tol), "centre": _clusters([b[0] + b[2] / 2 for b in boxes], tol),
             "right": _clusters([b[0] + b[2] for b in boxes], tol)}
    out["alignment"] = {k: sum(len(g) for g in v) for k, v in lines.items()}
    out["dominant_alignment"] = max(out["alignment"], key=out["alignment"].get) if any(out["alignment"].values()) else None
    out["columns"] = len(lines["left"])
    return out


def pooled(layouts: list[dict]) -> dict:
    ok = [x for x in layouts if not x.get("empty")]
    if not ok:
        return {}
    med = lambda f: round(float(np.median([f(x) for x in ok])), 3)  # noqa: E731
    al = [x["dominant_alignment"] for x in ok if x.get("dominant_alignment")]
    return {"density": med(lambda x: x["density"]),
            "margins": {k: med(lambda x, k=k: x["margins"][k]) for k in ("left", "right", "top", "bottom")},
            "min_margin": med(lambda x: min(x["margins"].values())),
            "centroid": [med(lambda x: x["centroid"][0]), med(lambda x: x["centroid"][1])],
            "symmetry": med(lambda x: x["symmetry"]), "blocks": med(lambda x: x["blocks"]),
            "dominant_alignment": max(set(al), key=al.count) if al else None,
            "columns": med(lambda x: x["columns"])}
