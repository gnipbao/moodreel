"""`moodreel probe` (a shot's numbers off full-size frames) and compare's grain, on pictures whose truth is known."""
from __future__ import annotations

import shutil
import subprocess

import cv2
import numpy as np
import pytest

from moodreel.check import compare, probe

needs_ffmpeg = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="needs ffmpeg")
W, H = 640, 360


def _write(path, frames, fps=30):
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(fps),
                          "-i", "-", "-c:v", "libx264", "-crf", "12", "-pix_fmt", "yuv420p", str(path)], stdin=subprocess.PIPE)
    for f in frames:
        p.stdin.write(f.tobytes())
    p.stdin.close()
    p.wait()


def _slash(angle_deg, ground=245, ink=20, grid=0):
    """A light frame with a dark rounded bar leaning `angle_deg` from vertical, top to the right; a cell grid if asked."""
    f = np.full((H, W, 3), ground, np.uint8)
    if grid:
        f[::grid, :] = ground - 30
        f[:, ::grid] = ground - 30
    a = np.radians(angle_deg)
    dx, dy = np.sin(a) * 90, -np.cos(a) * 90
    cv2.line(f, (int(320 - dx), int(180 - dy)), (int(320 + dx), int(180 + dy)), (ink,) * 3, 14, cv2.LINE_AA)
    return f


def test_a_bar_reads_its_lean_length_and_width():
    n = probe.numbers([_slash(25)])
    assert abs(n["bar"]["angle"] - 25) < 1.5
    assert 185 < n["bar"]["length"] < 205 and 11 < n["bar"]["width"] < 17
    assert abs(probe.numbers([_slash(-20)])["bar"]["angle"] + 20) < 1.5      # leaning the other way: "\"


def test_a_cell_grid_reads_its_period_and_phase():
    n = probe.numbers([_slash(25, grid=16)])
    assert n["cells"]["x"]["period"] == 16 and n["cells"]["y"]["period"] == 16
    assert n["cells"]["x"]["phase"] == 0 and n["cells"]["x"]["strength"] > 0.5


def test_lit_share_and_box_on_a_dark_frame():
    f = np.zeros((H, W, 3), np.uint8)
    f[100:200, 300:500] = 200
    n = probe.numbers([f])
    assert abs(n["lit"] - 100 * 200 * 100 / (W * H)) < 0.5
    assert np.allclose(n["box"], [300, 100, 499, 199], atol=2)          # 0.5-99.5 percentile: robust to strays
    assert n["colour"][0] == pytest.approx(200 * 200 * 100 / (W * H), abs=0.2)


def test_still_tells_a_fixed_grain_from_a_boiling_one():
    rng = np.random.default_rng(1)
    base = _slash(25)
    fixed = np.clip(base + rng.normal(0, 6, base.shape), 0, 255).astype(np.uint8)
    boiling = [np.clip(base + rng.normal(0, 6, base.shape), 0, 255).astype(np.uint8) for _ in range(5)]
    assert probe.numbers([fixed] * 5)["still"] == 0
    assert probe.numbers(boiling)["still"] > 2


@needs_ffmpeg
def test_probe_reads_a_reference_beside_its_remake(tmp_path):
    rng = np.random.default_rng(2)
    ref, ours = tmp_path / "ref.mp4", tmp_path / "ours.mp4"
    _write(ref, [_slash(28 - 6 * k / 59) for k in range(60)])                      # a slash turning upright, grain fixed
    _write(ours, [np.clip(_slash(28.0) + rng.normal(0, 8, (H, W, 3)), 0, 255).astype(np.uint8) for _ in range(60)])
    res = probe.run(ref, [0.0, 1.9], ours, sheet=tmp_path / "sheet.jpg")
    first, last = res["times"]
    assert abs(first["reference"]["bar"]["angle"] - 28) < 1.5 and abs(last["reference"]["bar"]["angle"] - 22.2) < 1.5
    assert abs(last["remake"]["bar"]["angle"] - 28) < 1.5                          # the remake forgot to turn
    assert first["reference"]["still"] < 0.1 and first["remake"]["still"] > 1
    assert (tmp_path / "sheet.jpg").stat().st_size > 1000
    assert "remake" in probe.report(res)


def test_compare_names_a_grain_that_boils_over_a_still_reference():
    assert "grain boils where the reference's holds still" in compare.problems({"grain": [0.0, 0.67]})
    assert not any("grain" in p for p in compare.problems({"grain": [0.0, 0.05]}))
    assert not any("grain" in p for p in compare.problems({"grain": [0.6, 0.67]}))      # both boil: as it should
