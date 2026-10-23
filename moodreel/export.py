"""Export a film as a HyperFrames composition: `moodreel export hyperframes <film> [--out dir] [--variant v]`.

A Moodreel film is already what HyperFrames asks of a composition: a picture that is a function of time, seekable to
any frame. The export wraps it: `<out>/film/` holds the film (its page code, kit, media, score.js, voice.js and its
mixed audio), and `<out>/index.html` is a standalone composition (root `data-composition-id="main"`, the film's
`data-width`, `data-height` and `data-duration`) whose one paused GSAP timeline runs a proxy from 0 to the film's
length through a property whose setter calls the film's `window.render(t)`, so each seek HyperFrames makes draws
exactly that frame (a seek suppresses callbacks such as onUpdate, but still sets the property). The film's stage
mounts into `#moodreel-stage` (kit/stage.js does when the element exists); a `<base>` keeps the film's relative paths
(media, images, fonts) pointing into `film/`. The audio, when the film has been delivered with music or narration,
is a timed `<audio>` clip. Check it with `npx hyperframes check` in the export folder, render
with `npx hyperframes render` (HyperFrames is not a dependency of Moodreel).
"""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

GSAP = "https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"
SKIP = {"out", "build.sh", "TREATMENT.md"}

PAGE = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width={w}, height={h}" />
    <title>{name}</title>
    <base href="film/" />
    <script src="{gsap}"></script>
    <style>
      html, body {{ width: 100%; height: 100%; margin: 0; background: #000; }}
      #root {{ position: relative; width: 100%; height: 100%; overflow: hidden; }}
      #moodreel-stage {{ position: absolute; inset: 0; }}
    </style>
{head}
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-width="{w}" data-height="{h}" data-duration="{dur}">
      <div id="moodreel-stage" class="clip" data-start="0" data-duration="{dur}" data-track-index="0"></div>
{audio}
    </div>
    <script>window.VARIANT = {variant};</script>
    <script type="module" src="main.js"></script>
    <script>
      // the film draws itself as a function of time: one paused timeline carries t from 0 to its length through a
      // property whose setter calls the film's render(t), so every seek draws that frame (a seek suppresses callbacks
      // like onUpdate; it still sets the property). Registered once the film is ready (fonts, images, media loaded).
      (function bind() {{
        if (!window.READY) return setTimeout(bind, 20);
        let now = 0;
        const clock = {{ get t() {{ return now; }}, set t(v) {{ now = v; window.render(v); }} }};
        const tl = gsap.timeline({{ paused: true }});
        tl.to(clock, {{ t: {dur}, duration: {dur}, ease: 'none' }}, 0);
        window.__timelines['main'] = tl;
        if (window.__hfForceTimelineRebind) window.__hfForceTimelineRebind();
      }})();
    </script>
  </body>
</html>
"""


def hyperframes(film: Path, out: Path | None = None, variant: str | None = None) -> dict:
    from .film.film import _variant
    film = Path(film)
    f, _, suffix = _variant(film, variant)
    params = (f.get("variants") or {}).get(variant) if variant else None
    out = Path(out or film / "out" / f"hyperframes{suffix}")
    if out.exists():
        shutil.rmtree(out)
    def skip(d, names):                                    # the film's source, not its work folder or deliverables
        return [n for n in names if Path(d) == film and (n in SKIP or n.endswith(".mp4") or n.startswith("poster"))]
    shutil.copytree(film, out / "film", ignore=skip)
    w, h = (int(v) for v in f["size"].split("x"))
    audio = ""
    mix = film / "out" / f"mix{suffix}.wav"
    if mix.exists():                                       # the delivered film's music and narration
        shutil.copyfile(mix, out / "film" / "audio.wav")
        audio = (f'      <audio id="moodreel-audio" src="audio.wav" data-start="0" data-duration="{f["duration"]}" '
                 'data-track-index="1"></audio>')
    # the film page's own head (fonts, styles) comes along; its title and scripts don't
    src_head = re.search(r"<head>(.*?)</head>", (film / "index.html").read_text(), re.S)
    tags = re.finditer(r"<(link|style)\b.*?(?:</style>|>)", src_head.group(1) if src_head else "", re.S)
    head = "\n".join("    " + m.group(0) for m in tags)
    (out / "index.html").write_text(PAGE.format(w=w, h=h, dur=f["duration"], name=f["name"] + suffix, gsap=GSAP, head=head,
                                                audio=audio, variant=json.dumps(params) if params else "undefined"))
    if (film / "CREDITS").exists():
        shutil.copyfile(film / "CREDITS", out / "CREDITS")
    return {"composition": str(out / "index.html"), "size": [w, h], "duration": f["duration"], "audio": bool(audio)}
