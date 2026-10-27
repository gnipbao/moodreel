"""`moodreel direct` (a director's reading by Jev), offline: a fake caller answers as a director would, differently for
the reference and the remake, and the notes name where they differ."""
from __future__ import annotations

import base64

from moodreel.check import direct

SHOTS = [(0.0, 2.0, "sunset"), (2.0, 4.0, "swoop")]


def grab(video, t):
    return f"{video}@{t:.3f}".encode()


def fake(calls):
    def caller(req, key):
        calls.append(req)
        rem = all(base64.b64decode(a["data_base64"]).decode().startswith("rem") for a in req["assets"].values())
        pick = {"shot": "wide", "angle": "ground" if rem else "high", "composition": "pattern" if rem else "leading_line",
                "light": "sunset", "move": "static" if rem else "pull_out", "ease": "steady" if rem else "slows_down",
                "action": "none" if rem else "flies"}
        ans = {}
        for k, q in req["questions"].items():
            if q["type"] == "choice":
                opts = list(q["criteria"])
                p = {o: (0.8 if o == pick[k] else 0.2 / (len(opts) - 1)) for o in opts}
                ans[k] = {"type": "choice", "choice": pick[k], "probabilities": p, "confidence": 0.8}
            elif q["type"] == "score":
                ans[k] = {"type": "score", "score": 1.0 if rem else 3.4, "confidence": 0.7}
            elif q["type"] == "noul":
                ans[k] = {"type": "noul", "noul": 0.2 if rem else 0.8}
            elif q["type"] == "box":
                x = 0.7 if rem else 0.4
                ans[k] = {"type": "box", "box": {"left": x - 0.05, "right": x + 0.05, "top": 0.3, "bottom": 0.4}, "confidence": 0.9}
        return {"model": "jev-1.14.0", "answers": ans, "usage": {"input_tokens": 3000, "output_tokens": 120}}
    return caller


def test_without_permission_only_the_preview(tmp_path):
    calls = []
    res = direct.direct("ref.mp4", SHOTS, "rem.mp4", allow=False, cache=tmp_path, grab=grab, caller=fake(calls))
    assert res["status"] == "preview" and calls == [] and res["requests"] == 8      # 2 films x 2 windows x (frame + motion)
    assert (tmp_path / "image-transfer-preview.json").exists()


def test_the_reading_and_the_notes(tmp_path, monkeypatch):
    monkeypatch.setenv("TYPESAFE_API_KEY", "test-key")
    calls = []
    res = direct.direct("ref.mp4", SHOTS, "rem.mp4", allow=True, cache=tmp_path, grab=grab, caller=fake(calls))
    assert res["status"] == "complete" and len(calls) == 8
    motion = [r for r in calls if "move" in r["questions"]]
    assert all(len(r["assets"]) == 3 for r in motion)                                # start, middle, end in one request
    w = res["windows"][0]
    assert w["reference"]["move"][0] == ("pull_out", 0.8) and w["reference"]["reveal"] == 0.8
    notes = " | ".join(w["notes"])
    for want in ("angle: the reference high (0.8), the remake ground (0.8)", "composition: the reference leading_line",
                 "ease: the reference slows_down", "speed: the reference fast, the remake slow, drifting",
                 "the eye goes to (0.70, 0.35), the reference's to (0.40, 0.35)", "ends on a reveal"):
        assert want in notes
    md = direct.markdown(res)
    assert md.startswith("# A director's reading") and "## sunset (0.00-2.00 s)" in md and "camera pull_out 0.80" in md
    assert "sunset:" in direct.report(res)
