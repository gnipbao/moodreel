"""Brush marks: whether a reference is laid in visible marks (knife dabs, bristle strokes, crayon, dry brush), and
how big they are and which way they run.

A painting is textured inside its shapes, densely edged (many short edges, not a few long ones) and its texture runs
in directions (the structure tensor's coherence is middling: one mark at a time, but marks in many places). A flat
design's texture is its few straight shape edges (coherence near 1, few edges); grain and a printed screen are dense
but go every way (coherence near 0). Marks are reported only between those. Their scale is the mean distance between
edges along a line (one over the share of edge pixels, at the work width): a mark's own highlight and shadow add edges
inside it, so this is the spacing of the marks' edges rather than their width, a scale to compare like with like;
their direction is the coherence-weighted axial mean of the strokes' long axes, with how much they agree.

Washes and ink lines are flat inside, like a vector shape, and aren't told apart here: the director reads them from
the pictures (soft, wandering edges, pooled rims, a bleed).
"""
from __future__ import annotations

import cv2
import numpy as np

TEXTURE = 4.0        # grey levels of mid-frequency texture for a pixel to count as textured
COVERS = 0.3         # share of the frame textured
EDGES = 0.03         # share of edge pixels (Canny, at the work width)
PIECES = 300         # ...in this many separate pieces at least
COHERENT = (0.3, 0.92)


def read(img: np.ndarray) -> dict | None:
    """img: RGB at the texture's work width."""
    g = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY).astype(np.float32)
    hp = g - cv2.GaussianBlur(g, (0, 0), 6)
    textured = np.sqrt(cv2.GaussianBlur(hp * hp, (0, 0), 8)) > TEXTURE
    edges = cv2.Canny(cv2.GaussianBlur(g.astype(np.uint8), (3, 3), 0), 40, 100) > 0
    pieces = cv2.connectedComponents(edges.astype(np.uint8), connectivity=8)[0] - 1
    if textured.mean() < COVERS or edges.mean() < EDGES or pieces < PIECES:
        return None
    gs = cv2.GaussianBlur(g, (0, 0), 1.0)
    gx, gy = cv2.Sobel(gs, cv2.CV_32F, 1, 0, ksize=3), cv2.Sobel(gs, cv2.CV_32F, 0, 1, ksize=3)
    jxx, jyy, jxy = (cv2.GaussianBlur(a, (0, 0), 5) for a in (gx * gx, gy * gy, gx * gy))
    coherence = np.sqrt((jxx - jyy) ** 2 + 4 * jxy ** 2) / (jxx + jyy + 1e-6)
    coh = float(np.median(coherence[textured]))
    if not COHERENT[0] <= coh <= COHERENT[1]:
        return None
    # a mark's long axis is across the gradient: the tensor's angle plus a right angle, axial (a stroke has no head)
    along = 0.5 * np.arctan2(2 * jxy, jxx - jyy) + np.pi / 2
    w = coherence * textured
    c, s = (w * np.cos(2 * along)).sum(), (w * np.sin(2 * along)).sum()
    agree = float(np.hypot(c, s) / max(w.sum(), 1e-6))
    return {"coverage": round(float(textured.mean()), 2), "edge_spacing_px": round(1.0 / float(edges.mean()), 1),
            "coherence": round(coh, 2),
            "direction_deg": round(float(np.degrees(0.5 * np.arctan2(s, c))) % 180, 1), "agreement": round(agree, 2),
            "edge_pieces": int(pieces)}
