"""A blind distillation of the example films, for the STYLE.md sections no measurement can judge (`moodreel bench blind`).

§8 of the design asks that at least 8 of a style's 11 STYLE.md sections, distilled back from a film made in it, be
judged the same style. Five sections are judged from the measurements by the round trip; the other six (essence,
sound, native moves, pitfalls, engine, variation) need a director who has not read the style. Whoever made the
films has, so the distillation goes to someone else:

  moodreel bench blind make     each round-trip project becomes a packet under a neutral code (out/blind/A, B, ...)
                                holding only what a user would hand over and what Moodreel measures: the references,
                                MEASURE.md, measure/, evidence/, the kit, the STYLE.md template and BRIEF.md; every
                                path or file name that could name the film or the style is left out
  (a director who reads only the packet writes <packet>/STYLE.md)
  (a judge reads JUDGE.md and writes out/blind/<code>/verdict.json)
  moodreel bench blind score    the verdicts and the judge's notes, beside the round trip's own five, into
                                bench/roundtrip/BLIND.md; the distilled STYLE.md files, verdicts and that table are
                                kept per round (bench/roundtrip/blind/round<N>/, --round N)
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SECTIONS = ["Essence", "Materials & rendering", "Colour logic", "Type & subtitles", "Motion quality", "Camera grammar",
            "Sound palette", "Native moves", "Pitfalls of the medium", "Engine", "Variation space"]
VERDICTS = ("same", "partly", "different", "absent")

BRIEF = """# Brief: distil this style

You are the director. These references are all a user has given you, measured by Moodreel. Write `STYLE.md` in this
folder: the style they show, in the eleven sections of `TEMPLATE.md`, as rules that hold for every film in it.

Read only this folder (and, for how to read the numbers, `skills/moodreel/SKILL.md` and
`skills/moodreel/references/`). Do not open `styles/`, `examples/`, `bench/`, `docs/`, the READMEs, `out/` outside
this folder, or anything else in the repository: the test is whether the style can be found from its references.

Work as the skill's distil flow says: `MEASURE.md` first, then the evidence (`evidence/refs-sheet.jpg`,
`evidence/type-lines.jpg`, the motion strips under `evidence/motion-*/evidence/`), then the pictures in `refs/` and
the video. Every number you write comes from `measure/` or the kit; what you infer from looking, say so. Name the
style yourself. Sound: the references are silent; say what the picture suggests, marked inferred. Engine: describe
what the kit (`kit/`) would need for this style, not files you haven't seen.
"""

JUDGE = """# Judge: does each distilled section describe the same style?

For each code in `KEY.json`, compare `out/blind/<code>/packet/STYLE.md` (written by a director who saw only the
references) with the library's `styles/<slug>/STYLE.md`, section by section. You may read both, the film's source in
`examples/<film>/` and the references in the packet.

For each of the eleven sections give one verdict:

| Verdict | When |
|---|---|
| same | a film made from the distilled section would read as the original style in what that section governs |
| partly | the core is right, but a rule that matters is missing or wrong |
| different | it describes another style, or contradicts the original |
| absent | the section is missing or empty |

Judge the rules, not the wording, and not what the references could not show (a silent film's sound: judge whether
what is inferred is consistent with the original, and say "absent" only if nothing is written). Write
`out/blind/<code>/verdict.json`:

```json
{"sections": {"1": "same", "2": "partly", "...": "...", "11": "same"},
 "notes": {"2": "one line on what is missing"}}
```

§8 passes a style when at least 8 of its 11 sections are "same".
"""


def _strip_paths(o):
    """Paths in the measurements would name the film."""
    if isinstance(o, dict):
        return {k: _strip_paths(v) for k, v in o.items() if k not in ("path", "source_path")}
    if isinstance(o, list):
        return [_strip_paths(v) for v in o]
    return o


def make(rt_root: Path, out_root: Path, only: set[str] | None = None) -> dict:
    """One packet per round-trip project, under a neutral code; KEY.json maps the codes to films (for the judge)."""
    films = sorted(d.name for d in Path(rt_root).iterdir() if (d / "project" / "MEASURE.md").exists()
                   and (not only or d.name in only))
    if out_root.exists():
        shutil.rmtree(out_root)
    key = {}
    for i, film in enumerate(films):
        code, src = chr(ord("A") + i), Path(rt_root) / film / "project"
        dst = out_root / code / "packet"
        dst.mkdir(parents=True)
        shutil.copytree(src / "refs", dst / "refs")
        shutil.copytree(src / "kit", dst / "kit")
        shutil.copytree(src / "evidence", dst / "evidence")
        shutil.copytree(src / "measure", dst / "measure")
        for f in list((dst / "measure").glob("*.json")) + list((dst / "evidence").rglob("*.json")):
            f.write_text(json.dumps(_strip_paths(json.loads(f.read_text())), indent=1, ensure_ascii=False))
        shutil.copyfile(src / "MEASURE.md", dst / "MEASURE.md")
        shutil.copyfile(REPO / "styles" / "_template" / "STYLE.md", dst / "TEMPLATE.md")
        (dst / "BRIEF.md").write_text(BRIEF)
        truth = json.loads((REPO / "examples" / film / "film.json").read_text())
        key[code] = {"film": film, "style": truth["style"]}
    (out_root / "KEY.json").write_text(json.dumps(key, indent=1))
    (out_root / "JUDGE.md").write_text(JUDGE)
    return key


def keep(out_root: Path, dest: Path) -> None:
    """The distilled STYLE.md files, the verdicts and the key, kept in the repository (the packets are not: they
    hold the references and the measurements, which the round trip rebuilds)."""
    if dest.exists():
        shutil.rmtree(dest)
    for code in json.loads((out_root / "KEY.json").read_text()):
        (dest / code).mkdir(parents=True)
        for src, name in ((out_root / code / "packet" / "STYLE.md", "STYLE.md"), (out_root / code / "verdict.json", "verdict.json")):
            if src.exists():
                shutil.copyfile(src, dest / code / name)
    shutil.copyfile(out_root / "KEY.json", dest / "KEY.json")


def score(out_root: Path, roundtrip_report: Path | None = None) -> str:
    """The judges' verdicts as a table, beside the round trip's own verdicts on the five measurable sections."""
    key = json.loads((out_root / "KEY.json").read_text())
    auto = {}
    if roundtrip_report and roundtrip_report.exists():          # "## film" then "Sections ...: §2. Materials ✓, ..."
        film = None
        for line in roundtrip_report.read_text().splitlines():
            if line.startswith("## "):
                film = line[3:].strip()
            elif line.startswith("Sections the measurements speak for") and film:
                auto[film] = {part.split(".")[0].strip(" §"): part.strip().endswith("✓")
                              for part in line.split(":", 1)[1].rstrip(".").split(",")}
    rows, done, notes = [], 0, []
    for code, k in key.items():
        v = out_root / code / "verdict.json"
        a = auto.get(k["film"], {})
        marks = []
        if v.exists():
            verdict = json.loads(v.read_text())["sections"]
            assert all(verdict.get(str(i)) in VERDICTS for i in range(1, 12)), f"{v}: a verdict for each of 11 sections"
            same = sum(verdict[str(i)] == "same" for i in range(1, 12))
            marks = [{"same": "✓", "partly": "~", "different": "✗", "absent": "—"}[verdict[str(i)]] for i in range(1, 12)]
            rows.append(f"| {code} | {k['film']} ({k['style']}) | " + " | ".join(marks) + f" | {same}/11 | "
                        f"{'pass' if same >= 8 else 'fail'} |")
            done += 1
            judged = json.loads(v.read_text()).get("notes") or {}
            if judged:
                notes += [f"### {code} · {k['film']} ({k['style']})", ""]
                notes += [f"- §{n} {SECTIONS[int(n) - 1]} ({verdict[n]}): {judged[n]}" for n in sorted(judged, key=int)] + [""]
        else:
            rows.append(f"| {code} | {k['film']} ({k['style']}) | " + " | ".join(
                ("✓" if a[str(i)] else "✗") + "*" if str(i) in a else "·" for i in range(1, 12)) + " | not judged yet | |")
    head = ["# Blind distillation", "",
            "Each example film's round-trip project, as a packet holding only its references and Moodreel's measurements, "
            "distilled into a STYLE.md by a director who has not read the style, then judged section by section against "
            "the library's STYLE.md (`moodreel bench blind`, see `moodreel/bench/blind.py`). §8 passes a style at 8 of 11 "
            "sections \"same\".", "",
            f"Judged: {done} of {len(key)}. ✓ same, ~ partly, ✗ different, — absent; * the round trip's own verdict on a "
            "section the measurements speak for, · not judged yet.", "",
            "| code | film (style) | " + " | ".join(f"§{i}" for i in range(1, 12)) + " | same | §8 |",
            "|---|---|" + "---|" * 11 + "---|---|"]
    return "\n".join(head + rows + ([""] + ["## The judge's notes", ""] + notes if notes else [])) + "\n"
