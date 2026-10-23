"""Turn tracks into motion events, then events into the style's motion grammar (motion.json)."""
from __future__ import annotations

import numpy as np

from . import eases, extent
from .fit import PREFER, fit_move, shared_bezier
from .track import series

PROP = {"cx": "x", "cy": "y", "s": "scale", "r": "rot", "a": "opacity"}
OPACITY_GAP = 25.0
# smallest travel whose ease may be named: of the width, of scale, in degrees, of the share shown
CLAIM_TRAVEL = {"cx": 0.03, "cy": 0.03, "s": 0.1, "r": 8.0, "share": 0.1}


MAX_RESID = 0.08         # a fit worse than this (rms, in units of the travel) is not one tween


def _drawing_time(t, fps, on):
    """Drawings held on twos (threes): a held frame shows the drawing made when it last changed."""
    if not on or on <= 1:
        return t
    rate = fps / on
    return np.floor(t * rate + 1e-3) / rate


def _cut_off(t, v, f, t_end):
    """Still moving when the window ends: the tween's end level was never seen, so its ease can't be named."""
    if f is None or f["t1"] <= t_end + 0.5 / 30:
        return False
    ok = ~np.isnan(v)
    tv, vv = t[ok], v[ok]
    if len(tv) < 4:
        return False
    tail = abs(vv[-1] - vv[-3]) / max(tv[-1] - tv[-3], 1e-6)
    mean = abs(f["delta"]) / max(f["dur"], 1e-6)
    return tail > 0.15 * mean


def _doubt(f: dict, **why) -> dict:
    """Neither the family nor the class of this curve can be named (its start or end was not seen, or it is too
    small to have a shape)."""
    f.update(ease="unknown", **{"class": None}, **why)
    return f


def _keep(f: dict, t, v, w=None) -> dict:
    """The readings a fit was made from, for the style's shared curve (dropped before motion.json is written)."""
    ok = ~np.isnan(v) & (np.ones_like(v, bool) if w is None else np.asarray(w) > 0)
    f["_samples"] = {"t": np.asarray(t)[ok], "v": np.asarray(v)[ok]}
    return f


def _one_axis(t, fps, X, prefer) -> dict | None:
    """A stretch or a wipe, read as the share shown (0 to 1): its start and end levels are seen, nothing hidden."""
    f = fit_move(t, X["series"], fps, prefer=prefer)
    if not f or f["resid"] > MAX_RESID or abs(f["delta"]) < 0.1:
        return None
    if _cut_off(t, X["series"], f, t[-1]):
        _doubt(f, cut_off=True)
    elif abs(f["delta"]) < CLAIM_TRAVEL["share"]:
        _doubt(f)
    return _keep({**f, "anchor": X["anchor"]}, t, X["series"])


def element_events(clip, track: dict, on: int = 1) -> dict:
    S = series(clip, track)
    t, fps, W, H = _drawing_time(S["t"], clip.fps, on), clip.fps, clip.src_w, clip.src_h
    side = S["edge_side"]
    out = {"kind": track["kind"], "shot": track["shot"], "box": [round(v, 1) for v in track["box"]],
           "via_edge": side, "props": {}}
    role = {"appear": "entrance", "disappear": "exit"}.get(track["kind"], "move")
    prefer = PREFER[role]
    # one axis changing while an edge holds still: a stretch, a wipe or a clip reveal, which the template misreads
    X = extent.reading(clip, track)
    if X and X["mode"] != "clip":
        f = _one_axis(t, fps, X, prefer)
        if f:
            out["reading"] = {k: X[k] for k in ("mode", "axis", "anchor")}
            out["props"][X["prop"]] = f
            return out
    elif X:
        # a clip reveal is a move whose leading edge is seen before the whole element is: no scale, no fade
        out["reading"] = {k: X[k] for k in ("mode", "axis", "anchor")}
        key = "c" + X["axis"]
        S = {**S, key: X["series"], "s": np.full_like(S["s"], np.nan), "r": np.full_like(S["r"], np.nan),
             "a": np.zeros_like(S["a"]), "intermediate_a": 0,
             "w": np.where(np.isnan(X["series"]), 0.0, 1.0)}
    # a flat elongated shape: its turn from the silhouette's axis, where the template's can't be trusted
    silhouette = False
    if np.nanmax(np.abs(np.nan_to_num(S["r"]))) < 1.0:
        R = extent.turn(clip, track)
        if R is not None and np.nanmax(np.abs(np.nan_to_num(R))) >= 4.0:
            S, silhouette = {**S, "r": R}, True
    a = S["a"]
    afit = None
    # a fade is claimed only when it is seen: three or more trustworthy readings part-way between 0 and 1
    if np.nanmax(a) - np.nanmin(a) > 0.15 and S["intermediate_a"] >= 3:
        afit = fit_move(t, a, fps, monotone=True, gap_needed=OPACITY_GAP, prefer=prefer)
        if afit and afit["dur"] < 3 / fps:          # a one-frame jump is an element arriving, not a fade
            afit = None
    if afit:
        out["props"]["opacity"] = afit
    # a change counts when the fitted travel is large enough; what is seen of it can be much less (a rise that
    # starts transparent is half done when it becomes visible), but not mere jitter
    thr = {"cx": 0.008 * W, "cy": 0.008 * W, "s": 0.04, "r": 4.0}
    seen = {"cx": 0.003 * W, "cy": 0.003 * W, "s": 0.02, "r": 2.0}
    bw, bh = track["box"][2], track["box"][3]
    offscreen = {("cx", "left"): -bw / 2, ("cx", "right"): W + bw / 2,
                 ("cy", "top"): -bh / 2, ("cy", "bottom"): H + bh / 2}
    for k in ("cx", "cy", "s", "r"):
        v = S[k]
        valid = ~np.isnan(v)
        if valid.sum() < 5 or np.nanpercentile(v, 95) - np.nanpercentile(v, 5) < seen[k]:
            continue
        tv = t[valid]
        t0_range, t1_max, start, end = None, None, None, None
        pin = offscreen.get((k, side))
        if track["kind"] == "appear":                # its start may be hidden (transparent or off frame)
            lo = (afit["t0"] if afit else t[0]) - 3 / fps
            t0_range = (lo, tv[0])
            start = pin                              # entering from off frame: assume it starts just outside
        elif track["kind"] == "disappear":
            t1_max = max(tv[-1], afit["t1"] if afit else t[-1]) + 3 / fps
            end = pin
        if k == "r" and silhouette:                  # seen wherever it is read, before and after: nothing hidden
            f = fit_move(t, v, fps, prefer=prefer)
        else:
            f = fit_move(t, v, fps, t0_range, t1_max, w=S["w"], start=start, end=end, prefer=prefer)
        if f and k == "s" and f["from"] < 0:          # a scale can't start below zero: it grew from nothing
            f = fit_move(t, v, fps, t0_range, t1_max, w=S["w"], start=0.0, prefer=prefer) or f
        # one start or two? Tweens placed at one timeline position share their start (GSAP from({y, opacity}),
        # or a scale and a fade at the same label). If pinning this prop's start to the fade's costs (almost)
        # nothing, the simpler story wins: the fade's start is observed, this prop's start is hidden
        if f and afit and abs(f["t0"] - afit["t0"]) > 1 / fps:
            tied = fit_move(t, v, fps, (afit["t0"] - 1 / fps, afit["t0"] + 1 / fps), t1_max, w=S["w"],
                            start=start if start is not None else (0.0 if k == "s" and f["pinned"] else None), end=end,
                            prefer=prefer)
            if tied and tied["bic"] <= f["bic"] + 4:
                f = _doubt(tied, tied_to="opacity")   # its start is borrowed from the fade: an assumption
        if f and (f["resid"] > MAX_RESID or abs(f["delta"]) < thr[k]):
            f = None
        if f and _cut_off(t, v, f, t[-1]):
            _doubt(f, cut_off=True)
        if f and abs(f["delta"]) < CLAIM_TRAVEL[k] * (W if k in ("cx", "cy") else 1):
            _doubt(f)                              # a short travel is measured, but its curve is too small to name
        if f:
            out["props"][PROP[k]] = _keep(f, t, v, S["w"])
    if afit and _cut_off(t, a, afit, t[-1]):
        _doubt(afit, cut_off=True)
    if afit:
        _keep(afit, t, a)
    return out


def onset(ev):
    """When an element's change is half done, by its earliest prop: steadier than t0, which hides in a slow
    or transparent start. A fade's is preferred: its start level (0) is seen. Used for stagger intervals."""
    if "opacity" in ev["props"]:
        return ev["props"]["opacity"]["checkpoints"]["t50"]
    return min(p["checkpoints"]["t50"] for p in ev["props"].values())


def merge_groups(events: list[dict], fps: float) -> list[dict]:
    """Parts that move as one tween (the words of a title) become one element with `members`."""
    tol = 1.5 / fps
    out = []
    for ev in events:
        for g in out:
            if g["kind"] != ev["kind"] or g["shot"] != ev["shot"] or set(g["props"]) != set(ev["props"]) or not ev["props"]:
                continue
            same = all(abs(g["props"][k]["t0"] - p["t0"]) <= tol and abs(g["props"][k]["t1"] - p["t1"]) <= tol
                       and (k in ("scale", "opacity") or abs(g["props"][k]["delta"] - p["delta"]) <= 0.15 * abs(p["delta"]))
                       for k, p in ev["props"].items())
            if same:
                x0, y0 = min(g["box"][0], ev["box"][0]), min(g["box"][1], ev["box"][1])
                x1 = max(g["box"][0] + g["box"][2], ev["box"][0] + ev["box"][2])
                y1 = max(g["box"][1] + g["box"][3], ev["box"][1] + ev["box"][3])
                g["box"] = [x0, y0, x1 - x0, y1 - y0]
                g["members"] = g.get("members", [g["id"]]) + [ev["id"]]
                break
        else:
            out.append(ev)
    return out


def label(ev: dict, frame=(1920, 1080)) -> str:
    """A plain name for the element's change. Off-frame is read from the edge it crossed, or from a fitted start
    (or end) level outside the frame: an element can jump from off frame to fully inside in one frame."""
    p = ev["props"]
    parts = []
    mode = (ev.get("reading") or {}).get("mode")
    for k in ("sy", "sx"):
        if k in p:
            parts.append(("grow-" if ev["kind"] != "disappear" else "collapse-") + k[1])
    if "wipe" in p:
        parts.append("wipe-" + ("out" if ev["kind"] == "disappear" else "in"))
    if "scale" in p:
        parts.append("scale-pop" if p["scale"]["overshoot"] > 0.02 else "scale")
    for axis, size in (("x", frame[0]), ("y", frame[1])):
        if axis not in p:
            continue
        d = p[axis]["delta"]
        far = p[axis]["to"] if ev["kind"] == "disappear" else p[axis]["from"]
        half = ev["box"][2 + (axis == "y")] / 2
        off = ev["via_edge"] or far < -half * 0.5 or far > size + half * 0.5
        if mode == "clip":
            parts.append(("clip-rise" if d < 0 else "clip-drop") if axis == "y" else "clip-slide")
        elif ev["kind"] in ("move", "change") and not off:
            parts.append(f"move-{axis}")
        elif off:
            parts.append(("slide" if axis == "x" else "drop" if d > 0 else "rise") +
                         ("-out" if ev["kind"] == "disappear" else "-in"))
        else:
            parts.append({"x": "drift-x", "y": "rise" if d < 0 else "sink"}[axis])
    if "rot" in p:
        parts.append("turn")
    if "opacity" in p:
        parts.append("fade")
    return "+".join(parts) or "static"


def main_prop(ev):
    for k in ("scale", "sy", "sx", "wipe", "y", "x", "rot", "opacity"):
        if k in ev["props"]:
            return k
    return None


def _stats(xs):
    xs = np.asarray([x for x in xs if x is not None], float)
    if not len(xs):
        return None
    return {"n": int(len(xs)), "median": round(float(np.median(xs)), 3),
            "p25": round(float(np.percentile(xs, 25)), 3), "p75": round(float(np.percentile(xs, 75)), 3)}


def grammar(clip, shots_, transitions, runs_by_shot, events, cam_events=()) -> dict:
    W, H = clip.src_w, clip.src_h
    role = {"appear": "entrance", "disappear": "exit", "move": "move", "change": "move"}
    groups = {"entrance": [], "exit": [], "move": []}
    for ev in events:
        if ev["props"]:
            groups[role[ev["kind"]]].append(ev)

    def summarise(evs):
        if not evs:
            return None
        durs, eases_, classes, guesses, labels, over, named = [], {}, {}, {}, {}, [], 0
        travel, by_class, onsets, named_at = [], {}, {}, []
        for ev in evs:
            m = ev["props"][main_prop(ev)]
            durs.append(max(p["dur"] for p in ev["props"].values()))
            labels[ev["label"]] = labels.get(ev["label"], 0) + 1
            for ax, size in (("x", W), ("y", H)):
                if ax in ev["props"]:
                    travel.append(abs(ev["props"][ax]["delta"]) / size)
            if m["ease"] != "unknown":
                eases_[m["ease"]] = eases_.get(m["ease"], 0) + 1
                if not any(abs(m["checkpoints"]["t50"] - t) <= 1 / clip.fps for t in named_at):
                    named_at.append(m["checkpoints"]["t50"])   # pieces of one move name it once
                    named += 1
            else:                                       # the fit's best guess is kept apart: it never becomes a token
                guesses[m["best"]] = guesses.get(m["best"], 0) + 1
            c = m.get("class") or (eases.shape_class(m["ease"]) if m["ease"] != "unknown" else None)
            # two pieces of one move (the halves of a title split by the tracker) are one reading
            if c and not any(abs(m["checkpoints"]["t50"] - t) <= 1 / clip.fps for t in onsets.get(c, ())):
                onsets.setdefault(c, []).append(m["checkpoints"]["t50"])
                classes[c] = classes.get(c, 0) + 1
                over.append(m["overshoot"])
                if m.get("_samples") is not None:
                    by_class.setdefault(c, []).append({**m["_samples"], "A": m["from"], "B": m["delta"],
                                                       "t0": m["t0"], "t1": m["t1"]})
        out = {"count": len(evs), "claimed": named, "class_claimed": len(over), "duration_s": _stats(durs),
               "eases": eases_, "classes": classes, "guesses": guesses, "vocabulary": labels,
               "overshoot_share": round(float(np.mean([o > 0.02 for o in over])), 2) if over else None,
               "overshoot": _stats([o for o in over if o > 0.02]),
               "travel_frac_of_frame": _stats(travel)}
        # the style's own curve: one cubic-bezier through every tween of the role's commonest claimed class
        if classes:
            top = max(classes, key=classes.get)
            curve = shared_bezier(by_class.get(top, []))
            if curve and curve["resid"] <= MAX_RESID:
                out["curve"] = {**curve, "class": top}
        scales = [ev["props"]["scale"]["from"] for ev in evs if "scale" in ev["props"]]
        if scales:
            out["scale_from"] = _stats(scales)
        return out

    stagger = []
    for sh in shots_:
        ents = [e for e in groups["entrance"] if e["shot"] == sh["id"]]
        by_label = {}
        for e in ents:
            by_label.setdefault(e["label"], []).append(e)
        for lab, es in by_label.items():
            if len(es) < 3:
                continue
            es = sorted(es, key=onset)
            d = np.diff([onset(e) for e in es])
            if np.all(d > 0) and np.std(d) / np.mean(d) < 0.3:
                xs = [e["box"][0] for e in es]
                ys = [e["box"][1] for e in es]
                order = ("left-to-right" if xs == sorted(xs) else "right-to-left" if xs == sorted(xs, reverse=True)
                         else "top-to-bottom" if ys == sorted(ys) else "unordered")
                stagger.append({"shot": sh["id"], "vocabulary": lab, "count": len(es),
                                "interval_s": round(float(np.median(d)), 3), "order": order})

    moving, holds = 0, []
    for sh in shots_:
        runs = runs_by_shot[sh["id"]]
        moving += sum(b - a for a, b in runs)
        edges = [sh["start"]] + [x for r in runs for x in r] + [sh["end"]]
        holds += [(edges[i + 1] - edges[i]) / clip.fps for i in range(0, len(edges) - 1, 2)]
    total = sum(s["end"] - s["start"] for s in shots_)
    lengths = [round(s["t1"] - s["t0"], 3) for s in shots_]
    dis = [tr for tr in transitions if tr["type"] == "dissolve"]
    dips = [tr for tr in transitions if tr["type"] == "dip"]
    steps = [s["stepping"]["on"] for s in shots_ if s.get("stepping")]
    cams = {}
    for c in cam_events:
        cams.setdefault(c["prop"], []).append(c)
    return {
        "shots": {"count": len(shots_), "length_s": _stats(lengths), "lengths": lengths,
                  "cuts": sum(tr["type"] == "cut" for tr in transitions), "dissolves": len(dis),
                  "dissolve_s": _stats([d["t1"] - d["t0"] for d in dis]), "dips": len(dips),
                  "dip_s": _stats([d["t1"] - d["t0"] for d in dips]),
                  "dip_colors": sorted({d["color"] for d in dips})},
        "stepping": {"on": max(set(steps), key=steps.count), "shots": len(steps)} if steps else None,
        "camera": {"moving_shots": len({c["shot"] for c in cam_events}),
                   "moves": {k: {"count": len(v), "duration_s": _stats([c["dur"] for c in v]),
                                 "eases": sorted({c["best"] for c in v}),
                                 "range": _stats([abs(c["delta"]) for c in v])} for k, v in cams.items()},
                   "locked_shots": sum(s.get("camera") == "locked" for s in shots_),
                   "unknown_shots": sum(s.get("camera") == "unknown" for s in shots_)},
        "motion_density": round(moving / max(total, 1), 3),
        "hold_s": _stats([h for h in holds if h > 0]),
        "entrance": summarise(groups["entrance"]), "exit": summarise(groups["exit"]),
        "move": summarise(groups["move"]), "stagger": stagger,
    }
