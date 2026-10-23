"""The test-film generator and the scorer."""
from __future__ import annotations

import json

from moodreel.bench import fixtures
from moodreel.bench.motion import aggregate, score


def test_every_fixture_writes_a_page_and_its_truth(tmp_path):
    dirs = fixtures.write(tmp_path)
    assert len(dirs) == len(fixtures.FIXTURES)
    for d in dirs:
        page = (d / "index.html").read_text()
        assert "__SPEC__" not in page and "window.render" in page
        truth = json.loads((d / "truth.json").read_text())
        assert truth["events"] and {e["scope"] for e in truth["events"]} <= {"mvp", "v1"}


def test_truth_marks_unmeasured_kinds_v1():
    truth = fixtures.truth(fixtures.letters())
    scopes = {(e["element"], e["prop"]): e["scope"] for e in truth["events"]}
    assert scopes[("kinetic", "y")] == "v1"          # per-letter text
    assert scopes[("underline", "sx")] == "v1"       # anisotropic scale
    assert scopes[("words", "opacity")] == "mvp"


def test_camera_truth_and_stepping():
    assert any(e["element"] == "camera" and e["prop"] == "zoom" for e in fixtures.truth(fixtures.camera_push())["events"])
    assert fixtures.truth(fixtures.on_twos())["stepping"][0]["on"] == 2


def test_scorer_counts_a_perfect_measurement():
    truth = {"W": 1000, "H": 500, "fps": 30, "transitions": [{"type": "cut", "t": 1.0}],
             "events": [{"element": "a", "shot": "A", "prop": "opacity", "t0": 0.2, "t1": 0.8, "dur": 0.6,
                         "ease": "power2.out", "from": 0, "to": 1, "end_xy": [500, 250], "scope": "mvp"}]}
    prop = {"best": "power2.out", "ease": "power2.out", "equivalent": [], "t0": 0.2, "t1": 0.8, "dur": 0.6,
            "checkpoints": {"t10": 0.22, "t50": 0.32, "t90": 0.56}, "bic_gap": 50, "overshoot": 0.0,
            "from": 0, "to": 1, "delta": 1}
    motion = {"source": {"w": 1000}, "camera": [], "shots": [{"t0": 0, "t1": 1.0}],
              "transitions": [{"type": "cut", "t": 1.0}], "grammar": {"stagger": []},
              "events": [{"id": "e0", "kind": "appear", "box": [450, 230, 100, 40], "props": {"opacity": prop}}]}
    agg = aggregate([score(truth, motion)])
    assert agg["recall"] == 1.0 and agg["spurious"] == 0 and agg["claimed_wrong"] == 0
    assert agg["transitions_found"] == 1
