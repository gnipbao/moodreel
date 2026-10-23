"""The blind-distillation packets name nothing, and the score follows the judges' verdicts."""
from __future__ import annotations

import json
from pathlib import Path

from moodreel.bench import blind


def _project(root: Path, film: str):
    p = root / film / "project"
    for d in ("refs", "kit", "evidence/motion-vid01", "measure"):
        (p / d).mkdir(parents=True)
    (p / "refs" / "vid01.mp4").write_bytes(b"")
    (p / "MEASURE.md").write_text("# Measurements\n")
    (p / "measure" / "motion.json").write_text(json.dumps({"per_video": {"vid01": {"source": {"path": f"/home/u/{film}.mp4", "fps": 24}}}}))
    (p / "evidence" / "motion-vid01" / "motion.json").write_text(json.dumps({"source": {"path": f"/x/{film}.mp4"}}))


def test_packets_hide_the_film_and_scores_count_same_sections(tmp_path):
    _project(tmp_path / "rt", "swiss-programme")
    key = blind.make(tmp_path / "rt", tmp_path / "blind")
    assert key == {"A": {"film": "swiss-programme", "style": "swiss-motion"}}
    packet = tmp_path / "blind" / "A" / "packet"
    text = "".join(f.read_text(errors="ignore") for f in packet.rglob("*") if f.is_file())
    assert "swiss" not in text.lower() and "/home/" not in text and (packet / "BRIEF.md").exists()
    (tmp_path / "blind" / "A" / "verdict.json").write_text(json.dumps(
        {"sections": {str(i): "same" if i <= 8 else "partly" for i in range(1, 12)}}))
    md = blind.score(tmp_path / "blind")
    assert "| 8/11 | pass |" in md and "Judged: 1 of 1" in md
