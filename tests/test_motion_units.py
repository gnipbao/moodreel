"""Fast checks on synthetic data: eases, the tween fitter, shot boundaries, stepping and the camera."""
from __future__ import annotations

import cv2
import numpy as np
import pytest

from moodreel.motion import camera, eases, fit, shots
from moodreel.video import Clip

FPS = 30


@pytest.mark.parametrize("name", [n for n, _ in eases.candidates()])
def test_every_ease_runs_from_0_to_1(name):
    u = np.array([0.0, 1.0])
    assert np.allclose(eases.get(name)(u), [0, 1], atol=2e-3)


def test_back_out_overshoots_and_class_names():
    assert eases.get("back.out(1.7)")(np.linspace(0, 1, 200)).max() > 1.05
    assert eases.shape_class("back.out(1.7)") == "out+overshoot"
    assert eases.shape_class("elastic.out(1,0.3)") == "out+oscillate"
    assert eases.shape_class("power2.inOut") == "inOut"


def _tween(name, t0=0.3, d=0.6, a=100.0, b=300.0, dur=1.4, noise=0.4, seed=1):
    t = np.arange(0, dur, 1 / FPS)
    v = a + (b - a) * eases.get(name)(np.clip((t - t0) / d, 0, 1))
    return t, v + np.random.default_rng(seed).normal(0, noise, len(t))


@pytest.mark.parametrize("name", ["power2.out", "power3.in", "sine.inOut", "back.out(1.7)", "expo.out"])
def test_fit_recovers_class_and_timing(name):
    t, v = _tween(name)
    f = fit.fit_move(t, v, FPS)
    assert eases.shape_class(f["best"]) == eases.shape_class(name)
    truth = eases.get(name)(np.linspace(0, 1, 4001))
    t50 = 0.3 + 0.6 * np.linspace(0, 1, 4001)[np.argmax(truth >= 0.5)]
    assert abs(f["checkpoints"]["t50"] - t50) <= 1 / FPS
    assert abs(f["delta"] - 200) < 10


def test_a_short_tween_is_measured_but_not_named():
    t, v = _tween("power2.out", d=0.15)
    f = fit.fit_move(t, v, FPS)
    assert f["ease"] == "unknown"                     # too few readings in transition to name a family
    assert eases.shape_class(f["best"]) in ("out", "out+overshoot", "linear", "inOut")


def test_hidden_start_is_solved_without_seeing_it():
    t, v = _tween("power3.out", t0=0.3)
    seen = t >= 0.42                                  # the first 20 % happened while invisible
    f = fit.fit_move(t[seen], v[seen], FPS, t0_range=(0.2, t[seen][0]))
    assert abs(f["from"] - 100) < 25 and abs(f["t0"] - 0.3) < 0.08


def test_role_prior_picks_among_equivalent_families():
    t, v = _tween("power1.out", noise=1.5)
    f = fit.fit_move(t, v, FPS, prefer=fit.PREFER["exit"])
    g = fit.fit_move(t, v, FPS, prefer=fit.PREFER["entrance"])
    assert eases.shape_class(g["best"]) == "out"     # the data says out; an entrance prefers out anyway
    assert eases.shape_class(f["best"]) == "out"     # a prior never overrides a curve the data tells apart


def _clip(frames, fps=FPS):
    frames = np.stack(frames).astype(np.uint8)
    return Clip("", fps, frames.shape[2], frames.shape[1], frames, 1.0)


def _flat(c, w=128, h=72):
    return np.full((h, w, 3), c, np.uint8)


def test_cut_dissolve_and_dip():
    a, b, c, d = (60, 60, 60), (200, 200, 200), (30, 120, 200), (240, 230, 220)
    fr = [_flat(a)] * 20 + [_flat(b)] * 20
    fr += [_flat(np.array(b) * (1 - k / 10) + np.array(c) * k / 10) for k in range(1, 11)] + [_flat(c)] * 10
    fr += [_flat(np.array(c) * (1 - k / 6)) for k in range(1, 7)] + [_flat((0, 0, 0))]
    fr += [_flat(np.array(d) * k / 6) for k in range(1, 7)] + [_flat(d)] * 10
    out, transitions, _e, _th = shots.shots(_clip(fr))
    kinds = [t["type"] for t in transitions]
    assert kinds == ["cut", "dissolve", "dip"]
    assert transitions[0]["frame"] == 20
    assert transitions[2]["color"] == "#000000"
    assert len(out) == 4


def test_stepping_on_twos():
    e = np.zeros(60)
    e[10:50:2] = 5.0                                  # the picture changes every second frame
    assert shots.stepping(e, [(10, 50)])["on"] == 2
    e[10:50] = 5.0
    assert shots.stepping(e, [(10, 50)])["on"] == 1


def test_camera_push_and_pan_on_a_textured_ground():
    rng = np.random.default_rng(3)
    ground = cv2.GaussianBlur(rng.integers(0, 255, (180, 320, 3)).astype(np.uint8), (0, 0), 1.5)
    C = np.array([160.0, 90.0])
    frames = []
    for k in range(30):
        z, px = 1 + 0.1 * k / 29, -12 * k / 29
        M = np.array([[z, 0, C[0] * (1 - z) + px], [0, z, C[1] * (1 - z)]])
        frames.append(cv2.warpAffine(ground, M, (320, 180), borderMode=cv2.BORDER_REFLECT))
    clip = _clip(frames)
    cam = camera.estimate(clip, {"start": 0, "end": 30})
    assert cam["status"] == "moving"
    assert abs(cam["zoom"][-1] - 1.1) < 0.005
    assert abs(cam["panx"][-1] + 12) < 1.5


def test_flat_ground_without_change_is_a_locked_camera():
    clip = _clip([_flat((40, 40, 40))] * 20)
    assert camera.estimate(clip, {"start": 0, "end": 20})["status"] == "locked"
