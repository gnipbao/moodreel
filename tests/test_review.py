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


def _motion_video(path, remake=False, n=120):
    """A 4 s film at 30 fps on grey: a white square snaps in at 1.0 s (the remake fades it in over 0.6 s), a second at
    2.5 s (the remake never shows it), and from 3.0 s a block of grain slides right 3 px a frame (the remake's holds)."""
    rng = np.random.default_rng(7)
    grain = rng.integers(0, 255, (30, 30), dtype=np.uint8)
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "gray", "-s", "160x90", "-r", "30",
                          "-i", "-", "-c:v", "libx264", "-crf", "6", "-pix_fmt", "yuv444p", str(path)], stdin=subprocess.PIPE)
    for i in range(n):
        f = np.full((90, 160), 128, np.uint8)
        a = 1.0 if not remake else min(1.0, max(0.0, (i - 21) / 18))
        if i >= (30 if not remake else 21):
            f[10:40, 10:40] = np.uint8(128 + 127 * a)
        if i >= 75 and not remake:
            f[10:40, 110:140] = 255
        x = 20 + (3 * (i - 90) if i >= 90 and not remake else 0)
        f[55:85, x:x + 30] = grain
        p.stdin.write(f.tobytes())
    p.stdin.close()
    p.wait()


@needs_ffmpeg
def test_the_motion_review_names_a_snap_eased_one_missing_and_a_move_held_still(tmp_path):
    ref, ours = tmp_path / "ref.mp4", tmp_path / "ours.mp4"
    _motion_video(ref)
    _motion_video(ours, remake=True)
    shots = tmp_path / "shots.json"
    shots.write_text(json.dumps([[0.0, 2.0, "first"], [2.0, 3.0, "second"], [3.0, 4.0, "slide"]]))
    m = review.motion_run(ref, ours, shots, tmp_path / "mv")
    off = {round(r["t"]): r for r in m["snaps"] if r["verdict"]}
    assert off[1]["window"] == "first" and off[1]["verdict"].startswith("eased")
    assert any(r["window"] == "second" and r["verdict"] == "missing" for r in m["snaps"])
    assert any(s["window"] == "slide" and "still where the reference moves" in s["off"] for s in m["spans"])
    assert (tmp_path / "mv" / "motion-1.jpg").exists()
    assert "| second |" in (tmp_path / "mv" / "motion.md").read_text()
