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
    R, O = np.array(m["reference"]["cells"]), np.array(m["remake"]["cells"])  # noqa: E741
    assert (R[..., 0] > 0).all() and (O[..., 0] < 0).all()             # every cell: right in one, left in the other
    text = compare.motion_report("pan", m)
    assert "reference" in text and "remake" in text and text.count("  |  ") == 4   # a row of cells each


def _counter(path, audio, n=48, step=5):
    """24 fps, frame m a flat grey of level 10 + 5 m (lossless), with or without an AAC soundtrack of the same length."""
    cmd = ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "gray", "-s", "64x36", "-r", "24", "-i", "-"]
    if audio:
        cmd += ["-f", "lavfi", "-i", f"sine=frequency=440:sample_rate=48000:duration={n / 24}", "-c:a", "aac"]
    p = subprocess.Popen(cmd + ["-c:v", "libx264", "-qp", "0", "-pix_fmt", "yuv420p", str(path)], stdin=subprocess.PIPE)
    for m in range(n):
        p.stdin.write(np.full((36, 64), 10 + step * m, np.uint8).tobytes())
    p.stdin.close()
    p.wait()


@needs_ffmpeg
def test_a_window_reads_the_picture_on_screen_at_each_time_with_or_without_a_soundtrack(tmp_path):
    # ffmpeg's own -ss/-t/fps resampling started one 30 fps frame apart on the same pictures with and without audio,
    # at more than half the window starts tried; frame k is now the picture on screen at t0 + k/30 in both
    with_audio, without = tmp_path / "with.mp4", tmp_path / "without.mp4"
    _counter(with_audio, audio=True)
    _counter(without, audio=False)
    for t0 in (0.05, 0.38, 0.71, 1.04):
        want = [int(np.floor((t0 + k / 30) * 24 + 1e-9)) for k in range(24)]
        got = [[int(round((f.mean() - 10) / 5)) for f in compare._frames(p, t0, t0 + 0.8, 64, 36, 30, gray=True)]
               for p in (with_audio, without)]
        assert got[0] == got[1] == want, t0


def _jump(path, at=12, dx=20, n=48):
    """24 fps, a textured ground that stands still except one jump of dx px at frame `at`, 160 x 90."""
    rng = np.random.default_rng(5)
    tex = np.asarray(Image.fromarray((rng.random((90, 120)) * 255).astype(np.uint8)).resize((240, 90), Image.NEAREST))
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "gray", "-s", "160x90", "-r", "24",
                          "-i", "-", "-c:v", "libx264", "-crf", "12", "-pix_fmt", "yuv420p", str(path)], stdin=subprocess.PIPE)
    for m in range(n):
        x0 = 40 - (dx if m >= at else 0)
        p.stdin.write(np.ascontiguousarray(tex[:, x0:x0 + 160]).tobytes())
    p.stdin.close()
    p.wait()


@needs_ffmpeg
def test_motion_is_seen_wherever_the_window_begins(tmp_path):
    # flow measured on every other pair of 30 fps frames saw a single jump or missed it whole, by the parity of the
    # window's start (mean flow 0.12 or 0.00 a frame apart); on every pair it reads the same from every start
    v = tmp_path / "jump.mp4"
    _jump(v)
    means = []
    for k in range(4):
        g = list(compare._frames(v, 0.1 + k / 30, 1.1 + k / 30, 160, 90, 30, gray=True))
        means.append(float(np.mean([np.linalg.norm(f, axis=1).mean() for _, f in compare._flow_cells(g)])))
    assert min(means) > 0.8 * max(means) > 0.03, means
