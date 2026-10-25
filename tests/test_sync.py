"""The beat-sync fingerprint (`moodreel sync`) and the camera tracked through a shot (`moodreel pose --track`), on
videos whose truth is known."""
from __future__ import annotations

import json
import shutil
import subprocess

import cv2
import numpy as np
import pytest

from moodreel.measure import pose, sync

needs_ffmpeg = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="needs ffmpeg")
FPS = 60


def _write(path, frames):
    h, w = frames[0].shape[:2]
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{w}x{h}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-crf", "12", "-pix_fmt", "yuv420p", str(path)], stdin=subprocess.PIPE)
    for f in frames:
        p.stdin.write(f.tobytes())
    p.stdin.close()
    p.wait()


def _ground(seed):
    rng = np.random.default_rng(seed)
    img = np.full((540, 960, 3), 14, np.uint8)
    for _ in range(140):
        x, y = rng.integers(0, 960), rng.integers(0, 540)
        end = (int(x + rng.integers(-120, 120)), int(y + rng.integers(-120, 120)))
        cv2.line(img, (int(x), int(y)), end, (220, 220, 220), 1, cv2.LINE_AA)
    return img


def _song(tmp_path, dur=8.0, bpm=120.0):
    beats = list(np.arange(0.5, dur, 60 / bpm))
    kicks = [[float(b), 1.0] for b in beats]
    words = [{"w": f"w{i}", "start": float(b + 0.25), "end": float(b + 0.45)} for i, b in enumerate(beats[::2])]
    audio = {"duration": dur, "bpm": bpm, "fps": 100, "beats": beats, "downbeats": beats[::4], "onsets": {"kick": kicks}}
    lyrics = [{"text": " ".join(w["w"] for w in words[i:i + 2]), "start": words[i]["start"],
               "end": words[min(i + 1, len(words) - 1)]["end"], "words": words[i:i + 2]} for i in range(0, len(words), 2)]
    (tmp_path / "music-data.js").write_text(f"export const AUDIO = {json.dumps(audio)};\nexport const LYRICS = {json.dumps(lyrics)};\n")
    return beats


def _film(beats, shake=True, dur=8.0):
    """A ground of lines that cuts to a new one on every other beat and shakes on every kick (8 px, half-life 0.05 s)."""
    grounds = [_ground(s) for s in range(8)]
    frames = []
    for f in range(int(dur * FPS)):
        t = f / FPS
        k = sum(1 for b in beats[::2] if b <= t)
        img = grounds[k % len(grounds)]
        last = max([b for b in beats if b <= t], default=-9)
        a = 8 * 0.5 ** ((t - last) / 0.05) if shake else 0.0
        r = np.random.default_rng(f)
        dx, dy = (r.uniform(-1, 1) * a, r.uniform(-1, 1) * a)
        M = np.float32([[1, 0, dx], [0, 1, dy]])
        frames.append(cv2.warpAffine(img, M, (960, 540), borderMode=cv2.BORDER_REFLECT))
    return frames


@needs_ffmpeg
def test_the_fingerprint_reads_a_shake_on_the_kick_and_cuts_on_the_beat(tmp_path):
    beats = _song(tmp_path)
    _write(tmp_path / "a.mp4", _film(beats))
    fp = sync.fingerprint(tmp_path / "a.mp4", tmp_path / "music-data.js")
    sh = fp["responses"]["kick"]["shake"]
    assert sh["z"] >= 3 and sh["latency_ms"] <= 34 and sh["peak"] > 2       # within two frames of the kick, clearly above chance
    cuts = fp["aligned"]["cut"]["beat"]
    assert cuts["share"] >= 0.8 and cuts["chance"] < 0.2 and abs(cuts["offset_ms"]) <= 17
    assert any("kick -> shake" in r for r in sync.recipe(fp))
    assert fp["kit_music"]["shake_px"] is not None


@needs_ffmpeg
def test_a_remake_without_the_shake_is_told_what_it_misses(tmp_path):
    beats = _song(tmp_path)
    _write(tmp_path / "ref.mp4", _film(beats))
    _write(tmp_path / "flat.mp4", _film(beats, shake=False))
    ref = sync.fingerprint(tmp_path / "ref.mp4", tmp_path / "music-data.js")
    d = sync.difference(ref, sync.fingerprint(tmp_path / "flat.mp4", tmp_path / "music-data.js"))
    assert any(x.startswith("missing: kick -> shake") for x in d["differences"])
    assert sync.difference(ref, ref)["similarity"] > 0.99 and not sync.difference(ref, ref)["differences"]


def _three_camera(pos, target, roll):
    back = (pos - target) / np.linalg.norm(pos - target)
    right = np.cross([0, 1, 0], back)
    right /= np.linalg.norm(right)
    up = np.cross(back, right)
    c, s = np.cos(roll), np.sin(roll)
    return right * c + up * s, -right * s + up * c, back


def _project(pos, axes, pts, fov=36, w=1280, h=720):
    right, up, back = axes
    R = np.stack([right, -up, -back])
    f = (h / 2) / np.tan(np.radians(fov) / 2)
    cam = (R @ (np.asarray(pts, float) - pos).T)
    return np.stack([w / 2 + f * cam[0] / cam[2], h / 2 + f * cam[1] / cam[2]], 1)


def test_the_world_frame_matches_three_js_cameras():
    wall = np.array([[-1, 0.5, 0], [1, 0.5, 0], [1, -0.5, 0], [-1, -0.5, 0]])           # 2 x 1, facing +Z: TL TR BR BL
    for pitch, yaw, dist, roll in ((0.45, -0.4, 3.5, -0.03), (0.9, 0.42, 4.0, 0.05)):
        pos = np.array([np.sin(yaw) * np.cos(pitch), np.sin(pitch), np.cos(yaw) * np.cos(pitch)]) * dist
        axes = _three_camera(pos, np.zeros(3), roll)
        r = pose.pose(_project(pos, axes, wall), 1280, 720, 2.0, 36, "wall")
        assert np.allclose(r["position"], pos, atol=0.01)
        assert abs(r["cam_pitch"] + np.degrees(pitch)) < 0.3 and abs(r["cam_roll"] - np.degrees(roll)) < 0.3
        assert abs(r["cam_yaw"] + np.degrees(yaw)) < 0.3                  # looking at the origin from +X turns toward -X
        assert abs(pose.pose(_project(pos, axes, wall), 1280, 720, 2.0, "shape", "wall")["fov"] - 36) < 0.5   # the lens from the shape


@needs_ffmpeg
def test_a_camera_is_tracked_through_a_shot(tmp_path):
    """A textured wall seen by a camera that orbits and closes in: the track follows it and gives the camera back."""
    tex = _ground(3)[:500, :, :]
    src = np.float32([[0, 0], [959, 0], [959, 479], [0, 479]])
    wall = np.array([[-1, 0.5, 0], [1, 0.5, 0], [1, -0.5, 0], [-1, -0.5, 0]])
    frames, truth = [], []
    for f in range(60):
        u = f / 59
        pitch, yaw, dist = 0.3 + 0.25 * u, -0.35 + 0.5 * u, 4.0 - 1.2 * u
        pos = np.array([np.sin(yaw) * np.cos(pitch), np.sin(pitch), np.cos(yaw) * np.cos(pitch)]) * dist
        axes = _three_camera(pos, np.zeros(3), 0.0)
        quad = _project(pos, axes, wall).astype(np.float32)
        frames.append(cv2.warpPerspective(tex[:480], cv2.getPerspectiveTransform(src, quad), (1280, 720)))
        truth.append((pos, quad))
    _write(tmp_path / "orbit.mp4", frames)
    res = pose.track(tmp_path / "orbit.mp4", 0.5, truth[30][1], 0.0, 1.0, aspect=2.0, fov=36, up="wall", smooth=1)
    assert res["covered"] > 0.9
    errs = [np.linalg.norm(np.array(r["position"]) - truth[min(59, round(r["t"] * FPS))][0]) for r in res["frames"]]
    assert np.median(errs) < 0.12                                          # within 3 % of the distance, most frames
    js = pose.camera_module(res)
    assert "export function cameraAt" in js and js.count("[") > 50
