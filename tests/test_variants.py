"""Batch variants: one film delivered as several, each with film.json's parameters as window.VARIANT."""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest

from moodreel.film import film

REPO = Path(__file__).resolve().parents[1]

MAIN = """import { stage } from './kit/stage.js';
import { pick } from './kit/variant.js';
stage({ width: 320, height: 180, duration: pick('duration', 1), draw: (g, t) => {
  g.fillStyle = pick('ground', '#222222'); g.fillRect(0, 0, 320, 180);
}});
"""


@pytest.mark.skipif(shutil.which("node") is None or not (REPO / "node_modules" / "puppeteer-core").exists(),
                    reason="needs node and npm install")
def test_every_variant_renders_with_its_own_parameters(tmp_path):
    d = film.new("vary", "swiss-motion", root=tmp_path, duration=1, size="320x180", fps=12)
    f = json.loads((d / "film.json").read_text())
    f["variants"] = {"red": {"ground": "#c83228"}, "blue": {"ground": "#2850c8", "duration": 0.5, "poster": 0.25}}
    (d / "film.json").write_text(json.dumps(f))
    (d / "main.js").write_text(MAIN)
    for name, want, seconds in (("red", [200, 50, 40], 1.0), ("blue", [40, 80, 200], 0.5)):
        film.deliver(d, variant=name)
        clip = d / f"vary-{name}.mp4"
        dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(clip)],
                                   capture_output=True, text=True).stdout)
        rgb = np.frombuffer(subprocess.run(["ffmpeg", "-v", "error", "-i", str(clip), "-frames:v", "1", "-vf", "scale=1:1",
                                            "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout, np.uint8)
        assert abs(dur - seconds) < 0.1 and np.abs(rgb.astype(int) - want).max() < 12 and (d / f"poster-{name}.jpg").exists()
    with pytest.raises(SystemExit):
        film.deliver(d, variant="green")
