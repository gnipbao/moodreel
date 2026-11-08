"""A built model on disk: <NAME>.json (what it is) beside <NAME>.bin (its arrays), and back.

The bin holds five arrays, little-endian, one after another, each starting on a 4-byte boundary:

  position     float32  V x 3   metres, rest pose
  normal       float32  V x 3   unit, outward
  skin_weight  float32  V x 4   sums to 1
  skin_index   uint16   V x 4   into the json's bones list
  index        uint32   F x 3   triangles, counter-clockwise from outside, indices into the whole model

The json's `layout` gives each one's byte offset, type, count and size, so a reader needs no other convention. Its
parts list ranges of both: a part owns vertices first .. first + count - 1 and triangles face_first ..
face_first + face_count - 1 (kit/figure.js makes each part its own mesh from them). Bones are listed parents first.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

FORMAT = "moodreel-figure"
VERSION = 1
ARRAYS = (("position", "verts", "<f4", 3), ("normal", "normals", "<f4", 3), ("skin_weight", "skin_weight", "<f4", 4),
          ("skin_index", "skin_index", "<u2", 4), ("index", "faces", "<u4", 3))
TYPES = {"<f4": "float32", "<u2": "uint16", "<u4": "uint32"}


@dataclass
class Model:
    name: str
    verts: np.ndarray                  # (V, 3) rest positions, float32 values held as float64
    normals: np.ndarray                # (V, 3)
    faces: np.ndarray                  # (F, 3) int64, into the whole model
    skin_index: np.ndarray             # (V, 4) int64, into `bones`
    skin_weight: np.ndarray            # (V, 4)
    bones: list                        # [{name, parent, head}], parents first
    parts: list                        # [{name, material, first, count, face_first, face_count, bone}]
    landmarks: dict = field(default_factory=dict)
    poses: dict = field(default_factory=dict)
    expressions: dict = field(default_factory=dict)
    collide: list = field(default_factory=list)
    materials: dict = field(default_factory=dict)
    bbox: list = field(default_factory=list)

    def part(self, name: str) -> dict:
        for p in self.parts:
            if p["name"] == name:
                return p
        raise KeyError(f"no part {name!r}")

    def part_faces(self, name: str) -> np.ndarray:
        p = self.part(name)
        return self.faces[p["face_first"]:p["face_first"] + p["face_count"]]


def as_stored(model: Model) -> Model:
    """The model with its arrays rounded to what the bin keeps, so a model checked in memory and one read back from
    disk give the same numbers."""
    model.verts = np.asarray(model.verts, np.float32).astype(np.float64)
    model.normals = np.asarray(model.normals, np.float32).astype(np.float64)
    model.skin_weight = np.asarray(model.skin_weight, np.float32).astype(np.float64)
    model.skin_index = np.asarray(model.skin_index, np.int64)
    model.faces = np.asarray(model.faces, np.int64)
    model.bbox = [model.verts.min(axis=0).tolist(), model.verts.max(axis=0).tolist()] if len(model.verts) else []
    return model


def _plain(x):
    """JSON-ready: tuples and numpy numbers as lists and floats."""
    if isinstance(x, dict):
        return {str(k): _plain(v) for k, v in x.items()}
    if isinstance(x, (list, tuple, np.ndarray)):
        return [_plain(v) for v in x]
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (np.floating, float)):
        return float(x)
    return x


def write(model: Model, out_dir) -> Path:
    """<out_dir>/<name>.json and <name>.bin; returns the json's path."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    model = as_stored(model)
    layout, chunks, at = {}, [], 0
    for key, attr, dtype, size in ARRAYS:
        data = np.ascontiguousarray(np.asarray(getattr(model, attr)).astype(dtype))
        raw = data.tobytes()
        layout[key] = {"offset": at, "type": TYPES[dtype], "count": int(len(data)), "size": size}
        chunks.append(raw)
        at += len(raw)
        pad = (-at) % 4
        chunks.append(b"\0" * pad)
        at += pad
    bin_name = f"{model.name}.bin"
    (out / bin_name).write_bytes(b"".join(chunks))
    meta = {
        "format": FORMAT, "version": VERSION, "name": model.name, "unit": "m", "up": "+y", "front": "+z",
        "bin": bin_name, "byteLength": at, "layout": layout,
        "vertexCount": int(len(model.verts)), "triangleCount": int(len(model.faces)),
        "parts": _plain(model.parts), "bones": _plain(model.bones), "landmarks": _plain(model.landmarks),
        "poses": _plain(model.poses), "expressions": _plain(model.expressions), "collide": _plain(model.collide),
        "materials": _plain(model.materials), "bbox": model.bbox,
    }
    path = out / f"{model.name}.json"
    path.write_text(json.dumps(meta, indent=1))
    return path


def load(path) -> Model:
    """A model written by write() (or `moodreel model build`)."""
    path = Path(path)
    meta = json.loads(path.read_text())
    if meta.get("format") != FORMAT:
        raise ValueError(f"{path} is not a {FORMAT} json")
    raw = (path.parent / meta["bin"]).read_bytes()
    arrays = {}
    for key, attr, dtype, size in ARRAYS:
        spec = meta["layout"][key]
        arr = np.frombuffer(raw, dtype=dtype, count=spec["count"] * size, offset=spec["offset"]).reshape(-1, size)
        arrays[attr] = arr.astype(np.float64 if dtype == "<f4" else np.int64)
    return Model(name=meta["name"], bones=meta["bones"], parts=meta["parts"], landmarks=meta.get("landmarks") or {},
                 poses=meta.get("poses") or {}, expressions=meta.get("expressions") or {},
                 collide=[tuple(c) for c in meta.get("collide") or []], materials=meta.get("materials") or {},
                 bbox=meta.get("bbox") or [], **arrays)
