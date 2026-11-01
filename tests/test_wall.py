"""moodreel wall: the candidates a user picks from, the film made from the picked posts, and the template's layout.

The browser half (render/wall.mjs: searching and recording) needs the platforms and isn't run here; everything after it
is, on synthetic clips."""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest
from PIL import Image

from moodreel import wall

REPO = Path(__file__).resolve().parents[1]
needs_three = pytest.mark.skipif(not (REPO / "node_modules" / "three" / "build" / "three.module.js").exists()
                                 or shutil.which("node") is None, reason="needs npm install")


def _wall(tmp_path: Path, sizes=((90, 160), (160, 128), (90, 160))) -> Path:
    d = tmp_path / "w"
    (d / "clips").mkdir(parents=True)
    (d / "thumbs").mkdir()
    posts, clips = [], []
    for n, (w, h) in enumerate(sizes, 1):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", f"testsrc2=size={w}x{h}:rate=30:duration=1",
                        str(d / "clips" / f"{n:02d}.mp4")], check=True)
        Image.new("RGB", (120, 68), "#345").save(d / "thumbs" / f"{n:02d}.jpg")
        posts.append({"n": n, "platform": "bilibili" if n == 2 else "youtube", "kind": "short" if h > w else "video",
                      "id": f"v{n}", "url": f"https://example.org/{n}", "title": f"测试帖子 {n}", "author": "Acme" if n == 3 else f"u{n}",
                      "views": "12K views", "notice": "未经作者授权，禁止转载" if n == 2 else None})
        clips.append({"n": n, "file": f"clips/{n:02d}.mp4", "platform": posts[-1]["platform"], "kind": posts[-1]["kind"],
                      "url": f"https://example.org/{n}", "title": f"测试帖子 {n}", "author": posts[-1]["author"],
                      "notice": posts[-1]["notice"], "recorded": "2026-11-01T00:00:00Z", "size": [w, h]})
    (d / "candidates.json").write_text(json.dumps({"query": "Acme", "searched": "2026-11-01T00:00:00Z",
                                                   "platforms": ["youtube", "bilibili"], "posts": posts}, ensure_ascii=False))
    (d / "clips.json").write_text(json.dumps(clips, ensure_ascii=False))
    return d


def test_the_products_own_account_is_not_word_of_mouth():
    assert wall._official({"author": "YouMind"}, "YouMind") and wall._official({"author": "you mind official"}, "YouMind")
    assert not wall._official({"author": "卷卷姐"}, "YouMind") and not wall._official({}, "YouMind")


def test_the_candidates_come_numbered_with_their_flags(tmp_path):
    d = _wall(tmp_path)
    data = json.loads((d / "candidates.json").read_text())
    for p in data["posts"]:
        p["official"] = wall._official(p, "Acme")
    (d / "candidates.json").write_text(json.dumps(data, ensure_ascii=False))
    jpg = wall.sheet(d, columns=2)
    assert Image.open(jpg).size[0] > 2 * 120
    table = (d / "CANDIDATES.md").read_text()
    assert "| 2 | bilibili | 测试帖子 2 | u2 |" in table and "禁止转载" in table.split("| 2 |")[1].split("\n")[0]
    assert "官方" in table.split("| 3 |")[1].split("\n")[0] and "官方" not in table.split("| 1 |")[1].split("\n")[0]


@needs_three
def test_a_wall_is_made_from_the_picked_posts_in_their_order(tmp_path):
    d = _wall(tmp_path)
    r = wall.make(d, render=False)
    film = d / "film"
    spec = json.loads((film / "wall.json").read_text())
    assert r["cards"] == 3 and spec["title"] == ["创作者都在聊", "Acme"] and spec["duration"] == 5.5
    assert [c["name"] for c in spec["cards"]] == ["card01", "card02", "card03"]
    assert spec["cards"][0]["aspect"] == round(90 / 160, 4)
    manifest = json.loads((film / "media" / "manifest.json").read_text())
    assert manifest["card02"]["source"] == "https://example.org/2" and "禁止转载" in manifest["card02"]["license"]
    credits = (film / "CREDITS").read_text()
    assert "© u2, as posted on bilibili" in credits and "three.js" in credits
    assert (film / "kit" / "wall.js").exists() and (film / "kit" / "vendor" / "three" / "three.module.js").exists()
    with pytest.raises(SystemExit):
        wall.make(d, render=False)                                   # an existing film is kept unless --replace
    wall.make(d, render=False, replace=True)
    assert (d / "film.prev" / "wall.json").exists() and (d / "film" / "wall.json").exists()


@needs_three
def test_the_templates_layout_puts_the_references_cards_where_it_did(tmp_path):
    d = _wall(tmp_path)
    wall.make(d, render=False)
    widths = [569, 428, 373, 440, 373, 470, 384, 369, 435, 374, 374, 368, 372]   # the reference's cards at a 679 px row
    js = ("import('./kit/wall.js').then(m => console.log(JSON.stringify(m.layout(" +
          json.dumps([w / 679 for w in widths]) + "))))")
    out = subprocess.run(["node", "--input-type=module", "-e", js], cwd=d / "film", capture_output=True, text=True, check=True)
    cards = json.loads(out.stdout)
    assert [c["row"] for c in cards] == [0] * 6 + [1] * 7
    assert all(abs(c["h"] - 679) < 0.5 for c in cards)
    assert abs(cards[0]["w"] - 569) < 0.5 and abs((cards[1]["x"] - cards[1]["w"] / 2) - (cards[0]["x"] + cards[0]["w"] / 2) - 31) < 0.5
    wide = json.loads(subprocess.run(["node", "--input-type=module", "-e", js.replace(json.dumps([w / 679 for w in widths]),
                                     json.dumps([1.5] * 12))], cwd=d / "film", capture_output=True, text=True, check=True).stdout)
    assert max(c["row"] for c in wide) >= 2                          # wide cards take more rows rather than shrink to slivers
