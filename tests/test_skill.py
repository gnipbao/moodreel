"""The skill's references exist, and the commands it tells the director to run exist."""
from __future__ import annotations

import re
from pathlib import Path

from moodreel import cli

SKILL = Path(__file__).resolve().parents[1] / "skills" / "moodreel"


def test_every_reference_the_skill_names_exists():
    text = "".join(p.read_text() for p in SKILL.rglob("*.md"))
    for ref in set(re.findall(r"`(references/[\w/.-]+\.md)`", text)):
        assert (SKILL / ref).exists(), ref


def test_frontmatter():
    head = (SKILL / "SKILL.md").read_text().split("---")[1]
    assert "name: moodreel" in head and "description:" in head


def test_every_command_the_skill_uses_exists():
    text = "".join(p.read_text() for p in SKILL.rglob("*.md"))
    used = set(re.findall(r"moodreel ([a-z][a-z-]+)", text)) - {"measure:", "pack:", "s"}
    parser_cmds = {"intake", "measure", "frame-check", "kit", "scaffold", "motion-check", "pack", "styles", "film", "render",
                   "motion", "bench", "sketch", "score", "media", "voice", "export", "csd", "samples"}
    assert used <= parser_cmds | {"film"}, used - parser_cmds
    assert cli.main(["styles", "swiss"]) is None
