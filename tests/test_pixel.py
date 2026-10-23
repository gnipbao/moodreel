"""Pixel art: a picture scaled up by whole pixels is read back with its scale, palette and dither; the kit's palette
tables reduce colour depth and step light along ramps."""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import cv2
import numpy as np
import pytest

from moodreel.measure import pixel

REPO = Path(__file__).resolve().parents[1]
PALETTE = np.array([[26, 28, 44], [93, 39, 93], [177, 62, 83], [239, 125, 87], [255, 205, 117], [56, 183, 100],
                    [37, 113, 121], [41, 54, 111], [59, 93, 201], [244, 244, 244]], np.uint8)


def _art(seed=1, scale=5, w=96, h=54):
    """A low-res picture of flat blocks, one dithered gradient band, and a few sprites; scaled up with no smoothing."""
    rng = np.random.default_rng(seed)
    idx = np.zeros((h, w), int)
    idx[: h // 2] = 7
    for y in range(h // 2, h):                             # a dithered band between two colours
        for x in range(w):
            idx[y, x] = 5 if (x + y) % 2 and y < h * 3 // 4 else 6
    for _ in range(8):
        x, y = rng.integers(0, w - 6), rng.integers(0, h - 6)
        idx[y:y + 5, x:x + 4] = rng.choice([1, 2, 3, 4, 9])
    img = PALETTE[idx]
    return cv2.resize(img, (w * scale, h * scale), interpolation=cv2.INTER_NEAREST)


def test_pixel_art_is_read_with_its_scale_palette_and_dither():
    img = _art()
    _, jpg = cv2.imencode(".jpg", cv2.cvtColor(img, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 92])
    for picture in (img, cv2.cvtColor(cv2.imdecode(jpg, cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGB)):   # also through JPEG
        r = pixel.read(picture)
        assert r and r["scale"] == 5 and r["native"] == [96, 54] and r["dither"]
        assert abs(r["palette_size"] - len(np.unique(PALETTE[[1, 2, 3, 4, 5, 6, 7, 9]], axis=0))) <= 2


def test_a_smooth_picture_is_not_pixel_art():
    y, x = np.mgrid[0:540, 0:960]
    img = np.dstack([x * 255 // 960, y * 255 // 540, np.full_like(x, 120)]).astype(np.uint8)
    cv2.circle(img, (480, 270), 130, (240, 200, 60), -1, cv2.LINE_AA)
    cv2.putText(img, "VECTOR", (300, 120), cv2.FONT_HERSHEY_DUPLEX, 3, (20, 20, 20), 6, cv2.LINE_AA)
    assert pixel.read(img) is None


@pytest.mark.skipif(shutil.which("node") is None, reason="needs node")
def test_palette_tables(tmp_path):
    js = tmp_path / "t.mjs"
    js.write_text(f"import {{ reduce, stepTable, nearest }} from '{(REPO / 'kit' / 'pixel.js').as_uri()}';\n"
                  "const P = ['#000000', '#555555', '#aaaaaa', '#ffffff', '#ff0000'];\n"
                  "console.log(JSON.stringify([reduce(P, [0, 3]), stepTable(5, [[0, 1, 2, 3]], 1), stepTable(5, [[0, 1, 2, 3]], -1),"
                  " nearest(P, [250, 10, 10])]));\n")
    out = json.loads(subprocess.run(["node", str(js)], capture_output=True, text=True, check=True).stdout)
    assert out == [[0, 0, 3, 3, 0], [1, 2, 3, 3, 4], [0, 0, 1, 2, 4], 4]
