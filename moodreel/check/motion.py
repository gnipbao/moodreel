"""`moodreel motion-check <project> <video>`: does a rendered film move the way the style does?

The film is measured with the same code as the references (as REM checks a rebuild), and the two grammars are
compared claim by claim, MoVer-style: each claim passes, fails, or is unknown when either side has no data
(unknown never passes). The failures, with the numbers on both sides, are what the director fixes.

The claims on a film's pace (its holds, shot lengths and how much of it moves) are advice, not rules: they follow the
film's content and are the film's to choose, so they are reported but never fail it. The motion's character (how
long things take to arrive and leave, their curves and overshoot, staggers, stepping, the transitions) is the style's.
"""
from __future__ import annotations

import json
from pathlib import Path

from ..motion.extract import measure

FRAME = 0.05             # s: about a frame at 24 fps, the least a duration can be measured to
SHORT = 0.17             # s: about four frames at 24 fps, the shortest tween whose length can be compared
TOL = {"duration": 0.25, "class_share": 0.20, "overshoot_share": 0.25, "stagger": 0.30, "hold": 0.8,
       "shot": 0.35, "density": 0.15}
PACE = {"hold", "shot_length", "density"}        # the film's pace: reported as advice, not counted


def _med(x, k="duration_s"):
    return ((x or {}).get(k) or {}).get("median")


def _dominant(role):
    c = (role or {}).get("classes") or {}
    return (max(c, key=c.get), c[max(c, key=c.get)] / sum(c.values())) if c else (None, None)


def claims(ref: dict, got: dict) -> list[dict]:
    out = []

    def add(cid, rule, rv, gv, ok):
        res = "unknown" if ok is None else "pass" if ok else "fail"
        if cid in PACE and res != "pass":                  # the film's own pace: advice, never a failure
            res = "advice"
        out.append({"id": cid, "rule": rule, "reference": rv, "film": gv, "result": res})

    for role in ("entrance", "exit", "move", "counters"):
        R, G = ref.get(role), got.get(role)
        if not R:
            continue
        rd, gd = _med(R), _med(G)
        # a tween of three or four frames can't be timed closer than its frames: no claim on it
        add(f"{role}.duration", f"median within ±{TOL['duration']:.0%} (at least a frame)", rd, gd,
            None if rd is None or gd is None or rd < SHORT else abs(gd - rd) <= max(TOL["duration"] * rd, FRAME))
        rc, rs = _dominant(R)
        gc = (G or {}).get("classes") or {}
        gs = gc.get(rc, 0) / sum(gc.values()) if gc else None      # nothing read in the film is no contradiction
        add(f"{role}.ease_class", f"share of '{rc}' within ±{TOL['class_share']:.0%}", rs and round(rs, 2),
            gs if gs is None else round(gs, 2), None if gs is None or rs is None else abs(gs - rs) <= TOL["class_share"])
        ro, go = R.get("overshoot_share"), (G or {}).get("overshoot_share")
        add(f"{role}.overshoot_share", f"within ±{TOL['overshoot_share']:.0%}", ro, go,
            None if ro is None or go is None else abs(go - ro) <= TOL["overshoot_share"])
        if R.get("overshoot"):
            lo, hi = R["overshoot"]["p25"] / 1.5, R["overshoot"]["p75"] * 1.5
            gm = ((G or {}).get("overshoot") or {}).get("median")
            add(f"{role}.overshoot", "median within reference p25/1.5 .. p75*1.5", [round(lo, 3), round(hi, 3)], gm,
                None if gm is None else lo <= gm <= hi)
    re_, rx = _med(ref.get("entrance")), _med(ref.get("exit"))
    if re_ and rx and rx < re_:
        ge, gx = _med(got.get("entrance")), _med(got.get("exit"))
        add("exit_shorter", "exits shorter than entrances", [rx, re_], [gx, ge], None if ge is None or gx is None else gx < ge)
    if ref.get("stagger"):                         # the references may stagger different groups differently: any one
        ri = sorted({s["interval_s"] for s in ref["stagger"]})
        gi = [s["interval_s"] for s in got.get("stagger") or []]
        add("stagger", f"a stagger within ±{TOL['stagger']:.0%} of one of the intervals", ri[0] if len(ri) == 1 else ri,
            gi or None, None if not gi else any(abs(x - r) <= TOL["stagger"] * r for x in gi for r in ri))
    rh, gh = _med(ref, "hold_s"), _med(got, "hold_s")
    add("hold", f"median hold at least {TOL['hold']:.0%} of the reference's", rh, gh,
        None if rh is None or gh is None else gh >= TOL["hold"] * rh)
    rs_, gs_ = ref.get("shots") or {}, got.get("shots") or {}
    if rs_.get("count", 0) >= 2:
        rl, gl = _med(rs_, "length_s"), _med(gs_, "length_s")
        add("shot_length", f"median within ±{TOL['shot']:.0%}", rl, gl,
            None if rl is None or gl is None else abs(gl - rl) <= TOL["shot"] * rl)
    kinds = lambda s: {k for k, n in (("cut", s.get("cuts", 0)), ("dissolve", s.get("dissolves", 0)), ("dip", s.get("dips", 0))) if n}  # noqa: E731
    add("transition_types", "no transition the references don't use", sorted(kinds(rs_)), sorted(kinds(gs_)),
        kinds(gs_) <= kinds(rs_) if gs_ else None)
    rdn, gdn = ref.get("motion_density"), got.get("motion_density")
    add("density", f"within ±{TOL['density']}", rdn, gdn, None if rdn is None or gdn is None else abs(gdn - rdn) <= TOL["density"])
    ron, gon = (ref.get("stepping") or {}).get("on", 1), (got.get("stepping") or {}).get("on", 1)
    add("stepping", "drawings held on the same number of frames", ron, gon, ron == gon)
    return out


def check(project: Path, video: Path, reference: str | None = None, out: Path | None = None) -> dict:
    """project: a project or a packed style. out: where the film's measurement and the result go."""
    from .frame import measure_dir
    project = Path(project)
    mdir = measure_dir(project)
    m = json.loads((mdir / "motion.json").read_text())
    ref = m["grammar"]
    if "videos" in ref:                             # several references: compare with the one named, or the first
        vid = reference or ref["videos"][0]
        ref = m["per_video"][vid]["grammar"]
    film = measure(str(video), (Path(out) if out else project / "evidence") / f"motion-check-{Path(video).stem}")
    cs = claims(ref, film["grammar"])
    res = {"video": str(video), "claims": cs, "pass": sum(c["result"] == "pass" for c in cs),
           "fail": sum(c["result"] == "fail" for c in cs), "unknown": sum(c["result"] == "unknown" for c in cs),
           "advice": sum(c["result"] == "advice" for c in cs)}
    counted = len(cs) - res["advice"]
    res["ok"] = res["fail"] == 0 and res["unknown"] <= counted // 4
    (Path(out) if out else mdir).mkdir(parents=True, exist_ok=True)
    ((Path(out) if out else mdir) / f"motion-check-{Path(video).stem}.json").write_text(json.dumps(res, indent=1, default=float))
    return res
