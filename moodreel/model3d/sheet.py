"""A contact sheet of a model: views x poses, rendered in headless Chrome, each cell labelled, beside sheet.json.

The model goes into a throwaway film folder with this repository's kit, three.js and a page that loads it with
kit/figure.js, poses it and points an orthographic camera at it, one cell per still (render.mjs still, t = the cell's
number). Plain clay shading, a key light that follows the camera, and a ground line at y = 0, so a pose whose feet
float or sink shows it. Every cell has the same scale and the same height for the ground, framed once around all
the poses in every view; the cells are then laid out here, poses down and views across, with a label bar above each.
Nothing in it varies between runs: the same model gives the same sheet, pixel for pixel.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import cv2
import numpy as np

from . import build, export, skin

REPO = Path(__file__).resolve().parents[2]
RENDER = REPO / "render" / "render.mjs"
# degrees round the figure from its front (+z) towards its left (+x): the camera's side
VIEWS = {"front": 0.0, "three-quarter": 45.0, "side": 90.0, "back": 180.0}
CELL = (360, 480)
GAP, BAR = 12, 28
PAPER = (38, 39, 42)                   # BGR, between the cells
BAR_TONE, INK = (30, 31, 34), (226, 228, 232)
LOOK = {"background": "#3c3d42", "ground": "#22231f", "tones": {"body": "#d9cfbf", "joint": "#b3a795", "default": "#cdc4b6"},
        "sky": 1.6, "key": 2.4}

PAGE = """import { stage } from './kit/stage.js';
import { layer3d, THREE } from './kit/three.js';
import * as figure from './kit/figure.js';

const S = %s;
const L = layer3d(S.w, S.h, { background: S.look.background, toneMapping: 'none', ortho: S.half, near: 0.05, far: 80 });
const key = new THREE.DirectionalLight('#ffffff', S.look.key);
L.scene.add(new THREE.HemisphereLight('#ffffff', '#5b564e', S.look.sky), key, key.target);
const floor = new THREE.Mesh(new THREE.BoxGeometry(S.floor, 0.006, S.floor), new THREE.MeshBasicMaterial({ color: S.look.ground }));
floor.position.y = -0.003;
L.scene.add(floor);
const tones = {};
const clay = (part, name) => tones[name] || (tones[name] = new THREE.MeshLambertMaterial({
  color: S.look.tones[name] || S.look.tones.default }));
let fig = null;

stage({ width: S.w, height: S.h, duration: S.cells.length, background: S.look.background,
  prepare: async () => { fig = await figure.load(S.model, { material: clay }); L.scene.add(fig.root); },
  draw: (g, t) => {
    const c = S.cells[Math.min(S.cells.length - 1, Math.max(0, Math.round(t)))];
    fig.setPose(c.pose);
    L.look(c.eye, c.target);
    key.position.set(...c.light);
    key.target.position.set(...c.target);
    key.target.updateMatrixWorld();
    L.draw(g);
  } });
"""


def _poses(model: export.Model, names) -> dict:
    """{name: pose} for the sheet: the names asked for (all the model's when none; 'rest' is the unposed figure)."""
    wanted = list(names) if names else (list(model.poses) or ["rest"])
    out = {}
    for n in wanted:
        if n in model.poses:
            out[n] = model.poses[n]
        elif n == "rest":
            out[n] = {}
        else:
            raise SystemExit(f"no pose {n!r} in {model.name} (poses: {', '.join(model.poses) or 'none'}; 'rest' always works)")
    return out


def framing(model: export.Model, poses: dict, views: list[str], aspect: float) -> dict:
    """One scale for every cell: the orthographic half-height that fits every pose in every view (and the ground),
    each view centred across on its own poses, all at one height."""
    posed = [skin.pose(model, p) for p in poses.values()]
    ys = np.concatenate([p[:, 1] for p in posed] + [[0.0]])
    half_h = (ys.max() - ys.min()) / 2
    out = {"centre_y": float((ys.max() + ys.min()) / 2), "views": {}}
    half = half_h
    for v in views:
        a = np.radians(VIEWS[v])
        right = np.array([np.cos(a), 0.0, -np.sin(a)])
        across = np.concatenate([p @ right for p in posed])
        out["views"][v] = float((across.max() + across.min()) / 2)
        half = max(half, (across.max() - across.min()) / 2 / aspect)
    out["half"] = float(half * 1.07)
    return out


def _camera(view: str, fr: dict) -> dict:
    a = np.radians(VIEWS[view])
    back = np.array([np.sin(a), 0.0, np.cos(a)])            # from the figure towards the camera
    right = np.array([np.cos(a), 0.0, -np.sin(a)])
    target = fr["views"][view] * right + np.array([0.0, fr["centre_y"], 0.0])
    light = target + 6.0 * (0.55 * back + 0.75 * np.array([0.0, 1.0, 0.0]) - 0.45 * right)
    return {"eye": (target + 20.0 * back).tolist(), "target": target.tolist(), "light": light.tolist()}


def _label(img: np.ndarray, box: list[int], text: str) -> None:
    x, y, w, h = box
    img[y:y + h, x:x + w] = BAR_TONE
    cv2.putText(img, text, (x + 10, y + h - 9), cv2.FONT_HERSHEY_SIMPLEX, 0.55, INK, 1, cv2.LINE_AA)


def _film(folder: Path, model_json: Path, settings: dict) -> None:
    from ..pack.kit import vendor_three
    shutil.copytree(REPO / "kit", folder / "kit", ignore=shutil.ignore_patterns("README.md", "vendor"))
    vendor_three(folder / "kit")
    (folder / "model").mkdir()
    meta = json.loads(model_json.read_text())
    for name in (model_json.name, meta["bin"]):
        shutil.copyfile(model_json.parent / name, folder / "model" / name)
    (folder / "index.html").write_text('<!doctype html><html><head><meta charset="utf-8"><title>model sheet</title></head>'
                                       '<body><script type="module" src="main.js"></script></body></html>')
    (folder / "main.js").write_text(PAGE % json.dumps(settings))


def run(src, out, poses=None, views=None, cell=CELL) -> dict:
    """Render the sheet of `src` (a built model's json, a spec .py or a built-in spec name) to `out` (a .png) and
    write sheet.json beside it; returns what sheet.json holds."""
    out = Path(out)
    views = list(views) if views else list(VIEWS)
    unknown = [v for v in views if v not in VIEWS]
    if unknown:
        raise SystemExit(f"no view {unknown} (views: {', '.join(VIEWS)})")
    w, h = cell
    with tempfile.TemporaryDirectory(prefix="moodreel-sheet-") as tmp:
        tmp = Path(tmp)
        src_path = Path(str(src))
        model_json = src_path if src_path.suffix == ".json" else build.build_to(src, tmp / "built")
        model = export.load(model_json)
        chosen = _poses(model, poses)
        fr = framing(model, chosen, views, w / h)
        cells = [{"pose": p, "view": v} for p in chosen for v in views]
        settings = {"w": w, "h": h, "half": fr["half"], "model": f"model/{model_json.name}", "look": LOOK,
                    "floor": float(4 * fr["half"]),
                    "cells": [{"pose": chosen[c["pose"]], **_camera(c["view"], fr)} for c in cells]}
        film = tmp / "film"
        _film(film, model_json, settings)
        shots = film / "out"
        r = subprocess.run(["node", str(RENDER), "still", str(film), *[str(i) for i in range(len(cells))], "--size",
                            f"{w}x{h}", "--out", str(shots)], capture_output=True, text=True)
        if r.returncode:
            raise SystemExit(f"model sheet: the render failed: {(r.stderr or r.stdout).strip()[-1200:]}")
        pictures = [cv2.imread(str(shots / f"t_{i}.jpg")) for i in range(len(cells))]
    if any(p is None for p in pictures):
        raise SystemExit("model sheet: a still is missing")
    cols, rows = len(views), len(chosen)
    width = cols * w + (cols + 1) * GAP
    height = rows * (h + BAR) + (rows + 1) * GAP
    sheet = np.full((height, width, 3), PAPER, np.uint8)
    listed = []
    for i, (c, pic) in enumerate(zip(cells, pictures)):
        row, col = divmod(i, cols)
        x = GAP + col * (w + GAP)
        y = GAP + row * (h + BAR + GAP) + BAR
        sheet[y:y + h, x:x + w] = pic
        label = f"{c['pose']} / {c['view']}"
        bar = [x, y - BAR, w, BAR]
        _label(sheet, bar, label)
        listed.append({"view": c["view"], "pose": c["pose"], "label": label, "x": x, "y": y, "w": w, "h": h,
                       "label_box": bar})
    out.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out), sheet)
    info = {"model": model.name, "image": out.name, "size": [width, height], "poses": list(chosen), "views": views,
            "metres_per_px": round(2 * fr["half"] / h, 6), "cells": listed}
    (out.parent / "sheet.json").write_text(json.dumps(info, indent=1))
    return info
