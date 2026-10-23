"""Real material in a film: footage, stills and prints, and data, each with where it came from and under what licence.

`moodreel media add <film> <file> --name N --source S --license L` brings a local file into `<film>/media/`:
  footage  (mp4, mov, webm, mkv, avi, m4v)  frames at the film's rate, one JPEG per film frame, so any frame of the
           film draws without seeking a video (deterministic, any order, any worker); trimmed (--start/--end),
           cropped (--crop x,y,w,h in source px), scaled (--width) and optionally graded (--grade mono)
  still    (png, jpg, tif, webp, gif)       cropped and scaled the same way
  data     (csv, tsv, json, geojson, txt)   copied as it is
and records it in `media/manifest.json` (kind, size, frames, rate, the trim, the file's SHA-256, source, licence)
and in CREDITS. The picture reads it with kit/media.js. `check` says what has no source or licence, and what sits
in media/ without an entry. Moodreel doesn't fetch anything: obtaining the file (and the right to use it) is a step
the user agrees to.
"""
from __future__ import annotations

import datetime
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

FOOTAGE = {".mp4", ".mov", ".webm", ".mkv", ".avi", ".m4v"}
STILL = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".webp", ".gif"}
DATA = {".csv", ".tsv", ".json", ".geojson", ".txt"}
GRADES = {"none": None, "mono": "format=gray,format=yuv420p"}


def _manifest(film: Path) -> dict:
    p = film / "media" / "manifest.json"
    return json.loads(p.read_text()) if p.exists() else {}


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _filters(crop, width, grade) -> list[str]:
    vf = []
    if crop:
        x, y, w, h = crop
        vf.append(f"crop={w}:{h}:{x}:{y}")
    if width:
        vf.append(f"scale={width}:-2:flags=lanczos")
    if GRADES.get(grade or "none"):
        vf.append(GRADES[grade])
    return vf


def _size(path: Path) -> list[int]:
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                          "-of", "json", str(path)], capture_output=True, text=True, check=True)
    s = json.loads(out.stdout)["streams"][0]
    return [s["width"], s["height"]]


def add(film: Path, src: Path, name: str, source: str, license: str, start: float | None = None, end: float | None = None,
        crop: tuple[int, int, int, int] | None = None, width: int | None = None, grade: str | None = None) -> dict:
    film, src = Path(film), Path(src)
    if not name.replace("-", "").replace("_", "").isalnum():
        raise SystemExit(f"media name {name!r}: letters, digits, - and _ only")
    if not source.strip() or not license.strip():
        raise SystemExit("every piece of material needs --source (where it came from) and --license (the terms it is used under)")
    if grade and grade not in GRADES:
        raise SystemExit(f"--grade: one of {', '.join(GRADES)}")
    ext = src.suffix.lower()
    f = json.loads((film / "film.json").read_text())
    out_dir = film / "media"
    out_dir.mkdir(exist_ok=True)
    entry = {"source": source, "license": license, "sha256": _sha(src), "original": src.name,
             "added": datetime.date.today().isoformat()}
    if ext in FOOTAGE:
        dst = out_dir / name
        if dst.exists():
            shutil.rmtree(dst)
        dst.mkdir()
        trim = (["-ss", str(start)] if start is not None else []) + (["-to", str(end)] if end is not None else [])
        vf = ",".join(_filters(crop, width, grade) + [f"fps={f['fps']}"])
        subprocess.run(["ffmpeg", "-y", "-v", "error", *trim, "-i", str(src), "-an", "-vf", vf, "-q:v", "3",
                        str(dst / "%05d.jpg")], check=True)
        frames = sorted(dst.glob("*.jpg"))
        if not frames:
            raise SystemExit(f"{src}: no frames in that range")
        entry.update({"kind": "footage", "path": f"media/{name}/", "frames": len(frames), "fps": f["fps"],
                      "duration": round(len(frames) / f["fps"], 3), "size": _size(frames[0]),
                      "start": start, "end": end, "crop": crop, "width": width, "grade": grade})
    elif ext in STILL:
        dst = out_dir / f"{name}{'.png' if ext in ('.png', '.gif', '.tif', '.tiff') else '.jpg'}"
        vf = _filters(crop, width, grade)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(src), *(["-vf", ",".join(vf)] if vf else []),
                        "-frames:v", "1", *(["-q:v", "2"] if dst.suffix == ".jpg" else []), str(dst)], check=True)
        entry.update({"kind": "still", "path": f"media/{dst.name}", "size": _size(dst), "crop": crop, "width": width,
                      "grade": grade})
    elif ext in DATA:
        dst = out_dir / f"{name}{ext}"
        shutil.copyfile(src, dst)
        entry.update({"kind": "data", "path": f"media/{dst.name}", "format": ext.lstrip(".")})
    else:
        raise SystemExit(f"{src}: not footage ({', '.join(sorted(FOOTAGE))}), a still ({', '.join(sorted(STILL))}) "
                         f"or data ({', '.join(sorted(DATA))})")
    manifest = _manifest(film)
    manifest[name] = entry
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=1))
    credits = film / "CREDITS"
    line = f"- {name} ({entry['kind']}): {source} — {license}\n"
    text = credits.read_text() if credits.exists() else ""
    if line not in text:
        credits.write_text(text + line)
    return {"name": name, **{k: v for k, v in entry.items() if v is not None}}


def check(film: Path) -> dict:
    """Material without a source or licence, and files in media/ that no entry lists."""
    film = Path(film)
    media = film / "media"
    if not media.exists():
        return {"items": 0, "ok": True}
    manifest = _manifest(film)
    missing = [n for n, e in manifest.items() if not (e.get("source") or "").strip() or not (e.get("license") or "").strip()]
    listed = {e["path"].rstrip("/") for e in manifest.values()}
    unlisted = [p.relative_to(film).as_posix() for p in media.iterdir() if p.name != "manifest.json"
                and p.relative_to(film).as_posix() not in listed]
    gone = [n for n, e in manifest.items() if not (film / e["path"]).exists()]
    return {"items": len(manifest), "no_source_or_license": missing, "unlisted": sorted(unlisted), "missing_files": gone,
            "ok": not (missing or unlisted or gone)}
