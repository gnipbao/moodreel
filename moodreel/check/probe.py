"""`moodreel probe <reference> --at t1,t2 [--against <remake>]`: the numbers that settle a shot, read off full-size frames.

A remake drawn from stills runs darker or brighter, sparser or busier and slower than its reference, and the eye can't
say by how much. These numbers can, and a pass that moves them toward the reference's converges in two or three tries
(a particle ring judged "not intense enough" was first redrawn at 2.8 times the reference's lit share, then matched
it on the numbers). Each is read at each time from the reference, and from the remake beside it:

  colour  mean RGB of the region
  lit     share of the region brighter than --lit (default 50 of 255), and the box that light fills (0.5-99.5 percentile)
  detail  mean |Laplacian| at 320 px wide: what `moodreel compare` counts as detail
  still   the least median change between neighbouring frames over the next four: 0 when the texture holds still
          (a fixed grain).
          A remake whose grain boils over a still reference reads as motion going another way.
  cells   the strongest period of the region's row and column profiles between 6 and 40 px, its strength (0..1) and
          its phase: where a grid of cells starts (in a GPU pass y counts from the bottom: offset by the height mod P)
  bar     the angle from vertical, length and width of the darkest shape (the brightest on a dark frame): a slash, a
          beam, a tube; read each tenth of a second, it gives a turn's curve
  type    with --region drawn round a line of type: its ink's box and height, the stroke width and their ratio. Read on
          both, it says which line is set heavier or larger: the eye calls Medium "regular" on a light card and a light
          mono "bold" once it is drawn in dots

The remake may be a video or a film folder (its frames are rendered as stills). --sheet writes the frames as a contact
sheet, the reference above the remake.
"""
from __future__ import annotations

import io
import json
import subprocess
import tempfile
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]


def frame_of(path, t: float, n: int = 1) -> list[np.ndarray]:
    """`n` consecutive RGB frames of a video from `t`, full size."""
    probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                            "-of", "csv=p=0", str(path)], capture_output=True, text=True, check=True).stdout
    w, h = (int(v) for v in probe.strip().split(",")[:2])
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.4f}", "-i", str(path), "-frames:v", str(n),
                          "-pix_fmt", "rgb24", "-f", "rawvideo", "-"], capture_output=True, check=True).stdout
    k = len(raw) // (w * h * 3)
    return list(np.frombuffer(raw[:k * w * h * 3], np.uint8).reshape(k, h, w, 3))


def stills_of(film: Path, times: list[float], size: str) -> list[np.ndarray]:
    """A film folder's frames at `times`, rendered as stills."""
    from PIL import Image
    with tempfile.TemporaryDirectory() as tmp:
        out = subprocess.run(["node", str(REPO / "render" / "render.mjs"), "still", str(film), *[f"{t:g}" for t in times],
                              "--size", size, "--out", tmp], capture_output=True, text=True, check=True).stdout
        files = [ln.strip() for ln in out.splitlines() if ln.strip().endswith(".jpg")]
        return [np.asarray(Image.open(f).convert("RGB")) for f in files]


def _period(profile: np.ndarray, lo: int = 6, hi: int = 40):
    p = profile - profile.mean()
    if len(p) < 2 * hi or not p.any():
        return None
    ac = np.correlate(p, p, "full")[len(p) - 1:]
    ac = ac / ac[0]
    k = lo + int(np.argmax(ac[lo:hi + 1]))
    phase = int(np.argmin([profile[i::k].mean() for i in range(k)]))           # the darkest offset: a gap or a line
    return {"period": k, "strength": round(float(ac[k]), 2), "phase": phase}


def _bar(g: np.ndarray):
    """The darkest (on a light frame) or brightest (on a dark one) elongated shape: angle from vertical, length, width."""
    m = g < 80 if g.mean() > 128 else g > 170
    ys, xs = np.nonzero(m)
    if len(xs) < 50:
        return None
    w, v = np.linalg.eigh(np.cov(xs, ys))
    dx, dy = v[:, 1] if v[1, 1] < 0 else -v[:, 1]                 # the long axis, pointing up the picture
    proj = (xs - xs.mean()) * dx + (ys - ys.mean()) * dy
    length = float(proj.max() - proj.min())
    return {"centre": [round(float(xs.mean())), round(float(ys.mean()))],
            "angle": round(float(np.degrees(np.arctan2(dx, -dy))), 1),    # + leans right at the top, like "/"
            "length": round(length), "width": round(len(xs) / max(length, 1), 1)}


def _type(g: np.ndarray, ink: str = "auto"):
    """The type in a region: its ink's height (top of the tallest letter to the bottom of the lowest), the stroke width
    (twice the distance to the ink's edge along its middle) and their ratio, which tells a weight from its neighbours
    (Inter at the same size: 300 0.07, 400 0.09, 500 0.10, 600 0.12, 700 0.14 of the cap-to-descender height)."""
    from scipy import ndimage
    light = g.mean() > 128 if ink == "auto" else ink == "dark"
    m = g < 0.5 * (g.min() + np.median(g)) if light else g > 0.5 * (g.max() + np.median(g))
    m = ndimage.binary_opening(m, iterations=1)
    if m.sum() < 30:
        return None
    rows = np.flatnonzero(m.sum(1) >= max(2, 0.01 * m.shape[1] * m.mean()))
    d = ndimage.distance_transform_edt(m)
    ridge = (d >= 1) & (d == ndimage.maximum_filter(d, size=3))
    stroke = float(2 * np.median(d[ridge]))
    height = int(rows.max() - rows.min() + 1)
    cols = np.flatnonzero(m.any(0))
    return {"ink": "dark" if light else "light", "height": height, "stroke": round(stroke, 1),
            "ratio": round(stroke / max(height, 1), 3), "box": [int(cols[0]), int(rows[0]), int(cols[-1]), int(rows[-1])]}


def numbers(frames: list[np.ndarray], region=None, lit: float = 50) -> dict:
    """The numbers of one moment: `frames[0]` is the frame, the rest (if any) its successors, for `still`."""
    import cv2
    f = frames[0].astype(np.float32)
    x0, y0, x1, y1 = region or (0, 0, f.shape[1], f.shape[0])
    r = f[y0:y1, x0:x1]
    g = r.mean(2)
    on = g > lit
    ys, xs = np.nonzero(on)
    small = cv2.resize(g, (320, max(1, round(320 * g.shape[0] / g.shape[1]))), interpolation=cv2.INTER_AREA)
    out = {"colour": [round(float(c), 1) for c in r.reshape(-1, 3).mean(0)],
           "lit": round(float(on.mean()) * 100, 1),
           "box": [int(np.percentile(xs, 0.5)) + x0, int(np.percentile(ys, 0.5)) + y0,
                   int(np.percentile(xs, 99.5)) + x0, int(np.percentile(ys, 99.5)) + y0] if len(xs) > 20 else None,
           "detail": round(float(np.abs(cv2.Laplacian(small, cv2.CV_32F, ksize=3)).mean()), 2),
           "cells": {"x": _period(g.mean(0)), "y": _period(g.mean(1))},
           "bar": _bar(g)}
    if region:                                                     # a region drawn round a line of type: its weight
        out["type"] = _type(g)
        if out["type"]:
            b = out["type"]["box"]
            out["type"]["box"] = [b[0] + x0, b[1] + y0, b[2] + x0, b[3] + y0]
    if len(frames) > 1:
        seq = np.stack([x[y0:y1, x0:x1].astype(np.float32).mean(2) for x in frames])
        # the least change between neighbours: an encoder settling after a cut moves a frame or two, a grain every one
        out["still"] = round(float(np.min([np.median(d) for d in np.abs(np.diff(seq, axis=0))])), 2)
    return out


def run(reference, times: list[float], against=None, region=None, lit: float = 50, sheet=None, out=None) -> dict:
    ref = [frame_of(reference, t, 5) for t in times]
    ours = None
    if against:
        a = Path(against)
        if a.is_dir():
            h, w = ref[0][0].shape[:2]
            ours = [[x] for x in stills_of(a, times, f"{w}x{h}")]
        else:
            ours = [frame_of(a, t, 5) for t in times]
    rows = []
    for i, t in enumerate(times):
        row = {"t": t, "reference": numbers(ref[i], region, lit)}
        if ours:
            row["remake"] = numbers(ours[i], region, lit)
        rows.append(row)
    res = {"reference": str(reference), "remake": str(against) if against else None, "region": region, "lit": lit,
           "times": rows}
    if sheet:
        write_sheet(sheet, times, [x[0] for x in ref], [x[0] for x in ours] if ours else None)
    if out:
        Path(out).write_text(json.dumps(res, indent=1))
    return res


def write_sheet(path, times, ref, ours=None, width: int = 480) -> None:
    from PIL import Image, ImageDraw
    h = width * ref[0].shape[0] // ref[0].shape[1]
    rows = 2 if ours else 1
    sheet = Image.new("RGB", (width * len(times), h * rows + 20), (20, 20, 20))
    d = ImageDraw.Draw(sheet)
    for i, t in enumerate(times):
        sheet.paste(Image.fromarray(ref[i]).resize((width, h)), (i * width, 20))
        if ours:
            sheet.paste(Image.fromarray(ours[i]).resize((width, h)), (i * width, 20 + h))
        d.text((i * width + 4, 4), f"{t:g} s  reference" + (" / remake" if ours else ""), fill=(230, 230, 80))
    buf = io.BytesIO()
    sheet.save(buf, "JPEG", quality=85)
    Path(path).write_bytes(buf.getvalue())


def report(res: dict) -> str:
    def line(name, n):
        cells = "  ".join(f"{a} {c['period']}px@{c['phase']} ({c['strength']})" for a, c in n["cells"].items() if c) or "-"
        bar = n.get("bar")
        bar = f"{bar['angle']}deg {bar['length']}x{bar['width']} at {bar['centre']}" if bar else "-"
        still = n.get("still", "-")
        ty = n.get("type")
        ty = f"  type {ty['height']}px high, stroke {ty['stroke']} ({ty['ratio']}) in {ty['box']}" if ty else ""
        return (f"  {name:<9} colour {n['colour']}  lit {n['lit']}% {n['box'] or ''}  detail {n['detail']}  "
                f"still {still}  cells {cells}  bar {bar}{ty}")
    out = []
    for row in res["times"]:
        out.append(f"{row['t']:g} s")
        out.append(line("reference", row["reference"]))
        if "remake" in row:
            out.append(line("remake", row["remake"]))
    return "\n".join(out)
