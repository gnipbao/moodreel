"""Score measured motion against a test film's truth (`moodreel bench motion`).

Element tweens and camera moves are matched to the measured ones by place and time; transitions by type and
time; drawings held on twos by shot; staggers by interval. Acceptance is judged on the "mvp" scope only: the
kinds of motion the measurement covers today. "v1" truth (rotation, anisotropic scale, draw-on, per-letter text)
is reported so the gap stays visible.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from ..motion import eases

TARGETS = {"recall": 0.90, "t50_within_1f": 0.85, "class_ok": 0.80, "claimed_wrong_rate": 0.05}


def checkpoints(ease, t0, t1):
    u = np.linspace(0, 1, 4001)
    y = eases.get(ease)(u)
    return {q: t0 + (t1 - t0) * float(u[np.argmax(y >= q / 100)]) for q in (10, 50, 90)}


def peak_overshoot(ease):
    u = np.linspace(0, 1, 4001)
    return float(max(0.0, eases.get(ease)(u).max() - 1))


def _scaled(truth, motion):
    """Measured px -> truth px (a stress copy is smaller)."""
    k = truth["W"] / motion["source"]["w"]
    events = []
    for ev in motion["events"]:
        ev = {**ev, "box": [v * k for v in ev["box"]], "props": {n: dict(p) for n, p in ev["props"].items()}}
        for name, p in ev["props"].items():
            if name in ("x", "y"):
                p["from"], p["to"] = round(p["from"] * k, 1), round(p["to"] * k, 1)
        events.append(ev)
    cams = []
    for c in motion.get("camera", []):
        c = dict(c)
        if c["prop"] in ("panx", "pany"):
            c["from"], c["to"] = round(c["from"] * k, 1), round(c["to"] * k, 1)
        cams.append(c)
    return events, cams


def match(truth, motion):
    W = truth["W"]
    events, cams = _scaled(truth, motion)
    rows, used = [], {}
    for te in truth["events"]:
        best = None
        if te["element"] == "camera":
            for i, c in enumerate(cams):
                dt = abs(c["t0"] - te["t0"])
                if c["prop"] == te["prop"] and ("cam", i) not in used and dt < 0.5 and (best is None or dt < best[0]):
                    best = (dt, {"id": ("cam", i)}, c)
            if best:
                used[best[1]["id"]] = 1
            rows.append((te, best))
            continue
        # a solid shape swept on and one stretched from the same edge look alike: either reading finds it
        alias = {"wipe": ("sx", "sy"), "sx": ("wipe",), "sy": ("wipe",)}.get(te["prop"], ())
        for ev in events:
            p = ev["props"].get(te["prop"]) or next((ev["props"][a] for a in alias if a in ev["props"]), None)
            # a merged group (parts that moved as one tween) stands for each of its members
            if p is None or used.get((ev["id"], te["prop"]), 0) >= len(ev.get("members", [ev["id"]])):
                continue
            bx, by = ev["box"][0] + ev["box"][2] / 2, ev["box"][1] + ev["box"][3] / 2
            # the box is where the element rests: for an exit, where it was; for x/y moves, compare the axis that
            # did not move, plus time
            ex, ey = te["end_xy"]
            dist = abs(by - ey) if te["prop"] == "x" else abs(bx - ex) if te["prop"] == "y" else np.hypot(bx - ex, by - ey)
            if te["prop"] in ("sx", "sy", "wipe"):          # a truth may place a stretch at its anchor, not its centre
                x0, y0, w_, h_ = ev["box"]
                dist = min(np.hypot(px - ex, py - ey) for px, py in ((bx, by), (bx, y0), (bx, y0 + h_), (x0, by), (x0 + w_, by)))
            if ev.get("members") and (ev["box"][0] <= ex <= ev["box"][0] + ev["box"][2]
                                      and ev["box"][1] <= ey <= ev["box"][1] + ev["box"][3]):
                dist = 0                                # the group box spans its members
            # t50 is steadier than t0, which hides in a slow or transparent start; a tween cut off by the shot's
            # end has no t50 of its own, so its start is used
            dt = min(abs(p["checkpoints"]["t50"] - checkpoints(te["ease"], te["t0"], te["t1"])[50]),
                     abs(p["t0"] - te["t0"]) if p.get("cut_off") else 9)
            if dist < 0.1 * W and dt < 0.25 and (best is None or dt < best[0]):
                best = (dt, ev, p)
        if best:
            key = (best[1]["id"], te["prop"])
            used[key] = used.get(key, 0) + 1
        rows.append((te, best))
    spurious = [f"{ev['id']}.{k}" for ev in events for k in ev["props"] if (ev["id"], k) not in used]
    spurious += [f"camera.{c['prop']}" for i, c in enumerate(cams) if ("cam", i) not in used]
    return rows, spurious


def _transitions(truth, motion):
    fps = truth["fps"]
    got = [dict(t) for t in motion["transitions"]]
    rows = []
    for tt in truth["transitions"]:
        hit = None
        for g in got:
            if g.get("_used") or g["type"] != tt["type"]:
                continue
            if tt["type"] == "cut":
                ok = abs(g["t"] - tt["t"]) <= 1.5 / fps
            else:
                ok = abs(g["t0"] - tt["t0"]) <= 3 / fps and abs(g["t1"] - tt["t1"]) <= 3 / fps
            if ok:
                hit, g["_used"] = g, True
                break
        rows.append({"truth": tt, "measured": hit and {k: v for k, v in hit.items() if not k.startswith("_")}})
    extra = [g for g in got if not g.get("_used")]
    return rows, extra


def _staggers(truth, motion):
    groups = {}
    for e in truth["events"]:
        if e["scope"] == "mvp" and e["element"] != "camera":
            groups.setdefault((e["shot"], e["prop"], e["ease"], e["dur"]), []).append(e["t0"])
    want = []
    for (shot, prop, *_), t0 in groups.items():
        t0 = sorted(set(t0))
        d = np.diff(t0)
        if len(t0) >= 3 and np.ptp(d) < 1e-6:
            want.append({"shot": shot, "prop": prop, "count": len(t0), "interval_s": round(float(d[0]), 3),
                         "t": (t0[0], t0[-1])})
    want = {(w["shot"], w["t"]): w for w in want}.values()     # one stagger per group of elements
    rows = []
    for w in want:
        hit = None
        for s in motion["grammar"]["stagger"]:
            sh = motion["shots"][s["shot"]]
            if sh["t0"] - 0.1 <= w["t"][0] <= sh["t1"] and abs(s["interval_s"] - w["interval_s"]) <= 0.3 * w["interval_s"]:
                hit = s
                break
        rows.append({"truth": w, "measured": hit})
    return rows


def _stepping(truth, motion):
    rows = []
    for st in truth.get("stepping", []):
        mid = (st["t0"] + st["t1"]) / 2
        sh = next((s for s in motion["shots"] if s["t0"] <= mid < s["t1"]), None)
        rows.append({"truth": st, "measured": sh and sh.get("stepping")})
    return rows


def score(truth, motion) -> dict:
    fps = truth["fps"]
    rows, spurious = match(truth, motion)
    props = []
    for te, m in rows:
        r = {"element": te["element"], "prop": te["prop"], "scope": te["scope"],
             "truth": f"{te['ease']} {te['t0']:.2f}-{te['t1']:.2f}s", "found": bool(m)}
        if m:
            _, ev, p = m
            tc = checkpoints(te["ease"], te["t0"], te["t1"])
            r.update({
                "measured": f"{p['best']} {p['t0']:.2f}-{p['t1']:.2f}s", "claimed": p["ease"] != "unknown",
                "bic_gap": p["bic_gap"],
                "t0_err_f": round((p["t0"] - te["t0"]) * fps, 1),
                "t50_err_f": round((p["checkpoints"]["t50"] - tc[50]) * fps, 1),
                "ease_exact": p["best"] == te["ease"],
                "family_ok": eases.family(p["best"]) == eases.family(te["ease"]),
                "family_or_equivalent_ok": eases.family(te["ease"]) in {eases.family(p["best"]), *p.get("equivalent", [])},
                "class_ok": eases.shape_class(p["best"]) == eases.shape_class(te["ease"]),
                "overshoot": [round(peak_overshoot(te["ease"]), 3), p["overshoot"]],
                "note": p.get("pinned") or p.get("tied_to"),
            })
        props.append(r)
    trans, extra = _transitions(truth, motion)
    return {"props": props, "spurious": spurious, "transitions": trans, "extra_transitions": extra,
            "staggers": _staggers(truth, motion), "stepping": _stepping(truth, motion)}


def aggregate(scores: list[dict]) -> dict:
    mvp = [r for s in scores for r in s["props"] if r["scope"] == "mvp"]
    v1 = [r for s in scores for r in s["props"] if r["scope"] == "v1"]
    found = [r for r in mvp if r["found"]]
    claimed = [r for r in found if r["claimed"]]
    mean = lambda xs: round(float(np.mean(xs)), 3) if len(xs) else None  # noqa: E731
    trans = [t for s in scores for t in s["transitions"]]
    return {
        "props": len(mvp), "found": len(found), "recall": mean([r["found"] for r in mvp]),
        "spurious": sum(len(s["spurious"]) for s in scores),
        "t50_within_1f": mean([abs(r["t50_err_f"]) <= 1 for r in found]),
        "t50_abs_err_f_median": float(np.median([abs(r["t50_err_f"]) for r in found])) if found else None,
        "class_ok": mean([r["class_ok"] for r in found]), "family_ok": mean([r["family_ok"] for r in found]),
        "claimed": len(claimed), "claimed_wrong": sum(not r["family_or_equivalent_ok"] for r in claimed),
        "claimed_wrong_rate": mean([not r["family_or_equivalent_ok"] for r in claimed]) if claimed else 0.0,
        "transitions": len(trans), "transitions_found": sum(bool(t["measured"]) for t in trans),
        "extra_transitions": sum(len(s["extra_transitions"]) for s in scores),
        "staggers": sum(len(s["staggers"]) for s in scores),
        "staggers_found": sum(bool(x["measured"]) for s in scores for x in s["staggers"]),
        "stepping": sum(len(s["stepping"]) for s in scores),
        "stepping_ok": sum(bool(x["measured"]) and x["measured"]["on"] == x["truth"]["on"]
                           for s in scores for x in s["stepping"]),
        "v1_props": len(v1), "v1_found": sum(r["found"] for r in v1),
    }


def verdict(agg: dict) -> list[str]:
    out = []
    for k, target in TARGETS.items():
        v = agg[k]
        ok = v is not None and (v <= target if k == "claimed_wrong_rate" else v >= target)
        out.append(f"{'✓' if ok else '✗'} {k} {v} (target {'≤' if k == 'claimed_wrong_rate' else '≥'} {target})")
    return out


def _fixture_md(name, s):
    lines = [f"### {name}", "",
             "| element | prop | scope | truth | measured | claimed (BIC gap) | t0 err (f) | t50 err (f) | family | class |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for r in s["props"]:
        if not r["found"]:
            lines.append(f"| {r['element']} | {r['prop']} | {r['scope']} | {r['truth']} | **missed** | | | | | |")
            continue
        note = f" ({r['note']})" if r["note"] else ""
        lines.append(f"| {r['element']} | {r['prop']} | {r['scope']} | {r['truth']} | {r['measured']}{note} | "
                     f"{'yes' if r['claimed'] else 'no'} ({r['bic_gap']}) | {r['t0_err_f']} | {r['t50_err_f']} | "
                     f"{'✓' if r['family_ok'] else '✗'} | {'✓' if r['class_ok'] else '✗'} |")
    for t in s["transitions"]:
        tt, m = t["truth"], t["measured"]
        when = f"{tt.get('t', tt.get('t0'))}s"
        lines.append(f"\nTransition {tt['type']} at {when}: " + (f"found ({m.get('ease') or m['type']})" if m else "**missed**"))
    for x in s["extra_transitions"]:
        lines.append(f"\nExtra transition: {x['type']} at {x.get('t', x.get('t0')):.2f}s")
    for x in s["staggers"]:
        lines.append(f"\nStagger {x['truth']['count']} × {x['truth']['interval_s']}s: "
                     + (f"found {x['measured']['count']} × {x['measured']['interval_s']}s" if x["measured"] else "**missed**"))
    for x in s["stepping"]:
        lines.append(f"\nOn {x['truth']['on']}s (shot {x['truth']['shot']}): measured {x['measured']}")
    if s["spurious"]:
        lines.append(f"\nSpurious: {', '.join(s['spurious'])}")
    return "\n".join(lines) + "\n"


def report(dirs: list[Path], variants: list[str], out: Path) -> str:
    from ..motion.extract import measure
    per, details = {v: [] for v in variants}, []
    for d in dirs:
        truth = json.loads((d / "truth.json").read_text())
        for v in variants:
            motion = measure(str(d / f"{v}.mp4"), out / f"{d.name}-{v}")
            s = score(truth, motion)
            per[v].append(s)
            details.append(_fixture_md(f"{d.name} · {v}", s))
    lines = ["# Motion bench", "", f"{len(dirs)} test films × {', '.join(variants)}. Generated by `moodreel bench motion`.", ""]
    head = ("| variant | props found | spurious | t50 ≤ 1 f | class | family | named / wrong | transitions | "
            "staggers | stepping | v1 found |")
    lines += [head, "|---|---|---|---|---|---|---|---|---|---|---|"]
    for v in variants:
        a = aggregate(per[v])
        lines.append(f"| {v} | {a['found']}/{a['props']} | {a['spurious']} | {a['t50_within_1f']} | {a['class_ok']} | "
                     f"{a['family_ok']} | {a['claimed']} / {a['claimed_wrong']} | {a['transitions_found']}/{a['transitions']}"
                     f" (+{a['extra_transitions']}) | {a['staggers_found']}/{a['staggers']} | "
                     f"{a['stepping_ok']}/{a['stepping']} | {a['v1_found']}/{a['v1_props']} |")
    lines.append("")
    for v in variants:
        lines += [f"**{v}**: " + " · ".join(verdict(aggregate(per[v]))), ""]
    lines += ["## Per film", ""] + details
    return "\n".join(lines)
