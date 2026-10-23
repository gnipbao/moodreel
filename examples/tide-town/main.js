// tide-town: a small island builds itself out of the sea, on Low-poly Isometric Island (styles/lowpoly-island).
// Flat-shaded primitives, an orthographic camera at an isometric angle, every arrival scheduled on a grid of 1/8 s
// slots; the sea is a faceted plane displaced on the CPU from t, so any frame stands alone.
import { stage, texts } from './kit/stage.js';
import { layer3d, orbit, THREE } from './kit/three.js';
import { clamp, rng } from './kit/core.js';

const W = 1920, H = 1080, SLOT = 0.125;
const L = layer3d(W, H, { background: null, shadows: true, ortho: 4.8, exposure: 1.05 });
const { scene } = L;
scene.add(new THREE.HemisphereLight('#fff6e8', '#4a6b7a', 1.6));
const sun = new THREE.DirectionalLight('#fff1d6', 2.4);
sun.position.set(-8, 14, 6); sun.castShadow = true; sun.shadow.mapSize.set(2048, 2048);
Object.assign(sun.shadow.camera, { left: -10, right: 10, top: 10, bottom: -10 });
scene.add(sun);
const mat = c => new THREE.MeshStandardMaterial({ color: c, flatShading: true, roughness: 0.9 });
const R = rng(7);

// arrivals: rise from below (cubic up, then a damped-sine overshoot), drop with a squash, pop with ~25 % overshoot
const rise = (t, at) => { const s = t - at; return s <= 0 ? 0 : s < 0.35 ? 1 - (1 - s / 0.35) ** 3 : 1 + 0.08 * Math.exp(-(s - 0.35) * 9) * Math.sin((s - 0.35) * 22); };
const popScale = (t, at) => { const s = t - at; return s <= 0 ? 0 : 1 - Math.exp(-9 * s) * Math.cos(16 * s); };
const drop = (t, at) => { const s = t - at; return s <= 0 ? { y: 6, sq: 0 } : s < 0.3 ? { y: 6 * (1 - (s / 0.3) ** 2), sq: 0 }
  : { y: 0, sq: 0.18 * Math.exp(-(s - 0.3) * 10) * Math.cos((s - 0.3) * 25) }; };

// the island: pointy-top hex columns, two rings round a centre, heights by material
const tiles = [], hex = new THREE.CylinderGeometry(0.98, 0.98, 1, 6);
for (let q = -3; q <= 3; q++) for (let r = -3; r <= 3; r++) {
  const d = Math.max(Math.abs(q), Math.abs(r), Math.abs(-q - r));
  if (d > 3) continue;
  const h = d === 3 ? 0.35 : d === 2 ? 0.6 + 0.1 * R() : 0.9 + 0.3 * R();
  const color = d === 3 ? '#e8d39a' : d === 2 ? '#7dbb5a' : (q + r) % 2 ? '#5e9a48' : '#6aa64f';
  const m = new THREE.Mesh(hex, mat(new THREE.Color(color).offsetHSL(0, 0, (R() - 0.5) * 0.04)));
  m.position.set(Math.sqrt(3) * (q + r / 2), 0, 1.5 * r);
  m.castShadow = m.receiveShadow = true;
  scene.add(m);
  tiles.push({ m, h, at: 0.2 + Math.round((d * 6 + R() * 5) * 1.0) * SLOT * 0.5 });
}
const top = (x, z) => tiles.reduce((best, t) => (Math.hypot(t.m.position.x - x, t.m.position.z - z) < 1 ? t.h : best), 0.4);

const houses = [[-1.7, 0.2, '#f2efe6', '#c8553d'], [0.9, -1.4, '#f6e7c8', '#3f6f8f'], [1.8, 1.2, '#f2efe6', '#c8553d'],
  [-0.4, 1.9, '#efe0c4', '#6b4f8f'], [-2.4, -1.6, '#f6e7c8', '#3f6f8f']].map(([x, z, wall, roof], i) => {
  const g = new THREE.Group();
  const body = new THREE.Mesh(new THREE.BoxGeometry(0.8, 0.6, 0.7), mat(wall));
  body.position.y = 0.3; body.castShadow = true;
  const cap = new THREE.Mesh(new THREE.ConeGeometry(0.62, 0.45, 4), mat(roof));
  cap.position.y = 0.82; cap.rotation.y = Math.PI / 4; cap.castShadow = true;
  g.add(body, cap); g.position.set(x, top(x, z), z); g.rotation.y = i * 0.6;
  scene.add(g);
  return { g, at: 2.25 + i * 2 * SLOT };
});
const trees = Array.from({ length: 12 }, (_, i) => {
  const a = i * 2.4, d = 1.2 + (i % 4) * 0.6, x = Math.cos(a) * d, z = Math.sin(a) * d;
  const g = new THREE.Group();
  const trunk = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.08, 0.3, 5), mat('#7a5638'));
  trunk.position.y = 0.15;
  const crown = new THREE.Mesh(i % 3 ? new THREE.ConeGeometry(0.32, 0.8, 6) : new THREE.IcosahedronGeometry(0.34, 0), mat(i % 2 ? '#2f7a4a' : '#3d8a52'));
  crown.position.y = 0.65; crown.castShadow = trunk.castShadow = true;
  g.add(trunk, crown); g.position.set(x, top(x, z), z);
  scene.add(g);
  return { g, at: 3.75 + i * SLOT };
});
// a mill: a tower and four blades that turn once it stands
const mill = new THREE.Group();
const tower = new THREE.Mesh(new THREE.CylinderGeometry(0.22, 0.32, 1.2, 8), mat('#efe6d4'));
tower.position.y = 0.6; tower.castShadow = true;
const hub = new THREE.Group(); hub.position.set(0, 1.15, 0.3);
for (let k = 0; k < 4; k++) { const b = new THREE.Mesh(new THREE.BoxGeometry(0.1, 0.75, 0.03), mat('#8a5a3c')); b.position.y = 0.38; const arm = new THREE.Group(); arm.rotation.z = k * Math.PI / 2; arm.add(b); hub.add(arm); }
mill.add(tower, hub); mill.position.set(0, top(0, 0), 0); scene.add(mill);
const MILL_AT = 5.5;

// the sea: a dense non-indexed plane, flat-shaded so each triangle glints on its own, displaced by summed sines
const seaGeo = new THREE.PlaneGeometry(40, 40, 70, 70).toNonIndexed();
seaGeo.rotateX(-Math.PI / 2);
const seaBase = seaGeo.attributes.position.array.slice();
const sea = new THREE.Mesh(seaGeo, new THREE.MeshStandardMaterial({ color: '#3f8fb5', flatShading: true, roughness: 0.55, metalness: 0.05 }));
sea.receiveShadow = true; sea.position.y = -0.05; scene.add(sea);
const wave = (x, z, t) => 0.06 * Math.sin(0.9 * x + 1.3 * t) + 0.05 * Math.sin(1.1 * z - 1.1 * t) + 0.03 * Math.sin(2.3 * (x + z) + 2.1 * t);

texts(t => (t >= 7.5 ? [{ id: 'title', text: 'Tide Town', x0: 120, y0: 930, x1: 520, y1: 1010 }] : []));

stage({ width: W, height: H, duration: 10, background: '#cfe4ee', fonts: ['600 72px Helvetica'], draw: (g, t) => {
  const sky = g.createLinearGradient(0, 0, 0, H);            // a sky without a horizon: a vertical screen gradient
  sky.addColorStop(0, '#b9d8ea'); sky.addColorStop(1, '#e9f1ec');
  g.fillStyle = sky; g.fillRect(0, 0, W, H);
  L.look(orbit(0.8 + 0.06 * t, 20, 16), [0, 0.4, 0]);       // isometric-ish elevation, a slow orbit; the projection never changes
  for (const tile of tiles) { const u = rise(t, tile.at); tile.m.scale.y = Math.max(0.001, tile.h * u); tile.m.position.y = tile.h * u / 2 - 0.05; tile.m.visible = u > 0; }
  for (const hs of houses) { const { y, sq } = drop(t, hs.at); hs.g.visible = t >= hs.at; hs.g.position.y = hs.g.userData.base ??= hs.g.position.y;
    hs.g.position.y = hs.g.userData.base + y; hs.g.scale.set(1 + sq, 1 - sq, 1 + sq); }
  for (const tr of trees) { const s = popScale(t, tr.at); tr.g.visible = s > 0; tr.g.scale.setScalar(Math.max(0.001, s)); }
  const ms = popScale(t, MILL_AT - 0.5); mill.visible = ms > 0; mill.scale.setScalar(Math.max(0.001, ms));
  hub.rotation.z = t > MILL_AT ? -(t - MILL_AT) * 1.6 : 0;
  const pos = seaGeo.attributes.position.array;
  for (let i = 0; i < pos.length; i += 3) pos[i + 1] = wave(seaBase[i], seaBase[i + 2], t);
  seaGeo.attributes.position.needsUpdate = true; seaGeo.computeVertexNormals();
  L.draw(g);
  const u = clamp((t - 7.5) / 0.4);                          // a quiet title, opening left to right
  if (u > 0) { g.save(); g.beginPath(); g.rect(110, 920, 420 * u, 110); g.clip();
    g.fillStyle = '#1f3a48'; g.font = '600 72px Helvetica'; g.fillText('Tide Town', 120, 995); g.restore(); }
}});
