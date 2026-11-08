"""Decode a video once into an RGB array at analysis width."""
from __future__ import annotations

import json
import math
import subprocess
from dataclasses import dataclass
from fractions import Fraction
from functools import lru_cache

import numpy as np


@dataclass
class Clip:
    path: str
    fps: float
    src_w: int
    src_h: int
    frames: np.ndarray          # (N, h, w, 3) uint8, RGB, at analysis width
    scale: float                # source px per analysis px

    @property
    def n(self):
        return len(self.frames)

    @property
    def w(self):
        return self.frames.shape[2]

    @property
    def h(self):
        return self.frames.shape[1]

    def t(self, i):
        return i / self.fps


def probe(path: str) -> dict:
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height,r_frame_rate", "-of", "json", path],
                         check=True, capture_output=True, text=True).stdout
    s = json.loads(out)["streams"][0]
    return {"w": s["width"], "h": s["height"], "fps": float(Fraction(s["r_frame_rate"]))}


def load(path: str, width: int = 640) -> Clip:
    p = probe(path)
    width = min(width, p["w"])
    height = int(round(p["h"] * width / p["w"] / 2) * 2)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vf", f"scale={width}:{height}:flags=area",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], check=True, capture_output=True).stdout
    frames = np.frombuffer(bytearray(raw), np.uint8).reshape(-1, height, width, 3)   # writable: shots get stabilised in place
    return Clip(path, p["fps"], p["w"], p["h"], frames, p["w"] / width)


@lru_cache(maxsize=64)
def _video_start(path: str) -> float:
    """The first timestamp of the first video stream, in seconds (0 for most files)."""
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=start_time",
                          "-of", "csv=p=0", path], check=True, capture_output=True, text=True).stdout.strip()
    try:
        return float(out.split(",")[0])
    except ValueError:
        return 0.0


def window(path: str, t0: float, t1: float, fps: float, w: int, h: int, pix_fmt: str = "bgr24") -> np.ndarray:
    """Frames of [t0, t1) at `fps`: frame k is the picture on screen at t0 + k / fps (the last frame of the video that
    starts at or before that moment), ceil((t1 - t0) * fps) of them unless the video ends first, scaled to w x h.

    The sampling is set by the times alone. Left to ffmpeg (-ss before -i, -t, the fps filter's defaults), where the
    resampling starts depended on the file: the same pictures with and without an audio track came out one 30 fps
    frame apart in some windows. Here the input keeps its timestamps (-copyts), the window's start becomes time 0
    (setpts), and the fps filter fills each output time with the last frame already shown (round=up), from 0."""
    n = max(0, math.ceil((t1 - t0) * fps - 1e-6))
    if n == 0:
        return np.zeros((0, h, w) if pix_fmt == "gray" else (0, h, w, 3), np.uint8)
    pre = max(0.0, t0 - 1.0)                                 # seek a second early: the frame on screen at t0 began before it
    zero = _video_start(str(path)) + t0
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{pre:.6f}", "-copyts", "-i", str(path), "-map", "0:v:0",
                          "-vf", f"setpts=PTS-{zero:.6f}/TB,fps=fps={fps}:start_time=0:round=up,scale={w}:{h}:flags=area",
                          "-fps_mode", "passthrough", "-frames:v", str(n), "-pix_fmt", pix_fmt, "-f", "rawvideo", "-"],
                         capture_output=True, check=True).stdout
    size = w * h * (1 if pix_fmt == "gray" else 3)
    k = len(raw) // size
    return np.frombuffer(raw[:k * size], np.uint8).reshape((k, h, w) if pix_fmt == "gray" else (k, h, w, 3))
