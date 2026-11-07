"""`moodreel diff <reference> <remake>`: a remake against its reference, frame by frame, as a list of what to fix.

`compare` scores windows; this lists the events a viewer notices on the frame they happen:

- **Cuts.** Every cut in both films (`cutlist`). Each of the reference's is matched to the remake's nearest within
  three quarters of a second: on time, late or early by n frames, or missed (with what the remake does there
  instead, a dissolve or nothing). The remake's other cuts are extra.
- **Length.** Both films' lengths and the difference.
- **Sound.** How late the remake's soundtrack runs against the reference's: the two onset envelopes (10 ms hops)
  cross-correlated within a second either way, in ms and frames.
- **Gaps.** Stretches of six frames or more where the reference has a picture and the remake shows black, one flat
  colour, or a frozen frame while the reference moves.
- **Worst moments.** The six frames furthest from the reference (at least a second apart), each with the cell of a
  4 x 4 grid that fails most, laid beside the reference's in `worst.jpg`.

Everything is in the reference's frames (the remake is read at the reference's rate). Writes diff.json, DIFF.md and
worst.jpg to `out`.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import cv2
import numpy as np

from . import cutlist
from ..video import probe

MATCH_S = 0.75          # a reference cut and a remake cut this close are the same cut, late or early
HOP_S = 0.01
LAG_S = 1.0
GAP_MIN = 6             # frames
SMALL = (160, 90)
GRID = 4


def _frames(path: str, fps: float, size=SMALL):
    w, h = size
    proc = subprocess.Popen(["ffmpeg", "-v", "error", "-i", str(path), "-vf", f"setpts=PTS-STARTPTS,fps={fps},scale={w}:{h}:flags=area",
                             "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
    out = []
    try:
        while True:
            b = proc.stdout.read(w * h * 3)
            if len(b) < w * h * 3:
                break
            out.append(np.frombuffer(b, np.uint8).reshape(h, w, 3))
    finally:
        proc.stdout.close()
        proc.wait()
    return np.stack(out) if out else np.zeros((0, h, w, 3), np.uint8)


def _sound(path: str, rate: int = 8000) -> np.ndarray | None:
    """Mono samples from the film's start (silence first where the soundtrack starts late), or None without sound."""
    p = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-map", "0:a:0", "-ac", "1", "-ar", str(rate),
                        "-af", "aresample=async=1:first_pts=0", "-f", "f32le", "-"], capture_output=True)
    if p.returncode or not p.stdout:
        return None
    return np.frombuffer(p.stdout, np.float32)


def _onsets(x: np.ndarray, rate: int = 8000) -> np.ndarray:
    hop = int(rate * HOP_S)
    n = len(x) // hop
    e = np.log1p(1000 * np.square(x[: n * hop].reshape(n, hop)).mean(axis=1))
    return np.maximum(0.0, np.diff(e, prepend=e[:1]))


def offset_ms(ref: str, remake: str) -> float | None:
    """How late the remake's sound runs (ms; negative: early), from the onset envelopes' cross-correlation peak."""
    a, b = _sound(ref), _sound(remake)
    if a is None or b is None or len(a) < 8000 or len(b) < 8000:
        return None
    ea, eb = _onsets(a), _onsets(b)
    n = min(len(ea), len(eb))
    ea, eb = ea[:n] - ea[:n].mean(), eb[:n] - eb[:n].mean()
    if not ea.any() or not eb.any():
        return None
    size = 1 << int(np.ceil(np.log2(2 * n)))
    xc = np.fft.irfft(np.fft.rfft(eb, size) * np.conj(np.fft.rfft(ea, size)), size)
    lag = int(round(LAG_S / HOP_S))
    lags = np.r_[np.arange(0, lag + 1), np.arange(-lag, 0)]
    vals = np.r_[xc[: lag + 1], xc[-lag:]]
    k = int(np.argmax(vals))
    best = float(lags[k])
    if 0 < k < len(vals) - 1 and lags[k - 1] == lags[k] - 1 and lags[k + 1] == lags[k] + 1:
        y0, y1, y2 = vals[k - 1], vals[k], vals[k + 1]
        d = y0 - 2 * y1 + y2
        if d:
            best += float(0.5 * (y0 - y2) / d)          # the peak between hops
    return round(float(best) * HOP_S * 1000, 1)


def _like(a: np.ndarray, b: np.ndarray) -> float:
    a = a.astype(np.float32).mean(axis=2).ravel()
    b = b.astype(np.float32).mean(axis=2).ravel()
    a, b = a - a.mean(), b - b.mean()
    d = float(np.sqrt((a * a).sum() * (b * b).sum()))
    return float((a * b).sum() / d) if d > 1e-6 else (1.0 if not a.any() and not b.any() else 0.0)


def blended(f: int, ref: np.ndarray, rem: np.ndarray, span: int = 12) -> bool:
    """Around a reference cut the remake missed, does it mix the old shot into the new one (a dissolve, even over moving
    shots) rather than carry on? Frames that look like both shots at once, the new one gaining."""
    lo, hi = max(1, f - span), min(len(rem), len(ref), f + span)
    if hi - lo < 4 or f >= len(ref):
        return False
    old = [_like(rem[k], ref[min(k, f - 1)]) for k in range(lo, hi)]
    new = [_like(rem[k], ref[max(k, f)]) for k in range(lo, hi)]
    mixed = sum(1 for a, b in zip(old, new) if 0.15 < a < 0.95 and 0.15 < b < 0.95)
    return mixed >= 3 and new[-1] > new[0] + 0.2


def match(ref_cuts: list[int], rem_cuts: list[int], fps: float, ref=None, rem=None,
          rem_dissolves=()) -> tuple[list[dict], list[int], list[int]]:
    """One-to-one, nearest first, within MATCH_S. With the frames, a pair more than a frame apart counts only if the
    remake's cut lands on the reference's new shot (what follows it looks more like the reference after its cut than
    before it); a reference cut the remake dissolves over is missed, whatever cut comes near it."""
    win = max(1, int(round(MATCH_S * fps)))
    covered = {f for f in ref_cuts if any(a - 2 <= f <= b + 2 for a, b in rem_dissolves)
               or (ref is not None and rem is not None and f not in rem_cuts and blended(f, ref, rem))}

    def lands(f, g):
        if ref is None or rem is None or abs(g - f) <= 1:
            return True                     # on its frame: the same cut, however unlike the remake's picture is
        k = min(g + 1, len(rem) - 1, len(ref) - 1)
        if rem[k].std() < 3:
            return False                    # a cut to black or one flat colour lands on no shot
        before = ref[max(0, min(f - 1, len(ref) - 1))]
        return _like(rem[k], ref[k]) > _like(rem[k], before)   # relative: a remake looks unlike its reference anyway

    pairs = sorted(((abs(g - f), f, g) for f in ref_cuts for g in rem_cuts if abs(g - f) <= win and f not in covered))
    used_f, used_g, matched = set(), set(), []
    for _, f, g in pairs:
        if f in used_f or g in used_g or not lands(f, g):
            continue
        used_f.add(f)
        used_g.add(g)
        matched.append({"reference": int(f), "remake": int(g), "off": int(g - f)})
    matched.sort(key=lambda m: m["reference"])
    return matched, [int(f) for f in ref_cuts if f not in used_f], [int(g) for g in rem_cuts if g not in used_g]


def gaps(ref: np.ndarray, rem: np.ndarray) -> list[dict]:
    """Remake stretches (start, end exclusive) of black, one flat colour, or a frozen frame where the reference moves."""
    n = min(len(ref), len(rem))
    rf, mf = ref[:n].astype(np.int16), rem[:n].astype(np.int16)
    ref_std = rf.reshape(n, -1).std(axis=1)
    rem_std = mf.reshape(n, -1).std(axis=1)
    rem_mean = mf.reshape(n, -1).mean(axis=1)
    ref_move = np.r_[0.0, np.abs(np.diff(rf, axis=0)).mean(axis=(1, 2, 3))]
    rem_move = np.r_[0.0, np.abs(np.diff(mf, axis=0)).mean(axis=(1, 2, 3))]
    kind = np.full(n, "", dtype=object)
    has = ref_std > 8
    kind[has & (rem_mean < 10) & (rem_std < 3)] = "black"
    kind[has & (kind == "") & (rem_std < 3)] = "flat"
    frozen = has & (kind == "") & (rem_move < 0.15) & (ref_move > 0.6)
    kind[frozen] = "frozen"
    out, i = [], 0
    while i < n:
        if kind[i]:
            j = i
            while j < n and kind[j] == kind[i]:
                j += 1
            if kind[i] == "frozen":
                i0 = max(0, i - 1)                     # the frame that holds is the one before the first still step
                if j - i0 >= GAP_MIN:
                    out.append({"start": int(i0), "end": int(j), "what": "frozen"})
            elif j - i >= GAP_MIN:
                out.append({"start": int(i), "end": int(j), "what": kind[i]})
            i = j
        else:
            i += 1
    return out


def worst(ref: np.ndarray, rem: np.ndarray, fps: float, k: int = 6) -> list[dict]:
    n = min(len(ref), len(rem))
    if not n:
        return []
    g1 = ref[:n].astype(np.float32).mean(axis=3)
    g2 = rem[:n].astype(np.float32).mean(axis=3)
    h, w = g1.shape[1:]
    ch, cw = h // GRID, w // GRID
    cells = np.abs(g1[:, :ch * GRID, :cw * GRID] - g2[:, :ch * GRID, :cw * GRID]).reshape(n, GRID, ch, GRID, cw).mean(axis=(2, 4))
    score = 1 - cells.mean(axis=(1, 2)) / 255
    out, taken = [], []
    for i in np.argsort(score):
        if any(abs(int(i) - t) < fps for t in taken):
            continue
        taken.append(int(i))
        r, c = np.unravel_index(int(np.argmax(cells[i])), (GRID, GRID))
        out.append({"frame": int(i), "t": round(int(i) / fps, 3), "score": round(float(score[i]), 3),
                    "cell": [int(c), int(r)], "cell_error": round(float(cells[i, r, c]), 1)})
        if len(out) == k:
            break
    return out


def _window(shots, t):
    for a, b, name in shots or []:
        if a <= t < b:
            return name
    return None


def run(reference, remake, shots=None, out=None) -> dict:
    reference, remake = str(reference), str(remake)
    if isinstance(shots, (str, Path)):
        shots = json.loads(Path(shots).read_text())
    fps = probe(reference)["fps"]
    a, b = cutlist.find(reference), cutlist.find(remake)
    scale = fps / b["fps"]
    rem_cuts = [int(round(g * scale)) for g in b["cuts"]]       # the remake's cuts in the reference's frames
    rem_dis = [[int(round(x * scale)), int(round(y * scale))] for x, y in b["dissolves"] + b["dips"]]
    ref_frames, rem_frames = _frames(reference, fps), _frames(remake, fps)
    matched, missed, extra = match(a["cuts"], rem_cuts, fps, ref_frames, rem_frames, rem_dis)
    missed_how = {f: "dissolve" if any(x - 2 <= f <= y + 2 for x, y in rem_dis) or blended(f, ref_frames, rem_frames) else "none"
                  for f in missed}
    res = {
        "reference": reference, "remake": remake, "fps": fps,
        "cuts": {"reference": a["cuts"], "remake": rem_cuts, "matched": matched, "missed": missed, "extra": extra,
                 "missed_how": {str(k): v for k, v in missed_how.items()},
                 "reference_dissolves": a["dissolves"] + a["dips"], "remake_dissolves": rem_dis},
        "duration": {"reference": round(a["n"] / fps, 3), "remake": round(b["n"] / b["fps"], 3),
                     "difference": round(b["n"] / b["fps"] - a["n"] / fps, 3)},
        "audio": {"offset_ms": None, "offset_frames": None},
        "blanks": gaps(ref_frames, rem_frames),
        "worst": worst(ref_frames, rem_frames, fps),
    }
    off = offset_ms(reference, remake)
    if off is not None:
        res["audio"] = {"offset_ms": off, "offset_frames": round(off / 1000 * fps, 2)}
    for m in res["cuts"]["matched"]:
        m["window"] = _window(shots, m["reference"] / fps)
    if out:
        out = Path(out)
        out.mkdir(parents=True, exist_ok=True)
        (out / "diff.json").write_text(json.dumps(res, indent=1))
        (out / "DIFF.md").write_text(report(res, shots))
        sheet(res, out / "worst.jpg")
    return res


def sheet(res: dict, path, size=(480, 270)) -> Path:
    """Each worst moment: the reference (left) and the remake (right), the failing cell outlined in both."""
    w, h = size
    rows = []
    for m in res["worst"]:
        pair = []
        for src in (res["reference"], res["remake"]):
            raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{m['t']:.4f}", "-i", src, "-frames:v", "1", "-vf",
                                  f"scale={w}:{h}", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], capture_output=True).stdout
            img = np.frombuffer(raw, np.uint8).reshape(h, w, 3).copy() if len(raw) >= w * h * 3 else np.zeros((h, w, 3), np.uint8)
            c, r = m["cell"]
            cv2.rectangle(img, (c * w // GRID, r * h // GRID), ((c + 1) * w // GRID - 1, (r + 1) * h // GRID - 1), (0, 220, 255), 2)
            pair.append(img)
        row = np.hstack(pair)
        label = f"{m['t']:.2f}s  frame {m['frame']}  score {m['score']}"
        cv2.rectangle(row, (0, 0), (10 + 8 * len(label), 20), (0, 0, 0), -1)
        cv2.putText(row, label, (5, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 230, 255), 1, cv2.LINE_AA)
        rows.append(row)
    board = np.vstack(rows) if rows else np.zeros((h, w * 2, 3), np.uint8)
    cv2.imwrite(str(path), board, [cv2.IMWRITE_JPEG_QUALITY, 88])
    return Path(path)


def report(res: dict, shots=None) -> str:
    fps = res["fps"]
    t = lambda f: f"{f / fps:.3f}s (frame {f})"  # noqa: E731
    c = res["cuts"]
    late = [m for m in c["matched"] if m["off"]]
    lines = ["# The remake against its reference, frame by frame", "",
             f"- reference: `{res['reference']}`", f"- remake: `{res['remake']}`", f"- frames at the reference's {fps:g} fps", "",
             "## What to fix", ""]
    for m in late:
        where = f" ({m['window']})" if m.get("window") else ""
        lines.append(f"- cut at {t(m['reference'])}{where}: the remake's comes {abs(m['off'])} frames "
                     f"{'late' if m['off'] > 0 else 'early'} ({t(m['remake'])})")
    for f in c["missed"]:
        how = c["missed_how"].get(str(f), "none")
        lines.append(f"- cut at {t(f)} ({_window(shots, f / fps) or 'no window'}): missed"
                     + (", the remake dissolves there instead" if how == "dissolve" else ", the remake carries on"))
    for g in c["extra"]:
        lines.append(f"- extra cut in the remake at {t(g)} ({_window(shots, g / fps) or 'no window'})")
    for b in res["blanks"]:
        lines.append(f"- {b['what']} in the remake from {t(b['start'])} to {t(b['end'])} ({b['end'] - b['start']} frames) "
                     "where the reference has a picture")
    d = res["duration"]
    if abs(d["difference"]) >= 0.5 / fps:
        lines.append(f"- length: the remake runs {d['remake']} s against {d['reference']} s ({d['difference']:+.3f} s)")
    a = res["audio"]
    if a["offset_ms"] is not None and abs(a["offset_ms"]) > 1000 / fps / 2:
        lines.append(f"- sound: the remake's runs {abs(a['offset_ms']):.0f} ms {'late' if a['offset_ms'] > 0 else 'early'} "
                     f"({a['offset_frames']:+.2f} frames)")
    if len(lines) == 8:
        lines.append("- nothing: every cut on its frame, the same length, the sound in sync, no gaps")
    lines += ["", "## Cuts", "", "| reference | remake | off (frames) | window |", "|---|---|---|---|"]
    for m in c["matched"]:
        lines.append(f"| {t(m['reference'])} | {t(m['remake'])} | {m['off']:+d} | {m.get('window') or ''} |")
    for f in c["missed"]:
        lines.append(f"| {t(f)} | missed | | {_window(shots, f / fps) or ''} |")
    for g in c["extra"]:
        lines.append(f"| | {t(g)} (extra) | | {_window(shots, g / fps) or ''} |")
    lines += ["", f"Length: reference {d['reference']} s, remake {d['remake']} s.",
              "Sound: " + ("no soundtrack in one of them." if a["offset_ms"] is None else f"the remake's offset {a['offset_ms']:+.1f} ms."),
              "", "## Worst moments (worst.jpg: reference left, remake right, the failing cell outlined)", ""]
    for m in res["worst"]:
        lines.append(f"- {m['t']:.2f}s (frame {m['frame']}): score {m['score']}, cell column {m['cell'][0] + 1}, "
                     f"row {m['cell'][1] + 1} off by {m['cell_error']} levels")
    return "\n".join(lines) + "\n"
