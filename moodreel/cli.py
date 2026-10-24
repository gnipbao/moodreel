"""moodreel <command>: the command line.

  moodreel intake <project> <ref>... [--source own|web]   copy references in, normalised; check they share a style
  moodreel measure <project>                              palette, surface, layout, type, motion, rhythm
  moodreel frame-check <project> <still>...               does a style frame look like the references?
  moodreel csd setup | compare <picture or video>...       style embeddings: download once; style similarity
  moodreel kit <project>                                  the style's tokens.js and motion.js, with the shared kit
  moodreel scaffold <project>                             a first style frame drawn from the tokens (look/)
  moodreel motion-check <project> <video>                 does a rendered film move the way the references do?
  moodreel pack <project> --slug S --name N               check a distilled style and add it to your library
  moodreel styles [query]                                 your styles and the built-in ones
  moodreel film new <name> --style S | check <dir> | deliver <dir> [--music f] [--variant V | --all-variants] [--engine E]
  moodreel score <film>                                   the film's score.json as out/score.wav and score.js (cue times)
  moodreel samples fetch|list                             the sampled instruments (CC0): download once; what is there
  moodreel voice <film>                                   narration.json voiced: out/voice.wav and voice.js (line times)
  moodreel export hyperframes|remotion <film> [--out d] [--variant v]  the film as a HyperFrames composition or Remotion project
  moodreel media add <film> <file> --name N --source S --license L [--start --end --crop --width --grade]
  moodreel media list|check <film>                        real footage, stills and data, with source and licence
  moodreel render video|still|texts <dir> [...]           the renderer (render/render.mjs), from anywhere
  moodreel motion <video> --out <dir>                     measure one video's motion grammar
  moodreel bench make|render|motion [...]                 build, render and score the motion test films
  moodreel sketch <project>                               the measured motion replayed with neutral shapes
  moodreel bench roundtrip [--only name]                  distil the example films back and compare with their code
  moodreel bench blind make|score                         packets for a blind distillation, and the judges' scores
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
    print(f"{'OK' if r['ok'] else 'NOT YET'}: {r['pass']} pass, {r['fail']} fail, {r['unknown']} unknown")


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
    p.add_argument("--fps", type=int, default=30)
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
