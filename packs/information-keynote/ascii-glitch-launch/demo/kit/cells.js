// The cell pass, the style's core device: one GPU pass over a picture drawn in 2D, the frame cut into square cells,
// each cell shown as its colour plus a line glyph chosen by its brightness (ascii), as a lit rounded square or nothing
// (dots), as flat colour (pixelate), as diagonal hatching where it is lit (hatch), or as line glyphs on paper (lines: a
// dot, a slash, a cross as it brightens; the picture behind a transition at a tenth of its light). ascii with
// ramp: 'rings' draws the ramp measured on the beam and the dim eye (a grey ring in each dark cell, a slash, a cross, a
// dot in a box). The grid starts at the frame's corner; in GL y runs up, so `off` shifts it. `mix` blends back to the
// picture underneath; tap: 'centre' samples one point (type drawn as dashes), 'min' the darkest of four (thin strokes
// still darken their cell).
//
//   const C = cells(G);                                      // G = gpu(W, H) from kit/gl.js (kit/glitch.js frame() does this)
//   C.draw(layer.upload(), hdr, { mode: 'ascii', cell: 24, t });
import { THREE } from './gl.js';

const MODES = { ascii: 0, dots: 1, pixelate: 2, hatch: 3, lines: 4 };

export function cells(G) {
  const p = G.pass(/* glsl */ `
    uniform sampler2D src; uniform vec2 uRes; uniform float uCell, uMode, uMix, uT, uThr, uFlick, uGap, uGrid;
    uniform vec3 uInk, uPaper; uniform vec2 uOff; uniform float uTap, uRamp, uRing;
    float sdBox2(vec2 p, vec2 b, float r) { vec2 d = abs(p) - b + r; return length(max(d, 0.0)) + min(max(d.x, d.y), 0.0) - r; }
    float stroke(float d, float w) { return 1.0 - smoothstep(w * 0.5 - 0.02, w * 0.5 + 0.02, abs(d)); }
    void main() {
      vec2 px = gl_FragCoord.xy - uOff;
      vec2 id = floor(px / uCell), c = (id + 0.5) * uCell + uOff, q = (gl_FragCoord.xy - c) / uCell;   // q in -0.5..0.5
      // the cell's colour: four taps round its centre
      vec2 o = vec2(uCell * 0.25);
      vec3 s = 0.25 * (texture(src, (c + vec2(-o.x, -o.y)) / uRes).rgb + texture(src, (c + vec2(o.x, -o.y)) / uRes).rgb
                     + texture(src, (c + vec2(-o.x, o.y)) / uRes).rgb + texture(src, (c + o) / uRes).rgb);
      vec3 under = texture(src, vUv).rgb;
      // the darkest of the taps: a thin dark stroke anywhere in the cell still darkens it (type stays legible as dashes)
      vec3 d0 = uTap > 0.5 ? texture(src, c / uRes).rgb
        : min(min(texture(src, (c + vec2(-o.x, -o.y)) / uRes).rgb, texture(src, (c + vec2(o.x, -o.y)) / uRes).rgb),
              min(texture(src, (c + vec2(-o.x, o.y)) / uRes).rgb, texture(src, (c + o) / uRes).rgb));
      float l = luma(toSRGB(s)), h = hash12(id + floor(uT * 12.0) * 17.0);
      vec3 col;
      if (uMode < 0.5 && uRamp > 0.5) {                      // ascii, the ramp measured on the beam and the dim eye:
        float k = l + (h - 0.5) * 0.08, inBox = step(max(abs(q.x), abs(q.y)), 0.42), g = 0.0, w = 0.075;   // a grey ring
        vec3 lc = s * 1.8 + vec3(0.02);                      // when dark, a slash, then a cross, then a dot in a box
        if (k > uThr + 0.3) { g = max(stroke(sdBox2(q, vec2(0.42), 0.0), w), 1.0 - smoothstep(0.06, 0.1, length(q))); lc = s * 0.55; }
        else if (k > uThr + 0.15) g = max(stroke(q.x - q.y, w * 1.2), stroke(q.x + q.y, w * 1.2)) * inBox;
        else if (k > uThr) g = stroke(q.x - q.y, w * 1.2) * inBox;
        else { g = stroke(length(q) - 0.36, w); lc = vec3(uRing); }
        col = mix(s, lc, min(g, 1.0));
      } else if (uMode < 0.5) {                              // ascii: colour + a glyph by brightness
        col = s;
        float g = 0.0, w = 0.075;
        float k = l + (h - 0.5) * 0.12;
        if (luma(toSRGB(d0)) < 0.25 && (l > 0.3 || uTap > 0.5)) { col = uTap > 0.5 ? vec3(0.004) : d0 * 0.4; g = 0.0; k = -1.0; }   // a stroke: a solid dark cell
        if (k < -0.5) {}
        else if (h > 0.985) g = step(q.y - q.x, 0.0) * step(max(abs(q.x), abs(q.y)), 0.36) * 2.0;  // a stray triangle
        else if (k > 0.82) g = max(stroke(sdBox2(q, vec2(0.38), 0.0), w), 1.0 - smoothstep(0.06, 0.1, length(q)));
        else if (k > 0.62) g = h > 0.85 ? max(stroke(sdBox2(q, vec2(0.38), 0.0), w), stroke(abs(q.x) - abs(q.y), w * 1.2) * step(max(abs(q.x), abs(q.y)), 0.38))
                              : stroke(length(q) - 0.36, w);
        else if (k > 0.4) g = h > 0.9 ? step(q.x + q.y, 0.0) * step(max(abs(q.x), abs(q.y)), 0.38) : stroke(length(q) - 0.36, w);
        else if (k > 0.18) g = h > 0.94 ? step(q.y - q.x, 0.0) * step(max(abs(q.x), abs(q.y)), 0.36) : stroke(length(q) - 0.36, w * 0.8) * 0.7;
        else g = stroke(length(q) - 0.36, w * 0.7) * 0.45;
        vec3 lineCol = g > 1.5 ? vec3(0.0) : l > 0.5 ? s * 0.55 : s + vec3(0.12);
        g = min(g, 1.0);
        col = mix(col, lineCol, g);
        col = mix(col, s * 0.75, stroke(max(abs(q.x), abs(q.y)) - 0.5, 0.06) * uGrid);   // the grid between cells
      } else if (uMode < 1.5) {                              // dots: a lit cell is a rounded square
        float on = step(uThr, l), flick = step(1.0 - uFlick, h);
        float sq = 1.0 - smoothstep(-0.02, 0.02, sdBox2(q, vec2(0.5 - uGap), 0.08));
        vec3 lit = mix(uInk, uInk * 0.5 + uPaper * 0.5, flick);
        col = mix(uPaper, lit, on * sq);
      } else if (uMode < 2.5) {                              // pixelate
        col = s;
      } else if (uMode > 3.5) {                              // lines: a picture as line glyphs on paper, by brightness:
        float k = l + (h - 0.5) * 0.06, g = 0.0;              // nothing, a dot, a slash, a cross (y runs up: "/" is x = y)
        if (k > uThr + 0.3) g = max(stroke(q.x - q.y, 0.1), stroke(q.x + q.y, 0.1));
        else if (k > uThr + 0.12) g = stroke(q.x - q.y, 0.1);
        else if (k > uThr) g = 1.0 - smoothstep(0.08, 0.13, length(q));
        col = mix(uPaper, uInk, g * step(max(abs(q.x), abs(q.y)), 0.5));
      } else {                                               // hatch: diagonal stripes where lit, the cells showing
        float on = step(uThr, l);
        float st = 1.0 - smoothstep(0.32, 0.4, abs(fract((gl_FragCoord.x + gl_FragCoord.y) / (uCell * 0.5)) - 0.5) * 2.0);
        float gap = stroke(max(abs(q.x), abs(q.y)) - 0.5, 0.12);
        col = mix(uPaper, uInk, on * st * (1.0 - gap));
      }
      fragColor = vec4(mix(col, under, uMix), 1.0);
    }`, {
    src: { value: null }, uRes: { value: new THREE.Vector2(G.width, G.height) }, uCell: { value: 24 }, uMode: { value: 0 },
    uMix: { value: 0 }, uT: { value: 0 }, uThr: { value: 0.5 }, uFlick: { value: 0 }, uGap: { value: 0.1 }, uGrid: { value: 1 },
    uInk: { value: new THREE.Vector3(1, 1, 1) }, uPaper: { value: new THREE.Vector3(0, 0, 0) }, uOff: { value: new THREE.Vector2() },
    uTap: { value: 0 }, uRamp: { value: 0 }, uRing: { value: 0.05 },
  });
  return {
    draw(tex, target, { mode = 'ascii', cell = 24, mix = 0, t = 0, thr = 0.5, flick = 0, gap = 0.1, grid = 1, ink = [1, 1, 1],
      paper = [0, 0, 0], off = [0, 0], tap = 'min', ramp = null, ring = 0.05 } = {}) {
      const u = p.u;
      u.src.value = tex; u.uCell.value = cell; u.uMode.value = MODES[mode]; u.uMix.value = mix; u.uT.value = t;
      u.uThr.value = thr; u.uFlick.value = flick; u.uGap.value = gap; u.uGrid.value = grid;
      u.uInk.value.set(...ink); u.uPaper.value.set(...paper); u.uOff.value.set(...off); u.uTap.value = tap === 'centre' ? 1 : 0;
      u.uRamp.value = ramp === 'rings' ? 1 : 0; u.uRing.value = ring;
      u.uRes.value.set(target ? target.width : G.width, target ? target.height : G.height);
      p.render(target);
    } };
}
