"""The frame-by-frame list (`moodreel.check.diff`) on a clip drawn here and a "remake" of it with known faults: a cut
five frames late, a cut turned into a dissolve, eight black frames, the sound 100 ms late and the end cut short; and
the clip against itself, which has nothing to fix."""
from __future__ import annotations

import shutil
import subprocess

import cv2
import numpy as np
import pytest

from moodreel.check import diff

needs_ffmpeg = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="needs ffmpeg")
# clips go into ffmpeg's own container (.nut), whose clock keeps every frame on its exact time
W, H, FPS, N = 480, 270, 24, 120
CLICKS = (0.31, 1.07, 1.83, 2.4, 2.9, 3.62, 4.15, 4.71)       # uneven, so only one lag lines them up


def _texture(seed):
    rng = np.random.default_rng(seed)
    img = np.zeros((H, W + 240, 3), np.float32)
    for s in (40, 12, 4):
        img += cv2.resize(rng.random((H // s + 2, (W + 240) // s + 2, 3)).astype(np.float32), (W + 240, H),
                          interpolation=cv2.INTER_CUBIC) * (s / 56)
    return np.clip(img / img.max() * 255, 0, 255).astype(np.uint8)


def _reference():
    shots = [_texture(1), _texture(2), _texture(3)]
    start = lambda i: 0 if i < 30 else 30 if i < 60 else 60  # noqa: E731
    return [shots[start(i) // 30][:, (i - start(i)) * 4:(i - start(i)) * 4 + W].copy() for i in range(N)]


def _remake(ref):
    out = []
    for i in range(N - 6):                               # the end cut short by six frames
        f = ref[i]
        if 30 <= i < 35:
            f = ref[29]                                  # the first cut comes five frames late
        if 56 <= i < 64:                                 # the second cut turned into a dissolve
            k = (i - 55) / 9
            f = (ref[55] * (1 - k) + ref[64] * k).astype(np.uint8)
        if 76 <= i < 84:
            f = np.zeros_like(f)                         # eight black frames
        out.append(f)
    return out


def _write(frames, path, delay_ms=0):
    gate = "+".join(f"between(t,{c},{c + 0.02})" for c in CLICKS)
    audio = f"aevalsrc='if({gate},sin(2*PI*900*t),0)':s=48000:d={N / FPS}"
    af = ["-af", f"adelay={delay_ms}"] if delay_ms else []
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                          "-f", "lavfi", "-i", audio, *af, "-c:v", "libx264", "-crf", "12", "-pix_fmt", "yuv420p", "-c:a", "aac",
                          "-shortest", str(path)], stdin=subprocess.PIPE)
    for f in frames:
        p.stdin.write(np.ascontiguousarray(f).tobytes())
    p.stdin.close()
    p.wait()


@needs_ffmpeg
def test_every_planted_fault_is_listed_on_its_frame(tmp_path):
    ref = _reference()
    _write(ref, tmp_path / "ref.nut")
    _write(_remake(ref), tmp_path / "remake.nut", delay_ms=100)
    r = diff.run(tmp_path / "ref.nut", tmp_path / "remake.nut", shots=[[0, 1.25, "a"], [1.25, 2.5, "b"], [2.5, 5, "c"]], out=tmp_path / "d")
    c = r["cuts"]
    assert any(m["reference"] == 30 and 4 <= m["off"] <= 6 for m in c["matched"]), c
    assert c["missed"] == [60] and c["missed_how"]["60"] == "dissolve", c
    assert sorted(c["extra"]) == [76, 84] or all(any(abs(g - e) <= 1 for e in (76, 84)) for g in c["extra"]), c
    assert any(b["what"] == "black" and abs(b["start"] - 76) <= 1 and abs(b["end"] - 84) <= 1 for b in r["blanks"]), r["blanks"]
    assert r["audio"]["offset_ms"] is not None and abs(r["audio"]["offset_ms"] - 100) <= 21, r["audio"]
    assert abs(r["duration"]["difference"] + 6 / FPS) < 1e-3, r["duration"]
    for name in ("diff.json", "DIFF.md", "worst.jpg"):
        assert (tmp_path / "d" / name).exists()
    md = (tmp_path / "d" / "DIFF.md").read_text()
    assert "5 frames late" in md and "missed, the remake dissolves there instead" in md and "100 ms late" in md


@needs_ffmpeg
def test_a_film_against_itself_has_nothing_to_fix(tmp_path):
    _write(_reference(), tmp_path / "ref.nut")
    r = diff.run(tmp_path / "ref.nut", tmp_path / "ref.nut")
    assert not r["cuts"]["missed"] and not r["cuts"]["extra"] and all(m["off"] == 0 for m in r["cuts"]["matched"])
    assert len(r["cuts"]["matched"]) == 2 and abs(r["audio"]["offset_ms"]) <= 21 and not r["blanks"]
    assert "nothing: every cut on its frame" in diff.report(r)
