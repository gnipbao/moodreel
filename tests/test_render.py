"""The renderer: every frame of the film is the page's drawing at that frame's time, and a page error stops it, with
either engine (Chrome's screenshots, FrameVelo's hardware encoder); a variant reaches the page through FrameVelo too."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import json
import platform

import numpy as np
import pytest

REPO = Path(__file__).resolve().parents[1]
RENDER = REPO / "render" / "render.mjs"
needs = pytest.mark.skipif(shutil.which("node") is None or shutil.which("ffmpeg") is None
                           or not (REPO / "node_modules" / "puppeteer-core").exists(), reason="needs node, ffmpeg and npm install")
FRAMEVELO = (REPO / "node_modules" / "framevelo" / "dist" / "index.js").exists() and platform.system() == "Darwin"
ENGINES = ["chrome", pytest.param("framevelo", marks=pytest.mark.skipif(not FRAMEVELO, reason="FrameVelo runs on macOS"))]

# frame f fills the screen with grey 20 + 8 f: a screenshot a frame late (or early) is 8 levels off
PAGE = """<!doctype html><html><body style="margin:0"><canvas width="160" height="90"></canvas><script>
const g = document.querySelector('canvas').getContext('2d');
window.DUR = __DUR__;
window.render = t => {
  if (t > __THROW__) throw new Error('drawing failed at ' + t.toFixed(2));
  const v = (window.VARIANT || {}).grey ?? 20 + 8 * Math.round(t * 24);
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


def _greys(out: Path) -> np.ndarray:
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(out), "-f", "rawvideo", "-pix_fmt", "gray", "-"],
                         check=True, capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, 90, 160).reshape(-1, 90 * 160).mean(axis=1)


@needs
@pytest.mark.parametrize("engine", ENGINES)
def test_each_frame_is_the_page_at_its_own_time(tmp_path, engine):
    film, out = _page(tmp_path / "film"), tmp_path / "film.mp4"
    subprocess.run(["node", str(RENDER), "video", str(film), "--fps", "24", "--size", "160x90", "--workers", "2",
                    "--engine", engine, "--out", str(out)], check=True, capture_output=True, timeout=120)
    greys = _greys(out)
    assert len(greys) == 24
    assert np.abs(greys - (20 + 8 * np.arange(24))).max() < 2.5


@needs
@pytest.mark.parametrize("engine", ENGINES)
def test_a_page_error_stops_the_render(tmp_path, engine):
    film, out = _page(tmp_path / "film", dur=2.0, throw_after=1.0), tmp_path / "film.mp4"
    r = subprocess.run(["node", str(RENDER), "video", str(film), "--fps", "24", "--size", "160x90", "--workers", "2",
                        "--engine", engine, "--out", str(out)], capture_output=True, text=True, timeout=120)
    assert r.returncode == 1 and "drawing failed at" in r.stderr and not out.exists()
    assert not [p for p in tmp_path.iterdir() if p.name.startswith(".segments-")]
    assert not [p for p in film.iterdir() if p.name.startswith(".framevelo-")]          # the entry page is cleaned up


@needs
@pytest.mark.skipif(not FRAMEVELO, reason="FrameVelo runs on macOS")
def test_a_variant_reaches_the_page_through_framevelo(tmp_path):
    film, out = _page(tmp_path / "film"), tmp_path / "film.mp4"
    subprocess.run(["node", str(RENDER), "video", str(film), "--fps", "24", "--size", "160x90", "--engine", "framevelo",
                    "--variant", json.dumps({"grey": 200}), "--out", str(out)], check=True, capture_output=True, timeout=120)
    assert np.abs(_greys(out) - 200).max() < 2.5
