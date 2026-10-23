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


def test_ground_from_an_empty_opening_frame():
    paper, teal = (244, 238, 226), (0, 131, 138)
    img = np.full((720, 1280, 3), paper, np.uint8)
    img[300:] = teal                                          # the sea takes more of the frame and all its border
    img[100:160, 900:1000] = (255, 116, 119)
    assert palette.opening_ground(np.full((720, 1280, 3), paper, np.uint8)) is not None
    assert palette.opening_ground(img) is None
    p = palette.image_palette(img)
    hint = palette.opening_ground(np.full((720, 1280, 3), paper, np.uint8))
    roles = palette.pooled([p], hint)["roles"]
    near = lambda h, rgb: color.delta_e(color.rgb_to_lab(np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], float)),  # noqa: E731
                                        color.rgb_to_lab(np.array(rgb, float))) < 3
    assert near(roles["ground"], paper) and near(roles["ink"], teal)
    assert near(palette.pooled([p])["roles"]["ground"], teal)  # without the opening, the border decides


def test_a_band_of_tint_along_one_edge_is_no_vignette():
    img = np.full((720, 1280, 3), 236, np.uint8)
    img[:160] = 214                                           # a pale band at the top, close to the ground
    img = np.clip(img + np.random.default_rng(1).normal(0, 3, (720, 1280, 1)), 0, 255).astype(np.uint8)
    t = texture.texture(img, "#ececec")
    assert t["vignette"] == 0.0 and t["grain"] < 4


def test_a_halftone_band_is_not_a_line_of_text():
    img = np.full((720, 1280, 3), 240, np.uint8)
    yy, xx = np.mgrid[:120, :1280]
    img[60:180][((np.cos(2 * np.pi * (xx + yy) / 4.67 / np.sqrt(2)) + np.cos(2 * np.pi * (xx - yy) / 4.67 / np.sqrt(2))) > 0.6)] = 40
    cv2.putText(img, "first light", (100, 400), cv2.FONT_HERSHEY_DUPLEX, 3.0, (20, 20, 20), 8, cv2.LINE_AA)
    lines = typeset.text_lines(img, screen_px=4.67)
    assert lines and all(ln["box"][1] > 0.4 for ln in lines)  # only the words, not the band at the top


def test_a_small_vivid_accent_keeps_its_colour():
    img = np.full((720, 1280, 3), (11, 13, 18), np.uint8)
    img[200:420, 300:900] = (27, 32, 48)                       # a large surface one step off the ground
    cv2.putText(img, "2.0", (500, 600), cv2.FONT_HERSHEY_DUPLEX, 5.0, (233, 237, 245), 14, cv2.LINE_AA)
    img[60:100, 1100:1140] = (183, 243, 74)                    # one small lime tile, 0.17 % of the picture
    roles = palette.pooled([palette.image_palette(img)])["roles"]
    rgb = lambda h: np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], float)  # noqa: E731
    assert color.delta_e(color.rgb_to_lab(rgb(roles["accent"])), color.rgb_to_lab(np.array([183, 243, 74.]))) < 6
    assert color.delta_e(color.rgb_to_lab(rgb(roles["ink"])), color.rgb_to_lab(np.array([233, 237, 245.]))) < 8


def test_big_type_with_wide_gaps_is_one_line_and_a_row_of_blocks_is_none():
    img = np.full((720, 1280, 3), 240, np.uint8)
    cv2.putText(img, "W A K E", (80, 300), cv2.FONT_HERSHEY_DUPLEX, 6.0, (20, 20, 20), 22, cv2.LINE_AA)
    for k in range(8):
        img[560:600, 80 + 90 * k:140 + 90 * k] = 20            # squares in a row, like a caption's height
    lines = typeset.text_lines(img)
    assert len(lines) == 1 and lines[0]["box"][2] > 0.45       # the spaced word, whole; not the squares


def test_scanlines_are_not_a_halftone_and_fill_back_in():
    img = np.full((720, 1280, 3), (20, 12, 5), np.uint8)
    img[200:500, 200:1000] = (255, 176, 0)
    img[::4] = (img[::4] * 0.4).astype(np.uint8)                # every fourth row darkened
    t = texture.texture(img)
    assert t["scanlines"] and t["halftone"] is None
    assert typeset.descan(img, t["scanlines"]["period_px"])[300:400, 300:900].min(axis=(0, 1))[0] > 240
