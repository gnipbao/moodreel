"""Write a render-contract page (window.render(t)) with known motion, plus its ground truth.

  python fixtures/make_fixture.py fixtures/mg-basic

The spec below is the single source of truth: the page draws it, and truth.json is computed from it with the
same ease formulas (motionx/eases.py). Render the page from the repository root:

  node render/render.mjs video <fixture dir> --fps 30 --size 1280x720 --out <fixture dir>/clean.mp4
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from motionx import eases  # noqa: E402

W, H, FPS, DUR = 1280, 720, 30, 7.0
CARD_COLORS = ["#ff5f5f", "#ffc94d", "#4dd4ff", "#9b7bff"]


def card(i):
    t = 0.95 + i * 0.12
    anims = [{"prop": "scale", "from": 0.6, "to": 1, "t": t, "d": 0.45, "ease": "back.out(1.7)"},
             {"prop": "opacity", "from": 0, "to": 1, "t": t, "d": 0.25, "ease": "power1.out"}]
    if i == 0:
        anims.append({"prop": "y", "from": 430, "to": 580, "t": 2.10, "d": 0.50, "ease": "sine.inOut"})
    return {"id": f"card{i}", "kind": "rect", "w": 200, "h": 140, "r": 18, "color": CARD_COLORS[i],
            "x": 640 + (i - 1.5) * 240, "y": 430, "anims": anims}


SPEC = {
    "W": W, "H": H, "fps": FPS, "dur": DUR,
    "shots": [
        {"id": "A", "t0": 0.0, "t1": 3.0, "bg": {"kind": "vignette", "c0": "#262d52", "c1": "#12162a"},
         "elements": [
             {"id": "title", "kind": "text", "text": "MOTION GRAMMAR", "font": "bold 64px Helvetica, Arial, sans-serif",
              "color": "#f2efe6", "x": 640, "y": 170,
              "anims": [{"prop": "y", "from": 230, "to": 170, "t": 0.30, "d": 0.60, "ease": "power3.out"},
                        {"prop": "opacity", "from": 0, "to": 1, "t": 0.30, "d": 0.60, "ease": "power3.out"}]},
             *[card(i) for i in range(4)],
         ]},
        {"id": "B", "t0": 3.0, "t1": 5.5, "bg": {"kind": "paper", "c": "#efe6d2"},
         "elements": [
             {"id": "big42", "kind": "text", "text": "42", "font": "bold 220px Helvetica, Arial, sans-serif",
              "color": "#1b1b1b", "x": 640, "y": 330,
              "anims": [{"prop": "scale", "from": 0.05, "to": 1, "t": 3.30, "d": 0.50, "ease": "expo.out"},
                        {"prop": "opacity", "from": 1, "to": 0, "t": 4.40, "d": 0.30, "ease": "power2.in"}]},
             {"id": "bar", "kind": "rect", "w": 640, "h": 70, "r": 0, "color": "#d6452f", "x": 640, "y": 540,
              "text": "THE ANSWER", "font": "bold 40px Helvetica, Arial, sans-serif", "textColor": "#ffffff",
              "anims": [{"prop": "x", "from": -400, "to": 640, "t": 3.60, "d": 0.40, "ease": "power2.out"},
                        {"prop": "opacity", "from": 1, "to": 0, "t": 4.40, "d": 0.30, "ease": "power2.in"}]},
         ]},
        {"id": "C", "t0": 5.0, "t1": 7.0, "bg": {"kind": "flat", "c": "#f7c6d0"},
         "elements": [
             {"id": "ball", "kind": "circle", "r": 70, "color": "#2b2d6e", "x": 640, "y": 360,
              "anims": [{"prop": "y", "from": -120, "to": 360, "t": 5.80, "d": 0.90, "ease": "elastic.out(1,0.3)"}]},
             {"id": "label", "kind": "text", "text": "BOUNCE", "font": "bold 48px Helvetica, Arial, sans-serif",
              "color": "#2b2d6e", "x": 640, "y": 560,
              "anims": [{"prop": "y", "from": 600, "to": 560, "t": 6.30, "d": 0.40, "ease": "power2.out"},
                        {"prop": "opacity", "from": 0, "to": 1, "t": 6.30, "d": 0.40, "ease": "power2.out"}]},
         ]},
    ],
    "transitions": [{"type": "cut", "t": 3.0},
                    {"type": "dissolve", "t0": 5.0, "t1": 5.5, "ease": "sine.inOut"}],
}

PAGE = r"""<!doctype html><html><head><meta charset="utf-8">
<style>html,body{margin:0;background:#000;overflow:hidden}canvas{display:block}</style></head>
<body><canvas id="c"></canvas><script>
const SPEC = __SPEC__;
const W = innerWidth, H = innerHeight, c = document.getElementById('c');
c.width = W; c.height = H; const g = c.getContext('2d');
const sx = W / SPEC.W;                               // draw in spec units at any --size
// GSAP-named eases: keep in step with motionx/eases.py
const pw = p => [u => u ** p, u => 1 - (1 - u) ** p, u => u < .5 ? 2 ** (p - 1) * u ** p : 1 - (-2 * u + 2) ** p / 2];
const BASE = { none: u => u };
[['power1', 2], ['power2', 3], ['power3', 4], ['power4', 5]].forEach(([k, p]) => {
  const [i, o, io] = pw(p); BASE[k + '.in'] = i; BASE[k + '.out'] = o; BASE[k + '.inOut'] = io; });
Object.assign(BASE, {
  'sine.in': u => 1 - Math.cos(u * Math.PI / 2), 'sine.out': u => Math.sin(u * Math.PI / 2),
  'sine.inOut': u => -(Math.cos(Math.PI * u) - 1) / 2,
  'expo.out': u => u >= 1 ? 1 : 1 - 2 ** (-10 * u), 'expo.in': u => u <= 0 ? 0 : 2 ** (10 * u - 10),
});
function ease(name) {
  const m = name.match(/^([a-zA-Z0-9.]+)(?:\(([^)]*)\))?$/), base = m[1], a = m[2] ? m[2].split(',').map(Number) : [];
  if (BASE[base]) return BASE[base];
  if (base === 'back.out') { const s = a[0] ?? 1.7; return u => 1 + (s + 1) * (u - 1) ** 3 + s * (u - 1) ** 2; }
  if (base === 'elastic.out') {
    const amp = Math.max(a[0] ?? 1, 1), per = a[1] ?? 0.3, p3 = per / (2 * Math.PI) * Math.asin(1 / amp);
    return u => u >= 1 ? 1 : amp * 2 ** (-10 * u) * Math.sin((u - p3) * 2 * Math.PI / per) + 1; }
  throw new Error('ease ' + name);
}
function val(el, prop, t) {
  const base = prop === 'scale' || prop === 'opacity' ? 1 : el[prop];
  const as = el.anims.filter(a => a.prop === prop).sort((p, q) => p.t - q.t);
  let v = base;
  as.forEach((a, k) => {
    if (t >= a.t) v = a.from + (a.to - a.from) * ease(a.ease)(Math.min(1, (t - a.t) / a.d));
    else if (k === 0) v = a.from;
  });
  return v;
}
function mulberry(a) { return () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a);
  t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
const bgs = {};
function bgCanvas(shot) {
  if (bgs[shot.id]) return bgs[shot.id];
  const o = document.createElement('canvas'); o.width = W; o.height = H; const q = o.getContext('2d'), b = shot.bg;
  if (b.kind === 'vignette') {
    const gr = q.createRadialGradient(W / 2, H / 2, 0, W / 2, H / 2, Math.hypot(W, H) / 2);
    gr.addColorStop(0, b.c0); gr.addColorStop(1, b.c1); q.fillStyle = gr; q.fillRect(0, 0, W, H);
  } else {
    q.fillStyle = b.c; q.fillRect(0, 0, W, H);
    if (b.kind === 'paper') {                        // static fibre noise, seeded
      const img = q.getImageData(0, 0, W, H), d = img.data, r = mulberry(7);
      for (let i = 0; i < d.length; i += 4) { const n = (r() - 0.5) * 14; d[i] += n; d[i + 1] += n; d[i + 2] += n * 0.8; }
      q.putImageData(img, 0, 0);
      q.globalAlpha = 0.05; q.strokeStyle = '#7a6a4a';
      for (let k = 0; k < 400; k++) { const x = r() * W, y = r() * H, a = r() * Math.PI;
        q.beginPath(); q.moveTo(x, y); q.lineTo(x + Math.cos(a) * 30, y + Math.sin(a) * 30); q.stroke(); }
      q.globalAlpha = 1;
    }
  }
  return (bgs[shot.id] = o);
}
function drawEl(el, t, shotAlpha) {
  const x = val(el, 'x', t) * sx, y = val(el, 'y', t) * sx, s = val(el, 'scale', t), op = val(el, 'opacity', t);
  if (op <= 0 || s <= 0) return;
  g.save(); g.globalAlpha = op * shotAlpha; g.translate(x, y); g.scale(s * sx, s * sx); g.fillStyle = el.color;
  if (el.kind === 'rect') {
    g.beginPath(); g.roundRect(-el.w / 2, -el.h / 2, el.w, el.h, el.r); g.fill();
    if (el.text) { g.fillStyle = el.textColor; g.font = el.font; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText(el.text, 0, 2); }
  } else if (el.kind === 'circle') { g.beginPath(); g.arc(0, 0, el.r, 0, Math.PI * 2); g.fill(); }
  else { g.font = el.font; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText(el.text, 0, 0); }
  g.restore();
}
function shotAlpha(shot, t) {
  for (const tr of SPEC.transitions) if (tr.type === 'dissolve' && Math.abs(shot.t0 - tr.t0) < 1e-6 && t < tr.t1)
    return ease(tr.ease)(Math.max(0, (t - tr.t0) / (tr.t1 - tr.t0)));
  return 1;
}
window.DUR = SPEC.dur;
window.render = t => {
  g.globalAlpha = 1; g.fillStyle = '#000'; g.fillRect(0, 0, W, H);
  for (const shot of SPEC.shots) {
    if (t < shot.t0 || t >= shot.t1) continue;
    const a = shotAlpha(shot, t); if (a <= 0) continue;
    g.globalAlpha = a; g.drawImage(bgCanvas(shot), 0, 0); g.globalAlpha = 1;
    for (const el of shot.elements) drawEl(el, t, a);
  }
};
document.fonts.ready.then(() => { SPEC.shots.forEach(bgCanvas); window.render(0); window.READY = true; });
</script></body></html>
"""


def value(el, prop, t):
    base = 1.0 if prop in ("scale", "opacity") else float(el[prop])
    v = base
    anims = sorted((a for a in el["anims"] if a["prop"] == prop), key=lambda a: a["t"])
    for k, a in enumerate(anims):
        if t >= a["t"]:
            u = min(1.0, (t - a["t"]) / a["d"])
            v = a["from"] + (a["to"] - a["from"]) * float(eases.get(a["ease"])(np.array(u)))
        elif k == 0:
            v = a["from"]
    return v


def truth(spec):
    events = []
    for shot in spec["shots"]:
        for el in shot["elements"]:
            for a in el["anims"]:
                end_xy = (value(el, "x", a["t"] + a["d"]), value(el, "y", a["t"] + a["d"]))
                events.append({"element": el["id"], "shot": shot["id"], "prop": a["prop"], "t0": a["t"],
                               "t1": round(a["t"] + a["d"], 4), "dur": a["d"], "ease": a["ease"],
                               "from": a["from"], "to": a["to"], "end_xy": end_xy})
    n = int(round(spec["dur"] * spec["fps"]))
    curves = {}
    for shot in spec["shots"]:
        for el in shot["elements"]:
            ts = [i / spec["fps"] for i in range(n) if shot["t0"] <= i / spec["fps"] < shot["t1"]]
            curves[el["id"]] = {"t": ts, **{p: [value(el, p, t) for t in ts] for p in ("x", "y", "scale", "opacity")}}
    return {"W": spec["W"], "H": spec["H"], "fps": spec["fps"], "dur": spec["dur"], "events": events,
            "transitions": spec["transitions"], "curves": curves}


def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).parent / "mg-basic")
    out.mkdir(parents=True, exist_ok=True)
    (out / "index.html").write_text(PAGE.replace("__SPEC__", json.dumps(SPEC)), encoding="utf-8")
    (out / "truth.json").write_text(json.dumps(truth(SPEC), indent=1), encoding="utf-8")
    print(f"wrote {out}/index.html and truth.json")


if __name__ == "__main__":
    main()
