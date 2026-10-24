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
from ..check.motion import check as motion_check
from ..pack.kit import motion_tokens, style_tokens, write_kit
from ..pack.sketch import write_sketch
from .motion import _transitions, score

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
    # Chrome's engine: every render the same, bit for bit, so the report is too
    run("video", film, "--fps", truth["fps"], "--size", VIDEO_SIZE, "--workers", workers, "--engine", "chrome",
        "--out", refs / f"{truth['name']}.mp4")
    run("still", film, *truth["stills"], "--size", f"{truth['W']}x{truth['H']}", "--out", refs)
    project = work / "project"
    intake(project, sorted(refs.iterdir()), source="own")
    measure(project)
    write_kit(project)
    sketch = write_sketch(project, truth["fps"])
    run("video", sketch, "--fps", truth["fps"], "--size", VIDEO_SIZE, "--workers", workers, "--engine", "chrome",
        "--out", work / "sketch.mp4")
    return project


def sketch_claims(project: Path) -> dict:
    """The kit's motion replayed (moodreel sketch), measured and checked claim by claim against the references.
    Where the kit left a curve unread, the sketch eases with a placeholder: its class and overshoot claim nothing;
    nor does its density, which is how much its three shapes move, not how the style moves."""
    res = motion_check(project, project.parent / "sketch.mp4", out=project.parent / "sketch-check")
    mt = motion_tokens(json.loads((project / "measure" / "motion.json").read_text())["grammar"])
    unread = {role for role, key in (("entrance", "enter"), ("exit", "exit"), ("move", "move")) if not (mt.get(key) or {}).get("ease")}
    for c in res["claims"]:
        part = c["id"].split(".")
        if part[0] in unread and len(part) > 1 and part[1].startswith(("ease_class", "overshoot")):
            c["result"] = "unknown"
        if c["id"] == "density":            # how much a film has moving is its own content, not the kit's
            c["result"] = "unknown"
    for k in ("pass", "fail", "unknown"):
        res[k] = sum(c["result"] == k for c in res["claims"])
    return res


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

    pal = tok["palette"]
    for role in ("ground", "ink"):
        # a role may accept several tones (a phosphor's ramp, a pattern's tones): the nearest counts
        want, got = truth["palette"][role], pal.get(role)
        wants = want if isinstance(want, list) else [want]
        d = min(float(delta_e(_lab(w), _lab(got))) for w in wants) if got else None
        add("palette", role, want, got and f"{got} (ΔE {d:.1f})", d is not None and d <= TOL["colour"])
    want, got = truth["palette"]["accent"], pal.get("accent")
    if want:
        d = float(delta_e(_lab(want), _lab(got))) if got else None
        add("palette", "accent", want, got and f"{got} (ΔE {d:.1f})", d is not None and d <= TOL["colour"])
    else:
        # no accent of its own: whatever the role holds must be a tone of the ground's or the ink's hue
        hue = lambda h: float(np.degrees(np.arctan2(_lab(h)[2], _lab(h)[1])) % 360)  # noqa: E731
        near = got is None or any(abs((hue(got) - hue(pal[r]) + 180) % 360 - 180) <= 20 for r in ("ground", "ink") if pal.get(r))
        add("palette", "accent", "none (tones of the hue)", got, near)
    tex, sv = tok["texture"], truth["surface"]
    g = tex.get("grain")
    add("surface", "grain (levels)", sv["grain"], g,
        g is not None and (g < 2.5 if sv["grain"] < 2.5 else abs(g - sv["grain"]) <= TOL["grain"] * sv["grain"]))
    v, want = tex.get("vignette"), sv["vignette"]
    lo, hi = want if isinstance(want, list) else (want - TOL["vignette"], want + TOL["vignette"])   # or a range
    add("surface", "vignette", want, v, v is not None and lo <= v <= hi)
    ht, want = tex.get("halftone"), sv["halftone"]
    if want is None:
        add("surface", "halftone", "none", ht and f"period {ht['period_px']} px", ht is None)
    else:
        add("surface", "halftone period (design px)", want["period_px"], ht and ht["period_px"],
            ht is not None and abs(ht["period_px"] - want["period_px"]) <= TOL["period"] * want["period_px"])
        da = ht and abs((ht["angle"] - want["angle"] + 45) % 90 - 45)
        add("surface", "halftone angle (°)", want["angle"], ht and ht["angle"], ht is not None and da <= TOL["angle"])
    if "scanlines" in sv:
        sl, want = tex.get("scanlines"), sv["scanlines"]
        if want is None:
            add("surface", "scanlines", "none", sl and f"period {sl['period_px']} px", sl is None)
        else:
            add("surface", "scanline period (design px)", want["period_px"], sl and sl["period_px"],
                sl is not None and abs(sl["period_px"] - want["period_px"]) <= TOL["period"] * want["period_px"])
    ty, tt = tok["type"], truth["type"]
    add("type", "title size (of the height)", tt["title"], ty["title"],
        bool(ty["title"]) and abs(ty["title"] / tt["title"] - 1) <= TOL["title"])
    add("type", "title weight", tt["weight"], ty["titleWeight"], any(abs(ty["titleWeight"] - w) <= TOL["weight"] for w in tt["weight"]))
    # each of the film's cuts, dissolves and dips found at its time, and nothing else
    vid = next(r["id"] for r in json.loads((project / "intake.json").read_text())["refs"] if r["kind"] == "video")
    measured = json.loads((project / "evidence" / f"motion-{vid}" / "motion.json").read_text())
    found, extra = _transitions(truth, measured)
    show = lambda ts: ", ".join(f"{t['type']} {t.get('t', t.get('t0', 0)):.2f}s" for t in ts) or "none"  # noqa: E731
    add("motion", "cuts and transitions", show(truth["transitions"]), show([r["measured"] for r in found if r["measured"]] + extra),
        all(r["measured"] for r in found) and not extra)
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


SECTIONS = {"2. Materials": "surface", "3. Colour": "palette", "4. Type": "type", "5. Motion": None, "6. Camera": None}


def sections(st: list[dict], mo: dict, mc: dict) -> dict:
    """The STYLE.md sections the measurements speak for, judged from the comparisons: a section holds when none of
    its values fails. §5 also needs four in five of the sketch's decided motion claims to pass; §6 needs the cuts and
    the drawing rate, and any camera move the film makes to be found. §1 and §7-§11 are the director's judgement."""
    out = {}
    for name, group in SECTIONS.items():
        if group:
            out[name] = all(r["result"] != "fail" for r in st if r["group"] == group)
    decided = mc["pass"] + mc["fail"]
    out["5. Motion"] = (all(r["result"] != "fail" for r in st if r["group"] == "kit eases")
                        and decided > 0 and mc["pass"] >= 0.8 * decided)
    cams = [r for r in mo["rows"] if r["element"] == "camera"]
    out["6. Camera"] = (all(r["result"] != "fail" for r in st if r["group"] == "motion")
                        and all(r["found"] for r in cams))
    return out


def report(film_dirs: list[Path], work: Path, workers: int = 3) -> str:
    out, summary = [], []
    for film in film_dirs:
        truth = json.loads((film / "truth.json").read_text())
        project = build(film, work / film.name, workers)
        st, mo, mc = static(truth, project), motion(truth, project), sketch_claims(project)
        passed = sum(r["result"] == "pass" for r in st)
        failed = [r["what"] for r in st if r["result"] == "fail"]
        found = sum(r["found"] for r in mo["rows"])
        wrong = sum(r["verdict"] == "claimed wrong" for r in mo["rows"])
        decided = mc["pass"] + mc["fail"]
        sec = sections(st, mo, mc)
        summary.append(f"| {film.name} | {passed}/{len(st)} | {', '.join(failed) or '—'} | {found}/{len(mo['rows'])} | "
                       f"{sum(r['verdict'] == 'claimed right' for r in mo['rows'])} | {wrong} | "
                       f"{mc['pass']}/{decided} ({mc['unknown']} unknown) | {sum(sec.values())}/{len(sec)} |")
        out += [f"## {film.name}", "",
                "Sections the measurements speak for: " + ", ".join(f"§{k} {'✓' if v else '✗'}" for k, v in sec.items()) + ".",
                "", "| group | value | film | distilled | result |", "|---|---|---|---|---|"]
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
        out += ["", "The kit's motion replayed (`moodreel sketch`) and checked against the references (`motion-check`):", "",
                "| claim | rule | references | sketch | result |", "|---|---|---|---|---|"]
        out += [f"| {c['id']} | {c['rule']} | {c['reference']} | {c['film']} | "
                f"{'✓' if c['result'] == 'pass' else '✗' if c['result'] == 'fail' else '?'} |" for c in mc["claims"]]
        out += ["", f"Measured but not in the film: {', '.join(mo['spurious']) or 'nothing'}."]
        out += [f"Left out of the truth: {'; '.join(truth.get('omitted', []))}." if truth.get("omitted") else "", ""]
    head = ["# Round trip", "",
            "Each example film rendered, taken in as references, measured and written into a kit, then compared with the "
            "values in its own code. Generated by `moodreel bench roundtrip`; the work folders are under `out/roundtrip/`.",
            "", "? is unknown: the kit left the curve unread for the director, which is safe; ✗ would mislead a new film.", "",
            "| film | static values | failed | moves found | eases claimed right | eases claimed wrong "
            "| sketch motion claims passed | sections held |",
            "|---|---|---|---|---|---|---|---|", *summary, "",
            "Sections held: of the five STYLE.md sections the measurements speak for (§2 materials, §3 colour, §4 type, "
            "§5 motion, §6 camera and editing). §1 and §7-§11 (essence, sound, native moves, pitfalls, engine, "
            "variation) are the director's judgement and need a blind distillation of real references.", ""]
    return "\n".join(head + out)
