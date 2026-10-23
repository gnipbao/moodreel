"""Export to HyperFrames: the composition carries the film's size and length, packs the film's source (not its work
folder or deliverables), and seeking its timeline draws the film's own frame."""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from moodreel import export
from moodreel.film import film

REPO = Path(__file__).resolve().parents[1]

MAIN = """import { stage } from './kit/stage.js';
import { pick } from './kit/variant.js';
stage({ width: 320, height: 180, duration: 2, draw: (g, t) => {
  g.fillStyle = pick('ground', '#000000'); g.fillRect(0, 0, 320, 180);
  g.fillStyle = '#ffffff'; g.fillRect(0, 0, 320 * t / 2, 180);         // a bar as long as the time
}});
"""

# GSAP stand-in for the test (no network): a paused timeline that, on seek, sets each tweened property as GSAP does
STUB = """window.gsap = { timeline: () => { const tw = [];
  return { to(o, v, at) { tw.push([o, v]); return this; },
           seek(t) { for (const [o, v] of tw) o.t = Math.min(t, v.duration) / v.duration * v.t; return this; } }; } };"""

PROBE = """import http from 'node:http'; import fs from 'node:fs'; import path from 'node:path';
import puppeteer from 'puppeteer-core';
const root = process.argv[2];
const s = http.createServer((req, res) => { const f = path.join(root, decodeURIComponent(new URL(req.url, 'http://x').pathname));
  const type = f.endsWith('.js') ? 'text/javascript' : 'text/html';
  fs.readFile(f, (e, d) => e ? res.writeHead(404).end() : res.writeHead(200, { 'Content-Type': type }).end(d)); });
await new Promise(r => s.listen(0, '127.0.0.1', r));
const browser = await puppeteer.launch({ executablePath: await (await import('puppeteer')).default.executablePath(), headless: true });
const page = await browser.newPage();
await page.setViewport({ width: 320, height: 180 });
await page.setRequestInterception(true);
page.on('request', r => r.url().includes('gsap') ? r.respond({ contentType: 'text/javascript', body: process.argv[3] }) : r.continue());
await page.evaluateOnNewDocument(() => { window.__timelines = {}; });
await page.goto('http://127.0.0.1:' + s.address().port + '/index.html');
await page.waitForFunction(() => window.__timelines.main, { polling: 50 });
const out = await page.evaluate(() => [0.5, 1.5].map(t => { window.__timelines.main.seek(t);
  const c = document.querySelector('#moodreel-stage canvas'), d = c.getContext('2d').getImageData(0, 90, c.width, 1).data;
  let lit = 0; for (let i = 0; i < d.length; i += 4) lit += d[i] > 128; return [c.width, c.height, lit]; }));
console.log(JSON.stringify(out));
await browser.close(); s.close();
"""


def _film(tmp_path):
    d = film.new("clip", "swiss-motion", root=tmp_path, duration=2, size="320x180", fps=12)
    f = json.loads((d / "film.json").read_text())
    f["variants"] = {"red": {"ground": "#c83228"}}
    (d / "film.json").write_text(json.dumps(f))
    (d / "main.js").write_text(MAIN)
    (d / "out" / "mix.wav").parent.mkdir(exist_ok=True)
    (d / "out" / "mix.wav").write_bytes(b"RIFF")
    (d / "clip.mp4").write_bytes(b"")
    return d


def test_the_composition_carries_the_films_size_length_and_source(tmp_path):
    d = _film(tmp_path)
    r = export.hyperframes(d, tmp_path / "hf")
    page = (tmp_path / "hf" / "index.html").read_text()
    root = re.search(r'<div id="root"([^>]*)>', page).group(1)
    assert 'data-composition-id="main"' in root and 'data-width="320"' in root and 'data-height="180"' in root
    assert 'data-duration="2"' in root and '<base href="film/" />' in page and "__timelines['main']" in page
    assert r["audio"] and '<audio id="moodreel-audio" src="audio.wav"' in page
    packed = {p.name for p in (tmp_path / "hf" / "film").iterdir()}
    assert {"main.js", "kit", "film.json", "audio.wav"} <= packed and not {"out", "clip.mp4", "build.sh"} & packed
    red = (export.hyperframes(d, tmp_path / "hf-red", "red"), (tmp_path / "hf-red" / "index.html").read_text())[1]
    assert 'window.VARIANT = {"ground": "#c83228"}' in red


@pytest.mark.skipif(shutil.which("node") is None or not (REPO / "node_modules" / "puppeteer-core").exists(),
                    reason="needs node and npm install")
def test_seeking_the_timeline_draws_the_films_frame(tmp_path):
    d = _film(tmp_path)
    export.hyperframes(d, tmp_path / "hf")
    probe = REPO / "out" / f"probe-{tmp_path.name}.mjs"                 # beside node_modules, so puppeteer resolves
    probe.parent.mkdir(exist_ok=True)
    probe.write_text(PROBE)
    try:
        out = json.loads(subprocess.run(["node", str(probe), str(tmp_path / "hf"), STUB], capture_output=True, text=True,
                                        check=True, timeout=120).stdout)
    finally:
        probe.unlink()
    assert out[0][:2] == [320, 180] and abs(out[0][2] - 80) <= 2 and abs(out[1][2] - 240) <= 2   # t / 2 of the width
