"""Sampled instruments: the manifest is pinned, notes sound their pitch, a score plays them and credits them."""
import json
import re

import numpy as np
import pytest

from moodreel.score import samples
from moodreel.score import score as sc

READY = samples.ready()
needs_samples = pytest.mark.skipif(not READY, reason="samples not fetched (moodreel samples fetch)")


def test_manifest_is_pinned_and_complete():
    m = samples.manifest()
    assert re.fullmatch(r"[0-9a-f]{40}", m["source"]["commit"]) and m["source"]["license"] == "CC0 1.0"
    assert set(m["instruments"]) >= {"piano", "strings", "pizz", "trumpet", "horn", "tuba", "clarinet", "marimba",
                                     "glock", "harp", "timpani", "timpani_roll"}
    for fs in m["instruments"].values():
        assert [e["midi"] for e in fs] == sorted(e["midi"] for e in fs)
        for e in fs:
            assert re.fullmatch(r"[0-9a-f]{64}", e["sha256"]) and e["bytes"] > 0 and 20 <= e["midi"] <= 110


def _pitch_error(x, midi):
    """Cents between the spectral peak near midi and midi itself."""
    seg = x[int(0.06 * samples.SR): int(0.56 * samples.SR)]
    n = 1 << 17
    mag = np.abs(np.fft.rfft(seg * np.hanning(len(seg)), n))
    f = np.fft.rfftfreq(n, 1 / samples.SR)
    f0 = 440 * 2 ** ((midi - 69) / 12)
    win = (f > f0 * 2 ** (-1.5 / 12)) & (f < f0 * 2 ** (1.5 / 12))
    return 1200 * np.log2(f[win][np.argmax(mag[win])] / f0)


@needs_samples
def test_notes_sound_the_pitch_asked_for():
    for inst, notes in {"piano": [60, 67, 76], "strings": [62, 69], "pizz": [57, 64], "trumpet": [67, 72], "horn": [57, 62],
                        "tuba": [48, 50], "clarinet": [70, 77, 89], "marimba": [64, 71], "glock": [86, 91], "harp": [60, 65]}.items():
        for m in notes:
            assert abs(_pitch_error(samples.note(inst, m, 0.8), m)) < 30, (inst, m)


@needs_samples
def test_a_note_lasts_its_length_and_release():
    x = samples.note("strings", 62, 1.0)
    assert len(x) == int((1.0 + 0.4) * samples.SR) and abs(x[-1]) < 1e-3


BAND = {"bpm": 120, "meter": 4, "seed": 3,
        "sections": [{"name": "a", "bars": 2, "chords": ["F", "C7"], "groove": "oompah", "parts": ["piano", "tuba", "brass"]},
                     {"name": "b", "bars": 2, "chords": ["Bb", "C"], "groove": "none", "parts": ["strings", "harp", "timpani"]}],
        "cues": [{"name": "swell", "bar": 3, "sound": "roll", "beats": 4}, {"name": "hit", "bar": 4, "sound": "brass"}]}


@needs_samples
def test_a_score_plays_sampled_parts_and_credits_them(tmp_path):
    audio, tl = sc.render(BAND)
    assert np.isfinite(audio).all() and np.abs(audio).max() <= 0.91
    i, w = 4 * int(0.5 * samples.SR), 2400                   # bar 2's downbeat: the stride bass note starts on it
    before, after = np.abs(audio[i - w:i]).max(), np.abs(audio[i:i + w]).max()
    assert after > 1.5 * before and np.abs(audio[:w]).max() > 0.05
    (tmp_path / "score.json").write_text(json.dumps(BAND))
    (tmp_path / "CREDITS").write_text("x\n\n- nothing else\n")
    sc.write(tmp_path)
    sc.write(tmp_path)                                      # credited once
    assert (tmp_path / "CREDITS").read_text().count("VSCO-2-CE") == 1


def test_a_score_needs_its_samples_fetched(monkeypatch):
    assert sc.uses_samples(BAND) == ["brass", "harp", "piano", "roll", "strings", "timpani", "tuba"]
    monkeypatch.setattr(samples, "ready", lambda: False)
    with pytest.raises(SystemExit, match="moodreel samples fetch"):
        sc.render(BAND)
    assert sc.uses_samples({"sections": [{"parts": ["kick", "pad"]}], "cues": [{"sound": "stab"}]}) == []
