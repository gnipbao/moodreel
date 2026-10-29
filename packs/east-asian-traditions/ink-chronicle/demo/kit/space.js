// Ink Chronicle: a space to stage type in (STYLE §2, §6). A three.js layer with the style's light and haze where a film
// lays its own text on planes at any angle (a floor, walls, a ceiling, a page in the air) and stands characters as
// blocks, then moves its camera through them. It renders into its own canvas; the shot lays that into the 2D frame and
// draws type over it. Nothing here is a scene: the film builds its own from these parts.
//
//   const S = typeSpace(1280, 720);
//   S.plane('floor', { corpus, size: [200, 400], p: [0, 0, -150], r: [-Math.PI / 2, 0, 0] });
//   S.block('k1', '河', { accent: true });
//   g.drawImage(S.render({ p: [0, 2, 8], l: [0, 0.5, -4] }, { place: k => ({ p: [...], r: [...] }) }), 0, 0, W, H);
import { THREE } from './three.js';
import { INK } from './tokens.js';
import { hash } from './anim.js';
import { SONG, font } from './faces.js';
import { canvas } from './paper.js';

// a texture of text: the corpus set in a grid of cells, each character's ink a little different; light or dark
export function textTexture(corpus, { dark = false, cell = 128, n = 2048, ink = dark ? [118, 114, 108] : [30, 26, 22], ground = dark ? '#0b0a09' : '#f6f0e5', weight = 700, alpha = [0.35, 0.55] } = {}) {
  const [c, g] = canvas(n, n), chars = [...corpus];
  g.fillStyle = ground; g.fillRect(0, 0, n, n);
  g.font = font(weight, cell * 0.81, SONG); g.textAlign = 'center'; g.textBaseline = 'middle';
  for (let j = 0; j < n / cell; j++) for (let i = 0; i < n / cell; i++) {
    const k = j * (n / cell) + i, v = hash(k, 3);
    g.fillStyle = `rgba(${ink},${alpha[0] + alpha[1] * v})`;
    g.fillText(chars[k % chars.length], i * cell + cell / 2, j * cell + cell / 2 + 4);
  }
  const tex = new THREE.CanvasTexture(c);
  tex.wrapS = tex.wrapT = THREE.RepeatWrapping; tex.anisotropy = 8; tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}

function faceTexture(ch, fg, bg) {
  const [c, g] = canvas(256, 256);
  g.fillStyle = bg; g.fillRect(0, 0, 256, 256);
  g.fillStyle = fg; g.font = font(900, 190, SONG); g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText(ch, 128, 140);
  const tex = new THREE.CanvasTexture(c); tex.colorSpace = THREE.SRGBColorSpace; return tex;
}

export function typeSpace(w = 1280, h = 720) {
  const R = new THREE.WebGLRenderer({ antialias: true, alpha: false });
  R.setPixelRatio(1); R.setSize(w, h, false); R.outputColorSpace = THREE.SRGBColorSpace;
  const scene = new THREE.Scene(), cam = new THREE.PerspectiveCamera(40, w / h, 0.05, 400);
  scene.fog = new THREE.Fog(0xf4f0ea, 6, 60);
  const amb = new THREE.AmbientLight(0xffffff, 1.6), sun = new THREE.DirectionalLight(0xffffff, 2.2);
  sun.position.set(-3, 8, 6); scene.add(amb, sun);
  const spot = new THREE.SpotLight(0xfff4e8, 0, 30, 0.35, 0.6, 1); scene.add(spot, spot.target);
  const items = {};
  const S = {
    canvas: R.domElement, scene, items,
    // a plane printed with text: any size, place and turn (a floor lies at r [-PI/2, 0, 0], a wall stands at r 0);
    // `day` and `night` textures are made once, the shot picks one
    plane(key, { corpus, size = [40, 40], p = [0, 0, 0], r = [0, 0, 0], repeat = [4, 4], cell = 128 } = {}) {
      const day = textTexture(corpus, { cell }), night = textTexture(corpus, { dark: true, cell, alpha: [0.3, 0.45] });
      day.repeat.set(...repeat); night.repeat.set(...repeat);
      const mat = new THREE.MeshBasicMaterial({ map: day, side: THREE.DoubleSide });
      const m = new THREE.Mesh(new THREE.PlaneGeometry(...size), mat);
      m.position.set(...p); m.rotation.set(...r); m.userData = { kind: 'plane', day, night, mat, repeat }; scene.add(m);
      return (items[key] = m);
    },
    // a character standing as a block: its face in the accent with white type, or grey once its meaning is gone
    block(key, ch, { accent = INK.accentTile, side = 0xd9542a, size = [1, 1, 0.42] } = {}) {
      const tex = faceTexture(ch, '#ffffff', accent), texG = faceTexture(ch, '#e2ded7', '#6d6964');
      const sideM = new THREE.MeshLambertMaterial({ color: side }), sideG = new THREE.MeshLambertMaterial({ color: 0x4f4b47 });
      const face = new THREE.MeshLambertMaterial({ map: tex, emissive: 0xffffff, emissiveMap: tex, emissiveIntensity: 0 });
      const faceG = new THREE.MeshLambertMaterial({ map: texG, emissive: 0xffffff, emissiveMap: texG, emissiveIntensity: 0 });
      const m = new THREE.Mesh(new THREE.BoxGeometry(...size), [sideM, sideM, sideM, sideM, face, sideM]);
      m.userData = { kind: 'block', lit: m.material, grey: [sideG, sideG, sideG, sideG, faceG, sideG], faces: [face, faceG] };
      scene.add(m);
      return (items[key] = m);
    },
    // the shot: the camera { p, l, fov, roll } and its settings: theme 'day' or 'night', fog [near, far], the light
    // ({ ambient, sun, spot: [x, y, z], spotI }), the text planes' brightness (`words`) and size (`repeat`), the
    // blocks' glow by night; place(key) -> null (hidden) or { p, r, s, grey } for whatever moves
    render(c, { theme = 'day', fog = null, words = 1, repeat = null, glow = 0, glowGrey = 0, light = {}, place = null } = {}) {
      const night = theme === 'night', bg = night ? 0x070606 : 0xfbf8f0;
      scene.background = new THREE.Color(bg); scene.fog.color.set(bg);
      [scene.fog.near, scene.fog.far] = fog ?? (night ? [3, 26] : [6, 60]);
      amb.intensity = light.ambient ?? (night ? 0.25 : 1.6); sun.intensity = light.sun ?? (night ? 0.15 : 2.2);
      spot.intensity = night ? (light.spotI ?? 0) : 0;
      if (light.spot) { spot.position.set(...light.spot); spot.target.position.set(light.spot[0], 0, light.spot[2]); }
      for (const [k, m] of Object.entries(items)) {
        if (m.userData.kind === 'plane') {
          const u = m.userData; u.mat.map = night ? u.night : u.day; u.mat.color.setScalar(words); u.mat.needsUpdate = true;
          if (repeat) u.mat.map.repeat.set(...repeat);
        }
        const q = place ? place(k) : undefined;
        if (q === null) { m.visible = false; continue; }
        m.visible = true;
        if (q) { if (q.p) m.position.set(...q.p); if (q.r) m.rotation.set(...q.r); m.scale.setScalar(q.s ?? 1); }
        if (m.userData.kind === 'block') {
          m.material = q?.grey ? m.userData.grey : m.userData.lit;
          m.userData.faces[0].emissiveIntensity = glow; m.userData.faces[1].emissiveIntensity = glowGrey;
        }
      }
      cam.fov = c.fov ?? 40; cam.position.set(...c.p); cam.up.set(0, 1, 0); cam.lookAt(...c.l); cam.rotateZ(c.roll ?? 0); cam.updateProjectionMatrix();
      R.render(scene, cam);
      return R.domElement;
    },
    // where a world point lands in the frame (shares of the width and height), with the last camera rendered
    toScreen(pt) { const v = new THREE.Vector3(...pt).project(cam); return [(v.x + 1) / 2, (1 - v.y) / 2, v.z]; },
  };
  return S;
}

// fit a camera to a composition: world points that should land on screen points (x, y as shares of the frame).
// targets [[[x, y, z], sx, sy], ...]; start [px, py, pz, lx, ly, lz, roll]; a pattern search, a few thousand projections
export function fitCamera(targets, start, { fov = 40, aspect = 16 / 9 } = {}) {
  const cam = new THREE.PerspectiveCamera(fov, aspect, 0.05, 300), v3 = new THREE.Vector3();
  const proj = (v, pt) => { cam.position.set(v[0], v[1], v[2]); cam.up.set(0, 1, 0); cam.lookAt(v[3], v[4], v[5]); cam.rotateZ(v[6] || 0); cam.updateMatrixWorld();
    cam.updateProjectionMatrix(); const q = v3.set(...pt).project(cam); return [(q.x + 1) / 2, (1 - q.y) / 2, q.z]; };
  const err = v => targets.reduce((s, [pt, sx, sy]) => { const [x, y, z] = proj(v, pt); return s + (z > 1 ? 9 : (x - sx) ** 2 + (y - sy) ** 2); }, 0);
  let v = start.slice(), e = err(v), step = 0.5;
  for (let it = 0; it < 6000 && step > 1e-4; it++) {
    let better = false;
    for (let k = 0; k < v.length; k++) for (const d of [step, -step]) { const w = v.slice(); w[k] += d * (k === 6 ? 0.1 : 1); const ew = err(w); if (ew < e) { v = w; e = ew; better = true; } }
    if (!better) step *= 0.6;
  }
  return { p: v.slice(0, 3), l: v.slice(3, 6), roll: v[6] || 0, fov, rms: Math.sqrt(e / targets.length) };
}
