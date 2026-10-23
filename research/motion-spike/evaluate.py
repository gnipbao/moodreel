"""Score a motion.json against the fixture's truth.json.

  .venv/bin/python research/motion-spike/evaluate.py <truth.json> <motion.json> [--md report.md]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from motionx import eases  # noqa: E402


def checkpoints(ease, t0, t1):
    u = np.linspace(0, 1, 4001)
    y = eases.get(ease)(u)
    return {q: t0 + (t1 - t0) * float(u[np.argmax(y >= q / 100)]) for q in (10, 50, 90)}


def peak_overshoot(ease):
    u = np.linspace(0, 1, 4001)
    return float(max(0.0, eases.get(ease)(u).max() - 1))


def match(truth, motion):
    W = truth["W"]
    k = W / motion["source"]["w"]                       # measured px -> truth px (the stress copy is smaller)
    for ev in motion["events"]:
        ev["box"] = [v * k for v in ev["box"]]
        for name, p in ev["props"].items():
            if name in ("x", "y"):
                p["from"], p["to"] = round(p["from"] * k, 1), round(p["to"] * k, 1)
    rows, used = [], {}
    for te in truth["events"]:
        best = None
        for ev in motion["events"]:
            p = ev["props"].get(te["prop"])
            # a merged group (parts that moved as one tween) stands for each of its members
            if p is None or used.get((ev["id"], te["prop"]), 0) >= len(ev.get("members", [ev["id"]])):
                continue
            bx = ev["box"][0] + ev["box"][2] / 2
            by = ev["box"][1] + ev["box"][3] / 2
            # the box is where the element rests: for an exit, where it was; for x/y moves, compare the axis
            # that did not move, plus time
            ex, ey = te["end_xy"]
            dist = abs(by - ey) if te["prop"] == "x" else abs(bx - ex) if te["prop"] == "y" else np.hypot(bx - ex, by - ey)
            if ev.get("members"):                       # the group box spans its members
                dist = 0 if (ev["box"][0] <= ex <= ev["box"][0] + ev["box"][2]
                             and ev["box"][1] <= ey <= ev["box"][1] + ev["box"][3]) else dist
            dt = abs(p["t0"] - te["t0"])
            if dist < 0.1 * W and dt < 0.3 and (best is None or dt < best[0]):
                best = (dt, ev, p)
        if best:
            key = (best[1]["id"], te["prop"])
            used[key] = used.get(key, 0) + 1
        rows.append((te, best))
    spurious = [(ev["id"], k) for ev in motion["events"] for k in ev["props"] if (ev["id"], k) not in used]
    return rows, spurious


def score(truth, motion):
    fps = truth["fps"]
    rows, spurious = match(truth, motion)
    out = []
    for te, m in rows:
        r = {"element": te["element"], "prop": te["prop"], "truth": f"{te['ease']} {te['t0']:.2f}-{te['t1']:.2f}s"}
        if not m:
            r["found"] = False
            out.append(r)
            continue
        _, ev, p = m
        tc = checkpoints(te["ease"], te["t0"], te["t1"])
        r.update({
            "found": True, "measured": f"{p['best']} {p['t0']:.2f}-{p['t1']:.2f}s", "claimed": p["ease"] != "unknown",
            "bic_gap": p["bic_gap"],
            "t0_err_f": round((p["t0"] - te["t0"]) * fps, 1),
            "t50_err_f": round((p["checkpoints"]["t50"] - tc[50]) * fps, 1),
            "t90_err_f": round((p["checkpoints"]["t90"] - tc[90]) * fps, 1),
            "dur_err_s": round(p["dur"] - te["dur"], 3),
            "ease_exact": p["best"] == te["ease"],
            "family_ok": eases.family(p["best"]) == eases.family(te["ease"]),
            "class_ok": eases.shape_class(p["best"]) == eases.shape_class(te["ease"]),
            "overshoot": [round(peak_overshoot(te["ease"]), 3), p["overshoot"]],
            "from_to": [[te["from"], te["to"]], [p["from"], p["to"]]],
            "pinned_or_tied": p.get("pinned") or p.get("tied_to"),
        })
        out.append(r)
    found = [r for r in out if r["found"]]
    agg = {
        "truth_props": len(out), "found": len(found), "recall": round(len(found) / len(out), 3),
        "spurious": spurious,
        "t0_abs_err_f_median": float(np.median([abs(r["t0_err_f"]) for r in found])),
        "t50_abs_err_f_median": float(np.median([abs(r["t50_err_f"]) for r in found])),
        "t90_abs_err_f_median": float(np.median([abs(r["t90_err_f"]) for r in found])),
        "within_1f_t50": round(np.mean([abs(r["t50_err_f"]) <= 1 for r in found]), 3),
        "ease_exact": round(np.mean([r["ease_exact"] for r in found]), 3),
        "family_ok": round(np.mean([r["family_ok"] for r in found]), 3),
        "class_ok": round(np.mean([r["class_ok"] for r in found]), 3),
        "claimed": sum(r["claimed"] for r in found),
        "claimed_wrong": sum(r["claimed"] and not r["family_ok"] for r in found),
    }
    tr = {"truth": truth["transitions"],
          "measured": [{k: v for k, v in t.items() if k in ("type", "t", "t0", "t1", "ease")} for t in motion["transitions"]]}
    st = motion["grammar"]["stagger"]
    return out, agg, tr, st


def to_md(name, rows, agg, tr, st):
    lines = [f"### {name}", "",
             f"recall {agg['found']}/{agg['truth_props']} · spurious {len(agg['spurious'])} · "
             f"median |error| t0 {agg['t0_abs_err_f_median']} f, t50 {agg['t50_abs_err_f_median']} f, "
             f"t90 {agg['t90_abs_err_f_median']} f · t50 within 1 frame {agg['within_1f_t50']:.0%} · "
             f"ease exact {agg['ease_exact']:.0%}, family {agg['family_ok']:.0%}, class {agg['class_ok']:.0%} · "
             f"claimed {agg['claimed']}, claimed wrong {agg['claimed_wrong']}", "",
             "| element | prop | truth | measured | claimed | t0 err (f) | t50 err (f) | family | class | overshoot truth / measured |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        if not r["found"]:
            lines.append(f"| {r['element']} | {r['prop']} | {r['truth']} | **missed** | | | | | | |")
            continue
        lines.append(f"| {r['element']} | {r['prop']} | {r['truth']} | {r['measured']}"
                     f"{' (' + r['pinned_or_tied'] + ')' if r['pinned_or_tied'] else ''} | "
                     f"{'yes' if r['claimed'] else 'no'} ({r['bic_gap']}) | {r['t0_err_f']} | {r['t50_err_f']} | "
                     f"{'✓' if r['family_ok'] else '✗'} | {'✓' if r['class_ok'] else '✗'} | "
                     f"{r['overshoot'][0]} / {r['overshoot'][1]} |")
    lines += ["", f"Transitions — truth: {json.dumps(tr['truth'])}", "",
              f"Transitions — measured: {json.dumps(tr['measured'])}", "", f"Stagger — measured: {json.dumps(st)}", ""]
    if agg["spurious"]:
        lines += [f"Spurious: {agg['spurious']}", ""]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("truth")
    ap.add_argument("motion")
    ap.add_argument("--md")
    ap.add_argument("--name", default="")
    a = ap.parse_args()
    truth, motion = json.loads(Path(a.truth).read_text()), json.loads(Path(a.motion).read_text())
    rows, agg, tr, st = score(truth, motion)
    md = to_md(a.name or a.motion, rows, agg, tr, st)
    print(md)
    if a.md:
        Path(a.md).write_text(md)


if __name__ == "__main__":
    main()
