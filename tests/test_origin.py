"""How each shot was made (`moodreel origin`), on clips drawn here: a designed frame (flat fills, type, a card that
slides), a photographic one (texture everywhere, sensor noise, a hand-held wobble), and a figure held on twos while the
camera pans on ones. Each clip goes into ffmpeg's own container (.nut)."""
from __future__ import annotations

import json
import shutil
import subprocess

import cv2
import numpy as np
import pytest

from moodreel.check import origin

needs_ffmpeg = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="needs ffmpeg")
W, H, FPS = 480, 270, 24


def _write(frames, path):
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-crf", "14", "-pix_fmt", "yuv420p", str(path)], stdin=subprocess.PIPE)
    for f in frames:
        p.stdin.write(np.ascontiguousarray(f).tobytes())
    p.stdin.close()
    p.wait()


def _designed():
    out = []
    for i in range(48):
        f = np.full((H, W, 3), (236, 228, 210), np.uint8)
        cv2.rectangle(f, (40 + i * 4, 90), (200 + i * 4, 180), (30, 60, 200), -1)
        cv2.putText(f, "LAUNCH", (250, 230), cv2.FONT_HERSHEY_SIMPLEX, 1.4, (20, 20, 20), 3)
        cv2.line(f, (20, 40), (460, 40), (20, 20, 20), 2)
        out.append(f)
    return out


def _photo(seed=4):
    rng = np.random.default_rng(seed)
    big = np.zeros((H + 40, W + 40, 3), np.float32)
    for s in (60, 20, 6, 2):
        big += cv2.resize(rng.random(((H + 40) // s + 2, (W + 40) // s + 2, 3)).astype(np.float32), (W + 40, H + 40),
                          interpolation=cv2.INTER_CUBIC) * (s ** 0.5)
    big = (big - big.min()) / (big.max() - big.min()) * 220 + 15
    out = []
    for i in range(48):
        dx, dy = int(20 + 6 * np.sin(i * 0.7)), int(20 + 5 * np.cos(i * 0.9))     # a hand-held wobble
        f = big[dy:dy + H, dx:dx + W] + rng.normal(0, 4, (H, W, 3))               # sensor noise, new every frame
        out.append(np.clip(f, 0, 255).astype(np.uint8))
    return out


def _twos_under_a_pan():
    rng = np.random.default_rng(7)
    ground = cv2.GaussianBlur((rng.random((H, W + 200, 3)) * 255).astype(np.uint8), (0, 0), 3)
    ground = cv2.addWeighted(ground, 0.5, np.full_like(ground, 128), 0.5, 0)
    sprite = np.zeros((90, 90, 3), np.uint8)                                      # a figure with markings of its own
    sprite[::2] = (230, 80, 40)
    sprite[1::2] = (250, 200, 60)
    sprite[:, ::12] = (30, 30, 120)
    out = []
    for i in range(72):
        f = ground[:, i * 2: i * 2 + W].copy()                                    # the camera pans on ones
        x = 20 + (i // 2) * 10                                                    # the figure moves on twos
        f[90:180, x:x + 90] = sprite
        out.append(f)
    return out


@needs_ffmpeg
def test_a_designed_frame_is_graphics_drawn_in_canvas(tmp_path):
    _write(_designed(), tmp_path / "designed.nut")
    r = origin.run(tmp_path / "designed.nut", out=tmp_path / "o")
    assert [s["kind"] for s in r["shots"]] == ["graphics"] and r["shots"][0]["route"] == "canvas"
    assert (tmp_path / "o" / "origin.json").exists() and (tmp_path / "o" / "strips" / "shot-000.jpg").exists()
    md = (tmp_path / "o" / "ORIGIN.md").read_text()
    assert "graphics" in md and "canvas" in md and json.loads((tmp_path / "o" / "origin.json").read_text())["summary"]["graphics"] == 1.0


@needs_ffmpeg
def test_a_photographic_shot_is_footage(tmp_path):
    _write(_photo(), tmp_path / "photo.nut")
    s = origin.run(tmp_path / "photo.nut")["shots"][0]
    assert s["kind"] == "footage" and s["route"] == "footage", s
    assert s["texture"]["straight"] < 0.1 and s["texture"]["busy"] > 0.45


@needs_ffmpeg
def test_a_subject_on_twos_under_a_camera_on_ones(tmp_path):
    _write(_twos_under_a_pan(), tmp_path / "twos.nut")
    c = origin.run(tmp_path / "twos.nut")["shots"][0]["cadence"]
    assert c["subject_on"] == 2 and c["camera_on"] == 1, c


def test_routes_follow_the_kind_and_the_cadence():
    shot = {"texture": {"busy": 0.2, "colours": 90}, "cadence": {"subject_on": 2}}
    assert origin.route("render_3d", shot) == "three+assets"
    shot["cadence"]["subject_on"] = 1
    assert origin.route("render_3d", shot) == "three" and origin.route("graphics", shot) == "canvas"
    assert origin.route("footage", shot) == "footage"
