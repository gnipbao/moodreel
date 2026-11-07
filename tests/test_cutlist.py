"""Cuts to the frame (`moodreel.check.cutlist`) on a clip drawn here whose every event is known: two hard cuts between
textured shots (one panning, one on twos), light that brightens, a two-frame flash, an empty grid ground that turns
plain, a title that pops onto a plain ground, and a dissolve."""
from __future__ import annotations

import shutil
import subprocess

import cv2
import numpy as np
import pytest

from moodreel.check import cutlist

# clips go into ffmpeg's own container (.nut); x264's B-frames start the stream two frames late, which must not shift
# the frame count
needs_ffmpeg = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="needs ffmpeg")
W, H, FPS = 480, 270, 24


def _texture(seed, w=W + 200, h=H):
    rng = np.random.default_rng(seed)
    img = np.zeros((h, w, 3), np.float32)
    for s in (40, 12, 4):
        n = cv2.resize(rng.random((h // s + 2, w // s + 2, 3)).astype(np.float32), (w, h), interpolation=cv2.INTER_CUBIC)
        img += n * (s / 56)
    return np.clip(img / img.max() * 255, 0, 255).astype(np.uint8)


def _clip():
    a, b, e = _texture(1), _texture(2), _texture(3)
    grey = np.full((H, W, 3), 60, np.uint8)
    grid = grey.copy()
    grid[::24] = 72
    grid[:, ::24] = 72
    frames = []
    for i in range(132):
        if i < 36:                                    # shot A: the camera pans, a disc moves on twos
            f = a[:, i * 3: i * 3 + W].copy()
            cv2.circle(f, (60 + (i // 2) * 16, 140), 22, (250, 250, 250), -1)
        elif i < 72:                                  # shot B: still; the light comes up at 54, a flash at 60-61
            f = b[:, :W].copy()
            if i >= 54:
                f = np.clip(f.astype(np.float32) * 1.25 + 10, 0, 255).astype(np.uint8)
            if i in (60, 61):
                f = np.full_like(f, 255)
        elif i < 90:                                  # shot C: an empty grid ground
            f = grid.copy()
        elif i < 108:                                 # shot D: a plain ground; a title pops on at 100
            f = grey.copy()
            if i >= 100:
                cv2.putText(f, "TITLE", (150, 150), cv2.FONT_HERSHEY_SIMPLEX, 2, (240, 240, 240), 5)
        else:                                         # a dissolve 108-119 into shot E
            k = min(1.0, (i - 107) / 12)
            d = grey.copy()
            cv2.putText(d, "TITLE", (150, 150), cv2.FONT_HERSHEY_SIMPLEX, 2, (240, 240, 240), 5)
            f = (d * (1 - k) + e[:, :W] * k).astype(np.uint8)
        frames.append(f)
    return frames


def _write(frames, path):
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-crf", "12", "-pix_fmt", "yuv420p", str(path)], stdin=subprocess.PIPE)
    for f in frames:
        p.stdin.write(np.ascontiguousarray(f).tobytes())
    p.stdin.close()
    p.wait()


@needs_ffmpeg
def test_cuts_to_the_frame_and_nothing_else(tmp_path):
    path = tmp_path / "events.nut"
    _write(_clip(), path)
    r = cutlist.find(str(path))
    assert r["fps"] == FPS and r["n"] == 132
    assert r["cuts"] == [36, 72, 90], r            # two hard cuts and the faint one, each on its first frame; not the
    assert r["flashes"] == [60], r                 # light coming up, the flash or the title
    assert any(a <= 113 <= b for a, b in r["dissolves"]), r
