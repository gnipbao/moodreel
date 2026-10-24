"""`moodreel frame-check <project> <still>...`: does a style frame look like the references?

Scored on what was measured from the references: palette coverage (the references' colours that cover at least
3 % of the picture should each have a near match, CIEDE2000 <= 6), off-palette area (colours far from every
reference colour, CIEDE2000 > 12), the spread of lightness (earth mover's distance between L* histograms) and the
surface (grain, vignette, edge sharpness against the references' range) and, when the references were measured with
style embeddings (`moodreel csd setup`), the style itself: the still's CSD similarity to the references' centre,
against the floor measure set from how well the references agree with each other. A side-by-side sheet goes with it:
the numbers say where to look, the director judges what it means.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image

from .. import sheet
from ..intake import samples
from ..measure import palette, texture
from ..measure.color import delta_e

LIMITS = {"coverage": 0.8, "off_palette": 0.05, "lightness_emd": 0.15}


def _emd(h1, h2):
    return float(np.abs(np.cumsum(np.asarray(h1) - np.asarray(h2))).sum() / len(h1))


REL = {"grain": 0.2, "vignette": 0.3, "edge_sharpness": 0.08}      # tolerance as a share of the reference value
ABS = {"grain": 0.6, "vignette": 0.03, "edge_sharpness": 0.03}     # and never tighter than this


def _surface(t, ref):
    out = {}
    for k in ("grain", "vignette", "edge_sharpness"):
        v, rng = t.get(k), ref.get(f"{k}_range")
        if v is None or rng is None:
            out[k] = {"value": v, "refs": rng, "ok": None}
            continue
        lo, hi = rng
        pad = max(0.25 * (hi - lo), REL[k] * abs((lo + hi) / 2), ABS[k])
        ok = lo - pad <= v <= hi + pad
        if k == "grain" and v < 2.5 and hi < 2.5:     # none and fine grain both read as clean: compression, not a look
            ok = True
        out[k] = {"value": v, "refs": rng, "ok": bool(ok)}
    return out


def measure_dir(root: Path) -> Path:
    """A project keeps its measurements in measure/, a packed style in evidence/measure/."""
    root = Path(root)
    return root / "measure" if (root / "measure").is_dir() else root / "evidence" / "measure"


def check(project: Path, stills: list[Path], out: Path | None = None) -> dict:
    """project: a project or a packed style. out: where results and sheets go (default: the project's own)."""
    project = Path(project)
    mdir = measure_dir(project)
    pal = json.loads((mdir / "palette.json").read_text())
    tex = json.loads((mdir / "texture.json").read_text())
    ref_cols = [c for c in pal["colors"] if c["area"] >= 0.005]
    ref_lab = np.array([c["lab"] for c in ref_cols])
    if (project / "refs").is_dir():
        intake = json.loads((project / "intake.json").read_text())
        refs = [samples(it, project, 1)[0] for it in intake["refs"]][:3]
    else:                                              # a packed style keeps no references: show its style frame
        refs = [np.asarray(Image.open(project / "styleframe.jpg").convert("RGB"))] if (project / "styleframe.jpg").exists() else []
    style = json.loads((mdir / "style.json").read_text()) if (mdir / "style.json").exists() else None
    from ..measure import csd
    styles = csd.score([np.asarray(Image.open(p).convert("RGB")) for p in stills], style) if style and csd.ready() else None
    sheets, results_dir = (Path(out), Path(out)) if out else (project / "evidence", mdir)
    sheets.mkdir(parents=True, exist_ok=True)
    results = []
    for i, path in enumerate(stills):
        rgb = np.asarray(Image.open(path).convert("RGB"))
        p = palette.image_palette(rgb)
        cols = [c for c in p["colors"] if c["area"] >= 0.005]
        lab = np.array([c["lab"] for c in cols])
        d_ref = delta_e(ref_lab[:, None], lab[None]).min(axis=1)            # each reference colour -> ours
        big = np.array([c["area"] >= 0.03 for c in ref_cols])
        w = np.array([c["area"] for c in ref_cols])
        coverage = float((w * (d_ref <= 6) * big).sum() / max((w * big).sum(), 1e-9))
        d_ours = delta_e(lab[:, None], ref_lab[None]).min(axis=1)            # each of our colours -> references
        off = float(sum(c["area"] for c, d in zip(cols, d_ours) if d > 12))
        emd = _emd(p["luminance_hist"], pal["luminance_hist"])
        t = texture.texture(rgb, pal["roles"]["ground"])
        surf = _surface(t, tex)
        missing = [c["hex"] for c, d, b in zip(ref_cols, d_ref, big) if b and d > 6]
        extra = [c["hex"] for c, d in zip(cols, d_ours) if d > 12 and c["area"] >= 0.01]
        st = styles[i] if styles else {"ok": None, "note": "references measured without style embeddings" if not style
                                       else "style embeddings not set up here (moodreel csd setup)"}
        ok = (coverage >= LIMITS["coverage"] and off <= LIMITS["off_palette"] and emd <= LIMITS["lightness_emd"]
              and all(v["ok"] is not False for v in surf.values()) and st["ok"] is not False)
        sheet_path = sheets / f"frame-check-{i + 1:02d}-{Path(path).stem}.jpg"
        sheet.side_by_side(rgb, refs or [rgb], sheet_path)
        results.append({"still": str(path), "pass": ok, "coverage": round(coverage, 3), "missing_colours": missing,
                        "off_palette": round(off, 3), "extra_colours": extra, "lightness_emd": round(emd, 3),
                        "surface": surf, "style": st, "sheet": str(sheet_path)})
    res = {"limits": LIMITS, "stills": results}
    (results_dir / "frame-check.json").write_text(json.dumps(res, indent=1))
    return res
