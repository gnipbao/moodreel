"""The renderer: every frame of the film is the page's drawing at that frame's time, and a page error stops it."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[1]
RENDER = REPO / "render" / "render.mjs"
needs = pytest.mark.skipif(shutil.which("node") is None or shutil.which("ffmpeg") is None
                           or not (REPO / "node_modules" / "puppeteer-core").exists(), reason="needs node, ffmpeg and npm install")

# frame f fills the screen with grey 20 + 8 f: a screenshot a frame late (or early) is 8 levels off
PAGE = """<!doctype html><html><body style="margin:0"><canvas width="160" height="90"></canvas><script>
const g = document.querySelector('canvas').getContext('2d');
window.DUR = __DUR__;
window.render = t => {
  if (t > __THROW__) throw new Error('drawing failed at ' + t.toFixed(2));
  const v = 20 + 8 * Math.round(t * 24);
  g.fillStyle = `rgb(${v},${v},${v})`;
  g.fillRect(0, 0, 160, 90);
};
window.READY = true;
</script></body></html>
"""


def _page(d: Path, dur=1.0, throw_after=99.0) -> Path:
    d.mkdir()
    (d / "index.html").write_text(PAGE.replace("__DUR__", str(dur)).replace("__THROW__", str(throw_after)))
    return d


@needs
def test_each_frame_is_the_page_at_its_own_time(tmp_path):
    film, out = _page(tmp_path / "film"), tmp_path / "film.mp4"
    subprocess.run(["node", str(RENDER), "video", str(film), "--fps", "24", "--size", "160x90", "--workers", "2",
                    "--out", str(out)], check=True, capture_output=True, timeout=120)
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(out), "-f", "rawvideo", "-pix_fmt", "gray", "-"],
                         check=True, capture_output=True).stdout
    frames = np.frombuffer(raw, np.uint8).reshape(-1, 90, 160)
    assert len(frames) == 24
    assert np.abs(frames.reshape(24, -1).mean(axis=1) - (20 + 8 * np.arange(24))).max() < 2.5


@needs
def test_a_page_error_stops_the_render(tmp_path):
    film, out = _page(tmp_path / "film", dur=2.0, throw_after=1.0), tmp_path / "film.mp4"
    r = subprocess.run(["node", str(RENDER), "video", str(film), "--fps", "24", "--size", "160x90", "--workers", "2",
                        "--out", str(out)], capture_output=True, text=True, timeout=120)
    assert r.returncode == 1 and "drawing failed at" in r.stderr and not out.exists()
    assert not [p for p in tmp_path.iterdir() if p.name.startswith(".segments-")]
