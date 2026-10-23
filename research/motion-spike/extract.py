"""Measure the motion grammar of a reference video.

  .venv/bin/python research/motion-spike/extract.py <video> --out <dir> [--width 640]

Writes <dir>/motion.json (shots, transitions, per-element events, grammar) and <dir>/evidence/*.jpg
(each motion run with its tracked elements boxed, for the director to look at).
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from motionx import fit, profile, shots, track, video  # noqa: E402


def evidence(clip, run_tracks, path, cols=6):
    p, q = run_tracks[0]["p"], run_tracks[0]["q"]
    idx = np.unique(np.linspace(p, q, cols).round().astype(int))
    tiles = []
    for f in idx:
        im = cv2.cvtColor(clip.frames[f], cv2.COLOR_RGB2BGR).copy()
        for k, tr in enumerate(run_tracks):
            r = tr["readings"].get(int(f))
            if not r or not r["ok"]:
                continue
            bw, bh = tr["box"][2] / clip.scale * r["s"], tr["box"][3] / clip.scale * r["s"]
            x0, y0 = int(r["cx"] - bw / 2), int(r["cy"] - bh / 2)
            cv2.rectangle(im, (x0, y0), (int(x0 + bw), int(y0 + bh)), (0, 255, 0), 1)
            cv2.putText(im, f"{tr['id']} a={r['a']:.2f}", (x0, max(10, y0 - 3)), cv2.FONT_HERSHEY_SIMPLEX, 0.35,
                        (0, 255, 0), 1)
        cv2.putText(im, f"t={f / clip.fps:.2f}s", (6, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        tiles.append(cv2.resize(im, (320, int(320 * im.shape[0] / im.shape[1]))))
    cv2.imwrite(str(path), np.hstack(tiles), [cv2.IMWRITE_JPEG_QUALITY, 85])


def clean(o):
    if isinstance(o, dict):
        return {k: clean(v) for k, v in o.items() if k not in ("readings", "mask")}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    if isinstance(o, (np.floating, np.integer)):
        return o.item()
    return o


def run(path, out: Path, width=640):
    t_start = time.time()
    out.mkdir(parents=True, exist_ok=True)
    (out / "evidence").mkdir(exist_ok=True)
    clip = video.load(path, width)
    shots_, transitions, e, _th = shots.shots(clip)
    for tr in transitions:
        if tr["type"] == "dissolve":
            t = np.arange(tr["a"], tr["b"] + 1) / clip.fps
            f = fit.fit_move(t, np.array(tr["alpha"]), clip.fps)
            tr["ease"] = f and (f["ease"] if f["ease"] != "unknown" else f["best"])
            tr["fit"] = f
            tr.pop("alpha")
    events, runs_by_shot, n_el = [], {}, 0
    for sh in shots_:
        runs, thr = shots.motion_runs(e, sh, clip.fps)
        runs_by_shot[sh["id"]] = runs
        sh["runs_t"] = [[round(a / clip.fps, 3), round(b / clip.fps, 3)] for a, b in runs]
        for k, run_ in enumerate(runs):
            nxt = runs[k + 1][0] if k + 1 < len(runs) else None
            prev = runs[k - 1][1] if k > 0 else None
            tracks = track.track_run(clip, sh, run_, nxt, prev)
            run_events = []
            for tr in tracks:
                tr["id"] = f"e{n_el}"
                n_el += 1
                ev = profile.element_events(clip, tr)
                ev["id"] = tr["id"]
                run_events.append(ev)
            for ev in profile.merge_groups(run_events, clip.fps):
                ev["label"] = profile.label(ev, (clip.src_w, clip.src_h))
                events.append(ev)
            if tracks:
                evidence(clip, tracks, out / "evidence" / f"shot{sh['id']}_run{k}.jpg")
    result = {"source": {"path": str(path), "fps": clip.fps, "w": clip.src_w, "h": clip.src_h,
                         "frames": clip.n, "analysis_width": clip.w},
              "shots": shots_, "transitions": transitions, "events": events,
              "grammar": profile.grammar(clip, shots_, transitions, runs_by_shot, events),
              "seconds": round(time.time() - t_start, 1)}
    (out / "motion.json").write_text(json.dumps(clean(result), indent=1, ensure_ascii=False))
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--out", required=True)
    ap.add_argument("--width", type=int, default=640)
    a = ap.parse_args()
    r = run(a.video, Path(a.out), a.width)
    print(f"{len(r['shots'])} shots, {len(r['events'])} element events, {r['seconds']}s -> {a.out}/motion.json")
    for ev in r["events"]:
        props = ", ".join(f"{k} {v['best']} {v['t0']:.2f}-{v['t1']:.2f}s gap={v['bic_gap']}"
                          for k, v in ev["props"].items())
        print(f"  {ev['id']} shot{ev['shot']} {ev['kind']:9s} {ev['label']:18s} {props}")


if __name__ == "__main__":
    main()
