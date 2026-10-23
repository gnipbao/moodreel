"""The style library: the user's styles first (~/.moodreel/styles, or $MOODREEL_HOME/styles), then the built-in ones
(the repository's styles/). Each library has an index.json; a style is found by slug, English or Chinese name."""
from __future__ import annotations

import json
import os
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

# what Moodreel can draw beyond flat 2D: a style whose needs are all here can be made now
CAPABLE = {"music-led"}


def home() -> Path:
    return Path(os.environ.get("MOODREEL_HOME", Path.home() / ".moodreel"))


def user_dir() -> Path:
    return home() / "styles"


def builtin_dir() -> Path:
    return REPO / "styles"


def _index(root: Path, origin: str) -> list[dict]:
    f = root / "index.json"
    if not f.exists():
        return []
    return [{**s, "origin": origin, "path": str(root / s["slug"])} for s in json.loads(f.read_text())["styles"]]


def all_styles() -> list[dict]:
    return _index(user_dir(), "user") + _index(builtin_dir(), "builtin")


def find(name: str) -> dict | None:
    key = name.strip().lower()
    for s in all_styles():
        if key in {s["slug"].lower(), str(s.get("name", "")).lower(), str(s.get("name_zh", "")).lower()}:
            return s
    return None


def register(entry: dict) -> None:
    root = user_dir()
    root.mkdir(parents=True, exist_ok=True)
    f = root / "index.json"
    index = json.loads(f.read_text()) if f.exists() else {"styles": []}
    index["styles"] = [s for s in index["styles"] if s["slug"] != entry["slug"]] + [entry]
    f.write_text(json.dumps(index, indent=1, ensure_ascii=False) + "\n")
