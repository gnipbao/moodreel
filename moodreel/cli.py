"""moodreel <command>: the command line.

  moodreel intake <project> <ref>... [--source own|web]   copy references in, normalised; check they share a style
  moodreel measure <project>                              palette, surface, layout, type, motion, rhythm
  moodreel frame-check <project> <still>...               does a style frame look like the references?
  moodreel csd setup | compare <picture or video>...       style embeddings: download once; style similarity
  moodreel kit <project>                                  the style's tokens.js and motion.js, with the shared kit
  moodreel scaffold <project>                             a first style frame drawn from the tokens (look/)
  moodreel motion-check <project> <video>                 does a rendered film move the way the references do?
  moodreel scene-check <project> <film or stills>...     the style's look, but scenes of its own (not the references')?
  moodreel pack <project> --slug S --name N               check a distilled style and add it to your library
  moodreel styles [query]                                 your styles and the built-in ones
  moodreel film new <name> --style S | check <dir> | deliver <dir> [--music f] [--variant V | --all-variants] [--engine E]
  moodreel score <film>                                   the film's score.json as out/score.wav and score.js (cue times)
  moodreel samples fetch|list                             the sampled instruments (CC0): download once; what is there
  moodreel voice <film>                                   narration.json voiced: out/voice.wav and voice.js (line times)
  moodreel export hyperframes|remotion <film> [--out d] [--variant v]  the film as a HyperFrames composition or Remotion project
  moodreel media add <film> <file> --name N --source S --license L [--start --end --crop --width --grade]
  moodreel media list|check <film>                        real footage, stills and data, with source and licence
  moodreel wall search <product> | record <dir> --pick 3,5 | make <dir>   a word-of-mouth wall of the product's real posts
  moodreel render video|still|texts <dir> [...]           the renderer (render/render.mjs), from anywhere
  moodreel motion <video> --out <dir>                     measure one video's motion grammar
  moodreel bench make|render|motion [...]                 build, render and score the motion test films
  moodreel sketch <project>                               the measured motion replayed with neutral shapes
  moodreel bench roundtrip [--only name]                  distil the example films back and compare with their code
  moodreel bench blind make|score                         packets for a blind distillation, and the judges' scores
  moodreel compare <reference> <remake> [--shots f]       a remake against its reference, window by window
                   [--against last.json] [--sheet f.jpg]  each window's change since the last pass; a contact sheet
                   [--motion window,window]               where those windows' pictures move, when and which way
  moodreel review <reference> <remake> --shots f --out d  the producer's and the motion designer's review: sheets, colours, snaps, spans
  moodreel probe <reference> --at t,t [--against remake]  a shot's numbers, the reference's beside the remake's
  moodreel camera <reference> [--against remake] [--js f] the camera, window by window: pan, push, roll; a track for kit/follow.js
  moodreel triage <compare.json> [--camera f] [--allow-text-upload]  opt-in Jev: what to fix first, and how
  moodreel pass <reference> <film> --shots f --name p [--jev] [--vision]  render, score, camera (and Jev) in one go
  moodreel look <reference> <remake> --shots f [--spec f] [--allow-image-upload]  opt-in Jev vision: frames compared
  moodreel track <video> --spec f [--every s] [--js f] [--allow-image-upload]  opt-in Jev vision: subjects on screen
  moodreel direct <reference> --shots f [--against remake] [--md f] [--allow-image-upload]  opt-in Jev: a director's reading
  moodreel model build|check|sheet <spec.py | mannequin | model.json>  an SDF character: built, checked, on a contact sheet
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
RENDER = REPO / "render" / "render.mjs"
BENCH = REPO / "bench" / "motion"
STRESS = "eq=contrast=0.85,noise=alls=14:allf=t+u,fps=25"


def render_video(page_dir: Path, out: Path, fps: float, size: str, workers: int = 3) -> None:
    subprocess.run(["node", str(RENDER), "video", str(page_dir), "--fps", str(fps), "--size", size,    # the bench: Chrome,
                    "--workers", str(workers), "--engine", "chrome", "--out", str(out)], check=True)   # bit for bit


def stress_copy(src: Path, dst: Path, w: int, h: int) -> None:
    """A degraded copy: 3/4 size, lower contrast, moving grain, 25 fps, crf 30."""
    sw, sh = (round(w * 0.75 / 2) * 2, round(h * 0.75 / 2) * 2)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(src), "-vf", f"scale={sw}:{sh}:flags=bicubic,{STRESS}",
                    "-c:v", "libx264", "-crf", "30", "-pix_fmt", "yuv420p", str(dst)], check=True)


def cmd_motion(a):
    from .motion.extract import measure
    r = measure(a.video, Path(a.out), a.width)
    print(f"{len(r['shots'])} shots, {len(r['events'])} element events, {r['seconds']}s -> {a.out}/motion.json")
    for ev in r["events"]:
        props = ", ".join(f"{k} {v['best']} {v['t0']:.2f}-{v['t1']:.2f}s" for k, v in ev["props"].items())
        print(f"  {ev['id']} shot{ev['shot']} {ev['kind']:9s} {ev['label']:22s} {props}")


def cmd_intake(a):
    from .intake import intake
    r = intake(Path(a.project), [Path(x) for x in a.refs], a.source)
    print(f"{len(r['refs'])} references -> {a.project}/refs; default size {r['default_size']}")
    if not r["unity"]["unified"]:
        print("the references split into palettes: " + " | ".join(", ".join(g) for g in r["unity"]["groups"]))
    print(f"sheet: {a.project}/evidence/refs-sheet.jpg")


def cmd_measure(a):
    from .measure.run import measure
    m = measure(Path(a.project))
    print(f"measured: {', '.join(m)} -> {a.project}/measure/*.json, {a.project}/MEASURE.md")


def cmd_frame_check(a):
    from .check.frame import check
    r = check(Path(a.project), [Path(x) for x in a.stills])
    for s in r["stills"]:
        print(f"{'PASS' if s['pass'] else 'FAIL'} {s['still']}: coverage {s['coverage']:.0%}, off-palette {s['off_palette']:.0%}, "
              f"lightness EMD {s['lightness_emd']}; surface " + ", ".join(f"{k} {'ok' if v['ok'] else 'off' if v['ok'] is False else '?'}"
                                                                         for k, v in s["surface"].items())
              + (f"; style {s['style']['similarity']} (floor {s['style']['floor']})" if s["style"].get("similarity") is not None
                 else f"; style ? ({s['style']['note']})") + f"; sheet {s['sheet']}")


def cmd_scene_check(a):
    from .check.scene import check
    r = check(Path(a.project), [Path(x) for x in a.inputs], a.step)
    if r["ok"] is None:
        print(r["note"])
        return 0
    for f in r["frames"]:
        if f["verdict"] in ("copies", "close"):
            where = f"{f['t']:6.1f} s" if f["t"] is not None else Path(f["input"]).name
            print(f"  {f['verdict']:6s} {where}: {f['similarity']} like the reference at {f['at']} s")
    n = len(r["frames"])
    n -= r["blank"]
    print(f"{'OK' if r['ok'] else 'NOT YET'}: {r['new']} of {n} frames new, {r['close']} close to a reference's composition, "
          f"{r['copies']} copying one ({r['blank']} too even to judge)" + (f"; sheet {r['sheet']}" if r.get("sheet") else ""))
    return 0 if r["ok"] else 1


def cmd_csd(a):
    from .measure import csd
    if a.action == "setup":
        print(f"style embeddings -> {csd.setup()}")
        return 0
    if len(a.files) < 2:
        raise SystemExit("csd compare <picture or video> <picture or video>...")
    import numpy as np

    from . import sheet
    from .intake import probe
    rows = []
    for f in a.files:                                    # a video: four frames away from its ends, averaged
        if Path(f).suffix.lower() in {".mp4", ".mov", ".webm", ".mkv", ".m4v", ".gif"}:
            d = probe(Path(f))["duration"]
            pics = sheet.video_frames(f, [d * (k + 0.5) / 4 for k in range(4)])
        else:
            from PIL import Image
            pics = [np.asarray(Image.open(f).convert("RGB"))]
        rows.append(csd._unit(csd.embed(pics).mean(0)))
    sims = np.stack(rows) @ np.stack(rows).T
    names = [Path(f).name[:18] for f in a.files]
    print(" " * 19 + " ".join(f"{n[:6]:>6s}" for n in names))
    for n, r in zip(names, sims):
        print(f"{n:18s} " + " ".join(f"{x:6.2f}" for x in r))
    return 0


def cmd_samples(a):
    from .score import samples
    if a.action == "fetch":
        print(json.dumps(samples.fetch(), indent=1))
        return 0
    m = samples.manifest()
    gone = {e["path"] for e in samples.missing()}
    for name, fs in m["instruments"].items():
        have = sum(e["path"] not in gone for e in fs)
        print(f"{name:13s} {have:3d}/{len(fs)} files, MIDI {fs[0]['midi']}-{fs[-1]['midi']}")
    print(samples.credit())
    return 0 if not gone else 1


def cmd_kit(a):
    from .pack.kit import write_kit
    print(f"kit -> {write_kit(Path(a.project))}")


def cmd_scaffold(a):
    from .pack.scaffold import scaffold
    look = scaffold(Path(a.project))
    print(f"style frame page -> {look}; render a still with:\n  moodreel render still {look} 2.5 --size "
          f"{json.loads((Path(a.project) / 'intake.json').read_text())['default_size']} --out {look}/stills")


def cmd_motion_check(a):
    from .check.motion import check
    r = check(Path(a.project), Path(a.video), a.reference)
    for c in r["claims"]:
        print(f"  {c['result']:7s} {c['id']:24s} {c['rule']:52s} reference {c['reference']} film {c['film']}")
    print(f"{'OK' if r['ok'] else 'NOT YET'}: {r['pass']} pass, {r['fail']} fail, {r['unknown']} unknown"
          + (f"; {r['advice']} on the film's own pace, as advice" if r.get("advice") else ""))


def cmd_pack(a):
    from .pack.pack import pack
    r = pack(Path(a.project), a.slug, a.name, a.name_zh, a.strict, a.build)
    for w in r["warnings"]:
        print(f"warning: {w}")
    for p in r["problems"]:
        print(f"problem: {p}")
    print(f"packed -> {r['path']}" if r["ok"] else "not packed")


def cmd_styles(a):
    from . import library
    rows = library.all_styles()
    if a.query:
        q = a.query.lower()
        rows = [s for s in rows if q in json.dumps(s, ensure_ascii=False).lower()]
    for s in rows:
        needs = ", ".join(s.get("needs") or []) or "-"
        phase = "ready" if s.get("phase") == "later" and set(s.get("needs") or []) <= library.CAPABLE else s.get("phase", "?")
        print(f"{s['origin']:7s} {phase:5s} {s['slug']:22s} {s.get('name', '')} · {s.get('name_zh', '')}  [{needs}]")
    print(f"{len(rows)} styles")


def cmd_export(a):
    from . import export
    fn = export.hyperframes if a.format == "hyperframes" else export.remotion
    print(json.dumps(fn(Path(a.film), Path(a.out) if a.out else None, a.variant), indent=1))


def cmd_voice(a):
    from . import voice
    print(json.dumps(voice.write(Path(a.film)), indent=1))


def cmd_media(a):
    from . import media
    if a.action == "add":
        if not a.file:
            raise SystemExit("media add <film> <file> --name N --source S --license L")
        crop = tuple(int(v) for v in a.crop.split(",")) if a.crop else None
        r = media.add(Path(a.film), Path(a.file), a.name or Path(a.file).stem, a.source or "", a.license or "",
                      a.start, a.end, crop, a.width, a.grade)
    elif a.action == "list":
        r = media._manifest(Path(a.film))
    else:
        r = media.check(Path(a.film))
    print(json.dumps(r, indent=1, ensure_ascii=False))
    return 0 if r.get("ok", True) else 1


def cmd_wall(a):
    from . import wall
    if a.action == "search":
        r = wall.search(a.target, Path(a.out) if a.out else None, a.platforms, a.max, a.lang)
    elif a.action == "record":
        if not a.pick:
            raise SystemExit("wall record <dir> --pick 3,5,8 (numbers from CANDIDATES.md)")
        r = wall.record(Path(a.target), [int(n) for n in a.pick.split(",")], a.seconds, a.lang, a.at)
    else:
        r = wall.make(Path(a.target), a.name, a.lead, a.duration, not a.no_render, a.replace)
    print(json.dumps(r, indent=1, ensure_ascii=False))


def cmd_music(a):
    from .measure import music
    lyrics = music.load_lyrics(a.lyrics) if a.lyrics else None
    if a.source.endswith(".json"):
        data = music.from_json(a.source, lyrics, a.offset)
    else:
        data = music.analyse(a.source, lyrics, grid=not a.no_grid)
    out = music.write_module(data, a.out, a.credit or "")
    words = f", {sum(len(x['words']) for x in lyrics)} words" if lyrics else ""
    print(f"{out}: {data['bpm']} BPM, {len(data['beats'])} beats, {len(data['downbeats'])} bars, "
          + ", ".join(f"{len(v)} {k}" for k, v in data["onsets"].items()) + words)


def cmd_compare(a):
    from .check import compare
    res = compare.run(a.reference, a.remake, a.shots, a.every, a.offset, a.json, a.against, a.sheet)
    print(compare.report(res))
    rows = {r["window"]: r for r in res["windows"]}
    for name in (a.motion.split(",") if a.motion else []):
        if name.strip() not in rows:
            raise SystemExit(f"compare: no window {name.strip()!r} (windows: {', '.join(rows)})")
        r = rows[name.strip()]
        print("\n" + compare.motion_report(r["window"], compare.motion(a.reference, a.remake, r["t0"], r["t1"], a.offset)))


def cmd_origin(a):
    from .check import origin
    out = a.out or str(Path(a.video).with_suffix("")) + "-origin"
    r = origin.run(a.video, a.shots, out)
    print(f"{len(r['shots'])} shots, {r['duration']} s: "
          + ", ".join(f"{k.replace('_', ' ')} {v:.0%}" for k, v in r["summary"].items() if v))
    for s in r["shots"]:
        c = s["cadence"]
        on = "" if c["subject_on"] != 2 else ", subject on twos" + (" under a camera on ones" if c["camera_on"] == 1 else "")
        print(f"  {s['t0']:7.2f}-{s['t1']:7.2f} {s['name'] or '':>14} {s['kind']:>9} -> {s['route']}{on}")
    print(f"report: {out}/ORIGIN.md (strips of every shot in {out}/strips)")


def cmd_diff(a):
    from .check import diff
    out = a.out or str(Path(a.remake).with_suffix("")) + "-diff"
    r = diff.run(a.reference, a.remake, a.shots, out)
    c = r["cuts"]
    late = sum(1 for m in c["matched"] if m["off"])
    off = r["audio"]["offset_ms"]
    print(f"cuts: {len(c['matched']) - late} on time, {late} late or early, {len(c['missed'])} missed, {len(c['extra'])} extra; "
          f"length {r['duration']['difference']:+.3f} s; sound {'-' if off is None else f'{off:+.0f} ms'}; "
          f"{len(r['blanks'])} black, flat or frozen stretches")
    print(f"the list: {out}/DIFF.md (the worst moments beside the reference: {out}/worst.jpg)")


def cmd_review(a):
    from .check import review
    if a.only != "motion":
        res = review.run(a.reference, a.remake, a.shots, a.out, a.per)
        print(f"review in {res['out']}: {len(res['flagged'])} of {len(res['windows'])} windows with a colour off; sheets "
              + ", ".join(Path(p).name for p in res["sheets"]))
        for f in res["flagged"][:8]:
            print(f"  {f['window']:>16} " + "; ".join(f"{k} {v['reference']} -> {v['remake']} (dE {v['dE']})" for k, v in f["off"].items()))
    if a.only != "stills":
        m = review.motion_run(a.reference, a.remake, a.shots, a.out)
        off = [r for r in m["snaps"] if r["verdict"]]
        print(f"motion in {m['out']}: {len(off)} of the reference's {len(m['snaps'])} snaps off, {len(m['extra'])} the "
              f"reference doesn't have, {len(m['spans'])} spans moving or changing unlike it; strips "
              + ", ".join(Path(p).name for p in m["strips"]))
        for r in off[:8]:
            print(f"  {r['t']:6.2f} {r['window']:>14}  {r['verdict']}")
        for s in m["spans"][:8]:
            print(f"  {s['t0']:6.1f}-{s['t1']:.1f} {s['window']:>14}  {', '.join(s['off'])}")


def cmd_camera(a):
    from .check import camera
    print(camera.report(camera.run(a.reference, a.shots, a.every, a.against, a.js, a.json, a.fov)))


def cmd_pass(a):
    from .check import remake_pass, triage
    try:
        r = remake_pass.run(a.reference, a.film, a.shots, a.name, a.out, a.music, a.against, not a.no_render,
                            not a.no_sheet, a.jev, a.allow_text_upload, a.model, a.key_file, a.vision, a.spec,
                            a.allow_image_upload, a.samples)
    except triage.TriageError as e:
        raise SystemExit(f"pass: {e}")
    print(remake_pass.report(r))


def cmd_look(a):
    from .check import look, triage
    try:
        res = look.run(a.reference, a.remake, a.shots, a.spec, a.samples, a.allow_image_upload, a.json, a.cache, a.model,
                       a.key_file, a.workers)
    except triage.TriageError as e:
        raise SystemExit(f"look: {e}")
    print(look.report(res, a.top))


def cmd_track(a):
    from .check import look, triage
    try:
        res = look.track(a.video, look.load_spec(a.spec), a.subjects.split(",") if a.subjects else None,
                         checks=a.checks.split(",") if a.checks else (), every=a.every,
                         start=a.start, end=a.end, allow=a.allow_image_upload,
                         cache=a.cache or Path(a.video).parent / "jev-cache", model=a.model, key_file=a.key_file,
                         workers=a.workers)
    except triage.TriageError as e:
        raise SystemExit(f"track: {e}")
    if res["status"] == "preview":
        print(f"Jev track not sent: {res['not_cached']} of {res['requests']} frames need a call. Read {res['preview']}; "
              "add --allow-image-upload to send them.")
        return
    if a.json:
        Path(a.json).write_text(json.dumps(res, indent=1))
    if a.js:
        look.write_js(res, a.js)
    for s, rows in res["subjects"].items():
        seen = [r for r in rows if r[1] >= 0.5]
        print(f"{s}: seen in {len(seen)} of {len(rows)} frames")
    for e in res["errors"]:
        print(f"failed: {e['t']} s: {e['error']}")


def cmd_direct(a):
    from .check import direct, triage
    try:
        res = direct.run(a.reference, a.shots, a.against, a.allow_image_upload, a.json, a.md, a.cache, a.model, a.key_file,
                         a.workers)
    except triage.TriageError as e:
        raise SystemExit(f"direct: {e}")
    print(direct.report(res))


def cmd_triage(a):
    from .check import triage
    try:
        res = triage.run(a.compare, a.camera, a.allow_text_upload, a.json, a.cache, a.model, a.key_file, a.workers)
    except triage.TriageError as e:
        raise SystemExit(f"triage: {e}")
    print(triage.report(res, a.top))


def cmd_probe(a):
    from .check import probe
    times = [float(x) for x in a.at.split(",")]
    region = [int(x) for x in a.region.split(",")] if a.region else None
    res = probe.run(a.reference, times, a.against, region, a.lit, a.sheet, a.json)
    print(probe.report(res))
    if a.sheet:
        print(f"sheet -> {a.sheet}")


def cmd_dossier(a):
    from .measure import shot
    shots = json.loads(Path(a.shots).read_text()) if a.shots else None
    res = shot.dossier(a.video, shots, a.out, a.every)
    print(shot.report(res) if not a.out else f"{a.out}/DOSSIER.md: {len(res['shots'])} shots")


def cmd_pose(a):
    from .measure import pose
    if a.grid:
        print(pose.grid(a.image, a.grid))
        return
    aspect = None if a.aspect == "solve" else float(a.aspect)
    fov = a.fov if a.fov != "shape" else "shape"
    fov = float(fov) if fov not in (None, "shape") else fov
    if a.track:
        if not a.points or a.at is None:
            raise SystemExit("--track needs --at (the frame the corners are read on) and --points")
        t0, t1 = (float(x) for x in a.track.split(","))
        res = pose.track(a.image, a.at, pose.parse_points(a.points), t0, t1, aspect or 1.0,
                         fov if fov is not None else 35.0, a.up or "wall")
        if a.module:
            Path(a.module).write_text(pose.camera_module(res))
        fr = res["frames"]
        print(f"{a.image}: {len(fr)} frames tracked ({res['covered']:.0%} of {t0}-{t1} s)"
              + (f", camera written to {a.module}" if a.module else ""))
        for r in fr[:: max(1, len(fr) // 8)]:
            print(f"  {r['t']:.3f} s: pitch {r['cam_pitch']}, yaw {r['cam_yaw']}, roll {r['cam_roll']}, position {r['position']}")
        return
    print(pose.report(pose.run(a.image, pose.parse_points(a.points) if a.points else None, aspect, fov, a.up)))


def cmd_sync(a):
    from .measure import sync
    fp = sync.run(a.video, a.music, a.json)
    print(f"{a.video}: {fp['cuts']} cuts at {fp['fps']:g} fps, {fp['bpm']} BPM")
    for line in fp["recipe"]:
        print(f"- {line}")
    if any(v is not None for v in fp["kit_music"].values()):
        print("kit/music.js: " + ", ".join(f"{k} {v}" for k, v in fp["kit_music"].items() if v is not None))
    if a.against:
        d = sync.difference(json.loads(Path(a.against).read_text()), fp)
        print(f"against {a.against}: similarity {d['similarity']}")
        for line in d["differences"]:
            print(f"- {line}")


def cmd_score(a):
    from .score.score import write
    print(json.dumps(write(Path(a.film)), indent=1))


def cmd_film(a):
    from .film import film
    if a.action == "new":
        print(f"film -> {film.new(a.target, a.style, Path(a.root), a.duration, a.size, a.fps)}")
    elif a.action == "variants":
        print(json.dumps(film.variants(Path(a.target)), indent=1, ensure_ascii=False))
    elif a.action == "check":
        r = film.check(Path(a.target), a.variant)
        rd = r.get("reading", {})
        print("reading: " + (rd["error"] if "error" in rd else f"{len(rd['too_short'])} lines too short"))
        for x in rd.get("too_short", []):
            print(f"  '{x['text']}' from {x['from']} s: shown {x['shown']} s, needs {x['needs']} s")
        if "black" in r:
            print(f"black frames: {r['black'] or 'none'}")
        if "frames" in r:
            print("frames: " + ", ".join("pass" if x["pass"] else "fail" for x in r["frames"]["stills"]))
        if "motion" in r:
            print(f"motion: {r['motion']['pass']} pass, {r['motion']['fail']} fail, {r['motion']['unknown']} unknown")
        if r.get("media", {}).get("items"):
            print(f"media: {r['media']['items']} pieces" + ("" if r["media"]["ok"] else f", provenance: {r['media']}"))
        if "cues" in r:
            c = r["cues"]
            print(f"cues: {c['hit']} of {c['cues']} hit" + (f", missed {c['missed']}" if c["missed"] else ""))
        print("OK" if r["ok"] else "NOT YET")
        return 0 if r["ok"] else 1
    else:
        names = list(film.variants(Path(a.target))) if a.all_variants else [a.variant]
        for v in names:
            r = film.deliver(Path(a.target), Path(a.music) if a.music else None, Path(a.out) if a.out else None, variant=v,
                             engine=a.engine)
            print(json.dumps(r, indent=1))


def _fixtures(a):
    root = Path(a.root)
    names = set(a.only.split(",")) if a.only else None
    return root, [d for d in sorted(root.iterdir()) if (d / "truth.json").exists() and (not names or d.name in names)]


def cmd_bench_make(a):
    from .bench.fixtures import write
    for d in write(Path(a.root), set(a.only.split(",")) if a.only else None):
        print(d)


def cmd_bench_render(a):
    _, dirs = _fixtures(a)
    for d in dirs:
        t = json.loads((d / "truth.json").read_text())
        render_video(d, d / "clean.mp4", t["fps"], f"{t['W']}x{t['H']}")
        stress_copy(d / "clean.mp4", d / "stress.mp4", t["W"], t["H"])


def cmd_bench_motion(a):
    from .bench.motion import report
    root, dirs = _fixtures(a)
    variants = ["clean", "stress"] if a.variant == "both" else [a.variant]
    md = report(dirs, variants, Path(a.out))
    (root / "REPORT.md").write_text(md, encoding="utf-8")
    print(md.split("\n\n## ")[0])
    print(f"\n-> {root / 'REPORT.md'}")


def cmd_sketch(a):
    from .pack.sketch import write_sketch
    out = write_sketch(Path(a.project), a.fps)
    print(f"sketch -> {out}  (render: moodreel render video {out} --fps {a.fps})")


def cmd_model(a):
    from .model3d import build, check, sheet
    if a.step == "build":
        spec = Path(a.spec)
        out = Path(a.out) if a.out else (spec.parent / "build" if spec.suffix == ".py" else Path("out") / "model" / a.spec)
        path = build.build_to(a.spec, out, log=print)
        print(f"model -> {path} and {path.with_suffix('.bin').name}")
    elif a.step == "check":
        text = json.dumps(check.run(a.spec, a.built), indent=1)
        if a.json:
            Path(a.json).parent.mkdir(parents=True, exist_ok=True)
            Path(a.json).write_text(text)
        print(text)
    else:
        info = sheet.run(a.spec, a.out, a.poses.split(",") if a.poses else None, a.views.split(",") if a.views else None)
        print(f"sheet -> {a.out} and {Path(a.out).parent / 'sheet.json'}: {len(info['cells'])} cells")


def cmd_bench_blind(a):
    from .bench import blind
    out = Path(a.out)
    if a.step == "make":
        key = blind.make(Path(a.roundtrip), out, set(a.only.split(",")) if a.only else None)
        print(f"{len(key)} packets -> {out}/<code>/packet (BRIEF.md for the director); JUDGE.md and KEY.json for the judge")
    md = blind.score(out, REPO / "bench" / "roundtrip" / "REPORT.md")
    (REPO / "bench" / "roundtrip" / "BLIND.md").write_text(md, encoding="utf-8")
    if a.step == "score":                               # each round kept apart: blind/round<N>/
        dest = REPO / "bench" / "roundtrip" / "blind" / f"round{a.round}"
        blind.keep(out, dest)
        (dest / "BLIND.md").write_text(md, encoding="utf-8")
    print(md)


def cmd_bench_roundtrip(a):
    from .bench.roundtrip import films, report
    md = report(films(Path(a.root), set(a.only.split(",")) if a.only else None), Path(a.out), a.workers)
    dst = REPO / "bench" / "roundtrip" / "REPORT.md"
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(md, encoding="utf-8")
    print(md.split("\n## ")[0])
    print(f"-> {dst}")


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv and argv[0] == "render":                   # straight through to the renderer, flags and all
        return subprocess.run(["node", str(RENDER), *argv[1:]]).returncode
    ap = argparse.ArgumentParser(prog="moodreel")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("intake", help="copy references into a project and check they share a style")
    p.add_argument("project")
    p.add_argument("refs", nargs="+")
    p.add_argument("--source", choices=["own", "web", "unknown"], default="unknown",
                   help="own work may keep a reference sheet in the style pack; web references stay local")
    p.set_defaults(fn=cmd_intake)
    p = sub.add_parser("measure", help="measure palette, surface, layout, type, motion and rhythm")
    p.add_argument("project")
    p.set_defaults(fn=cmd_measure)
    p = sub.add_parser("frame-check", help="score style frames against the references")
    p.add_argument("project")
    p.add_argument("stills", nargs="+")
    p.set_defaults(fn=cmd_frame_check)
    p = sub.add_parser("csd", help="style embeddings: setup (download once), compare pictures or videos")
    p.add_argument("action", choices=["setup", "compare"])
    p.add_argument("files", nargs="*")
    p.set_defaults(fn=cmd_csd)
    p = sub.add_parser("kit", help="write the style's kit from the measurements")
    p.add_argument("project")
    p.set_defaults(fn=cmd_kit)
    p = sub.add_parser("scaffold", help="write a first style frame page drawn from the tokens")
    p.add_argument("project")
    p.set_defaults(fn=cmd_scaffold)
    p = sub.add_parser("motion-check", help="compare a rendered film's motion with the references'")
    p.add_argument("project")
    p.add_argument("video")
    p.add_argument("--reference", help="with several reference videos, the one to compare with (vid01...)")
    p.set_defaults(fn=cmd_motion_check)
    p = sub.add_parser("scene-check", help="does a film or a still copy a reference's scene (its composition), or is it its own?")
    p.add_argument("project")
    p.add_argument("inputs", nargs="+", help="a rendered film, or stills")
    p.add_argument("--step", type=float, default=1.0, help="seconds between a film's sampled frames")
    p.set_defaults(fn=cmd_scene_check)
    p = sub.add_parser("pack", help="check a distilled style and add it to your library")
    p.add_argument("project")
    p.add_argument("--slug", required=True)
    p.add_argument("--name", required=True)
    p.add_argument("--name-zh")
    p.add_argument("--strict", action="store_true", help="untraced numbers in STYLE.md are errors")
    p.add_argument("--build", action="store_true", help="rebuild the demo from demo/build.sh to prove it builds")
    p.set_defaults(fn=cmd_pack)
    p = sub.add_parser("styles", help="list your styles and the built-in ones")
    p.add_argument("query", nargs="?")
    p.set_defaults(fn=cmd_styles)
    p = sub.add_parser("export", help="a film as a composition for another tool: hyperframes, remotion")
    p.add_argument("format", choices=["hyperframes", "remotion"])
    p.add_argument("film")
    p.add_argument("--out")
    p.add_argument("--variant")
    p.set_defaults(fn=cmd_export)
    p = sub.add_parser("voice", help="voice a film's narration.json: out/voice.wav and voice.js")
    p.add_argument("film")
    p.set_defaults(fn=cmd_voice)
    p = sub.add_parser("media", help="real footage, stills and data in a film, with source and licence")
    p.add_argument("action", choices=["add", "list", "check"])
    p.add_argument("film")
    p.add_argument("file", nargs="?")
    p.add_argument("--name")
    p.add_argument("--source", help="where it came from: a URL, an archive and its catalogue number, the person who made it")
    p.add_argument("--license", help="the terms it is used under: CC0, CC BY 4.0, public domain (and why), licensed from ...")
    p.add_argument("--start", type=float)
    p.add_argument("--end", type=float)
    p.add_argument("--crop", help="x,y,w,h in the source's pixels")
    p.add_argument("--width", type=int)
    p.add_argument("--grade", choices=["none", "mono"])
    p.set_defaults(fn=cmd_media)
    p = sub.add_parser("wall", help="a word-of-mouth wall (社媒口碑墙): search a product's real posts, record the ones "
                                    "picked, make the 4K film")
    p.add_argument("action", choices=["search", "record", "make"])
    p.add_argument("target", help="search: the product; record, make: the wall's folder")
    p.add_argument("--out", help="search: the wall's folder (default out/walls/<product>)")
    p.add_argument("--platforms", default="youtube,bilibili", help="search: platforms that need no login")
    p.add_argument("--max", type=int, default=24, help="search: posts per platform")
    p.add_argument("--pick", help="record: candidate numbers, in the order the wall shows them")
    p.add_argument("--seconds", type=float, default=6.5, help="record: how long each post is recorded")
    p.add_argument("--at", type=float, default=0.0, help="record: start each video this many seconds in (past an intro)")
    p.add_argument("--lang", default="en-US", help="search, record: the platforms' interface language")
    p.add_argument("--name", help="make: the product's name in the title (default: the search's)")
    p.add_argument("--lead", default="创作者都在聊", help="make: the title's words before the name")
    p.add_argument("--duration", type=float, default=5.5)
    p.add_argument("--no-render", action="store_true", help="make: build the film folder only")
    p.add_argument("--replace", action="store_true", help="make: keep an existing film as film.prev")
    p.set_defaults(fn=cmd_wall)
    p = sub.add_parser("music", help="a song as data for a film to follow (beats, bars, drum hits, envelopes, the "
                       "lyric's words as sung): music-data.js for kit/music.js")
    p.add_argument("source", help="the song (audio or video), or an analysis made elsewhere (pdoom-video's audio.json)")
    p.add_argument("--lyrics", help="word timings: pdoom-video's lyrics.json, lines with words, or a flat list of words")
    p.add_argument("--offset", type=float, default=0.0, help="shift an imported analysis and its lyrics by this many s")
    p.add_argument("--no-grid", action="store_true", help="keep drum hits off the 4/4 grid too (not pop or dance)")
    p.add_argument("--credit", help="where the data came from, written into the module's header")
    p.add_argument("--out", default="music-data.js")
    p.set_defaults(fn=cmd_music)
    p = sub.add_parser("compare", help="a remake against its reference, shot by shot: structure, detail, tone, "
                       "motion direction and speed, worst first")
    p.add_argument("reference")
    p.add_argument("remake")
    p.add_argument("--shots", help="windows as JSON [[t0, t1, name], ...] (default: the reference's own shots)")
    p.add_argument("--every", type=float, help="fixed windows of this many seconds instead")
    p.add_argument("--offset", type=float, default=0.0, help="remake time = reference time + offset")
    p.add_argument("--json", help="write the full result here")
    p.add_argument("--against", help="a previous pass's --json: each window's score change and the mean's")
    p.add_argument("--sheet", help="write the reference beside the remake at each window's middle, worst first (.jpg)")
    p.add_argument("--motion", help="windows by name, comma-separated: where their pictures move, when and which way "
                   "(speed every 0.2 s and each cell's mean flow, the reference's beside the remake's)")
    p.set_defaults(fn=cmd_compare)
    p = sub.add_parser("origin", help="how each shot was made, before anything is rebuilt: drawn (graphics), a 3D render, "
                       "footage (filmed or generated), one picture moved, or a hold; its cadence (camera and subject on ones, "
                       "twos or threes) and the route to rebuild it (canvas, three, 3D assets + three, footage)")
    p.add_argument("video")
    p.add_argument("--shots", help="windows as JSON [[t0, t1, name], ...] (default: the video's own cuts, to the frame)")
    p.add_argument("--out", help="a folder for origin.json, ORIGIN.md and strips/ (default: <video>-origin)")
    p.set_defaults(fn=cmd_origin)
    p = sub.add_parser("diff", help="a remake against its reference, frame by frame, as a list of what to fix: every cut "
                       "on time, late, early, missed or extra; the length; the sound's offset; black, flat or frozen "
                       "stretches; the worst moments beside the reference")
    p.add_argument("reference")
    p.add_argument("remake")
    p.add_argument("--shots", help="windows as JSON [[t0, t1, name], ...]: names each cut by its window")
    p.add_argument("--out", help="a folder for diff.json, DIFF.md and worst.jpg (default: <remake>-diff)")
    p.set_defaults(fn=cmd_diff)
    p = sub.add_parser("review", help="the review before a cut is shown: the producer's (every window at full size beside "
                       "the reference, its ground, ink and accent colours audited: review.md) and the motion designer's (the "
                       "reference's snaps met or missed, spans moving or changing unlike it, strips: motion.md)")
    p.add_argument("reference")
    p.add_argument("remake")
    p.add_argument("--shots", required=True, help="windows as JSON [[t0, t1, name], ...]")
    p.add_argument("--out", required=True, help="a folder for the sheets, review.json and review.md")
    p.add_argument("--per", type=int, default=8, help="windows per sheet")
    p.add_argument("--only", choices=("stills", "motion"), help="one half of the review: the producer's (stills: sheets "
                   "and colours) or the motion designer's (motion: the reference's snaps met or missed, spans moving or "
                   "changing unlike it, strips frame by frame); both by default")
    p.set_defaults(fn=cmd_review)
    p = sub.add_parser("camera", help="a film's camera read off its picture, window by window (pan, push, roll and the "
                       "turn they mean), a remake's beside it, and the track as camera-data.js for kit/follow.js")
    p.add_argument("reference")
    p.add_argument("--against", help="a remake: its camera beside the reference's, and what is off")
    p.add_argument("--shots", help="windows as JSON [[t0, t1, name], ...] (default: the reference's own shots)")
    p.add_argument("--every", type=float, help="fixed windows of this many seconds instead")
    p.add_argument("--js", help="write the reference's track here (camera-data.js)")
    p.add_argument("--json", help="write the full result here")
    p.add_argument("--fov", type=float, default=36.0, help="the remake's field of view, for the turn and tilt (deg)")
    p.set_defaults(fn=cmd_camera)
    p = sub.add_parser("pass", help="one pass of a remake: render, score every window in parallel, read the camera, and "
                       "with --jev rank what to fix first; all in <out>/<name>/")
    p.add_argument("reference")
    p.add_argument("film", help="the remake's film folder")
    p.add_argument("--shots", required=True, help="windows as JSON [[t0, t1, name], ...]")
    p.add_argument("--name", required=True, help="this pass's name (its folder)")
    p.add_argument("--out", help="where passes live (default: passes/ beside the film)")
    p.add_argument("--music", help="the soundtrack for the render")
    p.add_argument("--against", help="an earlier pass's folder: each window's change")
    p.add_argument("--no-render", action="store_true", help="score the film's last render as it is")
    p.add_argument("--no-sheet", action="store_true", help="skip the contact sheet")
    p.add_argument("--jev", action="store_true", help="opt-in: rank what to fix with Jev (needs --allow-text-upload to send)")
    p.add_argument("--allow-text-upload", action="store_true")
    p.add_argument("--vision", action="store_true", help="opt-in: Jev looks at frames of both films (moodreel look; "
                   "needs --allow-image-upload to send)")
    p.add_argument("--spec", help="what Jev looks for, and where (see moodreel look)")
    p.add_argument("--allow-image-upload", action="store_true")
    p.add_argument("--samples", type=int, default=3, help="moments per window Jev looks at")
    p.add_argument("--model")
    p.add_argument("--key-file")
    p.set_defaults(fn=cmd_pass)
    p = sub.add_parser("look", help="opt-in: Jev (TypeSafe) looks at frames of a reference and its remake, window by "
                       "window: where each subject sits, checks that disagree, how alike; worst first")
    p.add_argument("reference")
    p.add_argument("remake")
    p.add_argument("--shots", required=True, help="windows as JSON [[t0, t1, name], ...]")
    p.add_argument("--spec", help="subjects, checks and which windows ask what (JSON; default: the main subject)")
    p.add_argument("--samples", type=int, default=3, help="moments per window")
    p.add_argument("--allow-image-upload", action="store_true",
                   help="send the frames (JPEG, 1280 x 720) to TypeSafe/Jev; without it only the transfer preview is written")
    p.add_argument("--json", help="write the result here")
    p.add_argument("--cache", help="where answers are cached (default: jev-cache beside the remake)")
    p.add_argument("--model", default="jev-1.14.0")
    p.add_argument("--key-file", help="a private file with the key, when TYPESAFE_API_KEY is not set")
    p.add_argument("--workers", type=int, default=8)
    p.add_argument("--top", type=int, default=12, help="how many windows to list")
    p.set_defaults(fn=cmd_look)
    p = sub.add_parser("direct", help="opt-in: Jev reads each window as a director and a motion designer would - shot size, "
                       "angle, composition, light, where the eye goes, how the camera moves and eases, what the subject "
                       "does; --against a remake: where it reads differently")
    p.add_argument("reference")
    p.add_argument("--shots", required=True, help="windows as JSON [[t0, t1, name], ...]")
    p.add_argument("--against", help="a remake: the same questions, and the notes where it differs")
    p.add_argument("--allow-image-upload", action="store_true")
    p.add_argument("--json", help="write the reading here")
    p.add_argument("--md", help="write it as a director's notes (Markdown)")
    p.add_argument("--cache")
    p.add_argument("--model", default="jev-1.14.0")
    p.add_argument("--key-file")
    p.add_argument("--workers", type=int, default=8)
    p.set_defaults(fn=cmd_direct)
    p = sub.add_parser("track", help="opt-in: Jev finds each subject of the spec on screen, frame after frame, in one "
                       "film: [t, seen, cx, cy, w, h] (track.json, --js for a film to frame by)")
    p.add_argument("video")
    p.add_argument("--spec", help="the subjects (JSON, as for moodreel look)")
    p.add_argument("--subjects", help="only these, comma-separated")
    p.add_argument("--checks", help="checks of the spec to answer frame by frame too, comma-separated")
    p.add_argument("--every", type=float, default=0.25, help="seconds between frames")
    p.add_argument("--start", type=float, default=0.0)
    p.add_argument("--end", type=float)
    p.add_argument("--allow-image-upload", action="store_true")
    p.add_argument("--json", help="write the track here")
    p.add_argument("--js", help="write it as an ES module (export const TRACK)")
    p.add_argument("--cache")
    p.add_argument("--model", default="jev-1.14.0")
    p.add_argument("--key-file")
    p.add_argument("--workers", type=int, default=8)
    p.set_defaults(fn=cmd_track)
    p = sub.add_parser("triage", help="opt-in: Jev (TypeSafe) judges every window's measures at once and ranks what to "
                       "fix first and how (camera, framing, light, motion, detail); numbers only, never frames")
    p.add_argument("compare", help="a pass's `moodreel compare --json` result")
    p.add_argument("--camera", help="the same pass's `moodreel camera --json` result")
    p.add_argument("--allow-text-upload", action="store_true",
                   help="send the windows' measures to TypeSafe/Jev; without it only the transfer preview is written")
    p.add_argument("--json", help="write the ranked result here")
    p.add_argument("--cache", help="where answers are cached (default: next to the compare json)")
    p.add_argument("--model", default="jev-1.13.0")
    p.add_argument("--key-file", help="a private file with the key, when TYPESAFE_API_KEY is not set")
    p.add_argument("--workers", type=int, default=6)
    p.add_argument("--top", type=int, default=12, help="how many windows to list")
    p.set_defaults(fn=cmd_triage)
    p = sub.add_parser("probe", help="a shot's numbers off full-size frames (colour, lit share and box, detail, still "
                       "grain, cell grid, a bar's angle), the reference's beside a remake's")
    p.add_argument("reference")
    p.add_argument("--at", required=True, help="times in seconds, comma-separated")
    p.add_argument("--against", help="the remake: a video, or a film folder (rendered as stills)")
    p.add_argument("--region", help="x0,y0,x1,y1 in the reference's pixels (default: the whole frame)")
    p.add_argument("--lit", type=float, default=50, help="brightness (0-255) above which a pixel counts as lit")
    p.add_argument("--sheet", help="write the frames as a contact sheet, reference above remake")
    p.add_argument("--json", help="write the full result here")
    p.set_defaults(fn=cmd_probe)
    p = sub.add_parser("dossier", help="read each shot of a video as its code would be written: motion (pan, zoom, roll, "
                       "spin, parallax), linework, finish, colour, and what to build")
    p.add_argument("video")
    p.add_argument("--shots", help="windows as JSON [[t0, t1, name], ...] (default: the video's own cuts)")
    p.add_argument("--every", type=float, help="fixed windows of this many seconds instead")
    p.add_argument("--out", help="a folder for DOSSIER.md, dossier.json and each shot's keyframes and flow arrows")
    p.set_defaults(fn=cmd_dossier)
    p = sub.add_parser("pose", help="the 3D camera from a rectangle in a frame (pitch, yaw, roll, distance, field of view), "
                       "or tracked through a shot")
    p.add_argument("image", help="a frame, or a video with --track")
    p.add_argument("--points", help="the rectangle's corners in order round it: x1,y1,x2,y2,x3,y3,x4,y4 (default: found)")
    p.add_argument("--aspect", default="1", help="the rectangle's width per unit height, or 'solve'")
    p.add_argument("--fov", help="the vertical field of view in degrees, when known (a film keeps its lens); 'shape' to solve it "
                   "from the rectangle's aspect, frame by frame (a zoom)")
    p.add_argument("--up", choices=["wall", "floor"], help="which way the rectangle stands: the camera is also given in its world, "
                   "Y up (a stack's direction in the rectangle's own plane: a wall)")
    p.add_argument("--track", help="t0,t1: follow the rectangle through this stretch of a video and solve the camera every frame")
    p.add_argument("--at", type=float, help="with --track: the time the corners were read at")
    p.add_argument("--module", help="with --track: write the camera as a JS module (cameraAt(t)) here")
    p.add_argument("--grid", help="instead: write the frame with a labelled coordinate grid here, to read corners off it")
    p.set_defaults(fn=cmd_pose)
    p = sub.add_parser("sync", help="the beat-sync fingerprint: what the picture does on each kind of musical event (cuts, "
                       "surges, shake, slams on beats, kicks, snares and sung words)")
    p.add_argument("video")
    p.add_argument("--music", help="the song's data: a music-data.js (moodreel music) or pdoom-video's audio.json (with "
                   "lyrics.json beside it); default: analyse the video's own sound")
    p.add_argument("--json", help="write the whole fingerprint here (signals included)")
    p.add_argument("--against", help="a reference's fingerprint (--json of an earlier run): what this video does differently")
    p.set_defaults(fn=cmd_sync)
    p = sub.add_parser("score", help="render a film's score.json: out/score.wav and score.js")
    p.add_argument("film")
    p.set_defaults(fn=cmd_score)
    p = sub.add_parser("samples", help="the sampled instruments: fetch (download once, CC0), list")
    p.add_argument("action", choices=["fetch", "list"])
    p.set_defaults(fn=cmd_samples)
    p = sub.add_parser("film", help="make a film in a style: new, check, deliver")
    p.add_argument("action", choices=["new", "check", "deliver", "variants"])
    p.add_argument("target", help="the film's name (new) or folder (check, deliver)")
    p.add_argument("--style", help="new: the style's slug or name")
    p.add_argument("--root", default="films", help="new: where films live")
    p.add_argument("--duration", type=float, default=15.0)
    p.add_argument("--size")
    p.add_argument("--fps", type=int, help="new: frames a second (default: the style's, else 30)")
    p.add_argument("--music", help="deliver: a music track, normalised to -14 LUFS")
    p.add_argument("--out", help="deliver: where the finished film and poster go")
    p.add_argument("--variant", help="check, deliver: one of film.json's variants (window.VARIANT for the page)")
    p.add_argument("--all-variants", action="store_true", help="deliver: every variant, <name>-<variant>.mp4 each")
    p.add_argument("--engine", choices=["auto", "framevelo", "chrome"],
                   help="deliver: FrameVelo (fast, the GPU's hardware encoder) or Chrome (bit for bit); "
                        "auto takes FrameVelo when installed")
    p.set_defaults(fn=cmd_film)
    sub.add_parser("render", help="the renderer: video|still|texts <dir> [--fps] [--size] [--workers] [--out]")
    p = sub.add_parser("sketch", help="replay the measured motion grammar with neutral shapes, as a film")
    p.add_argument("project")
    p.add_argument("--fps", type=int, default=24)
    p.set_defaults(fn=cmd_sketch)
    p = sub.add_parser("motion", help="measure a video's motion grammar")
    p.add_argument("video")
    p.add_argument("--out", required=True)
    p.add_argument("--width", type=int, default=640)
    p.set_defaults(fn=cmd_motion)
    m = sub.add_parser("model", help="a character modelled as signed distance fields: build it (json + bin for "
                       "kit/figure.js), check it (closed parts, floating parts, penetration per pose), see it (a contact "
                       "sheet)").add_subparsers(dest="step", required=True)
    q = m.add_parser("build", help="mesh and rig a spec: <NAME>.json and <NAME>.bin")
    q.add_argument("spec", help="a spec .py (NAME, BONES, PARTS, POSES, COLLIDE, ...) or a built-in: mannequin")
    q.add_argument("--out", help="the folder to write to (default: build/ beside the spec; out/model/<name> for a built-in)")
    q.set_defaults(fn=cmd_model)
    q = m.add_parser("check", help="print JSON: closed parts, floating parts (2 mm contact), penetration in every pose")
    q.add_argument("spec", help="a spec .py or a built-in: mannequin")
    q.add_argument("--model", dest="built", help="the spec's model already built (its .json): skip building it again")
    q.add_argument("--json", help="also write the report here")
    q.set_defaults(fn=cmd_model)
    q = m.add_parser("sheet", help="a contact sheet in headless Chrome: views across, poses down, labelled; sheet.json beside it")
    q.add_argument("spec", help="a built model's .json, a spec .py or a built-in: mannequin")
    q.add_argument("--out", required=True, help="the sheet (.png); sheet.json is written beside it")
    q.add_argument("--poses", help="comma-separated pose names (default: all of them; 'rest' is the unposed figure)")
    q.add_argument("--views", help="comma-separated: front,three-quarter,side,back (the default)")
    q.set_defaults(fn=cmd_model)
    b = sub.add_parser("bench", help="motion test films and the round trip").add_subparsers(dest="bench", required=True)
    for name, fn, hlp in (("make", cmd_bench_make, "write the test pages and their truth"),
                          ("render", cmd_bench_render, "render clean and stress videos"),
                          ("motion", cmd_bench_motion, "measure every test film and score it")):
        q = b.add_parser(name, help=hlp)
        q.add_argument("--root", default=str(BENCH))
        q.add_argument("--only", help="comma-separated fixture names")
        if name == "motion":
            q.add_argument("--variant", choices=["clean", "stress", "both"], default="both")
            q.add_argument("--out", default=str(REPO / "out" / "bench"))
        q.set_defaults(fn=fn)
    q = b.add_parser("roundtrip", help="distil the example films back and compare with their code")
    q.add_argument("--root", default=str(REPO / "examples"))
    q.add_argument("--only", help="comma-separated film names")
    q.add_argument("--out", default=str(REPO / "out" / "roundtrip"))
    q.add_argument("--workers", type=int, default=3)
    q.set_defaults(fn=cmd_bench_roundtrip)
    q = b.add_parser("blind", help="packets for a blind distillation of the example films, and the judges' scores")
    q.add_argument("step", choices=["make", "score"])
    q.add_argument("--round", default="1", help="which blind round the verdicts are (kept in bench/roundtrip/blind/round<N>)")
    q.add_argument("--roundtrip", default=str(REPO / "out" / "roundtrip"))
    q.add_argument("--out", default=str(REPO / "out" / "blind"))
    q.add_argument("--only", help="comma-separated film names")
    q.set_defaults(fn=cmd_bench_blind)
    a = ap.parse_args(argv)
    r = a.fn(a)
    return r if isinstance(r, int) else None                # a command's exit status, when it gives one


if __name__ == "__main__":
    sys.exit(main())
