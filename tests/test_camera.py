"""`moodreel camera` (a film's camera read off its picture) and kit/follow.js (a remake's camera moved by it), on
pictures and tracks whose motion is known."""
from __future__ import annotations

import json
import math
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest

from moodreel.check import camera

REPO = Path(__file__).resolve().parents[1]
needs_ffmpeg = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="needs ffmpeg")
needs_node = pytest.mark.skipif(shutil.which("node") is None, reason="needs node")
W, H = 640, 360


def _texture(w, h, seed=3):
    import cv2
    rng = np.random.default_rng(seed)                            # smooth noise with edges, no period the flow could alias
    n = cv2.GaussianBlur(rng.integers(0, 255, (h, w, 3)).astype(np.float32), (0, 0), 2.5)
    n = (n - n.min()) / (n.max() - n.min()) * 255
    return np.clip((n - 128) * 2.2 + 128, 0, 255).astype(np.uint8)


def _write(path, frames, fps=30):
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(fps),
                          "-i", "-", "-c:v", "libx264", "-crf", "14", "-pix_fmt", "yuv420p", str(path)], stdin=subprocess.PIPE)
    for f in frames:
        p.stdin.write(np.ascontiguousarray(f).tobytes())
    p.stdin.close()
    p.wait()


def _pan(path, px_per_frame=3, n=45):
    big = _texture(W + px_per_frame * n + 16, H)
    _write(path, [big[:, px_per_frame * (n - i): px_per_frame * (n - i) + W] for i in range(n)])  # the picture moves right


def _push(path, rate=0.012, n=45):
    import cv2
    big = _texture(W, H, 5)
    frames = []
    for i in range(n):
        s = (1 + rate) ** i
        M = cv2.getRotationMatrix2D((W / 2, H / 2), 0, s)
        frames.append(cv2.warpAffine(big, M, (W, H), borderMode=cv2.BORDER_REFLECT))
    _write(path, frames)


@needs_ffmpeg
def test_a_pan_reads_its_direction_and_speed(tmp_path):
    v = tmp_path / "pan.mp4"
    _pan(v)
    r = camera.read(v, [(0.0, 1.4, "pan")], workers=1)[0]
    tot = camera.totals(r["track"])
    # 3 px a frame at 640 wide, 30 frames a second: 270 px/s at 1920, over the 1.4 s window about 380 px
    assert tot["x"] > 0 and abs(tot["x"] - 270 * 1.4) / (270 * 1.4) < 0.3
    assert abs(tot["y"]) < 60 and abs(tot["push"]) < 6
    turn, tilt = camera.turn(tot, fov=36)
    assert turn < 0                                               # the picture moving right: the camera turned left


@needs_ffmpeg
def test_a_push_reads_as_growth(tmp_path):
    v = tmp_path / "push.mp4"
    _push(v)
    tot = camera.totals(camera.read(v, [(0.0, 1.4, "push")], workers=1)[0]["track"])
    expected = ((1.012 ** 30) ** 1.4 - 1) * 100                  # 1.2 % a frame, 30 frames a second
    assert tot["push"] > 0 and abs(tot["push"] - expected) / expected < 0.35
    assert abs(tot["x"]) < 80


def test_turn_converts_travel_at_a_field_of_view():
    f = 540 / math.tan(math.radians(18))
    assert camera.turn({"x": f, "y": 0}, 36)[0] == pytest.approx(-45.0, abs=0.1)
    assert camera.turn({"x": 0, "y": f}, 36)[1] == pytest.approx(45.0, abs=0.1)   # the picture moving down: tilting up


def test_verdict_names_what_is_off():
    ref = {"x": 489, "y": 0, "push": 0.5, "roll": 0}
    assert "pans the other way" in camera.verdict(ref, {"x": -300, "y": 0, "push": 0, "roll": 0})
    assert "doesn't pan" in camera.verdict(ref, {"x": 20, "y": 0, "push": 0, "roll": 0})
    assert camera.verdict(ref, {"x": 380, "y": 10, "push": 3, "roll": 0}) == []
    pull = {"x": 0, "y": 0, "push": -63, "roll": -30}
    off = camera.verdict(pull, {"x": 0, "y": 0, "push": 40, "roll": 0})
    assert "pushes in where the reference pulls out" in off and "doesn't roll" in off
    still = {"x": 5, "y": 0, "push": 0.3, "roll": 0}
    assert camera.verdict(still, {"x": 600, "y": 0, "push": 0, "roll": 0}) == ["moves where the reference holds still"]


def test_track_rows_lays_windows_end_to_end_and_writes_a_module(tmp_path):
    rows = [{"t0": 0.0, "t1": 1.0, "track": [[300, 0, 0, 0]] * 15}, {"t0": 1.0, "t1": 2.0, "track": [None] * 15}]
    out = camera.track_rows(rows, 2.0)
    assert len(out) == 32 and out[7][0] == 300 and out[22][0] == 0   # smoothed within a window, not across
    js = camera.write_js(out, tmp_path / "camera-data.js", "ref.mp4").read_text()
    assert js.startswith("// The reference's camera") and "export const MOTION = { fps: 15, rows: [[" in js


@needs_node
def test_follow_meets_its_anchors_and_turns_as_measured(tmp_path):
    # the picture moves 300 px/s right for 2 s: at fov 36 the camera turns left by 600 / f rad between the anchors' aims
    script = tmp_path / "follow.mjs"
    script.write_text(f"""import {{ follow }} from '{(REPO / 'kit' / 'follow.js').as_uri()}';
const rows = Array.from({{ length: 60 }}, (_, i) => i < 30 ? [300, 0, 0, 0] : [0, 0, 0, 0]);
const M = {{ fps: 15, rows }};
const a = [[0, {{ p: [0, 0, 0], l: [0, 0, -10], fov: 36 }}]];
const free = follow(M, a, 4);                                     // one anchor: the measured turn alone
const pinned = follow(M, [...a, [3, {{ p: [5, 0, 0], l: [5, 0, -10] }}]], 4);
const own = follow(M, a, 4, {{ own: [[0, 4]] }});                  // a span keyed by hand: no measured turn
const yaw = c => Math.atan2(c.l[0] - c.p[0], -(c.l[2] - c.p[2]));
console.log(JSON.stringify({{ free2: yaw(free(2)), pinned3: pinned(3), own2: yaw(own(2)) }}));
""")
    out = json.loads(subprocess.run(["node", str(script)], capture_output=True, text=True, check=True).stdout)
    f = 540 / math.tan(math.radians(18))
    assert out["free2"] == pytest.approx(-600 / f, abs=0.02)
    assert out["pinned3"]["p"] == pytest.approx([5, 0, 0], abs=1e-6) and out["pinned3"]["l"] == pytest.approx([5, 0, -10], abs=1e-6)
    assert out["own2"] == pytest.approx(0, abs=1e-9)
