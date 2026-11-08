"""A spec into one skinned model: every part meshed from its distance field and bound to its bones.

A spec is a Python module (or the built-in `mannequin`: mannequin.py is the example to copy):

  NAME = "mannequin"
  BONES = {"hips": (None, (0, 0.96, 0)), "spine": ("hips", (0, 1.06, 0)), ...}   bone -> (parent, rest joint position)
  PARTS = {"torso": Part(sdf=..., bone="chest", material="body"), ...}            one closed surface each
  POSES = {"stand": {...}, "walk": {"l_thigh": (-22, 0, 0), ...}}                 bone -> XYZ Euler degrees
  COLLIDE = [("l_forearm", "torso"), ...]                                          pairs check.py measures
  LANDMARKS = {"eye_l": (x, y, z), ...}                                           optional: named rest-pose points
  EXPRESSIONS = {"blink": {...}, ...}                                              optional, written like POSES
  STEP = 0.004                                                                    optional: default grid step (m)
  MATERIALS = {...}                                                               optional: copied into the json

Metres, y up; the figure faces +z and its left is +x. Bones carry no rotation at rest, only a position. A part's
`bone` is one bone (weight 1) or {bone: weight}; `weights` (a function of the rest points, see along()) lets a part
bend across a joint instead. A humanoid has at least the bones in HUMANOID.
"""
from __future__ import annotations

import importlib
import importlib.util
import os
import re
import sys
import time
import types
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from . import export, mesh, skin

BUILTIN = {"mannequin": "moodreel.model3d.mannequin"}
HUMANOID = ("hips", "spine", "chest", "neck", "head", "l_upperarm", "l_forearm", "l_hand", "r_upperarm", "r_forearm",
            "r_hand", "l_thigh", "l_shin", "l_foot", "r_thigh", "r_shin", "r_foot")


@dataclass
class Part:
    sdf: object                        # a field from sdf.py: f(P) -> distances, f.bounds
    bone: object                       # a bone's name, or {bone: weight}
    material: str = "default"
    step: float | None = None          # grid step in metres (default: the spec's STEP, else from the part's size)
    weights: object = None             # optional: rest points (N, 3) -> {bone: (N,) weights}; replaces `bone`


def along(first: str, second: str, start, end):
    """Weights that hand a part over from bone `first` to bone `second` between the points start and end (a smooth
    step along start -> end): a sleeve or a skin that bends at the joint between them."""
    a = np.asarray(start, float)
    span = np.asarray(end, float) - a
    length2 = float(span @ span)

    def weights(P):
        s = np.clip(((np.asarray(P, float) - a) @ span) / length2, 0.0, 1.0)
        s = s * s * (3.0 - 2.0 * s)
        return {first: 1.0 - s, second: s}
    return weights


def load_spec(spec):
    """A spec module from a .py path or a built-in name; a module (or any object with BONES and PARTS) as is."""
    if isinstance(spec, types.ModuleType) or (hasattr(spec, "BONES") and hasattr(spec, "PARTS")):
        return spec
    text = str(spec)
    if text in BUILTIN:
        return importlib.import_module(BUILTIN[text])
    path = Path(text)
    if path.suffix != ".py" or not path.is_file():
        raise SystemExit(f"{text}: not a model spec (a .py file, or built in: {', '.join(BUILTIN)})")
    name = "moodreel_spec_" + re.sub(r"\W", "_", path.stem)
    found = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(found)
    sys.modules[name] = module                     # dataclasses and pickling look modules up by name
    folder = str(path.resolve().parent)
    sys.path.insert(0, folder)                     # a spec may import helpers kept beside it
    try:
        found.loader.exec_module(module)
    finally:
        sys.path.remove(folder)
    return module


def validate(spec) -> None:
    """Raise ValueError on a spec that can't be built: what is missing or names something that isn't there."""
    for key in ("NAME", "BONES", "PARTS"):
        if not hasattr(spec, key):
            raise ValueError(f"the spec has no {key}")
    if not re.fullmatch(r"[\w.-]+", str(spec.NAME)):
        raise ValueError(f"NAME {spec.NAME!r}: use letters, digits, '_', '-' or '.' (it names the files)")
    bones = spec.BONES
    skin.bone_table(bones)                         # roots and loops
    for name, (parent, head) in bones.items():
        if parent is not None and parent not in bones:
            raise ValueError(f"bone {name}: parent {parent!r} is not a bone")
        if np.asarray(head, float).shape != (3,):
            raise ValueError(f"bone {name}: its position must be (x, y, z)")
    if not spec.PARTS:
        raise ValueError("the spec has no parts")
    for name, part in spec.PARTS.items():
        if not callable(part.sdf) or not hasattr(part.sdf, "bounds"):
            raise ValueError(f"part {name}: sdf must be a field from moodreel.model3d.sdf")
        lo, hi = part.sdf.bounds
        if not (np.all(np.isfinite(lo)) and np.all(np.isfinite(hi))):
            raise ValueError(f"part {name}: its field is unbounded (intersect planes with something finite)")
        if part.weights is None:
            used = [part.bone] if isinstance(part.bone, str) else list(dict(part.bone))
            missing = [b for b in used if b not in bones]
            if missing:
                raise ValueError(f"part {name}: no bone {missing}")
    for kind in ("POSES", "EXPRESSIONS"):
        for pose_name, pose in (getattr(spec, kind, None) or {}).items():
            missing = [b for b in pose if b not in bones]
            if missing:
                raise ValueError(f"{kind} {pose_name}: no bone {missing}")
            bad = [b for b, v in pose.items() if np.asarray(v, float).shape != (3,)]
            if bad:
                raise ValueError(f"{kind} {pose_name}: {bad} need three angles (rx, ry, rz) in degrees")
    for pair in getattr(spec, "COLLIDE", None) or []:
        missing = [p for p in pair if p not in spec.PARTS]
        if len(pair) != 2 or missing:
            raise ValueError(f"COLLIDE {pair}: must name two parts ({missing} are not parts)")


def part_step(part: Part, spec) -> float:
    """The part's own step, else the spec's STEP, else a twelfth of its bounds' smallest side within 1.5-4 mm."""
    if part.step:
        return float(part.step)
    if getattr(spec, "STEP", None):
        return float(spec.STEP)
    lo, hi = part.sdf.bounds
    return float(np.clip((hi - lo).min() / 12.0, 0.0015, 0.004))


def bind(part: Part, verts: np.ndarray, index: dict) -> tuple[np.ndarray, np.ndarray]:
    """(V, 4) bone indices and weights for a part's vertices: the four heaviest bones, normalised to sum to 1."""
    n = len(verts)
    if part.weights is not None:
        table = part.weights(verts)
    elif isinstance(part.bone, str):
        table = {part.bone: 1.0}
    else:
        table = dict(part.bone)
    missing = [b for b in table if b not in index]
    if missing:
        raise ValueError(f"weights name bones that aren't there: {missing}")
    names = list(table)
    W = np.clip(np.stack([np.broadcast_to(np.asarray(table[b], float), (n,)) for b in names], axis=1), 0.0, None)
    keep = min(4, len(names))
    order = np.argsort(-W, axis=1, kind="stable")[:, :keep]
    top = np.take_along_axis(W, order, axis=1)
    total = top.sum(axis=1, keepdims=True)
    if (total <= 0).any():
        raise ValueError("some vertices have no weight on any bone")
    idx = np.zeros((n, 4), np.int64)
    wts = np.zeros((n, 4))
    idx[:, :keep] = np.array([index[b] for b in names])[order]
    wts[:, :keep] = top / total
    return idx, wts


def _plain_pose(pose: dict) -> dict:
    return {b: [float(x) for x in v] for b, v in pose.items()}


def build(spec, workers: int | None = None, log=None) -> export.Model:
    """The spec's parts meshed and bound, as one model (arrays rounded as the bin stores them)."""
    spec = load_spec(spec)
    validate(spec)
    names, parent, heads = skin.bone_table(spec.BONES)
    index = {n: i for i, n in enumerate(names)}
    bones = [{"name": n, "parent": names[parent[i]] if parent[i] >= 0 else None, "head": heads[i].tolist()}
             for i, n in enumerate(names)]
    items = list(spec.PARTS.items())
    t0 = time.time()

    def one(item):
        name, part = item
        step = part_step(part, spec)
        lo, hi = part.sdf.bounds
        m = mesh.extract(part.sdf, lo - 2 * step, hi + 2 * step, step)
        if not len(m.faces):
            raise ValueError(f"part {name}: no surface inside its bounds")
        idx, wts = bind(part, m.verts, index)
        return m, idx, wts, step

    # numpy lets go of the GIL inside its loops, so parts mesh side by side on threads
    with ThreadPoolExecutor(max_workers=workers or min(8, os.cpu_count() or 1)) as pool:
        done = list(pool.map(one, items))
    verts, normals, faces, sidx, swts, parts = [], [], [], [], [], []
    nv = nf = 0
    for (name, part), (m, idx, wts, step) in zip(items, done):
        per_bone = np.zeros(len(names))
        np.add.at(per_bone, idx.ravel(), wts.ravel())
        parts.append({"name": name, "material": part.material, "first": nv, "count": int(len(m.verts)),
                      "face_first": nf, "face_count": int(len(m.faces)), "bone": names[int(per_bone.argmax())],
                      "step": step})
        verts.append(m.verts)
        normals.append(m.normals)
        faces.append(m.faces + nv)
        sidx.append(idx)
        swts.append(wts)
        nv += len(m.verts)
        nf += len(m.faces)
    model = export.Model(
        name=str(spec.NAME), verts=np.concatenate(verts), normals=np.concatenate(normals), faces=np.concatenate(faces),
        skin_index=np.concatenate(sidx), skin_weight=np.concatenate(swts), bones=bones, parts=parts,
        landmarks={k: [float(x) for x in v] for k, v in (getattr(spec, "LANDMARKS", None) or {}).items()},
        poses={k: _plain_pose(v) for k, v in (getattr(spec, "POSES", None) or {}).items()},
        expressions={k: _plain_pose(v) for k, v in (getattr(spec, "EXPRESSIONS", None) or {}).items()},
        collide=[tuple(c) for c in getattr(spec, "COLLIDE", None) or []],
        materials=dict(getattr(spec, "MATERIALS", None) or {}))
    if log:
        log(f"{len(parts)} parts, {nv} vertices, {nf} triangles in {time.time() - t0:.1f}s")
    return export.as_stored(model)


def build_to(spec, out_dir, workers: int | None = None, log=None) -> Path:
    """Build the spec and write <NAME>.json and <NAME>.bin into out_dir; returns the json's path."""
    return export.write(build(spec, workers, log), out_dir)
