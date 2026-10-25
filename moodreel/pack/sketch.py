"""`moodreel sketch <project>`: the measured motion grammar replayed with neutral shapes, as a film.

Writes <project>/sketch/ (index.html, main.js and the project's kit): as many shots as the references have (at
most four) at their median length (longer when the moves need it), each with three elements that enter, one after
another with the measured hold between (or the measured stagger; overlapping when they can't follow one another
inside the shot), the commonest way the references' elements do
(rise, slide, scale, grow, clip, wipe or fade), with the kit's ease and duration, and leave the same way with its
exit ease when the references have exits; shots change by cuts, dissolves or dips as the references' do, and the
drawings are held on twos when theirs are. Measured with motion-check against the references, it tells whether
the kit carries the style's motion; it is no film of the style, only its timing drawn plainly.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from .kit import write_kit

PAGE = """<!doctype html><html><head><meta charset="utf-8"><title>motion sketch</title></head>
<body><script type="module" src="main.js"></script></body></html>
"""

MAIN = r"""import { stage } from './kit/stage.js';
import { step, lerp, clamp } from './kit/core.js';
import { SIZE, PALETTE, TYPE } from './kit/tokens.js';
import { MOTION, enter, exit } from './kit/motion.js';

const [W, H] = SIZE;
const SHOTS = __SHOTS__, KIND = '__KIND__', EXITS = __EXITS__, CHANGE = '__CHANGE__', FPS = __FPS__;
const inDur = MOTION?.enter?.duration ?? 0.5, outDur = MOTION?.exit?.duration ?? 0.4, n = EXITS ? 6 : 3;
// several shots keep the references' shot length: the holds give way first
const hold = SHOTS > 1 ? Math.max(0.2, Math.min(MOTION?.hold ?? 0.8, (__LEN__ - 0.3 - 3 * inDur - (EXITS ? 3 * outDur : 0)) / n))
  : MOTION?.hold ?? 0.8;
// one element after another with the references' hold between, or their stagger when they stagger; entrances too
// slow to follow one another inside the references' shot overlap instead
let nextIn = MOTION?.stagger?.interval ?? inDur + hold, nextOut = MOTION?.stagger?.interval ?? outDur + hold;
const fixed = 0.3 + inDur + hold + (EXITS ? outDur + hold : 0), spread = 2 * nextIn + (EXITS ? 2 * nextOut : 0);
if (SHOTS > 1 && !MOTION?.stagger && fixed + spread > __LEN__) {
  const k = Math.max(0, __LEN__ - fixed) / spread;
  nextIn *= k;
  nextOut *= k;
}
const IN = [0, 1, 2].map(i => 0.3 + i * nextIn), OUT = [0, 1, 2].map(i => IN[2] + inDur + hold + i * nextOut);
const NEED = (EXITS ? OUT[2] + outDur : IN[2] + inDur) + hold;
const LEN = SHOTS > 1 ? Math.max(__LEN__, NEED) : NEED;          // one shot: no idle tail to thin the motion out
const gap = 0, travel = (MOTION?.enter?.travel ?? 0.06) * H;
const from = MOTION?.enter?.scale_from ?? 0.6, on = MOTION?.on ?? 1;
const ink = PALETTE.ink ?? '#ffffff', accent = PALETTE.accent ?? ink;
const titlePx = Math.round((TYPE.title ?? 0.08) * H), font = `${TYPE.titleWeight ?? 700} ${titlePx}px ${TYPE.display}`;
const ITEMS = [{ x: 0.10, y: 0.18, w: 0.5, h: (TYPE.title ?? 0.08) * 0.75, text: 'Motion' },
  { x: 0.10, y: 0.62, w: 0.2, h: 0.16, fill: accent }, { x: 0.62, y: 0.62, w: 0.2, h: 0.16, fill: ink }];

function item(g, it, p) {
  if (p <= 0) return;
  const x = it.x * W, y = it.y * H, w = it.w * W, h = it.h * H;
  g.save();
  let dx = 0, dy = 0, sx = 1, sy = 1, a = 1, cx = x + w / 2, cy = y + h / 2;
  if (KIND === 'rise') dy = (1 - p) * travel;
  else if (KIND === 'slide') dx = (1 - p) * travel * 2;
  else if (KIND === 'scale') sx = sy = lerp(from, 1, p);
  else if (KIND === 'grow') { sy = p; cy = y + h; }
  else if (KIND === 'fade') a = p;
  if (KIND === 'clip' || KIND === 'wipe') {
    g.beginPath();
    if (KIND === 'clip') g.rect(x - 20, y - 20, w + 40, h + 20);
    else g.rect(x - 20, y - 20, (w + 40) * p, h + 40);
    g.clip();
    if (KIND === 'clip') dy = (1 - p) * (h + 20);
  }
  g.globalAlpha = a;
  g.translate(cx + dx, cy + dy);
  g.scale(sx, sy);
  g.translate(-cx, -cy);
  if (it.text) {
    g.font = font;
    g.fillStyle = ink;
    g.fillText(it.text, x, y + h);
  } else {
    g.fillStyle = it.fill;
    g.fillRect(x, y, w, h);
  }
  g.restore();
}

function shot(g, t, s) {
  g.fillStyle = PALETTE.ground;
  g.fillRect(0, 0, W, H);
  if (s % 2) {                                             // every other shot a tone off the ground, so a cut shows
    g.globalAlpha = 0.25;
    g.fillStyle = ink;
    g.fillRect(0, 0, W, H);
    g.globalAlpha = 1;
  }
  ITEMS.forEach((it, i) => {
    const p = enter(t, IN[i]), q = EXITS ? exit(t, OUT[i]) : 0;
    item(g, it, t < IN[i] ? 0 : clamp(p * (1 - q)));
  });
}

stage({
  width: W, height: H, duration: SHOTS * LEN, background: PALETTE.ground, fonts: [font],
  draw: (g, time) => {
    const t = on > 1 ? step(time, FPS / on) : time;
    const s = Math.min(SHOTS - 1, Math.floor(time / LEN)), local = t - s * LEN;
    shot(g, local, s);
    if (CHANGE === 'dissolve' && s > 0 && local < 0.4) {     // the shot before, dissolving out
      g.save();
      g.globalAlpha = 1 - local / 0.4;
      shot(g, local + LEN, s - 1);
      g.restore();
    }
    const edge = Math.round(time / LEN) * LEN, dip = MOTION?.transitions?.dip ?? 0.5;
    if (CHANGE === 'dip' && edge > 0 && edge < SHOTS * LEN && Math.abs(time - edge) < dip / 2) {  // through a colour
      g.save();
      g.globalAlpha = 1 - Math.abs(time - edge) / (dip / 2);
      g.fillStyle = MOTION?.transitions?.dip_colours?.[0] ?? '#000000';
      g.fillRect(0, 0, W, H);
      g.restore();
    }
  },
});
"""

KINDS = (("clip", "clip"), ("wipe", "wipe"), ("grow", "grow"), ("scale", "scale"), ("slide", "slide"), ("rise", "rise"),
         ("drop", "rise"), ("fade", "fade"))


def _kind(vocabulary: dict | None) -> str:
    """The commonest way the references' elements enter, in the sketch's few words."""
    votes = {}
    for label, n in (vocabulary or {}).items():
        kind = next((k for word, k in KINDS if word in label), None)
        if kind:
            votes[kind] = votes.get(kind, 0) + n
    return max(votes, key=votes.get) if votes else "rise"


def write_sketch(project: Path, fps: int = 24) -> Path:
    project = Path(project)
    if not (project / "kit" / "tokens.js").exists():       # never overwrite the director's kit
        write_kit(project)
    grammar = json.loads((project / "measure" / "motion.json").read_text())["grammar"]
    if "videos" in grammar:
        vid = grammar["videos"][0]
        grammar = {"entrance": grammar["entrance"][vid], "exit": grammar["exit"][vid], "shots": grammar["shots"][vid]}
    sh = grammar.get("shots") or {}
    length = min(6.0, max(2.5, (sh.get("length_s") or {}).get("median") or 4.0))
    out = project / "sketch"
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(project / "kit", out / "kit")
    (out / "index.html").write_text(PAGE)
    main = (MAIN.replace("__SHOTS__", str(min(4, max(1, sh.get("count") or 1)))).replace("__LEN__", f"{length:.3f}")
            .replace("__KIND__", _kind((grammar.get("entrance") or {}).get("vocabulary")))
            .replace("__EXITS__", "true" if grammar.get("exit") else "false")
            .replace("__CHANGE__", "dissolve" if sh.get("dissolves") and not sh.get("cuts")
                     else "dip" if sh.get("dips") and not sh.get("cuts") else "cut")
            .replace("__FPS__", str(fps)))
    (out / "main.js").write_text(main)
    return out
