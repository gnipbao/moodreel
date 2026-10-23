"""Narration: lines placed at times, after one another or on cues, levelled, refused when they collide; and a score of
cues alone as a film's sound effects."""
from __future__ import annotations

import json
import shutil
import subprocess

import numpy as np
import pytest
from scipy.io import wavfile

from moodreel import voice
from moodreel.score import score as sc
from moodreel.score import synth

needs_say = pytest.mark.skipif(shutil.which("say") is None or shutil.which("ffmpeg") is None, reason="needs macOS say")


def _film(tmp_path, lines, duration=8.0, cues=None):
    d = tmp_path / "film"
    (d / "out").mkdir(parents=True)
    (d / "film.json").write_text(json.dumps({"name": "film", "fps": 24, "size": "320x180", "duration": duration}))
    (d / "narration.json").write_text(json.dumps({"voice": "Samantha", "rate": 190, "lines": lines}))
    if cues:
        (d / "score.json").write_text(json.dumps({"bpm": 120, "sections": [], "cues": cues}))
    return d


@needs_say
def test_lines_fall_at_their_times_after_each_other_and_on_cues(tmp_path):
    d = _film(tmp_path, [{"id": "a", "at": 0.5, "text": "One."}, {"id": "b", "gap": 0.3, "text": "Two."},
                         {"id": "c", "cue": "bell", "text": "Three."}], cues=[{"name": "bell", "bar": 3, "sound": "ding"}])
    r = voice.write(d)
    lines = json.loads((d / "voice.js").read_text().split("export const VOICE = ")[1].split(";\n")[0])["lines"]
    assert r["lines"] == 3 and lines[0]["start"] == 0.5 and abs(lines[1]["start"] - (lines[0]["end"] + 0.3)) < 1e-3
    assert lines[2]["start"] == 4.0                                    # bar 3 at 120 BPM
    sr, x = wavfile.read(d / "out" / "voice.wav")
    x = x.astype(float) / 32768
    speech = x[int(lines[0]["start"] * sr):int(lines[0]["end"] * sr)]
    assert abs(20 * np.log10(np.sqrt(np.mean(speech[np.abs(speech) > 1e-4] ** 2))) - voice.SPEECH_DB) < 2
    assert np.abs(x[int(0.1 * sr):int(0.4 * sr)]).max() < 1e-3          # silent before the first line
    assert "draft voice" in (d / "CREDITS").read_text()
    js = d / "t.mjs"
    js.write_text(f"import {{ line }} from '{(d / 'voice.js').as_uri()}';\n"
                  f"console.log(JSON.stringify([line(0.2), line({lines[0]['start'] + 0.1}).id, line({lines[2]['start'] + 0.1}).id]));\n")
    assert json.loads(subprocess.run(["node", str(js)], capture_output=True, text=True, check=True).stdout) == [None, "a", "c"]


@needs_say
def test_lines_that_collide_or_run_past_the_end_are_refused(tmp_path):
    with pytest.raises(SystemExit, match="before the line before it ends"):
        voice.write(_film(tmp_path / "x", [{"at": 1.0, "text": "A rather long first sentence."}, {"at": 1.2, "text": "Two."}]))
    with pytest.raises(SystemExit, match="past the film"):
        voice.write(_film(tmp_path / "y", [{"at": 1.5, "text": "Too late to finish this one."}], duration=2.0))


def test_a_score_of_cues_alone_is_the_sound_effects():
    audio, tl = sc.render({"bpm": 120, "sections": [], "cues": [{"name": "pop", "bar": 2, "sound": "pop"},
                                                                  {"name": "ding", "bar": 4, "beat": 3, "sound": "ding"}]})
    rms = lambda t0, t1: float(np.sqrt(np.mean(audio[int(t0 * synth.SR):int(t1 * synth.SR)] ** 2)))  # noqa: E731
    assert [c["t"] for c in tl["cues"]] == [2.0, 7.0] and len(audio) / synth.SR >= 9
    assert rms(0.5, 1.9) < 1e-4 < rms(2.0, 2.1) and rms(7.0, 7.4) > 1e-3
