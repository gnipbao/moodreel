"""`moodreel review <reference> <remake> --shots scenes.json --out <dir>`: a producer's review before a cut is shown.

The scores say how close a remake is; they don't say what a viewer sees first: the paper a shade too grey, the orange
too dull, a creature facing the wrong way. A review looks at every window at full size, side by side, and audits the
colours that carry the picture, so the faults are listed before anything is fixed:

  sheets   for every window, the reference beside the remake at 40 % and at 80 % of it, 480 px each (review-N.jpg)
  palette  per window, at three moments, the ground (the most common colour), the ink (the 4 % farthest from the ground
           in lightness) and the accent (the 3 % most saturated, when there is one), the reference's beside the
           remake's, with the colour difference (CIE76 dE): above 6 a viewer sees it, above 12 it is another colour

and writes review.md: the windows whose ground, ink or accent are off, worst first, with the sheets to read beside it.
The fault list is the reviewer's to finish: what is missing, what faces or moves the wrong way, what a shot is for.

Stills don't show how a thing arrives. The motion designer reviews beside the producer (motion.md, motion-N.jpg):

  snaps    every moment the reference's picture changes at once (a cut, a slam, a shatter, a flash: a frame changing
           4 levels or more and 4 times the drift round it), and how the remake meets it: on time, late or early,
           weaker, eased (the same change spread over a fade), or missing; and the remake's snaps the reference lacks
  spans    every 0.6 s, the picture's speed (optical flow) and its change in place (a reshuffle, a reveal), the
           remake's against the reference's: still or slow where the reference moves, fast where it holds
  strips   each flagged moment frame by frame, the reference over the remake: a snap from 0.2 s before to 0.4 s after,
           a span at eight moments across it

What the numbers can't see is still the reviewer's: a figure's gait, what a move is for, the curve of a push.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import numpy as np

SEEN, OTHER = 6.0, 12.0


def _frame(path, t: float, w: int, h: int) -> np.ndarray:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{max(0.0, t):.3f}", "-i", str(path), "-frames:v", "1",
                          "-vf", f"scale={w}:{h}:flags=area", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw[: w * h * 3], np.uint8).reshape(h, w, 3)


def lab(rgb) -> np.ndarray:
    c = np.asarray(rgb, float) / 255
    c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    x = c @ np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722], [0.0193, 0.1192, 0.9505]]).T / [0.9505, 1, 1.089]
    f = np.where(x > 0.008856, np.cbrt(x), 7.787 * x + 16 / 116)
    return np.array([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])]).T


def de(a, b) -> float | None:
    return None if a is None or b is None else round(float(np.linalg.norm(lab(a) - lab(b))), 1)


def parts(px: np.ndarray):
    """A frame's (N x 3) ground, ink and accent colours."""
    q = (px // 24).astype(int)
    key = q[:, 0] * 10000 + q[:, 1] * 100 + q[:, 2]
    vals, cnt = np.unique(key, return_counts=True)
    ground = px[key == vals[cnt.argmax()]].mean(0)
    luma = px @ [0.2126, 0.7152, 0.0722]
    far = np.abs(luma - ground @ [0.2126, 0.7152, 0.0722])
    ink = px[far >= np.percentile(far, 96)].mean(0)
    sat = px.max(1) - px.min(1)
    accent = px[sat >= np.percentile(sat, 97)].mean(0) if sat.max() > 40 else None
    return ground, ink, accent


def palette(reference, remake, shots, at=(0.3, 0.55, 0.8)) -> list[dict]:
    rows = []
    for t0, t1, name in shots:
        got = {"reference": [], "remake": []}
        for f in at:
            t = t0 + (t1 - t0) * f
            for key, path in (("reference", reference), ("remake", remake)):
                got[key].append(parts(_frame(path, t, 160, 90).reshape(-1, 3).astype(float)))
        row = {"window": name, "t0": t0, "t1": t1}
        for k, part in enumerate(("ground", "ink", "accent")):
            r = [p[k] for p in got["reference"] if p[k] is not None]
            o = [p[k] for p in got["remake"] if p[k] is not None]
            r, o = (np.mean(r, 0) if r else None), (np.mean(o, 0) if o else None)
            row[part] = {"reference": None if r is None else "#%02x%02x%02x" % tuple(int(round(v)) for v in r),
                         "remake": None if o is None else "#%02x%02x%02x" % tuple(int(round(v)) for v in o), "dE": de(r, o)}
        rows.append(row)
    return rows


def sheets(reference, remake, shots, out: Path, per: int = 8, w: int = 480) -> list[Path]:
    from PIL import Image, ImageDraw
    h = w * 9 // 16
    paths = []
    for s in range(0, len(shots), per):
        part = shots[s:s + per]
        sheet = Image.new("RGB", (4 * w, len(part) * (h + 18)), "black")
        d = ImageDraw.Draw(sheet)
        for k, (t0, t1, name) in enumerate(part):
            y = k * (h + 18)
            for j, f in enumerate((0.4, 0.8)):
                t = t0 + (t1 - t0) * f
                sheet.paste(Image.fromarray(_frame(reference, t, w, h)), (2 * j * w, y + 18))
                sheet.paste(Image.fromarray(_frame(remake, t, w, h)), ((2 * j + 1) * w, y + 18))
                d.text((2 * j * w + 4, y + 3), f"{name} {t:.2f}  reference", fill="yellow")
                d.text(((2 * j + 1) * w + 4, y + 3), "remake", fill="cyan")
        p = out / f"review-{s // per + 1}.jpg"
        sheet.save(p, quality=86)
        paths.append(p)
    return paths


def flagged(rows: list[dict]) -> list[dict]:
    """The windows with a colour a viewer sees as off, worst first."""
    out = []
    for r in rows:
        off = {k: r[k] for k in ("ground", "ink", "accent") if (r[k]["dE"] or 0) > SEEN}
        if off:
            out.append({"window": r["window"], "t0": r["t0"], "off": off, "worst": max(v["dE"] for v in off.values())})
    return sorted(out, key=lambda x: -x["worst"])


def report(rows: list[dict], sheet_paths) -> str:
    lines = ["# Review", "", "Colours a viewer sees as off (dE above 6; above 12 another colour), worst first. Read the sheets "
             "beside it and add what the numbers can't see: what is missing, what faces or moves the wrong way, what a "
             "shot is for.", "", "| window | t0 | ground | ink | accent |", "|---|---|---|---|---|"]
    cell = lambda v: "" if not v or (v["dE"] or 0) <= SEEN else f'{v["reference"]} → {v["remake"]} (dE {v["dE"]}{"!" if v["dE"] > OTHER else ""})'  # noqa: E731
    for f in flagged(rows):
        lines.append(f'| {f["window"]} | {f["t0"]:.2f} | ' + " | ".join(cell(f["off"].get(k)) for k in ("ground", "ink", "accent")) + " |")
    if len(lines) == 6:
        lines.append("| (none) | | | | |")
    lines += ["", "Sheets: " + ", ".join(Path(p).name for p in sheet_paths)]
    return "\n".join(lines) + "\n"


def run(reference, remake, shots_path, out, per: int = 8) -> dict:
    shots = json.loads(Path(shots_path).read_text())
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    rows = palette(reference, remake, shots)
    paths = sheets(reference, remake, shots, out, per)
    (out / "review.json").write_text(json.dumps({"windows": rows, "flagged": flagged(rows)}, indent=1))
    (out / "review.md").write_text(report(rows, paths))
    return {"windows": rows, "flagged": flagged(rows), "sheets": [str(p) for p in paths], "out": str(out)}


# ---- the motion designer's review

MW, MH, MFPS = 160, 90, 30
SNAP = 4.0        # levels a frame at 160 x 90: the picture changing at once
STEP, SEG = 0.2, 0.6
MOVING = 0.25     # px a frame at 320 wide: a picture that moves
CHANGING = 1.5    # levels a frame: a picture that changes in place


def _gray(path) -> np.ndarray:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-vf", f"fps={MFPS},scale={MW}:{MH}:flags=area",
                          "-pix_fmt", "gray", "-f", "rawvideo", "-"], capture_output=True, check=True).stdout
    n = len(raw) // (MW * MH)
    return np.frombuffer(raw[: n * MW * MH], np.uint8).reshape(n, MH, MW)


def change(g) -> np.ndarray:
    """Each frame's mean change from the one before, in levels of 255 (the first frame's is 0)."""
    return np.concatenate([[0.0], np.abs(np.diff(g.astype(np.int16), axis=0)).mean(axis=(1, 2))])


def drift(c) -> np.ndarray:
    """The change a picture keeps up round each frame (the median over a second each side): rain, grain, a slow move."""
    w = MFPS
    return np.array([np.median(c[max(0, i - w): i + w + 1]) for i in range(len(c))])


def speeds(g) -> np.ndarray:
    """The picture's speed every STEP s: the mean optical-flow length, in px a frame at 320 wide."""
    import cv2
    k = int(round(STEP * MFPS))
    return np.array([float(np.linalg.norm(cv2.calcOpticalFlowFarneback(g[i], g[i + 1], None, 0.5, 3, 15, 3, 5, 1.2, 0),
                                          axis=2).mean()) * 320 / MW for i in range(0, len(g) - 1, k)])


def snaps(c, base, gap: float = 0.1) -> list[dict]:
    """The frames where the picture changes at once, merged when under `gap` s apart."""
    out = []
    for i in np.flatnonzero((c > SNAP) & (c > 4 * np.maximum(base, 0.25))):
        if out and i - out[-1]["end"] <= gap * MFPS:
            out[-1]["end"] = int(i)
        else:
            out.append({"start": int(i), "end": int(i)})
    for e in out:
        p = e["start"] + int(np.argmax(c[e["start"]: e["end"] + 1]))
        e.update(peak=p, t=round(p / MFPS, 3), size=round(float(c[p]), 1))
    return out


def _place(x: float, y: float) -> str:
    v, h = ("top", "middle", "bottom")[min(2, int(y * 3))], ("left", "centre", "right")[min(2, int(x * 3))]
    return "the centre" if (v, h) == ("middle", "centre") else f"the {v} {h}"


def what(g, p: int) -> dict:
    """A snap at frame p: how much of the frame changes, where, and whether it brightens or darkens."""
    d = g[p].astype(np.int16) - g[p - 1].astype(np.int16)
    hot = np.abs(d) > 16
    ys, xs = np.nonzero(hot)
    share = float(hot.mean())
    kind = "a cut" if share > 0.5 else "a local change" if share < 0.12 else "a burst"
    return {"kind": kind, "share": round(share, 2), "where": _place(xs.mean() / MW, ys.mean() / MH) if len(xs) else "",
            "light": round(float(d.mean()), 1)}


def meet(e: dict, cr, co, br, bo) -> tuple[dict, str | None]:
    """How the remake meets a reference snap: its largest change within 0.25 s, and the verdict (None: on time)."""
    near, wide = int(0.25 * MFPS), int(0.5 * MFPS)
    lo, hi = max(1, e["start"] - near), min(len(co) - 1, e["end"] + near)
    q = lo + int(np.argmax(co[lo:hi + 1]))
    got = {"t": round(q / MFPS, 3), "size": round(float(co[q]), 1)}
    if co[q] >= 0.5 * cr[e["peak"]]:
        dt = (q - e["peak"]) / MFPS
        return got, None if abs(dt) <= 0.1 else f"{abs(dt):.2f} s {'late' if dt > 0 else 'early'}"
    if co[q] > SNAP and co[q] > 4 * max(bo[q], 0.25):
        return got, f"weaker ({co[q]:.0f} levels to {cr[e['peak']]:.0f})"
    a, b = max(1, e["start"] - wide), min(len(co) - 1, e["end"] + wide)
    excess = lambda c, base: float(np.clip(c[a:b + 1] - base[a:b + 1], 0, None).sum())  # noqa: E731
    return got, "eased: the change spread where the reference snaps" if excess(co, bo) >= 0.5 * excess(cr, br) else "missing"


def _window_at(shots, t: float) -> str:
    return next((n for t0, t1, n in shots if t0 <= t < t1), "")


def spans(cr, co, sr, so, shots) -> list[dict]:
    """Every SEG s: the remake's speed and change in place against the reference's, merged where the verdict holds."""
    k = int(round(SEG / STEP))
    out = []
    for j in range(0, min(len(sr), len(so)) - k + 1, k):
        t0, t1 = round(j * STEP, 2), round((j + k) * STEP, 2)
        vr, vo = float(sr[j:j + k].mean()), float(so[j:j + k].mean())
        ar, ao = float(cr[int(t0 * MFPS):int(t1 * MFPS)].mean()), float(co[int(t0 * MFPS):int(t1 * MFPS)].mean())
        off = []
        if vr >= MOVING and vo < 0.5 * vr:
            off.append("still where the reference moves" if vo < 0.15 * vr else "slow")
        elif vo >= MOVING and vr < 0.5 * vo:
            off.append("moves where the reference holds" if vr < 0.15 * vo else "fast")
        if ar >= CHANGING and ao < 0.4 * ar:
            off.append("holds where the reference changes")
        elif ao >= CHANGING and ar < 0.4 * ao:
            off.append("changes where the reference holds")
        if not off:
            continue
        row = {"t0": t0, "t1": t1, "window": _window_at(shots, t0), "off": off, "speed": [round(vr, 2), round(vo, 2)],
               "change": [round(ar, 1), round(ao, 1)]}
        last = out[-1] if out else None
        if last and last["t1"] == t0 and last["off"] == off and last["window"] == row["window"]:
            n = (last["t1"] - last["t0"]) / SEG
            last["speed"] = [round((last["speed"][i] * n + row["speed"][i]) / (n + 1), 2) for i in (0, 1)]
            last["change"] = [round((last["change"][i] * n + row["change"][i]) / (n + 1), 1) for i in (0, 1)]
            last["t1"] = t1
        else:
            out.append(row)
    return out


def _clip(path, t0: float, t1: float, w: int, h: int) -> list[np.ndarray]:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{max(0.0, t0):.3f}", "-i", str(path), "-t", f"{t1 - t0:.3f}",
                          "-vf", f"fps={MFPS},scale={w}:{h}:flags=area", "-pix_fmt", "rgb24", "-f", "rawvideo", "-"],
                         capture_output=True, check=True).stdout
    n = len(raw) // (w * h * 3)
    return list(np.frombuffer(raw[: n * w * h * 3], np.uint8).reshape(n, h, w, 3))


def strips(reference, remake, items: list[dict], out: Path, per: int = 5, w: int = 240) -> list[Path]:
    """Each item's moments, the reference over the remake: {"label", "times"}."""
    from PIL import Image, ImageDraw
    h = w * 9 // 16
    cols = max((len(i["times"]) for i in items), default=8)
    paths = []
    for s in range(0, len(items), per):
        part = items[s:s + per]
        row = 18 + 2 * (h + 14)
        sheet = Image.new("RGB", (cols * w, len(part) * row), "black")
        d = ImageDraw.Draw(sheet)
        for k, it in enumerate(part):
            y = k * row
            d.text((4, y + 3), it["label"], fill="white")
            t0, t1 = min(it["times"]), max(it["times"])
            for j, (path, name, col) in enumerate(((reference, "reference", "yellow"), (remake, "remake", "cyan"))):
                fr = _clip(path, t0, t1 + 2 / MFPS, w, h)
                for c, t in enumerate(it["times"]):
                    if not fr:
                        continue
                    f = fr[min(len(fr) - 1, max(0, int(round((t - t0) * MFPS))))]
                    x, yy = c * w, y + 18 + j * (h + 14)
                    sheet.paste(Image.fromarray(f), (x, yy + 14))
                    d.text((x + 3, yy + 1), f"{name} {t:.2f}", fill=col)
        p = out / f"motion-{s // per + 1}.jpg"
        sheet.save(p, quality=86)
        paths.append(p)
    return paths


def motion(reference, remake, shots) -> dict:
    gr, go = _gray(reference), _gray(remake)
    n = min(len(gr), len(go))
    gr, go = gr[:n], go[:n]
    cr, co = change(gr), change(go)
    br, bo = drift(cr), drift(co)
    rows = []
    for e in snaps(cr, br):
        got, verdict = meet(e, cr, co, br, bo)
        rows.append({"t": e["t"], "window": _window_at(shots, e["t"]), "reference": {"size": e["size"], **what(gr, e["peak"])},
                     "remake": got, "verdict": verdict})
    ref_t = [r["t"] for r in rows]
    extra = [{"t": e["t"], "window": _window_at(shots, e["t"]), "remake": {"size": e["size"], **what(go, e["peak"])},
              "verdict": "a snap the reference doesn't have"}
             for e in snaps(co, bo) if all(abs(e["t"] - t) > 0.25 for t in ref_t)]
    return {"snaps": rows, "extra": extra, "spans": spans(cr, co, speeds(gr), speeds(go), shots)}


def motion_report(m: dict, strip_paths) -> str:
    off = [r for r in m["snaps"] if r["verdict"]]
    lines = ["# Motion review", "",
             f"The reference's snaps (frames where its picture changes at once): {len(m['snaps'])}, of which the remake "
             f"meets {len(m['snaps']) - len(off)} on time. Then every 0.6 s where the remake's picture moves or changes "
             "unlike the reference's. Read the strips beside it, then add what the numbers can't see: a figure's gait, "
             "what a move is for, the curve of a push.", "",
             "| t | window | the reference | the remake | verdict |", "|---|---|---|---|---|"]
    desc = lambda r: f'{r["kind"]}, {r["size"]} levels, {int(r["share"] * 100)} % of the frame, {r["where"]}' + (  # noqa: E731
        f', {"brighter" if r["light"] > 0 else "darker"} by {abs(r["light"])}' if abs(r["light"]) >= 4 else "")
    for r in off:
        lines.append(f'| {r["t"]:.2f} | {r["window"]} | {desc(r["reference"])} | {r["remake"]["size"]} levels at '
                     f'{r["remake"]["t"]:.2f} | {r["verdict"]} |')
    for r in m["extra"]:
        lines.append(f'| {r["t"]:.2f} | {r["window"]} | | {desc(r["remake"])} | {r["verdict"]} |')
    if len(lines) == 6:
        lines.append("| (none) | | | | |")
    lines += ["", "| from | to | window | the remake | speed (px a frame: reference, remake) | change (levels a frame) |",
              "|---|---|---|---|---|---|"]
    for s in m["spans"]:
        lines.append(f'| {s["t0"]:.1f} | {s["t1"]:.1f} | {s["window"]} | {", ".join(s["off"])} | '
                     f'{s["speed"][0]}, {s["speed"][1]} | {s["change"][0]}, {s["change"][1]} |')
    lines += ["", "Strips: " + ", ".join(Path(p).name for p in strip_paths)]
    return "\n".join(lines) + "\n"


def motion_run(reference, remake, shots_path, out, cap: int = 40) -> dict:
    shots = json.loads(Path(shots_path).read_text())
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    m = motion(reference, remake, shots)
    items = [{"label": f'{r["t"]:.2f} s  {r["window"]}: {r["verdict"]}', "times": [r["t"] + d for d in
              (-0.2, -0.1, -1 / MFPS, 0, 1 / MFPS, 0.1, 0.2, 0.4)]} for r in m["snaps"] if r["verdict"]]
    items += [{"label": f'{s["t0"]:.1f}-{s["t1"]:.1f} s  {s["window"]}: {", ".join(s["off"])}',
               "times": [s["t0"] + (s["t1"] - s["t0"]) * f for f in np.linspace(0.05, 0.95, 8)]} for s in m["spans"]]
    paths = strips(reference, remake, items[:cap], out)
    (out / "motion.json").write_text(json.dumps(m, indent=1))
    (out / "motion.md").write_text(motion_report(m, paths))
    return {**m, "strips": [str(p) for p in paths], "out": str(out)}
