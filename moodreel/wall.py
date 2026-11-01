"""`moodreel wall`: a word-of-mouth wall (社媒口碑墙) for a product, made from its real posts.

  moodreel wall search <product> [--out out/walls/<slug>] [--platforms youtube,bilibili] [--max 24]
      finds the posts that name the product on platforms that need no login (render/wall.mjs) and numbers them for the
      user to pick from: candidates.json, a contact sheet (candidates.jpg) and CANDIDATES.md, with who posted, the
      views and date, and flags: the product's own account (官方, not word of mouth), an uploader's "no reprint"
      (禁止转载) and a post that says it is paid for (推广)
  moodreel wall record <dir> --pick 3,5,8 [--seconds 6.5] [--at s]
      records each picked post as its platform shows it, muted, in a window sized for a 4K card (clips/, clips.json);
      recording a card again replaces it where it stands; --at starts the video that far in (past an intro)
  moodreel wall make <dir> [--lead 创作者都在聊] [--name <product>] [--duration 5.5]
      the film: the template (kit/wall.js) with the recordings as its cards, in the order picked, each in media/ with its
      source and in CREDITS; rendered at 3840 x 2160 to <dir>/film/<name>.mp4

The posts are other people's work. Nothing is recorded until the user has picked it, every card is credited with its
author and link, and whether a post may be shown is the user's to settle with its author: the tool flags what it can
see (an uploader's no-reprint notice, a post's own paid-promotion label) and records nothing behind a login or a bot
check.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

from . import media
from .film import film as films

REPO = Path(__file__).resolve().parents[1]
WALL = REPO / "render" / "wall.mjs"
FONTS = ["/System/Library/Fonts/Hiragino Sans GB.ttc", "/System/Library/Fonts/STHeiti Medium.ttc",
         "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc"]

MAIN = r"""// A word-of-mouth wall (社媒口碑墙), made by `moodreel wall make`: the posts in wall.json, each a recording in
// media/, on the template in kit/wall.js. Every card's frame is read from media/ at the film's time.
import { stage, texts } from './kit/stage.js';
import { load } from './kit/media.js';
import { socialWall, WALL } from './kit/wall.js';

const spec = await (await fetch('wall.json')).json();
const cards = await load(spec.cards.map(c => c.name));
const T = WALL.title;
let wall, box = null;
stage({
  width: 3840, height: 2160, duration: spec.duration, background: WALL.ground,
  fonts: [`${T.weight} ${T.size}px ${T.family}`, `${T.latin.weight} ${T.latin.size}px ${T.latin.family}`],
  prepare: () => { const c = document.querySelector('canvas'); wall = socialWall(cards, spec, [c.width, c.height]); },
  draw: (g, t) => { box = wall.draw(g, t); },
});
texts(() => [{ id: 'title', text: spec.title.filter(Boolean).join(' '), ...(box || {}) }]);
"""


def slug(product: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", product.lower()).strip("-") or "wall"


def _node(*args: str) -> None:
    subprocess.run(["node", str(WALL), *args], check=True, cwd=REPO)


def _official(post: dict, product: str) -> bool:
    """The product's own account: its posts are announcements, not word of mouth."""
    norm = lambda s: re.sub(r"[\s\-_·.]+", "", (s or "").lower())
    return bool(post.get("author")) and norm(post["author"]).startswith(norm(product))


def search(product: str, out: Path | None = None, platforms: str = "youtube,bilibili", max_posts: int = 24,
           lang: str = "en-US") -> dict:
    out = Path(out or Path("out") / "walls" / slug(product))
    _node("search", product, "--out", str(out), "--platforms", platforms, "--max", str(max_posts), "--lang", lang)
    data = json.loads((out / "candidates.json").read_text())
    for p in data["posts"]:
        p["official"] = _official(p, product)
    (out / "candidates.json").write_text(json.dumps(data, indent=1, ensure_ascii=False))
    sheet(out)
    return {"dir": str(out), "candidates": len(data["posts"]), "sheet": str(out / "candidates.jpg")}


def _flags(p: dict) -> str:
    return " ".join(f for f in ("官方" if p.get("official") else "", "禁止转载" if p.get("notice") else "",
                               "推广" if p.get("paid") else "") if f)


def sheet(out: Path, columns: int = 6, tile: tuple[int, int] = (360, 202)) -> Path:
    """The candidates as a numbered contact sheet, and as a table (CANDIDATES.md), for the user to pick from."""
    from PIL import Image, ImageDraw, ImageFont
    out = Path(out)
    data = json.loads((out / "candidates.json").read_text())
    posts = data["posts"]
    font = next((f for f in FONTS if Path(f).exists()), None)
    face = lambda size: ImageFont.truetype(font, size) if font else ImageFont.load_default()
    tw, th, text_h, pad = tile[0], tile[1], 74, 10
    rows = (len(posts) + columns - 1) // columns
    img = Image.new("RGB", (columns * (tw + pad) + pad, rows * (th + text_h + pad) + pad), "#111")
    d = ImageDraw.Draw(img)
    for i, p in enumerate(posts):
        x, y = pad + (i % columns) * (tw + pad), pad + (i // columns) * (th + text_h + pad)
        thumb = out / "thumbs" / f"{p['n']:02d}.jpg"
        if thumb.exists():
            im = Image.open(thumb).convert("RGB")
            im.thumbnail((tw, th))
            img.paste(im, (x + (tw - im.width) // 2, y + (th - im.height) // 2))
        d.rectangle([x, y, x + 54, y + 34], fill="#f2c94c")
        d.text((x + 8, y + 3), f"{p['n']}", fill="#000", font=face(26))
        tag = f"{p['platform']} {'short' if p['kind'] == 'short' else ''}".strip()
        d.text((x + 62, y + 6), tag, fill="#fff", font=face(18), stroke_width=2, stroke_fill="#000")
        if _flags(p):
            d.text((x + 6, y + th - 30), _flags(p), fill="#ff6b6b", font=face(20), stroke_width=2, stroke_fill="#000")
        title = p.get("title") or ""
        d.text((x, y + th + 6), title[:24], fill="#eee", font=face(18))
        d.text((x, y + th + 30), title[24:48], fill="#eee", font=face(18))
        d.text((x, y + th + 52), f"{(p.get('author') or '')[:14]}  {p.get('views') or ''}  {p.get('date') or ''}"[:44],
               fill="#999", font=face(15))
    img.save(out / "candidates.jpg", quality=90)
    lines = [f"# Candidates for the wall: {data['query']}", "",
             f"Searched {data['searched'][:16].replace('T', ' ')} on {', '.join(data['platforms'])}. Pick by number "
             "(`moodreel wall record <dir> --pick 3,5,8`); the wall shows them in the order picked.", "",
             "| # | platform | title | author | views | date | length | flags | link |", "|---|---|---|---|---|---|---|---|---|"]
    cell = lambda s: str(s or "").replace("|", "/").replace("\n", " ")
    lines += [f"| {p['n']} | {p['platform']}{' short' if p['kind'] == 'short' else ''} | {cell(p.get('title'))[:70]} | "
              f"{cell(p.get('author'))} | {cell(p.get('views'))} | {cell(p.get('date'))} | {cell(p.get('duration'))} | "
              f"{_flags(p)} | {p['url']} |" for p in posts]
    (out / "CANDIDATES.md").write_text("\n".join(lines) + "\n")
    return out / "candidates.jpg"


def record(out: Path, picks: list[int], seconds: float = 6.5, lang: str = "en-US", at: float = 0.0) -> dict:
    out = Path(out)
    _node("record", str(out), "--pick", ",".join(map(str, picks)), "--seconds", str(seconds), "--lang", lang, "--at", str(at))
    clips = json.loads((out / "clips.json").read_text())
    run = json.loads((out / "record.json").read_text())             # this run: what was recorded, what failed and why
    return {"cards": len(clips), "recorded": run["recorded"], "failed": run["failed"],
            "flagged": {c["n"]: _flags(c) for c in clips if _flags(c)}}


def make(out: Path, name: str | None = None, lead: str = "创作者都在聊", duration: float = 5.5, render: bool = True,
         replace: bool = False) -> dict:
    out = Path(out)
    data = json.loads((out / "candidates.json").read_text())
    clips = json.loads((out / "clips.json").read_text())
    if not clips:
        raise SystemExit("no recorded posts: moodreel wall record <dir> --pick ...")
    name = name or data["query"]
    d = out / "film"
    if d.exists():
        if not replace:
            raise SystemExit(f"{d} exists (--replace keeps it as film.prev and makes a new one)")
        prev = out / "film.prev"
        if prev.exists():
            raise SystemExit(f"{prev} exists too: move it away first")
        d.rename(prev)
    d.mkdir(parents=True)
    shutil.copytree(REPO / "kit", d / "kit", ignore=shutil.ignore_patterns("README.md", "vendor"))
    from .pack.kit import vendor_three
    three = vendor_three(d / "kit")
    film_name = f"{slug(name)}-wall"
    (d / "film.json").write_text(json.dumps({"name": film_name, "style": "social-wall", "size": "3840x2160", "fps": 30,
                                             "duration": duration, "poster": round(duration * 0.6, 2)}, indent=1))
    (d / "index.html").write_text('<!doctype html><html><head><meta charset="utf-8"><title>' + film_name +
                                  '</title></head><body><script type="module" src="main.js"></script></body></html>\n')
    (d / "main.js").write_text(MAIN)
    (d / "CREDITS").write_text(f"{film_name}: a word-of-mouth wall for {name}\n\nThe posts on the wall, each recorded as "
                               "its platform shows it; they are their authors' work, shown at the user's pick:\n\n")
    cards = []
    for c in clips:
        card = f"card{c['n']:02d}"
        terms = (f"© {c.get('author') or 'its author'}, as posted on {c['platform']}; recorded {c['recorded'][:10]} and "
                 "shown at the user's pick" + (f"; the uploader marks it {c['notice']}" if c.get("notice") else "")
                 + ("; the post says it is paid promotion" if c.get("paid") else ""))
        media.add(d, out / c["file"], card, c["url"], terms)
        w, h = c["size"]
        cards.append({"name": card, "aspect": round(w / h, 4), "platform": c["platform"], "url": c["url"],
                      "author": c.get("author") or ""})
    with open(d / "CREDITS", "a") as cr:
        cr.write(f"\nType: system faces, not shipped (PingFang SC, Avenir Next Condensed; Noto Sans SC and Roboto "
                 f"Condensed elsewhere).\n- {three}\n")
    (d / "wall.json").write_text(json.dumps({"title": [lead, name], "duration": duration, "cards": cards}, indent=1,
                                            ensure_ascii=False))
    res = {"film": str(d), "cards": len(cards)}
    if render:
        res |= films.deliver(d)
    return res
