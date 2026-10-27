"""`moodreel look` and `moodreel track` (opt-in Jev vision), offline: a fake caller stands in for TypeSafe and the frames
are tagged bytes, so the tests know which film each image came from."""
from __future__ import annotations

import base64
import json

import pytest

from moodreel.check import look
from moodreel.check.triage import TriageError

SPEC = {"subjects": {"critter": "the small orange box-shaped character", "keyboard": "the whole keyboard"},
        "checks": {"legends": {"type": "noul", "instructions": "The keycaps have printed legends."},
                   "face": {"type": "choice", "instructions": "What face?", "criteria": {"smile": "^ ^", "slits": "| |"}}},
        "windows": {"*": {"subjects": ["critter"], "checks": []},
                    "keys": {"subjects": ["critter", "keyboard"], "checks": ["legends", "face"]}}}
SHOTS = [(0.0, 2.0, "keys"), (2.0, 4.0, "world")]


def grab(video, t):
    return f"{video}@{t:.3f}".encode()                    # stands in for a JPEG: tells the fake which film it is


def _film(req):
    return [base64.b64decode(a["data_base64"]).decode().split("@")[0] for a in req["assets"].values()]


def fake(calls, bad=None):
    """The reference: critter at the centre, legends, smiling. The remake: critter 0.1 to the right, no legends, slits."""
    def caller(req, key):
        calls.append(req)
        films = _film(req)
        ans = {}
        for k, q in req["questions"].items():
            rem = films == ["rem.mp4"]
            if q["type"] == "box":
                x = 0.5 + (0.1 if rem else 0.0)
                ans[k] = {"type": "box", "box": {"left": x - 0.1, "right": x + 0.1, "top": 0.4, "bottom": 0.6}, "confidence": 0.9}
            elif q["type"] == "noul":
                v = (0.1 if rem else 0.9) if k == "chk_legends" else 0.2 if k == "same_shot" else 0.95
                ans[k] = {"type": "noul", "noul": v}
            elif q["type"] == "choice":
                opts = list(q["criteria"])
                top = ("slits" if rem else "smile") if k == "chk_face" else opts[0]
                p = {o: (0.9 if o == top else 0.1 / (len(opts) - 1)) for o in opts}
                ans[k] = {"type": "choice", "choice": top, "probabilities": p, "confidence": 0.9}
            elif q["type"] == "score":
                ans[k] = {"type": "score", "score": 1.0 if films[0] == "ref.mp4" else 0.0, "confidence": 0.8}
        if bad:
            bad(ans)
        return {"model": "jev-1.14.0", "answers": ans, "usage": {"input_tokens": 2800, "output_tokens": 90}}
    return caller


def test_without_permission_only_the_image_preview_is_written(tmp_path):
    calls = []
    res = look.look("ref.mp4", "rem.mp4", SHOTS, SPEC, samples=2, allow=False, cache=tmp_path, grab=grab, caller=fake(calls))
    assert res["status"] == "preview" and calls == [] and res["requests"] == 2 * 2 * 3
    p = json.loads((tmp_path / "image-transfer-preview.json").read_text())
    assert p["header"] == look.HEADERS and p["frames_to_send"] == 8 and "no file paths" in p["data"]
    assert all("characters of base64" in a["data_base64"] for a in p["sample"]["assets"].values())   # the preview holds no image


def test_windows_name_what_is_off_and_answers_are_cached(tmp_path, monkeypatch):
    monkeypatch.setenv("TYPESAFE_API_KEY", "test-key")
    calls = []
    res = look.look("ref.mp4", "rem.mp4", SHOTS, SPEC, samples=2, allow=True, cache=tmp_path, grab=grab, caller=fake(calls))
    assert res["status"] == "complete" and len(calls) == 12
    keys = next(r for r in res["windows"] if r["window"] == "keys")
    c = keys["subjects"]["critter"]
    assert c["dx"] == round(0.1 * look.W) and c["dy"] == 0 and c["size"] == 1.0
    assert keys["checks"]["legends"] == {"reference": 0.9, "remake": 0.1, "agree": False}
    assert keys["checks"]["face"]["reference"] == "smile" and keys["checks"]["face"]["remake"] == "slits"
    assert any(p.startswith("critter: 192 px right") for p in keys["problems"]) and "legends: reference 0.90, remake 0.10" in keys["problems"]
    assert "keyboard" not in next(r for r in res["windows"] if r["window"] == "world")["subjects"]     # per window, as the spec says
    again = look.look("ref.mp4", "rem.mp4", SHOTS, SPEC, samples=2, allow=False, cache=tmp_path, grab=grab, caller=fake(calls))
    assert again["status"] == "complete" and len(calls) == 12                                          # all cached
    assert "keys" in look.report(again)


def test_a_wrong_answer_is_refused_not_kept(tmp_path, monkeypatch):
    monkeypatch.setenv("TYPESAFE_API_KEY", "test-key")
    def inverted(ans):
        for a in ans.values():
            if a["type"] == "box":
                a["box"]["left"], a["box"]["right"] = 0.8, 0.2
    res = look.look("ref.mp4", "rem.mp4", SHOTS[:1], SPEC, samples=1, allow=True, cache=tmp_path, grab=grab,
                    caller=fake([], inverted))
    assert res["status"] == "partial" and res["windows"] == [] and res["errors"]
    kept = [json.loads(p.read_text()) for p in tmp_path.glob("v-*.json")]                             # only the pair's answers,
    assert len(kept) == 1 and "same_shot" in kept[0]["answers"]                                        # which had no box
    with pytest.raises(TriageError, match="spec"):
        look.for_window(SPEC, "keys") and look.for_window({**SPEC, "windows": {"x": {"subjects": ["plant"]}}}, "x")


def test_track_follows_subjects_and_checks_through_time(tmp_path, monkeypatch):
    monkeypatch.setenv("TYPESAFE_API_KEY", "test-key")
    res = look.track("rem.mp4", SPEC, ["critter"], checks=["face"], every=0.5, start=1.0, end=2.0, allow=True,
                     cache=tmp_path, grab=grab, caller=fake([]))
    assert [r[0] for r in res["subjects"]["critter"]] == [1.0, 1.5]
    assert res["subjects"]["critter"][0][2:] == [0.6, 0.5, 0.2, 0.2] and res["checks"]["face"][0] == [1.0, "slits", 0.9]
    js = look.write_js(res, tmp_path / "track.js").read_text()
    assert "export const TRACK = {\"critter\":[[1.0,0.95,0.6,0.5,0.2,0.2]" in js and "export const CHECKS = {\"face\"" in js
    with pytest.raises(TriageError, match="not in the spec"):
        look.track("rem.mp4", SPEC, ["critter"], checks=["mood"], every=0.5, start=0, end=1, cache=tmp_path, grab=grab)


def test_frames_never_carry_the_key_and_go_with_the_image_header():
    req = look.frame_request(b"\xff\xd8 a frame", SPEC, ["critter"], [])
    assert req["model"] == "jev-1.14.0" and req["state"] in req["assets"] and set(req["questions"]) == {"critter_seen", "critter_box"}
    sent = {}
    class Opener:
        def open(self, r, timeout):
            sent.update(headers=dict(r.header_items()), timeout=timeout)
            raise TriageError("stop")
    with pytest.raises(TriageError, match="stop"):
        look.call(req, "k-123", opener=Opener(), headers=look.HEADERS, timeout=120)
    assert sent["headers"]["Typesafe-danger-zone-images"] == "true" and sent["timeout"] == 120
