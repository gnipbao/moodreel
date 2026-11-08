"""SDF characters: the fields measure distance, the mesher closes every surface and lands on it, poses match three.js,
the export reads back, the checks find what is loose or sunk in, and figure.js agrees with Python in the browser."""
from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import cv2
import numpy as np
import pytest

from moodreel import cli
from moodreel.model3d import build, check, export, mannequin, mesh, sdf, sheet, skin

REPO = Path(__file__).resolve().parents[1]
browser = pytest.mark.skipif(not (REPO / "node_modules" / "three" / "build" / "three.module.js").exists()
                             or shutil.which("node") is None, reason="needs npm install")

# a body, an arm of two bones that touches it (1 mm gap) and a pebble that touches nothing; "fold" swings the arm
# 131.41 degrees about its joint, which takes the arm's axis to 0.15 m from the body's centre: 30 mm into it
ARM_SPEC = '''
from moodreel.model3d import sdf
from moodreel.model3d.build import Part
NAME = "arm"
BONES = {"chest": (None, (0.0, 0.0, 0.0)), "upper": ("chest", (0.2, 0.0, 0.0)), "lower": ("upper", (0.45, 0.0, 0.0)),
         "tip": ("lower", (0.7, 0.0, 0.0))}
PARTS = {"body": Part(sdf.sphere(0.15), "chest", "body"),
         "upper": Part(sdf.capsule((0.181, 0.0, 0.0), (0.45, 0.0, 0.0), 0.03), "upper", "body"),
         "lower": Part(sdf.capsule((0.45, 0.0, 0.0), (0.7, 0.0, 0.0), 0.025), "lower", "body"),
         "pebble": Part(sdf.sphere(0.02, (0.0, 0.4, 0.0)), "chest", "stone")}
POSES = {"rest": {}, "fold": {"upper": (0.0, 0.0, 131.41)}}
EXPRESSIONS = {"wave": {"lower": (0.0, 0.0, 30.0)}}
COLLIDE = [("upper", "body"), ("lower", "body")]
'''


@pytest.fixture
def arm_spec(tmp_path):
    p = tmp_path / "arm_spec.py"
    p.write_text(ARM_SPEC)
    return p


def _volume(m):
    a, b, c = (m.verts[m.faces[:, k]] for k in range(3))
    return float(np.einsum("ij,ij->i", a, np.cross(b, c)).sum() / 6)


def test_primitives_measure_distance():
    P = np.array([[0.3, 0, 0], [0, 0, 0], [0.1, 0.1, 0.1]])
    assert np.allclose(sdf.sphere(0.1)(P), [0.2, -0.1, np.sqrt(0.03) - 0.1])
    stick = sdf.capsule((0, 0, 0), (0, 1, 0), 0.1)
    assert np.allclose(stick(np.array([[0.5, 0.5, 0], [0, 1.3, 0], [0, -0.2, 0]])), [0.4, 0.2, 0.1])
    brick = sdf.round_box((0, 0, 0), (0.2, 0.1, 0.1), 0.02)
    assert np.allclose(brick(np.array([[0.5, 0, 0], [0, 0, 0]])), [0.3, -0.1])
    ring = sdf.torus((0, 0, 0), 0.3, 0.05)
    assert np.allclose(ring(np.array([[0.3, 0, 0], [0, 0.2, 0]])), [-0.05, np.hypot(0.3, 0.2) - 0.05])


def test_a_round_cone_is_the_hull_of_its_two_spheres():
    # outside it, the distance is the one to the nearest sphere of the sweep from one end to the other
    a, b, ra, rb = np.array([0.0, 0, 0]), np.array([0.1, 0.5, 0.05]), 0.12, 0.04
    cone = sdf.round_cone(a, b, ra, rb)
    t = np.linspace(0, 1, 40001)[:, None]
    centres, radii = a + t * (b - a), (ra + t * (rb - ra))[:, 0]
    rng = np.random.default_rng(1)
    tested = 0
    for p in rng.uniform(-0.6, 0.9, (60, 3)):
        sweep = (np.linalg.norm(centres - p, axis=1) - radii).min()
        if sweep > 0.01:
            assert abs(cone(p[None])[0] - sweep) < 1e-6
            tested += 1
    assert tested > 30
    P = rng.normal(scale=0.4, size=(200, 3))
    assert np.allclose(sdf.round_cone(a, b, 0.07, 0.07)(P), sdf.capsule(a, b, 0.07)(P))


def test_ellipsoid_surface_and_booleans():
    r = np.array([0.2, 0.1, 0.05])
    u, v = np.meshgrid(np.linspace(0.1, 3.0, 9), np.linspace(0, 6.2, 11))
    on = np.stack([r[0] * np.sin(u) * np.cos(v), r[1] * np.sin(u) * np.sin(v), r[2] * np.cos(u)], -1).reshape(-1, 3)
    f = sdf.ellipsoid((0, 0, 0), r)
    assert np.abs(f(on)).max() < 1e-12
    g = sdf.gradient(f, on)
    true = on / r ** 2
    cos = (g * true).sum(1) / np.linalg.norm(g, axis=1) / np.linalg.norm(true, axis=1)
    assert cos.min() > 0.99999 and np.allclose(np.linalg.norm(g, axis=1), 1, atol=1e-5)
    s1, s2 = sdf.sphere(0.1, (-0.06, 0, 0)), sdf.sphere(0.1, (0.06, 0, 0))
    P = np.random.default_rng(3).uniform(-0.3, 0.3, (500, 3))
    both = np.minimum(s1(P), s2(P))
    blended = sdf.smooth_union(s1, s2, 0.05)(P)
    assert (blended <= both + 1e-12).all() and (both - blended).max() <= 0.05 / 4 + 1e-12
    assert (sdf.smooth_difference(s1, s2, 0.05)(P) >= s1(P) - 1e-12).all()
    moved = sdf.translate(s1, (0, 0.5, 0))
    assert np.allclose(moved(P + [0, 0.5, 0]), s1(P)) and np.allclose(moved.bounds[0], s1.bounds[0] + [0, 0.5, 0])


def test_sphere_mesh_is_closed_and_on_the_surface():
    m = mesh.extract(sdf.sphere(0.1), (-0.12,) * 3, (0.12,) * 3, 0.004)
    r = np.linalg.norm(m.verts, axis=1)
    assert np.abs(r - 0.1).max() < 2e-4
    angle = np.degrees(np.arccos(np.clip((m.normals * m.verts / r[:, None]).sum(1), -1, 1)))
    assert angle.max() < 2
    top = mesh.topology(m.faces)
    assert top["closed"] and top["euler"] == 2
    ball = 4 / 3 * np.pi * 0.1 ** 3
    assert abs(_volume(m) - ball) < 0.01 * ball                       # and wound outwards


@pytest.mark.parametrize("field,euler", [
    (sdf.capsule((-0.05, 0, 0), (0.05, 0, 0), 0.03), 2),
    (sdf.smooth_union(sdf.sphere(0.04, (-0.035, 0, 0)), sdf.sphere(0.04, (0.035, 0, 0)), 0.02), 2),
    (sdf.torus((0, 0, 0), 0.05, 0.015, (0.3, 1.0, 0.2)), 0),
    (sdf.smooth_difference(sdf.round_box((0, 0, 0), (0.06, 0.04, 0.05), 0.01), sdf.sphere(0.035, (0.05, 0.03, 0.0)), 0.01), 2),
])
def test_meshes_close(field, euler):
    lo, hi = field.bounds
    m = mesh.extract(field, lo - 0.008, hi + 0.008, 0.003)
    top = mesh.topology(m.faces)
    assert top["closed"] and top["euler"] == euler
    assert np.abs(field(m.verts)).max() < 1e-6 and _volume(m) > 0


def test_a_box_that_cuts_the_shape_still_gives_a_closed_mesh():
    m = mesh.extract(sdf.sphere(0.1), (-0.05, -0.12, -0.12), (0.12, 0.12, 0.12), 0.005)
    assert mesh.topology(m.faces)["closed"]


def test_euler_angles_are_three_js_xyz():
    x, y, z = np.eye(3)
    assert np.allclose(sdf.euler_matrix((90, 0, 0)) @ y, z)
    assert np.allclose(sdf.euler_matrix((0, 90, 0)) @ z, x)
    assert np.allclose(sdf.euler_matrix((0, 0, 90)) @ x, y)
    assert np.allclose(sdf.euler_matrix((90, 0, 90)) @ x, z)          # z first, then x: Rx Ry Rz
    for angles in np.random.default_rng(4).uniform([-180, -89, -180], [180, 89, 180], (30, 3)):
        assert np.allclose(skin.matrix_euler(sdf.euler_matrix(angles)), angles)


def test_poses_turn_vertices_rigidly(arm_spec):
    model = build.build(arm_spec)
    upper, body = model.part("upper"), model.part("body")
    span = slice(upper["first"], upper["first"] + upper["count"])
    still = slice(body["first"], body["first"] + body["count"])
    turned = skin.pose(model, {"upper": (0, 0, 30)})
    head = np.array([0.2, 0, 0])
    assert np.abs(turned[span] - ((model.verts[span] - head) @ sdf.euler_matrix((0, 0, 30)).T + head)).max() < 1e-12
    assert np.array_equal(turned[still], model.verts[still])
    # an expression adds its angles, times its weight, after the pose
    assert np.allclose(skin.pose(model, "rest", {"wave": 0.5}), skin.pose(model, {"lower": (0, 0, 15)}))


def test_reach_lands_the_end_of_the_chain(arm_spec):
    bones = build.load_spec(arm_spec).BONES
    names = skin.bone_table(bones)[0]
    chain = ("upper", "lower", "tip")
    for target in ([0.45, 0.25, 0.15], [0.3, -0.2, 0.3], [0.05, 0.1, 0.35]):
        W = skin.world_matrices(bones, skin.reach(bones, {"chest": (10, 20, 0)}, "", target, chain=chain))
        assert np.linalg.norm(W[names.index("tip")][:3, 3] - target) < 1e-9
    W = skin.world_matrices(bones, skin.reach(bones, {}, "", [0.2, 0.0, 2.0], chain=chain))   # out of reach
    tip = W[names.index("tip")][:3, 3] - [0.2, 0, 0]
    assert np.allclose(tip / np.linalg.norm(tip), [0, 0, 1], atol=1e-6)


def test_export_reads_back(arm_spec, tmp_path):
    model = build.build(arm_spec)
    path = export.write(model, tmp_path / "built")
    meta = json.loads(path.read_text())
    assert meta["vertexCount"] == len(model.verts) and meta["triangleCount"] == len(model.faces)
    assert all(v["offset"] % 4 == 0 for v in meta["layout"].values())
    assert [p["name"] for p in meta["parts"]] == ["body", "upper", "lower", "pebble"]
    assert sum(p["count"] for p in meta["parts"]) == len(model.verts)
    back = export.load(path)
    for attr in ("verts", "normals", "faces", "skin_index", "skin_weight"):
        assert np.array_equal(getattr(back, attr), getattr(model, attr)), attr
    assert back.poses["fold"]["upper"] == [0.0, 0.0, 131.41] and back.bbox == model.bbox
    assert np.allclose(back.skin_weight.sum(1), 1, atol=1e-6)


def test_check_finds_what_floats_and_what_sinks_in(arm_spec):
    r = check.run(arm_spec)
    assert r["closed"] and all(p["euler"] == 2 for p in r["parts"])
    assert r["floating"] == ["pebble"]                  # the arm touches the body; the pebble touches nothing
    fold, rest = r["poses"]["fold"], r["poses"]["rest"]
    assert abs(fold["penetration_mm"] - 30) < 1.5 and fold["worst"] == ["upper", "body"]
    assert rest["penetration_mm"] == 0 and rest["worst"] == [] and rest["closest"] == ["upper", "body"]


def test_the_mannequin_is_a_sound_test_model():
    model = build.build("mannequin")
    names = [p["name"] for p in model.parts]
    assert len(names) >= 30 and {"torso", "head", "l_forearm", "r_forearm", "l_hand", "r_hand"} <= set(names)
    assert set(build.HUMANOID) <= {b["name"] for b in model.bones}
    assert {"stand", "walk", "write"} <= set(model.poses)
    assert {(a, "torso") for a in ("l_forearm", "r_forearm", "l_hand", "r_hand")} <= set(mannequin.COLLIDE)
    assert 1.68 < model.verts[:, 1].max() < 1.76 and abs(model.verts[:, 1].min()) < 0.005
    assert abs(skin.pose(model, "walk")[:, 1].min()) < 0.005          # the standing foot is on the ground
    # the abdomen bends: its bottom stays with the spine, its top goes with the chest, between them a blend
    belly = model.part("abdomen")
    own = slice(belly["first"], belly["first"] + belly["count"])
    w = model.skin_weight[own]
    assert ((w[:, 0] > 0.05) & (w[:, 0] < 0.95)).any()
    moved = np.linalg.norm(skin.pose(model, {"chest": (20, 0, 0)})[own] - model.verts[own], axis=1)
    y = model.verts[own, 1]
    assert moved[y < 1.03].max() < 1e-12 and moved[y > 1.2].min() > 0.005
    r = check.run(mannequin)
    assert r["closed"] and r["floating"] == [] and r["humanoid"]
    assert all(r["poses"][p]["penetration_mm"] <= 3 for p in ("stand", "walk", "write"))
    # the left hand slid 5 cm down the arm, off its wrist: it floats, with the fingers it carries
    hand = mannequin.PARTS["l_hand"]
    moved = SimpleNamespace(NAME="moved", BONES=mannequin.BONES, POSES=mannequin.POSES, COLLIDE=mannequin.COLLIDE,
                            PARTS={**mannequin.PARTS, "l_hand": replace(hand, sdf=sdf.translate(hand.sdf, 0.05 * mannequin.arm("l")[3]))})
    loose = check.run(moved)["floating"]
    assert "l_hand" in loose and "torso" not in loose


def test_the_command_line(arm_spec, tmp_path):
    with pytest.raises(SystemExit) as e:
        cli.main(["model", "--help"])
    assert e.value.code == 0
    cli.main(["model", "build", str(arm_spec), "--out", str(tmp_path / "b")])
    assert (tmp_path / "b" / "arm.json").exists() and (tmp_path / "b" / "arm.bin").exists()
    cli.main(["model", "check", str(arm_spec), "--model", str(tmp_path / "b" / "arm.json"), "--json", str(tmp_path / "c.json")])
    report = json.loads((tmp_path / "c.json").read_text())
    assert report["floating"] == ["pebble"] and report["poses"]["fold"]["penetration_mm"] > 25


PAGE = """import { stage } from './kit/stage.js';
import { layer3d, THREE } from './kit/three.js';
import * as figure from './kit/figure.js';

const L = layer3d(160, 120, { background: '#000000' });
let fig = null;
const sample = () => {
  const out = {}, v = new THREE.Vector3();
  for (const m of fig.meshes) {
    const pos = m.geometry.attributes.position, pts = [];
    for (let i = 0; i < pos.count; i += 61) { v.fromBufferAttribute(pos, i); m.applyBoneTransform(i, v); pts.push([i, v.x, v.y, v.z]); }
    out[m.name] = pts;
  }
  return out;
};
window.REPORT = () => {
  const r = { count: fig.vertexCount, names: fig.meshes.map(m => m.name), poses: {} };
  for (const p of Object.keys(fig.poses)) { fig.setPose(p); r.poses[p] = sample(); }
  fig.setPose('stand');
  fig.setExpression({ nod: 0.7, turn: -0.4, nothing: 1 });
  r.expression = sample();
  fig.setExpression({});
  fig.setPose({ spine: [8, 0, 0] });
  const target = [-0.3, 1.1, 0.32];
  fig.reach('r', target);
  r.reach = fig.bones.r_hand.getWorldPosition(new THREE.Vector3()).distanceTo(new THREE.Vector3(...target));
  fig.setPose('stand');
  const look = [0.7, 1.9, 1.2];
  fig.aimHead(look, 1);
  const head = fig.bones.head, at = head.getWorldPosition(new THREE.Vector3());
  const facing = new THREE.Vector3(0, 0, 1).applyQuaternion(head.getWorldQuaternion(new THREE.Quaternion()));
  r.aim = THREE.MathUtils.radToDeg(facing.angleTo(new THREE.Vector3(...look).sub(at)));
  try { fig.setPose('nope'); r.bad = ''; } catch (e) { r.bad = e.message; }
  return r;
};
stage({ width: 160, height: 120, duration: 1,
  prepare: async () => { fig = await figure.load('model/mannequin.json'); L.scene.add(fig.root); },
  draw: g => L.draw(g) });
"""


@browser
def test_figure_js_agrees_with_python(tmp_path):
    from moodreel.pack.kit import vendor_three
    path = build.build_to("mannequin", tmp_path / "built")
    d = tmp_path / "film"
    shutil.copytree(REPO / "kit", d / "kit", ignore=shutil.ignore_patterns("README.md", "vendor"))
    vendor_three(d / "kit")
    (d / "model").mkdir()
    for f in (path, path.with_suffix(".bin")):
        shutil.copyfile(f, d / "model" / f.name)
    (d / "index.html").write_text('<!doctype html><html><body><script type="module" src="main.js"></script></body></html>')
    (d / "main.js").write_text(PAGE)
    subprocess.run(["node", str(REPO / "render" / "render.mjs"), "report", str(d), "--size", "160x120", "--out",
                    str(d / "report.json")], check=True, capture_output=True, timeout=180)
    rep = json.loads((d / "report.json").read_text())
    model = export.load(path)
    assert rep["count"] == len(model.verts) and rep["names"] == [p["name"] for p in model.parts]
    first = {p["name"]: p["first"] for p in model.parts}

    def off(sampled, posed):
        return max(np.abs(posed[first[n] + i] - [x, y, z]).max() for n, pts in sampled.items() for i, x, y, z in pts)
    for name, sampled in rep["poses"].items():
        assert off(sampled, skin.pose(model, name)) < 1e-6, name
    assert off(rep["expression"], skin.pose(model, "stand", {"nod": 0.7, "turn": -0.4})) < 1e-6
    assert rep["reach"] < 1e-6 and rep["aim"] < 0.01
    assert "no pose" in rep["bad"]


@browser
def test_the_sheet_is_labelled_and_the_same_every_time(tmp_path):
    path = build.build_to("mannequin", tmp_path / "m")
    runs = [sheet.run(path, tmp_path / k / "sheet.png", poses=["stand", "write"], views=["front", "side"], cell=(180, 240))
            for k in ("a", "b")]
    A, B = (cv2.imread(str(tmp_path / k / "sheet.png")) for k in ("a", "b"))
    assert np.array_equal(A, B)
    cells = json.loads((tmp_path / "a" / "sheet.json").read_text())["cells"]
    assert cells == runs[0]["cells"]
    assert {(c["pose"], c["view"]) for c in cells} == {(p, v) for p in ("stand", "write") for v in ("front", "side")}
    g = cv2.cvtColor(A, cv2.COLOR_BGR2GRAY).astype(float)
    for c in cells:
        x, y, w, h = c["label_box"]
        assert g[c["y"]:c["y"] + c["h"], c["x"]:c["x"] + c["w"]].std() > 8 and g[y:y + h, x:x + w].std() > 4
