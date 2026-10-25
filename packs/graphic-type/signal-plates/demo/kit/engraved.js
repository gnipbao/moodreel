// Signal Plates idiom: the engraved body. A solid given by a signed distance (GLSL `float map(vec3 p)`, smooth unions
// welcome) ray-marched on the GPU and engraved: parallel contour lines cut across it along one axis, each line wider
// where the light falls (on a dark plate the lines are the light), a hairline silhouette, and whatever the body itself
// emits (`vec3 glow(vec3 p, vec3 n)`, linear, past 1 to bloom: a hot band, a charge level, a seam).
//
//   const body = engraved(P.G, { glsl: `uniform float uLevel;
//     float map(vec3 p) { return sdCapsule(p, vec3(0, -1, 0), vec3(0, 1, 0), 0.5); }
//     vec3 glow(vec3 p, vec3 n) { return C_SIGNAL * 3.0 * step(p.y, uLevel); }`, uniforms: { uLevel: { value: -0.8 } } });
//   body.look([3, 1, 4], [0, 0, 0], 30);   // eye, target, vertical field of view in degrees
//   body.render(P.hdr, t);
//
// The lines follow the body's own surface (slices along `axis`, freq lines a unit), so they wrap round its forms as an
// engraver's would, and stay put on it as the camera moves. `weight` is a line's width in full light, as a share of
// the spacing (hairlines at 0.3-0.5); bone only in the highlights, graphite elsewhere. The glow sits mostly on the
// lines (`glowFill` of it between them). uT (seconds) is declared for the body's GLSL. All from t: no state between frames.
import { THREE } from './gl.js';

export function engraved(G, { glsl, uniforms = {}, axis = [0, 1, 0], freq = 40, light = [-0.55, 0.65, 0.5], steps = 160,
  far = 40, ink = 'C_BONE', shade = 'C_GRAPHITE', edge = 0.7, weight = 0.42, glowFill = 0.25 } = {}) {
  const hasGlow = /vec3\s+glow\s*\(/.test(glsl);
  const p = G.pass(/* glsl */ `
    uniform vec3 uEye, uTarget, uLight, uAxis; uniform float uFov, uT, uFreq, uEdge; uniform vec2 uRes;
    ${glsl}
    ${hasGlow ? '' : 'vec3 glow(vec3 p, vec3 n) { return vec3(0.0); }'}
    vec3 nrm(vec3 p) {
      const vec2 k = vec2(1.0, -1.0); const float e = 0.0008;
      return normalize(k.xyy * map(p + k.xyy * e) + k.yyx * map(p + k.yyx * e) + k.yxy * map(p + k.yxy * e) + k.xxx * map(p + k.xxx * e));
    }
    void main() {
      vec3 f = normalize(uTarget - uEye), r = normalize(cross(f, vec3(0.0, 1.0, 0.0))), u = cross(r, f);
      float fl = 0.5 / tan(radians(uFov) * 0.5), px = 1.0 / (fl * uRes.y);
      vec2 q = (gl_FragCoord.xy - 0.5 * uRes) / uRes.y;
      vec3 rd = normalize(f * fl + r * q.x + u * q.y);
      float t = 0.0, dmin = 1e9, tmin = 0.0; bool hit = false;
      for (int i = 0; i < ${steps}; i++) {
        float d = map(uEye + rd * t);
        if (d < dmin) { dmin = d; tmin = t; }
        if (d < 0.0004 * max(t, 1.0)) { hit = true; break; }
        t += d * 0.9;
        if (t > ${far.toFixed(1)}) break;
      }
      vec3 pos = uEye + rd * t, n = hit ? nrm(pos) : vec3(0.0, 0.0, 1.0);
      float lam = max(0.0, dot(n, normalize(uLight)));
      float facing = abs(dot(n, rd));
      float tone = sat(0.08 + 0.92 * lam) * smoothstep(0.0, 0.35, facing);   // the light, falling off at the rim
      float cov = hatch(dot(pos, normalize(uAxis)) * uFreq, tone * ${weight.toFixed(3)});   // the engraver's lines, wider in light
      vec3 col = mix(${shade}, ${ink}, smoothstep(0.55, 1.0, tone)) * cov;
      // the silhouette: a hairline where the ray grazes the body (anti-aliased by its closest approach)
      float rim = hit ? smoothstep(0.25, 0.0, facing) : 1.0 - smoothstep(0.0, 1.2 * px * tmin, dmin);
      col = max(col, ${ink} * rim * uEdge);
      if (hit) col += glow(pos, n) * mix(${glowFill.toFixed(3)}, 1.0, sat(cov / max(1e-3, tone * ${weight.toFixed(3)})));
      float a = hit ? 1.0 : rim;
      if (a <= 0.0) discard;
      fragColor = vec4(col, a);
    }`, {
    uEye: { value: new THREE.Vector3(0, 0, 5) }, uTarget: { value: new THREE.Vector3() }, uLight: { value: new THREE.Vector3(...light) },
    uAxis: { value: new THREE.Vector3(...axis) }, uFov: { value: 30 }, uT: { value: 0 }, uFreq: { value: freq }, uEdge: { value: edge },
    uRes: { value: new THREE.Vector2(G.width, G.height) }, ...uniforms,
  }, { blend: 'normal' });
  return { pass: p, u: p.u,
    look(eye, target = [0, 0, 0], fov = 30) { p.u.uEye.value.set(...eye); p.u.uTarget.value.set(...target); p.u.uFov.value = fov; },
    render(target, t = 0) {
      p.u.uT.value = t;
      p.u.uRes.value.set(target ? target.width : G.width, target ? target.height : G.height);
      p.render(target);
    } };
}
