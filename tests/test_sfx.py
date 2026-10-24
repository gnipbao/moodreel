"""A film's sound effects at seconds: every foley sound, each cue landing on its time and side, the file deliver mixes, and
the mix keeping the film's length."""
from __future__ import annotations

import json
import shutil

import numpy as np
import pytest
from scipy.io import wavfile

from moodreel.film import film
from moodreel.score import sfx, synth


def _start(x: np.ndarray, floor: float = 1e-3) -> float:
    """The first second at which a channel rises above `floor`."""
    i = np.flatnonzero(np.abs(x) > floor)
    return i[0] / synth.SR if len(i) else -1.0


@pytest.mark.parametrize("name", sorted(synth.FOLEY))
def test_every_foley_sound_is_heard_bounded_and_the_same_every_time(name):
    a = synth.FOLEY[name](np.random.default_rng(3), 0.8)
    b = synth.FOLEY[name](np.random.default_rng(3), 0.8)
    assert a.ndim == 1 and len(a) > 0 and np.all(np.isfinite(a)) and np.array_equal(a, b)
    assert 1e-3 < np.abs(a).max() <= 1.5


def test_a_cue_lands_on_its_time_and_side():
    out = sfx.render({"seed": 1, "gain_db": 0, "cues": [{"t": 0.5, "sound": "slam", "pan": -1},
                                                         {"t": 1.25, "sound": "click", "pan": 1}]}, 2.0)
    assert out.shape == (2 * synth.SR, 2) and np.abs(out).max() <= 1.0
    left, right = out[: synth.SR, 0], out[: synth.SR, 1]
    assert abs(_start(left) - 0.5) < 0.005 and np.abs(right).max() < 1e-6       # hard left: nothing on the right
    late = out[synth.SR:]
    assert abs(1 + _start(late[:, 1]) - 1.25) < 0.005 and np.abs(late[:, 0]).max() < 0.05 * np.abs(late[:, 1]).max()


def test_a_riser_ends_on_its_time_and_the_effects_sit_by_gain_db():
    cfg = {"seed": 2, "gain_db": 0, "cues": [{"t": 1.5, "sound": "riser", "dur": 0.8}]}
    loud = sfx.render(cfg, 2.5)
    env = np.abs(loud[:, 0])
    peak = np.argmax(env) / synth.SR
    assert 1.3 < peak <= 1.5 and _start(loud[:, 0]) > 0.69                          # it swells over dur and ends on t
    quiet = sfx.render({**cfg, "gain_db": -12}, 2.5)
    assert np.allclose(quiet, loud * 10 ** (-12 / 20), atol=1e-6)
    assert np.array_equal(loud, sfx.render(cfg, 2.5))


def test_an_unknown_sound_names_the_choices():
    with pytest.raises(ValueError, match="kaboom.*slam"):
        sfx.render({"cues": [{"t": 1, "sound": "kaboom"}]})


def test_write_puts_the_effects_beside_the_film(tmp_path):
    (tmp_path / "sfx.json").write_text(json.dumps({"cues": [{"t": 0.2, "sound": "key"}, {"t": 0.6, "sound": "boom"}]}))
    info = sfx.write(tmp_path, 1.5)
    sr, data = wavfile.read(info["wav"])
    assert sr == synth.SR and data.shape == (int(1.5 * synth.SR), 2) and info["cues"] == 2 and info["seconds"] == 1.5


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="needs ffmpeg")
def test_the_loudness_pass_keeps_the_film_to_the_frame(tmp_path):
    # a mix a little longer than the film (here by 11 ms) once came out of loudnorm 0.1 s short, taking the last frames
    rng = np.random.default_rng(4)
    x = np.cumsum(rng.normal(0, 1, int(6.011479 * synth.SR)))
    x = 0.4 * (x - np.convolve(x, np.ones(64) / 64, "same")) / np.abs(x).max()
    wavfile.write(tmp_path / "bed.wav", synth.SR, (np.stack([x, x], 1) * 32767).astype(np.int16))
    film._loudnorm(tmp_path / "bed.wav", tmp_path / "mix.wav", 6.0)
    sr, data = wavfile.read(tmp_path / "mix.wav")
    assert sr == 48000 and len(data) == 6 * 48000
