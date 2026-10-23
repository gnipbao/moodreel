"""The JS kit agrees with the Python measurement; kit generation and the motion claims."""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest

from moodreel.check.motion import claims
from moodreel.motion import eases
from moodreel.pack import kit

REPO = Path(__file__).resolve().parents[1]


@pytest.mark.skipif(shutil.which("node") is None, reason="needs node")
def test_js_eases_match_python(tmp_path):
    curves = ["bezier(0.7,0,0.2,1)", "bezier(0.727,-0.033,0.18,1.039)"]   # a style's own curve, as the kit writes it
    names = [n for n, _ in eases.candidates()] + ["back.inOut(1.7)"] + curves
    u = np.linspace(0, 1, 21).tolist()
    script = tmp_path / "eases.mjs"
    script.write_text(f"import {{ ease }} from '{(REPO / 'kit' / 'eases.js').as_uri()}';\n"
                      f"const names = {json.dumps(names)}, u = {json.dumps(u)};\n"
                      "console.log(JSON.stringify(Object.fromEntries(names.map(n => [n, u.map(ease(n))]))));\n")
    out = json.loads(subprocess.run(["node", str(script)], capture_output=True, text=True, check=True).stdout)
    for n in names:                                   # beziers are solved numerically on both sides
        assert np.allclose(out[n], eases.get(n)(np.array(u)), atol=2e-3 if n in curves else 1e-9), n


def test_back_for_matches_the_overshoot():
    name = kit._back_for(0.10)
    assert name.startswith("back.out(") and abs(eases.get(name)(np.linspace(0, 1, 2001)).max() - 1.10) < 0.01


def _grammar(enter=0.5, cls="out", overshoot=0.0, shots=3, stagger=0.1):
    role = {"count": 6, "duration_s": {"median": enter, "p25": enter * 0.9, "p75": enter * 1.1},
            "classes": {cls: 5, "inOut": 1}, "eases": {"power3.out": 5}, "overshoot_share": overshoot,
            "overshoot": {"median": 0.1, "p25": 0.08, "p75": 0.12} if overshoot else None}
    return {"entrance": role, "exit": None, "move": None, "hold_s": {"median": 0.4}, "motion_density": 0.4,
            "stagger": [{"interval_s": stagger, "order": "left-to-right", "count": 4}] if stagger else [],
            "shots": {"count": shots, "length_s": {"median": 2.0}, "cuts": shots - 1, "dissolves": 0, "dips": 0},
            "stepping": {"on": 1}}


def test_claims_pass_on_the_same_grammar_and_fail_on_another():
    ref = _grammar()
    same = claims(ref, _grammar())
    assert all(c["result"] == "pass" for c in same)
    other = claims(ref, _grammar(enter=0.25, cls="inOut", stagger=0.3))
    failed = {c["id"] for c in other if c["result"] == "fail"}
    assert {"entrance.duration", "entrance.ease_class", "stagger"} <= failed


def test_motion_tokens_from_a_grammar():
    mt = kit.motion_tokens(_grammar(overshoot=0.6))
    assert mt["enter"]["ease"].startswith("back.out(") and mt["stagger"]["interval"] == 0.1
    assert mt["enter"]["duration"] == 0.5 and mt["on"] == 1


def test_an_ease_read_once_or_never_is_left_to_the_director():
    g = _grammar()
    g["entrance"] = {**g["entrance"], "claimed": 1, "classes": {"in": 1}, "eases": {"expo.in": 1}}
    mt = kit.motion_tokens(g)
    assert mt["enter"]["ease"] is None and mt["enter"]["duration"] == 0.5 and "unread" in mt["enter"]
    g["entrance"]["claimed"] = 5
    assert kit.motion_tokens(g)["enter"]["ease"] == "expo.in"
