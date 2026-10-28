"""`moodreel review`: the colour audit names the window whose ground is off, and writes the sheets and the report."""
from __future__ import annotations

import json
import shutil
import subprocess

import numpy as np
import pytest

from moodreel.check import review

needs_ffmpeg = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="needs ffmpeg")


def _video(path, grounds, n=30):
    """A 2 s film at 30 fps: a ground colour per second with a dark mark (ink) and an orange mark (accent) on it."""
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "160x90", "-r", "30",
                          "-i", "-", "-c:v", "libx264", "-crf", "8", "-pix_fmt", "yuv444p", str(path)], stdin=subprocess.PIPE)
    for g in grounds:
        for _ in range(n):
            f = np.full((90, 160, 3), g, np.uint8)
            f[30:60, 20:50] = (24, 20, 16)
            f[30:60, 100:130] = (235, 90, 36)
            p.stdin.write(f.tobytes())
    p.stdin.close()
    p.wait()


def test_the_lab_difference_is_zero_for_a_colour_and_large_for_another():
    assert review.de((240, 236, 226), (240, 236, 226)) == 0
    assert review.de((240, 236, 226), (200, 200, 200)) > 6


@needs_ffmpeg
def test_review_names_the_window_whose_paper_is_off(tmp_path):
    ref, ours = tmp_path / "ref.mp4", tmp_path / "ours.mp4"
    _video(ref, [(245, 240, 230), (245, 240, 230)])
    _video(ours, [(245, 240, 230), (205, 205, 205)])             # the second second's paper grey, not warm
    shots = tmp_path / "shots.json"
    shots.write_text(json.dumps([[0.0, 1.0, "warm"], [1.0, 2.0, "grey"]]))
    res = review.run(ref, ours, shots, tmp_path / "rv", per=8)
    rows = {r["window"]: r for r in res["windows"]}
    assert rows["warm"]["ground"]["dE"] < 3 and rows["grey"]["ground"]["dE"] > review.SEEN
    assert [f["window"] for f in res["flagged"]] == ["grey"]
    assert (tmp_path / "rv" / "review-1.jpg").exists()
    text = (tmp_path / "rv" / "review.md").read_text()
    assert "| grey |" in text and "| warm |" not in text
