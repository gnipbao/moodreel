"""`moodreel scene-check <project> <film or stills>...`: the style's look, but scenes of its own?

A distilled style should carry its references' look, not their scenes: a film that re-dresses the reference's
compositions (the same opening, the same set piece, the same framing) reads as a remake of it, however new its
subject. frame-check says whether a picture looks like the style; this says whether it copies a reference's scene.

Each frame (a film's every `step` seconds, or each still) is laid out as its masses of light and dark at the size of
objects (luma at 96 x 54, band-passed between blurs of 1.5 and 8 px so a vignette, a haze or a ground's gradient don't
count; normalised) and matched against every reference frame (every 0.5 s). The best correlation says how close the
composition is, and where in the references it is:

  0.70 and up   copies a scene: the reference's layout at that time
  0.55-0.70     close: a reference's composition, perhaps re-dressed: a lead to look at, not a fault (an unrelated
                film reaches it in up to a third of its frames)
  under 0.55    new
  (blank)       too even to have a composition: an empty page, a fade

Calibrated on the fourth manual test: its shot-by-shot remake's frames match at 0.63 (median; 42 % at 0.70 or more),
two unrelated films at 0.28 and 0.38 (none at 0.70). Plain luma matched any empty page to any other by its vignette;
edge maps matched any film full of type with any other (the style, not the scene). It sees compositions, not ideas: a
reference's set piece redrawn in a new layout passes; that is the director's review against ANALYSIS.md's inventory.
A sheet puts each copied or close frame beside its reference frame.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import numpy as np

COPY, CLOSE = 0.70, 0.55
LW, LH = 96, 54
BAND = (1.5, 8.0)       # px at 96 x 54: masses the size of objects, not a vignette or a haze
BLANK = 1.5             # levels: a band-passed frame that varies less has no composition to judge (paper, a fade)


def _gray(path, step: float, w: int = LW, h: int = LH) -> tuple[list[float], np.ndarray]:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-vf", f"fps={1 / step},scale={w}:{h}:flags=area",
                          "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True, check=True).stdout
    n = len(raw) // (w * h)
    return [round((k + 0.5) * step, 2) for k in range(n)], np.frombuffer(raw[: n * w * h], np.uint8).reshape(n, h, w)


def _still(path, w: int = LW, h: int = LH) -> np.ndarray:
    from PIL import Image
    return np.asarray(Image.open(path).convert("L").resize((w, h), Image.BOX))


def layout(a: np.ndarray) -> np.ndarray | None:
    """A frame's masses of light and dark: blurred, zero mean, unit spread (so brightness and contrast don't count);
    None for a frame too even to have a composition (an empty page, a fade): it would match any other by its vignette."""
    from scipy.ndimage import gaussian_filter
    a = np.asarray(a, float)
    a = gaussian_filter(a, BAND[0]) - gaussian_filter(a, BAND[1])
    a = a - a.mean()
    s = a.std()
    return None if s < BLANK else (a / s).ravel()


VIDEO = {".mp4", ".mov", ".webm", ".mkv", ".m4v", ".gif"}


def references(project: Path, step: float = 0.5) -> list[tuple[str, float, np.ndarray]]:
    """Every reference frame as (reference file, time, layout); a packed style keeps no references: []."""
    project = Path(project)
    intake = project / "intake.json"
    if not intake.exists():
        return []
    out = []
    for r in json.loads(intake.read_text())["refs"]:
        f = project / r["file"]
        if not f.exists():
            continue
        if f.suffix.lower() in VIDEO:
            times, frames = _gray(f, step)
            out += [(r["file"], t, lay) for t, fr in zip(times, frames) if (lay := layout(fr)) is not None]
        elif (lay := layout(_still(f))) is not None:
            out.append((r["file"], 0.0, lay))
    return out


def match(frames: list[np.ndarray], refs: list[tuple[str, float, np.ndarray]]) -> list[dict]:
    """For each frame, the nearest reference composition: its file, time and correlation."""
    R = np.stack([r[2] for r in refs])
    out = []
    for f in frames:
        lay = layout(f)
        if lay is None:
            out.append({"similarity": None, "reference": None, "at": None})
            continue
        c = R @ lay / R.shape[1]
        k = int(c.argmax())
        out.append({"similarity": round(float(c[k]), 3), "reference": refs[k][0], "at": refs[k][1]})
    return out


def verdict(s: float | None) -> str:
    return "blank" if s is None else "copies" if s >= COPY else "close" if s >= CLOSE else "new"


def check(project: Path, inputs: list[Path], step: float = 1.0, out: Path | None = None) -> dict:
    project = Path(project)
    refs = references(project)
    if not refs:
        return {"ok": None, "note": "no references here (a packed style keeps none): run it in the project", "frames": []}
    rows = []
    for p in inputs:
        p = Path(p)
        if p.suffix.lower() in VIDEO:
            times, frames = _gray(p, step)
            rows += [{"input": str(p), "t": t, **m} for t, m in zip(times, match(list(frames), refs))]
        else:
            rows += [{"input": str(p), "t": None, **match([_still(p)], refs)[0]}]
    for r in rows:
        r["verdict"] = verdict(r["similarity"])
    n = sum(r["verdict"] != "blank" for r in rows)
    copies, close = sum(r["verdict"] == "copies" for r in rows), sum(r["verdict"] == "close" for r in rows)
    res = {"frames": rows, "copies": copies, "close": close, "new": n - copies - close, "blank": len(rows) - n,
           "copy_share": round(copies / n, 3) if n else None,
           "ok": copies == 0, "limits": {"copies": COPY, "close": CLOSE}}   # close frames are leads to look at, not faults:
    # an unrelated film reaches the close band in up to a third of its frames
    dest = Path(out) if out else project / "evidence"
    dest.mkdir(parents=True, exist_ok=True)
    flagged = [r for r in rows if r["verdict"] in ("copies", "close")]
    if flagged:
        res["sheet"] = str(_sheet(project, flagged[:12], dest / "scene-check.jpg"))
    (dest / "scene-check.json").write_text(json.dumps(res, indent=1))
    return res


def _sheet(project: Path, rows: list[dict], path: Path) -> Path:
    """Each copied or close frame beside the reference frame it matches."""
    from PIL import Image

    from .. import sheet
    pic = lambda f, t: sheet.video_frames(str(f), [t])[0] if Path(f).suffix.lower() in VIDEO else np.asarray(Image.open(f).convert("RGB"))  # noqa: E731
    tiles = []
    for r in rows:
        where = f"{r['t']} s" if r["t"] is not None else Path(r["input"]).name
        tiles += [sheet._label(sheet.fit_cell(pic(r["input"], r["t"]), 360), f"ours {where}: {r['verdict']} {r['similarity']}"),
                  sheet._label(sheet.fit_cell(pic(Path(project) / r["reference"], r["at"]), 360), f"reference {r['at']} s")]
    return sheet.write(path, sheet.grid(tiles, 4))
