"""Numbers that count: how a printed number is parsed, misreads dropped, and a counter read back from a clip."""
from __future__ import annotations

import cv2
import numpy as np
import pytest

from moodreel.motion import counter, eases
from moodreel.video import Clip


def test_printed_numbers_parse_with_their_format():
    assert counter.parse("4,200") == {"value": 4200.0, "prefix": "", "suffix": "", "decimals": 0, "sep": ","}
    assert counter.parse("$12.5M") == {"value": 12.5, "prefix": "$", "suffix": "M", "decimals": 1, "sep": ""}
    assert counter.parse("98%")["suffix"] == "%"
    assert counter.parse("2,17") is None and counter.parse("1.2.3") is None and counter.parse("") is None


def test_the_longest_monotone_run_drops_misreads():
    v = np.array([np.nan, 0, 120, 950, 400, 610, 3959, 820, 900, 900])     # 950 and 3959: a digit misread
    keep = counter._monotone(v)
    assert list(v[keep]) == [0, 120, 400, 610, 820, 900, 900]
    assert counter._monotone(v[::-1]).sum() == 7                          # counting down is a count too


FPS, W, H, N = 30, 640, 360, 75
GROUND = (240, 238, 232)


def _clip():
    """0 to 900 over 1.2 s (power2.out) in the middle; a year that never changes; a price sliding in from the left."""
    frames = []
    for f in range(N):
        img = np.full((H, W, 3), GROUND, np.uint8)
        v = 900 * float(eases.get("power2.out")(np.clip((f / FPS - 0.5) / 1.2, 0, 1)))
        cv2.putText(img, str(round(v)), (250, 160), cv2.FONT_HERSHEY_DUPLEX, 2.2, (20, 20, 20), 4, cv2.LINE_AA)
        cv2.putText(img, "2024", (40, 320), cv2.FONT_HERSHEY_DUPLEX, 1.2, (20, 20, 20), 2, cv2.LINE_AA)
        x = int(round(-200 + 640 * float(eases.get("power3.out")(np.clip((f / FPS - 0.8) / 0.6, 0, 1)))))
        cv2.putText(img, "$49", (x, 260), cv2.FONT_HERSHEY_DUPLEX, 1.4, (200, 40, 40), 3, cv2.LINE_AA)
        frames.append(img)
    return Clip("", FPS, W, H, np.stack(frames), 1.0)


@pytest.mark.skipif(not counter.available(), reason="needs tesseract")
def test_a_counter_is_read_and_still_or_sliding_numbers_are_not():
    found = counter.find(_clip(), {"id": "A", "start": 0, "end": N}, (12, 54))
    assert len(found) == 1
    c = found[0]
    f = c["props"]["value"]
    assert c["counter"]["to"] == 900 and abs(f["t0"] - 0.5) < 1.5 / FPS and abs(f["t1"] - 1.7) < 2 / FPS
    assert eases.shape_class(f["best"]) == "out"
    # the digits' pieces the tracker found inside its box go with it; what is outside stays
    inside = {"kind": "move", "box": [300, 100, 30, 50]}
    outside = {"kind": "appear", "box": [40, 290, 100, 40]}
    assert counter.absorb(found, [inside, outside], found) == [outside]
