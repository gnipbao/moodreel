"""kit/lock.js: a remake's camera and subjects moved so its subjects land in the reference's boxes (moodreel track)."""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
needs_three = pytest.mark.skipif(shutil.which("node") is None or not (REPO / "node_modules" / "three").exists(),
                                 reason="needs node and three.js (npm install)")


def _run(tmp_path, body: str) -> dict:
    from moodreel.pack.kit import vendor_three
    kit = tmp_path / "kit"
    kit.mkdir()
    for f in ("lock.js", "follow.js", "gl.js"):
        shutil.copyfile(REPO / "kit" / f, kit / f)
    vendor_three(kit)
    script = tmp_path / "t.mjs"
    script.write_text(f"import {{ lock, visible, visibleOf, moveCam }} from '{(kit / 'lock.js').as_uri()}';\n{body}")
    return json.loads(subprocess.run(["node", str(script)], capture_output=True, text=True, check=True).stdout)


@needs_three
def test_the_lock_finds_the_reference_camera_and_where_the_subject_stood(tmp_path):
    out = _run(tmp_path, """
const box = (x0, x1, y0, y1, z0, z1) => [[x0, y0, z0], [x1, y0, z0], [x0, y1, z0], [x1, y1, z0], [x0, y0, z1], [x1, y0, z1], [x0, y1, z1], [x1, y1, z1]];
const shift = (pts, d) => pts.map(q => q.map((v, k) => v + d[k]));
const A = box(-3, -1, 0, 1, -1, 1), B = box(2, 4, 0, 2, -2, 0), M = box(-0.5, 0.5, 0, 1, -0.5, 0.5), TRUE_D = [0.5, 0, -0.5];
const ref = { p: [0, 2, 10], l: [0, 1, 0], fov: 36, roll: 0 };          // the reference's camera
const row = (t, pts) => { const b = visible(ref, pts).box; return [t, 0.95, (b[0] + b[2]) / 2, (b[1] + b[3]) / 2, b[2] - b[0], b[3] - b[1]]; };
const times = [0, 0.125, 0.25, 0.375, 0.5, 0.625, 0.75, 0.875];
const TRACK = { A: times.map(t => row(t, A)), B: times.map(t => row(t, B)), M: times.map(t => row(t, shift(M, TRUE_D))) };
const ours = moveCam(ref, [1, 0.5, 1.2, 0.05, -0.03]);                    // the remake's camera, off
const L = lock(() => ours, TRACK, { set: { A: () => A, B: () => B }, moving: { M: { points: (t, d) => shift(M, d), axes: [0, 2] } } },
  { spans: [[0, 1, 0, 0]], keep: 0.002, keepMove: 0.001 });
console.log(JSON.stringify({ report: L.report.spans[0], cam: L.cam(0.5), move: L.move.M(0.5), outside: L.cam(2) }));
""")
    r = out["report"]
    assert r["samples"] == 8 and all(r["before"][k] > 20 for k in "ABM")
    assert all(r["after"][k] < 3 for k in "ABM")                          # px at 1080: each box where the reference has it
    assert out["move"] == pytest.approx([0.5, 0, -0.5], abs=0.1)          # the subject put back where it stood
    assert out["cam"]["p"] == pytest.approx([0, 2, 10], abs=0.3)
    assert out["outside"]["p"] == pytest.approx([1, 2.5, 11.2], abs=1e-6)  # outside its spans the camera is the remake's


@needs_three
def test_visible_is_what_the_frame_shows(tmp_path):
    out = _run(tmp_path, """
const box = (x0, x1, y0, y1, z0, z1) => [[x0, y0, z0], [x1, y0, z0], [x0, y1, z0], [x1, y1, z0], [x0, y0, z1], [x1, y0, z1], [x0, y1, z1], [x1, y1, z1]];
const c = { p: [0, 1, 0], l: [0, 1, -10], fov: 40, roll: 0 };
console.log(JSON.stringify({
  floor: visible(c, box(-50, 50, -1, 0, -60, 20)),       // a floor reaching behind the camera: the lower half, cut by the frame
  behind: visible(c, box(-1, 1, 0, 2, 5, 7)),            // all behind: nothing
  aside: visible(c, box(40, 42, 0, 2, -12, -10)),        // in front but outside the frame: its box, not in frame
}));
""")
    assert out["behind"] is None
    l, t, r, b = out["floor"]["box"]
    assert out["floor"]["inFrame"] and l == pytest.approx(0) and r == pytest.approx(1) and b == pytest.approx(1)
    assert 0.5 < t < 0.55                                                  # the horizon, a little below the middle
    assert out["aside"]["inFrame"] is False and out["aside"]["box"][0] > 1


@needs_three
def test_a_scattered_subject_is_boxed_by_its_points_in_the_frame(tmp_path):
    out = _run(tmp_path, """
const c = { p: [0, 10, 20], l: [0, 0, 0], fov: 40, roll: 0 };
// a river bending across the frame and far out of it: as a solid its hull would fill the frame; as a cloud, only its
// points in the frame count
const river = { cloud: Array.from({ length: 81 }, (_, i) => { const z = -40 + i; return [8 * Math.sin(z / 6), 0, z]; }) };
console.log(JSON.stringify({ cloud: visibleOf(c, river), solid: visibleOf(c, river.cloud) }));
""")
    cl, so = out["cloud"]["box"], out["solid"]["box"]
    assert out["cloud"]["inFrame"] and 0 <= cl[0] < cl[2] <= 1 and 0 <= cl[1] < cl[3] <= 1
    assert (cl[2] - cl[0]) * (cl[3] - cl[1]) <= (so[2] - so[0]) * (so[3] - so[1]) + 1e-9
