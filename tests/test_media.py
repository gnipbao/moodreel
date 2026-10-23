"""Real material: footage becomes frames at the film's rate, stills and data come in with their source and licence,
the check finds what has none or isn't listed, and the picture shows the frame of its own time."""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import cv2
import numpy as np
import pytest

from moodreel import media

REPO = Path(__file__).resolve().parents[1]
needs_ffmpeg = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="needs ffmpeg")


def _film(tmp_path, fps=24):
    d = tmp_path / "film"
    (d / "kit").mkdir(parents=True)
    (d / "film.json").write_text(json.dumps({"name": "film", "fps": fps, "size": "320x180", "duration": 3}))
    (d / "CREDITS").write_text("film\n\n")
    return d


def _clip(path, seconds=2, rate=30):
    """A clip whose every frame shows its own number as a grey level (frame k: 4 k)."""
    frames = np.stack([np.full((120, 160, 3), 4 * k, np.uint8) for k in range(seconds * rate)])
    p = subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "160x120", "-r", str(rate),
                        "-i", "-", "-c:v", "libx264", "-qp", "0", "-pix_fmt", "yuv444p", str(path)], input=frames.tobytes())
    assert p.returncode == 0


@needs_ffmpeg
def test_footage_stills_and_data_come_in_with_their_provenance(tmp_path):
    d = _film(tmp_path)
    _clip(tmp_path / "clip.mp4")
    r = media.add(d, tmp_path / "clip.mp4", "clip", "made for the test", "CC0", start=1.0, end=2.0)
    assert r["kind"] == "footage" and r["frames"] == 24 and r["fps"] == 24 and r["duration"] == 1.0
    first = cv2.imread(str(d / "media" / "clip" / "00001.jpg"))
    assert abs(float(first.mean()) - 4 * 30) < 2              # the trim starts at 1 s: source frame 30
    cv2.imwrite(str(tmp_path / "scan.png"), np.full((300, 400, 3), 200, np.uint8))
    assert media.add(d, tmp_path / "scan.png", "scan", "an archive, item 12", "public domain", width=200)["size"] == [200, 150]
    (tmp_path / "t.csv").write_text("a,b\n1,2\n")
    assert media.add(d, tmp_path / "t.csv", "table", "made up", "CC0")["kind"] == "data"
    assert media.check(d)["ok"] and "clip (footage): made for the test — CC0" in (d / "CREDITS").read_text()
    with pytest.raises(SystemExit):
        media.add(d, tmp_path / "t.csv", "nolicence", "somewhere", "")


@needs_ffmpeg
def test_the_check_finds_what_has_no_provenance_or_no_entry(tmp_path):
    d = _film(tmp_path)
    (tmp_path / "t.csv").write_text("a\n1\n")
    media.add(d, tmp_path / "t.csv", "table", "made up", "CC0")
    m = json.loads((d / "media" / "manifest.json").read_text())
    m["table"]["license"] = ""
    (d / "media" / "manifest.json").write_text(json.dumps(m))
    (d / "media" / "stray.png").write_bytes(b"")
    r = media.check(d)
    assert not r["ok"] and r["no_source_or_license"] == ["table"] and r["unlisted"] == ["media/stray.png"]


@needs_ffmpeg
@pytest.mark.skipif(shutil.which("node") is None or not (REPO / "node_modules" / "puppeteer-core").exists(),
                    reason="needs node and npm install")
def test_the_picture_shows_the_frame_of_its_own_time(tmp_path):
    d = _film(tmp_path)
    _clip(tmp_path / "clip.mp4")
    media.add(d, tmp_path / "clip.mp4", "clip", "made for the test", "CC0")
    for f in ("stage.js", "media.js"):
        shutil.copyfile(REPO / "kit" / f, d / "kit" / f)
    (d / "index.html").write_text('<!doctype html><html><body><script type="module" src="main.js"></script></body></html>')
    (d / "main.js").write_text("import { stage } from './kit/stage.js';\nimport { load } from './kit/media.js';\n"
                               "const M = await load();\n"
                               "stage({ width: 320, height: 180, duration: 3,\n"
                               "  draw: (g, t) => g.drawImage(M.frame('clip', t), 0, 0, 320, 180) });\n")
    subprocess.run(["node", str(REPO / "render" / "render.mjs"), "still", str(d), "1.5", "--size", "320x180", "--out",
                    str(d / "out")], check=True, capture_output=True, timeout=120)
    shown = cv2.imread(str(d / "out" / "t_1.5.jpg")).mean()
    assert abs(shown - 4 * 45) < 2                            # 1.5 s at 30 fps in the source: its frame 45
