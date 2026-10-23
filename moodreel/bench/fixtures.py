"""Test films with known motion: one spec draws the page and computes the truth.

Each fixture is a render-contract page (window.DUR, window.render(t), window.READY) written from a spec, plus a
truth.json computed from the same spec with the same ease formulas (motion/eases.py; the page carries a JS copy).
Events whose kind the measurement does not cover yet (rotation, anisotropic scale, line draw-on, per-letter
text, a counter's value) are kept with scope "v1": reported, but left out of the acceptance numbers.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from ..motion import eases

V1_PROPS = {"rot", "sx", "sy", "draw", "value"}
FONT = "Helvetica, Arial, sans-serif"


def A(prop, frm, to, t, d, ease):
    return {"prop": prop, "from": frm, "to": to, "t": t, "d": d, "ease": ease}


def text(id_, s, size, color, x, y, anims, bold=True):
    return {"id": id_, "kind": "text", "text": s, "font": f"{'bold ' if bold else ''}{size}px {FONT}",
            "color": color, "x": x, "y": y, "anims": anims}


def rect(id_, w, h, color, x, y, anims, r=0, **kw):
    return {"id": id_, "kind": "rect", "w": w, "h": h, "r": r, "color": color, "x": x, "y": y, "anims": anims, **kw}


def circle(id_, r, color, x, y, anims):
    return {"id": id_, "kind": "circle", "r": r, "color": color, "x": x, "y": y, "anims": anims}


def counter(id_, size, color, x, y, anims, start=0, decimals=0, prefix="", suffix="", sep=","):
    """A number drawn as text, its value tweened: `value` anims, printed with `decimals`, `prefix`, `suffix`, `sep`."""
    return {"id": id_, "kind": "counter", "value": start, "decimals": decimals, "prefix": prefix, "suffix": suffix,
            "sep": sep, "font": f"bold {size}px {FONT}", "color": color, "x": x, "y": y, "anims": anims}


def fade_rise(t, d, ease, y, dy=40):
    return [A("y", y + dy, y, t, d, ease), A("opacity", 0, 1, t, d, ease)]


def mg_basic():
    cards = []
    for i, c in enumerate(["#ff5f5f", "#ffc94d", "#4dd4ff", "#9b7bff"]):
        t = 0.95 + i * 0.12
        an = [A("scale", 0.6, 1, t, 0.45, "back.out(1.7)"), A("opacity", 0, 1, t, 0.25, "power1.out")]
        if i == 0:
            an.append(A("y", 430, 580, 2.10, 0.50, "sine.inOut"))
        cards.append(rect(f"card{i}", 200, 140, c, 640 + (i - 1.5) * 240, 430, an, r=18))
    return {"name": "mg-basic", "W": 1280, "H": 720, "fps": 30, "dur": 7.0, "shots": [
        {"id": "A", "t0": 0.0, "t1": 3.0, "bg": {"kind": "vignette", "c0": "#262d52", "c1": "#12162a"}, "elements": [
            text("title", "MOTION GRAMMAR", 64, "#f2efe6", 640, 170, fade_rise(0.30, 0.60, "power3.out", 170, 60)),
            *cards]},
        {"id": "B", "t0": 3.0, "t1": 5.5, "bg": {"kind": "paper", "c": "#efe6d2"}, "elements": [
            text("big42", "42", 220, "#1b1b1b", 640, 330,
                 [A("scale", 0.05, 1, 3.30, 0.50, "expo.out"), A("opacity", 1, 0, 4.40, 0.30, "power2.in")]),
            rect("bar", 640, 70, "#d6452f", 640, 540,
                 [A("x", -400, 640, 3.60, 0.40, "power2.out"), A("opacity", 1, 0, 4.40, 0.30, "power2.in")],
                 text="THE ANSWER", font=f"bold 40px {FONT}", textColor="#ffffff")]},
        {"id": "C", "t0": 5.0, "t1": 7.0, "bg": {"kind": "flat", "c": "#f7c6d0"}, "elements": [
            circle("ball", 70, "#2b2d6e", 640, 360, [A("y", -120, 360, 5.80, 0.90, "elastic.out(1,0.3)")]),
            text("label", "BOUNCE", 48, "#2b2d6e", 640, 560, fade_rise(6.30, 0.40, "power2.out", 560))]}],
        "transitions": [{"type": "cut", "t": 3.0}, {"type": "dissolve", "t0": 5.0, "t1": 5.5, "ease": "sine.inOut"}]}


def keynote_dark():
    grid = {"kind": "grid", "c": "#0b0d12", "line": "#1a2030", "step": 64}
    panels = [rect(f"panel{i}", 260, 140, c, 1000, 180 + i * 180, [A("x", 1450, 1000, 0.9 + i * 0.08, 0.6, "expo.out")], r=12)
              for i, c in enumerate(["#1f6feb", "#2ea043", "#d29922"])]
    return {"name": "keynote-dark", "W": 1280, "H": 720, "fps": 30, "dur": 6.0, "shots": [
        {"id": "A", "t0": 0.0, "t1": 2.4, "bg": grid, "elements": [
            text("headline", "SHIP FASTER", 72, "#e8ecf4", 420, 250, [A("x", -300, 420, 0.3, 0.7, "power4.out")]),
            text("sub", "Launch notes", 32, "#8b93a7", 420, 320, fade_rise(0.45, 0.5, "power2.out", 320, 30), bold=False),
            *panels]},
        {"id": "B", "t0": 2.4, "t1": 5.0, "bg": grid, "elements": [
            text("big", "98%", 200, "#e8ecf4", 640, 330,
                 [A("scale", 0.5, 1, 2.7, 0.5, "back.out(2.5)"), A("opacity", 0, 1, 2.7, 0.2, "power1.out"),
                  A("x", 640, 1700, 4.4, 0.35, "power2.in")]),
            text("uptime", "uptime", 36, "#8b93a7", 640, 470,
                 [A("opacity", 0, 1, 3.1, 0.6, "sine.inOut"), A("opacity", 1, 0, 4.4, 0.3, "power2.in")], bold=False)]},
        {"id": "C", "t0": 5.0, "t1": 6.0, "bg": {"kind": "flat", "c": "#0b0d12"}, "elements": [
            rect("logo", 120, 120, "#1f6feb", 640, 360,
                 [A("opacity", 0, 1, 5.15, 0.6, "sine.inOut"), A("scale", 0.9, 1, 5.15, 0.6, "sine.inOut")], r=24)]}],
        "transitions": [{"type": "cut", "t": 2.4}, {"type": "cut", "t": 5.0}]}


def vertical_social():
    stickers = [circle(f"sticker{i}", 70, c, 180 + i * 180, 700, [A("scale", 0.2, 1, 0.6 + i * 0.1, 0.45, "back.out(3)")])
                for i, c in enumerate(["#ff3d7f", "#00c2a8", "#5b5bff"])]
    return {"name": "vertical-social", "W": 720, "H": 1280, "fps": 30, "dur": 6.0, "shots": [
        {"id": "A", "t0": 0.0, "t1": 2.0, "bg": {"kind": "flat", "c": "#ffe14d"}, "elements": [
            text("headline", "WAIT FOR IT", 84, "#111111", 360, 300, fade_rise(0.2, 0.5, "power3.out", 300)),
            *stickers,
            rect("tilted", 420, 180, "#111111", 360, 1000,
                 [A("rot", -12, 0, 1.1, 0.5, "power3.out"), A("scale", 0.7, 1, 1.1, 0.5, "power3.out")], r=16)]},
        {"id": "B", "t0": 2.0, "t1": 4.0, "bg": {"kind": "flat", "c": "#111111"}, "elements": [
            text("trick", "THE TRICK", 90, "#ffe14d", 360, 500,
                 [A("scale", 1.6, 1, 2.2, 0.45, "expo.out"), A("opacity", 0, 1, 2.2, 0.15, "power1.out")]),
            rect("rule", 500, 16, "#ffe14d", 360, 580, [A("x", -300, 360, 2.5, 0.5, "power3.out")])]},
        {"id": "C", "t0": 4.0, "t1": 6.0, "bg": {"kind": "flat", "c": "#ff3d7f"}, "elements": [
            circle("ball", 90, "#111111", 360, 640, [A("y", -150, 640, 4.2, 1.0, "bounce.out")])]}],
        "transitions": [{"type": "cut", "t": 2.0}, {"type": "cut", "t": 4.0}]}


def camera_push():
    labels = [text(f"label{i}", s, 40, "#2a2a2a", 300 + i * 340, 200, [A("opacity", 0, 1, 0.8 + i * 0.25, 0.5, "power2.out")])
              for i, s in enumerate(["north", "centre", "south"])]
    return {"name": "camera-push", "W": 1280, "H": 720, "fps": 30, "dur": 6.0, "shots": [
        {"id": "A", "t0": 0.0, "t1": 6.0, "bg": {"kind": "gridpaper", "c": "#efe9dc", "line": "#c9bfa9", "step": 48},
         "camera": [A("zoom", 1, 1.18, 0.5, 5.0, "sine.inOut"), A("panx", 0, -110, 1.0, 4.0, "power1.inOut")],
         "elements": [*labels,
                      rect("card", 220, 140, "#e4572e", 300, 480, [A("x", 300, 980, 2.5, 1.2, "power2.inOut")], r=10)]}],
        "transitions": []}


def on_twos():
    return {"name": "on-twos", "W": 1280, "H": 720, "fps": 24, "dur": 5.0, "shots": [
        {"id": "A", "t0": 0.0, "t1": 2.6, "step": 12, "bg": {"kind": "flat", "c": "#fdf6e3"}, "elements": [
            circle("ball", 60, "#d33682", 200, 360, [A("x", 200, 1080, 0.3, 1.5, "power1.inOut")]),
            rect("box", 160, 160, "#268bd2", 640, 180, [A("scale", 0.3, 1, 0.5, 0.6, "back.out(1.7)")], r=20),
            text("caption", "ON TWOS", 64, "#073642", 640, 560, fade_rise(1.0, 0.6, "power2.out", 560))]},
        {"id": "B", "t0": 2.6, "t1": 5.0, "step": 12, "bg": {"kind": "flat", "c": "#073642"}, "elements": [
            circle("sun", 80, "#b58900", 640, 360,
                   [A("scale", 0.2, 1, 2.9, 0.7, "power3.out"), A("y", 360, 300, 3.8, 0.8, "sine.inOut")])]}],
        "transitions": [{"type": "cut", "t": 2.6}]}


def dips_and_drifts():
    return {"name": "dips-and-drifts", "W": 1280, "H": 720, "fps": 25, "dur": 7.0, "shots": [
        {"id": "A", "t0": 0.0, "t1": 2.3, "bg": {"kind": "vignette", "c0": "#22324a", "c1": "#0e1520"}, "elements": [
            text("ch1", "CHAPTER ONE", 64, "#ffffff", 640, 330, [A("opacity", 0, 1, 0.3, 1.0, "sine.inOut")]),
            rect("drift", 300, 8, "#ffffff", 340, 420, [A("x", 340, 940, 0.2, 2.0, "none")])]},
        {"id": "B", "t0": 2.3, "t1": 5.6, "bg": {"kind": "flat", "c": "#f4efe6"}, "elements": [
            text("ch2", "CHAPTER TWO", 64, "#222222", 640, 330, [A("opacity", 0, 1, 2.8, 0.9, "sine.inOut")]),
            text("slow", "a slow fade", 32, "#666666", 640, 400, [A("opacity", 0, 1, 3.3, 1.0, "power1.inOut")], bold=False)]},
        {"id": "C", "t0": 4.6, "t1": 7.0, "bg": {"kind": "flat", "c": "#2d4a3e"}, "elements": [
            circle("moon", 100, "#f4efe6", 640, 360,
                   [A("scale", 0.8, 1, 5.9, 0.8, "sine.out"), A("opacity", 0, 1, 5.9, 0.8, "sine.out")])]}],
        "transitions": [{"type": "dip", "t0": 2.0, "t1": 2.6, "color": "#000000", "ease": "sine.inOut"},
                        {"type": "dissolve", "t0": 4.6, "t1": 5.6, "ease": "power1.inOut"}]}


def dataviz_bars():
    hs = [200, 320, 260, 420, 150]
    bars = [{"id": f"bar{i}", "kind": "bar", "w": 120, "h": h, "color": "#3b82f6", "x": 260 + i * 190, "y": 600,
             "anims": [A("sy", 0, 1, 0.9 + i * 0.1, 0.6, "power3.out")]} for i, h in enumerate(hs)]
    vals = [text(f"value{i}", str(h // 4), 28, "#222222", 260 + i * 190, 600 - h - 30,
                 fade_rise(1.4 + i * 0.1, 0.3, "power2.out", 600 - h - 30, 15)) for i, h in enumerate(hs)]
    return {"name": "dataviz-bars", "W": 1280, "H": 720, "fps": 30, "dur": 5.0, "shots": [
        {"id": "A", "t0": 0.0, "t1": 5.0, "bg": {"kind": "flat", "c": "#fbfaf7"}, "elements": [
            text("title", "Revenue by region", 40, "#222222", 640, 90, fade_rise(0.2, 0.5, "power2.out", 90, 20)),
            {"id": "axis", "kind": "path", "points": [[160, 600], [1120, 600]], "color": "#222222", "width": 3,
             "x": 0, "y": 0, "anims": [A("draw", 0, 1, 0.4, 0.6, "power2.inOut")]},
            *bars, *vals]}],
        "transitions": []}


def letters():
    return {"name": "letters", "W": 1280, "H": 720, "fps": 30, "dur": 4.0, "shots": [
        {"id": "A", "t0": 0.0, "t1": 4.0, "bg": {"kind": "flat", "c": "#101418"}, "elements": [
            {"id": "kinetic", "kind": "chars", "text": "KINETIC TYPE", "font": f"bold 96px {FONT}", "color": "#f5f5f5",
             "x": 640, "y": 320, "stagger": 0.04,
             "anims": [*fade_rise(0.3, 0.5, "power3.out", 320, 60), A("opacity", 1, 0, 3.2, 0.4, "power2.in")]},
            text("words", "word by word", 36, "#9aa4b2", 640, 420, [A("opacity", 0, 1, 1.2, 0.5, "power2.out")], bold=False),
            rect("underline", 400, 6, "#f5f5f5", 640, 470, [A("sx", 0, 1, 1.5, 0.6, "power3.inOut")])]}],
        "transitions": []}


def counters():
    return {"name": "counters", "W": 1280, "H": 720, "fps": 30, "dur": 5.0, "shots": [
        {"id": "A", "t0": 0.0, "t1": 5.0, "bg": {"kind": "flat", "c": "#f6f4ef"}, "elements": [
            text("label", "ACTIVE USERS", 30, "#6b6b6b", 640, 150, [A("opacity", 0, 1, 0.2, 0.4, "power1.out")]),
            counter("users", 120, "#1b1b1b", 640, 270,
                    [A("opacity", 0, 1, 0.4, 0.3, "power1.out"), A("value", 0, 4200, 0.6, 1.6, "power3.out")]),
            counter("share", 96, "#d6452f", 400, 520, [A("value", 0, 98, 1.4, 1.2, "expo.out")], suffix="%"),
            counter("revenue", 96, "#2f6fd6", 880, 520, [A("value", 0, 12.5, 2.6, 1.4, "sine.inOut")], decimals=1,
                    prefix="$", suffix="M")]}],
        "transitions": []}


def busy():
    chips = [rect(f"chip{i}", 200, 60, c, 250 + i * 260, 620, [A("y", 790, 620, 0.3 + i * 0.07, 0.5, "circ.out")], r=30)
             for i, c in enumerate(["#ff6b6b", "#feca57", "#48dbfb", "#1dd1a1"])]
    chips[3]["anims"].append(A("x", 1030, 1500, 2.4, 0.5, "expo.in"))
    dots = [circle(f"dot{i}", 16, "#feca57", 560 + i * 80, 470, [A("opacity", 0, 1, 4.4 + i * 0.12, 0.25, "power1.out")])
            for i in range(3)]
    return {"name": "busy", "W": 1280, "H": 720, "fps": 30, "dur": 6.0, "shots": [
        {"id": "A", "t0": 0.0, "t1": 3.5, "bg": {"kind": "flat", "c": "#eef1f5"}, "elements": [
            *chips,
            rect("cardL", 260, 180, "#341f97", 300, 330,
                 [A("x", 300, 900, 1.3, 0.8, "power2.inOut"), A("scale", 1, 0.2, 2.8, 0.4, "power2.in"),
                  A("opacity", 1, 0, 2.8, 0.4, "power2.in")], r=14),
            rect("cardR", 260, 120, "#ee5253", 980, 130, [A("x", 980, 380, 1.3, 0.8, "power2.inOut")], r=14)]},
        {"id": "B", "t0": 3.5, "t1": 6.0, "bg": {"kind": "flat", "c": "#222f3e"}, "elements": [
            text("done", "DONE", 120, "#ffffff", 640, 360,
                 [A("scale", 0.6, 1, 3.8, 0.5, "back.out(1.4)"), A("opacity", 0, 1, 3.8, 0.25, "power1.out")]),
            *dots]}],
        "transitions": [{"type": "cut", "t": 3.5}]}


def print_rhythm():
    shots = []
    for i in range(5):
        color = ["#ff48b0", "#0078bf"][i % 2]
        an = fade_rise(i + 0.15, 0.3, "power1.out", 360, 60)
        if i % 2:
            an = [A("scale", 0.85, 1, i + 0.15, 0.35, "power2.out"), A("opacity", 0, 1, i + 0.15, 0.35, "power2.out")]
        el = (circle(f"shape{i}", 150, color, 640, 360, an) if i % 2 == 0
              else rect(f"shape{i}", 360, 260, color, 640, 360, an))
        el["misreg"] = {"color": "#ffe800", "dx": 5, "dy": 4}
        shots.append({"id": f"S{i}", "t0": float(i), "t1": float(i + 1), "grain": 18,
                      "bg": {"kind": "paper", "c": ["#f2e8d5", "#e9dfc9"][i % 2]}, "elements": [el]})
    return {"name": "print-rhythm", "W": 1280, "H": 720, "fps": 24, "dur": 5.0, "shots": shots,
            "transitions": [{"type": "cut", "t": float(i)} for i in range(1, 5)]}


FIXTURES = [mg_basic, keynote_dark, vertical_social, camera_push, on_twos, dips_and_drifts, dataviz_bars, letters,
            busy, print_rhythm, counters]

PAGE = (Path(__file__).with_name("fixture_page.html")).read_text(encoding="utf-8")


def _value(el, prop, t, i=0):
    base = 1.0 if prop in ("scale", "opacity", "sx", "sy", "draw", "zoom") else 0.0 if prop in ("rot", "panx", "pany") \
        else float(el[prop])
    v, anims = base, sorted((a for a in el["anims"] if a["prop"] == prop), key=lambda a: a["t"])
    for k, a in enumerate(anims):
        start = a["t"] + i * el.get("stagger", 0)
        if t >= start:
            v = a["from"] + (a["to"] - a["from"]) * float(eases.get(a["ease"])(np.array(min(1.0, (t - start) / a["d"]))))
        elif k == 0:
            v = a["from"]
    return v


def _camera(shot, t):
    cam = {"anims": shot.get("camera", [])}
    return _value(cam, "zoom", t), _value(cam, "panx", t), _value(cam, "pany", t)


def _to_screen(spec, shot, x, y, t):
    z, px, py = _camera(shot, t)
    W, H = spec["W"], spec["H"]
    return W / 2 + px + (x - W / 2) * z, H / 2 + py + (y - H / 2) * z


def truth(spec) -> dict:
    events = []
    for shot in spec["shots"]:
        for el in shot["elements"]:
            for a in el["anims"]:
                end = a["t"] + a["d"]
                if el["kind"] == "path":                # a path is placed by its points: its middle
                    pts = el["points"]
                    x, y = sum(q[0] for q in pts) / len(pts), sum(q[1] for q in pts) / len(pts)
                else:
                    x, y = _value(el, "x", end), _value(el, "y", end)
                ex, ey = _to_screen(spec, shot, x, y, end)
                v1 = a["prop"] in V1_PROPS or el["kind"] in ("chars", "path", "bar", "counter")
                events.append({"element": el["id"], "shot": shot["id"], "prop": a["prop"], "t0": a["t"],
                               "t1": round(end, 4), "dur": a["d"], "ease": a["ease"], "from": a["from"], "to": a["to"],
                               "end_xy": [round(ex, 1), round(ey, 1)], "scope": "v1" if v1 else "mvp",
                               **({"stagger": el["stagger"], "count": len(el["text"].replace(" ", ""))}
                                  if el.get("stagger") else {})})
        for a in shot.get("camera", []):
            events.append({"element": "camera", "shot": shot["id"], "prop": a["prop"], "t0": a["t"],
                           "t1": round(a["t"] + a["d"], 4), "dur": a["d"], "ease": a["ease"], "from": a["from"],
                           "to": a["to"], "end_xy": [spec["W"] / 2, spec["H"] / 2], "scope": "mvp"})
    stepping = [{"shot": s["id"], "t0": s["t0"], "t1": s["t1"], "on": round(spec["fps"] / s["step"])}
                for s in spec["shots"] if s.get("step")]
    return {"name": spec["name"], "W": spec["W"], "H": spec["H"], "fps": spec["fps"], "dur": spec["dur"],
            "events": events, "transitions": spec["transitions"], "stepping": stepping}


def write(root: Path, names=None) -> list[Path]:
    out = []
    for make in FIXTURES:
        spec = make()
        if names and spec["name"] not in names:
            continue
        d = root / spec["name"]
        d.mkdir(parents=True, exist_ok=True)
        (d / "index.html").write_text(PAGE.replace("__SPEC__", json.dumps(spec)), encoding="utf-8")
        (d / "truth.json").write_text(json.dumps(truth(spec), indent=1), encoding="utf-8")
        out.append(d)
    return out
