"""Signed distance fields in numpy: the shapes a character is carved from.

A field is a callable. f(P) takes points P, an (N, 3) array in metres, and gives (N,) signed distances, negative
inside; f.bounds is (lo, hi), a box the surface lies in. Primitives (sphere, capsule, round_cone, ellipsoid,
round_box, cylinder, torus, plane) are placed (translate, rotate, place, mirror, scale) and combined (union,
intersection, difference, their smooth versions, offset, shell), so every part of a figure is one expression.

The smooth booleans use the polynomial smooth minimum: where two surfaces come within k of each other they melt into
a fillet about k wide, and further apart they meet as plain min and max would. The mesher (mesh.py) projects its
vertices onto the zero set by Newton steps, so what matters is that the zero set is the shape and the gradient points
across it; the distance itself only has to be right near the surface. The primitives are exact distances except the
ellipsoid, which is exact to first order at its surface (good enough for contact tests at a few millimetres).
"""
from __future__ import annotations

import numpy as np

INF = np.inf


class Field:
    """A distance field: fn maps (N, 3) points to (N,) distances; lo, hi bound its surface."""

    __slots__ = ("fn", "lo", "hi")

    def __init__(self, fn, lo, hi):
        self.fn = fn
        self.lo = np.asarray(lo, float).reshape(3)
        self.hi = np.asarray(hi, float).reshape(3)

    @property
    def bounds(self) -> tuple[np.ndarray, np.ndarray]:
        return self.lo.copy(), self.hi.copy()

    def __call__(self, P) -> np.ndarray:
        pts = np.asarray(P, float)
        lead = pts.shape[:-1]
        return np.asarray(self.fn(pts.reshape(-1, 3)), float).reshape(lead)


def _vec(v) -> np.ndarray:
    return np.asarray(v, float).reshape(3)


def _norm(a: np.ndarray) -> np.ndarray:
    return np.sqrt((a * a).sum(axis=-1))


def gradient(f, P, h: float = 1e-6) -> np.ndarray:
    """Central differences of f at P (N, 3): the outward normal direction, not normalised."""
    P = np.asarray(P, float)
    g = np.empty_like(P)
    for axis in range(3):
        dp = np.zeros(3)
        dp[axis] = h
        g[:, axis] = (f(P + dp) - f(P - dp)) / (2 * h)
    return g


# primitives

def sphere(r: float, center=(0.0, 0.0, 0.0)) -> Field:
    c = _vec(center)
    return Field(lambda P: _norm(P - c) - r, c - r, c + r)


def capsule(a, b, r: float) -> Field:
    """Every point within r of the segment a-b."""
    a, b = _vec(a), _vec(b)
    ab = b - a
    span = float(ab @ ab)
    if span < 1e-24:
        return sphere(r, a)

    def fn(P):
        rel = P - a
        s = np.clip((rel @ ab) / span, 0.0, 1.0)
        return _norm(rel - s[:, None] * ab) - r
    return Field(fn, np.minimum(a, b) - r, np.maximum(a, b) + r)


def round_cone(a, b, ra: float, rb: float) -> Field:
    """The convex hull of the spheres (a, ra) and (b, rb): a capsule that tapers, the usual limb.

    In the plane through the axis, a point sits at height y along a->b and distance x off it. The hull's side is the
    line touching both circles; its outward normal n = (nx, ny) has ny = (ra - rb) / L (it leans towards the thin
    end) and touches circle a at ra * n. The coordinate along that line, s = nx * y - ny * x, is 0 at the touching
    point on circle a and nx * L at the one on circle b: below 0 the nearest surface is sphere a, past nx * L it is
    sphere b, and in between it is the line, at nx * x + ny * y - ra.
    """
    a, b = _vec(a), _vec(b)
    axis = b - a
    L = float(np.sqrt(axis @ axis))
    if L <= abs(ra - rb) + 1e-12:                       # one sphere swallows the other
        return sphere(ra, a) if ra >= rb else sphere(rb, b)
    u = axis / L
    ny = (ra - rb) / L
    nx = float(np.sqrt(max(0.0, 1.0 - ny * ny)))

    def fn(P):
        rel = P - a
        y = rel @ u
        x = _norm(rel - y[:, None] * u)
        s = nx * y - ny * x
        to_a = np.sqrt(x * x + y * y) - ra
        to_b = np.sqrt(x * x + (y - L) ** 2) - rb
        side = nx * x + ny * y - ra
        return np.where(s < 0, to_a, np.where(s > nx * L, to_b, side))
    # the hull of two spheres lies inside the box around both of them
    return Field(fn, np.minimum(a - ra, b - rb), np.maximum(a + ra, b + rb))


def ellipsoid(center, radii) -> Field:
    """An ellipsoid with semi-axes `radii` along x, y, z.

    The distance is k0 (k0 - 1) / k1 with k0 = |q / r| and k1 = |q / r^2|: zero exactly on the surface, and there its
    gradient is the true normal with length 1, so it reads like a distance near the surface and stays a smooth,
    monotone field further out.
    """
    c, r = _vec(center), np.abs(_vec(radii))

    def fn(P):
        q = P - c
        k0 = _norm(q / r)
        k1 = _norm(q / (r * r))
        with np.errstate(divide="ignore", invalid="ignore"):
            d = k0 * (k0 - 1.0) / k1
        return np.where(k1 > 1e-12, d, -r.min())
    return Field(fn, c - r, c + r)


def round_box(center, half, r: float = 0.0) -> Field:
    """A box with outer half-sizes `half` and its edges rounded to radius r (r <= the smallest half-size)."""
    c, h = _vec(center), _vec(half)
    core = h - r

    def fn(P):
        q = np.abs(P - c) - core
        out = _norm(np.maximum(q, 0.0))
        return out + np.minimum(q.max(axis=1), 0.0) - r
    return Field(fn, c - h, c + h)


def box(center, half) -> Field:
    return round_box(center, half, 0.0)


def cylinder(a, b, r: float, rounding: float = 0.0) -> Field:
    """A solid cylinder of radius r from a to b, its rims rounded by `rounding`."""
    a, b = _vec(a), _vec(b)
    L = float(np.linalg.norm(b - a))
    u = (b - a) / L
    mid = (a + b) / 2
    half = L / 2 - rounding
    rad = r - rounding

    def fn(P):
        rel = P - mid
        y = rel @ u
        x = _norm(rel - y[:, None] * u)
        dx, dy = x - rad, np.abs(y) - half
        outside = np.sqrt(np.maximum(dx, 0.0) ** 2 + np.maximum(dy, 0.0) ** 2)
        return outside + np.minimum(np.maximum(dx, dy), 0.0) - rounding
    pad = np.sqrt(np.clip(1.0 - u * u, 0.0, 1.0)) * r
    return Field(fn, np.minimum(a, b) - pad, np.maximum(a, b) + pad)


def torus(center, R: float, r: float, axis=(0.0, 1.0, 0.0)) -> Field:
    """A ring of tube radius r whose centre line is the circle of radius R about `axis` through `center`."""
    c = _vec(center)
    n = _vec(axis) / np.linalg.norm(axis)

    def fn(P):
        rel = P - c
        h = rel @ n
        ring = _norm(rel - h[:, None] * n) - R
        return np.sqrt(ring * ring + h * h) - r
    pad = np.sqrt(np.clip(1.0 - n * n, 0.0, 1.0)) * R + r
    return Field(fn, c - pad, c + pad)


def plane(point, normal) -> Field:
    """The half-space behind the plane through `point`: `normal` points out of the solid. Unbounded: intersect it."""
    p, n = _vec(point), _vec(normal) / np.linalg.norm(normal)
    return Field(lambda P: (P - p) @ n, [-INF] * 3, [INF] * 3)


# placement

def euler_matrix(deg) -> np.ndarray:
    """The rotation three.js builds from Euler(x, y, z, 'XYZ') in degrees: Rx @ Ry @ Rz (applied z first)."""
    x, y, z = np.radians(np.asarray(deg, float).reshape(3))
    cx, sx, cy, sy, cz, sz = np.cos(x), np.sin(x), np.cos(y), np.sin(y), np.cos(z), np.sin(z)
    rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return rx @ ry @ rz


def _box_corners(lo, hi) -> np.ndarray:
    return np.array([[(lo, hi)[i >> k & 1][k] for k in range(3)] for i in range(8)], float)


def translate(f: Field, offset) -> Field:
    o = _vec(offset)
    return Field(lambda P: f(P - o), f.lo + o, f.hi + o)


def place(f: Field, origin=(0.0, 0.0, 0.0), rotation=None) -> Field:
    """f modelled about the origin in its own axes, set down at `origin` turned by `rotation` (a 3x3 matrix whose
    columns are f's axes in the world, or XYZ Euler degrees)."""
    o = _vec(origin)
    R = np.eye(3) if rotation is None else np.asarray(rotation, float)
    if R.shape != (3, 3):
        R = euler_matrix(R)
    if not np.all(np.isfinite(f.lo)) or not np.all(np.isfinite(f.hi)):
        lo, hi = [-INF] * 3, [INF] * 3
    else:
        world = _box_corners(f.lo, f.hi) @ R.T + o
        lo, hi = world.min(axis=0), world.max(axis=0)
    return Field(lambda P: f((P - o) @ R), lo, hi)


def rotate(f: Field, rotation, center=(0.0, 0.0, 0.0)) -> Field:
    """f turned by `rotation` (matrix or XYZ Euler degrees) about `center`."""
    c = _vec(center)
    return place(translate(f, -c), c, rotation)


def frame(f: Field, origin, x_axis, y_axis) -> Field:
    """f placed with its x axis along `x_axis` and its y axis as close to `y_axis` as stays square to it."""
    x = _vec(x_axis) / np.linalg.norm(x_axis)
    y = _vec(y_axis) - (_vec(y_axis) @ x) * x
    y /= np.linalg.norm(y)
    return place(f, origin, np.column_stack([x, y, np.cross(x, y)]))


def mirror(f: Field, axis: int = 0) -> Field:
    """f reflected through the plane where coordinate `axis` is 0: a left part from a right one."""
    flip = np.ones(3)
    flip[axis] = -1.0
    lo, hi = f.lo * flip, f.hi * flip
    return Field(lambda P: f(P * flip), np.minimum(lo, hi), np.maximum(lo, hi))


def scale(f: Field, s: float) -> Field:
    return Field(lambda P: f(P / s) * s, f.lo * s, f.hi * s)


# booleans

def union(*fields: Field) -> Field:
    lo = np.min([f.lo for f in fields], axis=0)
    hi = np.max([f.hi for f in fields], axis=0)
    return Field(lambda P: np.min([f(P) for f in fields], axis=0), lo, hi)


def intersection(*fields: Field) -> Field:
    lo = np.max([f.lo for f in fields], axis=0)
    hi = np.min([f.hi for f in fields], axis=0)
    return Field(lambda P: np.max([f(P) for f in fields], axis=0), lo, hi)


def difference(f: Field, g: Field) -> Field:
    """f with g cut away."""
    return Field(lambda P: np.maximum(f(P), -g(P)), f.lo, f.hi)


def _smin(a: np.ndarray, b: np.ndarray, k: float) -> np.ndarray:
    """Polynomial smooth minimum: a quadratic blend over the band |a - b| < k, at most k / 4 below min(a, b)."""
    if k <= 0:
        return np.minimum(a, b)
    w = np.clip(0.5 + 0.5 * (b - a) / k, 0.0, 1.0)
    return a * w + b * (1.0 - w) - k * w * (1.0 - w)


def smooth_union(f: Field, g: Field, k: float) -> Field:
    """f and g melted together with a fillet about k wide. The blend can swell the surface by up to k / 4 (more for
    fields whose gradient is shorter than 1), so the bounds grow by k / 2."""
    grow = k / 2
    return Field(lambda P: _smin(f(P), g(P), k), np.minimum(f.lo, g.lo) - grow, np.maximum(f.hi, g.hi) + grow)


def smooth_difference(f: Field, g: Field, k: float) -> Field:
    """f with g carved out, the cut's rim rounded about k wide."""
    return Field(lambda P: -_smin(-f(P), g(P), k), f.lo, f.hi)


def smooth_intersection(f: Field, g: Field, k: float) -> Field:
    return Field(lambda P: -_smin(-f(P), -g(P), k), np.maximum(f.lo, g.lo), np.minimum(f.hi, g.hi))


def blend(fields, k: float) -> Field:
    """Several fields smooth-unioned in turn with the same k."""
    out = fields[0]
    for g in fields[1:]:
        out = smooth_union(out, g, k)
    return out


def offset(f: Field, d: float) -> Field:
    """f grown by d (shrunk if d < 0): rounds every edge by d."""
    return Field(lambda P: f(P) - d, f.lo - d, f.hi + d)


def shell(f: Field, thickness: float) -> Field:
    """A skin of `thickness` centred on f's surface."""
    t = thickness / 2
    return Field(lambda P: np.abs(f(P)) - t, f.lo - t, f.hi + t)
