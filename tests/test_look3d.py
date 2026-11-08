"""The illustrated 3D look (kit/look3d.js, kit/post3d.js): the ramp lands on its colours, its steps widen with softness,
the stipple rides the surface, the picture changes on the drawings (hold) and not between them, a chain's hold wins
over a material's own, grain sits in the mid tones, a chain with every pass off is the plain render, skinned and
instanced meshes take the material, and a shader that does not compile stops the render with its log.

One film holds every case as a shot of its own, ten seconds apart, so one browser renders them all."""
from __future__ import annotations

import json
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

W, H, FPS = 320, 180, 24
COL = {"lit": "#f0d6b0", "mid": "#a8786c", "shade": "#3e4a6a"}

PAGE = r"""import { stage } from './kit/stage.js';
import { layer3d, THREE } from './kit/three.js';
import * as look3d from './kit/look3d.js';
import * as post3d from './kit/post3d.js';

const W = 320, H = 180, FPS = 24, V = window.VARIANT || {};
const COL = __COL__;
const BARE = { terminator: 0, formTint: null, stipple: 0 };
const L = layer3d(W, H, { background: '#000000', toneMapping: 'none' });
const R = L.renderer;
look3d.guard(R);

const flat = (half, x = 0) => {                   // an orthographic camera half units high, looking down -z at x
  const c = new THREE.OrthographicCamera(-half * W / H, half * W / H, half, -half, 0.1, 100);
  c.position.set(x, 0, 10);
  c.lookAt(x, 0, 0);
  return c;
};
const room = () => { const s = new THREE.Scene(); s.background = new THREE.Color('#000000'); return s; };
const ball = (r, mat) => new THREE.Mesh(new THREE.SphereGeometry(r, 160, 80), mat);
const shots = [];

{ // 0: three spheres, softness 0.1 / 0.3 / 0.6, the light to the right and toward us
  const s = room();
  [0.1, 0.3, 0.6].forEach((softness, i) => {
    const m = look3d.ramp({ ...COL, ...BARE, softness, light: [0.8, 0, 0.6] });
    if (i === 1 && V.broken) {                      // one line of nonsense, for the guard
      m.onBeforeCompile = sh => { sh.fragmentShader = sh.fragmentShader.replace('void main', 'not even glsl;\nvoid main'); };
    }
    const b = ball(0.5, m);
    b.position.x = (i - 1) * 1.15;
    s.add(b);
  });
  const cam = flat(1);
  shots.push(n => { look3d.setFrame(n); R.setRenderTarget(null); R.render(s, cam); });
}
{ // 1: a big stippled sphere; the camera pans 8 px a frame
  const s = room();
  s.add(ball(3, look3d.ramp({ ...COL, ...BARE, stipple: 1, boil: 0, light: [1, 0, 0.15] })));
  const cam = flat(1);
  shots.push(n => {
    const x = n * 8 / 90;
    cam.position.set(x, 0, 10);
    cam.lookAt(x, 0, 0);
    look3d.setFrame(n);
    R.setRenderTarget(null);
    R.render(s, cam);
  });
}
const table = () => {                             // a ball on a floor, the whole material on, seen in perspective
  const s = room();
  const b = ball(1, look3d.ramp({ ...COL, terminator: 0.5, termTint: '#c85a64', formTint: '#5c5a90', stipple: 1, boil: 0.2 }));
  b.position.y = 1;
  s.add(b);
  const floor = new THREE.Mesh(new THREE.PlaneGeometry(30, 30),
    look3d.ramp({ lit: '#e2d4bc', mid: '#a89a86', shade: '#4e4a5c', stipple: 1 }));
  floor.rotation.x = -Math.PI / 2;
  s.add(floor);
  const cam = new THREE.PerspectiveCamera(35, W / H, 0.1, 100);
  cam.position.set(2.8, 2.2, 5.6);
  cam.lookAt(0, 0.9, 0);
  return { s, cam };
};
{ // 2: two frames a drawing, grain only on the drawings
  const { s, cam } = table();
  const finish = post3d.chain(R, { hold: 2, grain: 0.04, flicker: 0 });
  shots.push(n => finish(s, cam, n));
}
{ // 3: the same with a share of the grain flickering every frame
  const { s, cam } = table();
  const finish = post3d.chain(R, { hold: 2, grain: 0.04, flicker: 0.3 });
  shots.push(n => finish(s, cam, n));
}
{ // 4: grey cards, dark / mid / light, under grain alone
  const s = room();
  ['#262626', '#808080', '#ebebeb'].forEach((c, i) => {
    const q = new THREE.Mesh(new THREE.PlaneGeometry(0.9, 1.6), new THREE.MeshBasicMaterial({ color: c }));
    q.position.x = (i - 1) * 1.2;
    s.add(q);
  });
  const cam = flat(1);
  const finish = post3d.chain(R, { grain: 0.04 });
  shots.push(n => finish(s, cam, n));
}
{ // 5 and 6: the table drawn plainly, then through a chain with every pass off
  const { s, cam } = table();
  shots.push(n => { look3d.setFrame(n); R.setRenderTarget(null); R.render(s, cam); });
  const idle = post3d.chain(R, {});
  shots.push(n => idle(s, cam, n));
}
{ // 7: a bent skinned tube, instanced balls, a two-sided card and fog, under every pass
  const s = room();
  s.fog = new THREE.Fog('#000000', 8, 30);
  const tube = new THREE.CylinderGeometry(0.3, 0.3, 2, 24, 12);
  const at = tube.attributes.position, bones = [], share = [];
  for (let i = 0; i < at.count; i++) {
    const up = Math.min(1, Math.max(0, at.getY(i) / 2 + 0.5));   // 0 at the foot, 1 at the top
    bones.push(0, 1, 0, 0);
    share.push(1 - up, up, 0, 0);
  }
  tube.setAttribute('skinIndex', new THREE.Uint16BufferAttribute(bones, 4));
  tube.setAttribute('skinWeight', new THREE.Float32BufferAttribute(share, 4));
  const foot = new THREE.Bone(), top = new THREE.Bone();
  foot.position.y = -1;
  top.position.y = 1;
  foot.add(top);
  const limb = new THREE.SkinnedMesh(tube, look3d.ramp({ ...COL, stipple: 1, terminator: 0.4 }));
  limb.add(foot);
  limb.bind(new THREE.Skeleton([foot, top]));
  top.rotation.z = 0.7;
  s.add(limb);
  const many = new THREE.InstancedMesh(new THREE.SphereGeometry(0.25, 32, 16), look3d.ramp({ ...COL, stipple: 1 }), 3);
  for (let i = 0; i < 3; i++) many.setMatrixAt(i, new THREE.Matrix4().makeTranslation(-1.6 + 0.6 * i, -0.8, 0.5));
  s.add(many);
  const card = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), look3d.ramp({ ...COL, side: THREE.DoubleSide }));
  card.position.set(1.5, 0, 0);
  card.rotation.y = 2.5;
  s.add(card);
  const cam = new THREE.PerspectiveCamera(35, W / H, 0.1, 100);
  cam.position.set(0, 0.3, 7);
  cam.lookAt(0, 0, 0);
  const finish = post3d.chain(R, { hold: 2, ao: 1, aoTint: '#40385a', dof: { focus: 7, aperture: 0.4 }, bloom: 0.6,
    shoulder: 1, vignette: 0.3, grain: 0.03, grainSize: 1.5, flicker: 0.1, mottle: 0.4 });
  shots.push(n => finish(s, cam, n));
}
{ // 8: every dot boils; the material's own hold of 2, drawn without a chain
  const s = room();
  const m = look3d.ramp({ ...COL, ...BARE, stipple: 1, boil: 1, hold: 2, light: [1, 0, 0.15] });
  s.add(ball(3, m));
  const cam = flat(1);
  shots.push(n => { look3d.setFrame(n); R.setRenderTarget(null); R.render(s, cam); });
  // 9: a copy of it with a hold of 3, under a chain that holds 1: the chain's hold wins, and the copy follows the frame
  const s2 = room();
  const copy = m.clone();
  copy.uniforms.uDots.value.z = 3;
  s2.add(ball(3, copy));
  const finish = post3d.chain(R, { hold: 1, vignette: 0.2 });
  shots.push(n => finish(s2, cam, n));
}

stage({ width: W, height: H, duration: 10 * shots.length, background: '#000', draw: (g, t) => {
  const k = Math.min(shots.length - 1, Math.floor(t / 10 + 1e-6));
  shots[k](look3d.frameOf(t - 10 * k, FPS));
  g.drawImage(L.canvas, 0, 0, W, H);
} });
""".replace("__COL__", json.dumps(COL))


def at(shot, n):
    return 10 * shot + n / FPS


def rgb(h):
    return np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], float)


def luma(img):
    return img[..., 0] * 0.299 + img[..., 1] * 0.587 + img[..., 2] * 0.114


def band(y):                                        # the 1-4 px band, where a pixel-sized stipple lives
    y = y.astype(np.float32)
    return cv2.GaussianBlur(y, (0, 0), 0.6) - cv2.GaussianBlur(y, (0, 0), 2.0)


def ncc(a, b):
    a, b = a - a.mean(), b - b.mean()
    return float((a * b).sum() / np.sqrt((a * a).sum() * (b * b).sum()))


def render(d, cmd, *args):
    return subprocess.run(["node", str(REPO / "render" / "render.mjs"), cmd, str(d), *map(str, args)],
                          capture_output=True, text=True, timeout=180)


@pytest.fixture(scope="module")
def shots(tmp_path_factory):
    d = film.new("look", "lowpoly-island", root=tmp_path_factory.mktemp("look3d"), duration=1, size=f"{W}x{H}")
    (d / "main.js").write_text(PAGE)
    times = [at(0, 0), at(1, 0), at(1, 4), *[at(2, n) for n in range(4)], at(3, 0), at(3, 1), at(4, 0), at(5, 3),
             at(6, 3), at(7, 0), at(8, 0), at(8, 1), at(8, 2), at(9, 0), at(9, 1)]
    p = render(d, "still", *times, "--size", f"{W}x{H}", "--out", d / "out")
    assert p.returncode == 0, p.stdout + p.stderr
    got = {}
    for f in (d / "out").glob("t_*.jpg"):
        t = float(f.stem[2:])
        hit = [x for x in times if abs(x - t) < 1e-9]
        if hit:
            got[hit[0]] = cv2.cvtColor(cv2.imread(str(f)), cv2.COLOR_BGR2RGB).astype(float)
    assert len(got) == len(times)
    return d, got


@needs
def test_the_ramp_lands_on_its_colours_and_softness_widens_the_steps(shots):
    _, img = shots
    a = img[at(0, 0)]
    lit = np.median(a[88:93, 194:199].reshape(-1, 3), axis=0)        # the middle ball where it faces the light
    shade = np.median(a[88:93, 122:127].reshape(-1, 3), axis=0)      # turned away: N·L about -0.28, below the wrap
    assert np.abs(lit - rgb(COL["lit"])).max() <= 4, lit
    assert np.abs(shade - rgb(COL["shade"])).max() <= 4, shade
    ls, lm = luma(rgb(COL["shade"])), luma(rgb(COL["mid"]))
    widths = []
    for cx in (160 - 103.5, 160, 160 + 103.5):                     # along each ball's equator, shade side to the light
        x0, x1 = int(cx - 0.95 * 45), int(cx + 0.8 * 45)
        prof = np.median(luma(a[88:93, x0:x1]), axis=0)
        lo = int(np.argmax(prof >= ls + 0.1 * (lm - ls)))
        hi = int(np.argmax(prof >= ls + 0.9 * (lm - ls)))
        assert prof[hi] >= ls + 0.9 * (lm - ls), prof
        widths.append(hi - lo)
    assert widths[0] < widths[1] < widths[2], widths


@needs
def test_the_stipple_rides_the_surface_not_the_screen(shots):
    _, img = shots
    a, b = band(luma(img[at(1, 0)])), band(luma(img[at(1, 4)]))
    s, m = 32, 16                                                    # 4 frames of an 8 px pan
    surface = ncc(a[m:-m, m + s:-m], b[m:-m, m:-m - s])
    screen = ncc(a[m:-m, m + s:-m], b[m:-m, m + s:-m])
    assert a[m:-m, m:-m].std() > 1.0                                 # there is a stipple to follow
    assert surface > 0.8 and screen < 0.3, (surface, screen)


@needs
def test_the_picture_changes_on_the_drawings_and_flicker_breaks_that(shots):
    _, img = shots
    f = [img[at(2, n)] for n in range(4)]
    assert np.array_equal(f[0], f[1]) and np.array_equal(f[2], f[3])  # hold 2: one drawing on two frames
    assert np.abs(f[1] - f[2]).mean() > 0.5                          # the next drawing: new grain, some dots boiled
    assert np.abs(img[at(3, 0)] - img[at(3, 1)]).mean() > 0.2        # flicker: some grain on every frame


@needs
def test_a_material_holds_its_own_drawings_unless_a_chain_holds_them(shots):
    _, img = shots
    assert np.array_equal(img[at(8, 0)], img[at(8, 1)])                # hold 2 without a chain: frames 0 and 1 alike
    assert np.abs(img[at(8, 1)] - img[at(8, 2)]).mean() > 0.5           # frame 2 is a new drawing: the dots boil
    assert np.abs(img[at(9, 0)] - img[at(9, 1)]).mean() > 0.5           # a hold-1 chain over a hold-3 copy: every frame


@needs
def test_grain_sits_in_the_mid_tones(shots):
    _, img = shots
    y = luma(img[at(4, 0)]).astype(np.float32)
    hp = y - cv2.GaussianBlur(y, (0, 0), 3)
    std = {k: float(hp[60:120, int(cx) - 30:int(cx) + 30].std()) for k, cx in (("dark", 52), ("mid", 160), ("light", 268))}
    assert std["mid"] > 3, std
    assert std["mid"] >= 2 * std["light"] and std["dark"] > std["light"], std


@needs
def test_a_chain_with_every_pass_off_is_the_plain_render(shots):
    _, img = shots
    assert np.array_equal(img[at(5, 3)], img[at(6, 3)])


@needs
def test_skinned_instanced_and_two_sided_meshes_take_the_material(shots):
    _, img = shots
    a = img[at(7, 0)]
    assert luma(a[60:120, 140:180]).mean() > 60                      # the tube, lit, in the middle
    assert luma(a[110:140, 60:130]).max() > 60                       # the instanced balls along the bottom left


@needs
def test_a_shader_that_does_not_compile_stops_the_render_with_its_log(shots):
    d, _ = shots
    p = render(d, "still", 0.5, "--size", f"{W}x{H}", "--out", d / "broken", "--variant", json.dumps({"broken": True}))
    out = p.stdout + p.stderr
    assert p.returncode != 0
    assert "look3d.guard" in out and "ERROR" in out and "not even glsl" in out, out[-2000:]


@needs
def test_frames_and_drawings(shots):
    d, _ = shots
    code = ("import * as L from './kit/look3d.js';"
            "console.log(JSON.stringify([L.frameOf(0.5, 24), L.frameOf(7 / 24, 24), L.frameOf(1 / 3, 30), "
            "L.held(7 / 24, 24, 2), L.held(8 / 24, 24, 2), L.held(9 / 24, 24, 3), L.held(5 / 24, 24, 1)]));")
    p = subprocess.run(["node", "--input-type=module", "-e", code], cwd=d, capture_output=True, text=True, timeout=60)
    assert p.returncode == 0, p.stderr
    got = json.loads(p.stdout)
    assert got[:3] == [12, 7, 10]
    assert np.allclose(got[3:], [6 / 24, 8 / 24, 9 / 24, 5 / 24])
