"""Decode a video once into an RGB array at analysis width."""
from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from fractions import Fraction

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
