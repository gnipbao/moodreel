"""Contact sheets: references tiled with labels, and video frames with their times, for the director to read."""
from __future__ import annotations

import subprocess
from pathlib import Path

import cv2
import numpy as np


def _label(img, text):
    img = img.copy()
    cv2.rectangle(img, (0, 0), (min(img.shape[1], 10 + 9 * len(text)), 22), (0, 0, 0), -1)
    cv2.putText(img, text, (5, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
    return img


def fit_cell(rgb: np.ndarray, cell: int) -> np.ndarray:
    """Letterbox into a square cell."""
    h, w = rgb.shape[:2]
    k = cell / max(h, w)
    small = cv2.resize(rgb, (max(1, round(w * k)), max(1, round(h * k))), interpolation=cv2.INTER_AREA)
    out = np.full((cell, cell, 3), 24, np.uint8)
    y, x = (cell - small.shape[0]) // 2, (cell - small.shape[1]) // 2
    out[y:y + small.shape[0], x:x + small.shape[1]] = small
    return out


def stack(pictures: list[np.ndarray], width: int = 512) -> np.ndarray:
    """Pictures one above the other at one width, no borders: one picture to measure several by."""
    return np.vstack([cv2.resize(p, (width, max(1, round(p.shape[0] * width / p.shape[1]))), interpolation=cv2.INTER_AREA)
                      for p in pictures])


def grid(tiles: list[np.ndarray], cols: int) -> np.ndarray:
    cell = tiles[0].shape[0]
    rows = -(-len(tiles) // cols)
    out = np.full((rows * cell, cols * cell, 3), 24, np.uint8)
    for i, t in enumerate(tiles):
        r, c = divmod(i, cols)
        out[r * cell:(r + 1) * cell, c * cell:(c + 1) * cell] = t
    return out


def video_frames(path: str, times: list[float]) -> list[np.ndarray]:
    out = []
    for t in times:
        r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", path, "-frames:v", "1", "-f", "image2pipe",
                            "-vcodec", "png", "-"], capture_output=True)
        if r.stdout:
            img = cv2.imdecode(np.frombuffer(r.stdout, np.uint8), cv2.IMREAD_COLOR)
            out.append(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    return out


def write(path: Path, rgb: np.ndarray, quality: int = 88) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(path), cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, quality])
    return path


def references(items: list[tuple[str, np.ndarray]], path: Path, cell: int = 320, cols: int = 4) -> Path:
    tiles = [_label(fit_cell(img, cell), name) for name, img in items]
    return write(path, grid(tiles, min(cols, len(tiles))))


def side_by_side(left: np.ndarray, rights: list[np.ndarray], path: Path, cell: int = 480,
                 labels=("ours", "reference")) -> Path:
    tiles = [_label(fit_cell(left, cell), labels[0])] + [_label(fit_cell(r, cell), f"{labels[1]} {i + 1}")
                                                          for i, r in enumerate(rights)]
    return write(path, grid(tiles, len(tiles)))
