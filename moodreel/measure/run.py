"""`moodreel measure <project>`: every measurement of the references, as JSON for tools and MEASURE.md for the
director. Each number is what the code read off the pictures (observed) or computed from such readings
(derived); naming what it means for the style is left to the director."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np


from .. import sheet
from ..intake import samples
from ..motion.extract import measure as measure_motion
from . import layout, palette, rhythm, texture, typeset


def _pool_motion(per_video: dict) -> dict:
    """With several reference videos, each keeps its own grammar; the pooled view lists the numbers side by side."""
    if len(per_video) == 1:
        return next(iter(per_video.values()))["grammar"]
    keys = ("entrance", "exit", "move", "counters", "loops", "particles", "beat")
    out = {"videos": list(per_video)}
    for k in keys:
        out[k] = {vid: m["grammar"].get(k) for vid, m in per_video.items()}
    out["stagger"] = [dict(s, video=vid) for vid, m in per_video.items() for s in m["grammar"]["stagger"]]
    out["shots"] = {vid: m["grammar"]["shots"] for vid, m in per_video.items()}
    return out


def _scan_px(textures: list[dict], pictures: list) -> float | None:
    """A reference's scanline period in its own pixels (texture reads it at texture.WORK), or None."""
    ps = [t["scanlines"]["period_px"] * max(p.shape[:2]) / texture.WORK for t, p in zip(textures, pictures) if t.get("scanlines")]
    return float(np.median(ps)) if len(ps) * 2 >= len(textures) else None


def measure(project: Path) -> dict:
    project = Path(project)
    intake = json.loads((project / "intake.json").read_text())
    items = intake["refs"]
    (project / "measure").mkdir(exist_ok=True)
    pictures = {it["id"]: samples(it, project) for it in items}
    flat = [(it["id"], p) for it in items for p in pictures[it["id"]]]

    # palette: one per reference (a video's frames as one picture), pooled with equal weight
    # scanlines darken every other few rows: colours and strokes are read with the rows filled in
    tex = {it["id"]: [texture.texture(p) for p in pictures[it["id"]]] for it in items}
    scan = {rid: _scan_px(ts, pictures[rid]) for rid, ts in tex.items()}
    pals = [palette.image_palette(sheet.stack([typeset.descan(p, scan[it["id"]]) if scan[it["id"]] else p
                                               for p in pictures[it["id"]]])) for it in items]
    openings = {it["id"]: palette.opening_ground(f[0]) for it in items if it["kind"] == "video"
                for f in [sheet.video_frames(str(project / it["file"]), [0.05])] if f}
    hint = next(((vid, h) for vid, h in openings.items() if h), None)
    pal = {**palette.pooled(pals, hint and hint[1]), "per_ref": {it["id"]: p for it, p in zip(items, pals)},
           "unity": intake.get("unity"), "ground_from": f"opening frame of {hint[0]}" if hint else "border"}
    ground = pal["roles"]["ground"]

    tex = [texture.texture(p, ground) for _, p in flat]
    lay = [layout.layout(p, ground) for _, p in flat]
    lines = [typeset.text_lines(p, (t.get("halftone") or {}).get("period_px"), (t.get("scanlines") or {}).get("period_px"))
             for (_, p), t in zip(flat, tex)]
    typeset.crops_sheet([p for _, p in flat], lines, project / "evidence" / "type-lines.jpg")
    out = {"palette": pal, "texture": {**texture.pooled(tex), "per_picture": tex},
           "layout": {**layout.pooled(lay), "per_picture": lay},
           "type": {**typeset.pooled(lines), "per_picture": lines}}

    from . import csd
    if csd.ready():                                       # style embeddings, when `moodreel csd setup` has run
        out["style"] = csd.summary([rid for rid, _ in flat], csd.embed([p for _, p in flat]))

    motion, rhy = {}, {}
    for it in items:
        if it["kind"] != "video":
            continue
        m = measure_motion(str(project / it["file"]), project / "evidence" / f"motion-{it['id']}")
        motion[it["id"]] = m
        if it.get("audio"):
            cuts = [t.get("t", t.get("t0")) for t in m["transitions"]]
            arrivals = [min(p["checkpoints"]["t50"] for p in e["props"].values())
                        for e in m["events"] if e["kind"] == "appear" and e["props"]]
            rhy[it["id"]] = rhythm.rhythm(str(project / it["file"]), cuts, arrivals, it["fps"])
    if motion:
        out["motion"] = {"grammar": _pool_motion(motion),
                         "per_video": {vid: {k: m[k] for k in ("source", "shots", "transitions", "camera", "grammar")}
                                       for vid, m in motion.items()}}
    if rhy:
        out["rhythm"] = rhy

    for k, v in out.items():
        (project / "measure" / f"{k}.json").write_text(json.dumps(v, indent=1, ensure_ascii=False, default=float))
    (project / "MEASURE.md").write_text(report(intake, out), encoding="utf-8")
    return out


def _fmt(x, nd=2):
    return "—" if x is None else f"{x:.{nd}f}" if isinstance(x, float) else str(x)


def report(intake: dict, m: dict) -> str:
    """The measurements in words and tables: the director's first read, before the evidence images."""
    pal, tex, lay, typ = m["palette"], m["texture"], m["layout"], m["type"]
    refs = intake["refs"]
    L = ["# Measurements", "",
         f"{len(refs)} references: " + ", ".join(f"{r['id']} ({r['kind']}, {r['w']}x{r['h']}"
                                                  + (f", {r['fps']} fps, {r['duration']} s" if r['kind'] == 'video' else '') + ")"
                                                  for r in refs),
         f"Default size: {intake['default_size']}. Evidence: `evidence/refs-sheet.jpg`, `evidence/type-lines.jpg`"
         + (", `evidence/motion-*/evidence/*.jpg`" if "motion" in m else "") + ".", ""]
    u = intake.get("unity") or {}
    if u and not u.get("unified"):
        L += [f"**The references split into {len(u['groups'])} palettes**: " + " | ".join(", ".join(g) for g in u["groups"])
              + ". Ask which group is the style, or whether to mix them.", ""]
    r, s = pal["roles"], pal["structure"]
    L += ["## Colour (observed)", "",
          f"Ground {r.get('ground')} ({s['ground']}, L* {s['ground_lightness']}); ink {r.get('ink', '—')} "
          f"(contrast {r.get('ink_contrast', '—')}:1); accent {r.get('accent', '—')} (contrast {r.get('accent_contrast', '—')}:1). "
          f"{s['hue_families']} hue families, {s['chromatic_colours']} chromatic colours; mean chroma {s['mean_chroma']}; "
          f"saturated area {s['saturated_area']:.0%}, neutral area {s['neutral_area']:.0%}.", "",
          "| colour | area | L* | chroma | used in refs |", "|---|---|---|---|---|"]
    for c in pal["colors"][:12]:
        L.append(f"| {c['hex']} | {c['area']:.1%} | {c['lightness']} | {c['chroma']} | {c.get('presence', '—')} / {len(refs)} |")
    sm = tex["summary"]
    L += ["", "## Surface (observed)", "",
          f"Grain {sm['grain']} ({_fmt(tex['grain'])} levels), mottle {sm['mottle']} ({_fmt(tex['mottle'])}), "
          f"vignette {sm['vignette']} ({_fmt(tex['vignette'])}), edges {sm['edges']} (sharpness {_fmt(tex['edge_sharpness'], 3)}), "
          f"halftone {'yes ' + json.dumps(tex['halftone']) if tex['halftone'] else 'no'}, "
          f"scanlines {'yes ' + json.dumps(tex['scanlines']) if tex['scanlines'] else 'no'}"
          + (f"; pixel art in {tex['pixel']['share']:.0%} of the pictures: {tex['pixel']['native_width']} px wide natively "
             f"(one pixel = {tex['pixel']['scale_of_width']:.2%} of the width), {tex['pixel']['palette_size']} colours, "
             f"{'ordered dither' if tex['pixel']['dither'] else 'no dither'} ({tex['pixel']['dither_share']:.0%} checkerboard)"
             if tex.get("pixel") else "")
          + (f"; brush marks in {tex['brush']['share']:.0%} of the pictures, over {tex['brush']['coverage']:.0%} of the frame: "
             f"edges every {_fmt(tex['brush']['edge_spacing_px'])} px (at {texture.WORK} px wide), running "
             f"{_fmt(tex['brush']['direction_deg'])}° (0 = across, 90 = up and down; agreement {_fmt(tex['brush']['agreement'])})"
             if tex.get("brush") else "") + ".", ""]
    if lay:
        mg = lay["margins"]
        L += ["## Layout (observed, medians)", "",
              f"Content covers {lay['density']:.0%} of the frame; margins L {mg['left']:.0%} R {mg['right']:.0%} "
              f"T {mg['top']:.0%} B {mg['bottom']:.0%} (smallest {lay['min_margin']:.0%}); centroid {lay['centroid']}; "
              f"symmetry {lay['symmetry']}; {lay['blocks']} blocks; dominant alignment {lay['dominant_alignment']}; "
              f"{lay['columns']} left-aligned columns.", ""]
    if typ.get("lines"):
        L += ["## Type (observed)", "",
              f"{typ['lines']} text lines. Title line height {typ['title_height']:.1%} of the frame, body {typ['body_height']:.1%} "
              f"(ratio {typ['title_to_body']}); stroke weight: titles {typ['weight_title']}, overall {typ['weight_overall']}. "
              "Size tiers: " + ", ".join(f"{t['height']:.1%} x{t['count']}" for t in typ["tiers"]) + ". "
              "Read the words, case and typeface class from `evidence/type-lines.jpg`.", ""]
    st = m.get("style")
    if st:
        ag = st["agreement"]
        L += ["## Style embedding (CSD)", "",
              f"{st['pictures']} pictures from {st['references']} references"
              + (f"; they agree with each other at {ag['min']}-{ag['median']} (lowest, median; cosine, leave one out)" if ag else "")
              + f". A style frame passes `frame-check` at a similarity of {st['floor']} or more to their centre.", ""]
    if "motion" in m:
        g = m["motion"]["grammar"]
        L += ["## Motion (measured; see each video's motion.json for every event)", ""]
        if "videos" not in g:
            L += _motion_lines(g)
        else:
            L.append(f"{len(g['videos'])} videos, kept apart: see `measure/motion.json`.")
        L.append("")
    for vid, rh in (m.get("rhythm") or {}).items():
        if rh.get("audio"):
            c, a = rh["cuts_on_beat"], rh["arrivals_on_beat"]
            L += [f"## Rhythm ({vid})", "",
                  f"{rh['bpm']} BPM (clarity {rh['clarity']}). Cuts on a beat: {_fmt(c['share'])} of {c['events']} "
                  f"(chance {_fmt(c['chance'])}); arrivals on a beat: {_fmt(a['share'])} of {a['events']} "
                  f"(chance {_fmt(a['chance'])}).", ""]
    return "\n".join(L)


def _motion_lines(g: dict) -> list[str]:
    out = []
    sh = g["shots"]
    out.append(f"Shots: {sh['count']}, median length {_fmt((sh['length_s'] or {}).get('median'))} s; "
               f"{sh['cuts']} cuts, {sh['dissolves']} dissolves, {sh.get('dips', 0)} dips. Motion density {g['motion_density']}; "
               f"median hold {_fmt((g['hold_s'] or {}).get('median'))} s.")
    for role in ("entrance", "exit", "move", "counters"):
        r = g.get(role)
        if not r:
            continue
        d = r["duration_s"] or {}
        eased = (f"classes read with confidence in {r.get('class_claimed', 0)} ({r['classes']}), families in "
                 f"{r.get('claimed', 0)}; overshoot in {r['overshoot_share']:.0%}"
                 + (f" (median {r['overshoot']['median']:.0%})" if r.get("overshoot") else "")
                 + (f"; one curve draws them: bezier{tuple(r['curve']['bezier'])} ({r['curve']['tweens']} tweens)"
                    if r.get("curve") else "")
                 if r.get("class_claimed") else "no ease read with confidence")
        name = {"entrance": "Entrances", "exit": "Exits", "move": "Moves", "counters": "Counters"}[role]
        out.append(f"{name} ({r['count']}): {_fmt(d.get('p25'))}–{_fmt(d.get('p75'))} s (median {_fmt(d.get('median'))}); "
                   f"vocabulary {r['vocabulary']}; {eased}"
                   + (f"; unconfirmed guesses {r['guesses']}" if r.get("guesses") else "") + ".")
    if g.get("counters"):
        c = g["counters"]
        out.append(f"Counters print as {c['formats']} and count " + ", ".join(f"{a:g}→{b:g}" for a, b in c["ranges"]) + ".")
    if g.get("loops"):
        L = g["loops"]
        amp = {"x": "sway {} px", "y": "bob {} px", "scale": "pulse ±{}", "opacity": "breathe to {} of full",
               "rot": "spin {} deg/s"}
        out.append(f"Loops ({L['count']}): periods {_fmt((L['period_s'] or {}).get('min'))}–{_fmt((L['period_s'] or {}).get('max'))} s "
                   f"(median {_fmt((L['period_s'] or {}).get('median'))}); "
                   + ", ".join(amp[k].format(_fmt(v["median"])) + f" ×{v['n']}" for k, v in L["props"].items()) + ".")
    for f in g.get("particles") or []:
        out.append(f"Particles: about {f['count']} in frame, radius {_fmt(f['radius_px'])} px, drifting "
                   f"{_fmt(f['speed']['p10'])}–{_fmt(f['speed']['p90'])} px/s toward {_fmt(f['direction_deg'])}° "
                   f"(0 = right, 90 = down; spread {_fmt(f['spread_deg'])}°).")
    if g.get("beat"):
        b = g["beat"]
        out.append(f"Beat grid: moves start and land, and shots cut, on a {_fmt(b['bpm'])} BPM grid"
                   + (f" (in {b['subdivision']}s of the beat)" if b["subdivision"] > 1 else "")
                   + f" counted from {_fmt(b['phase_s'])} s: {b['on_grid']} of {b['marks']} within a frame and a half "
                   f"(chance {b['chance']:.0%}; p {b['p_value']}). A timing rule for §5 and §6, whatever the sound.")
    for s in g.get("stagger", []):
        out.append(f"Stagger: {s['count']} × {s['interval_s']} s, {s['order']} ({s['vocabulary']}).")
    if g.get("stepping") and g["stepping"]["on"] > 1:
        out.append(f"Drawings held on {g['stepping']['on']}s.")
    cam = g.get("camera") or {}
    if cam.get("moves"):
        out.append("Camera: " + "; ".join(f"{k} ×{v['count']} {v['eases']}" for k, v in cam["moves"].items()) + ".")
    return out
