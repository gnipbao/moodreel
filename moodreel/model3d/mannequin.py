"""A generic jointed figure, 1.72 m tall: the built-in spec (`moodreel model build mannequin`) and the test model.

An artist's wooden mannequin in metres: an egg of a head, ball joints at the shoulders, elbows and knees, tapered
limbs, and hands of a palm and five fingers. It rests in an A-pose, the arms 40 degrees out from hanging straight
down, so every part is its own shape touching only its neighbours (no hand against a thigh). Its poses stand it up,
walk it and have it write at a standing desk; the writing arms are solved with skin.reach, the same two-bone solve
figure.js runs. Every field a spec can have is used (but STEP: each part sets its own), so this is also the example
to copy for a new character.
"""
from __future__ import annotations

import numpy as np

from . import sdf
from .build import Part, along
from .skin import FRONT, hinge, matrix_euler, reach

NAME = "mannequin"
A_POSE = 40.0                          # the arms' angle out from hanging straight down, at rest (degrees)
SIDES = {"l": 1.0, "r": -1.0}          # the figure's left is +x
SHOULDER = (0.175, 1.415, 0.0)
UPPER, FORE = 0.29, 0.255              # upper arm and forearm, joint to joint
# finger: (knuckle along the hand, across the hand towards the thumb, splay, length, radius at the knuckle)
FINGERS = {"index": (0.088, 0.026, 0.10, 0.074, 0.0094), "middle": (0.092, 0.008, 0.02, 0.082, 0.0097),
           "ring": (0.089, -0.010, -0.06, 0.076, 0.0091), "pinky": (0.083, -0.027, -0.14, 0.062, 0.0081)}


def _unit(v) -> np.ndarray:
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


def arm(side: str):
    """Rest shoulder, elbow and wrist of one arm, the direction down it, and the palm's outward normal (down and in,
    towards the thigh; the thumb then points forward)."""
    s = SIDES[side]
    a = np.radians(A_POSE)
    down = np.array([s * np.sin(a), -np.cos(a), 0.0])
    palm = np.array([-s * np.cos(a), -np.sin(a), 0.0])
    shoulder = np.array([s * SHOULDER[0], SHOULDER[1], SHOULDER[2]])
    elbow = shoulder + UPPER * down
    return shoulder, elbow, elbow + FORE * down, down, palm


def _finger_line(side: str, finger: str):
    _, _, wrist, down, palm = arm(side)
    at, across, splay, length, radius = FINGERS[finger]
    base = wrist + at * down + across * FRONT
    return base, _unit(down + splay * FRONT), length, radius


def _thumb_line(side: str):
    _, _, wrist, down, palm = arm(side)
    return wrist + 0.026 * down + 0.028 * FRONT + 0.004 * palm, _unit(0.7 * down + 0.62 * FRONT + 0.3 * palm), 0.056, 0.0112


def _leg_x(side: str) -> float:
    return SIDES[side] * 0.09


# skeleton

BONES = {"hips": (None, (0.0, 0.96, 0.0)), "spine": ("hips", (0.0, 1.06, 0.0)), "chest": ("spine", (0.0, 1.24, 0.0)),
         "neck": ("chest", (0.0, 1.455, -0.008)), "head": ("neck", (0.0, 1.565, -0.004))}
for _s in SIDES:
    _sh, _el, _wr, _, _ = arm(_s)
    BONES[f"{_s}_upperarm"] = ("chest", tuple(float(v) for v in _sh))
    BONES[f"{_s}_forearm"] = (f"{_s}_upperarm", tuple(float(v) for v in _el))
    BONES[f"{_s}_hand"] = (f"{_s}_forearm", tuple(float(v) for v in _wr))
    BONES[f"{_s}_thumb"] = (f"{_s}_hand", tuple(float(v) for v in _thumb_line(_s)[0]))
    for _f in FINGERS:
        BONES[f"{_s}_{_f}"] = (f"{_s}_hand", tuple(float(v) for v in _finger_line(_s, _f)[0]))
    BONES[f"{_s}_thigh"] = ("hips", (_leg_x(_s), 0.90, 0.0))
    BONES[f"{_s}_shin"] = (f"{_s}_thigh", (_leg_x(_s), 0.49, 0.008))
    BONES[f"{_s}_foot"] = (f"{_s}_shin", (_leg_x(_s), 0.08, -0.012))


# parts

def _head():
    skull = sdf.ellipsoid((0.0, 1.628, 0.0), (0.077, 0.098, 0.091))
    jaw = sdf.ellipsoid((0.0, 1.568, 0.028), (0.057, 0.05, 0.06))
    return sdf.smooth_union(skull, jaw, 0.04)


def _torso():
    ribs = sdf.ellipsoid((0.0, 1.30, 0.0), (0.152, 0.165, 0.102))
    yoke = sdf.capsule((-0.125, 1.405, -0.012), (0.125, 1.405, -0.012), 0.062)
    return sdf.smooth_union(ribs, yoke, 0.07)


def _pelvis():
    basin = sdf.ellipsoid((0.0, 0.96, -0.005), (0.16, 0.11, 0.105))
    hips = sdf.union(sdf.sphere(0.075, (0.09, 0.90, 0.0)), sdf.sphere(0.075, (-0.09, 0.90, 0.0)))
    return sdf.smooth_union(basin, hips, 0.05)


def _palm(side: str):
    _, _, wrist, down, palm = arm(side)
    plate = sdf.round_box((0.0, 0.0, 0.0), (0.047, 0.0135, 0.039), 0.011)
    return sdf.frame(plate, wrist + 0.042 * down, down, palm)


def _foot(side: str):
    x = _leg_x(side)
    sole = sdf.round_box((x, 0.036, 0.04), (0.04, 0.035, 0.115), 0.03)
    heel = sdf.ellipsoid((x, 0.06, -0.02), (0.038, 0.04, 0.05))
    return sdf.smooth_union(sole, heel, 0.03)


def _digit(base, direction, length, radius):
    return sdf.round_cone(base - 0.004 * direction, base + length * direction, radius, 0.8 * radius)


PARTS = {"head": Part(_head(), "head", "body", step=0.004),
         "neck": Part(sdf.capsule((0.0, 1.43, -0.012), (0.0, 1.575, -0.004), 0.045), "neck", "body", step=0.004),
         "torso": Part(_torso(), "chest", "body", step=0.006),
         # the one part that bends: its lower half rides the spine, its upper half the chest
         "abdomen": Part(sdf.ellipsoid((0.0, 1.10, 0.005), (0.13, 0.115, 0.092)), "spine", "body", step=0.006,
                         weights=along("spine", "chest", (0.0, 1.04, 0.0), (0.0, 1.20, 0.0))),
         "pelvis": Part(_pelvis(), "hips", "body", step=0.006)}
for _s in SIDES:
    _sh, _el, _wr, _dn, _ = arm(_s)
    PARTS[f"{_s}_shoulder"] = Part(sdf.sphere(0.053, _sh), f"{_s}_upperarm", "joint", step=0.004)
    PARTS[f"{_s}_upperarm"] = Part(sdf.round_cone(_sh + 0.02 * _dn, _el - 0.015 * _dn, 0.046, 0.037), f"{_s}_upperarm",
                                   "body", step=0.0045)
    PARTS[f"{_s}_elbow"] = Part(sdf.sphere(0.038, _el), f"{_s}_forearm", "joint", step=0.0035)
    PARTS[f"{_s}_forearm"] = Part(sdf.round_cone(_el + 0.012 * _dn, _wr - 0.012 * _dn, 0.036, 0.026), f"{_s}_forearm",
                                  "body", step=0.004)
    PARTS[f"{_s}_hand"] = Part(_palm(_s), f"{_s}_hand", "body", step=0.003)
    PARTS[f"{_s}_thumb"] = Part(_digit(*_thumb_line(_s)), f"{_s}_thumb", "body", step=0.002)
    for _f in FINGERS:
        PARTS[f"{_s}_{_f}"] = Part(_digit(*_finger_line(_s, _f)), f"{_s}_{_f}", "body", step=0.002)
    _x = _leg_x(_s)
    PARTS[f"{_s}_thigh"] = Part(sdf.round_cone((_x, 0.93, 0.0), (_x, 0.505, 0.006), 0.074, 0.05), f"{_s}_thigh", "body",
                                step=0.006)
    PARTS[f"{_s}_knee"] = Part(sdf.sphere(0.05, (_x, 0.49, 0.008)), f"{_s}_shin", "joint", step=0.004)
    PARTS[f"{_s}_shin"] = Part(sdf.round_cone((_x, 0.48, 0.008), (_x, 0.09, -0.012), 0.047, 0.031), f"{_s}_shin", "body",
                               step=0.005)
    PARTS[f"{_s}_foot"] = Part(_foot(_s), f"{_s}_foot", "body", step=0.0045)


def _on(part: str, near) -> tuple:
    """The point of a part's surface nearest `near` (a few Newton steps along the field's gradient)."""
    f = PARTS[part].sdf
    p = np.array([near], float)
    for _ in range(8):
        g = sdf.gradient(f, p)
        p = p - f(p)[:, None] * g / (g * g).sum()
    return tuple(float(v) for v in p[0])


# named points on the surface, rest pose: where to hang a prop, aim a camera or measure a proportion
LANDMARKS = {"head_top": _on("head", (0.0, 1.8, 0.0)), "chin": _on("head", (0.0, 1.48, 0.09)),
             "face": _on("head", (0.0, 1.63, 0.2))}
for _s in SIDES:
    _wr, _dn, _pm = arm(_s)[2:]
    LANDMARKS[f"{_s}_palm"] = _on(f"{_s}_hand", _wr + 0.042 * _dn + 0.05 * _pm)
    LANDMARKS[f"{_s}_heel"] = _on(f"{_s}_foot", (_leg_x(_s), 0.0, -0.12))

# passed through to the json for whoever shades the figure (kit/look3d.js takes these as its ramp)
MATERIALS = {"body": {"lit": "#efe6d8", "mid": "#d2c4ae", "shade": "#8c7d69"},
             "joint": {"lit": "#dccdb8", "mid": "#b9a78e", "shade": "#76654f"}}


# poses

def _about(axis, deg) -> list[float]:
    """XYZ Euler degrees of a turn by `deg` about `axis` (the bone's rest axes)."""
    k = _unit(axis)
    a = np.radians(deg)
    K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    return matrix_euler(np.eye(3) + np.sin(a) * K + (1 - np.cos(a)) * (K @ K))


def arm_pose(side: str, down: float, swing: float = 0.0, bend: float = 0.0) -> dict:
    """One arm: brought `down` degrees from the A-pose towards the side, swung `swing` degrees forward (negative: back),
    the elbow folded `bend` degrees."""
    s = SIDES[side]
    d = arm(side)[3]
    return {f"{side}_upperarm": [-swing, 0.0, -s * down], f"{side}_forearm": _about(hinge(d, d), bend)}


def leg_pose(side: str, lift: float, knee: float, foot: float = 0.0) -> dict:
    """One leg: the thigh swung `lift` degrees forward, the knee folded `knee` degrees, the foot pitched `foot` degrees
    toe-down from level."""
    return {f"{side}_thigh": [-lift, 0.0, 0.0], f"{side}_shin": [knee, 0.0, 0.0], f"{side}_foot": [foot + lift - knee, 0.0, 0.0]}


def curl(side: str, fingers: dict) -> dict:
    """Fingers folded towards the palm by the given degrees ({'index': 30, ...}; 'thumb' too)."""
    _, _, _, down, palm = arm(side)
    out = {}
    for finger, deg in fingers.items():
        line = _thumb_line(side)[1] if finger == "thumb" else _finger_line(side, finger)[1]
        out[f"{side}_{finger}"] = _about(np.cross(line, palm), deg)
    return out


STAND = {**arm_pose("l", 31, 0, 8), **arm_pose("r", 31, 0, 8),
         **curl("l", {"index": 8, "middle": 10, "ring": 12, "pinky": 14}),
         **curl("r", {"index": 8, "middle": 10, "ring": 12, "pinky": 14})}

# the passing position: poses only turn bones and the hips keep their height, so of the walk's keys this is the one
# whose standing foot stays on the ground (in a contact pose both legs reach out and both feet lift off it)
WALK = {"hips": [0.0, 3.0, 0.0], "spine": [3.0, -5.0, 0.0], "neck": [-2.0, 2.0, 0.0],
        **leg_pose("l", 1, 1, 0), **leg_pose("r", 30, 62, 18),
        **arm_pose("l", 31, 14, 22), **arm_pose("r", 31, -12, 10),
        **curl("l", {"index": 10, "middle": 12, "ring": 14, "pinky": 16}),
        **curl("r", {"index": 10, "middle": 12, "ring": 14, "pinky": 16})}

# at a standing desk: leaning in, looking down, the right hand writing and the left holding the page
DESK = {"pen": (-0.09, 1.12, 0.37), "page": (0.15, 1.10, 0.35)}
_lean = {"spine": [6.0, 0.0, 0.0], "chest": [6.0, 0.0, 0.0], "neck": [10.0, 0.0, 0.0], "head": [14.0, 0.0, 0.0]}
WRITE = reach(BONES, reach(BONES, _lean, "r", DESK["pen"]), "l", DESK["page"])
WRITE.update({**curl("r", {"thumb": 25, "index": 35, "middle": 45, "ring": 70, "pinky": 75}),     # holding the pen
              **curl("l", {"index": 4, "middle": 4, "ring": 6, "pinky": 8})})

POSES = {"stand": STAND, "walk": WALK, "write": WRITE}
EXPRESSIONS = {"nod": {"neck": (6.0, 0.0, 0.0), "head": (10.0, 0.0, 0.0)},
               "turn": {"neck": (0.0, 14.0, 0.0), "head": (0.0, 18.0, 0.0)}}

_arms = [f"{s}_{p}" for s in SIDES for p in ("forearm", "hand")]
COLLIDE = ([(a, "torso") for a in _arms] + [(a, "abdomen") for a in _arms] + [(a, "pelvis") for a in _arms]
           + [("l_thigh", "r_thigh"), ("l_shin", "r_shin"), ("l_foot", "r_foot")])
