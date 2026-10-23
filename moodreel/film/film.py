"""Films: `moodreel film new | check | deliver`.

  films/<name>/film.json      the style it follows, size, frame rate, length, poster time
  films/<name>/main.js        the film, drawn as a function of time with the style's kit (copied in: self-contained)
  films/<name>/TREATMENT.md   three candidate structures, the choice, shots and beats, written before drawing
  films/<name>/CREDITS        every third-party asset and its licence
  films/<name>/build.sh       one command from source to <name>.mp4
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

from .. import library

REPO = Path(__file__).resolve().parents[2]
RENDER = REPO / "render" / "render.mjs"
CJK = re.compile(r"[　-鿿가-힯぀-ヿ]")

MAIN = r"""import { stage, texts } from './kit/stage.js';
import { clamp } from './kit/core.js';
import { SIZE, PALETTE, TYPE } from './kit/tokens.js';
import { enter, exit } from './kit/motion.js';

// The film, as a function of time: draw(g, t) paints the whole frame at second t, from nothing but t.
// Follow the style's STYLE.md; take timings and eases from kit/motion.js, colours and sizes from kit/tokens.js.
const [W, H] = SIZE;
const DUR = __DUR__;

// every line of on-screen text, with when it is on screen: the reading-time check reads these through TEXTS
const LINES = [
  { id: 'title', text: '__NAME__', at: 0.5, until: 3.5, x: W * 0.1, y: H * 0.5 },
];

stage({
  width: W, height: H, duration: DUR, background: PALETTE.ground,
  fonts: [`${TYPE.titleWeight} ${Math.round(TYPE.title * H)}px ${TYPE.display}`],
  draw: (g, t) => {
    for (const l of LINES) {
      const a = enter(t, l.at) * (1 - exit(t, l.until));
      if (a <= 0) continue;
      g.globalAlpha = clamp(a);
      g.fillStyle = PALETTE.ink;
      g.font = `${TYPE.titleWeight} ${TYPE.title * H}px ${TYPE.display}`;
      g.fillText(l.text, l.x, l.y);
      g.globalAlpha = 1;
    }
  },
});

// text boxes in output pixels while each line is fully shown
texts(t => LINES.filter(l => t >= l.at + 0.5 && t <= l.until).map(l => {
  const k = innerWidth / W, h = TYPE.title * H;
  return { id: l.id, text: l.text, x0: l.x * k, y0: (l.y - h) * k, x1: (l.x + l.text.length * h * 0.6) * k, y1: l.y * k };
}));
"""

TREATMENT = """# Treatment: {name}

Style: {style}. Read its STYLE.md first; DEMO.md and the demo source only after this treatment exists.

## Brief

Topic, audience, length, size, the words or points that must appear, brand material, music.

## Three structures

1. ...
2. ...
3. ...

Chosen: ... because ...

## Logline and arc

One sentence; then setup, turn, ending.

## Shots

| # | time | framing | camera | duration | why |
|---|---|---|---|---|---|

## Beats

Second by second: what arrives, what holds, what leaves; which ones land on the music.

## Not the demo

The style's demo film beside this one: structure, opening, signature shot, ending. At least three must differ.
"""

BUILD = """#!/bin/sh
# Rebuild the film from its source: sh build.sh  (OUT=<folder> to write elsewhere)
set -e
cd "$(dirname "$0")"
moodreel film deliver . ${{OUT:+--out "$OUT"}} {music}
"""


def _style(name: str) -> dict:
    s = library.find(name)
    if not s:
        raise SystemExit(f"no style '{name}' (moodreel styles lists them)")
    return s


def new(name: str, style: str, root: Path = Path("films"), duration: float = 15.0, size: str | None = None,
        fps: int = 30) -> Path:
    s = _style(style)
    d = Path(root) / name
    if d.exists():
        raise SystemExit(f"{d} exists")
    d.mkdir(parents=True)
    sdir = Path(s["path"])
    shutil.copytree(REPO / "kit", d / "kit", ignore=shutil.ignore_patterns("README.md"))
    if (sdir / "kit").exists():                       # a distilled style: its measured tokens and motion
        shutil.copytree(sdir / "kit", d / "kit", dirs_exist_ok=True)
    else:                                             # a library style without a kit yet: the director fills these in
        w, h = (size or "1920x1080").split("x")
        (d / "kit" / "tokens.js").write_text(
            f"// Fill in from STYLE.md §3 (colour) and §4 (type).\nexport const SIZE = [{w}, {h}];\n"
            "export const PALETTE = { ground: '#000000', ink: '#ffffff', accent: null, secondary: [] };\n"
            "export const TYPE = { title: 0.08, body: 0.04, titleWeight: 700, bodyWeight: 400,\n"
            "  display: 'Helvetica Neue, Arial, sans-serif', text: 'Helvetica Neue, Arial, sans-serif' };\n"
            "export const LAYOUT = { margin: 0.08, align: 'left' };\nexport const TEXTURE = {};\n")
        (d / "kit" / "motion.js").write_text(
            "// Fill in from STYLE.md §5 (motion) and §6 (camera and editing).\nimport { tween } from './core.js';\n"
            "export const MOTION = { enter: { ease: 'power3.out', duration: 0.5 }, exit: { ease: 'power2.in', duration: 0.35 } };\n"
            "export const enter = (t, at) => tween(t, at, MOTION.enter.duration, MOTION.enter.ease);\n"
            "export const exit = (t, at) => tween(t, at, MOTION.exit.duration, MOTION.exit.ease);\n")
    st = json.loads((sdir / "style.json").read_text()) if (sdir / "style.json").exists() else {}
    size = size or st.get("size") or "1920x1080"
    (d / "film.json").write_text(json.dumps({"name": name, "style": s["slug"], "style_origin": s["origin"], "size": size,
                                             "fps": fps, "duration": duration, "poster": round(duration * 0.6, 2)}, indent=1))
    (d / "index.html").write_text('<!doctype html><html><head><meta charset="utf-8"><title>' + name +
                                  '</title></head><body><script type="module" src="main.js"></script></body></html>\n')
    (d / "main.js").write_text(MAIN.replace("__DUR__", str(duration)).replace("__NAME__", name))
    (d / "TREATMENT.md").write_text(TREATMENT.format(name=name, style=f"{s.get('name')} ({s['slug']}, {_shown(sdir)})"))
    (d / "CREDITS").write_text(f"{name}\n\nThird-party assets (fonts, images, music, samples) and their licences:\n\n")
    (d / "build.sh").write_text(BUILD.format(music=""))
    return d


def _shown(p: Path) -> str:
    """A path as the treatment shows it: relative to the repo or the home folder, never the user's full path."""
    p = p.resolve()
    for base, prefix in ((REPO, ""), (Path.home(), "~/")):
        if p.is_relative_to(base):
            return prefix + str(p.relative_to(base))
    return p.name


def reading_time(text: str) -> float:
    """Seconds a line needs on screen: CJK characters at 4.5 a second, other characters at 15, plus 1.5 s."""
    cjk = len(CJK.findall(text))
    other = len(re.sub(r"\s", "", CJK.sub("", text)))
    return max(1.5, cjk / 4.5 + other / 15 + 1.5)


def readtime(samples: list[dict], width: int, height: int, step: float) -> list[dict]:
    """Each text, from the frame it is complete and fully inside the picture, must stay unchanged long enough."""
    spans, open_ = [], {}
    for s in samples:
        seen = set()
        for x in s["texts"]:
            inside = x["x0"] >= -1 and x["y0"] >= -1 and x["x1"] <= width + 1 and x["y1"] <= height + 1
            key = (x["id"], x["text"])
            if inside:
                seen.add(key)
                open_.setdefault(key, s["t"])
        for key in [k for k in open_ if k not in seen]:
            spans.append((key, open_.pop(key), s["t"]))
    end = samples[-1]["t"] + step if samples else 0
    spans += [(k, t0, end) for k, t0 in open_.items()]
    out = []
    for (tid, text), t0, t1 in spans:
        need = reading_time(text)
        if t1 - t0 + 1e-6 < need:
            out.append({"id": tid, "text": text, "from": round(t0, 2), "shown": round(t1 - t0, 2), "needs": round(need, 2)})
    return out


def _film(d: Path) -> dict:
    return json.loads((Path(d) / "film.json").read_text())


def black_frames(video: Path, duration: float) -> list[list[float]]:
    r = subprocess.run(["ffmpeg", "-v", "info", "-i", str(video), "-vf", "blackdetect=d=0.04:pix_th=0.06", "-an", "-f", "null", "-"],
                       capture_output=True, text=True)
    spans = [[float(a), float(b)] for a, b in re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", r.stderr)]
    return [s for s in spans if s[0] > 0.2 and s[1] < duration - 0.5]


def check(d: Path) -> dict:
    d = Path(d)
    f = _film(d)
    w, h = (int(x) for x in f["size"].split("x"))
    out = {"film": f["name"]}
    r = subprocess.run(["node", str(RENDER), "texts", str(d), "--size", f["size"], "--step", "0.1"], capture_output=True, text=True)
    if r.returncode:
        out["reading"] = {"error": r.stderr.strip()[-300:]}
    else:
        data = json.loads(r.stdout)
        out["reading"] = {"too_short": readtime(data["samples"], w, h, data["step"])}
    video = d / "out" / "video.mp4"
    if video.exists():
        out["black"] = black_frames(video, f["duration"])
    s = library.find(f["style"])
    sdir = Path(s["path"]) if s else None
    if sdir and (sdir / "evidence" / "measure").exists():
        from ..check.frame import check as frame_check
        times = [round(f["duration"] * k, 2) for k in (0.25, 0.5, 0.75)]
        subprocess.run(["node", str(RENDER), "still", str(d), *map(str, times), "--size", f["size"], "--out", str(d / "out" / "stills")],
                       check=True, capture_output=True)
        out["frames"] = frame_check(sdir, [d / "out" / "stills" / f"t_{t}.jpg" for t in times], out=d / "out")
        if video.exists():
            from ..check.motion import check as motion_check
            out["motion"] = motion_check(sdir, video, out=d / "out")
    ok = not out.get("reading", {}).get("too_short") and not out.get("reading", {}).get("error") and not out.get("black")
    if "frames" in out:
        ok = ok and all(x["pass"] for x in out["frames"]["stills"])
    if "motion" in out:
        ok = ok and out["motion"]["ok"]
    out["ok"] = ok
    (d / "out").mkdir(exist_ok=True)
    (d / "out" / "check.json").write_text(json.dumps(out, indent=1, default=float))
    return out


def _loudnorm(music: Path, dst: Path, duration: float) -> dict:
    target = "I=-14:TP=-1.5:LRA=11"
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(music), "-af", f"loudnorm={target}:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True)
    m = json.loads(r.stderr[r.stderr.rindex("{"):r.stderr.rindex("}") + 1])
    af = (f"loudnorm={target}:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:"
          f"measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true,"
          f"afade=t=out:st={max(0.0, duration - 1.0)}:d=1,apad")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(music), "-af", af, "-t", str(duration), "-ar", "48000", str(dst)], check=True)
    return {"measured_input_lufs": float(m["input_i"])}


def deliver(d: Path, music: Path | None = None, out: Path | None = None, workers: int = 3) -> dict:
    d = Path(d)
    f = _film(d)
    out = Path(out or d)
    out.mkdir(parents=True, exist_ok=True)
    work = d / "out"
    work.mkdir(exist_ok=True)
    video = work / "video.mp4"
    subprocess.run(["node", str(RENDER), "video", str(d), "--fps", str(f["fps"]), "--size", f["size"], "--workers", str(workers),
                    "--out", str(video)], check=True)
    final = out / f"{f['name']}.mp4"
    info = {"video": str(final)}
    if music:
        mix = work / "mix.wav"
        info["music"] = _loudnorm(Path(music), mix, f["duration"])
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(video), "-i", str(mix), "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                        "-shortest", "-movflags", "+faststart", str(final)], check=True)
    else:
        shutil.copyfile(video, final)
    subprocess.run(["node", str(RENDER), "still", str(d), str(f["poster"]), "--size", f["size"], "--out", str(work / "poster")],
                   check=True, capture_output=True)
    shutil.copyfile(work / "poster" / f"t_{f['poster']}.jpg", out / "poster.jpg")
    info["poster"] = str(out / "poster.jpg")
    return info
