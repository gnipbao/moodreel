"""GSAP-named ease functions, shared by the fixture generator (ground truth) and the fitter.

Names follow GSAP so a measured ease drops straight into GSAP, HyperFrames or any render(t) page:
  none, power1..4.{in,out,inOut}, sine.*, expo.*, circ.*, back.{in,out,inOut}(s), elastic.out(amp,period), bounce.out
and, for curves a style names exactly, bezier(x1,y1,x2,y2) as CSS cubic-bezier() (truth only: the fitter keeps to
the named families). The page in fixtures/ carries a JS copy of the same formulas; keep the two in step.
"""
from __future__ import annotations

import math
import re

import numpy as np

PI = np.pi


def _directions(ease_in):
    """in, out and inOut variants of one ease-in curve (out mirrors it; inOut runs it twice at double speed)."""
    def ease_out(u):
        return 1 - ease_in(1 - u)

    def ease_in_out(u):
        return np.where(u < 0.5, ease_in(2 * u) / 2, 1 - ease_in(2 - 2 * u) / 2)
    return {"in": ease_in, "out": ease_out, "inOut": ease_in_out}


BASE = {"none": lambda u: u}
for level in range(1, 5):                     # GSAP powerN is a polynomial of degree N + 1
    for direction, f in _directions(lambda u, d=level + 1: u ** d).items():
        BASE[f"power{level}.{direction}"] = f
BASE.update({
    "sine.in": lambda u: 1 - np.cos(u * PI / 2),
    "sine.out": lambda u: np.sin(u * PI / 2),
    "sine.inOut": lambda u: -(np.cos(PI * u) - 1) / 2,
    "expo.in": lambda u: np.where(u <= 0, 0.0, 2.0 ** (10 * u - 10)),
    "expo.out": lambda u: np.where(u >= 1, 1.0, 1 - 2.0 ** (-10 * u)),
    "expo.inOut": lambda u: np.where(u <= 0, 0.0, np.where(u >= 1, 1.0, np.where(
        u < 0.5, 2.0 ** (20 * u - 10) / 2, (2 - 2.0 ** (-20 * u + 10)) / 2))),
    "circ.in": lambda u: 1 - np.sqrt(np.clip(1 - u ** 2, 0, 1)),
    "circ.out": lambda u: np.sqrt(np.clip(1 - (u - 1) ** 2, 0, 1)),
    "circ.inOut": lambda u: np.where(u < 0.5, (1 - np.sqrt(np.clip(1 - (2 * u) ** 2, 0, 1))) / 2,
                                     (np.sqrt(np.clip(1 - (-2 * u + 2) ** 2, 0, 1)) + 1) / 2),
})


def back_in(s):
    return lambda u: (s + 1) * u ** 3 - s * u ** 2


def back_out(s):
    return lambda u: 1 + (s + 1) * (u - 1) ** 3 + s * (u - 1) ** 2


def back_inout(s):
    c2 = s * 1.525
    return lambda u: np.where(u < 0.5, ((2 * u) ** 2 * ((c2 + 1) * 2 * u - c2)) / 2,
                              ((2 * u - 2) ** 2 * ((c2 + 1) * (u * 2 - 2) + c2) + 2) / 2)


def elastic_out(amp=1.0, period=0.3):
    amp = max(amp, 1.0)
    p3 = period / (2 * PI) * math.asin(1 / amp)
    return lambda u: np.where(u >= 1, 1.0, amp * 2.0 ** (-10 * u) * np.sin((u - p3) * 2 * PI / period) + 1)


def bounce_out(u):
    n1, d1 = 7.5625, 2.75
    u = np.asarray(u, dtype=float)
    return np.where(u < 1 / d1, n1 * u * u,
           np.where(u < 2 / d1, n1 * (u - 1.5 / d1) ** 2 + 0.75,
           np.where(u < 2.5 / d1, n1 * (u - 2.25 / d1) ** 2 + 0.9375, n1 * (u - 2.625 / d1) ** 2 + 0.984375)))


def bezier(x1, y1, x2, y2):
    """CSS cubic-bezier(x1, y1, x2, y2): y as a function of x, inverting x(s) on a fine grid (x1, x2 in [0, 1])."""
    s = np.linspace(0, 1, 4001)
    bx = 3 * (1 - s) ** 2 * s * x1 + 3 * (1 - s) * s ** 2 * x2 + s ** 3
    by = 3 * (1 - s) ** 2 * s * y1 + 3 * (1 - s) * s ** 2 * y2 + s ** 3
    return lambda u: np.interp(u, bx, by)


_NAME = re.compile(r"^([a-z0-9]+(?:\.(?:in|out|inOut))?)(?:\(([^)]*)\))?$")


def get(name: str):
    """'power3.out' | 'back.out(1.7)' | 'elastic.out(1,0.3)' -> f(u) on numpy arrays, u in [0, 1]."""
    m = _NAME.match(name.replace(" ", ""))
    if not m:
        raise ValueError(f"bad ease {name!r}")
    base, args = m.group(1), [float(x) for x in m.group(2).split(",")] if m.group(2) else []
    if base in BASE:
        return BASE[base]
    if base == "back.in":
        return back_in(*(args or [1.7]))
    if base == "back.out":
        return back_out(*(args or [1.7]))
    if base == "back.inOut":
        return back_inout(*(args or [1.7]))
    if base == "elastic.out":
        return elastic_out(*(args or [1.0, 0.3]))
    if base == "bounce.out":
        return bounce_out
    if base == "bezier" and len(args) == 4:
        return bezier(*args)
    raise ValueError(f"unknown ease {name!r}")


def family(name: str) -> str:
    """'back.out(1.7)' -> 'back.out'."""
    return name.split("(")[0]


def shape_class(name: str) -> str:
    """Coarse class used for style statistics: linear | in | out | inOut, plus +overshoot / +oscillate."""
    fam = family(name)
    if fam == "none":
        return "linear"
    if fam == "bezier":                         # slow where the control point lies on the flat side of the diagonal
        x1, y1, x2, y2 = (float(v) for v in name.split("(")[1].rstrip(")").split(","))
        slow_in, slow_out = y1 < x1, y2 > x2
        c = "inOut" if slow_in and slow_out else "in" if slow_in else "out" if slow_out else "linear"
        y = bezier(x1, y1, x2, y2)(np.linspace(0, 1, 401))      # overshoot as drawn, not as the handles lean
        return c + ("+overshoot" if y.max() > 1.02 or y.min() < -0.02 else "")
    direction = fam.split(".")[1]
    if fam.startswith("back."):
        return f"{direction}+overshoot"
    if fam.startswith("elastic.") or fam.startswith("bounce."):
        return f"{direction}+oscillate"
    return direction


def candidates():
    """Every (name, extra_param_count) the fitter tries."""
    out = [(n, 0) for n in BASE]
    for s in (0.8, 1.2, 1.7, 2.2, 3.0, 4.0):
        out += [(f"back.out({s:g})", 1), (f"back.in({s:g})", 1)]
    for a in (1.0, 1.3):
        for p in (0.3, 0.45, 0.6):
            out.append((f"elastic.out({a:g},{p:g})", 2))
    out.append(("bounce.out", 0))
    return out
