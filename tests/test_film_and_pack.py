"""Reading time, the ledger check, packing into a library and finding styles."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from moodreel import library
from moodreel.film import film
from moodreel.pack import pack


def _samples(text, t0, t1, step=0.1, box=(100, 100, 600, 160)):
    out, t = [], 0.0
    while t <= t1 + 1.0:
        shown = t0 <= t <= t1
        out.append({"t": round(t, 2), "texts": [{"id": "a", "text": text, "x0": box[0], "y0": box[1], "x1": box[2], "y1": box[3]}]
                    if shown else []})
        t += step
    return out


def test_reading_time_rule():
    assert film.reading_time("hello world") == 1.5 + 10 / 15
    assert abs(film.reading_time("你好世界") - (4 / 4.5 + 1.5)) < 1e-9
    assert film.readtime(_samples("a long enough line", 0.5, 4.0), 1920, 1080, 0.1) == []
    short = film.readtime(_samples("a line that leaves too soon", 0.5, 1.2), 1920, 1080, 0.1)
    assert short and short[0]["needs"] > short[0]["shown"]
    offscreen = film.readtime(_samples("half out of frame", 0.5, 4.0, box=(-300, 100, 200, 160)), 1920, 1080, 0.1)
    assert offscreen == []                                 # never fully inside: never counted as shown


def test_ledger_check_finds_untraced_values():
    md = "## 5. Motion\nEntrances take 0.45 s and overshoot by 12%. Accent #ff3366, ground #f0e8d6.\n"
    ledger = "| enter.duration | 0.45 | observed |\n| overshoot | 0.12 | derived |\n| ground | #f0e8d6 | observed |"
    assert pack.untraced(md, ledger, "") == ["#ff3366"]
    assert pack.sections("## 1. A\n## 2. B\n## 11. C") == [1, 2, 11]


def _project(root: Path) -> Path:
    p = root / "proj"
    (p / "kit").mkdir(parents=True)
    (p / "demo").mkdir()
    (p / "measure").mkdir()
    (p / "evidence").mkdir()
    (p / "STYLE.md").write_text("# Test\n\n" + "".join(f"## {i}. Section\nText.\n\n" for i in range(1, 12)))
    (p / "DECISIONS.md").write_text("# Decisions\n")
    (p / "LEDGER.md").write_text("# Ledger\n")
    (p / "kit" / "tokens.js").write_text("export const SIZE = [1920, 1080];\n")
    (p / "kit" / "motion.js").write_text("export const MOTION = null;\n")
    (p / "demo" / "index.html").write_text("<!doctype html>")
    for f in ("styleframe.jpg", "demo.mp4"):
        (p / f).write_bytes(b"x")
    (p / "measure" / "palette.json").write_text("{}")
    (p / "intake.json").write_text(json.dumps({"default_size": "1920x1080", "refs": [
        {"id": "img01", "kind": "image", "sha256": "ab", "source": "web", "source_path": "/secret/path.png", "w": 10, "h": 10}]}))
    return p


def test_pack_into_a_library(tmp_path, monkeypatch):
    monkeypatch.setenv("MOODREEL_HOME", str(tmp_path / "home"))
    proj = _project(tmp_path)
    taken = pack.pack(proj, "ukiyoe", "Ukiyo-e")
    assert not taken["ok"] and any("taken" in p for p in taken["problems"])
    r = pack.pack(proj, "test-style", "Test Style", "测试风格")
    assert r["ok"], r
    dst = Path(r["path"])
    assert (dst / "STYLE.md").exists() and (dst / "kit" / "tokens.js").exists() and (dst / "evidence" / "LEDGER.md").exists()
    intake = json.loads((dst / "evidence" / "intake.json").read_text())
    assert "source_path" not in intake["refs"][0]          # where the references came from stays on this machine
    assert not (dst / "evidence" / "refs-sheet.jpg").exists()
    found = library.find("测试风格")
    assert found and found["origin"] == "user" and found["slug"] == "test-style"
    assert library.all_styles()[0]["origin"] == "user"     # the user's styles come first


def test_pack_refuses_an_incomplete_project(tmp_path, monkeypatch):
    monkeypatch.setenv("MOODREEL_HOME", str(tmp_path / "home"))
    proj = _project(tmp_path)
    (proj / "STYLE.md").write_text("# Test\n## 1. Only one section\n")
    (proj / "demo.mp4").unlink()
    r = pack.check(proj, "x-style", "X Style")
    assert not r["ok"] and any("sections" in p for p in r["problems"]) and any("demo" in p for p in r["problems"])


def test_pack_reads_the_demo_for_frame_rate_and_needs_and_leaves_renders_out(tmp_path, monkeypatch):
    monkeypatch.setenv("MOODREEL_HOME", str(tmp_path / "home"))
    proj = _project(tmp_path)
    assert pack.traits(proj) == (30, [])
    (proj / "kit" / "signal.js").write_text("import { gpu } from './gl.js';\n")       # the style draws on the GPU
    (proj / "demo" / "film.json").write_text(json.dumps({"name": "demo", "fps": 60}))
    (proj / "demo" / "score.json").write_text("{}")                                   # cut to its own score
    (proj / "demo" / "demo.mp4").write_bytes(b"x" * 10)                              # a render left in the source
    (proj / "demo" / "out").mkdir()
    (proj / "demo" / "out" / "score.wav").write_bytes(b"x")
    assert pack.traits(proj) == (60, ["3d", "music-led"])
    r = pack.pack(proj, "gpu-style", "GPU Style")
    assert r["ok"], r
    dst = Path(r["path"])
    meta = json.loads((dst / "style.json").read_text())
    assert meta["fps"] == 60 and meta["needs"] == ["3d", "music-led"]
    assert (dst / "demo" / "film.json").exists() and not (dst / "demo" / "demo.mp4").exists() and not (dst / "demo" / "out").exists()


def test_a_new_film_takes_the_styles_frame_rate(tmp_path, monkeypatch):
    monkeypatch.setenv("MOODREEL_HOME", str(tmp_path / "home"))
    proj = _project(tmp_path)
    (proj / "demo" / "film.json").write_text(json.dumps({"name": "demo", "fps": 60}))
    assert pack.pack(proj, "fast-style", "Fast Style")["ok"]
    d = film.new("a", "fast-style", tmp_path / "films")
    assert json.loads((d / "film.json").read_text())["fps"] == 60
    d = film.new("b", "fast-style", tmp_path / "films", fps=24)
    assert json.loads((d / "film.json").read_text())["fps"] == 24
    assert "OFL" not in (d / "CREDITS").read_text()


def test_a_film_lists_the_fonts_its_style_ships(tmp_path, monkeypatch):
    monkeypatch.setenv("MOODREEL_HOME", str(tmp_path / "home"))
    proj = _project(tmp_path)
    (proj / "kit" / "fonts").mkdir()
    (proj / "kit" / "fonts" / "OFL.txt").write_text("Copyright 2020 The Archivo Project Authors\n")
    assert pack.pack(proj, "typed-style", "Typed Style")["ok"]
    d = film.new("c", "typed-style", tmp_path / "films")
    assert (d / "kit" / "fonts" / "OFL.txt").exists() and "kit/fonts/OFL.txt" in (d / "CREDITS").read_text()


def test_a_film_credits_each_familys_licence_when_its_style_ships_one_per_family(tmp_path, monkeypatch):
    monkeypatch.setenv("MOODREEL_HOME", str(tmp_path / "home"))
    proj = _project(tmp_path)
    (proj / "kit" / "fonts").mkdir()
    for fam in ("NotoSerifSC", "LXGWWenKai"):
        (proj / "kit" / "fonts" / f"OFL-{fam}.txt").write_text(f"Copyright the {fam} authors\n")
    assert pack.pack(proj, "ink-style", "Ink Style")["ok"]
    credits = (film.new("d", "ink-style", tmp_path / "films") / "CREDITS").read_text()
    assert "licence in kit/fonts/OFL-LXGWWenKai.txt, kit/fonts/OFL-NotoSerifSC.txt\n" in credits


REPO = Path(__file__).resolve().parents[1]
needs_three = pytest.mark.skipif(not (REPO / "node_modules" / "three" / "build" / "three.module.js").exists(),
                                 reason="needs npm install")


def test_a_new_film_leaves_kit_3dcv_out_unless_asked(tmp_path):
    d = film.new("plain", "swiss-motion", tmp_path / "films", duration=2, size="320x180")
    assert not (d / "kit" / "3dcv").exists() and (d / "kit" / "three.js").exists()   # the rest of the kit as before
    assert "kit/3dcv" not in (d / "CREDITS").read_text()
    with pytest.raises(SystemExit):
        film.new("odd", "swiss-motion", tmp_path / "films", add=("nothing",))


@needs_three
def test_with_3dcv_a_film_gets_the_folder_three_js_and_the_credit(tmp_path):
    d = film.new("cv", "swiss-motion", tmp_path / "films", duration=2, size="320x180", add=("3dcv",))
    for f in (REPO / "kit" / "3dcv").iterdir():
        kept = d / "kit" / "3dcv" / f.name
        assert not kept.exists() if f.name == "README.md" else kept.read_bytes() == f.read_bytes()
    assert (d / "kit" / "vendor" / "three" / "three.module.js").exists()
    credits = (d / "CREDITS").read_text()
    line = next(ln for ln in credits.splitlines() if "kit/3dcv" in ln)
    assert "CC BY-NC-SA 4.0" in line and "non-commercial" in line and "three.js" in credits


@needs_three
def test_a_film_that_uses_only_kit_3dcv_gets_three_js_back(tmp_path):
    d = film.new("cv", "swiss-motion", tmp_path / "films", duration=2, size="320x180", add=("3dcv",))
    (d / "main.js").write_text("import * as cv from './kit/3dcv/stage.js';\n")      # kit/three.js named nowhere
    shutil.rmtree(d / "kit" / "vendor")
    film._vendored(d)
    assert (d / "kit" / "vendor" / "three" / "three.module.js").exists()


def test_pack_keeps_the_demos_kit_link_and_its_three_js(tmp_path, monkeypatch):
    monkeypatch.setenv("MOODREEL_HOME", str(tmp_path / "home"))
    proj = _project(tmp_path)
    (proj / "kit" / "vendor" / "three").mkdir(parents=True)
    (proj / "kit" / "vendor" / "three" / "three.module.js").write_text("export {};\n")
    (proj / "demo" / "kit").symlink_to("../kit")                                     # the demo draws with the style's kit
    (proj / "demo" / "review").mkdir()                                               # a build's leftovers
    (proj / "demo" / "deliver.log").write_text("log")
    (proj / "demo" / "poster.jpg").write_bytes(b"x")
    shared = tmp_path / "shared"                                                     # a link out of the project
    shared.mkdir()
    (shared / "notes.txt").write_text("notes")
    (proj / "demo" / "shared").symlink_to(shared)
    r = pack.pack(proj, "linked-style", "Linked Style")
    assert r["ok"], r
    demo = Path(r["path"]) / "demo"
    assert (demo / "kit").is_symlink() and (demo / "kit" / "vendor" / "three" / "three.module.js").exists()
    assert not (demo / "shared").is_symlink() and (demo / "shared" / "notes.txt").read_text() == "notes"
    assert not any((demo / n).exists() for n in ("review", "deliver.log", "poster.jpg"))


def test_pack_keeps_three_js_in_a_demos_own_kit(tmp_path, monkeypatch):
    monkeypatch.setenv("MOODREEL_HOME", str(tmp_path / "home"))
    proj = _project(tmp_path)
    (proj / "demo" / "kit" / "vendor" / "three").mkdir(parents=True)                # a demo with its own copy of the kit
    (proj / "demo" / "kit" / "vendor" / "three" / "three.module.js").write_text("export {};\n")
    (proj / "demo" / "vendor").mkdir()                                               # a vendor folder outside a kit
    (proj / "demo" / "vendor" / "big.js").write_text("x")
    r = pack.pack(proj, "own-kit-style", "Own Kit Style")
    assert r["ok"], r
    demo = Path(r["path"]) / "demo"
    assert (demo / "kit" / "vendor" / "three" / "three.module.js").exists() and not (demo / "vendor").exists()
