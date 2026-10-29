"""The distilled style packs, kept in the repository and sorted by category.

  python scripts/packs.py export [slug ...]    the library's packs (~/.moodreel/styles) -> packs/<category>/<slug>/
  python scripts/packs.py install [slug ...]   packs/ -> the library, registered in its index.json

A pack keeps the layout the tools read (STYLE.md, DECISIONS.md, style.json, styleframe.jpg, evidence/, kit/, demo/),
so a copy installs as it is. Left out of the repository: demo.mp4 (rebuilt by `sh demo/build.sh`; GitHub refuses files
over 100 MB), kit/vendor/ (three.js, from `npm install`) and the fonts a pack fetches itself (named in its
kit/fonts/fetch.sh and ignored by its kit/fonts/.gitignore). Each pack gets a README.md that sorts its contents by
kind; packs/README.md lists the packs by category (the eleven of styles/index.json), and styles/README.md, the
one index of every style, lists them beside the imported ones.
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from moodreel import library  # noqa: E402

_spec = importlib.util.spec_from_file_location("import_lemo_styles", REPO / "scripts" / "import_lemo_styles.py")
lemo = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(lemo)

PACKS = Path(os.environ.get("MOODREEL_PACKS", REPO / "packs"))           # the repository's packs/ (a test points it elsewhere)
# the library's categories (styles/index.json), by folder name: "graphic-type" -> "Graphic & Type · 图形与排版"
CATEGORIES = dict(sorted({lemo.slugify(s["category"]): f"{s['category']} · {s['category_zh']}"
                          for s in json.loads((REPO / "styles" / "index.json").read_text())["styles"] if "category" in s}.items()))
DEFAULT = {"signal-plates": "graphic-type", "ascii-glitch-launch": "information-keynote",   # until style.json says
           "ink-chronicle": "east-asian-traditions"}
SKIP = {"demo.mp4", "vendor", ".DS_Store", "out", "stills"}
SHARED = {p.name for p in (REPO / "kit").glob("*.js")}                      # the kit every film gets


def _copy(src: Path, dst: Path) -> None:
    """Copy over what is there, deleting nothing (an installed pack keeps its rendered demo.mp4)."""
    shutil.copytree(src, dst, ignore=lambda d, names: [n for n in names if n in SKIP], dirs_exist_ok=True)


def _first_line(f: Path, style: str = "") -> str:
    """What a module says it is: the first sentence of its header comment, cut to a phrase (after "<style> ...:" when
    the header opens with the style's name, before the first colon otherwise)."""
    words = []
    for line in f.read_text(errors="ignore").splitlines():
        if not line.strip().startswith("//"):
            break
        words.append(line.strip().lstrip("/").strip())
    text = " ".join(w for w in words if w).split(". ")[0].rstrip(".")
    head, _, tail = text.partition(": ")
    text = tail if tail and style and head.startswith(style) else head
    return text if len(text) <= 90 else text[:90].rsplit(", ", 1)[0]


def fetched(fonts: Path) -> list[str]:
    """The fonts a pack fetches rather than keeps (too large for the repository): one `get <file> <url> <sha256>` line
    each in its kit/fonts/fetch.sh."""
    script = fonts / "fetch.sh"
    return re.findall(r"^get (\S+) ", script.read_text(), re.M) if script.exists() else []


def readme(pack: Path, meta: dict) -> str:
    kit = sorted(pack.glob("kit/*.js"))
    own = [f for f in kit if f.name not in SHARED and f.name not in ("tokens.js", "motion.js")]
    shared = [f.name for f in kit if f.name in SHARED]
    fonts = sorted(p.name for p in (pack / "kit" / "fonts").glob("*") if p.suffix in (".ttf", ".otf", ".woff2", ".woff"))
    licences = sorted(p.name for p in (pack / "kit" / "fonts").glob("OFL*.txt")) or ["OFL.txt"]
    away = fetched(pack / "kit" / "fonts")
    fetch = f"; {', '.join(f'`{n}`' for n in away)}: not in the repository, `sh kit/fonts/fetch.sh` downloads them" if away else ""
    demo = sorted(p.name for p in (pack / "demo").iterdir() if p.is_file()) if (pack / "demo").exists() else []
    measures = sorted(p.name for p in (pack / "evidence" / "measure").glob("*.json"))
    rows = [
        ("Rules · 规则", "`STYLE.md`", "the style prompt: essence, materials, colour, type, motion, camera, sound, moves, pitfalls, engine, variation"),
        ("", "`DECISIONS.md`", "the choices the measurements could not make, approved at gate 1"),
        ("", "`style.json`", f"slug, names, size {meta.get('size')}, {meta.get('fps')} fps, needs: {', '.join(meta.get('needs', [])) or '—'}"),
        ("Evidence · 证据", "`evidence/LEDGER.md`", "every number in STYLE.md with its basis (observed, derived, inferred) and source"),
        ("", "`evidence/intake.json`", "the references: kind, size, licence source, checksum (the files stay with their owner)"),
        ("", f"`evidence/measure/` ({len(measures)})", ", ".join(m.removesuffix(".json") for m in measures)),
    ]
    if (pack / "evidence" / "refs-sheet.jpg").exists():
        rows.append(("", "`evidence/refs-sheet.jpg`", "the references, one sheet (own work, so it may travel)"))
    rows += [("Kit · 代码: the style's own", f"`kit/{f.name}`", _first_line(f, meta["name"])) for f in own]
    rows += [
        ("Kit · 代码: measured", "`kit/tokens.js`, `kit/motion.js`", "palette, type tiers, layout, texture; durations, eases, stagger, beat"),
        ("Kit · 代码: shared", ", ".join(f"`{n}`" for n in shared), "the kit every film gets (stage, core, eases, text, texture, ...)"),
        ("Kit · 代码: fonts", ", ".join(f"`kit/fonts/{n}`" for n in fonts), "with " + ", ".join(f"`kit/fonts/{n}`" for n in licences) + fetch),
        ("Demo · 演示片", "`demo/`", "the demo film's source: " + ", ".join(f"`{n}`" for n in demo)),
        ("", "`demo.mp4`", "not in the repository: rebuild with `sh demo/build.sh` (it writes `demo.mp4` beside `demo/`)"),
        ("", "`styleframe.jpg`", "the style frame approved at gate 2 (frame-check compares films with it)"),
    ]
    lines = [f"# {meta['name']} · {meta.get('name_zh', '')}", "",
             f"{CATEGORIES.get(meta.get('category'), meta.get('category', ''))}. Distilled with Moodreel on {meta.get('created')}; "
             f"install with `python scripts/packs.py install {meta['slug']}`, then `moodreel film new <name> --style {meta['slug']}`.",
             "", "| Kind · 类别 | Files | What it is |", "|---|---|---|"]
    lines += [f"| {a} | {b} | {c} |" for a, b, c in rows]
    return "\n".join(lines) + "\n"


def index_readme(packs: list[tuple[str, dict]]) -> str:
    lines = ["# Packs · 风格包", "",
             "The styles distilled here, each a complete pack (rules, evidence, kit, demo source), sorted by the categories of",
             "`styles/README.md`. `python scripts/packs.py install` puts them in the style library (`~/.moodreel/styles`);",
             "`export` brings the library's packs back here. Demo films are rebuilt from source (`sh demo/build.sh`).",
             "", "这里是在本仓库蒸馏出的风格包（规则、证据、代码、演示片源码），按 `styles/README.md` 的分类存放。", ""]
    for cat, title in CATEGORIES.items():
        rows = [m for c, m in packs if c == cat]
        if not rows:
            continue
        lines += [f"## {title}", "", "| Style | 风格 | Folder | Needs · 需要 |", "|---|---|---|---|"]
        lines += [f"| {m['name']} | {m.get('name_zh', '')} | [`{cat}/{m['slug']}`]({cat}/{m['slug']}/README.md) | "
                  f"{', '.join(m.get('needs', [])) or '—'} |" for m in rows]
        lines.append("")
    return "\n".join(lines)


def export(slugs: list[str]) -> None:
    lib = library.user_dir()
    names = slugs or [s["slug"] for s in library._index(lib, "user")]
    for slug in names:
        src = lib / slug
        meta = json.loads((src / "style.json").read_text())
        meta.setdefault("category", DEFAULT.get(slug, "uncategorised"))
        (src / "style.json").write_text(json.dumps(meta, indent=1, ensure_ascii=False) + "\n")   # the library learns it too
        dst = PACKS / meta["category"] / slug
        _copy(src, dst)
        (dst / "README.md").write_text(readme(dst, meta))
        print(f"{slug} -> {dst}")
    packs = sorted(((p.parent.parent.name, json.loads(p.read_text())) for p in PACKS.glob("*/*/style.json")),
                   key=lambda x: x[1]["name"])
    (PACKS / "README.md").write_text(index_readme(packs))
    if PACKS == REPO / "packs":                                     # and the one index of every style, by category
        lemo.write_readme(REPO / "styles", PACKS)


def install(slugs: list[str]) -> None:
    for meta_file in sorted(PACKS.glob("*/*/style.json")):
        meta = json.loads(meta_file.read_text())
        if slugs and meta["slug"] not in slugs:
            continue
        dst = library.user_dir() / meta["slug"]
        _copy(meta_file.parent, dst)
        (dst / "README.md").unlink(missing_ok=True)
        library.register({k: meta[k] for k in ("slug", "name", "name_zh", "phase", "needs", "source") if k in meta}
                         | {"size": [int(v) for v in meta["size"].split("x")]})
        missing = [n for n in fetched(dst / "kit" / "fonts") if not (dst / "kit" / "fonts" / n).exists()]
        print(f"{meta['slug']} -> {dst}" + ("" if (dst / "demo.mp4").exists() else "  (no demo.mp4: sh demo/build.sh)")
              + (f"  (no {', '.join(missing)}: sh kit/fonts/fetch.sh)" if missing else ""))


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in ("export", "install"):
        raise SystemExit(__doc__)
    (export if sys.argv[1] == "export" else install)(sys.argv[2:])
