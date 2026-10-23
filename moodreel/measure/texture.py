"""Surface: grain, paper mottle, vignette, halftone screens, scanlines and how crisp the edges are.

All of it is measured on a picture scaled to a long edge of WORK px, so numbers compare across references of
different sizes. Grain and mottle are read only where the picture has no structure of its own (flat areas), so a
busy illustration doesn't count as noise.
"""
from __future__ import annotations

import cv2
import numpy as np

from . import brush, pixel

from .color import delta_e, rgb_to_lab

WORK = 1280
HALFTONE_LEVELS = 4.0    # a printed screen swings by tens of grey levels; codec blocks by under one
SCANLINE_LEVELS = 2.0


def _work(rgb):
    h, w = rgb.shape[:2]
    k = WORK / max(h, w)
    return cv2.resize(rgb, (round(w * k), round(h * k)), interpolation=cv2.INTER_AREA) if k < 1 else rgb


def _local_std(img, k):
    m = cv2.boxFilter(img, -1, (k, k))
    return np.sqrt(np.maximum(cv2.boxFilter(img * img, -1, (k, k)) - m * m, 0))


def _peak(power, rmin, rmax):
    """Strongest peak of a centred power spectrum in a ring, against the ring's median."""
    h, w = power.shape
    yy, xx = np.mgrid[:h, :w]
    r = np.hypot(yy - h / 2, xx - w / 2)
    ring = (r >= rmin) & (r <= rmax)
    if not ring.any():
        return 0.0, 0.0, 0.0
    vals = power[ring]
    i = int(np.argmax(vals))
    py, px = yy[ring][i], xx[ring][i]
    return float(vals[i] / (np.median(vals) + 1e-9)), float(r[py, px]), float(np.degrees(np.arctan2(py - h / 2, px - w / 2)) % 180)


def _ring_max(power, rad):
    h, w = power.shape
    yy, xx = np.mgrid[:h, :w]
    return power[np.abs(np.hypot(yy - h / 2, xx - w / 2) - rad) < 0.5].max()


def texture(rgb: np.ndarray, ground_hex: str | None = None) -> dict:
    art = pixel.read(rgb)                                 # at the picture's own size: resizing smears the cells
    img = _work(rgb)
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY).astype(np.float32)
    h, w = gray.shape
    smooth = cv2.GaussianBlur(gray, (0, 0), 2)
    hp = gray - smooth
    flat = _local_std(smooth, 15) < 2.5
    flat_share = float(flat.mean())
    out = {"work_size": [w, h], "flat_share": round(flat_share, 3)}

    # the ground, loosely (a vignette darkens it towards the corners) and tightly (a pale tint or screen next to
    # it is not ground)
    ground = tight = flat
    if ground_hex:
        g = rgb_to_lab(np.array([int(ground_hex[i:i + 2], 16) for i in (1, 3, 5)], np.float64))
        de = delta_e(rgb_to_lab(cv2.resize(img, (w // 4, h // 4), interpolation=cv2.INTER_AREA).astype(np.float64)), g)
        up = lambda m: cv2.resize(m.astype(np.uint8), (w, h), interpolation=cv2.INTER_NEAREST).astype(bool) & flat  # noqa: E731
        ground, tight = up(de < 12), up(de < 6)

    # grain: fine noise read on the ground, where the kit's grain() is calibrated (overlay grain is stronger on
    # mid-tones than on a light or dark ground), else on any flat area
    where = tight if tight.mean() > 0.03 else flat
    out["grain"] = round(float(hp[where].std()), 2) if where.mean() > 0.03 else None
    yy, xx = np.mgrid[:h, :w]
    r2 = ((xx - w / 2) / (w / 2)) ** 2 + ((yy - h / 2) / (h / 2)) ** 2      # 0 at the centre, 2 in the corners
    if ground.mean() > 0.05:
        blur = cv2.GaussianBlur(gray, (0, 0), 8)

        def fit(m):
            A = np.stack([np.ones(m.sum()), r2[m]], 1)
            return A, np.linalg.lstsq(A, blur[m], rcond=None)[0]

        A, (a, b) = fit(ground)
        # a vignette darkens every corner: read the loss in each quadrant that shows enough ground and keep the
        # smallest, so a band of tint along one edge isn't one. Grey levels lost at a corner
        top, left = yy < h / 2, xx < w / 2
        quads = [m for m in (top & left, top & ~left, ~top & left, ~top & ~left) if (ground & m).mean() > 0.01]
        lost = min(float(-2 * fit(ground & m)[1][1]) for m in quads) if len(quads) >= 2 else None
        # on a dark ground a level or two of unevenness is a large share of very little light: under 3 levels
        # there is no vignette to reproduce
        out["vignette"] = None if lost is None else round(lost / max(a, 1e-6), 3) if lost >= 3 else 0.0
        out["vignette_levels"] = None if lost is None else round(lost, 1)
        # mottle: slow variation of the ground once a vignette is taken out, on the ground proper
        resid = blur - (a + b * r2)
        out["mottle"] = round(float(resid[tight if (tight & ground).mean() > 0.03 else ground].std()), 2)
    else:
        out["vignette"], out["mottle"] = None, None

    # periodic screens. Judged by amplitude in grey levels, not by how sharp the spectral peak is: codec blocks
    # (4 and 8 px) and the harmonics of a thin-line grid make sharp peaks too, but well under one level
    n = 256
    crops = [hp[y:y + n, x:x + n] for y in range(0, h - n + 1, n) for x in range(0, w - n + 1, n)]
    crops = [c for c in crops if c.std() > 1.0]
    out["halftone"] = None
    if crops:
        win = np.outer(np.hanning(n), np.hanning(n))
        power = np.mean([np.abs(np.fft.fftshift(np.fft.fft2(c * win))) ** 2 for c in crops], axis=0)
        ratio, rad, ang = _peak(power, 8, n / 2.2)
        amp = 8 * float(np.sqrt(power.max() if rad == 0 else _ring_max(power, rad))) / n ** 2
        if amp >= HALFTONE_LEVELS:
            out["halftone"] = {"amplitude": round(amp, 1), "period_px": round(n / rad, 2), "angle": round(ang, 1)}
    rows, cols = hp.mean(axis=1), hp.mean(axis=0)

    def line_amp(sig):
        spec = np.abs(np.fft.rfft(sig - sig.mean())) ** 2
        lo, hi = len(sig) // 8, len(sig) // 2            # periods of 2 to 8 px
        k = lo + int(np.argmax(spec[lo:hi]))
        return 2 * float(np.sqrt(spec[k])) / len(sig), len(sig) / k
    ra, rp = line_amp(rows)
    ca, _ = line_amp(cols)
    out["scanlines"] = ({"amplitude": round(ra, 2), "period_px": round(rp, 2)}
                        if ra >= SCANLINE_LEVELS and ca < 0.3 * ra else None)
    # rows of scanlines are a periodic screen too, along one axis: the same period is the scanlines, not dots
    if out["scanlines"] and out["halftone"] and abs(out["halftone"]["period_px"] / rp - 1) < 0.15:
        out["halftone"] = None

    # edges: how much of an edge's contrast is crossed in one pixel (1 = a vector edge, lower = soft or brushy)
    edges = cv2.Canny(cv2.GaussianBlur(gray, (3, 3), 0).astype(np.uint8), 40, 100) > 0
    if edges.sum() > 50:
        gx, gy = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3) / 8, cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3) / 8
        grad = np.hypot(gx, gy)
        span = cv2.dilate(gray, np.ones((5, 5))) - cv2.erode(gray, np.ones((5, 5)))
        sharp = grad[edges] / np.maximum(span[edges], 1)
        out["edge_sharpness"] = round(float(np.median(sharp)), 3)
        out["edge_density"] = round(float(edges.mean()), 4)
    else:
        out["edge_sharpness"], out["edge_density"] = None, 0.0
    marks = None if art else brush.read(img)
    if marks:
        out["brush"] = marks
    if art:
        out["pixel"] = {**art, "picture_width": int(rgb.shape[1])}
        # a pixel picture's dither and cell edges read as grain, a screen or scanlines: they are the pixel art
        for k in ("grain", "halftone", "scanlines"):
            out[k] = None
        out["note"] = "pixel art: grain, halftone and scanlines not read (the dither and the cells would pass for them)"
    out["summary"] = summarise(out)
    return out


def summarise(t: dict) -> dict:
    """Words for the numbers, with the thresholds in the open."""
    g = t.get("grain")
    s = {"grain": None if g is None else "none" if g < 0.8 else "fine" if g < 2.5 else "visible" if g < 6 else "heavy"}
    v = t.get("vignette")
    s["vignette"] = None if v is None else "none" if v < 0.04 else "soft" if v < 0.15 else "strong"
    m = t.get("mottle")
    s["mottle"] = None if m is None else "none" if m < 0.8 else "paper" if m < 3 else "blotchy"
    e = t.get("edge_sharpness")
    s["edges"] = None if e is None else "crisp" if e >= 0.32 else "soft" if e >= 0.2 else "blurred"
    s["halftone"] = bool(t.get("halftone"))
    s["scanlines"] = bool(t.get("scanlines"))
    s["pixel"] = bool(t.get("pixel"))
    s["brush"] = bool(t.get("brush"))
    return s


def pooled(textures: list[dict]) -> dict:
    """Median of each number over the references, and the words for it."""
    keys = ["grain", "vignette", "mottle", "edge_sharpness", "edge_density", "flat_share"]
    out = {}
    for k in keys:
        vals = [t[k] for t in textures if t.get(k) is not None]
        out[k] = round(float(np.median(vals)), 3) if vals else None
        out[f"{k}_range"] = [round(float(min(vals)), 3), round(float(max(vals)), 3)] if vals else None
    hts = [t["halftone"] for t in textures if t.get("halftone")]
    out["halftone"] = ({"share": round(len(hts) / len(textures), 2),
                        "period_px": round(float(np.median([x["period_px"] for x in hts])), 2),
                        "angle": round(float(np.median([x["angle"] for x in hts])), 1)} if hts else None)
    sls = [t["scanlines"] for t in textures if t.get("scanlines")]
    out["scanlines"] = ({"share": round(len(sls) / len(textures), 2),
                         "period_px": round(float(np.median([x["period_px"] for x in sls])), 2)} if sls else None)
    # pixel art: the scale as a share of the picture's width (references come at different sizes), the rest as medians
    px = [t["pixel"] for t in textures if t.get("pixel")]
    out["pixel"] = ({"share": round(len(px) / len(textures), 2),
                     "scale_of_width": round(float(np.median([p["scale"] / p["picture_width"] for p in px])), 5),
                     "native_width": int(np.median([p["native"][0] for p in px])),
                     "palette_size": int(np.median([p["palette_size"] for p in px])),
                     "dither": float(np.mean([p["dither"] for p in px])) >= 0.5,
                     "dither_share": round(float(np.median([p["dither_share"] for p in px])), 3),
                     "palette": max(px, key=lambda p: p["palette_size"])["palette"]} if px else None)
    bs = [t["brush"] for t in textures if t.get("brush")]
    axial = np.radians([2 * b["direction_deg"] for b in bs])          # strokes are axial: average on doubled angles
    out["brush"] = ({"share": round(len(bs) / len(textures), 2),
                     "edge_spacing_px": round(float(np.median([b["edge_spacing_px"] for b in bs])), 1),
                     "coherence": round(float(np.median([b["coherence"] for b in bs])), 2),
                     "direction_deg": round(float(np.degrees(np.arctan2(np.sin(axial).mean(), np.cos(axial).mean())) / 2) % 180, 1),
                     "agreement": round(float(np.median([b["agreement"] for b in bs])), 2),
                     "coverage": round(float(np.median([b["coverage"] for b in bs])), 2)} if bs else None)
    out["summary"] = summarise(out)
    return out
