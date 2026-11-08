"""kit/3dcv through its shot adapter: a frame is the same whatever was rendered or initialised before it, a shot on
twos holds its drawing for two frames while the grain flicker still moves on every output frame, the post's grain is
weighted by tone (strong on mid-grey, faint on near-white), a painted texture follows its seed, a shot leaves no global
state behind for the next, and a film page with no import map loads the whole thing.

One throwaway film holds the shots; the page's window.REPORT renders a list of frames in the order asked for and hands
back the stage canvas of each as a PNG, so the pixels compared are exact (no JPEG in between)."""
from __future__ import annotations

import base64
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

W, H = 320, 180

PAGE = r"""import { stage } from './kit/stage.js';
import { THREE } from './kit/three.js';
import * as cv from './kit/3dcv/stage.js';
import * as look from './kit/3dcv/look.js';
import * as paint from './kit/3dcv/paint.js';

const W = 320, H = 180, V = window.VARIANT || {};
const at = n => (n - 0.75) / 24;                  // a time inside global frame n

const sphere = (ctx, name, r = 0.6) => {
  const m = new THREE.Mesh(new THREE.SphereGeometry(r, 64, 32), look.preset(name));
  m.castShadow = m.receiveShadow = true;
  ctx.scene.add(m);
  return m;
};
const floor = ctx => {
  const m = new THREE.Mesh(new THREE.PlaneGeometry(12, 12), look.preset('floor'));
  m.rotation.x = -Math.PI / 2;
  m.receiveShadow = true;
  ctx.scene.add(m);
};
const frame = ctx => { ctx.camera.position.set(0, 1.6, 4.5); ctx.camera.lookAt(0, 0.5, 0); };

const shots = {
  // listed first, so its init runs before every other: it changes the look env and the renderer, then changes them
  // again on each of its frames, and draws by itself without the post
  loud: {
    id: 'loud', frames: [13, 24],
    init(ctx) {
      look.setEnv({ globalTint: '#ff7050', hazeColor: '#50ff90', hazeDensity: 0.4, shadowMul: 0 });
      const r = ctx.renderer;
      r.shadowMap.enabled = false;
      r.toneMapping = THREE.ACESFilmicToneMapping;
      r.toneMappingExposure = 2.2;
      r.setClearColor('#ff00ff', 1);
      ctx.keyLight(ctx.scene, { dir: [0.7, 1, 0.3], shadow: false });
      this.ball = sphere(ctx, 'jacket');
      floor(ctx);
      frame(ctx);
    },
    render(ctx, n) {
      look.setEnv({ globalTint: [1, 0.4 + 0.03 * (n - 13), 0.3] });
      ctx.renderer.toneMappingExposure = 1 + 0.1 * (n - 13);
      this.ball.position.set(0, 0.6 + 0.05 * (n - 13), 0);
      ctx.renderer.setRenderTarget(null);
      ctx.renderer.render(ctx.scene, ctx.camera);
      ctx._drawn = true;
    },
  },
  // a lit, shadowed still life; its render only returns post params, the adapter draws ctx.scene and ctx.camera
  calm: {
    id: 'calm', frames: [1, 12],
    init(ctx) {
      ctx.keyLight(ctx.scene, { dir: [-0.6, 1, 0.5], shadow: { size: 512, extent: 4 } });
      this.ball = sphere(ctx, 'clay');
      floor(ctx);
      frame(ctx);
    },
    render(ctx, n) {
      this.ball.position.set(-1 + 0.1 * n, 0.6, 0);
      return { grain: { amount: 0.03 } };
    },
  },
};
// a bright ball crossing a dark frame on twos; `flicker` is the share of the grain drawn anew on every output frame
const crossing = (id, frames, flicker) => ({
  id, frames, hold: 2, ss: 1,
  init(ctx) {
    this.ball = sphere(ctx, 'glow', 0.35);
    frame(ctx);
  },
  render(ctx, n) {
    this.ball.position.set(-1.6 + 0.12 * (n - frames[0]), 0.5, 0);
    ctx.draw(ctx.scene, ctx.camera, { bloom: { strength: 0 }, grain: { flicker } });
  },
});
shots.twos = crossing('twos', [25, 36], 0);
shots.flicker = crossing('flicker', [37, 48], 0.3);
// flat mid-grey (left) and near-white (right) fields under nothing but the grain
shots.fields = {
  id: 'fields', frames: [49, 60],
  init(ctx) {
    const a = W / H;
    this.cam = new THREE.OrthographicCamera(-a, a, 1, -1, 0.1, 10);
    this.cam.position.z = 5;
    for (const [hex, x] of [['#808080', -a / 2], ['#f2f2f2', a / 2]]) {
      const card = new THREE.Mesh(new THREE.PlaneGeometry(a, 2.2), new THREE.MeshBasicMaterial({ color: hex }));
      card.position.x = x;
      ctx.scene.add(card);
    }
  },
  render(ctx) {
    ctx.draw(ctx.scene, this.cam, { grain: { amount: 0.08, mottle: 0, flicker: 0 }, vignette: { amount: 0 },
      bloom: { strength: 0 }, sharpen: 0 });
  },
};
shots.late = { id: 'late', frames: [61, 72], async render() {} };   // not allowed: moodreel renders synchronously

const film = cv.film({ width: W, height: H, shots: (V.only || Object.keys(shots)).map(k => shots[k]) });
const S = stage({ width: W, height: H, duration: 3, background: '#000', prepare: () => film.init(),
  draw: (g, t) => film.draw(g, t, W, H) });

const painted = seed => paint.painted({ w: 96, h: 64, base: '#b89080',
  fbm: { seed, scale: 0.06, alpha: 0.6, colors: ['#3a2030', '#f4e2c4'] },
  blotches: { seed, count: 24, colors: ['#ffffff', '#24324a'], alpha: 0.35, size: [6, 22] } }).userData.canvas.c.toDataURL('image/png');
const probe = () => ({ tone: film.renderer.toneMapping, exposure: film.renderer.toneMappingExposure,
  shadows: film.renderer.shadowMap.enabled, haze: look.env.uHazeDensity.value, tint: look.env.uGlobalTint.value.getHexString() });

window.REPORT = () => {
  const frames = {};
  for (const [name, n] of V.seq || []) { window.render(at(n)); frames[name] = S.canvas.toDataURL('image/png'); }
  const out = { frames, painted: V.only ? null : { a: painted(5), b: painted(5), c: painted(6) } };
  if (V.only) return out;
  film.render(18); out.afterLoud = probe();
  film.render(6); out.afterCalm = probe();
  out.consts = { aces: THREE.ACESFilmicToneMapping, none: THREE.NoToneMapping };
  try { film.render(61); } catch (e) { out.late = e.message; }
  out.outside = film.render(500);
  out.frameOf = [0, 1 / 24, 0.5, 2.99].map(film.frameOf);
  out.shotAt = [1, 13, 30, 500].map(n => (film.shotAt(n) || { id: null }).id);
  out.contexts = film.contexts.map(c => c.shotId);
  out.posts = new Set(film.contexts.map(c => c.post)).size;
  out.oneRenderer = film.contexts.every(c => c.renderer === film.renderer);
  out.canvases = document.querySelectorAll('body > canvas').length;
  out.offscreen = !film.canvas.isConnected;
  return out;
};
"""

SEQ = [["a1", 6], ["a2", 6], ["b", 18], ["a3", 6], ["c26", 26], ["c27", 27], ["c28", 28],
       ["d38", 38], ["d39", 39], ["d40", 40], ["e", 50]]


def png(url):
    raw = np.frombuffer(base64.b64decode(url.split(",", 1)[1]), np.uint8)
    return cv2.cvtColor(cv2.imdecode(raw, cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGB).astype(float)


def luma(img):
    return img[..., 0] * 0.299 + img[..., 1] * 0.587 + img[..., 2] * 0.114


def report(d, name, variant):
    out = d / f"report-{name}.json"
    p = subprocess.run(["node", str(REPO / "render" / "render.mjs"), "report", str(d), "--size", f"{W}x{H}",
                        "--variant", json.dumps(variant), "--out", str(out)], capture_output=True, text=True, timeout=300)
    assert p.returncode == 0, p.stdout + p.stderr
    rep = json.loads(out.read_text())
    rep["frames"] = {k: png(v) for k, v in rep["frames"].items()}
    if rep.get("painted"):
        rep["painted"] = {k: png(v) for k, v in rep["painted"].items()}
    return rep


@pytest.fixture(scope="module")
def page(tmp_path_factory):
    d = film.new("cv", "lowpoly-island", root=tmp_path_factory.mktemp("3dcv"), duration=3, size=f"{W}x{H}", add=("3dcv",))
    (d / "main.js").write_text(PAGE)
    return d


@pytest.fixture(scope="module")
def full(page):
    return report(page, "full", {"seq": SEQ})


@pytest.fixture(scope="module")
def alone(page):
    return report(page, "alone", {"only": ["calm"], "seq": [["a", 6]]})


def centre_x(img):                                  # where the bright ball is, along x
    xs = np.nonzero(luma(img) > 160)[1]
    assert xs.size > 50, xs.size
    return float(xs.mean())


@needs
def test_deterministic_the_same_frame_whatever_was_rendered_or_initialised_before(full, alone):
    f = full["frames"]
    assert luma(f["a1"]).std() > 10                                 # a picture, not a blank
    assert np.array_equal(f["a1"], f["a2"])                         # the same frame twice in a row
    assert np.abs(f["b"] - f["a1"]).mean() > 10                     # the other shot looks nothing like it ...
    assert np.array_equal(f["a1"], f["a3"])                         # ... and leaves it as it was
    assert np.array_equal(f["a1"], alone["frames"]["a"])            # as in a film without the other shot and its init


@needs
def test_a_shot_leaves_no_global_state_for_the_next(full):
    c, loud, calm = full["consts"], full["afterLoud"], full["afterCalm"]
    assert loud == {"tone": c["aces"], "exposure": 1.5, "shadows": False, "haze": 0.4, "tint": loud["tint"]}, loud
    assert loud["tint"] != "ffffff"
    assert calm == {"tone": c["none"], "exposure": 1, "shadows": True, "haze": 0, "tint": "ffffff"}, calm


@needs
def test_hold_2_draws_on_twos_while_the_flicker_moves_on_every_frame(full):
    f = full["frames"]
    assert np.array_equal(f["c26"], f["c27"])                       # frames 26 and 27 show drawing 26
    assert centre_x(f["c28"]) - centre_x(f["c27"]) > 8              # drawing 28: the ball has moved on
    still = np.abs(f["d38"] - f["d39"]).mean()                      # one drawing, two output frames, flicker 0.3
    assert 0.02 < still < 2, still
    assert abs(centre_x(f["d38"]) - centre_x(f["d39"])) < 0.5
    assert centre_x(f["d40"]) - centre_x(f["d39"]) > 8


@needs
def test_grain_is_tone_weighted_strong_on_mid_grey_faint_on_near_white(full):
    y = luma(full["frames"]["e"]).astype(np.float32)
    hp = y - cv2.GaussianBlur(y, (0, 0), 3)
    mid, white = (slice(20, 160), slice(16, 144)), (slice(20, 160), slice(176, 304))
    assert 100 < y[mid].mean() < 160 and y[white].mean() > 215, (y[mid].mean(), y[white].mean())
    k = hp[mid].std() / hp[white].std()
    assert hp[mid].std() > 2 and k > 3, (hp[mid].std(), hp[white].std(), k)


@needs
def test_a_painted_texture_follows_its_seed(full):
    p = full["painted"]
    assert p["a"].shape == (64, 96, 3) and p["a"].std() > 10
    assert np.array_equal(p["a"], p["b"])
    assert np.abs(p["a"] - p["c"]).mean() > 5


@needs
def test_a_page_without_an_import_map_runs_the_film_and_its_api(page, full):
    assert "importmap" not in (page / "index.html").read_text() and (page / "kit" / "3dcv" / "stage.js").exists()
    assert full["frameOf"] == [1, 2, 13, 72]
    assert full["shotAt"] == ["calm", "loud", "twos", None] and full["outside"] is False
    assert "Promise" in full["late"] and "late" in full["late"]
    assert full["contexts"] == ["loud", "calm", "twos", "flicker", "fields", "late"]
    assert full["posts"] == 2 and full["oneRenderer"]                 # one Post per supersampling factor, one renderer
    assert full["canvases"] == 1 and full["offscreen"]                # the stage's canvas stays the only one
