"""Numbers that count: a value printed as text and tweened (0 to 4,200, 0% to 98%), read back by OCR.

To the tracker a counter is digits changing in place, which it reports as a scatter of small moves. This reader
finds the numbers in a motion run's frame at rest (tesseract, sparse text), keeps those whose box holds still while
its reading changes, reads the box on every frame that changed (one line, digits and the usual signs only), keeps
the longest monotone run of readings (a misread digit breaks it and is dropped), and fits the value like any tween:
the counter's duration and ease, its start and end values and how it is printed. A count's slow tail (the last few
units of an expo.out) can outlast the motion run, so the box is read on until it has held still for a while; a
misread that still fits the monotone run (a 5 read as a 9) lies off the fitted curve and is dropped before a second
fit. The tracks inside a counter's box are its digits and are folded into it, in that run and in later ones.

tesseract is optional: without it counters are not read, and the tracker's pieces stay as they were.
"""
from __future__ import annotations

import re
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor

import cv2
import numpy as np

from ..video import Clip
from . import eases
from .fit import PREFER, fit_move

TESSERACT = shutil.which("tesseract")
FIND_UP = 2          # the frame is enlarged this much to find the numbers in it
READ_UP = 3          # ...and a counter's box this much to read it
DIGITS = "0123456789.,%$€£¥+-KMBkx"
MIN_VALUES = 3       # distinct readings needed: fewer is a number that changed once (a cut, a swap), not a count
KEPT = 0.6           # share of the readings the monotone run must keep: fewer and the box isn't one counting number
CHANGED = 30.0       # grey levels a pixel changes by, between frames, where a digit was redrawn (blurred: not grain)
REDRAWN = 6          # ...and how many such pixels make the box redrawn: one digit of many is enough
SETTLED = 0.5        # s: a box not redrawn for this long has finished counting
OFF_CURVE = 0.04     # a reading this far from the fitted curve (share of the count's travel) is a misread
NUMBER = re.compile(r"^(?P<pre>[^\d+\-]*?)(?P<num>[+\-]?\d[\d,.]*)(?P<suf>[^\d]*)$")


def available() -> bool:
    return TESSERACT is not None


def parse(s: str) -> dict | None:
    """'$12.5M' -> value 12.5, prefix '$', suffix 'M', 1 decimal, ',' between thousands (when it shows)."""
    m = NUMBER.match(s.strip())
    if not m:
        return None
    num = m["num"]
    whole, _, frac = num.rpartition(".") if "." in num else (num, "", "")
    if "," in frac or (whole and not re.fullmatch(r"[+\-]?\d{1,3}(,\d{3})*|[+\-]?\d+", whole)):
        return None                                       # '2,17' or '1.2.3': a misread, not a number
    return {"value": float(num.replace(",", "")), "prefix": m["pre"], "suffix": m["suf"],
            "decimals": len(frac), "sep": "," if "," in whole else ""}


def _tesseract(img: np.ndarray, *args: str) -> str:
    ok, png = cv2.imencode(".png", img)
    r = subprocess.run([TESSERACT, "stdin", "stdout", *args], input=png.tobytes(), capture_output=True)
    return r.stdout.decode("utf-8", "replace")


def _numbers(frame: np.ndarray) -> list[dict]:
    """Words with a digit in them, with their boxes (analysis px) and line, in the frame."""
    grey = cv2.resize(cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY), None, fx=FIND_UP, fy=FIND_UP, interpolation=cv2.INTER_CUBIC)
    words = []
    for row in _tesseract(grey, "--psm", "11", "tsv").splitlines()[1:]:
        c = row.split("\t")
        if len(c) == 12 and c[11].strip() and float(c[10]) > 30:
            x, y, w, h = (int(v) / FIND_UP for v in c[6:10])
            words.append({"text": c[11].strip(), "box": (x, y, w, h)})
    return [{**w, "others": [o["box"] for o in words if o is not w]} for w in words if re.search(r"\d", w["text"])]


def _window(word: dict, clip: Clip) -> tuple[int, int, int, int]:
    """The word's box widened to where a longer or shorter number would reach, short of its neighbours."""
    x, y, w, h = word["box"]
    x0, x1 = x - max(w * 0.5, h), x + w + max(w * 0.5, h)
    for ox, oy, ow, oh in word["others"]:
        if oy < y + h and oy + oh > y:                    # a neighbour on the same line
            if ox + ow <= x:
                x0 = max(x0, ox + ow + 0.2 * h)
            elif ox >= x + w:
                x1 = min(x1, ox - 0.2 * h)
    pad = 0.3 * h
    return (int(max(0, x0)), int(max(0, y - pad)), int(min(clip.w, x1)), int(min(clip.h, y + h + pad)))


def _monotone(v: np.ndarray) -> np.ndarray:
    """Which readings to keep: the longest run that never goes down (or never goes up), in time order."""
    idx = np.flatnonzero(~np.isnan(v))
    best = np.zeros(len(v), bool)
    for sign in (1, -1):
        x = sign * v[idx]
        n = len(x)
        length, prev = np.ones(n, int), np.full(n, -1)
        for i in range(n):                                # O(n^2): a counter is read on a few dozen frames
            for j in range(i):
                if x[j] <= x[i] and length[j] + 1 > length[i]:
                    length[i], prev[i] = length[j] + 1, j
        if n and length.max() > best.sum():
            keep, i = np.zeros(len(v), bool), int(np.argmax(length))
            while i >= 0:
                keep[idx[i]], i = True, prev[i]
            best = keep
    return best


def _inside(box, x, y) -> bool:
    return box[0] <= x <= box[0] + box[2] and box[1] <= y <= box[1] + box[3]


def find(clip: Clip, shot: dict, run: tuple[int, int], known: list[dict] = ()) -> list[dict]:
    """The counters in one motion run, as events: kind 'count', the value's fit, and how the number is printed.
    `known`: counters found in the shot's earlier runs; one still counting when this run starts isn't found again."""
    if not available():
        return []
    a, b = run
    last_f = min(shot["end"] - 1, clip.n - 1)
    lo, rest = max(shot["start"], a - 2), min(last_f, b + 2)
    out = []
    for word in _numbers(clip.frames[rest]):
        x, y, w, h = (v * clip.scale for v in word["box"])
        if any(_inside(c["box"], x + w / 2, y + h / 2) and c["props"]["value"]["t1"] >= lo / clip.fps for c in known):
            continue
        x0, y0, x1, y1 = _window(word, clip)
        if x1 - x0 < 4 or y1 - y0 < 6:
            continue
        crops = clip.frames[lo:last_f + 1, y0:y1, x0:x1].astype(np.float32).mean(axis=3)
        diff = np.abs(np.diff(crops, axis=0))
        changed = [(cv2.blur(d, (3, 3)) > CHANGED).sum() for d in diff]
        redrawn = np.r_[True, np.array(changed) >= REDRAWN]
        hi, quiet = rest, int(round(SETTLED * clip.fps))
        while hi < last_f and redrawn[hi + 1 - lo:hi + 1 - lo + quiet].any():
            hi += 1                                       # still counting after the run: its slow tail
        redrawn = redrawn[:hi + 1 - lo]
        if redrawn.sum() < MIN_VALUES:
            continue                                      # a number that holds still
        frames = [f for f, r in zip(range(lo, hi + 1), redrawn) if r]
        big = [cv2.resize(cv2.cvtColor(clip.frames[f][y0:y1, x0:x1], cv2.COLOR_RGB2GRAY), None, fx=READ_UP, fy=READ_UP,
                          interpolation=cv2.INTER_CUBIC) for f in frames]
        with ThreadPoolExecutor(8) as pool:
            texts = list(pool.map(lambda g: _tesseract(g, "--psm", "7", "-c", f"tessedit_char_whitelist={DIGITS}").strip(),
                                  big))
        reads = {f: parse(s) for f, s in zip(frames, texts)}
        last, v = None, []
        for f in range(lo, hi + 1):                       # a frame not redrawn shows what the one before showed
            last = reads[f] if f in reads else last
            v.append(last["value"] if last else np.nan)
        v = np.array(v)
        seen = ~np.isnan(v)
        if len(np.unique(v[seen])) < MIN_VALUES:
            continue
        keep = _monotone(v)
        if keep.sum() < KEPT * seen.sum():
            continue
        v = np.where(keep, v, np.nan)
        t = np.arange(lo, hi + 1) / clip.fps
        f = fit_move(t, v, clip.fps, monotone=True, prefer=PREFER["move"])
        if f:
            curve = f["from"] + f["delta"] * eases.get(f["best"])(np.clip((t - f["t0"]) / (f["t1"] - f["t0"]), 0, 1))
            off = np.abs(v - curve) > OFF_CURVE * abs(f["delta"])
            if off.any():
                keep &= ~off
                v = np.where(off, np.nan, v)
                f = fit_move(t, v, clip.fps, monotone=True, prefer=PREFER["move"])
        if not f or f["dur"] < 3 / clip.fps:
            continue
        fmt = next((r for r in (reads.get(k) for k in range(hi, lo - 1, -1)) if r), None)
        values = v[keep]
        s = clip.scale
        out.append({"kind": "count", "shot": shot["id"], "via_edge": None,
                    "box": [round(x0 * s, 1), round(y0 * s, 1), round((x1 - x0) * s, 1), round((y1 - y0) * s, 1)],
                    "props": {"value": f}, "reading": {"mode": "counter", "axis": None, "anchor": None},
                    "counter": {"from": float(values[0]), "to": float(values[-1]), "reads": int(keep.sum()),
                                "format": {k: fmt[k] for k in ("prefix", "suffix", "decimals", "sep")}}})
    return out


def absorb(counters: list[dict], tracks: list[dict], new: list[dict] = ()) -> list[dict]:
    """The tracks that aren't a counter's digits (their centre inside its box). `new`: the counters found in this
    run; one whose digits appeared during it entered with them (later ticks of an earlier counter are just ticks)."""
    rest = []
    for tr in tracks:
        x, y, w, h = tr["box"]
        home = next((c for c in counters if _inside(c["box"], x + w / 2, y + h / 2)), None)
        if home is None:
            rest.append(tr)
        elif tr["kind"] == "appear" and any(home is c for c in new):
            home["counter"]["enters"] = True
    return rest
