"""Ambient motion on synthetic clips: loops (a pulse, a bob, a spinner, a breathing fade) and a particle field."""
from __future__ import annotations

import cv2
import numpy as np

from moodreel.motion import ambient
from moodreel.video import Clip

FPS, W, H, N = 30, 640, 360, 150
SHOT = {"id": 0, "start": 0, "end": N}


def _loops_clip():
    frames = []
    for f in range(N):
        t = f / FPS
        img = np.full((H, W, 3), (20, 22, 28), np.uint8)
        cv2.circle(img, (110, 180), int(round(26 * (1 + 0.15 * np.sin(2 * np.pi * t / 1.2)))), (90, 100, 240), -1)
        y = int(round(180 + 10 * np.sin(2 * np.pi * t / 2.0)))
        cv2.rectangle(img, (230, y - 30), (330, y + 30), (240, 200, 70), -1)
        a = np.radians(80 * t)                                # clockwise on screen, 80 deg/s
        dx, dy = 50 * np.cos(a), 50 * np.sin(a)
        cv2.line(img, (int(470 - dx), int(180 - dy)), (int(470 + dx), int(180 + dy)), (60, 200, 250), 10)
        k = 0.6 + 0.4 * np.sin(2 * np.pi * t / 1.5)           # breathing between 0.2 and 1.0 of full
        cv2.rectangle(img, (560, 150), (620, 210), tuple(int(20 + (230 - 20) * k) for _ in range(3)), -1)
        frames.append(img)
    return Clip("", FPS, W, H, np.stack(frames), 1.0)


def test_loops_are_found_with_what_loops_and_by_how_much():
    found = {}
    for L in ambient.loops(_loops_clip(), SHOT):
        x = L["box"][0] + L["box"][2] / 2
        found[min((110, "pulse"), (280, "bob"), (470, "spin"), (590, "breathe"), key=lambda c: abs(c[0] - x))[1]] = L
    assert set(found) == {"pulse", "bob", "spin", "breathe"}
    pulse, bob, spin, breathe = (found[k] for k in ("pulse", "bob", "spin", "breathe"))
    assert abs(pulse["period_s"] - 1.2) < 0.05 and [p["prop"] for p in pulse["props"]] == ["scale"]
    assert abs(pulse["props"][0]["amplitude"] - 0.15) < 0.03
    assert abs(bob["period_s"] - 2.0) < 0.07 and bob["props"][0]["prop"] == "y" and abs(bob["props"][0]["amplitude"] - 10) < 1.5
    assert spin["props"][0]["prop"] == "rot" and abs(spin["props"][0]["rate"] - 80) < 4
    assert breathe["props"][0]["prop"] == "opacity" and abs(breathe["props"][0]["low"] - 0.2) < 0.08


def test_a_field_of_drifting_dots_and_a_still_frame():
    rng = np.random.default_rng(3)
    start = rng.uniform(0, 1, (30, 2)) * (W, H)
    vel = np.column_stack([rng.uniform(20, 40, 30), rng.uniform(-10, 10, 30)])     # drifting right, px/s
    frames = []
    for f in range(N):
        img = np.full((H, W, 3), (235, 232, 225), np.uint8)
        for p in (start + vel * f / FPS) % (W, H):
            cv2.circle(img, (int(p[0]), int(p[1])), 3, (40, 40, 40), -1)
        frames.append(img)
    field = ambient.particles(Clip("", FPS, W, H, np.stack(frames), 1.0), SHOT)
    assert field and abs(field["count"] - 30) <= 4 and abs(field["direction_deg"]) < 10
    assert abs(field["speed"]["median"] - np.median(np.hypot(*vel.T))) < 4
    still = Clip("", FPS, W, H, np.repeat(frames[:1], N, axis=0), 1.0)
    assert ambient.particles(still, SHOT) is None and ambient.loops(still, SHOT) == []
