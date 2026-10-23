"""A beat grid in silent motion: moves on a steady pulse are found with their tempo; moves at random are not."""
from __future__ import annotations

import numpy as np

from moodreel.motion import beat

FPS = 24


def _events(starts, durs, rng):
    jitter = lambda: rng.normal(0, 0.4 / FPS)  # noqa: E731  (a measured start or landing is off by a fraction of a frame)
    return [{"props": {"y": {"t0": a + jitter(), "t1": a + d + jitter()}}} for a, d in zip(starts, durs)]


def test_moves_landing_on_a_120_bpm_grid_give_its_tempo():
    rng = np.random.default_rng(1)
    starts = rng.choice(np.arange(0, 12, 0.5), 18, replace=False)
    durs = rng.choice([0.5, 1.0], 18)                     # each lands on a later beat
    g = beat.grid(_events(starts, durs, rng), [{"type": "cut", "t": 6.0}], FPS)
    assert g and g["bpm"] == 120 and g["subdivision"] == 1 and g["phase_s"] == 0.0 and g["p_value"] < beat.ALPHA


def test_moves_at_random_times_have_no_grid():
    rng = np.random.default_rng(2)
    for _ in range(5):
        starts = rng.uniform(0, 12, 18)
        assert beat.grid(_events(starts, rng.uniform(0.2, 0.9, 18), rng), [], FPS) is None
