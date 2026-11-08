"""Poses: bone rotations, linear blend skinning and a two-bone reach, the same maths as kit/figure.js.

A pose is {bone: [rx, ry, rz]}: degrees, XYZ Euler angles (three.js's Euler(x, y, z, 'XYZ'), the matrix Rx Ry Rz) about
the bone's own rest axes. At rest no bone is turned, so its axes are the world's and a bone is just a point (its head,
the joint). A bone's world matrix is its parent's times a move to its head (relative to the parent's) times its turn;
a vertex moves by the sum over its (up to four) bones of weight x world x inverse bind, the inverse bind being a move
by minus the bone's rest head. Bones a pose leaves out stay at rest. An expression ({name: weight}) adds the weighted
Euler angles of the spec's EXPRESSIONS on top: a bone turns by its pose, then by its expression.

figure.js does exactly this on the GPU and in applyBoneTransform, and check.py measures penetration with it here, so
the two must agree: tests/test_model3d.py compares them vertex by vertex in headless Chrome.
"""
from __future__ import annotations

import numpy as np

from .sdf import euler_matrix

FRONT = np.array([0.0, 0.0, 1.0])                 # the figure faces +z; its left is +x


def matrix_euler(R) -> list[float]:
    """XYZ Euler degrees of a rotation matrix, decomposed the way three.js's Euler.setFromRotationMatrix does."""
    R = np.asarray(R, float)
    y = np.arcsin(np.clip(R[0, 2], -1.0, 1.0))
    if abs(R[0, 2]) < 0.9999999:
        x = np.arctan2(-R[1, 2], R[2, 2])
        z = np.arctan2(-R[0, 1], R[0, 0])
    else:                                          # gimbal lock: y is +-90 degrees, fold z into x
        x = np.arctan2(R[2, 1], R[1, 1])
        z = 0.0
    return [float(np.degrees(x)), float(np.degrees(y)), float(np.degrees(z))]


def bone_table(bones):
    """(names, parent index per bone or -1, rest heads (B, 3)) from a model, its bones list or a spec's BONES dict.
    Parents come before their children."""
    if hasattr(bones, "bones"):
        bones = bones.bones
    if isinstance(bones, dict):
        rows = [{"name": k, "parent": v[0], "head": v[1]} for k, v in bones.items()]
    else:
        rows = list(bones)
    placed: list[dict] = []
    seen: set = set()
    pending = rows
    while pending:                                 # parents first, otherwise in the order given
        held = []
        for r in pending:
            if r["parent"] is None or r["parent"] in seen:
                placed.append(r)
                seen.add(r["name"])
            else:
                held.append(r)
        if len(held) == len(pending):
            raise ValueError(f"bones without a root or with a loop: {[r['name'] for r in held]}")
        pending = held
    names = [r["name"] for r in placed]
    index = {n: i for i, n in enumerate(names)}
    parent = np.array([-1 if r["parent"] is None else index[r["parent"]] for r in placed], int)
    heads = np.array([np.asarray(r["head"], float).reshape(3) for r in placed])
    return names, parent, heads


def resolve(pose, poses=None) -> dict:
    """A pose by name (from `poses`) or as given; None is the rest pose."""
    if pose is None:
        return {}
    if isinstance(pose, str):
        if not poses or pose not in poses:
            raise KeyError(f"no pose {pose!r} (poses: {', '.join(poses or {}) or 'none'})")
        return dict(poses[pose])
    return dict(pose)


def local_rotations(names, pose=None, expression=None, poses=None, expressions=None) -> np.ndarray:
    """(B, 3, 3): each bone's turn, its pose's Euler rotation followed by its expression's."""
    p = resolve(pose, poses)
    unknown = set(p) - set(names)
    if unknown:
        raise KeyError(f"the pose turns bones the model doesn't have: {sorted(unknown)}")
    extra: dict[str, np.ndarray] = {}
    for name, weight in (expression or {}).items():
        for bone, angles in ((expressions or {}).get(name) or {}).items():
            extra[bone] = extra.get(bone, np.zeros(3)) + float(weight) * np.asarray(angles, float)
    out = np.tile(np.eye(3), (len(names), 1, 1))
    for i, n in enumerate(names):
        if n in p:
            out[i] = euler_matrix(p[n])
        if n in extra:
            out[i] = out[i] @ euler_matrix(extra[n])
    return out


def world_matrices(bones, pose=None, expression=None, poses=None, expressions=None) -> np.ndarray:
    """(B, 4, 4): every bone's world matrix in the pose (order: bone_table's)."""
    names, parent, heads = bone_table(bones)
    turn = local_rotations(names, pose, expression, poses, expressions)
    out = np.zeros((len(names), 4, 4))
    for i in range(len(names)):
        local = np.eye(4)
        local[:3, :3] = turn[i]
        local[:3, 3] = heads[i] - (heads[parent[i]] if parent[i] >= 0 else 0.0)
        out[i] = out[parent[i]] @ local if parent[i] >= 0 else local
    return out


def skinning_matrices(bones, pose=None, expression=None, poses=None, expressions=None) -> np.ndarray:
    """(B, 4, 4): world x inverse bind, what each bone does to the vertices bound to it."""
    _, _, heads = bone_table(bones)
    W = world_matrices(bones, pose, expression, poses, expressions)
    W[:, :3, 3] -= np.einsum("bij,bj->bi", W[:, :3, :3], heads)
    return W


def _model_bones_in_index_order(model):
    """Where each of the json's bones (the order skin indices count in) sits in bone_table's order."""
    names, _, _ = bone_table(model.bones)
    order = [b["name"] for b in model.bones]
    return [names.index(n) for n in order]


def pose(model, pose=None, expression=None) -> np.ndarray:
    """The model's vertices (V, 3) in `pose` (a name from model.poses or {bone: [rx, ry, rz]}), with an optional
    expression ({name: weight} over model.expressions): linear blend skinning, as figure.js does it."""
    M = skinning_matrices(model.bones, pose, expression, getattr(model, "poses", None), getattr(model, "expressions", None))
    M = M[_model_bones_in_index_order(model)]      # skin indices count bones in the json's order
    v = np.asarray(model.verts, float)
    idx = np.asarray(model.skin_index, np.int64)
    w = np.asarray(model.skin_weight, float)
    out = np.zeros_like(v)
    for k in range(idx.shape[1]):
        use = w[:, k] != 0
        if not use.any():
            continue
        m = M[idx[use, k]]
        out[use] += w[use, k, None] * (np.einsum("vij,vj->vi", m[:, :3, :3], v[use]) + m[:, :3, 3])
    return out


def hinge(u0: np.ndarray, f0: np.ndarray) -> np.ndarray:
    """A limb's rest bending axis: the axis of the turn that takes the upper bone's direction u0 to the lower's f0,
    or, for a straight limb, the one that swings the lower bone forward (+z): an elbow folds the forearm to the front."""
    n = np.cross(u0, f0)
    if np.linalg.norm(n) > 1e-6:
        return n / np.linalg.norm(n)
    fwd = FRONT - (FRONT @ u0) * u0
    if np.linalg.norm(fwd) < 1e-6:                 # a limb along z: fold it upwards instead
        fwd = np.array([0.0, 1.0, 0.0]) - u0[1] * u0
    n = np.cross(u0, fwd)
    return n / np.linalg.norm(n)


def default_pole(side: str) -> np.ndarray:
    """Where an elbow points, in the chest's axes: behind, a little down and out to its own side."""
    out = 1.0 if side == "l" else -1.0
    return np.array([0.35 * out, -0.35, -1.0])


def _frame(a, n):
    return np.column_stack([a, n, np.cross(a, n)])


def reach(bones, pose, side: str, target, pole=None, poses=None, chain=("upperarm", "forearm", "hand")) -> dict:
    """The pose with <side>_upperarm and <side>_forearm turned so <side>_hand's head lands on `target` (world).

    Two bones, solved outright: the law of cosines places the elbow on the circle of points L1 from the shoulder and L2
    from the target, on the side the pole points to (`pole`: a world point; by default behind and below the shoulder
    in the chest's axes). Each bone then turns so its rest frame (its direction and the rest hinge axis) lands on the
    new one, so the elbow stays a hinge and the forearm does not twist. A target out of reach straightens the arm
    towards it. The same steps as figure.js's reach(). With side "" the chain's names are used as they are.
    """
    names, parent, heads = bone_table(bones)
    up, mid, end = (names.index(f"{side}_{c}" if side else c) for c in chain)
    p = resolve(pose, poses)
    W = world_matrices(bones, p, poses=poses)
    shoulder = W[up][:3, 3]
    above = W[parent[up]][:3, :3] if parent[up] >= 0 else np.eye(3)
    L1 = float(np.linalg.norm(heads[mid] - heads[up]))
    L2 = float(np.linalg.norm(heads[end] - heads[mid]))
    u0 = (heads[mid] - heads[up]) / L1
    f0 = (heads[end] - heads[mid]) / L2
    n0 = hinge(u0, f0)

    to = np.asarray(target, float) - shoulder
    dist = float(np.linalg.norm(to))
    t = to / dist if dist > 1e-9 else above @ u0
    dist = float(np.clip(dist, abs(L1 - L2) + 1e-9, L1 + L2 - 1e-9))
    aim = (np.asarray(pole, float) - shoulder) if pole is not None else above @ default_pole(side)
    side_dir = aim - (aim @ t) * t
    if np.linalg.norm(side_dir) < 1e-9:            # pole straight along the reach: any side will do, pick below
        side_dir = np.array([0.0, -1.0, 0.0]) - t[1] * t
    side_dir /= np.linalg.norm(side_dir)
    along = (L1 * L1 - L2 * L2 + dist * dist) / (2 * dist)
    off = np.sqrt(max(L1 * L1 - along * along, 0.0))
    elbow = shoulder + along * t + off * side_dir
    u1 = (elbow - shoulder) / L1
    f1 = (shoulder + dist * t - elbow) / L2
    n1 = np.cross(side_dir, t)
    n1 /= np.linalg.norm(n1)

    upper_world = _frame(u1, n1) @ _frame(u0, n0).T
    lower_world = _frame(f1, n1) @ _frame(f0, n0).T
    out = dict(p)
    out[names[up]] = matrix_euler(above.T @ upper_world)
    out[names[mid]] = matrix_euler(upper_world.T @ lower_world)
    return out
