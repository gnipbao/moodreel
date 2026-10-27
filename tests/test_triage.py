"""`moodreel triage` (opt-in Jev ranking of a pass's windows), offline: a fake caller stands in for TypeSafe."""
from __future__ import annotations

import json

import pytest

from moodreel.check import triage


def _cmp():
    rows = [{"window": "night grass", "t0": 50.0, "t1": 52.2, "structure": 0.18, "detail": 0.56, "tone": 24.2, "flow": 0.29,
             "speed": 2.74, "grain": [0.0, 0.2], "score": 0.30, "problems": ["a different picture"]},
            {"window": "typing", "t0": 0.0, "t1": 2.7, "structure": 0.87, "detail": 0.93, "tone": 2.5, "flow": None,
             "speed": None, "score": 0.90, "problems": []}]
    return {"windows": rows, "median": {"score": 0.6}}


def _cam():
    return {"windows": [{"window": "night grass", "ref": {"x": 92, "y": 90, "push": -15.2, "roll": -2.7},
                         "rem": {"x": 4, "y": 1, "push": 3.4, "roll": 0}, "off": ["doesn't pull out"]}]}


def _answer(ok, sev, fix):
    probs = {k: (0.8 if k == fix else 0.05) for k in triage.FIXES}
    return {"model": "jev-1.13.0", "answers": {"acceptable": {"type": "noul", "noul": ok},
            "fix": {"type": "choice", "choice": fix, "probabilities": probs, "confidence": 0.8},
            "severity": {"type": "score", "score": sev, "confidence": 0.7}}, "usage": {"input_tokens": 1000, "output_tokens": 80}}


def _fake(calls):
    def caller(req, key):
        calls.append(req)
        name = req["state"]["window"]["window"]
        return _answer(0.1, 2.9, "camera") if name == "night grass" else _answer(0.7, 0.8, "light")
    return caller


def test_requests_carry_numbers_and_the_film_but_no_paths():
    req = triage.request_for(_cmp()["windows"][0], _cam()["windows"][0], film=triage.film_context(_cmp(), _cam()))
    s = req["state"]
    assert s["window"]["measures"]["structure"] == 0.18 and s["window"]["camera"]["off"] == ["doesn't pull out"]
    assert s["film"]["windows"] == 2 and s["film"]["camera_windows_matching"] == 0
    assert set(req["questions"]) == {"acceptable", "fix", "severity"} and set(req["questions"]["fix"]["criteria"]) == set(triage.FIXES)
    assert "/" not in json.dumps(s["window"])                     # no file paths go out


def test_without_permission_only_the_preview_is_written(tmp_path):
    calls = []
    res = triage.triage(_cmp(), _cam(), allow=False, cache=tmp_path, caller=_fake(calls))
    assert res["status"] == "preview" and calls == []
    preview = json.loads((tmp_path / "transfer-preview.json").read_text())
    assert preview["destination"] == triage.ENDPOINT and preview["requests"] == 2 and "no frames" in preview["data"]


def test_windows_are_ranked_and_answers_cached(tmp_path, monkeypatch):
    monkeypatch.setenv("TYPESAFE_API_KEY", "test-key")
    calls = []
    res = triage.triage(_cmp(), _cam(), allow=True, cache=tmp_path, caller=_fake(calls))
    assert res["status"] == "complete" and len(calls) == 2
    assert [r["window"] for r in res["windows"]] == ["night grass", "typing"]       # the worse window first
    top = res["windows"][0]
    assert top["fix"] == "camera" and top["priority"] > res["windows"][1]["priority"]
    again = triage.triage(_cmp(), _cam(), allow=False, cache=tmp_path, caller=_fake(calls))
    assert again["status"] == "complete" and len(calls) == 2      # all cached: no call, no permission needed
    assert "night grass" in triage.report(again)


def test_bad_answers_are_refused_not_kept(tmp_path, monkeypatch):
    monkeypatch.setenv("TYPESAFE_API_KEY", "test-key")
    def bad(req, key):
        a = _answer(0.2, 2.0, "camera")
        a["answers"]["fix"]["probabilities"]["light"] = 0.9           # no longer sums to one
        return a
    res = triage.triage(_cmp(), None, allow=True, cache=tmp_path, caller=bad)
    assert res["status"] == "partial" and len(res["errors"]) == 2 and res["windows"] == []
    assert not [p for p in tmp_path.glob("*.json") if p.name != "transfer-preview.json"]   # nothing cached
    with pytest.raises(triage.TriageError):
        triage.parse({"questions": {"acceptable": {"type": "noul"}}}, {"answers": {"acceptable": {"type": "score"}}})


def test_a_failed_call_is_reported_not_guessed(tmp_path, monkeypatch):
    monkeypatch.setenv("TYPESAFE_API_KEY", "test-key")
    def down(req, key):
        raise triage.TriageError("Jev could not be reached")
    res = triage.triage(_cmp(), None, allow=True, cache=tmp_path, caller=down)
    assert res["status"] == "partial" and {e["window"] for e in res["errors"]} == {"night grass", "typing"}
    assert "failed: night grass" in triage.report(res)


def test_the_key_is_required_and_never_sent_in_the_body(tmp_path, monkeypatch):
    monkeypatch.delenv("TYPESAFE_API_KEY", raising=False)
    with pytest.raises(triage.TriageError, match="TYPESAFE_API_KEY"):
        triage.triage(_cmp(), None, allow=True, cache=tmp_path, caller=_fake([]))
    req = triage.request_for(_cmp()["windows"][0], None)
    req["state"]["window"]["window"] = "leaked sk-123"
    with pytest.raises(triage.TriageError, match="refusing"):
        triage.call(req, "sk-123", opener=object())
