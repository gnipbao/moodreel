"""Type: where text lines are, how tall they are relative to the frame, and how heavy their strokes are.

Reading the words and naming the typeface class is the director's job (it reads the crops this writes);
measuring sizes and weights is ours. Lines are found by their texture: dense, short vertical edges packed in a
horizontal band.
"""
from __future__ import annotations

import cv2
import numpy as np

WORK = 1280


def _runs(ink: np.ndarray) -> int:
    """Strokes crossed by the busiest of three horizontal scans through a line: letters give many, an edge none."""
    h = ink.shape[0]
    return max(int(np.count_nonzero(np.diff((ink[int(f * h)] > 0).astype(np.int8)) == 1)) for f in (0.3, 0.5, 0.7))


def text_lines(rgb: np.ndarray, screen_px: float | None = None) -> list[dict]:
    """`screen_px`: a halftone's period at this scale (texture.json), blurred away first so its dots don't read
    as the dense strokes of a text line."""
    h0, w0 = rgb.shape[:2]
    k = min(1.0, WORK / max(h0, w0))
    img = cv2.resize(rgb, (round(w0 * k), round(h0 * k)), interpolation=cv2.INTER_AREA) if k < 1 else rgb
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    if screen_px:
        gray = cv2.GaussianBlur(gray, (0, 0), 0.6 * screen_px)
    h, w = gray.shape
    grad = cv2.morphologyEx(gray, cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8))
    _, bw = cv2.threshold(grad, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    bw = cv2.morphologyEx(bw, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (max(3, w // 90), 1)))
    n, _lab, stats, _ = cv2.connectedComponentsWithStats(bw, 8)
    out = []
    for x, y, bw_, bh, area in stats[1:]:
        if not (0.008 * h <= bh <= 0.3 * h and bw_ >= 1.2 * bh and area >= 0.35 * bw_ * bh):
            continue
        crop = gray[y:y + bh, x:x + bw_]
        _, ink = cv2.threshold(crop, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
        if (ink > 0).mean() > 0.5:                       # make the strokes the foreground
            ink = 255 - ink
        if not 0.08 <= (ink > 0).mean() <= 0.6 or _runs(ink) < max(2, 0.6 * bw_ / bh):
            continue
        dist = cv2.distanceTransform((ink > 0).astype(np.uint8), cv2.DIST_L2, 3)
        ridge = dist[(dist > 0) & (dist >= cv2.dilate(dist, np.ones((3, 3))) - 1e-6)]
        stroke = float(2 * np.median(ridge)) if ridge.size else 0.0
        out.append({"box": [round(x / w, 4), round(y / h, 4), round(bw_ / w, 4), round(bh / h, 4)],
                    "height": round(bh / h, 4), "stroke_ratio": round(stroke / bh, 3),
                    "ink_share": round(float((ink > 0).mean()), 3)})
    return sorted(out, key=lambda r: -r["height"])


def weight(stroke_ratio: float) -> str:
    """Stroke over line height to a weight class, calibrated on Helvetica Neue and Avenir Next set at 300-900:
    regular and medium read 0.11-0.12, bold and demi 0.17-0.22, heavy and black 0.26."""
    return "light" if stroke_ratio < 0.075 else "regular" if stroke_ratio < 0.14 else "bold" if stroke_ratio < 0.24 else "black"


def pooled(per_image: list[list[dict]]) -> dict:
    lines = [ln for img in per_image for ln in img]
    if not lines:
        return {"lines": 0}
    hs = np.array([ln["height"] for ln in lines])
    tiers = sorted({round(float(x), 3) for x in hs})
    groups = []                                       # sizes within 20 % of each other are one tier
    for x in tiers:
        if groups and x <= groups[-1][-1] * 1.2:
            groups[-1].append(x)
        else:
            groups.append([x])
    centres = np.array([float(np.median(g)) for g in groups])
    nearest = np.abs(np.round(hs, 3)[:, None] - centres[None]).argmin(axis=1)
    tier = [{"height": round(float(c), 4), "count": int((nearest == i).sum())} for i, c in enumerate(centres)]
    tier = sorted(tier, key=lambda t: -t["height"])
    title = tier[0]["height"]
    body = max(tier, key=lambda t: t["count"])["height"]
    strokes = [ln["stroke_ratio"] for ln in lines if ln["stroke_ratio"] > 0]
    big = [ln["stroke_ratio"] for ln in lines if ln["height"] >= 0.8 * title and ln["stroke_ratio"] > 0]
    return {"lines": len(lines), "tiers": tier, "title_height": title, "body_height": body,
            "title_to_body": round(title / body, 2) if body else None,
            "weight_title": weight(float(np.median(big))) if big else None,
            "weight_overall": weight(float(np.median(strokes))) if strokes else None}


def crops_sheet(rgb_list: list[np.ndarray], per_image: list[list[dict]], path, per=4, width=480):
    """The biggest lines of each picture, stacked, for the director to read."""
    rows = []
    for rgb, lines in zip(rgb_list, per_image):
        h, w = rgb.shape[:2]
        for ln in lines[:per]:
            x, y, bw, bh = ln["box"]
            pad = 0.2 * bh
            crop = rgb[max(0, int((y - pad) * h)):int((y + bh + pad) * h), max(0, int(x * w)):int((x + bw) * w)]
            if crop.size == 0:
                continue
            k = width / crop.shape[1]
            rows.append(cv2.resize(crop, (width, max(8, round(crop.shape[0] * k))), interpolation=cv2.INTER_AREA))
    if rows:
        cv2.imwrite(str(path), cv2.cvtColor(np.vstack(rows), cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 88])
    return bool(rows)
