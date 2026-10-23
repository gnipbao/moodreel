"""`moodreel scaffold <project>`: a first style frame, drawn only from the measured tokens.

Writes <project>/look/ (index.html, main.js and a copy of the kit), a three-second title card: the ground and its
surface, a headline in the ink at the measured title size, a line of body text, an accent shape and the
secondary colours, entering with the measured motion. It is a starting point for the director, not a design:
render a still, run frame-check, then rewrite main.js into the style's own picture.
"""
from __future__ import annotations

import shutil
from pathlib import Path

PAGE = """<!doctype html><html><head><meta charset="utf-8"><title>style frame</title></head>
<body><script type="module" src="main.js"></script></body></html>
"""

MAIN = r"""import { stage } from './kit/stage.js';
import { clamp, lerp } from './kit/core.js';
import { paper, grain, vignette, screen, scanlines } from './kit/texture.js';
import { SIZE, PALETTE, TYPE, LAYOUT, TEXTURE } from './kit/tokens.js';
import { MOTION, enter } from './kit/motion.js';

const [W, H] = SIZE;
const margin = (LAYOUT.margin ?? 0.08) * Math.min(W, H) + 0.04 * W;
const align = LAYOUT.align === 'centre' ? 'center' : 'left';
const x0 = align === 'center' ? W / 2 : margin;
const title = (TYPE.title ?? 0.08) * H, body = (TYPE.body ?? 0.04) * H;
const pop = MOTION?.enter?.scale_from ?? 0.85;

stage({
  width: W, height: H, duration: 3, background: PALETTE.ground,
  fonts: [`${TYPE.titleWeight} ${Math.round(title)}px ${TYPE.display}`, `${TYPE.bodyWeight} ${Math.round(body)}px ${TYPE.text}`],
  draw: (g, t) => {
    g.drawImage(TEXTURE.mottle > 0.8 ? paper(W, H, { color: PALETTE.ground, mottle: TEXTURE.mottle }) : flat(W, H), 0, 0, W, H);
    // accent block, behind the type
    const a = enter(t, 0.2, 2);
    const s = lerp(pop, 1, a);
    g.save();
    g.globalAlpha = clamp(a * 3);
    g.translate(W * 0.72, H * 0.55);
    g.scale(s, s);
    g.fillStyle = TEXTURE.halftone ? screen(g, { period: TEXTURE.halftone.period_px, angle: TEXTURE.halftone.angle,
      color: PALETTE.accent ?? PALETTE.ink }) : (PALETTE.accent ?? PALETTE.ink);
    g.beginPath();
    g.arc(0, 0, H * 0.16, 0, Math.PI * 2);
    g.fill();
    g.restore();
    (PALETTE.secondary ?? []).slice(0, 3).forEach((c, i) => {
      const p = enter(t, 0.35, 3 + i);
      g.fillStyle = c;
      g.globalAlpha = p;
      g.fillRect(x0 + i * H * 0.09, H * 0.78 + (1 - p) * H * 0.02, H * 0.07, H * 0.07);
      g.globalAlpha = 1;
    });
    // headline and body, in the ink
    g.textAlign = align;
    g.textBaseline = 'alphabetic';
    const rise = (MOTION?.enter?.travel ?? 0.03) * H;
    [[`${TYPE.titleWeight} ${title}px ${TYPE.display}`, 'Style frame', H * 0.42, 0],
     [`${TYPE.bodyWeight} ${body}px ${TYPE.text}`, 'A first draft from the measured tokens', H * 0.42 + title * 0.9, 1]]
      .forEach(([font, text, y, i]) => {
        const p = enter(t, 0.3, i);
        g.font = font;
        g.fillStyle = PALETTE.ink;
        g.globalAlpha = clamp(p * 1.5) * (i ? 0.75 : 1);
        g.fillText(text, x0, y + (1 - p) * rise);
        g.globalAlpha = 1;
      });
    vignette(g, W, H, TEXTURE.vignette ?? 0);
    if (TEXTURE.scanlines) scanlines(g, Math.round(TEXTURE.scanlines.period_px), 0.25);
    grain(g, TEXTURE.grain >= 2.5 ? TEXTURE.grain : 0, Math.round(t * 24), { ground: PALETTE.ground });   // fine grain is codec noise
  },
});

let ground;
function flat(w, h) {
  if (!ground) {
    ground = document.createElement('canvas');
    ground.width = w;
    ground.height = h;
    const q = ground.getContext('2d');
    q.fillStyle = PALETTE.ground;
    q.fillRect(0, 0, w, h);
  }
  return ground;
}
"""


def scaffold(project: Path) -> Path:
    project = Path(project)
    look = project / "look"
    look.mkdir(parents=True, exist_ok=True)
    if not (project / "kit" / "tokens.js").exists():
        from .kit import write_kit
        write_kit(project)
    shutil.copytree(project / "kit", look / "kit", dirs_exist_ok=True)
    (look / "index.html").write_text(PAGE)
    if not (look / "main.js").exists():               # never overwrite the director's frame
        (look / "main.js").write_text(MAIN)
    return look
