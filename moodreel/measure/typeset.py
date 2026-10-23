"""Type: where text lines are, how tall they are relative to the frame, and how heavy their strokes are.

Reading the words and naming the typeface class is the director's job (it reads the crops this writes);
measuring sizes and weights is ours. Lines are found by their texture: dense, short vertical edges packed in a
horizontal band.
"""
from __future__ import annotations

import cv2
import numpy as np

WORK = 1280


def descan(img: np.ndarray, period: float) -> np.ndarray:
    """Dark scanline rows filled from the lit rows around them (a vertical max over one period)."""
    n = max(2, int(round(period)))
    return cv2.dilate(img, np.ones((n, 1), np.uint8))


def _runs(ink: np.ndarray) -> int:
    """Strokes crossed by the busiest of three horizontal scans through a line: letters give many, an edge none."""
    h = ink.shape[0]
    return max(int(np.count_nonzero(np.diff((ink[int(f * h)] > 0).astype(np.int8)) == 1)) for f in (0.3, 0.5, 0.7))


def _rows(boxes: list[list[int]]) -> list[list[int]]:
    """Glyphs of big type stand further apart than the closing kernel joins: pieces sharing a band of rows, of
    similar height and a small gap apart are one line (x, y, w, h, area)."""
    lines = []
    for x, y, w, h, a in sorted(boxes):
        for L in lines:
            lh = L[3]
            same = min(L[1] + lh, y + h) - max(L[1], y) >= 0.6 * min(h, lh) and 0.6 <= h / lh <= 1.6
            if same and x - (L[0] + L[2]) <= 0.6 * max(h, lh):
                x0, y0 = min(L[0], x), min(L[1], y)
                L[:] = [x0, y0, max(L[0] + L[2], x + w) - x0, max(L[1] + lh, y + h) - y0, L[4] + a]
                break
        else:
            lines.append([x, y, w, h, a])
    return lines


def text_lines(rgb: np.ndarray, screen_px: float | None = None, scan_px: float | None = None) -> list[dict]:
    """`screen_px`: a halftone's period at this scale (texture.json), blurred away first so its dots don't read
    as the dense strokes of a text line; `scan_px`: a scanline period, filled in first."""
    h0, w0 = rgb.shape[:2]
    k = min(1.0, WORK / max(h0, w0))
    img = cv2.resize(rgb, (round(w0 * k), round(h0 * k)), interpolation=cv2.INTER_AREA) if k < 1 else rgb
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    if screen_px:
        gray = cv2.GaussianBlur(gray, (0, 0), 0.6 * screen_px)
    if scan_px:                                          # scanlines cut strokes into stripes: fill them back in
        gray = descan(gray, scan_px)
    h, w = gray.shape
    grad = cv2.morphologyEx(gray, cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8))
    _, bw = cv2.threshold(grad, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    bw = cv2.morphologyEx(bw, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (max(3, w // 90), 1)))
    n, _lab, stats, _ = cv2.connectedComponentsWithStats(bw, 8)
    out = []
    for x, y, bw_, bh, area in _rows([s for s in stats[1:].tolist() if 0.008 * h <= s[3] <= 0.3 * h]):
        # big glyphs show only their outlines in the gradient: the ink checks below do the rest
        if not (bw_ >= 1.2 * bh and area >= 0.05 * bw_ * bh):
            continue
        crop = gray[y:y + bh, x:x + bw_]
        thr, ink = cv2.threshold(crop, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
        # the strokes are the side the surroundings are not: heavy type can cover more of its box than the ground
        pad = max(2, bh // 6)
        around = gray[max(0, y - pad):y + bh + pad, max(0, x - pad):x + bw_ + pad].astype(np.int32)
        ring = np.ones(around.shape, bool)
        ring[y - max(0, y - pad):y - max(0, y - pad) + bh, x - max(0, x - pad):x - max(0, x - pad) + bw_] = False
        if (around[ring] > thr).mean() > 0.5:
            ink = 255 - ink
        if not 0.08 <= (ink > 0).mean() <= 0.7 or _runs(ink) < max(2, 0.6 * bw_ / bh):
            continue
        cover = (ink > 0).mean(axis=0)
        if np.median(cover[cover > 0]) > 0.85:           # solid blocks in a row (bars, tiles) are not glyphs
            continue
        dist = cv2.distanceTransform((ink > 0).astype(np.uint8), cv2.DIST_L2, 3)
        ridge = dist[(dist > 0) & (dist >= cv2.dilate(dist, np.ones((3, 3))) - 1e-6)]
        stroke = float(2 * np.median(ridge)) if ridge.size else 0.0
        out.append({"box": [round(x / w, 4), round(y / h, 4), round(bw_ / w, 4), round(bh / h, 4)],
                    "height": round(bh / h, 4), "stroke_ratio": round(stroke / bh, 3),
                    "ink_share": round(float((ink > 0).mean()), 3)})
    return sorted(out, key=lambda r: -r["height"])


# stroke over line height against weight, the medians over Helvetica Neue, Avenir Next and SF Pro set at 300-900 in
# lowercase, mixed case and capitals. Approximate by nature: a line without ascenders reads up to a step heavier, a
# mixed line with both ascenders and descenders, or a line of capitals in a black weight, up to a step lighter
CALIBRATION = ([0.06, 0.118, 0.2, 0.27], [300, 400, 700, 900])


def weight_value(stroke_ratio: float) -> int:
    return int(round(float(np.interp(stroke_ratio, *CALIBRATION)) / 100) * 100)


def weight(stroke_ratio: float) -> str:
    v = weight_value(stroke_ratio)
    return "light" if v < 350 else "regular" if v < 550 else "bold" if v < 800 else "black"


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
            "weight_title_value": weight_value(float(np.median(big))) if big else None,
            "weight_overall": weight(float(np.median(strokes))) if strokes else None,
            "weight_overall_value": weight_value(float(np.median(strokes))) if strokes else None}


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
