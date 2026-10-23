"""Palette: the colours a style uses, how much of the picture each takes, and the role each plays.

Per picture: k-means in CIELAB, then clusters closer than JND_MERGE (CIEDE2000) are merged, so a gradient or
compression noise doesn't split one colour into several. Across pictures: the per-picture palettes are pooled,
each picture weighing the same, and merged again; a colour's `presence` is how many pictures use it.

Roles follow what a viewer reads: the ground is what a video shows before anything stands on it (its opening
frame, when that is one colour), else the colour holding the frame's border; the ink stands furthest in lightness
from the ground, weighed by how much of the picture it takes; the accent is the most saturated colour that stays
small. Everything is measured; naming the logic
("red only for the one thing that matters") is the director's job.
"""
from __future__ import annotations

import cv2
import numpy as np
from scipy.optimize import linprog

from .color import chroma, contrast, delta_e, hex_, lab_to_rgb, rgb_to_lab

JND_MERGE = 5.0          # CIEDE2000: closer than this is one colour within a picture
POOL_MERGE = 7.0         # across pictures
LONG_EDGE = 256
VIVID, VIVID_AREA = 40.0, 0.0005   # chroma of a colour that can be an accent however small, and the least area it needs


def _small(rgb):
    h, w = rgb.shape[:2]
    k = LONG_EDGE / max(h, w)
    return cv2.resize(rgb, (max(1, round(w * k)), max(1, round(h * k))), interpolation=cv2.INTER_AREA) if k < 1 else rgb


def _merge(cols, thr):
    """cols: list of dicts with lab, area (and optional border); merges the closest pair under thr, repeatedly."""
    cols = [dict(c) for c in cols]
    while len(cols) > 1:
        labs = np.array([c["lab"] for c in cols])
        d = delta_e(labs[:, None], labs[None])
        np.fill_diagonal(d, np.inf)
        i, j = np.unravel_index(np.argmin(d), d.shape)
        if d[i, j] >= thr:
            break
        a, b = cols[i], cols[j]
        w = a["area"] + b["area"]
        m = {"lab": (np.asarray(a["lab"]) * a["area"] + np.asarray(b["lab"]) * b["area"]) / w, "area": w}
        if "border" in a:
            m["border"] = a["border"] + b["border"]
        if "refs" in a:
            m["refs"] = a["refs"] | b["refs"]
        cols = [c for k, c in enumerate(cols) if k not in (i, j)] + [m]
    return cols


def image_palette(rgb: np.ndarray, k: int = 10) -> dict:
    small = _small(rgb)
    h, w = small.shape[:2]
    lab = rgb_to_lab(small.astype(np.float64)).reshape(-1, 3).astype(np.float32)
    cv2.setRNGSeed(0)
    k = min(k, len(np.unique(small.reshape(-1, 3), axis=0)))
    _, labels, centers = cv2.kmeans(lab, k, None, (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_MAX_ITER, 30, 0.2),
                                    3, cv2.KMEANS_PP_CENTERS)
    labels = labels.ravel()
    edge = np.zeros((h, w), bool)
    bw = max(1, round(0.04 * min(h, w)))
    edge[:bw], edge[-bw:], edge[:, :bw], edge[:, -bw:] = True, True, True, True
    edge = edge.ravel()
    cols = []
    for c in range(k):
        sel = labels == c
        if sel.any():
            cols.append({"lab": lab[sel].mean(axis=0).astype(np.float64), "area": float(sel.mean()),
                         "border": float((sel & edge).sum() / edge.sum())})
    # a vivid colour kept small on purpose (one accent tile, one signal) can lose its own cluster among ten: each
    # vivid hue covering enough of the picture gets one, unless a cluster already holds it
    c = chroma(lab.astype(np.float64))
    hue = np.degrees(np.arctan2(lab[:, 2], lab[:, 1])) % 360
    for b in range(12):
        sel = (c >= VIVID) & (hue // 30 == b)
        if sel.mean() >= VIVID_AREA:
            m = np.median(lab[sel], axis=0).astype(np.float64)
            if all(float(delta_e(m, np.asarray(x["lab"]))) >= 10 for x in cols):
                cols.append({"lab": m, "area": float(sel.mean()), "border": float((sel & edge).sum() / edge.sum())})
    cols = sorted(_merge(cols, JND_MERGE), key=lambda c: -c["area"])
    return {"colors": [_describe(c) for c in cols], "luminance_hist": _lhist(lab)}


def _describe(c):
    lab = np.asarray(c["lab"], np.float64)
    rgb = lab_to_rgb(lab)
    out = {"hex": hex_(rgb), "lab": [round(float(x), 1) for x in lab], "area": round(float(c["area"]), 4),
           "chroma": round(float(chroma(lab)), 1), "lightness": round(float(lab[0]), 1),
           "hue": round(float(np.degrees(np.arctan2(lab[2], lab[1])) % 360), 1)}
    if "border" in c:
        out["border"] = round(float(c["border"]), 4)
    if "refs" in c:
        out["presence"] = len(c["refs"])
    return out


def _lhist(lab):
    h, _ = np.histogram(lab[:, 0], bins=10, range=(0, 100))
    return [round(float(x), 4) for x in h / max(1, h.sum())]


def distance(p1: dict, p2: dict) -> float:
    """Earth mover's distance between two palettes, in CIEDE2000: how far each colour's area has to travel to
    become the other palette. Areas matter: a light ground with dark type and a dark ground with light type use
    the same two colours, and are far apart."""
    la, lb = np.array([c["lab"] for c in p1["colors"]]), np.array([c["lab"] for c in p2["colors"]])
    wa = np.array([c["area"] for c in p1["colors"]], float)
    wb = np.array([c["area"] for c in p2["colors"]], float)
    wa, wb = wa / wa.sum(), wb / wb.sum()
    cost = delta_e(la[:, None], lb[None])
    n, m = cost.shape
    a_eq = np.zeros((n + m, n * m))
    for i in range(n):
        a_eq[i, i * m:(i + 1) * m] = 1
    for j in range(m):
        a_eq[n + j, j::m] = 1
    res = linprog(cost.ravel(), A_eq=a_eq, b_eq=np.concatenate([wa, wb]), bounds=(0, None), method="highs")
    return float(res.fun) if res.success else float((cost.min(axis=1) * wa).sum())


def unity(palettes: list[dict], thr: float = 15.0) -> dict:
    """Do the references share one palette? Single-linkage groups of pictures closer than `thr`."""
    n = len(palettes)
    if n < 2:
        return {"groups": [list(range(n))], "unified": True, "distances": []}
    D = np.array([[distance(palettes[i], palettes[j]) if i != j else 0.0 for j in range(n)] for i in range(n)])
    parent = list(range(n))
    find = lambda i: i if parent[i] == i else find(parent[i])  # noqa: E731
    for i in range(n):
        for j in range(i + 1, n):
            if D[i, j] < thr:
                parent[find(j)] = find(i)
    groups = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(i)
    return {"groups": list(groups.values()), "unified": len(groups) == 1, "distances": np.round(D, 1).tolist()}


def opening_ground(rgb: np.ndarray, share: float = 0.85) -> str | None:
    """The colour covering at least `share` of a video's opening frame, or None when the film opens on a picture."""
    lab = rgb_to_lab(_small(rgb).reshape(-1, 3).astype(np.float64))
    med = np.median(lab, axis=0)
    return hex_(lab_to_rgb(med)) if (delta_e(lab, med) < 8).mean() >= share else None


def pooled(palettes: list[dict], ground_hint: str | None = None) -> dict:
    """One palette for the style: every picture weighs the same."""
    cols = []
    for i, p in enumerate(palettes):
        for c in p["colors"]:
            cols.append({"lab": np.array(c["lab"]), "area": c["area"] / len(palettes),
                         "border": c.get("border", 0) / len(palettes), "refs": {i} if c["area"] >= 0.01 else set()})
    cols = sorted(_merge(cols, POOL_MERGE), key=lambda c: -c["area"])
    colors = [_describe(c) for c in cols]
    hist = np.mean([p["luminance_hist"] for p in palettes], axis=0)
    return {"colors": colors, "roles": roles(colors, ground_hint), "luminance_hist": [round(float(x), 4) for x in hist],
            "structure": structure(colors, ground_hint)}


def _ground(colors: list[dict], hint: str | None = None) -> dict:
    if hint:
        lab = rgb_to_lab(np.array([int(hint[i:i + 2], 16) for i in (1, 3, 5)], np.float64))
        near = min(colors, key=lambda c: float(delta_e(np.array(c["lab"]), lab)))
        if float(delta_e(np.array(near["lab"]), lab)) < 10:
            return near
    return max(colors, key=lambda c: (c.get("border", 0), c["area"]))


def roles(colors: list[dict], ground_hint: str | None = None) -> dict:
    if not colors:
        return {}
    ground = _ground(colors, ground_hint)
    rest = [c for c in colors if c is not ground and c["area"] >= 0.003]
    # lightness weighs most (type is thin), area some: a sliver of the darkest overprint is not the ink a whole sea
    # is printed in, and a large surface one step off the ground is not the ink either
    ink = max(rest, key=lambda c: abs(c["lightness"] - ground["lightness"]) * c["area"] ** 0.25, default=None)
    pool = [c for c in colors if c is not ground and c is not ink and c["area"] < 0.15
            and (c["chroma"] >= 20 and c["area"] >= 0.003 or c["chroma"] >= VIVID and c["area"] >= 0.0003)]
    accent = max(pool, key=lambda c: c["chroma"], default=None)
    rgb = lambda c: [int(c["hex"][i:i + 2], 16) for i in (1, 3, 5)]  # noqa: E731
    out = {"ground": ground["hex"]}
    if ink:
        out["ink"] = ink["hex"]
        out["ink_contrast"] = contrast(rgb(ink), rgb(ground))
    if accent:
        out["accent"] = accent["hex"]
        out["accent_contrast"] = contrast(rgb(accent), rgb(ground))
    out["secondary"] = [c["hex"] for c in colors if c["hex"] not in out.values() and c["area"] >= 0.02]
    return out


def structure(colors: list[dict], ground_hint: str | None = None) -> dict:
    """The palette's logic in numbers: how many hues, how light the ground, how saturated the picture."""
    area = np.array([c["area"] for c in colors])
    chromatic = [c for c in colors if c["chroma"] >= 15 and c["area"] >= 0.005]
    hues = sorted({int(c["hue"] // 30) for c in chromatic})
    ground = _ground(colors, ground_hint)
    return {"hue_families": len(hues), "chromatic_colours": len(chromatic),
            "ground": "light" if ground["lightness"] >= 60 else "dark" if ground["lightness"] <= 35 else "mid",
            "ground_lightness": ground["lightness"],
            "mean_chroma": round(float((np.array([c["chroma"] for c in colors]) * area).sum() / area.sum()), 1),
            "saturated_area": round(float(sum(c["area"] for c in colors if c["chroma"] >= 30)), 3),
            "neutral_area": round(float(sum(c["area"] for c in colors if c["chroma"] < 8)), 3)}
