"""Export a film for another tool: `moodreel export hyperframes|remotion <film> [--out dir] [--variant v]`.

HyperFrames

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

Remotion
A Remotion project (`package.json` pins Remotion and React; `npm install` there, then `npm run render` or
`npm run studio`). `public/film/` holds the film; `src/Film.jsx` is the one composition (`Film`, the film's size,
fps and length in frames). On mount it points the document's base at the film folder (the film fetches its media and
fonts by relative paths), brings in the film page's head styles, sets `window.VARIANT`, loads `main.js` as a module
into `#moodreel-stage`, and holds the render (`delayRender`) until the film is ready; every frame then draws itself
with `window.render(frame / fps)` before Remotion takes it. The audio, when delivered, is an `<Audio>`. Remotion has
its own licence (free for individuals and small teams, a company licence otherwise: remotion.dev/license), and is
not a dependency of Moodreel.
"""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

GSAP = "https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"
REMOTION, REACT = "4.0.534", "18.3.1"
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
    _copy_film(film, out / "film")
    w, h = (int(v) for v in f["size"].split("x"))
    audio = ""
    mix = film / "out" / f"mix{suffix}.wav"
    if mix.exists():                                       # the delivered film's music and narration
        shutil.copyfile(mix, out / "film" / "audio.wav")
        audio = (f'      <audio id="moodreel-audio" src="audio.wav" data-start="0" data-duration="{f["duration"]}" '
                 'data-track-index="1"></audio>')
    head = "\n".join("    " + line for line in _head(film).splitlines())   # the page's fonts and styles come along
    (out / "index.html").write_text(PAGE.format(w=w, h=h, dur=f["duration"], name=f["name"] + suffix, gsap=GSAP, head=head,
                                                audio=audio, variant=json.dumps(params) if params else "undefined"))
    if (film / "CREDITS").exists():
        shutil.copyfile(film / "CREDITS", out / "CREDITS")
    return {"composition": str(out / "index.html"), "size": [w, h], "duration": f["duration"], "audio": bool(audio)}


def _copy_film(film: Path, dst: Path) -> None:
    def skip(d, names):                                    # the film's source, not its work folder or deliverables
        return [n for n in names if Path(d) == film and (n in SKIP or n.endswith(".mp4") or n.startswith("poster"))]
    shutil.copytree(film, dst, ignore=skip)


def _head(film: Path) -> str:
    """The film page's own head tags (fonts, styles), without its title and scripts."""
    src_head = re.search(r"<head>(.*?)</head>", (film / "index.html").read_text(), re.S)
    return "\n".join(m.group(0) for m in re.finditer(r"<(link|style)\b.*?(?:</style>|>)", src_head.group(1) if src_head else "", re.S))


ROOT_JSX = """import {{ Composition }} from 'remotion';
import {{ Film }} from './Film';

// Written by `moodreel export remotion`: the film {name}, {w} x {h}, {fps} fps, {frames} frames.
export const Root = () => (
  <Composition id="Film" component={{Film}} durationInFrames={{{frames}}} fps={{{fps}}} width={{{w}}} height={{{h}}}
    defaultProps={{{{ variant: {variant}, audio: {audio} }}}} />
);
"""

FILM_JSX = """import {{ useEffect, useLayoutEffect, useState }} from 'react';
import {{ AbsoluteFill, Audio, cancelRender, continueRender, delayRender, staticFile, useCurrentFrame, useVideoConfig }} from 'remotion';

// A Moodreel film is a picture that is a function of time: its page code (public/film/main.js) mounts a canvas into
// #moodreel-stage and draws frame t with window.render(t). This composition loads it once, holds the render until it
// is ready (fonts, images, media), and draws each frame before Remotion takes it.
const HEAD = {head};

let loading = null;
const load = variant => (loading ??= new Promise((ok, fail) => {{
  const base = document.createElement('base');           // the film fetches media and fonts by relative paths
  base.href = new URL(staticFile('film/'), location.href).href;
  document.head.prepend(base);
  document.head.insertAdjacentHTML('beforeend', HEAD);
  if (variant) window.VARIANT = variant;
  window.addEventListener('error', e => fail(e.error || new Error(e.message)));
  window.addEventListener('unhandledrejection', e => fail(e.reason));
  const script = document.createElement('script');
  script.type = 'module';
  script.src = base.href + 'main.js';
  script.onerror = () => fail(new Error('main.js did not load'));
  document.body.appendChild(script);
  const poll = () => (window.READY ? ok() : setTimeout(poll, 20));
  poll();
}}));

export const Film = ({{ variant, audio }}) => {{
  const frame = useCurrentFrame();
  const {{ fps }} = useVideoConfig();
  const [handle] = useState(() => delayRender('Moodreel film loading'));
  const [ready, setReady] = useState(false);
  useEffect(() => {{
    load(variant).then(() => {{ setReady(true); continueRender(handle); }}, cancelRender);
  }}, []);
  useLayoutEffect(() => {{
    if (ready) window.render(frame / fps);
  }}, [ready, frame, fps]);
  return (
    <AbsoluteFill style={{{{ background: '#000' }}}}>
      <div id="moodreel-stage" style={{{{ position: 'absolute', inset: 0 }}}} />
      {{audio ? <Audio src={{staticFile('film/audio.wav')}} /> : null}}
    </AbsoluteFill>
  );
}};
"""

INDEX_JSX = """import {{ registerRoot }} from 'remotion';
import {{ Root }} from './Root';

registerRoot(Root);
"""


def remotion(film: Path, out: Path | None = None, variant: str | None = None) -> dict:
    from .film.film import _variant
    film = Path(film)
    f, _, suffix = _variant(film, variant)
    params = (f.get("variants") or {}).get(variant) if variant else None
    out = Path(out or film / "out" / f"remotion{suffix}")
    if out.exists():                                       # keep an installed node_modules: only the project is rewritten
        for p in out.iterdir():
            if p.name != "node_modules":
                shutil.rmtree(p) if p.is_dir() else p.unlink()
    out.mkdir(parents=True, exist_ok=True)
    _copy_film(film, out / "public" / "film")
    w, h = (int(v) for v in f["size"].split("x"))
    fps, frames = f["fps"], int(round(f["duration"] * f["fps"]))
    mix = film / "out" / f"mix{suffix}.wav"
    if mix.exists():
        shutil.copyfile(mix, out / "public" / "film" / "audio.wav")
    name = f["name"] + suffix
    (out / "src").mkdir()
    (out / "src" / "index.jsx").write_text(INDEX_JSX.format())
    (out / "src" / "Root.jsx").write_text(ROOT_JSX.format(name=name, w=w, h=h, fps=fps, frames=frames, audio=str(mix.exists()).lower(),
                                                          variant=json.dumps(params) if params else "null"))
    (out / "src" / "Film.jsx").write_text(FILM_JSX.format(head=json.dumps(_head(film))))
    (out / "package.json").write_text(json.dumps({
        "name": re.sub(r"[^a-z0-9-]", "-", name.lower()) + "-remotion", "private": True,
        "scripts": {"studio": "remotion studio src/index.jsx",
                    "render": f"remotion render src/index.jsx Film out/{name}.mp4"},
        "dependencies": {"remotion": REMOTION, "@remotion/cli": REMOTION, "react": REACT, "react-dom": REACT}}, indent=1) + "\n")
    (out / ".gitignore").write_text("node_modules/\nout/\n")
    if (film / "CREDITS").exists():
        shutil.copyfile(film / "CREDITS", out / "CREDITS")
    return {"project": str(out), "composition": "Film", "size": [w, h], "fps": fps, "frames": frames, "audio": mix.exists(),
            "next": f"cd {out} && npm install && npm run render"}
