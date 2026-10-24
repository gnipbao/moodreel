"""The GPU layer (kit/gl.js), glyph outlines (kit/outline.js), the time helpers (kit/anim.js), the stage's prepare step,
and `moodreel compare` on videos whose differences are known."""
from __future__ import annotations

import json
import shutil
import struct
import subprocess
from pathlib import Path

import cv2
import numpy as np
import pytest

from moodreel.check import compare

REPO = Path(__file__).resolve().parents[1]
has_three = (REPO / "node_modules" / "three" / "build" / "three.module.js").exists()
needs_node = pytest.mark.skipif(shutil.which("node") is None, reason="needs node")
needs_three = pytest.mark.skipif(not has_three or shutil.which("node") is None, reason="needs npm install")


def _page(tmp_path, main, kit=("stage.js",), three=False):
    d = tmp_path / "page"
    (d / "kit").mkdir(parents=True)
    for f in kit:
        shutil.copyfile(REPO / "kit" / f, d / "kit" / f)
    if three:
        from moodreel.pack.kit import vendor_three
        vendor_three(d / "kit")
    (d / "index.html").write_text('<!doctype html><html><body><script type="module" src="main.js"></script></body></html>')
    (d / "main.js").write_text(main)
    return d


def _still(d, t="0.5", size="320x180"):
    subprocess.run(["node", str(REPO / "render" / "render.mjs"), "still", str(d), t, "--size", size, "--out", str(d / "out")],
                   check=True, capture_output=True, timeout=120)
    return cv2.imread(str(d / "out" / f"t_{t}.jpg")).astype(int)


GL_PAGE = """import { stage } from './kit/stage.js';
import { gpu } from './kit/gl.js';
const G = gpu(640, 360);
// the right half burns orange past 1 (it blooms); a bone hairline crosses the left half
const scene = G.pass(`void main() { fragColor = vec4(C_SIGNAL * 1.6 * step(0.5, vUv.x) + C_INK, 1.0); }`);
const hdr = G.rt(), L = G.lines(16);
stage({ width: 640, height: 360, duration: 1, draw: (g, t) => {
  scene.render(hdr);
  L.clear(); L.seg2(20, 80, 300, 80, 3, [0.85, 0.82, 0.76]); L.render(hdr);
  G.post(hdr.texture, { bloom: 0.8, vignette: 0 });
  G.show(g);
} });
"""


@needs_three
def test_the_gpu_layer_draws_a_pass_hairlines_and_a_post_that_blooms_only_the_bright(tmp_path):
    img = _still(_page(tmp_path, GL_PAGE, ("stage.js", "gl.js", "three.js"), three=True), size="640x360")
    right, left = img[170:190, 480:560].mean(axis=(0, 1)), img[260:300, 20:80].mean(axis=(0, 1))
    assert right[2] > 200 and right[2] > right[1] + 60 > right[0] + 60      # orange (BGR): past 1, under the white shoulder
    assert left[2] < right[2] / 3                                         # the far side of the ink ground stays dark
    assert img[76:85, 80:240].mean(axis=(1, 2)).max() > 150 > img[100:110, 80:240].mean()   # the hairline, lit, and only it
    near, far = img[260:300, 300:316, 2].mean(), img[260:300, 20:36, 2].mean()
    assert near > far + 15                                                 # the bloom spills over the edge of the bright half


def _ttf(path: Path):
    """A minimal TrueType font: 'A' a square with one off-curve corner, 'B' that square halved and moved (composite)."""
    upm, n = 1000, 3
    pts = [(0, 0, 1), (100, 0, 1), (100, 100, 0), (0, 100, 1)]
    flags = bytes(f for *_, f in pts)
    dx = [pts[0][0]] + [pts[i][0] - pts[i - 1][0] for i in range(1, 4)]
    dy = [pts[0][1]] + [pts[i][1] - pts[i - 1][1] for i in range(1, 4)]
    g1 = struct.pack(">hhhhhH", 1, 0, 0, 100, 100, 3) + struct.pack(">H", 0) + flags \
        + b"".join(struct.pack(">h", v) for v in dx) + b"".join(struct.pack(">h", v) for v in dy)
    g2 = struct.pack(">hhhhh", -1, 200, 50, 250, 100) + struct.pack(">HHhhh", 0x0B, 1, 200, 50, 8192)
    glyphs = [b"", g1 + b"\0" * (len(g1) % 2), g2 + b"\0" * (len(g2) % 2)]
    offs = [0]
    for g in glyphs:
        offs.append(offs[-1] + len(g))
    seg = [(0x41, 0x42, 1 - 0x41), (0xFFFF, 0xFFFF, 1)]
    sub = struct.pack(">HHHHHHH", 4, 16 + 8 * len(seg), 0, 2 * len(seg), 0, 0, 0) \
        + b"".join(struct.pack(">H", e) for _, e, _ in seg) + b"\0\0" \
        + b"".join(struct.pack(">H", s) for s, _, _ in seg) + b"".join(struct.pack(">h", d) for *_, d in seg) \
        + b"\0\0" * len(seg)
    tables = {
        b"cmap": struct.pack(">HHHHI", 0, 1, 3, 1, 12) + sub,
        b"glyf": b"".join(glyphs),
        b"head": struct.pack(">IIIIHH", 0x10000, 0, 0, 0x5F0F3CF5, 0, upm) + b"\0" * 16
        + struct.pack(">hhhhHHhhh", 0, 0, 250, 100, 0, 8, 2, 0, 0),
        b"hhea": struct.pack(">I", 0x10000) + b"\0" * 30 + struct.pack(">H", n),
        b"hmtx": b"".join(struct.pack(">Hh", a, 0) for a in (500, 600, 700)),
        b"loca": b"".join(struct.pack(">H", o // 2) for o in offs),
        b"maxp": struct.pack(">IH", 0x5000, n),
    }
    head = struct.pack(">IHHHH", 0x10000, len(tables), 0, 0, 0)
    off, recs, body = 12 + 16 * len(tables), b"", b""
    for tag, data in tables.items():
        data += b"\0" * (-len(data) % 4)
        recs += struct.pack(">4sIII", tag, 0, off + len(body), len(data))
        body += data
    path.write_bytes(head + recs + body)


@needs_node
def test_glyph_outlines_from_a_truetype_file_simple_and_composite(tmp_path):
    _ttf(tmp_path / "t.ttf")
    js = tmp_path / "o.mjs"
    js.write_text(f"import {{ readFileSync }} from 'node:fs';\nimport {{ outline }} from '{(REPO / 'kit' / 'outline.js').as_uri()}';\n"
                  f"const b = readFileSync('{tmp_path / 't.ttf'}');\n"
                  "const f = outline(b.buffer.slice(b.byteOffset, b.byteOffset + b.byteLength));\n"
                  "const A = f.charToGlyph('A'), B = f.charToGlyph('B');\n"
                  "console.log(JSON.stringify({ a: A.getPath(0, 0, 1000).commands, b: B.getPath(10, 20, 2000).commands,"
                  " adv: [A.advanceWidth, B.advanceWidth], none: f.charToGlyph('Z').getPath().commands.length, upm: f.unitsPerEm }));\n")
    r = json.loads(subprocess.run(["node", str(js)], capture_output=True, text=True, check=True).stdout)
    assert r["upm"] == 1000 and r["adv"] == [600, 700] and r["none"] == 0
    a = r["a"]
    assert [c["type"] for c in a] == ["M", "L", "Q", "L", "Z"]                  # the off-curve corner is a quadratic
    assert (a[0]["x"], a[0]["y"]) == (0, 0) and (a[1]["x"], a[1]["y"]) == (100, 0)
    assert (a[2]["x1"], a[2]["y1"], a[2]["x"], a[2]["y"]) == (100, -100, 0, -100)  # y down
    b = r["b"]                                                                   # half size, moved (200, 50), drawn at 2x
    assert (b[0]["x"], b[0]["y"]) == (10 + 400, 20 - 100) and (b[2]["x1"], b[2]["y1"]) == (10 + 500, 20 - 200)


@needs_node
def test_the_time_helpers(tmp_path):
    js = tmp_path / "a.mjs"
    js.write_text(f"import * as A from '{(REPO / 'kit' / 'anim.js').as_uri()}';\n"
                  "const P = A.path([{ x: 0, y: 0 }, { x: 30, y: 0 }, { x: 30, y: 40 }]);\n"
                  "console.log(JSON.stringify([A.pulse(1.24, 1, 0.12), A.pulse(0.9, 1), A.prog(1.5, 1, 2, A.ease.inQuad),"
                  " A.springStep(0, 4), Math.max(...[0.05, 0.1, 0.15].map(t => A.springStep(t, 4, 0.35))),"
                  " A.keys(1.5, [[0, 0], [1, 10], [2, 20, A.ease.linear]]), A.frameIdx(1.004), A.frameIdx(1.012),"
                  " A.hash(3, 4) === A.hash(3, 4), P.length, P.at(50), A.window01(5, 0, 10, 1, 1)]));\n")
    r = json.loads(subprocess.run(["node", str(js)], capture_output=True, text=True, check=True).stdout)
    assert abs(r[0] - 0.25) < 1e-9 and r[1] == 0 and abs(r[2] - 0.25) < 1e-9 and r[3] == 0
    assert r[4] > 1.05                                                           # a spring overshoots
    assert abs(r[5] - 15) < 1e-9 and r[6] == 60 and r[7] == 61 and r[8] is True
    assert r[9] == 70 and abs(r[10]["x"] - 30) < 1e-9 and abs(r[10]["y"] - 20) < 1e-9 and abs(r[10]["angle"] - np.pi / 2) < 1e-9
    assert r[11] == 1


PREPARE_PAGE = """import { stage } from './kit/stage.js';
let colour = '#0000ff';
stage({ width: 320, height: 180, duration: 1,
  prepare: async () => { await new Promise(ok => setTimeout(ok, 50)); colour = '#ff0000'; },
  draw: (g, t) => { g.fillStyle = colour; g.fillRect(0, 0, 320, 180); } });
"""


@needs_node
def test_the_stage_prepares_before_the_first_frame(tmp_path):
    img = _still(_page(tmp_path, PREPARE_PAGE))
    b, g, r = img[90, 160]
    assert r > 200 and b < 60


def _video(path, filters, size="160x90", dur=3):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"testsrc2=size={size}:rate=30:duration={dur}",
                    "-vf", filters, "-pix_fmt", "yuv420p", str(path)], check=True)


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="needs ffmpeg")
def test_compare_tells_a_copy_from_a_mirror_and_a_blur(tmp_path):
    pan = "scroll=horizontal=0.008,scale=320:180"
    _video(tmp_path / "ref.mp4", pan)
    _video(tmp_path / "copy.mp4", pan)
    _video(tmp_path / "mirror.mp4", pan + ",hflip")
    _video(tmp_path / "soft.mp4", pan + ",boxblur=4")
    shots = [[0.2, 2.8, "all"]]
    same = compare.compare(tmp_path / "ref.mp4", tmp_path / "copy.mp4", shots)["windows"][0]
    mirror = compare.compare(tmp_path / "ref.mp4", tmp_path / "mirror.mp4", shots)["windows"][0]
    soft = compare.compare(tmp_path / "ref.mp4", tmp_path / "soft.mp4", shots)["windows"][0]
    assert same["structure"] > 0.95 and same["flow"] > 0.9 and abs(same["speed"] - 1) < 0.1 and not same["problems"]
    assert mirror["flow"] < 0 and "moving another way" in mirror["problems"]
    assert soft["detail"] < 0.8 and "softer, less detail" in soft["problems"] and soft["score"] < same["score"]


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="needs ffmpeg")
def test_compare_finds_the_references_cuts(tmp_path):
    _video(tmp_path / "a.mp4", "scale=320:180", dur=2)
    _video(tmp_path / "b.mp4", "negate,hflip,scale=320:180", dur=2)
    (tmp_path / "l.txt").write_text(f"file '{tmp_path / 'a.mp4'}'\nfile '{tmp_path / 'b.mp4'}'\n")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(tmp_path / "l.txt"), "-c", "copy",
                    str(tmp_path / "ab.mp4")], check=True)
    cs = compare.cuts(tmp_path / "ab.mp4")
    assert len(cs) == 1 and abs(cs[0] - 2.0) < 0.05
    assert [round(a, 1) for a, _, _ in compare.windows(tmp_path / "ab.mp4")] == [0.0, 2.0]
