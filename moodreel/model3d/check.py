"""Is a model sound? Closed parts, nothing floating, and how deep parts sink into each other in every pose.

  closed       every part's mesh is closed (each edge on two faces, wound consistently); its Euler characteristic
               V - E + F is 2 for one piece without handles, so a part that broke in two (too coarse a step) reads 4
  floating     parts are in contact when their surfaces come within 2 mm. The distance is read off the fields
               themselves: one part's vertices, evaluated in the other part's distance field, both ways round. The
               parts in contact form groups; every part outside the biggest group is floating (a hand that never
               reaches its wrist)
  penetration  for each pose and each COLLIDE pair (a, b): a's skinned vertices are carried back into the rest frame
               of b's bone (b's heaviest bone) and measured in b's field; the depth is the largest -distance. So a
               forearm driven 3 cm into the torso reads 30 mm wherever the two happen to be in the pose

Nothing here needs a collision library: the fields the parts were carved from answer every distance question.
"""
from __future__ import annotations

import numpy as np

from . import build, export, mesh, skin

CONTACT = 0.002                        # metres: parts this close touch


def _ranges(model: export.Model) -> dict:
    return {p["name"]: (p["first"], p["first"] + p["count"]) for p in model.parts}


def parts_report(model: export.Model) -> list[dict]:
    out = []
    for p in model.parts:
        t = mesh.topology(model.part_faces(p["name"]))
        out.append({"name": p["name"], "closed": t["closed"], "euler": t["euler"], "triangles": p["face_count"]})
    return out


def _near(points: np.ndarray, lo: np.ndarray, hi: np.ndarray, pad: float) -> np.ndarray:
    return points[np.all((points >= lo - pad) & (points <= hi + pad), axis=1)]


def contacts(spec, model: export.Model, gap: float = CONTACT) -> list[tuple[str, str, float]]:
    """Every pair of parts within `gap`: (a, b, closest distance in metres; negative where they overlap)."""
    spans = _ranges(model)
    names = [p["name"] for p in model.parts]
    pts = {n: model.verts[a:b] for n, (a, b) in spans.items()}
    box = {n: (v.min(axis=0), v.max(axis=0)) for n, v in pts.items()}
    out = []
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            (alo, ahi), (blo, bhi) = box[a], box[b]
            if np.any(alo > bhi + gap) or np.any(blo > ahi + gap):
                continue
            best = np.inf
            for one, other in ((a, b), (b, a)):
                near = _near(pts[one], *box[other], gap + 1e-4)
                if len(near):
                    best = min(best, float(spec.PARTS[other].sdf(near).min()))
            if best <= gap:
                out.append((a, b, best))
    return out


def groups(names: list[str], touching) -> list[list[str]]:
    """Parts joined by contact, biggest group first (ties: the one listed first)."""
    root = {n: n for n in names}

    def top(n):
        while root[n] != n:
            root[n] = root[root[n]]
            n = root[n]
        return n
    for a, b, *_ in touching:
        root[top(a)] = top(b)
    sets: dict[str, list[str]] = {}
    for n in names:
        sets.setdefault(top(n), []).append(n)
    order = sorted(sets.values(), key=lambda g: (-len(g), names.index(g[0])))
    return order


def penetration(spec, model: export.Model, pose, pairs=None) -> dict:
    """{penetration_mm, worst: [a, b] (empty when nothing sinks in), pairs: {"a/b": mm} for every pair that sinks in};
    when nothing does, clearance_mm and closest: how near the nearest pair comes."""
    pairs = list(pairs if pairs is not None else getattr(spec, "COLLIDE", None) or [])
    P = skin.pose(model, pose)
    order, _, _ = skin.bone_table(model.bones)
    M = skin.skinning_matrices(model.bones, pose, poses=model.poses)
    spans = _ranges(model)
    depth_of, worst, deepest, gap, nearest = {}, [], 0.0, np.inf, []
    for a, b in pairs:
        lo, hi = spans[a]
        bone = model.part(b)["bone"]
        back = np.linalg.inv(M[order.index(bone)])
        rest = P[lo:hi] @ back[:3, :3].T + back[:3, 3]
        d = float(spec.PARTS[b].sdf(rest).min())
        if d < gap:
            gap, nearest = d, [a, b]
        if d < 0:
            depth_of[f"{a}/{b}"] = round(-d * 1000, 2)
            if -d > deepest:
                deepest, worst = -d, [a, b]
    out = {"penetration_mm": round(deepest * 1000, 2), "worst": worst, "pairs": depth_of}
    if not worst and nearest:
        out.update(clearance_mm=round(gap * 1000, 2), closest=nearest)
    return out


def run(spec, model_json=None, workers: int | None = None) -> dict:
    """The full report for a spec (built now, or read from `model_json` when it was built already)."""
    spec = build.load_spec(spec)
    build.validate(spec)
    model = export.load(model_json) if model_json else build.build(spec, workers)
    names = [p["name"] for p in model.parts]
    if set(names) != set(spec.PARTS):
        raise SystemExit(f"{model_json}: its parts are not the spec's (built from another spec, or before an edit?): "
                         f"only in the model {sorted(set(names) - set(spec.PARTS))}, "
                         f"only in the spec {sorted(set(spec.PARTS) - set(names))}")
    per_part = parts_report(model)
    touching = contacts(spec, model)
    joined = groups(names, touching)
    poses = getattr(spec, "POSES", None) or {}
    report = {
        "name": model.name,
        "closed": all(p["closed"] for p in per_part),
        "euler": int(sum(p["euler"] for p in per_part)),
        "parts": per_part,
        "floating": [n for n in names if n not in joined[0]],
        "groups": joined if len(joined) > 1 else [],
        "triangles": int(len(model.faces)),
        "vertices": int(len(model.verts)),
        "humanoid": all(b in {x["name"] for x in model.bones} for b in build.HUMANOID),
        "poses": {name: penetration(spec, model, dict(pose)) for name, pose in poses.items()},
    }
    return report
