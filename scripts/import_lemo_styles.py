"""Import the style documents of lemo-opuscar into styles/.

  git clone --depth 1 https://github.com/lemomo-ai/lemo-opuscar <dir>
  uv run scripts/import_lemo_styles.py --from <dir>

Only the documents come over: each style's STYLE.md and DEMO.md, and its metadata rewritten as a Moodreel
style.json. The demo sources, the posters and stills, and the upstream toolchain stay upstream; links into a
style's demo/ folder are pinned to the imported commit on GitHub. The documents are MIT (Copyright (c) 2026
LemoLab): the licence is copied to styles/LICENSE-lemo-opuscar and every file says where it came from.

Re-running with a newer checkout replaces the imported styles and leaves Moodreel's own styles alone.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path

REPO = "https://github.com/lemomo-ai/lemo-opuscar"
ROOT = Path(__file__).resolve().parents[1]

# What each style needs beyond flat 2D drawing (Canvas 2D, SVG, a WebGL post pass). A style that needs any of
# these is built in a later phase; the MVP draws the rest. Curated by reading each STYLE.md (§1, §2, §10).
#   painterly       a brush or paint engine: oil, watercolour, ink wash, wax crayon, painted backgrounds
#   3d              a 3D scene: three.js sets, lit models, point clouds, a 3D wireframe projection
#   pixel           pixel art: indexed palettes, dithering, sprite worlds
#   music-led       the score is the engine: picture written to a tempo grid or a cinema accompaniment
#   real-material   built from real footage, photos, scans, imagery or data portals
NEEDS = {
    "impasto": ["painterly"], "watercolor": ["painterly"], "ink-wash": ["painterly"],
    "crayon-book": ["painterly"], "urban-sketch": ["painterly"], "cel-anime-80s": ["painterly"],
    "silent-film": ["painterly", "music-led"],
    "brick-toy": ["3d"], "glass-product": ["3d"], "lowpoly-island": ["3d"], "paper-popup": ["3d"],
    "tilt-shift": ["3d"], "paper-lantern": ["3d"], "backrooms": ["3d"], "hologram-hud": ["3d"],
    "data-physical": ["3d"],
    "pixel-rpg": ["pixel"], "hd-2d": ["pixel", "3d"],
    "rubber-hose": ["music-led"], "game-show": ["music-led"], "microgame": ["music-led"],
    "kino-montage": ["real-material", "music-led"], "city-symphony": ["real-material", "music-led"],
    "caption-news": ["real-material"], "countdown": ["real-material"], "news-package": ["real-material"],
    "newsreel": ["real-material"], "telestrator": ["real-material"], "visual-investigation": ["real-material"],
    "archive-lighttable": ["real-material"], "briefing-board": ["real-material"], "microscope": ["real-material"],
    "satellite-briefing": ["real-material"], "lidar-survey": ["real-material", "3d"],
    "teardown": ["real-material", "3d"], "white-model": ["real-material", "3d"],
}
NEEDS_ZH = {"painterly": "绘画笔触", "3d": "3D", "pixel": "像素", "music-led": "配乐驱动", "real-material": "真实素材"}

LINK = re.compile(r"\]\((demo/[^)\s]*)\)")


def provenance(slug: str, sha: str, kind: str) -> str:
    where = f"`styles/{slug}/{kind}`" if slug != "_template" else f"`styles/_template/{kind}`"
    return (f"> Imported from [lemo-opuscar]({REPO}/tree/{sha}/styles/{slug}) {where} at `{sha[:7]}` "
            f"(MIT, Copyright (c) 2026 LemoLab; see `styles/LICENSE-lemo-opuscar`). Mentions of `demo/` files, "
            f"`core/` tools, `setup.sh` and the library describe upstream's demo and toolchain, which Moodreel does "
            f"not ship; links into `demo/` open the upstream source at that commit. Moodreel re-implements the "
            f"techniques in its own kit.\n")


def adapt(text: str, slug: str, sha: str, kind: str) -> str:
    text = LINK.sub(lambda m: f"]({REPO}/blob/{sha}/styles/{slug}/{m.group(1)})", text)
    lines = text.split("\n")
    title = next((i for i, l in enumerate(lines) if l.startswith("# ")), -1)
    return "\n".join(lines[: title + 1] + ["", provenance(slug, sha, kind).rstrip()] + lines[title + 1:])


def metadata(src: dict, slug: str, sha: str) -> dict:
    needs = NEEDS.get(slug, [])
    return {
        "slug": slug, "name": src["en"], "name_zh": src["cn"],
        "category": src["category_en"], "category_zh": src["category_cn"], "uses": src.get("uses", []),
        "size": "1920x1080", "fps": 24,
        "phase": "later" if needs else "mvp", "needs": needs,
        "demo": {"title": src.get("film"), "line": src.get("line"), "line_zh": src.get("line_cn"),
                 "duration_s": src.get("dur")},
        "source": {"project": "lemo-opuscar", "repository": REPO, "path": f"styles/{slug}", "commit": sha,
                   "license": "MIT", "copyright": "Copyright (c) 2026 LemoLab"},
    }


def index_md(rows: list[dict], sha: str) -> str:
    out = ["# Styles · 风格库", "",
           f"{len(rows)} styles imported from [lemo-opuscar]({REPO}) at `{sha[:7]}` (MIT, Copyright (c) 2026 "
           "LemoLab). Each folder holds the style's `STYLE.md` (its invariants), `DEMO.md` (how the upstream demo "
           "film was made: one example, never a template) and `style.json`.",
           "",
           f"从 lemo-opuscar 导入的 {len(rows)} 套风格。**MVP** 阶段可以直接用代码实现；**later** 需要后期才有的能力"
           "（绘画笔触、3D、像素、配乐驱动、真实素材）。",
           "",
           "Generated by `scripts/import_lemo_styles.py`; do not edit by hand.", ""]
    cats = {}
    for r in rows:
        cats.setdefault((r["category"], r["category_zh"]), []).append(r)
    for (cat, cat_zh), rs in sorted(cats.items()):
        out += [f"## {cat} · {cat_zh}", "", "| Style | 风格 | Folder | Phase | Needs · 需要 |", "|---|---|---|---|---|"]
        for r in sorted(rs, key=lambda r: r["name"]):
            needs = ", ".join(f"{n} {NEEDS_ZH[n]}" for n in r["needs"]) or "—"
            out.append(f"| {r['name']} | {r['name_zh']} | [`{r['slug']}`]({r['slug']}/STYLE.md) | {r['phase']} | {needs} |")
        out.append("")
    mvp = sum(r["phase"] == "mvp" for r in rows)
    out += [f"MVP: {mvp} · later: {len(rows) - mvp}", ""]
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="src", required=True, help="a checkout of lemo-opuscar")
    ap.add_argument("--to", default=str(ROOT / "styles"))
    a = ap.parse_args()
    src, dst = Path(a.src).expanduser().resolve(), Path(a.to)
    sha = subprocess.run(["git", "-C", str(src), "rev-parse", "HEAD"], check=True, capture_output=True,
                         text=True).stdout.strip()
    dst.mkdir(parents=True, exist_ok=True)
    old = json.loads((dst / "index.json").read_text()) if (dst / "index.json").exists() else {"styles": []}
    for r in old["styles"]:                                   # replace what an earlier import brought in
        if r.get("source", {}).get("project") == "lemo-opuscar":
            shutil.rmtree(dst / r["slug"], ignore_errors=True)
    rows = []
    for d in sorted((src / "styles").iterdir()):
        if not (d / "STYLE.md").exists() or d.name.startswith("_"):
            continue
        out = dst / d.name
        out.mkdir(parents=True, exist_ok=True)
        for kind in ("STYLE.md", "DEMO.md"):
            (out / kind).write_text(adapt((d / kind).read_text(encoding="utf-8"), d.name, sha, kind), encoding="utf-8")
        meta = metadata(json.loads((d / "style.json").read_text(encoding="utf-8")), d.name, sha)
        (out / "style.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        rows.append(meta)
    unknown = set(NEEDS) - {r["slug"] for r in rows}
    if unknown:
        raise SystemExit(f"NEEDS names styles that upstream no longer has: {sorted(unknown)}")
    tpl = dst / "_template"
    tpl.mkdir(exist_ok=True)
    for kind in ("STYLE.md", "DEMO.md"):
        (tpl / kind).write_text(adapt((src / "styles" / "_template" / kind).read_text(encoding="utf-8"),
                                      "_template", sha, kind), encoding="utf-8")
    shutil.copyfile(src / "LICENSE", dst / "LICENSE-lemo-opuscar")
    keep = [r for r in old["styles"] if r.get("source", {}).get("project") != "lemo-opuscar"]
    index = {"generated_by": "scripts/import_lemo_styles.py", "lemo_commit": sha,
             "styles": keep + [{k: r[k] for k in ("slug", "name", "name_zh", "category", "category_zh", "phase",
                                                  "needs", "source")} for r in rows]}
    (dst / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    (dst / "README.md").write_text(index_md(rows, sha), encoding="utf-8")
    mvp = sum(r["phase"] == "mvp" for r in rows)
    print(f"imported {len(rows)} styles at {sha[:7]}: {mvp} mvp, {len(rows) - mvp} later -> {dst}")


if __name__ == "__main__":
    main()
