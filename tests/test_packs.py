"""scripts/packs.py: the library's packs into the repository by category, and back, deleting nothing on the way."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load(monkeypatch, tmp_path):
    monkeypatch.setenv("MOODREEL_HOME", str(tmp_path / "home"))
    monkeypatch.setenv("MOODREEL_PACKS", str(tmp_path / "packs"))
    spec = importlib.util.spec_from_file_location("packs", ROOT / "scripts" / "packs.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _pack(lib: Path, slug="ascii-glitch-launch"):
    d = lib / slug
    (d / "kit" / "fonts").mkdir(parents=True)
    (d / "kit" / "vendor" / "three").mkdir(parents=True)
    (d / "evidence" / "measure").mkdir(parents=True)
    (d / "demo").mkdir()
    for f, text in {"STYLE.md": "# s", "DECISIONS.md": "# d", "styleframe.jpg": "jpg", "demo.mp4": "video",
                    "evidence/LEDGER.md": "| v |", "evidence/intake.json": "{}", "evidence/measure/palette.json": "{}",
                    "kit/tokens.js": "", "kit/motion.js": "", "kit/stage.js": "// shared",
                    "kit/tracker.js": "// The tracker: a word read by a machine. Each glyph boxed.",
                    "kit/glitch.js": "// ASCII Glitch Launch: the style's own core. Its two voices.",
                    "kit/fonts/Inter.woff2": "font", "kit/vendor/three/three.module.js": "three",
                    "demo/main.js": "", "demo/build.sh": "", "demo/index.html": ""}.items():
        (d / f).write_text(text)
    (d / "style.json").write_text(json.dumps({"slug": slug, "name": "ASCII Glitch Launch", "name_zh": "字符故障发布片",
                                              "size": "1920x1080", "fps": 60, "phase": "mvp", "needs": ["3d"],
                                              "created": "2026-10-25"}))
    (lib / "index.json").write_text(json.dumps({"styles": [{"slug": slug, "name": "ASCII Glitch Launch"}]}))
    return d


def test_export_sorts_by_category_and_leaves_renders_and_vendor_out(monkeypatch, tmp_path):
    mod = _load(monkeypatch, tmp_path)
    _pack(tmp_path / "home" / "styles")
    mod.export([])
    dst = tmp_path / "packs" / "information-keynote" / "ascii-glitch-launch"
    assert (dst / "STYLE.md").exists() and (dst / "kit" / "tracker.js").exists() and (dst / "evidence" / "LEDGER.md").exists()
    assert not (dst / "demo.mp4").exists() and not (dst / "kit" / "vendor").exists()
    readme = (dst / "README.md").read_text()
    assert "Rules · 规则" in readme and "Evidence · 证据" in readme and "Demo · 演示片" in readme
    assert "| `kit/tracker.js` | The tracker |" in readme and "| `kit/glitch.js` | the style's own core |" in readme
    assert "`stage.js`" in readme.split("Kit · 代码: shared")[1].split("\n")[0]
    index = (tmp_path / "packs" / "README.md").read_text()
    assert "## Information & Keynote · 信息与发布" in index and "information-keynote/ascii-glitch-launch" in index
    assert json.loads((tmp_path / "home" / "styles" / "ascii-glitch-launch" / "style.json").read_text())["category"] == "information-keynote"


def test_install_registers_and_never_deletes_a_rendered_demo(monkeypatch, tmp_path):
    mod = _load(monkeypatch, tmp_path)
    lib = tmp_path / "home" / "styles"
    _pack(lib)
    mod.export([])
    (tmp_path / "packs" / "information-keynote" / "ascii-glitch-launch" / "STYLE.md").write_text("# s, revised")
    mod.install(["ascii-glitch-launch"])
    installed = lib / "ascii-glitch-launch"
    assert (installed / "demo.mp4").read_text() == "video"                     # kept, though the repo has none
    assert (installed / "STYLE.md").read_text() == "# s, revised" and not (installed / "README.md").exists()
    entry = json.loads((lib / "index.json").read_text())["styles"][0]
    assert entry["slug"] == "ascii-glitch-launch" and entry["size"] == [1920, 1080]


def test_the_style_index_lists_distilled_packs_in_their_categories(monkeypatch, tmp_path):
    mod = _load(monkeypatch, tmp_path)
    rows = [{"slug": "ascii-crt", "name": "ASCII / CRT Terminal", "name_zh": "ASCII / CRT 终端", "category": "Graphic & Type",
             "category_zh": "图形与排版", "phase": "mvp", "needs": []}]
    packs = [{"slug": "signal-plates", "name": "Signal Plates", "name_zh": "信号图版", "category": "graphic-type",
              "phase": "mvp", "needs": ["3d"], "folder": "packs/graphic-type/signal-plates"}]
    md = mod.lemo.index_md(rows, "3961ddb3", packs)
    section = md.split("## Graphic & Type · 图形与排版")[1]
    assert "| [`ascii-crt`](ascii-crt/STYLE.md) | mvp | — | lemo-opuscar |" in section
    assert "[`signal-plates`](../packs/graphic-type/signal-plates/README.md) | mvp | 3d 3D | distilled here · 本仓库蒸馏 |" in section
    assert "distilled here: 1" in md and mod.CATEGORIES["graphic-type"] == "Graphic & Type · 图形与排版"
    assert len(mod.CATEGORIES) == 11
