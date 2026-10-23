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

from ..measure.texture import WORK
from ..motion import eases

REPO = Path(__file__).resolve().parents[2]
SHARED = ["eases.js", "core.js", "stage.js", "texture.js", "text.js"]
WEIGHT = {"light": 300, "regular": 400, "bold": 700, "black": 900}
INK_PER_EM = 0.9


def _back_for(overshoot: float) -> str:
    """back.out(s) whose peak overshoot matches the measured one."""
    u = np.linspace(0, 1, 2001)
    best = min(np.arange(0.4, 5.01, 0.1), key=lambda s: abs(eases.back_out(s)(u).max() - 1 - overshoot))
    return f"back.out({best:.1f})"


def _ease_for(role: dict | None) -> dict | None:
    if not role:
        return None
    count = role.get("count", 1)
    named, classed = role.get("claimed", count), role.get("class_claimed", role.get("claimed", count))
    classes = role.get("classes") or {}
    ranked = sorted(classes.values(), reverse=True)
    # a tie between two classes is not a style's habit
    dominant = max(classes, key=classes.get) if classes and (len(ranked) < 2 or ranked[0] > ranked[1]) else None
    names = {n: c for n, c in (role.get("eases") or {}).items() if eases.shape_class(n) == dominant}
    curve = role.get("curve")
    dur = (role.get("duration_s") or {}).get("median")
    from ..motion.fit import bezier_for
    # a family read with confidence at least twice, for at least a third of the role's moves; else the style's own
    # curve, when the class was read as often and one bezier draws those tweens; else the timing only, and the
    # director picks the curve
    if named >= min(2, count) and 3 * named >= count and names:
        name = max(names, key=names.get)
        over = role.get("overshoot") or {}
        if role.get("overshoot_share", 0) >= 0.4 and over.get("median"):
            name = _back_for(over["median"])
        bezier, source = bezier_for(name), "named"
    elif classed >= min(2, count) and 3 * classed >= count and curve and curve["class"] == dominant:
        name, bezier = "bezier({},{},{},{})".format(*curve["bezier"]), curve["bezier"]
        dur = curve.get("duration") or dur
        source = f"one curve through {curve['tweens']} tweens whose class was read"
    else:
        out = {"ease": None, "duration": dur, "count": count,
               "unread": "no ease was read with confidence; take it from STYLE.md or the references by eye",
               "vocabulary": role.get("vocabulary")}
        # what was read, too seldom to stand for the role: a lead for the director, never used by the helpers
        if classes or curve:
            out["seen"] = {"classes": classes, "of": count,
                           **({"curve": "bezier({},{},{},{})".format(*curve["bezier"]), "curve_class": curve["class"]}
                              if curve else {})}
        return out
    out = {"ease": name, "class": eases.shape_class(name), "duration": dur, "bezier": bezier, "source": source,
           "overshoot_share": role.get("overshoot_share"), "count": count}
    if role.get("scale_from"):
        out["scale_from"] = role["scale_from"]["median"]
    if role.get("travel_frac_of_frame"):
        out["travel"] = role["travel_frac_of_frame"]["median"]
    if role.get("vocabulary"):
        out["vocabulary"] = role["vocabulary"]
    return out


def _count(role: dict | None) -> dict | None:
    """A counting number's timing and ease, and how the references print it ('#,###', '$#.#M')."""
    out = _ease_for(role)
    if out and role.get("formats"):
        out["format"] = max(role["formats"], key=role["formats"].get)
    return out


def motion_tokens(grammar: dict) -> dict:
    if "videos" in grammar:                         # several videos: take the first that has entrances
        vid = next((v for v in grammar["videos"] if grammar["entrance"].get(v)), grammar["videos"][0])
        counters = next((c for c in (grammar.get("counters") or {}).values() if c), None)
        grammar = {"entrance": grammar["entrance"][vid], "exit": grammar["exit"][vid], "move": grammar["move"][vid],
                   "stagger": [s for s in grammar["stagger"] if s.get("video") == vid], "shots": grammar["shots"][vid],
                   "counters": counters,
                   "loops": next((c for c in (grammar.get("loops") or {}).values() if c), None),
                   "particles": next((c for c in (grammar.get("particles") or {}).values() if c), None),
                   "beat": next((c for c in (grammar.get("beat") or {}).values() if c), None)}
    sh = grammar.get("shots") or {}
    every = grammar.get("stagger") or []
    st = [s for s in every if not s.get("letters")]          # elements in a group; letters in a word apart
    lt = [s for s in every if s.get("letters")]
    cam = grammar.get("camera") or {}
    return {
        "enter": _ease_for(grammar.get("entrance")), "exit": _ease_for(grammar.get("exit")),
        "move": _ease_for(grammar.get("move")), "count": _count(grammar.get("counters")),
        "stagger": ({"interval": float(np.median([s["interval_s"] for s in st])),
                     "order": max({s["order"] for s in st}, key=[s["order"] for s in st].count)} if st else None),
        "letters": ({"interval": float(np.median([s["interval_s"] for s in lt])),
                     "order": max({s["order"] for s in lt}, key=[s["order"] for s in lt].count)} if lt else None),
        "hold": (grammar.get("hold_s") or {}).get("median"),
        "shot": (sh.get("length_s") or {}).get("median"),
        "transitions": {"cuts": sh.get("cuts", 0), "dissolves": sh.get("dissolves", 0), "dips": sh.get("dips", 0),
                        "dissolve": (sh.get("dissolve_s") or {}).get("median"), "dip": (sh.get("dip_s") or {}).get("median"),
                        "dip_colours": sh.get("dip_colors", [])},
        "density": grammar.get("motion_density"),
        "on": (grammar.get("stepping") or {}).get("on", 1),
        "camera": cam.get("moves") or None,
        "loop": ({"period": grammar["loops"]["period_s"]["median"] if grammar["loops"].get("period_s") else None,
                  **{k: v["median"] for k, v in grammar["loops"]["props"].items()}} if grammar.get("loops") else None),
        "particles": (grammar.get("particles") or [None])[0],
        "beat": ({"bpm": grammar["beat"]["bpm"], "period": round(60 / grammar["beat"]["bpm"], 4),
                  "phase": grammar["beat"]["phase_s"]} if grammar.get("beat") else None),
    }


def _em(ink_height: float | None) -> float | None:
    """A line's font size from its measured ink height: a mixed-case line from ascender to descender is
    about nine tenths of the em (a line without either reads smaller; check the crops)."""
    return round(ink_height / INK_PER_EM, 4) if ink_height else None


def _design_px(periodic: dict | None, size: list[int]) -> dict | None:
    """A screen or scanline period measured at texture.WORK, in the film's design pixels."""
    return {**periodic, "period_px": round(periodic["period_px"] * max(size) / WORK, 2)} if periodic else None


def _pixel(px: dict | None, size: list[int]) -> dict | None:
    """Pixel art in the film's terms: how many design px one art pixel is, the native size kit/pixel.js draws at."""
    if not px:
        return None
    scale = max(1, round(px["scale_of_width"] * size[0]))
    return {"scale": scale, "native": [size[0] // scale, size[1] // scale], "palette_size": px["palette_size"],
            "dither": px["dither"], "palette": px["palette"]}


def _brush(b: dict | None, size: list[int]) -> dict | None:
    """Brush marks in design px: the spacing of their edges (the scale to lay kit/brush.js marks at), which way they
    run (radians, as canvas rotations) and how much they agree."""
    if not b:
        return None
    return {"spacing": round(b["edge_spacing_px"] * max(size) / WORK, 1), "angle": round(float(np.radians(b["direction_deg"])), 3),
            "agreement": b["agreement"], "coverage": b["coverage"]}


def style_tokens(project: Path, intake: dict) -> dict:
    m = lambda k: json.loads((project / "measure" / f"{k}.json").read_text())  # noqa: E731
    pal, tex, lay, typ = m("palette"), m("texture"), m("layout"), m("type")
    size = [int(x) for x in intake["default_size"].split("x")]
    return {
        "size": size,
        "palette": {**{k: v for k, v in pal["roles"].items() if not k.endswith("contrast")},
                    "colors": [{"hex": c["hex"], "area": c["area"]} for c in pal["colors"] if c["area"] >= 0.003]},
        "type": {"title": _em(typ.get("title_height")), "body": _em(typ.get("body_height")),
                 "titleWeight": typ.get("weight_title_value") or WEIGHT.get(typ.get("weight_title") or "", 700),
                 "bodyWeight": typ.get("weight_overall_value") or WEIGHT.get(typ.get("weight_overall") or "", 400),
                 "display": "Helvetica Neue, Helvetica, Arial, sans-serif",
                 "text": "Helvetica Neue, Helvetica, Arial, sans-serif"},
        "layout": {"margin": lay.get("min_margin"), "align": lay.get("dominant_alignment"), "density": lay.get("density")},
        "texture": {"grain": tex.get("grain"), "mottle": tex.get("mottle"), "vignette": tex.get("vignette"),
                    "halftone": _design_px(tex.get("halftone"), size), "scanlines": _design_px(tex.get("scanlines"), size),
                    "edges": tex["summary"].get("edges"), "pixel": _pixel(tex.get("pixel"), size),
                    "brush": _brush(tex.get("brush"), size)},
    }


SOURCES = {"size": "intake.json default_size", "palette": "measure/palette.json roles, colors",
           "type": "measure/type.json line heights as font sizes (ink = 0.9 em); families are placeholders until the "
                   "director picks licensed faces",
           "layout": "measure/layout.json medians",
           "texture": "measure/texture.json medians (screen and scanline periods in design px)",
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
    (out / "motion.js").write_text(head + "import { tween, stagger, value } from './core.js';\n\n" + _js("MOTION", mt, source)
                                   + MOTION_HELPERS)
    return out


MOTION_HELPERS = """
const role = r => ({ ...MOTION?.[r], ease: MOTION?.[r]?.ease ?? 'power2.out' });

// progress (0-1) of an element's entrance / exit / move that starts at `at`; i staggers it within a group
export const enter = (t, at, i = 0) => tween(t, MOTION?.stagger ? stagger(at, MOTION.stagger.interval, i) : at,
  role('enter').duration ?? 0.5, role('enter').ease);
export const exit = (t, at, i = 0) => tween(t, MOTION?.stagger ? stagger(at, MOTION.stagger.interval, i) : at,
  role('exit').duration ?? 0.4, role('exit').ease);
export const move = (t, at) => tween(t, at, role('move').duration ?? 0.6, role('move').ease);
// a number counting from `from` to `to`, starting at `at`, on the references' counting curve (print it as
// MOTION.count.format says: '#,###' groups thousands, '#.#' keeps one decimal)
export const count = (t, at, from, to) => value(t, at, role('count').duration ?? 1.2, from, to, role('count').ease);
// an ambient loop, -1..1, at the references' period (MOTION.loop also has how far they bob, pulse or breathe)
export const loop = (t, period = MOTION?.loop?.period ?? 2, phase = 0) => Math.sin(2 * Math.PI * (t / period + phase));
// the time of beat n on the references' grid (n may be fractional: 2.5 is the off-beat after beat 2)
export const beat = n => (MOTION?.beat?.phase ?? 0) + n * (MOTION?.beat?.period ?? 0.5);
"""
