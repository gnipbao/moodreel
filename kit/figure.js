// A rigged figure built by `moodreel model build`: <name>.json beside <name>.bin, read here with plain fetch and typed
// arrays (no three.js add-on). Each part is its own SkinnedMesh, named after the part; all share one skeleton. The
// figure's root sits at the origin unturned, so model coordinates are world coordinates: metres, y up, facing +z, its
// left on +x. Bones carry no rotation at rest, so each bone's own axes start parallel to the world's.
//
//   import * as figure from './kit/figure.js';
//   const fig = await figure.load('hero/mannequin.json');            // in stage({ prepare }): it is async
//   L.scene.add(fig.root);
//   draw: (g, t) => {
//     fig.setPose('walk');                                             // a pose by name, or { bone: [rx, ry, rz] }
//     fig.setExpression({ nod: 0.5 });                                 // weights over the spec's EXPRESSIONS
//     fig.reach('r', [-0.09, 1.12, 0.37]);                             // two-bone IK: the right wrist to a point
//     fig.aimHead(L.camera.position, 0.8);                             // look at the camera, 80% of the way
//     L.draw(g);
//   }
//
// Call them in that order every frame: setPose and setExpression set every bone afresh (pose, then expression on top),
// reach and aimHead then adjust the arm and the head from there. Angles are degrees, XYZ Euler (three.js's own order),
// about the bone's rest axes; bones a pose leaves out go back to rest. moodreel.model3d.skin does the same sums in
// Python (tests/test_model3d.py compares them vertex by vertex); `moodreel model check` measures penetration with it.
//
// Materials: by default a matte standard material per material name. Pass { material } to load() to choose your own:
// a function (partName, materialName) => THREE.Material, one material for every part, or an object keyed by part or
// material name; fig.setMaterial(...) takes the same later. fig.materials is the spec's MATERIALS as written (say,
// colour ramps per material name), fig.landmarks its named rest-pose points, and fig.attach(object, bone, at) hangs
// a prop on a bone.
import { THREE } from './three.js';

const ARRAYS = { float32: Float32Array, uint16: Uint16Array, uint32: Uint32Array };
const RAD = Math.PI / 180;
const TONES = { body: '#d8cdbd', joint: '#b9ad9c', default: '#cfc6b8' };
const scratch = { e: new THREE.Euler(), q: new THREE.Quaternion() };

// a point given as [x, y, z], a Vector3 or { x, y, z }, as a new Vector3
const vec = p => (Array.isArray(p) ? new THREE.Vector3(p[0], p[1], p[2]) : new THREE.Vector3(p.x, p.y, p.z));

async function grab(url, kind) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`figure: ${url} answered ${res.status}`);
  return kind === 'json' ? res.json() : res.arrayBuffer();
}

// a material per material name, made once and shared by the parts that use it
function matte() {
  const made = {};
  return (part, name) => made[name] || (made[name] = new THREE.MeshStandardMaterial({
    color: TONES[name] || TONES.default, roughness: 0.85, metalness: 0 }));
}

function chooser(material) {
  const fallback = matte();
  if (!material) return fallback;
  if (material.isMaterial) return () => material;
  if (typeof material === 'function') return material;
  return (part, name) => material[part] || material[name] || fallback(part, name);
}

// a limb's rest bending axis: from the upper bone's direction towards the lower's, or for a straight limb the axis
// that folds the lower bone forward (+z), the way an elbow folds the forearm to the front (skin.hinge in Python)
function hinge(u0, f0) {
  const n = new THREE.Vector3().crossVectors(u0, f0);
  if (n.length() > 1e-6) return n.normalize();
  const fwd = new THREE.Vector3(0, 0, 1).addScaledVector(u0, -u0.z);
  if (fwd.length() < 1e-6) fwd.set(0, 1, 0).addScaledVector(u0, -u0.y);
  return n.crossVectors(u0, fwd).normalize();
}

// the frame whose columns are a, n and a x n
const frameOf = (a, n) => new THREE.Matrix4().makeBasis(a, n, new THREE.Vector3().crossVectors(a, n));

export class Figure {
  constructor(meta, buffer, material = null) {
    this.name = meta.name;
    this.meta = meta;
    this.poses = meta.poses || {};
    this.expressions = meta.expressions || {};
    this.landmarks = meta.landmarks || {};
    this.materials = meta.materials || {};
    this.parts = meta.parts;
    this.root = new THREE.Group();
    this.root.name = meta.name;

    // bones: placed at their heads relative to their parents, unturned
    this.bones = {};
    this.rest = {};
    for (const b of meta.bones) {
      const bone = new THREE.Bone();
      bone.name = b.name;
      this.bones[b.name] = bone;
      this.rest[b.name] = new THREE.Vector3(...b.head);
    }
    for (const b of meta.bones) {
      const bone = this.bones[b.name];
      const base = b.parent ? this.rest[b.parent] : new THREE.Vector3();
      bone.position.copy(this.rest[b.name]).sub(base);
      (b.parent ? this.bones[b.parent] : this.root).add(bone);
    }
    const list = meta.bones.map(b => this.bones[b.name]);
    const unbind = meta.bones.map(b => new THREE.Matrix4().makeTranslation(-b.head[0], -b.head[1], -b.head[2]));
    this.skeleton = new THREE.Skeleton(list, unbind);

    // parts: slices of the shared arrays; triangle indices made local to the part
    const lay = meta.layout;
    const whole = key => new ARRAYS[lay[key].type](buffer, lay[key].offset, lay[key].count * lay[key].size);
    const pos = whole('position'), nrm = whole('normal'), wts = whole('skin_weight'), idx = whole('skin_index');
    const tri = whole('index');
    const pick = chooser(material);
    const identity = new THREE.Matrix4();
    this.meshes = meta.parts.map(p => {
      const g = new THREE.BufferGeometry();
      const span = (arr, size) => arr.subarray(p.first * size, (p.first + p.count) * size);
      g.setAttribute('position', new THREE.BufferAttribute(span(pos, 3), 3));
      g.setAttribute('normal', new THREE.BufferAttribute(span(nrm, 3), 3));
      g.setAttribute('skinIndex', new THREE.BufferAttribute(span(idx, 4), 4));
      g.setAttribute('skinWeight', new THREE.BufferAttribute(span(wts, 4), 4));
      const own = tri.subarray(p.face_first * 3, (p.face_first + p.face_count) * 3);
      const local = p.count < 65536 ? new Uint16Array(own.length) : new Uint32Array(own.length);
      for (let i = 0; i < own.length; i++) local[i] = own[i] - p.first;
      g.setIndex(new THREE.BufferAttribute(local, 1));
      const m = new THREE.SkinnedMesh(g, pick(p.name, p.material));
      m.name = p.name;
      m.userData.material = p.material;
      m.frustumCulled = false;                       // its bounds move with the pose; never cull it by stale ones
      this.root.add(m);
      m.bind(this.skeleton, identity);               // bind matrix: identity (the root is the world)
      return m;
    });
    this.vertexCount = meta.parts.reduce((s, p) => s + p.count, 0);
    this._pose = {};
    this._expression = {};
    this.root.updateMatrixWorld(true);
  }

  // every bone from the pose (a name or { bone: [rx, ry, rz] } in degrees), the expression turned on top
  setPose(pose) {
    if (typeof pose === 'string') {
      if (!this.poses[pose]) throw new Error(`figure ${this.name}: no pose "${pose}" (${Object.keys(this.poses).join(', ')})`);
      pose = this.poses[pose];
    }
    const unknown = Object.keys(pose || {}).filter(b => !this.bones[b]);
    if (unknown.length) throw new Error(`figure ${this.name}: the pose turns bones it doesn't have: ${unknown.join(', ')}`);
    this._pose = pose || {};
    return this._settle();
  }

  // { name: weight } over the spec's EXPRESSIONS: each one's angles, times its weight, added up per bone
  setExpression(weights = {}) {
    this._expression = { ...weights };
    return this._settle();
  }

  _settle() {
    const extra = {};
    for (const [name, w] of Object.entries(this._expression)) {
      const turns = this.expressions[name];
      if (!turns || !w) continue;                      // an expression the figure doesn't define is ignored
      for (const [bone, a] of Object.entries(turns)) {
        const s = extra[bone] || (extra[bone] = [0, 0, 0]);
        s[0] += w * a[0]; s[1] += w * a[1]; s[2] += w * a[2];
      }
    }
    const { e, q } = scratch;
    for (const [name, bone] of Object.entries(this.bones)) {
      const a = this._pose[name];
      if (a) bone.quaternion.setFromEuler(e.set(a[0] * RAD, a[1] * RAD, a[2] * RAD, 'XYZ'));
      else bone.quaternion.identity();
      const x = extra[name];
      if (x) bone.quaternion.multiply(q.setFromEuler(e.set(x[0] * RAD, x[1] * RAD, x[2] * RAD, 'XYZ')));
    }
    this.root.updateMatrixWorld(true);
    return this;
  }

  // two-bone IK: <side>_upperarm and <side>_forearm turn so the <side>_hand bone's origin lands on target (world).
  // The law of cosines puts the elbow L1 from the shoulder and L2 from the target, on the side `pole` points to (a
  // world point; by default behind, below and outside the shoulder, in the chest's axes). Each bone turns so its rest
  // frame (its direction and the rest hinge axis) lands on the new one: the elbow stays a hinge, the forearm doesn't
  // twist. Out of reach, the arm straightens towards the target. skin.reach in Python takes the same steps.
  reach(side, target, pole = null) {
    const up = this.bones[`${side}_upperarm`], mid = this.bones[`${side}_forearm`], end = this.bones[`${side}_hand`];
    if (!up || !mid || !end) throw new Error(`figure ${this.name}: reach needs ${side}_upperarm, ${side}_forearm, ${side}_hand`);
    this.root.updateMatrixWorld(true);
    const R = this.rest;
    const L1 = R[mid.name].distanceTo(R[up.name]), L2 = R[end.name].distanceTo(R[mid.name]);
    const u0 = R[mid.name].clone().sub(R[up.name]).normalize();
    const f0 = R[end.name].clone().sub(R[mid.name]).normalize();
    const n0 = hinge(u0, f0);
    const above = new THREE.Matrix4().extractRotation(up.parent.matrixWorld);
    const shoulder = up.getWorldPosition(new THREE.Vector3());

    const to = vec(target).sub(shoulder);
    let dist = to.length();
    const t = dist > 1e-9 ? to.divideScalar(dist) : u0.clone().applyMatrix4(above);
    dist = Math.min(Math.max(dist, Math.abs(L1 - L2) + 1e-9), L1 + L2 - 1e-9);
    const out = side === 'l' ? 1 : -1;
    const aim = pole ? vec(pole).sub(shoulder) : new THREE.Vector3(0.35 * out, -0.35, -1).applyMatrix4(above);
    const across = aim.addScaledVector(t, -aim.dot(t));
    if (across.length() < 1e-9) across.set(0, -1, 0).addScaledVector(t, -t.y);
    across.normalize();
    const along = (L1 * L1 - L2 * L2 + dist * dist) / (2 * dist);
    const off = Math.sqrt(Math.max(L1 * L1 - along * along, 0));
    const elbow = shoulder.clone().addScaledVector(t, along).addScaledVector(across, off);
    const u1 = elbow.clone().sub(shoulder).divideScalar(L1);
    const f1 = shoulder.clone().addScaledVector(t, dist).sub(elbow).divideScalar(L2);
    const n1 = new THREE.Vector3().crossVectors(across, t).normalize();

    const upperWorld = frameOf(u1, n1).multiply(frameOf(u0, n0).transpose());
    const lowerWorld = frameOf(f1, n1).multiply(frameOf(f0, n0).transpose());
    up.quaternion.setFromRotationMatrix(above.clone().transpose().multiply(upperWorld));
    mid.quaternion.setFromRotationMatrix(upperWorld.clone().transpose().multiply(lowerWorld));
    this.root.updateMatrixWorld(true);
    return this;
  }

  // the head turned to face `point` (world), upright, `weight` of the way from its pose (0..1); the neck takes about a
  // third of the turn first, so the look doesn't all hinge at the skull
  aimHead(point, weight = 1) {
    const head = this.bones.head;
    if (!head || !(weight > 0)) return this;
    const at = vec(point);
    this.root.updateMatrixWorld(true);
    const neck = this.bones.neck;
    const q = () => new THREE.Quaternion();
    if (neck && head.parent === neck) {
      const want = at.clone().sub(head.getWorldPosition(new THREE.Vector3())).normalize();
      const facing = new THREE.Vector3(0, 0, 1).applyQuaternion(head.getWorldQuaternion(q()));
      const share = q().slerp(q().setFromUnitVectors(facing, want), 0.35 * Math.min(weight, 1));
      const parentTurn = neck.parent.getWorldQuaternion(q()).invert();
      neck.quaternion.copy(parentTurn.multiply(share.multiply(neck.getWorldQuaternion(q()))));
      neck.updateMatrixWorld(true);
    }
    const z = at.clone().sub(head.getWorldPosition(new THREE.Vector3())).normalize();
    const x = new THREE.Vector3(0, 1, 0).cross(z);
    if (x.length() < 1e-6) x.set(1, 0, 0);
    x.normalize();
    const facingWorld = q().setFromRotationMatrix(new THREE.Matrix4().makeBasis(x, new THREE.Vector3().crossVectors(z, x), z));
    const blended = head.getWorldQuaternion(q()).slerp(facingWorld, Math.min(weight, 1));
    head.quaternion.copy(head.parent.getWorldQuaternion(q()).invert().multiply(blended));
    this.root.updateMatrixWorld(true);
    return this;
  }

  // an object carried by a bone (a pen in the hand): `at`, a rest-pose world point, is where it sits on the bone
  attach(object, bone, at = null) {
    const b = this.bones[bone];
    if (!b) throw new Error(`figure ${this.name}: no bone ${bone}`);
    if (at) object.position.copy(vec(at).sub(this.rest[bone]));
    b.add(object);
    return object;
  }

  setMaterial(material) {
    const pick = chooser(material);
    for (const m of this.meshes) m.material = pick(m.name, m.userData.material);
    return this;
  }
}

// the figure at `url` (the json; its bin is found beside it). options.material: see the top of this file
export async function load(url, { material = null } = {}) {
  const where = new URL(url, location.href);
  const meta = await grab(where, 'json');
  if (meta.format !== 'moodreel-figure') throw new Error(`figure: ${url} is not a moodreel model (format ${meta.format})`);
  const buffer = await grab(new URL(meta.bin, where), 'bin');
  if (buffer.byteLength < meta.byteLength) throw new Error(`figure: ${meta.bin} is shorter than ${url} says`);
  return new Figure(meta, buffer, material);
}
