"""Reading time, the ledger check, packing into a library and finding styles."""
from __future__ import annotations

import json
from pathlib import Path

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
