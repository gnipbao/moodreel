"""The one-axis reader (stretch, clip reveal, wipe), class claims and the style's shared curve, on synthetic clips."""
from __future__ import annotations

import numpy as np

from moodreel.motion import eases, extent, fit, track
from moodreel.video import Clip

FPS, W, H, N = 30, 320, 180, 40
GROUND = np.array([236, 234, 228], np.uint8)


def _block(h, w, seed=0):
    """A two-colour textured block: what shows of it tells a clip, a wipe and a stretch apart."""
    blk = np.empty((h, w, 3), np.uint8)
    blk[:] = (20, 20, 20)
    blk[np.random.default_rng(seed).random((h, w)) < 0.35] = (200, 30, 40)
    return blk


def _film(draw, ease="power3.out", t0=10, t1=25):
    frames = []
    for f in range(N):
        img = np.empty((H, W, 3), np.uint8)
        img[:] = GROUND
        draw(img, float(eases.get(ease)(np.clip((f - t0) / (t1 - t0), 0, 1))))
        frames.append(img)
    return Clip("", FPS, W, H, np.stack(frames), 1.0)


def _track(box, kind="appear"):
    return {"kind": kind, "shot": 0, "p": 5, "q": 34, "box": list(box), "readings": {}}


def test_a_bar_growing_from_its_base_is_a_stretch():
    def draw(img, p):
        h = int(round(80 * p))
        if h:
            img[150 - h:150, 100:160] = (30, 30, 30)
    X = extent.reading(_film(draw), _track((100, 70, 60, 80)))
    assert X and (X["mode"], X["axis"], X["anchor"], X["prop"]) == ("stretch", "y", "bottom", "sy")
    assert X["series"][0] == 0 and abs(X["series"][-1] - 1) < 0.05


def test_type_rising_out_of_a_slot_is_a_clip_reveal():
    blk = _block(50, 60)

    def draw(img, p):
        top = 60 + int(round(70 * (1 - p)))               # rests at 60..110; the slot hides rows from 120 down
        part = blk[:max(0, min(50, 120 - top))]
        img[top:top + len(part), 100:160] = part
    X = extent.reading(_film(draw), _track((100, 60, 60, 50)))
    assert X and (X["mode"], X["axis"], X["anchor"], X["prop"]) == ("clip", "y", "bottom", "y")
    assert abs(np.nanmin(X["series"]) - 85) < 1.5          # the centre, from the top edge, ends at rest


def test_a_block_swept_on_in_place_is_a_wipe():
    blk = _block(40, 100, seed=1)

    def draw(img, p):
        n = int(round(100 * p))
        img[70:110, 100:100 + n] = blk[:, :n]
    X = extent.reading(_film(draw, "none"), _track((100, 70, 100, 40)))
    assert X and (X["mode"], X["axis"], X["anchor"]) == ("wipe", "x", "left")


def test_a_plain_slide_is_left_to_the_tracker():
    blk = _block(40, 60, seed=2)

    def draw(img, p):
        x = 40 + int(round(100 * p))
        img[70:110, x:x + 60] = blk
    assert extent.reading(_film(draw), _track((140, 70, 60, 40))) is None


def test_a_short_clear_tween_claims_its_class_not_its_family():
    t = np.arange(0, 1.0, 1 / FPS)
    v = 100 + 200 * eases.get("power3.inOut")(np.clip((t - 0.3) / 0.23, 0, 1))
    f = fit.fit_move(t, v + np.random.default_rng(3).normal(0, 0.3, len(t)), FPS)
    assert f["ease"] == "unknown" and f["class"] == "inOut"


def test_one_bezier_through_several_tweens_of_a_house_curve():
    curve = eases.get("bezier(0.7,0,0.2,1)")
    rng = np.random.default_rng(4)
    samples = []
    for t0, d, a, b in ((0.2, 0.375, 10, 80), (0.5, 0.4, 300, -120), (0.1, 0.35, 0, 1)):
        t = np.arange(0, 1.2, 1 / 24)
        v = a + b * curve(np.clip((t - t0) / d, 0, 1)) + rng.normal(0, 0.002 * abs(b), len(t))
        samples.append({"t": t, "v": v, "A": a, "B": b, "t0": t0 - 0.03, "t1": t0 + d + 0.04})
    got = fit.shared_bezier(samples)
    assert got["tweens"] == 3 and np.allclose(got["bezier"], [0.7, 0, 0.2, 1], atol=0.06)


def test_bars_standing_on_an_axis_are_separate_elements():
    m = np.zeros((120, 200), bool)
    for x in (20, 80, 140):
        m[40:100, x:x + 30] = True
    m[100:102, 10:190] = True                                 # the axis they stand on
    parts = track._unjoin(m, area_min=20)
    assert len(parts) == 4 and sum(p.sum() for p in parts) <= m.sum()


def test_a_whole_layout_panning_on_a_flat_ground_is_the_camera():
    from moodreel.motion import camera

    def film(blocks):
        frames = []
        for f in range(N):
            img = np.empty((H, W, 3), np.uint8)
            img[:] = GROUND
            dx = -int(round(120 * eases.get("power2.inOut")(np.clip((f - 10) / 12, 0, 1))))
            for x, y, moves in blocks:
                img[y:y + 30, x + (dx if moves else 0):x + (dx if moves else 0) + 30] = (20, 20, 20)
            frames.append(img)
        return Clip("", FPS, W, H, np.stack(frames), 1.0)
    spread = [(40, 40, True), (120, 100, True), (200, 60, True), (260, 120, True)]
    pan = camera.layout_pan(film(spread), 10, 22)
    assert pan and abs(pan["panx"][-1] + 120) < 3
    alone = [(40, 40, True), (120, 100, False), (200, 60, False), (260, 120, False)]
    assert camera.layout_pan(film(alone), 10, 22) is None    # one element moving among still ones is its own move
