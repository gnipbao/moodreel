"""`moodreel sync <video>`: the beat-sync fingerprint of a video. What the picture does on each kind of musical event.

A music video lands on its song because its moves are driven by the song's events: a cut on the beat before a line's
first word, a word slamming in as it is sung, the frame punching in on each kick and shaking on the snare. Reading those
recipes off the video, rather than guessing them from stills, gives the numbers a remake needs (`kit/music.js`: `hit`
half-lives, slam sizes, punch amounts):

  picture   per frame at the video's rate: cuts (the picture's edges change at once, or a flash), motion energy, the
            frame's zoom rate, shake (its position, high-passed) and flashes, from the optical flow of its own lines
  music     beats, bars, kick / snare / hat / vocal hits and the sung words, from `moodreel music`'s data (a
            music-data.js, pdoom-video's audio.json and lyrics.json) or analysed from the video's own sound
  locked    for each kind of musical event, the average picture response around it: how big, how long after it peaks
            (latency), how fast it decays (half-life), and how far above chance (z, against the same events shifted to
            random times)
  aligned   for cuts, surges, punches and flashes: the share that fall on each kind of musical event (within a frame),
            against chance, and the typical offset; for cuts, the lead before the first word of a line

Calibrated against pdoom-video, whose plates' own post settings (punch, shake, flash) were recorded frame by frame as
the ground truth (docs/research/VISION-TO-CODE.md): shake reads well (timing to a frame, size 0.94); a slam's settle
reads at about half its size; a global punch under about 1 % can't be told from the scene's own zooms.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import numpy as np

W, H = 640, 360           # flow needs this much: at 320 x 180 a shake of a few px and a slam's settle drown in noise
TO1920 = 1920 / W


def _fps(path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate", "-of",
                          "csv=p=0", str(path)], capture_output=True, text=True, check=True).stdout.strip()
    a, b = out.split("/") if "/" in out else (out, "1")
    return float(a) / float(b)


def picture(video, fps: float | None = None) -> dict:
    """Per frame: cuts, motion energy (px/s at 1920), zoom rate (% a frame), shake (px at 1920), flash (levels).

    Cuts: the edges of the picture change at once (an edge change ratio above 0.6, a local peak), or the light does (a
    flash cut: mean change over 25 levels). Shake: the median flow of the picture's lines, integrated within a shot and
    high-passed over 3 frames (a moving camera's path is slower than that). Calibrated on pdoom-video's own post shake:
    correlation 0.78 / 0.54 (x / y) where it shakes, size 0.94 of it."""
    import cv2
    fps = fps or _fps(video)
    proc = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(video), "-vf", f"fps={fps},scale={W}:{H}:flags=area",
                             "-pix_fmt", "gray", "-f", "rawvideo", "-"], stdout=subprocess.PIPE)
    n = W * H
    prev = prevE = None
    cols = {k: [] for k in ("ecr", "diff", "luma", "speed", "zr", "mx", "my")}
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    k5 = np.ones((5, 5), np.uint8)
    while True:
        buf = proc.stdout.read(n)
        if len(buf) < n:
            break
        g = np.frombuffer(buf, np.uint8).reshape(H, W)
        E = cv2.Canny(g, 40, 120) > 0
        cols["luma"].append(float(g.mean()))
        if prev is None:
            for k in ("ecr", "diff", "speed", "zr", "mx", "my"):
                cols[k].append(0.0)
            prev, prevE = g, E
            continue
        dA, dB = cv2.dilate(prevE.astype(np.uint8), k5) > 0, cv2.dilate(E.astype(np.uint8), k5) > 0
        lit = E.sum() + prevE.sum()
        cols["ecr"].append(float(max((E & ~dA).sum() / max(E.sum(), 1), (prevE & ~dB).sum() / max(prevE.sum(), 1))) if lit > 200 else 0.0)
        cols["diff"].append(float(np.abs(g.astype(np.int16) - prev).mean()))
        mag = np.hypot(cv2.Sobel(prev, cv2.CV_32F, 1, 0), cv2.Sobel(prev, cv2.CV_32F, 0, 1))
        mask = mag > 24
        sp = zr = mx = my = 0.0
        if mask.mean() > 0.002:
            f = cv2.calcOpticalFlowFarneback(prev, g, None, 0.5, 4, 21, 3, 5, 1.2, 0)
            idx = np.flatnonzero(mask.ravel())
            if len(idx) > 5000:
                idx = idx[np.linspace(0, len(idx) - 1, 5000).astype(int)]
            src = np.stack([xx.ravel()[idx], yy.ravel()[idx]], 1)
            fl = f.reshape(-1, 2)[idx]
            sp = float(np.linalg.norm(fl, axis=1).mean())
            M, _ = cv2.estimateAffinePartial2D(src, src + fl, method=cv2.RANSAC, ransacReprojThreshold=1.0)
            if M is not None:
                zr = float(np.log(np.hypot(M[0, 0], M[1, 0])))
            mx, my = float(np.median(fl[:, 0])), float(np.median(fl[:, 1]))
        for k, v in (("speed", sp), ("zr", zr), ("mx", mx), ("my", my)):
            cols[k].append(v)
        prev, prevE = g, E
    proc.wait()
    c = {k: np.array(v) for k, v in cols.items()}
    ecr, diff = c["ecr"], c["diff"]
    cut = ((ecr > 0.6) & (ecr >= np.roll(ecr, 1)) & (ecr >= np.roll(ecr, -1))) | \
          ((diff > 25) & (diff >= np.roll(diff, 1)) & (diff >= np.roll(diff, -1)))
    cut[0] = False
    seg = np.cumsum(cut)

    def integrate(v):
        out, acc = np.zeros(len(v)), 0.0
        for i in range(len(v)):
            acc = 0.0 if (i == 0 or cut[i]) else acc + v[i]
            out[i] = acc
        return out

    def highpass(v, frames):
        k = max(1, int(frames)) | 1
        out = np.zeros(len(v))
        for s_ in np.unique(seg):
            m = seg == s_
            x = np.asarray(v, float)[m]
            if len(x) > 2:
                out[m] = x - np.convolve(np.pad(x, k // 2, mode="edge"), np.ones(k) / k, mode="valid")[:len(x)]
        return out

    shake = np.hypot(highpass(integrate(c["mx"] * TO1920), 3), highpass(integrate(c["my"] * TO1920), 3))
    zr = np.where(cut, 0.0, c["zr"]) * 100
    flash = np.maximum(highpass(c["luma"], max(3, int(0.3 * fps))), 0)
    return {"fps": fps, "cuts": (np.flatnonzero(cut) / fps).tolist(), "energy": (c["speed"] * TO1920 * fps).tolist(),
            "zoom": zr.tolist(), "shake": shake.tolist(), "flash": flash.tolist()}


def load_music(source, video=None) -> dict:
    """Events: beats, downbeats, kick, snare, hat, vocal (with strengths), words (start times), lines (first words)."""
    if source is None:
        from . import music
        a = music.analyse(str(video))
        lyrics = []
    else:
        p = Path(source)
        if p.suffix == ".js":
            src = p.read_text()
            a = json.loads(re.search(r"export const AUDIO = (\{.*?\});\n", src, re.S).group(1))
            m = re.search(r"export const LYRICS = (\[.*?\]);\n", src, re.S)
            lyrics = json.loads(m.group(1)) if m else []
        else:
            a = json.loads(p.read_text())
            lp = p.with_name("lyrics.json")
            lyrics = json.loads(lp.read_text())["lines"] if lp.exists() else []
    ons = a.get("onsets", {})
    ev = {"beat": [[t, 1.0] for t in a.get("beats", [])], "downbeat": [[t, 1.0] for t in a.get("downbeats", [])]}
    for k in ("kick", "snare", "hat", "vocal"):
        if ons.get(k):
            ev[k] = [[float(t), float(s)] for t, s in ons[k]]
    if lyrics:
        ev["word"] = [[w["start"], 1.0] for ln in lyrics for w in ln["words"]]
        ev["line"] = [[ln["words"][0]["start"], 1.0] for ln in lyrics if ln["words"]]
    return {"bpm": a.get("bpm"), "events": ev}


def locked(signal, fps, events, pre=0.15, post=0.35, shuffles=40, seed=1) -> dict | None:
    """The average of a signal around events (weighted by strength), against the same events at random times."""
    x = np.asarray(signal, float)
    if len(events) < 6:
        return None
    lags = np.arange(-int(pre * fps), int(post * fps) + 1)
    def avg(times, w):
        idx = np.round(np.asarray(times) * fps).astype(int)
        ok = (idx + lags[0] >= 0) & (idx + lags[-1] < len(x))
        if ok.sum() < 4:
            return None
        rows = x[idx[ok][:, None] + lags[None, :]]
        r = np.average(rows, axis=0, weights=np.asarray(w)[ok])
        return r - r[lags < -int(0.04 * fps)].mean()
    t, w = np.array([e[0] for e in events]), np.array([e[1] for e in events])
    r = avg(t, w)
    if r is None:
        return None
    after = lags >= 0
    k = int(np.argmax(np.where(after, r, -np.inf)))
    peak = float(r[k])
    rng = np.random.default_rng(seed)
    dur = len(x) / fps
    null = []
    for _ in range(shuffles):
        rr = avg(np.sort(rng.uniform(pre, dur - post, len(t))), w)
        if rr is not None:
            null.append(float(np.max(rr[after])))
    z = (peak - np.mean(null)) / (np.std(null) + 1e-9) if null else 0.0
    half = None
    for j in range(k + 1, len(r)):
        if r[j] <= peak / 2:
            half = round(float((lags[j] - lags[k]) / fps), 3)
            break
    return {"peak": round(peak, 4), "latency_ms": round(float(lags[k] / fps * 1000), 0), "half_life": half, "z": round(float(z), 1),
            "n": int(len(t))}


def aligned(times, events, fps, tol_frames=1.0, shuffles=200, seed=2) -> dict | None:
    """The share of `times` within a frame of an event, against chance, and the median offset to the nearest event."""
    if len(times) < 3 or len(events) < 3:
        return None
    e = np.sort(np.array([x[0] for x in events]))
    t = np.asarray(times)
    def near(tt):
        i = np.clip(np.searchsorted(e, tt), 1, len(e) - 1)
        a, b = e[i - 1], e[i]
        return np.where(np.abs(tt - a) < np.abs(tt - b), tt - a, tt - b)
    d = near(t)
    tol = tol_frames / fps + 1e-3
    share = float((np.abs(d) <= tol).mean())
    rng = np.random.default_rng(seed)
    chance = float(np.mean([(np.abs(near(rng.uniform(e[0], e[-1], len(t)))) <= tol).mean() for _ in range(shuffles)]))
    return {"share": round(share, 2), "chance": round(chance, 2), "offset_ms": round(float(np.median(d[np.abs(d) < 0.25]) * 1000)
            if (np.abs(d) < 0.25).any() else 0.0, 0), "n": int(len(t))}


def _peaks(x, fps, q=97, gap=0.12):
    x = np.asarray(x, float)
    thr = np.percentile(x, q)
    out, last = [], -1e9
    for i in range(1, len(x) - 1):
        if x[i] >= thr and x[i] >= x[i - 1] and x[i] >= x[i + 1] and (i - last) / fps >= gap and x[i] > 0:
            out.append(i / fps)
            last = i
    return out


def settle(zoom_rate, fps, events, a=0.02, b=0.3, shuffles=40, seed=3) -> dict | None:
    """The frame's scale change from just after an event to `b` s after it (%): a slam settling (negative: it shrinks back
    from big), against random times. The first frame after a cut has no flow, so a slam that settles mostly within a
    frame (an exponential ease of 0.16 s) reads about half its size."""
    z = np.asarray(zoom_rate, float)
    def at(times):
        v = [z[int(round((t + a) * fps)):int(round((t + b) * fps))].sum() for t in times if (t + b) * fps < len(z)]
        return np.array(v)
    t = np.array([e[0] for e in events])
    if len(t) < 6:
        return None
    v = at(t)
    rng = np.random.default_rng(seed)
    null = [np.median(at(rng.uniform(1, len(z) / fps - 1, len(t)))) for _ in range(shuffles)]
    return {"median": round(float(np.median(v)), 2), "z": round(float((np.median(v) - np.mean(null)) / (np.std(null) + 1e-9)), 1),
            "n": int(len(v))}


def fingerprint(video, music_source=None) -> dict:
    pic = picture(video)
    mus = load_music(music_source, video)
    fps, ev = pic["fps"], mus["events"]
    sigs = {k: np.array(pic[k]) for k in ("energy", "zoom", "shake", "flash")}
    resp = {kind: {k: locked(v, fps, es) for k, v in sigs.items()} for kind, es in ev.items()}
    settles = {kind: settle(sigs["zoom"], fps, es) for kind, es in ev.items()}
    visual = {"cut": pic["cuts"], "surge": _peaks(np.diff(sigs["energy"], prepend=0), fps),
              "punch": _peaks(sigs["zoom"], fps), "flash": _peaks(sigs["flash"], fps)}
    align = {v: {k: aligned(ts, es, fps) for k, es in ev.items()} for v, ts in visual.items()}
    lead = None
    if "line" in ev and pic["cuts"]:
        firsts = np.array([e[0] for e in ev["line"]])
        lds = [float(nx[0] - c) for c in pic["cuts"] if len(nx := firsts[(firsts >= c - 0.05) & (firsts <= c + 0.6)])]
        if lds:
            beat = 60 / mus["bpm"] if mus.get("bpm") else 0.5
            lead = {"cuts_before_a_line": len(lds), "median_lead_ms": round(float(np.median(lds)) * 1000, 0),
                    "within_a_beat_before": round(float(np.mean([0 <= x <= beat + 0.02 for x in lds])), 2)}
    # what kit/music.js would take: the half-life of the hits that drive the picture, the shake they bring
    kick = resp.get("kick", {})
    sh = kick.get("shake") if kick else None
    en = kick.get("energy") if kick else None
    suggest = {"hit_half_life": en["half_life"] if en and en["z"] >= 3 else None,
               "shake_px": round(sh["peak"], 1) if sh and sh["z"] >= 3 else None,
               "shake_half_life": sh["half_life"] if sh and sh["z"] >= 3 else None}
    return {"video": str(video), "fps": fps, "bpm": mus.get("bpm"), "cuts": len(pic["cuts"]), "responses": resp,
            "settles": settles, "aligned": align, "cut_lead": lead, "kit_music": suggest,
            "signals": {k: [round(float(x), 4) for x in v] for k, v in sigs.items()}, "cut_times": [round(t, 3) for t in pic["cuts"]]}


UNITS = {"zoom": "% scale a frame", "shake": "px", "flash": "levels", "energy": "px/s"}


def _plural(v: str) -> str:
    return v + ("es" if v.endswith(("sh", "ch")) else "s")


def recipe(fp: dict) -> list[str]:
    """The fingerprint as a remake's recipe: the significant responses and alignments, strongest first."""
    out = []
    rows = []
    for kind, rs in fp["responses"].items():
        for sig, r in rs.items():
            if r and r["z"] >= 3 and r["peak"] > 0:
                rows.append((r["z"], f"{kind} -> {sig} +{r['peak']:g} {UNITS[sig]}, peaking {r['latency_ms']:+.0f} ms after it, "
                                     f"half-life {r['half_life']} s (z {r['z']}, {r['n']} events)"))
    out += [s for _, s in sorted(rows, reverse=True)]
    for v, al in fp["aligned"].items():
        best = sorted(((a["share"] - a["chance"], k, a) for k, a in al.items() if a), reverse=True)
        if best and best[0][0] >= 0.15:
            _, k, a = best[0]
            out.append(f"{_plural(v)} land on the {k}: {a['share']:.0%} within a frame (chance {a['chance']:.0%}), median offset "
                       f"{a['offset_ms']:+.0f} ms")
    for kind, st in (fp.get("settles") or {}).items():
        if st and st["z"] <= -3:
            out.append(f"after each {kind} the frame's scale settles {st['median']:+.1f}% over 0.3 s (z {st['z']}): a slam, bigger "
                       "than it reads (most of a fast slam settles in the first frame)")
    if fp.get("cut_lead"):
        c = fp["cut_lead"]
        out.append(f"a cut comes {c['median_lead_ms']:.0f} ms before a line's first word (median of {c['cuts_before_a_line']}); "
                   f"{c['within_a_beat_before']:.0%} within a beat before it")
    return out



def difference(ref: dict, ours: dict) -> dict:
    """A remake's fingerprint against its reference's: the responses one has and the other lacks, the ones of another
    size or timing, the alignments that differ, and an overall similarity (cosine of the two z-score profiles)."""
    rows, za, zb = [], [], []
    for kind in sorted(set(ref["responses"]) & set(ours["responses"])):
        for sig in UNITS:
            a, b = ref["responses"][kind].get(sig), ours["responses"][kind].get(sig)
            if not a or not b:
                continue
            za.append(max(0.0, min(15.0, a["z"])))
            zb.append(max(0.0, min(15.0, b["z"])))
            sa, sb = a["z"] >= 3 and a["peak"] > 0, b["z"] >= 3 and b["peak"] > 0
            what = f"{kind} -> {sig}"
            if sa and b["z"] < 2:
                rows.append((a["z"], "missing", f"{what}: the reference responds +{a['peak']:g} {UNITS[sig]} at {a['latency_ms']:+.0f} ms "
                                                f"(z {a['z']}); the remake doesn't (z {b['z']})"))
            elif sb and a["z"] < 2:
                rows.append((b["z"], "extra", f"{what}: the remake responds +{b['peak']:g} {UNITS[sig]} (z {b['z']}); the reference "
                                              f"doesn't (z {a['z']})"))
            elif sa and sb:
                r = b["peak"] / max(a["peak"], 1e-9)
                if not 0.6 <= r <= 1.6:
                    rows.append((min(a["z"], b["z"]), "size", f"{what}: {r:.2f}x the reference's size (+{b['peak']:g} vs "
                                                              f"+{a['peak']:g} {UNITS[sig]})"))
                if abs(b["latency_ms"] - a["latency_ms"]) >= 2 * 1000 / ref["fps"] + 1:
                    rows.append((min(a["z"], b["z"]), "timing", f"{what}: peaks at {b['latency_ms']:+.0f} ms, the reference at "
                                                                f"{a['latency_ms']:+.0f} ms"))
    for v in ref["aligned"]:
        for kind, a in ref["aligned"][v].items():
            b = ours["aligned"].get(v, {}).get(kind)
            if a and b and abs((a["share"] - a["chance"]) - (b["share"] - b["chance"])) >= 0.12:
                rows.append((5.0, "alignment", f"{_plural(v)} on the {kind}: {b['share']:.0%} within a frame "
                                               f"(chance {b['chance']:.0%}); the reference {a['share']:.0%} (chance {a['chance']:.0%})"))
    za, zb = np.array(za), np.array(zb)
    sim = float(za @ zb / (np.linalg.norm(za) * np.linalg.norm(zb) + 1e-9)) if len(za) else 0.0
    return {"similarity": round(sim, 3), "differences": [f"{k}: {t}" for _, k, t in sorted(rows, key=lambda r: -r[0])]}


def run(video, music_source=None, out=None) -> dict:
    fp = fingerprint(video, music_source)
    fp["recipe"] = recipe(fp)
    if out:
        Path(out).write_text(json.dumps(fp))
    return fp
