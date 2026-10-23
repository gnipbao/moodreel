"""moodreel <command>: the command line.

  moodreel motion <video> --out <dir>         measure a video's motion grammar
  moodreel bench make|render|motion [...]     build, render and score the motion test films
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
    subprocess.run(["node", str(RENDER), "video", str(page_dir), "--fps", str(fps), "--size", size,
                    "--workers", str(workers), "--out", str(out)], check=True)


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


def main(argv=None):
    ap = argparse.ArgumentParser(prog="moodreel")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("motion", help="measure a video's motion grammar")
    p.add_argument("video")
    p.add_argument("--out", required=True)
    p.add_argument("--width", type=int, default=640)
    p.set_defaults(fn=cmd_motion)
    b = sub.add_parser("bench", help="motion test films").add_subparsers(dest="bench", required=True)
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
    a = ap.parse_args(argv)
    a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
