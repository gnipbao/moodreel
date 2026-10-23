"""3D: a film in a style that needs it gets three.js with its licence, and the renderer draws its WebGL layer."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import cv2
import numpy as np
import pytest

from moodreel.film import film

REPO = Path(__file__).resolve().parents[1]
needs = pytest.mark.skipif(not (REPO / "node_modules" / "three" / "build" / "three.module.js").exists()
                           or shutil.which("node") is None, reason="needs npm install")

PAGE = """import { stage } from './kit/stage.js';
import { layer3d, orbit, THREE } from './kit/three.js';
const L = layer3d(320, 180, { background: '#203040' });
L.scene.add(new THREE.AmbientLight('#ffffff', 0.4));
const key = new THREE.DirectionalLight('#ffffff', 2.5);
key.position.set(3, 4, 5);
L.scene.add(key);
const cube = new THREE.Mesh(new THREE.BoxGeometry(1.6, 1.6, 1.6), new THREE.MeshStandardMaterial({ color: '#e07a5f' }));
L.scene.add(cube);
stage({ width: 320, height: 180, duration: 1, draw: (g, t) => { L.look(orbit(t, 5, 2)); cube.rotation.y = t; L.draw(g); } });
"""


@needs
def test_a_3d_film_gets_three_and_draws_it(tmp_path):
    d = film.new("cube", "lowpoly-island", root=tmp_path, duration=1, size="320x180")
    assert {p.name for p in (d / "kit" / "vendor" / "three").iterdir()} == {"three.module.js", "three.core.js", "LICENSE"}
    assert "three.js" in (d / "CREDITS").read_text() and (d / "kit" / "three.js").exists()
    (d / "main.js").write_text(PAGE)
    subprocess.run(["node", str(REPO / "render" / "render.mjs"), "still", str(d), "0.5", "--size", "320x180",
                    "--out", str(d / "out")], check=True, capture_output=True, timeout=120)
    img = cv2.imread(str(d / "out" / "t_0.5.jpg")).astype(int)
    centre, corner = img[80:100, 150:170].mean(axis=(0, 1)), img[5:15, 5:15].mean(axis=(0, 1))
    assert np.abs(corner - [0x40, 0x30, 0x20]).max() < 12           # the scene's background (BGR)
    assert centre[2] > centre[0] + 40                                # a lit orange cube in the middle
