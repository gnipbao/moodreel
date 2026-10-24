"""Reading shots as code: the camera from a rectangle (`moodreel pose`), and each shot's motion, linework and technique
hints (`moodreel dossier`) on pictures and videos whose truth is known."""
from __future__ import annotations

import shutil
import subprocess

import cv2
import numpy as np
import pytest

from moodreel.measure import pose, shot

needs_ffmpeg = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="needs ffmpeg")


def _seen(pitch, yaw, dist, fov=40, w=1280, h=720, aspect=1.6):
    """A rectangle seen by a known camera: its four corners in the image."""
    f = (h / 2) / np.tan(np.radians(fov) / 2)
    K = np.array([[f, 0, w / 2], [0, f, h / 2], [0, 0, 1]])
    a, b = np.radians(90 - pitch), np.radians(yaw)
    R = np.array([[1, 0, 0], [0, np.cos(a), -np.sin(a)], [0, np.sin(a), np.cos(a)]]) @ \
        np.array([[np.cos(b), -np.sin(b), 0], [np.sin(b), np.cos(b), 0], [0, 0, 1]])
    obj = np.array([[-aspect / 2, -0.5, 0], [aspect / 2, -0.5, 0], [aspect / 2, 0.5, 0], [-aspect / 2, 0.5, 0]])
    img, _ = cv2.projectPoints(obj, cv2.Rodrigues(R)[0], np.array([0.05, -0.04, dist]), K, None)
    return img.reshape(4, 2)


@pytest.mark.parametrize("pitch,yaw,dist", [(50, 20, 3.0), (70, -35, 2.2), (35, 10, 4.0)])
def test_the_camera_from_a_rectangle(pitch, yaw, dist):
    r = pose.pose(_seen(pitch, yaw, dist), 1280, 720, 1.6)
    assert abs(r["pitch"] - pitch) < 0.5 and abs(r["fov"] - 40) < 0.5 and r["fov_measured"]
    assert abs(r["dist"] - np.hypot(np.hypot(0.05, 0.04), dist)) < 0.02 and r["reprojection_px"] < 0.5
    solved = pose.pose(_seen(pitch, yaw, dist), 1280, 720, None)
    assert abs(solved["aspect"] - 1.6) < 0.02                            # the rectangle's own shape, solved
    given = pose.pose(_seen(pitch, yaw, dist), 1280, 720, 1.6, fov=40)
    assert not given["fov_measured"] and abs(given["pitch"] - pitch) < 0.5


def test_rectangles_are_found_and_a_grid_is_drawn(tmp_path):
    img = np.zeros((720, 1280, 3), np.uint8)
    q = _seen(55, 15, 2.5).astype(np.int32)
    cv2.polylines(img, [q], True, (230, 230, 230), 3, cv2.LINE_AA)
    found = pose.candidates(img, 3)
    assert found and min(np.abs(np.roll(np.array(found[0]), k, axis=0) - q).max() for k in range(4)) < 8
    cv2.imwrite(str(tmp_path / "f.png"), img)
    out = pose.grid(tmp_path / "f.png", tmp_path / "g.png")
    g = cv2.imread(str(out))
    assert g.shape == img.shape and g[100, 3].sum() > 0 and g[3, 200].sum() > 0     # rules at every 50 px


def _video(path, filters, dur=2, src="testsrc2"):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"{src}=size=640x360:rate=30:duration={dur}",
                    "-vf", filters, "-pix_fmt", "yuv420p", str(path)], check=True)


@needs_ffmpeg
def test_the_dossier_reads_a_push_a_roll_and_a_pan(tmp_path):
    _video(tmp_path / "push.mp4", "scale=1280:720,zoompan=z='1+0.006*on':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d=1:s=640x360:fps=30")
    _video(tmp_path / "roll.mp4", "scale=900:900,rotate=a='0.6*t':ow=640:oh=360")
    _video(tmp_path / "pan.mp4", "scroll=horizontal=0.004")
    push = shot.read_shot(tmp_path / "push.mp4", 0.1, 1.9)["motion"]
    roll = shot.read_shot(tmp_path / "roll.mp4", 0.1, 1.9)["motion"]
    pan = shot.read_shot(tmp_path / "pan.mp4", 0.1, 1.9)["motion"]
    assert push["zoom"] > 8 and abs(push["roll"]) < 3                     # 0.6 % a frame at 30 fps: about 18 %/s, in
    assert 25 < roll["roll"] < 45 and abs(roll["zoom"]) < 4              # 0.6 rad/s = 34 deg/s, clockwise on screen
    assert pan["pan"][0] < -20 and abs(pan["pan"][1]) < 15 and abs(pan["zoom"]) < 3   # the picture slides left
    hints = shot.hints(shot.read_shot(tmp_path / "push.mp4", 0.1, 1.9))
    assert any(h.startswith("push in") for h in hints)


@needs_ffmpeg
def test_the_dossier_sees_hatching_and_lines_and_a_still_frame(tmp_path):
    img = np.full((720, 1280, 3), 12, np.uint8)
    for x in range(-720, 1280, 9):                                        # dense diagonal hatching over most of the frame
        cv2.line(img, (x, 0), (x + 720, 720), (225, 225, 225), 1, cv2.LINE_AA)
    cv2.imwrite(str(tmp_path / "h.png"), img)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-i", str(tmp_path / "h.png"), "-t", "1.5", "-r", "30",
                    "-pix_fmt", "yuv420p", str(tmp_path / "h.mp4")], check=True)
    s = shot.read_shot(tmp_path / "h.mp4", 0.1, 1.4, tmp_path / "out", "h")
    assert s["linework"]["hatched"] > 0.3 and s["linework"]["width"] <= 4.5
    assert any(h.startswith("hatching") for h in s["hints"]) and any(h.startswith("a line-heavy") for h in s["hints"])
    assert not s["motion"]["moving"]
    assert (tmp_path / "out" / "h-keys.jpg").exists() and (tmp_path / "out" / "h-flow.jpg").exists()
    p = shot.pooled([s, s])
    assert p["shots"] == 2 and p["techniques"]["hatching"] == 1.0 and p["techniques"]["3d camera"] == 0.0
    assert "hatching 100%" in shot.pooled_lines(p)[1]
