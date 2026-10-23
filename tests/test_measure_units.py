"""Static measurements on synthetic pictures with known answers."""
from __future__ import annotations

import cv2
import numpy as np

from moodreel.measure import color, layout, palette, rhythm, texture, typeset


def poster(ground=(240, 232, 214), ink=(20, 20, 30), accent=(230, 40, 120), w=1280, h=720):
    img = np.full((h, w, 3), ground, np.uint8)
    cv2.rectangle(img, (160, 120), (760, 220), ink, -1)                 # a heavy headline bar
    cv2.circle(img, (1000, 450), 60, accent, -1)                        # a small saturated accent
    cv2.rectangle(img, (160, 300), (700, 330), ink, -1)
    return img


def test_lab_round_trip_and_delta_e():
    rgb = np.array([31.0, 111.0, 235.0])
    assert np.allclose(color.lab_to_rgb(color.rgb_to_lab(rgb)), rgb, atol=1)
    assert abs(color.delta_e(color.rgb_to_lab(np.array([0, 0, 0.])), color.rgb_to_lab(np.array([255, 255, 255.]))) - 100) < 0.5
    assert color.contrast([0, 0, 0], [255, 255, 255]) == 21.0


def test_palette_roles():
    p = palette.pooled([palette.image_palette(poster())])
    r = p["roles"]
    ground = np.array([int(r["ground"][i:i + 2], 16) for i in (1, 3, 5)], float)
    assert color.delta_e(color.rgb_to_lab(np.array([240, 232, 214.])), color.rgb_to_lab(ground)) < 3
    assert r["ink"].startswith("#1") and r["ink_contrast"] > 10
    assert "accent" in r and p["structure"]["ground"] == "light"


def test_unity_splits_two_styles():
    light = palette.image_palette(poster())
    dark = palette.image_palette(poster(ground=(12, 14, 20), ink=(230, 235, 245), accent=(30, 110, 235)))
    u = palette.unity([light, light, dark])
    assert not u["unified"] and sorted(map(sorted, u["groups"])) == [[0, 1], [2]]


def test_grain_vignette_and_edges():
    clean = texture.texture(poster())
    assert clean["summary"]["grain"] == "none" and clean["summary"]["edges"] == "crisp"
    noisy = np.clip(poster().astype(float) + np.random.default_rng(0).normal(0, 6, (720, 1280, 1)), 0, 255).astype(np.uint8)
    assert texture.texture(noisy)["summary"]["grain"] in ("visible", "heavy")
    yy, xx = np.mgrid[:720, :1280]
    r2 = ((xx - 640) / 640) ** 2 + ((yy - 360) / 360) ** 2
    vig = (np.full((720, 1280, 3), 200.0) * (1 - 0.15 * r2)[..., None]).astype(np.uint8)
    assert texture.texture(vig)["summary"]["vignette"] in ("soft", "strong")
    soft = cv2.GaussianBlur(poster(), (0, 0), 3)
    assert texture.texture(soft)["edge_sharpness"] < clean["edge_sharpness"]


def test_halftone_and_scanlines_but_not_codec_blocks():
    yy, xx = np.mgrid[:720, :1280]
    u, v = (xx + yy) / np.sqrt(2), (xx - yy) / np.sqrt(2)
    dots = (np.cos(2 * np.pi * u / 6) + np.cos(2 * np.pi * v / 6)) > 0.5
    ht = np.where(dots[..., None], np.array([30, 60, 200]), np.array([240, 235, 220])).astype(np.uint8)
    t = texture.texture(ht)
    assert t["halftone"] and abs(t["halftone"]["period_px"] - 6) < 1 and t["scanlines"] is None
    sl = np.full((720, 1280, 3), 120, np.uint8)
    sl[::3] = 80
    assert texture.texture(sl)["scanlines"]["period_px"] == 3.0
    ok, enc = cv2.imencode(".jpg", poster(), [cv2.IMWRITE_JPEG_QUALITY, 30])
    assert texture.texture(cv2.imdecode(enc, cv2.IMREAD_COLOR))["halftone"] is None


def test_layout_margins_and_alignment():
    lay = layout.layout(poster(), color.hex_([240, 232, 214]))
    assert abs(lay["margins"]["left"] - 160 / 1280) < 0.02 and lay["dominant_alignment"] == "left"


def test_text_lines_and_weight():
    img = np.full((720, 1280, 3), 245, np.uint8)
    cv2.putText(img, "HEADLINE TYPE", (100, 200), cv2.FONT_HERSHEY_SIMPLEX, 3.0, (20, 20, 20), 14, cv2.LINE_AA)
    cv2.putText(img, "a thin line of body copy", (100, 400), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (20, 20, 20), 2, cv2.LINE_AA)
    lines = typeset.text_lines(img)
    assert len(lines) >= 2
    big, small = lines[0], lines[-1]
    assert big["height"] > 1.5 * small["height"] and big["stroke_ratio"] > small["stroke_ratio"]


def test_tempo_and_on_beat():
    sr, bpm = rhythm.SR, 120
    y = np.zeros(sr * 8, np.float32)
    for k in range(16):                                     # a click every half second
        i = int(k * 0.5 * sr)
        y[i:i + 400] = np.sin(np.arange(400) * 2 * np.pi * 1800 / sr) * np.hanning(400)
    env = rhythm.onset_envelope(y)
    found, _ = rhythm.tempo(env)
    assert abs(found - bpm) < 3
    beats = rhythm.beats(env, found)
    res = rhythm.on_beat([0.5, 1.0, 2.5, 3.0], beats, 0.04)
    assert res["share"] == 1.0 and res["chance"] < 0.2
