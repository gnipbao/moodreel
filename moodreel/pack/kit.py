"""`moodreel kit <project>`: the style's executable half, written from the measurements.

  <project>/kit/eases.js core.js stage.js texture.js text.js   the shared primitives (copied from the repo's kit/)
  <project>/kit/tokens.js                                       palette roles, type sizes and weights, layout, surface
  <project>/kit/motion.js                                       eases, durations, stagger, holds, cuts, camera

Every number in tokens.js and motion.js comes from measure/*.json; each carries a comment naming its source, so
the director can see what was measured before changing it. A film copies the kit and imports from it.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import numpy as np

from ..motion import eases

REPO = Path(__file__).resolve().parents[2]
SHARED = ["eases.js", "core.js", "stage.js", "texture.js", "text.js"]
WEIGHT = {"light": 300, "regular": 400, "bold": 700, "black": 900}


def _back_for(overshoot: float) -> str:
    """back.out(s) whose peak overshoot matches the measured one."""
    u = np.linspace(0, 1, 2001)
    best = min(np.arange(0.4, 5.01, 0.1), key=lambda s: abs(eases.back_out(s)(u).max() - 1 - overshoot))
    return f"back.out({best:.1f})"


def _ease_for(role: dict | None) -> dict | None:
    if not role:
        return None
    classes = role.get("classes") or {}
    dominant = max(classes, key=classes.get) if classes else None
    names = {n: c for n, c in (role.get("eases") or {}).items() if eases.shape_class(n) == dominant} or role.get("eases") or {}
    name = max(names, key=names.get) if names else "power2.out"
    over = role.get("overshoot") or {}
    if role.get("overshoot_share", 0) >= 0.4 and over.get("median"):
        name = _back_for(over["median"])
    dur = (role.get("duration_s") or {}).get("median")
    from ..motion.fit import bezier_for
    out = {"ease": name, "class": eases.shape_class(name), "duration": dur, "bezier": bezier_for(name),
           "overshoot_share": role.get("overshoot_share"), "count": role.get("count")}
    if role.get("scale_from"):
        out["scale_from"] = role["scale_from"]["median"]
    if role.get("travel_frac_of_frame"):
        out["travel"] = role["travel_frac_of_frame"]["median"]
    if role.get("vocabulary"):
        out["vocabulary"] = role["vocabulary"]
    return out


def motion_tokens(grammar: dict) -> dict:
    if "videos" in grammar:                         # several videos: take the first that has entrances
        vid = next((v for v in grammar["videos"] if grammar["entrance"].get(v)), grammar["videos"][0])
        grammar = {"entrance": grammar["entrance"][vid], "exit": grammar["exit"][vid], "move": grammar["move"][vid],
                   "stagger": [s for s in grammar["stagger"] if s.get("video") == vid], "shots": grammar["shots"][vid]}
    sh = grammar.get("shots") or {}
    st = grammar.get("stagger") or []
    cam = grammar.get("camera") or {}
    return {
        "enter": _ease_for(grammar.get("entrance")), "exit": _ease_for(grammar.get("exit")),
        "move": _ease_for(grammar.get("move")),
        "stagger": ({"interval": float(np.median([s["interval_s"] for s in st])),
                     "order": max({s["order"] for s in st}, key=[s["order"] for s in st].count)} if st else None),
        "hold": (grammar.get("hold_s") or {}).get("median"),
        "shot": (sh.get("length_s") or {}).get("median"),
        "transitions": {"cuts": sh.get("cuts", 0), "dissolves": sh.get("dissolves", 0), "dips": sh.get("dips", 0),
                        "dissolve": (sh.get("dissolve_s") or {}).get("median"), "dip": (sh.get("dip_s") or {}).get("median"),
                        "dip_colours": sh.get("dip_colors", [])},
        "density": grammar.get("motion_density"),
        "on": (grammar.get("stepping") or {}).get("on", 1),
        "camera": cam.get("moves") or None,
    }


def style_tokens(project: Path, intake: dict) -> dict:
    m = lambda k: json.loads((project / "measure" / f"{k}.json").read_text())  # noqa: E731
    pal, tex, lay, typ = m("palette"), m("texture"), m("layout"), m("type")
    size = [int(x) for x in intake["default_size"].split("x")]
    return {
        "size": size,
        "palette": {**{k: v for k, v in pal["roles"].items() if not k.endswith("contrast")},
                    "colors": [{"hex": c["hex"], "area": c["area"]} for c in pal["colors"] if c["area"] >= 0.003]},
        "type": {"title": typ.get("title_height"), "body": typ.get("body_height"),
                 "titleWeight": WEIGHT.get(typ.get("weight_title") or "", 700),
                 "bodyWeight": WEIGHT.get(typ.get("weight_overall") or "", 400),
                 "display": "Helvetica Neue, Helvetica, Arial, sans-serif",
                 "text": "Helvetica Neue, Helvetica, Arial, sans-serif"},
        "layout": {"margin": lay.get("min_margin"), "align": lay.get("dominant_alignment"), "density": lay.get("density")},
        "texture": {"grain": tex.get("grain"), "mottle": tex.get("mottle"), "vignette": tex.get("vignette"),
                    "halftone": tex.get("halftone"), "scanlines": tex.get("scanlines"), "edges": tex["summary"].get("edges")},
    }


SOURCES = {"size": "intake.json default_size", "palette": "measure/palette.json roles, colors",
           "type": "measure/type.json (families are placeholders until the director picks licensed faces)",
           "layout": "measure/layout.json medians", "texture": "measure/texture.json medians",
           "motion": "measure/motion.json grammar"}


def _js(name, value, source):
    return f"// {source}\nexport const {name} = {json.dumps(value, indent=2, ensure_ascii=False)};\n"


def write_kit(project: Path, out: Path | None = None) -> Path:
    project = Path(project)
    out = Path(out or project / "kit")
    out.mkdir(parents=True, exist_ok=True)
    for f in SHARED:
        shutil.copyfile(REPO / "kit" / f, out / f)
    intake = json.loads((project / "intake.json").read_text())
    tokens = style_tokens(project, intake)
    head = "// Written by `moodreel kit` from the project's measurements. Edit freely: the comments say where each came from.\n\n"
    (out / "tokens.js").write_text(head + "".join(_js(k.upper(), v, SOURCES[k]) + "\n" for k, v in tokens.items()))
    motion_path = project / "measure" / "motion.json"
    mt = motion_tokens(json.loads(motion_path.read_text())["grammar"]) if motion_path.exists() else None
    source = SOURCES["motion"] + (" (no reference video: fill in from the chosen motion preset)" if mt is None else "")
    (out / "motion.js").write_text(head + "import { tween, stagger } from './core.js';\n\n" + _js("MOTION", mt, source)
                                   + MOTION_HELPERS)
    return out


MOTION_HELPERS = """
const role = r => MOTION?.[r] ?? { ease: 'power2.out', duration: 0.5 };

// progress (0-1) of an element's entrance / exit / move that starts at `at`; i staggers it within a group
export const enter = (t, at, i = 0) => tween(t, MOTION?.stagger ? stagger(at, MOTION.stagger.interval, i) : at,
  role('enter').duration ?? 0.5, role('enter').ease);
export const exit = (t, at, i = 0) => tween(t, MOTION?.stagger ? stagger(at, MOTION.stagger.interval, i) : at,
  role('exit').duration ?? 0.4, role('exit').ease);
export const move = (t, at) => tween(t, at, role('move').duration ?? 0.6, role('move').ease);
"""
