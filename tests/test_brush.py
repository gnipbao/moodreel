"""Brush marks: a picture laid in short marks running one way is read with its direction; a flat design and grain
aren't marks. The kit's stroke geometry (spine, ribbon, wobble) is checked in node."""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import cv2
import numpy as np
import pytest

from moodreel.measure import brush, texture

REPO = Path(__file__).resolve().parents[1]


def _painted(angle_deg=30, seed=2):
    """Thousands of short dabs in three earth colours, each turned about `angle_deg` (+/- 12)."""
    rng = np.random.default_rng(seed)
    img = np.full((720, 1280, 3), (200, 170, 120), np.uint8)
    for _ in range(9000):
        x, y = rng.uniform(0, 1280), rng.uniform(0, 720)
        a = np.radians(angle_deg + rng.normal(0, 12))
        L, Wd = rng.uniform(14, 26), rng.uniform(6, 10)
        box = cv2.boxPoints(((x, y), (L, Wd), np.degrees(a))).astype(np.int32)
        colour = rng.choice([[176, 98, 60], [222, 190, 128], [94, 120, 70]]) + rng.integers(-12, 12, 3)
        cv2.fillConvexPoly(img, box, tuple(int(v) for v in colour))
    return img


def test_marks_running_one_way_are_read_with_their_direction():
    m = brush.read(texture._work(_painted(30)))
    assert m and abs(m["direction_deg"] - 30) < 8 and m["agreement"] > 0.5 and m["coverage"] > 0.5


def test_a_flat_design_and_grain_are_not_marks():
    flat = np.full((720, 1280, 3), 240, np.uint8)
    cv2.rectangle(flat, (100, 100), (600, 400), (30, 30, 30), -1)
    cv2.circle(flat, (900, 360), 200, (200, 40, 40), -1)
    cv2.putText(flat, "FLAT DESIGN", (120, 600), cv2.FONT_HERSHEY_DUPLEX, 3, (20, 20, 20), 6, cv2.LINE_AA)
    grain = np.clip(flat.astype(np.int16) + np.random.default_rng(1).normal(0, 18, flat.shape[:2])[..., None], 0, 255).astype(np.uint8)
    assert brush.read(texture._work(flat)) is None and brush.read(texture._work(grain)) is None


@pytest.mark.skipif(shutil.which("node") is None, reason="needs node")
def test_stroke_geometry(tmp_path):
    js = tmp_path / "t.mjs"
    js.write_text(f"import {{ spine, ribbon, wobble }} from '{(REPO / 'kit' / 'brush.js').as_uri()}';\n"
                  "const sp = spine([[0, 0], [100, 0], [200, 0]], 21);\n"
                  "const rb = ribbon([[0, 0], [200, 0]], { width: 20, profile: 'even', rough: 0 });\n"
                  "const wb = wobble([[0, 0], [100, 0], [100, 100], [0, 100]], { amount: 4, step: 10, seed: 3 });\n"
                  "console.log(JSON.stringify({ ends: [sp[0], sp[20]], ys: sp.map(p => p[1]),\n"
                  "  half: Math.max(...rb.map(p => Math.abs(p[1]))), n: wb.length,\n"
                  "  off: Math.max(...wb.slice(1, 10).map(p => Math.abs(p[1]))) }));\n")    # the top edge's 10 steps
    out = json.loads(subprocess.run(["node", str(js)], capture_output=True, text=True, check=True).stdout)
    assert out["ends"] == [[0, 0], [200, 0]] and max(abs(y) for y in out["ys"]) < 1e-9   # a straight spine stays straight
    assert abs(out["half"] - 10) < 1e-6                                                 # an even profile: half the width
    assert out["n"] == 40 and 0 < out["off"] <= 4                                        # every edge broken, within amount
