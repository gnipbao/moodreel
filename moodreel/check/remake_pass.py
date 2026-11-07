"""`moodreel pass <reference> <film> --shots scenes.json --name p20`: one pass of a remake in one command.

A pass used to be five commands and a few minutes of waiting between them: render, compare (90 s, one window after
another), camera, a contact sheet, then reading it all. This renders the film, scores every window in parallel
(about 15 s for 36 windows), reads the camera, lists frame by frame what a viewer notices (`diff`: cuts late, early,
missed or extra, the length, the sound's offset, black, flat or frozen stretches, the worst moments), and with --jev
asks Jev to rank what to fix first (a few seconds; opt-in, numbers only, --allow-text-upload to send), and with
--vision has Jev look at frames of both films (moodreel look; opt-in, --allow-image-upload to send). Everything lands
in <out>/<name>/: compare.json, camera.json, pairs.jpg, diff.json, DIFF.md, worst.jpg, triage.json, look.json;
--against <an earlier pass's folder> adds each window's change. --no-render re-scores the film as it is.
"""
from __future__ import annotations

import json
import time
from pathlib import Path


def run(reference, film, shots, name, out=None, music=None, against=None, render=True, sheet=True,
        jev=False, allow=False, model=None, key_file=None, vision=False, spec=None, allow_images=False, samples=3) -> dict:
    from . import camera, compare, diff, look, triage
    film = Path(film)
    out = Path(out or film.parent / "passes") / name
    out.mkdir(parents=True, exist_ok=True)
    clock, steps = time.time(), {}

    def lap(k):
        nonlocal clock
        steps[k] = round(time.time() - clock, 1)
        clock = time.time()

    if render:
        from ..film.film import deliver
        video = Path(deliver(film, Path(music) if music else None)["video"])
        lap("render")
    else:
        f = json.loads((film / "film.json").read_text())
        video = film / f"{f['name']}.mp4"
    prev = Path(against) / "compare.json" if against else None
    res = compare.run(reference, video, shots, out=out / "compare.json", prev=prev if prev and prev.exists() else None,
                      pairs=out / "pairs.jpg" if sheet else None)
    lap("compare")
    cam = camera.run(reference, shots, against=video, out=out / "camera.json")
    lap("camera")
    frames = diff.run(reference, video, shots, out=out)
    lap("diff")
    tri = None
    if jev:
        tri = triage.run(out / "compare.json", out / "camera.json", allow=allow, out=out / "triage.json",
                         cache=out.parent / "jev-cache", model=model or triage.MODEL, key_file=key_file)
        lap("triage")
    seen = None
    if vision:
        seen = look.run(reference, video, shots, spec, samples, allow_images, out / "look.json", out.parent / "jev-cache",
                        key_file=key_file)
        lap("look")
    return {"folder": str(out), "video": str(video), "steps": steps, "compare": res, "camera": cam, "diff": frames,
            "triage": tri, "look": seen}


def report(r: dict) -> str:
    from . import look, triage
    import numpy as np
    c = r["compare"]
    mean = round(float(np.mean([w["score"] for w in c["windows"]])), 3)
    change = f" ({c['mean']['before']} before)" if c.get("mean") else ""
    lines = [f"pass in {r['folder']}: " + ", ".join(f"{k} {v} s" for k, v in r["steps"].items()),
             f"score: mean {mean}{change}, median {c['median']['score']}; worst: " + ", ".join(c["worst"])]
    off = [w for w in r["camera"]["windows"] if w.get("off")]
    lines.append(f"camera: {len(r['camera']['windows']) - len(off)} of {len(r['camera']['windows'])} windows move as "
                 "the reference's; off: " + "; ".join(f"{w['window']} ({', '.join(w['off'])})" for w in off[:6]))
    d = r.get("diff")
    if d:
        c = d["cuts"]
        off = d["audio"]["offset_ms"]
        lines.append(f"frame by frame: {len(c['matched']) - sum(1 for m in c['matched'] if m['off'])} cuts on time, "
                     f"{sum(1 for m in c['matched'] if m['off'])} late or early, {len(c['missed'])} missed, {len(c['extra'])} extra; "
                     f"length {d['duration']['difference']:+.3f} s; sound {'-' if off is None else f'{off:+.0f} ms'}; "
                     f"{len(d['blanks'])} black, flat or frozen stretches (DIFF.md, worst.jpg)")
    if r["triage"]:
        lines.append(triage.report(r["triage"], top=8))
    if r.get("look"):
        lines.append(look.report(r["look"], top=10))
    lines.append(f"contact sheet: {r['folder']}/pairs.jpg")
    return "\n".join(lines)
