"""`moodreel pack <project> --slug <slug> --name <name>`: check a distilled style and put it in the user's library.

The project must hold what the director wrote (STYLE.md with its 11 sections, DECISIONS.md, LEDGER.md), the kit,
an approved style frame and a demo film. Checks before anything is written:
  - STYLE.md has sections 1-11;
  - every number with a unit and every colour in STYLE.md can be found in LEDGER.md or in the kit (a rule that
    cites a number nobody measured or decided is how a style drifts); --strict makes this an error;
  - the slug and names are free in both libraries;
  - with --build, demo/build.sh rebuilds the film in a scratch folder.
References stay out of the pack: only their hashes and, when all of them are the user's own work, the contact sheet.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from .. import __version__, library

NUMBER = re.compile(r"(?<![\w#.])(-?\d+(?:\.\d+)?)\s*(%|ms|s|px|°|fps|levels?|LUFS)\b|#[0-9a-fA-F]{6}\b")


def sections(md: str) -> list[int]:
    return sorted({int(m) for m in re.findall(r"^##\s+(\d+)\.", md, re.M)})


def untraced(style_md: str, ledger: str, kit_text: str) -> list[str]:
    """Numbers with units, and colours, in STYLE.md that neither the ledger nor the kit mentions."""
    haystack = (ledger + "\n" + kit_text).lower()
    numbers = {float(x) for x in re.findall(r"-?\d+(?:\.\d+)?", haystack)}
    out = []
    for line in style_md.splitlines():
        if line.startswith("#"):
            continue
        for m in NUMBER.finditer(line):
            tok = m.group(0)
            if tok.startswith("#"):
                if tok.lower() not in haystack:
                    out.append(tok)
                continue
            v, unit = float(m.group(1)), m.group(2)
            cands = {v, v / 100} if unit == "%" else {v, v / 1000} if unit == "ms" else {v}
            if not any(abs(c - n) <= max(0.01 * abs(c), 1e-6) for c in cands for n in numbers):
                out.append(tok)
    return sorted(set(out))


GPU = re.compile(r"""from\s+['"](?:\./|\.\./)(?:kit/)?(?:gl|three)\.js['"]""")


def traits(project: Path) -> tuple[int, list[str]]:
    """What the demo says about films made in the style: its frame rate (demo/film.json), and what a new film must be
    set up with: `3d` when the style's kit or the demo draws with kit/three.js or kit/gl.js (built on it), so three.js is
    vendored; `music-led` when the demo is cut to its own score, so a new film starts with one."""
    project = Path(project)
    film_json = project / "demo" / "film.json"
    fps = int(json.loads(film_json.read_text()).get("fps", 30)) if film_json.exists() else 30
    code = "".join(p.read_text(errors="ignore") for p in [*(project / "kit").glob("*.js"), *(project / "demo").glob("*.js")]
                   if p.name not in ("gl.js", "three.js"))
    needs = (["3d"] if GPU.search(code) else []) + (["music-led"] if (project / "demo" / "score.json").exists() else [])
    return fps, needs


def check(project: Path, slug: str, name: str, name_zh: str | None = None, strict: bool = False,
          build: bool = False) -> dict:
    project = Path(project)
    problems, warnings = [], []
    need = ["STYLE.md", "DECISIONS.md", "LEDGER.md", "kit/tokens.js", "kit/motion.js", "styleframe.jpg"]
    for f in need:
        if not (project / f).exists():
            problems.append(f"missing {f}")
    if not (project / "demo" / "index.html").exists() or not (project / "demo.mp4").exists():
        problems.append("missing the demo film: demo/ (with index.html and build.sh) and demo.mp4")
    if (project / "STYLE.md").exists():
        md = (project / "STYLE.md").read_text()
        got = sections(md)
        if got != list(range(1, 12)):
            problems.append(f"STYLE.md sections are {got}, expected 1-11")
        kit_text = "".join((project / "kit" / f).read_text() for f in ("tokens.js", "motion.js") if (project / "kit" / f).exists())
        ledger = (project / "LEDGER.md").read_text() if (project / "LEDGER.md").exists() else ""
        loose = untraced(md, ledger, kit_text)
        if loose:
            (problems if strict else warnings).append(f"STYLE.md cites values the ledger and the kit don't: {', '.join(loose)}")
    for s in library.all_styles():
        if s["slug"] == slug or name.lower() in {str(s.get("name", "")).lower(), str(s.get("name_zh", "")).lower()}:
            if s["origin"] == "builtin" or s["slug"] != slug:
                problems.append(f"'{slug}' / '{name}' is taken by {s['origin']} style {s['slug']}")
            else:
                warnings.append(f"replaces your style {slug}")
    if build and (project / "demo" / "build.sh").exists():
        with tempfile.TemporaryDirectory() as tmp:
            r = subprocess.run(["sh", str(project / "demo" / "build.sh")], env={**os.environ, "OUT": tmp},
                               capture_output=True, text=True)
            if r.returncode:
                problems.append(f"demo/build.sh failed: {r.stderr.strip()[-400:]}")
    return {"ok": not problems, "problems": problems, "warnings": warnings}


def pack(project: Path, slug: str, name: str, name_zh: str | None = None, strict: bool = False,
         build: bool = False) -> dict:
    project = Path(project)
    res = check(project, slug, name, name_zh, strict, build)
    if not res["ok"]:
        return res
    intake = json.loads((project / "intake.json").read_text())
    dst = library.user_dir() / slug
    if dst.exists():
        shutil.rmtree(dst)
    (dst / "evidence").mkdir(parents=True)
    for f in ("STYLE.md", "DECISIONS.md", "styleframe.jpg", "demo.mp4"):
        shutil.copyfile(project / f, dst / f)
    if (project / "poster.jpg").exists():
        shutil.copyfile(project / "poster.jpg", dst / "poster.jpg")
    shutil.copytree(project / "kit", dst / "kit")
    shutil.copytree(project / "demo", dst / "demo",                 # the source, not its renders (demo.mp4 is the film)
                    ignore=shutil.ignore_patterns("out", "stills", "node_modules", "vendor", "*.mp4", "*.wav"))
    shutil.copyfile(project / "LEDGER.md", dst / "evidence" / "LEDGER.md")
    shutil.copytree(project / "measure", dst / "evidence" / "measure")
    own = all(r.get("source") == "own" for r in intake["refs"])
    if own and (project / "evidence" / "refs-sheet.jpg").exists():
        shutil.copyfile(project / "evidence" / "refs-sheet.jpg", dst / "evidence" / "refs-sheet.jpg")
    refs = [{k: r[k] for k in ("id", "kind", "sha256", "source", "w", "h") if k in r} for r in intake["refs"]]
    (dst / "evidence" / "intake.json").write_text(json.dumps({**intake, "refs": refs}, indent=1, ensure_ascii=False))
    w, h = (int(x) for x in intake["default_size"].split("x"))
    fps, needs = traits(project)
    meta = {"slug": slug, "name": name, "name_zh": name_zh or name, "version": 1, "size": intake["default_size"],
            "fps": fps, "created": dt.date.today().isoformat(), "moodreel_version": __version__,
            "phase": "mvp", "needs": needs, "refs": refs, "source": {"project": "moodreel", "distilled_from": len(refs)}}
    (dst / "style.json").write_text(json.dumps(meta, indent=1, ensure_ascii=False) + "\n")
    library.register({k: meta[k] for k in ("slug", "name", "name_zh", "phase", "needs", "source")} | {"size": [w, h]})
    return {**res, "path": str(dst)}
