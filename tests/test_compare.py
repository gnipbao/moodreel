"""`moodreel compare` between passes: each window's change since the last pass, and the reference-beside-remake sheet."""
from __future__ import annotations

import shutil
import subprocess

import numpy as np
import pytest
from PIL import Image

from moodreel.check import compare

needs_ffmpeg = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="needs ffmpeg")


def _row(name, t0, t1, score):
    return {"window": name, "t0": t0, "t1": t1, "score": score, "problems": [], "structure": 0.5, "detail": 1.0,
            "tone": 1.0, "flow": None, "speed": None}


def _res(rows):
    return {"reference": "r.mp4", "remake": "m.mp4", "windows": rows,
            "median": {k: 0 for k in ("structure", "detail", "tone", "flow", "speed", "score")}, "worst": []}


def test_against_gives_each_windows_change_and_the_means():
    prev = _res([_row("fall", 18.2, 20.7, 0.27), _row("river", 26.0, 27.4, 0.38)])
    now = compare.against(_res([_row("fall", 18.2, 20.7, 0.55), _row("river", 26.0, 27.4, 0.36), _row("new", 30, 31, 0.5)]), prev)
    ch = {r["window"]: r["change"] for r in now["windows"]}
    assert ch == {"fall": 0.28, "river": -0.02, "new": None}         # a window the last pass didn't have: no change
    assert now["mean"] == {"before": 0.325, "now": 0.47}
    text = compare.report(now)
    assert "+0.280" in text and "-0.020" in text and "mean score: 0.325 -> 0.47" in text


def test_report_without_a_previous_pass_has_no_change_column():
    assert "change" not in compare.report(_res([_row("typing", 0, 2.7, 0.88)]))


def _video(path, colour, n=30):
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "160x90", "-r", "30",
                          "-i", "-", "-c:v", "libx264", "-crf", "12", "-pix_fmt", "yuv420p", str(path)], stdin=subprocess.PIPE)
    for i in range(n):
        f = np.full((90, 160, 3), colour, np.uint8)
        f[:, : 160 * (i + 1) // n] = 255 - np.array(colour, np.uint8)   # a wipe, so the frames differ
        p.stdin.write(f.tobytes())
    p.stdin.close()
    p.wait()


@needs_ffmpeg
def test_sheet_puts_the_reference_beside_the_remake_worst_first(tmp_path):
    ref, ours = tmp_path / "ref.mp4", tmp_path / "ours.mp4"
    _video(ref, (200, 30, 30))
    _video(ours, (30, 30, 200))
    res = _res([_row("good", 0.0, 0.5, 0.9), _row("bad", 0.5, 1.0, 0.2)])
    res["reference"], res["remake"] = str(ref), str(ours)
    out = compare.sheet(res, tmp_path / "pairs.jpg", size=(160, 90))
    img = np.asarray(Image.open(out).convert("RGB")).astype(int)
    assert img.shape == (90, 160 * 2 * 2, 3)                          # two windows: one row of two pairs
    mean = lambda x0, x1: img[20:70, x0:x1].mean((0, 1))  # noqa: E731
    # the reference left, the remake right: red ground beside blue ground, where the wipe hasn't reached
    assert mean(135, 155)[0] > mean(135, 155)[2] and mean(295, 315)[2] > mean(295, 315)[0]
    # worst first: the first pair is "bad" (t 0.75, the wipe three quarters across), the second "good" (t 0.25)
    assert mean(60, 100)[2] > mean(60, 100)[0]                         # wiped: red inverted to cyan
    assert mean(320 + 60, 320 + 100)[0] > mean(320 + 60, 320 + 100)[2]  # not yet wiped


@needs_ffmpeg
def test_windows_measured_in_parallel_match_one_by_one(tmp_path):
    ref, ours = tmp_path / "ref.mp4", tmp_path / "ours.mp4"
    _video(ref, (200, 30, 30))
    _video(ours, (30, 30, 200))
    shots = [[0.0, 0.5, "a"], [0.5, 1.0, "b"]]
    one = compare.compare(ref, ours, shots, workers=1)
    many = compare.compare(ref, ours, shots, workers=2)
    assert [r["score"] for r in one["windows"]] == [r["score"] for r in many["windows"]]


def _pan(path, dx, n=30):
    """A textured ground sliding dx px a frame (+ right), 160 x 90 at 30 fps."""
    rng = np.random.default_rng(3)
    tex = (rng.random((90, 400)) * 255).astype(np.uint8)
    tex = np.asarray(Image.fromarray(tex).resize((800, 90)))           # coarse enough for the flow to follow
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "gray", "-s", "160x90", "-r", "30",
                          "-i", "-", "-c:v", "libx264", "-crf", "12", "-pix_fmt", "yuv420p", str(path)], stdin=subprocess.PIPE)
    for i in range(n):
        x0 = 320 - dx * i
        p.stdin.write(np.ascontiguousarray(tex[:, x0:x0 + 160]).tobytes())
    p.stdin.close()
    p.wait()


@needs_ffmpeg
def test_motion_reads_when_and_which_way_each_picture_moves(tmp_path):
    ref, ours = tmp_path / "ref.mp4", tmp_path / "ours.mp4"
    _pan(ref, 2)                                                       # sliding right
    _pan(ours, -4)                                                     # left, twice as fast
    m = compare.motion(ref, ours, 0.0, 0.9)
    assert len(m["reference"]["speed"]) == 5                           # every 0.2 s over 0.9 s
    r, o = (np.nanmean([v for v in m[k]["speed"] if v is not None]) for k in ("reference", "remake"))
    assert 1.6 < o / r < 2.4                                           # the remake twice as fast
    R, O = np.array(m["reference"]["cells"]), np.array(m["remake"]["cells"])
    assert (R[..., 0] > 0).all() and (O[..., 0] < 0).all()             # every cell: right in one, left in the other
    text = compare.motion_report("pan", m)
    assert "reference" in text and "remake" in text and text.count("  |  ") == 4   # a row of cells each
