"""Intake: copy the references into a project, normalised, and check they share one style.

  <project>/refs/img01.png, vid01.mp4 ...   sRGB PNG (long edge <= 2048) and H.264 MP4 at the source frame rate
  <project>/intake.json                     what came in, from where, and what it is
  <project>/evidence/refs-sheet.jpg         every reference on one sheet (videos as frames with their times)
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from fractions import Fraction
from pathlib import Path

import numpy as np
from PIL import Image

from . import sheet
from .measure import palette

IMAGES = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff"}
VIDEOS = {".mp4", ".mov", ".webm", ".mkv", ".m4v", ".gif", ".avi"}
LONG_EDGE = 2048
SIZES = {"16:9": "1920x1080", "9:16": "1080x1920", "4:5": "1080x1350", "1:1": "1080x1080", "4:3": "1440x1080"}


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def probe(path: Path) -> dict:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                          "stream=codec_type,width,height,r_frame_rate:format=duration", "-of", "json", str(path)],
                         check=True, capture_output=True, text=True).stdout
    info = json.loads(out)
    v = next(s for s in info["streams"] if s["codec_type"] == "video")
    return {"w": v["width"], "h": v["height"], "fps": round(float(Fraction(v["r_frame_rate"])), 3),
            "duration": round(float(info["format"].get("duration", 0)), 3),
            "audio": any(s["codec_type"] == "audio" for s in info["streams"])}


def _aspect(w, h):
    ratio = lambda k: int(k.split(":")[0]) / int(k.split(":")[1])  # noqa: E731
    return min(SIZES, key=lambda k: abs(w / h - ratio(k)))


def samples(item: dict, root: Path, n: int = 4) -> list[np.ndarray]:
    """Pictures a reference contributes: the image, or n frames spread over a video (away from its ends)."""
    path = root / item["file"]
    if item["kind"] == "image":
        return [np.asarray(Image.open(path).convert("RGB"))]
    d = item["duration"]
    return sheet.video_frames(str(path), [d * (k + 0.5) / n for k in range(n)])


def intake(project: Path, refs: list[Path], source: str = "unknown") -> dict:
    project = Path(project)
    (project / "refs").mkdir(parents=True, exist_ok=True)
    items, counts = [], {"image": 0, "video": 0}
    for src in refs:
        src = Path(src)
        ext = src.suffix.lower()
        kind = "image" if ext in IMAGES else "video" if ext in VIDEOS else None
        if kind is None:
            raise SystemExit(f"{src}: not an image or a video this intake knows ({sorted(IMAGES | VIDEOS)})")
        counts[kind] += 1
        rid = f"{'img' if kind == 'image' else 'vid'}{counts[kind]:02d}"
        item = {"id": rid, "kind": kind, "source_path": str(src.resolve()), "sha256": _sha(src), "source": source}
        if kind == "image":
            im = Image.open(src).convert("RGB")
            k = LONG_EDGE / max(im.size)
            if k < 1:
                im = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
            dst = project / "refs" / f"{rid}.png"
            im.save(dst)
            item.update({"file": f"refs/{dst.name}", "w": im.width, "h": im.height})
        else:
            dst = project / "refs" / f"{rid}.mp4"
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-c:v", "libx264", "-crf", "16", "-preset", "medium",
                            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(dst)],
                           check=True)
            item.update({"file": f"refs/{dst.name}", **probe(dst)})
        items.append(item)
    pictures = {it["id"]: samples(it, project) for it in items}
    pals = [palette.image_palette(sheet.stack(pictures[it["id"]])) for it in items]
    uni = palette.unity(pals)
    aspects = [_aspect(it["w"], it["h"]) for it in items]
    size = SIZES[max(set(aspects), key=aspects.count)]
    tiles = []
    for it in items:
        ps = pictures[it["id"]]
        if it["kind"] == "image":
            tiles.append((it["id"], ps[0]))
        else:
            d = it["duration"]
            tiles += [(f"{it['id']} @{d * (k + 0.5) / len(ps):.1f}s", p) for k, p in enumerate(ps)]
    sheet.references(tiles, project / "evidence" / "refs-sheet.jpg")
    result = {"refs": items, "default_size": size,
              "unity": {**uni, "groups": [[items[i]["id"] for i in g] for g in uni["groups"]]}}
    (project / "intake.json").write_text(json.dumps(result, indent=1, ensure_ascii=False))
    return result
