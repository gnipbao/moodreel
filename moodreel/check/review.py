"""`moodreel review <reference> <remake> --shots scenes.json --out <dir>`: a producer's review before a cut is shown.

The scores say how close a remake is; they don't say what a viewer sees first: the paper a shade too grey, the orange
too dull, a creature facing the wrong way. A review looks at every window at full size, side by side, and audits the
colours that carry the picture, so the faults are listed before anything is fixed:

  sheets   for every window, the reference beside the remake at 40 % and at 80 % of it, 480 px each (review-N.jpg)
  palette  per window, at three moments, the ground (the most common colour), the ink (the 4 % farthest from the ground
           in lightness) and the accent (the 3 % most saturated, when there is one), the reference's beside the
           remake's, with the colour difference (CIE76 dE): above 6 a viewer sees it, above 12 it is another colour

and writes review.md: the windows whose ground, ink or accent are off, worst first, with the sheets to read beside it.
The fault list is the reviewer's to finish: what is missing, what faces or moves the wrong way, what a shot is for.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import numpy as np

SEEN, OTHER = 6.0, 12.0


def _frame(path, t: float, w: int, h: int) -> np.ndarray:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{max(0.0, t):.3f}", "-i", str(path), "-frames:v", "1",
                          "-vf", f"scale={w}:{h}:flags=area", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw[: w * h * 3], np.uint8).reshape(h, w, 3)


def lab(rgb) -> np.ndarray:
    c = np.asarray(rgb, float) / 255
    c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    x = c @ np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]]).T / [0.9505, 1, 1.089]
    f = np.where(x > 0.008856, np.cbrt(x), 7.787 * x + 16 / 116)
    return np.array([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])]).T


def de(a, b) -> float | None:
    return None if a is None or b is None else round(float(np.linalg.norm(lab(a) - lab(b))), 1)


def parts(px: np.ndarray):
    """A frame's (N x 3) ground, ink and accent colours."""
    q = (px // 24).astype(int)
    key = q[:, 0] * 10000 + q[:, 1] * 100 + q[:, 2]
    vals, cnt = np.unique(key, return_counts=True)
    ground = px[key == vals[cnt.argmax()]].mean(0)
    luma = px @ [0.2126, 0.7152, 0.0722]
    far = np.abs(luma - ground @ [0.2126, 0.7152, 0.0722])
    ink = px[far >= np.percentile(far, 96)].mean(0)
    sat = px.max(1) - px.min(1)
    accent = px[sat >= np.percentile(sat, 97)].mean(0) if sat.max() > 40 else None
    return ground, ink, accent


def palette(reference, remake, shots, at=(0.3, 0.55, 0.8)) -> list[dict]:
    rows = []
    for t0, t1, name in shots:
        got = {"reference": [], "remake": []}
        for f in at:
            t = t0 + (t1 - t0) * f
            for key, path in (("reference", reference), ("remake", remake)):
                got[key].append(parts(_frame(path, t, 160, 90).reshape(-1, 3).astype(float)))
        row = {"window": name, "t0": t0, "t1": t1}
        for k, part in enumerate(("ground", "ink", "accent")):
            r = [p[k] for p in got["reference"] if p[k] is not None]
            o = [p[k] for p in got["remake"] if p[k] is not None]
            r, o = (np.mean(r, 0) if r else None), (np.mean(o, 0) if o else None)
            row[part] = {"reference": None if r is None else "#%02x%02x%02x" % tuple(int(round(v)) for v in r),
                         "remake": None if o is None else "#%02x%02x%02x" % tuple(int(round(v)) for v in o), "dE": de(r, o)}
        rows.append(row)
    return rows


def sheets(reference, remake, shots, out: Path, per: int = 8, w: int = 480) -> list[Path]:
    from PIL import Image, ImageDraw
    h = w * 9 // 16
    paths = []
    for s in range(0, len(shots), per):
        part = shots[s:s + per]
        sheet = Image.new("RGB", (4 * w, len(part) * (h + 18)), "black")
        d = ImageDraw.Draw(sheet)
        for k, (t0, t1, name) in enumerate(part):
            y = k * (h + 18)
            for j, f in enumerate((0.4, 0.8)):
                t = t0 + (t1 - t0) * f
                sheet.paste(Image.fromarray(_frame(reference, t, w, h)), (2 * j * w, y + 18))
                sheet.paste(Image.fromarray(_frame(remake, t, w, h)), ((2 * j + 1) * w, y + 18))
                d.text((2 * j * w + 4, y + 3), f"{name} {t:.2f}  reference", fill="yellow")
                d.text(((2 * j + 1) * w + 4, y + 3), "remake", fill="cyan")
        p = out / f"review-{s // per + 1}.jpg"
        sheet.save(p, quality=86)
        paths.append(p)
    return paths


def flagged(rows: list[dict]) -> list[dict]:
    """The windows with a colour a viewer sees as off, worst first."""
    out = []
    for r in rows:
        off = {k: r[k] for k in ("ground", "ink", "accent") if (r[k]["dE"] or 0) > SEEN}
        if off:
            out.append({"window": r["window"], "t0": r["t0"], "off": off, "worst": max(v["dE"] for v in off.values())})
    return sorted(out, key=lambda x: -x["worst"])


def report(rows: list[dict], sheet_paths) -> str:
    lines = ["# Review", "", "Colours a viewer sees as off (dE above 6; above 12 another colour), worst first. Read the sheets "
             "beside it and add what the numbers can't see: what is missing, what faces or moves the wrong way, what a "
             "shot is for.", "", "| window | t0 | ground | ink | accent |", "|---|---|---|---|---|"]
    cell = lambda v: "" if not v or (v["dE"] or 0) <= SEEN else f'{v["reference"]} → {v["remake"]} (dE {v["dE"]}{"!" if v["dE"] > OTHER else ""})'  # noqa: E731
    for f in flagged(rows):
        lines.append(f'| {f["window"]} | {f["t0"]:.2f} | ' + " | ".join(cell(f["off"].get(k)) for k in ("ground", "ink", "accent")) + " |")
    if len(lines) == 6:
        lines.append("| (none) | | | | |")
    lines += ["", "Sheets: " + ", ".join(Path(p).name for p in sheet_paths)]
    return "\n".join(lines) + "\n"


def run(reference, remake, shots_path, out, per: int = 8) -> dict:
    shots = json.loads(Path(shots_path).read_text())
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    rows = palette(reference, remake, shots)
    paths = sheets(reference, remake, shots, out, per)
    (out / "review.json").write_text(json.dumps({"windows": rows, "flagged": flagged(rows)}, indent=1))
    (out / "review.md").write_text(report(rows, paths))
    return {"windows": rows, "flagged": flagged(rows), "sheets": [str(p) for p in paths], "out": str(out)}
