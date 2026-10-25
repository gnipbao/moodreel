"""A film's score: chords, the grid and cue times, the music drawn on them, and the timeline the picture imports."""
from __future__ import annotations

import json
import shutil
import subprocess

import numpy as np
import pytest
from scipy.signal import resample_poly

from moodreel.measure import rhythm
from moodreel.score import score as sc
from moodreel.score import synth

SCORE = {"bpm": 120, "meter": 4, "seed": 5,
         "sections": [{"name": "a", "bars": 2, "chords": ["C", "Am"], "groove": "four", "parts": ["kick", "hat", "pad"]},
                      {"name": "b", "bars": 4, "chords": ["F", "G7", "Em", "Am"], "groove": "backbeat",
                       "parts": ["kick", "snare", "hat", "bass", "pad", "lead", "pluck"]},
                      {"name": "c", "bars": 2, "chords": ["F", "C"], "groove": "oompah"}],
         "cues": [{"name": "late", "bar": 7, "beat": 2.5, "sound": "boing"}, {"name": "hit", "bar": 3, "sound": "stab"},
                  {"name": "hush", "bar": 5, "beat": 1, "sound": "stop", "beats": 2},
                  {"name": "bell", "bar": 5, "beat": 3, "sound": "ding"}]}


def test_chords_parse_to_a_root_and_intervals():
    assert sc.chord("F#m7") == (6, (0, 3, 7, 10)) and sc.chord("Bb") == (10, (0, 4, 7)) and sc.chord("Gsus4")[1] == (0, 5, 7)
    with pytest.raises(ValueError):
        sc.chord("H7")


def test_the_grid_gives_every_section_and_cue_its_time():
    tl = sc.timeline(SCORE)
    assert tl["beat_s"] == 0.5 and tl["bars"] == 8 and tl["duration"] == 16.0
    assert [s["start"] for s in tl["sections"]] == [0.0, 4.0, 12.0]
    assert [(c["name"], c["t"]) for c in tl["cues"]] == [("hit", 4.0), ("hush", 8.0), ("bell", 9.0), ("late", 12.75)]


def test_the_music_is_the_same_every_time_keeps_its_tempo_and_falls_silent_on_a_stop():
    a, tl = sc.render(SCORE)
    b, _ = sc.render(SCORE)
    assert np.array_equal(a, b) and np.abs(a).max() <= 0.9 + 1e-6
    rms = lambda t0, t1: float(np.sqrt(np.mean(a[int(t0 * synth.SR):int(t1 * synth.SR)] ** 2)))  # noqa: E731
    assert rms(8.05, 8.95) < 1e-4 < rms(9.0, 9.4)          # the band stops; the bell rings in the silence
    env = rhythm.onset_envelope(resample_poly(a, rhythm.SR, synth.SR).astype(np.float32))
    assert abs(rhythm.tempo(env)[0] - 120) < 2


@pytest.mark.skipif(shutil.which("node") is None, reason="needs node")
def test_the_picture_reads_the_same_times(tmp_path):
    (tmp_path / "score.json").write_text(json.dumps(SCORE))
    out = sc.write(tmp_path)
    assert (tmp_path / "out" / "score.wav").exists() and out["cues"] == 4
    js = tmp_path / "try.mjs"
    js.write_text(f"import {{ bar, cue }} from '{(tmp_path / 'score.js').as_uri()}';\n"
                  "console.log(JSON.stringify([bar(3), bar(7, 2.5), cue('bell')]));\n")
    assert json.loads(subprocess.run(["node", str(js)], capture_output=True, text=True, check=True).stdout) == [4, 12.75, 9]


SONG = {"bpm": 120, "meter": 4, "seed": 2,
        "sections": [{"name": "in", "bars": 1, "chords": ["Am"], "groove": "none", "parts": ["pad"]},
                     {"name": "verse", "bars": 2, "chords": ["Am", "F"], "groove": "backbeat",
                      "parts": ["kick", "snare", "hat", "bass", "lead"],
                      "melody": [{"bar": 1, "beat": 1, "beats": 1, "tone": 2, "word": "save"},
                                 {"bar": 1, "beat": 2, "beats": 1, "tone": 1, "word": "your"},
                                 {"bar": 1, "beat": 3, "beats": 2, "tone": 0, "word": "work"},
                                 {"bar": 2, "beat": 1, "beats": 1, "tone": 0},
                                 {"bar": 2, "beat": 2, "beats": 2, "tone": 2, "word": "please", "line": True}]},
                     {"name": "hook", "bars": 1, "chords": ["C"], "groove": "four", "parts": ["kick", "clap"]}],
        "cues": [{"name": "hush", "bar": 4, "beat": 3, "sound": "stop", "beats": 2}]}


def test_a_written_melody_is_the_lyric_as_sung():
    tl = sc.timeline(SONG)
    assert [(w["w"], w["start"]) for w in tl["words"]] == [("save", 2.0), ("your", 2.5), ("work", 3.0), ("please", 4.5)]
    assert [ln["text"] for ln in tl["lines"]] == ["save your work", "please"]   # a new line where a note says so
    assert tl["words"][2]["end"] == 3.9                                         # 90 % of its two beats
    a, _ = sc.render(SONG)
    b, _ = sc.render({**SONG, "sections": [{**s, "melody": []} if s["name"] == "verse" else s for s in SONG["sections"]]})
    assert not np.array_equal(a, b)                                             # the written lead replaces the drawn one


def test_the_score_writes_its_music_as_data_exactly(tmp_path):
    (tmp_path / "score.json").write_text(json.dumps(SONG))
    out = sc.write(tmp_path)
    assert out["words"] == 4 and json.loads((tmp_path / "lyrics.json").read_text())[1]["words"][0]["w"] == "please"
    text = (tmp_path / "music-data.js").read_text()
    audio = json.loads(text.split("export const AUDIO = ")[1].split(";\n")[0])
    assert audio["bpm"] == 120 and audio["beats"][:3] == [0.0, 0.5, 1.0] and audio["downbeats"] == [0.0, 2.0, 4.0, 6.0]
    assert [t for t, _ in audio["onsets"]["kick"]] == [2.0, 3.0, 4.0, 5.0, 6.0, 6.5]   # backbeat 1 and 3, then four, not in the stop
    assert [t for t, _ in audio["onsets"]["snare"]] == [2.5, 3.5, 4.5, 5.5, 6.5]       # the hook's claps count as snares
    assert [t for t, _ in audio["onsets"]["vocal"]] == [2.0, 2.5, 3.0, 4.5]
    assert len(audio["features"]["rms"]) > 700 and max(audio["features"]["rms"]) == 1.0
