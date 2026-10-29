"""`moodreel scene-check`: a copied composition is caught, a new one passes, an empty page is not judged."""
from __future__ import annotations

import json
import shutil
import subprocess

import numpy as np
import pytest
from PIL import Image

from moodreel.check import scene

needs_ffmpeg = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="needs ffmpeg")


def _frame(kind):
    f = np.full((270, 480), 40, np.uint8)
    yy, xx = np.mgrid[:270, :480]
    if kind == "disc":                                   # a white disc in the left third
        f[(xx - 140) ** 2 + (yy - 135) ** 2 < 60 ** 2] = 235
    elif kind == "bar":                                  # a white bar at the right
        f[60:210, 360:420] = 235
    elif kind == "corners":                              # two squares, top right and bottom left
        f[20:80, 380:440] = 235
        f[190:250, 40:100] = 235
    elif kind == "blank":
        f[:] = 236
    return f


@needs_ffmpeg
def test_scene_check_catches_a_copied_composition_and_passes_a_new_one(tmp_path):
    proj = tmp_path / "proj"
    (proj / "refs").mkdir(parents=True)
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "gray", "-s", "480x270", "-r", "10",
                          "-i", "-", "-c:v", "libx264", "-crf", "8", "-pix_fmt", "yuv444p", str(proj / "refs" / "vid01.mp4")],
                         stdin=subprocess.PIPE)
    for kind in ["disc"] * 20 + ["bar"] * 20:
        p.stdin.write(_frame(kind).tobytes())
    p.stdin.close()
    p.wait()
    (proj / "intake.json").write_text(json.dumps({"refs": [{"id": "vid01", "kind": "video", "file": "refs/vid01.mp4"}]}))
    stills = {}
    for kind in ("disc", "corners", "blank"):
        stills[kind] = tmp_path / f"{kind}.png"
        Image.fromarray(_frame(kind)).convert("RGB").save(stills[kind])
    r = scene.check(proj, [stills["disc"], stills["corners"], stills["blank"]], out=tmp_path / "out")
    got = {f["input"].rsplit("/", 1)[-1]: f["verdict"] for f in r["frames"]}
    assert got == {"disc.png": "copies", "corners.png": "new", "blank.png": "blank"}
    assert r["copies"] == 1 and not r["ok"] and (tmp_path / "out" / "scene-check.jpg").exists()
