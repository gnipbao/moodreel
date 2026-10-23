"""Distil the example films back and set what comes out against what they were made with (`moodreel bench roundtrip`).

Each film in examples/ with a truth.json is rendered (its video at 1280x720, a few stills at its design size), taken
in as references, measured and written into a kit, exactly as a user's references would be. Every value the pack
would carry is then compared with the value in the film's code: the palette roles, the surface, the title, the cuts
and the drawing rate, the kit's eases, and the motion element by element, scored as the motion bench scores its
test films and grouped by the reader each move needs. What fails is what the readers still miss.
"""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import numpy as np

from ..intake import intake
from ..measure.color import delta_e, rgb_to_lab
from ..measure.run import measure
from ..motion import eases
from ..pack.kit import motion_tokens, style_tokens, write_kit
from .motion import score

REPO = Path(__file__).resolve().parents[2]
RENDER = REPO / "render" / "render.mjs"
VIDEO_SIZE = "1280x720"
TOL = {"colour": 6.0, "grain": 0.5, "vignette": 0.04, "period": 0.10, "angle": 3.0, "title": 0.25, "weight": 100}


def films(root: Path, only: set[str] | None = None) -> list[Path]:
    return [d for d in sorted(Path(root).iterdir()) if (d / "truth.json").exists() and (not only or d.name in only)]


def build(film: Path, work: Path, workers: int = 3) -> Path:
    """Render the film, take it in, measure it and write its kit; returns the project folder."""
    truth = json.loads((film / "truth.json").read_text())
    if work.exists():
        shutil.rmtree(work)
    refs = work / "refs"
    run = lambda *a: subprocess.run(["node", str(RENDER), *map(str, a)], check=True, capture_output=True)  # noqa: E731
    run("video", film, "--fps", truth["fps"], "--size", VIDEO_SIZE, "--workers", workers, "--out", refs / f"{truth['name']}.mp4")
    run("still", film, *truth["stills"], "--size", f"{truth['W']}x{truth['H']}", "--out", refs)
    project = work / "project"
    intake(project, sorted(refs.iterdir()), source="own")
    measure(project)
    write_kit(project)
    return project


def _lab(h: str):
    return rgb_to_lab(np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], np.float64))


def _verdict(ok):
    return "unknown" if ok is None else "pass" if ok else "fail"


def static(truth: dict, project: Path) -> list[dict]:
    """The values a pack carries, from the kit's tokens (what a new film would be drawn with)."""
    tok = style_tokens(project, json.loads((project / "intake.json").read_text()))
    grammar = json.loads((project / "measure" / "motion.json").read_text())["grammar"]
    mot = motion_tokens(grammar)
    rows = []

    def add(group, what, want, got, ok):
        rows.append({"group": group, "what": what, "film": want, "distilled": got, "result": _verdict(ok)})

    for role in ("ground", "ink", "accent"):
        want, got = truth["palette"][role], tok["palette"].get(role)
        d = float(delta_e(_lab(want), _lab(got))) if got else None
        add("palette", role, want, got and f"{got} (ΔE {d:.1f})", d is not None and d <= TOL["colour"])
    tex, sv = tok["texture"], truth["surface"]
    g = tex.get("grain")
    add("surface", "grain (levels)", sv["grain"], g,
        g is not None and (g < 2.5 if sv["grain"] < 2.5 else abs(g - sv["grain"]) <= TOL["grain"] * sv["grain"]))
    v = tex.get("vignette")
    add("surface", "vignette", sv["vignette"], v, v is not None and abs(v - sv["vignette"]) <= TOL["vignette"])
    ht, want = tex.get("halftone"), sv["halftone"]
    if want is None:
        add("surface", "halftone", "none", ht and f"period {ht['period_px']} px", ht is None)
    else:
        add("surface", "halftone period (design px)", want["period_px"], ht and ht["period_px"],
            ht is not None and abs(ht["period_px"] - want["period_px"]) <= TOL["period"] * want["period_px"])
        da = ht and abs((ht["angle"] - want["angle"] + 45) % 90 - 45)
        add("surface", "halftone angle (°)", want["angle"], ht and ht["angle"], ht is not None and da <= TOL["angle"])
    ty, tt = tok["type"], truth["type"]
    add("type", "title size (of the height)", tt["title"], ty["title"],
        bool(ty["title"]) and abs(ty["title"] / tt["title"] - 1) <= TOL["title"])
    add("type", "title weight", tt["weight"], ty["titleWeight"], any(abs(ty["titleWeight"] - w) <= TOL["weight"] for w in tt["weight"]))
    sh = grammar["shots"]
    add("motion", "cuts and transitions", len(truth["transitions"]), sh["cuts"] + sh["dissolves"] + sh.get("dips", 0),
        sh["cuts"] + sh["dissolves"] + sh.get("dips", 0) == len(truth["transitions"]))
    on = (grammar.get("stepping") or {}).get("on", 1)
    add("motion", "drawings held on", truth["stepping"][0]["on"], on, on == truth["stepping"][0]["on"])
    # an unread curve leaves the choice to the director (unknown); a wrong one would mislead every film (fail)
    for role, key in (("entrance", "enter"), ("exit", "exit"), ("move", "move")):
        want, m = truth["motion"].get(role), mot.get(key)
        got = None if not m else m["class"] if m.get("ease") else "unread"
        add("kit eases", f"{role} class", want, got, None if want is None or got in (None, "unread") else got == want)
    return rows


def motion(truth: dict, project: Path) -> dict:
    vid = json.loads((project / "intake.json").read_text())["refs"]
    vid = next(r["id"] for r in vid if r["kind"] == "video")
    measured = json.loads((project / "evidence" / f"motion-{vid}" / "motion.json").read_text())
    s = score(truth, measured)
    rows = []
    for te, r in zip(truth["events"], s["props"]):
        claimed = r.get("claimed", False)
        rows.append({**r, "reader": te["reader"], "truth_class": eases.shape_class(te["ease"]),
                     "verdict": ("missed" if not r["found"] else ("claimed right" if r["class_ok"] else "claimed wrong")
                                 if claimed else ("guess right" if r["class_ok"] else "guess wrong"))})
    readers = {}
    for r in rows:
        k = readers.setdefault(r["reader"], {"events": 0, "found": 0, "claimed right": 0, "claimed wrong": 0,
                                             "guess right": 0, "guess wrong": 0, "scope": r["scope"]})
        k["events"] += 1
        k["found"] += r["found"]
        if r["found"]:
            k[r["verdict"]] += 1
    return {"rows": rows, "readers": readers, "spurious": s["spurious"]}


def report(film_dirs: list[Path], work: Path, workers: int = 3) -> str:
    out, summary = [], []
    for film in film_dirs:
        truth = json.loads((film / "truth.json").read_text())
        project = build(film, work / film.name, workers)
        st, mo = static(truth, project), motion(truth, project)
        passed = sum(r["result"] == "pass" for r in st)
        failed = [r["what"] for r in st if r["result"] == "fail"]
        found = sum(r["found"] for r in mo["rows"])
        wrong = sum(r["verdict"] == "claimed wrong" for r in mo["rows"])
        summary.append(f"| {film.name} | {passed}/{len(st)} | {', '.join(failed) or '—'} | {found}/{len(mo['rows'])} | "
                       f"{sum(r['verdict'] == 'claimed right' for r in mo['rows'])} | {wrong} |")
        out += [f"## {film.name}", "", "| group | value | film | distilled | result |", "|---|---|---|---|---|"]
        out += [f"| {r['group']} | {r['what']} | {r['film']} | {r['distilled'] if r['distilled'] is not None else '—'} | "
                f"{'✓' if r['result'] == 'pass' else '✗' if r['result'] == 'fail' else '?'} |" for r in st]
        out += ["", "Motion by the reader each move needs:", "",
                "| reader | scope | events | found | claimed right | claimed wrong | guessed right | guessed wrong |",
                "|---|---|---|---|---|---|---|---|"]
        out += [f"| {k} | {v['scope']} | {v['events']} | {v['found']} | {v['claimed right']} | {v['claimed wrong']} | "
                f"{v['guess right']} | {v['guess wrong']} |" for k, v in mo["readers"].items()]
        out += ["", "| element | prop | reader | film | measured | verdict | t50 err (f) |", "|---|---|---|---|---|---|---|"]
        out += [f"| {r['element']} | {r['prop']} | {r['reader']} | {r['truth']} ({r['truth_class']}) | {r.get('measured', '—')} | "
                f"{r['verdict']} | {r.get('t50_err_f', '—')} |" for r in mo["rows"]]
        out += ["", f"Measured but not in the film: {', '.join(mo['spurious']) or 'nothing'}."]
        out += [f"Left out of the truth: {'; '.join(truth.get('omitted', []))}." if truth.get("omitted") else "", ""]
    head = ["# Round trip", "",
            "Each example film rendered, taken in as references, measured and written into a kit, then compared with the "
            "values in its own code. Generated by `moodreel bench roundtrip`; the work folders are under `out/roundtrip/`.",
            "", "? is unknown: the kit left the curve unread for the director, which is safe; ✗ would mislead a new film.", "",
            "| film | static values | failed | moves found | eases claimed right | eases claimed wrong |",
            "|---|---|---|---|---|---|", *summary, ""]
    return "\n".join(head + out)
