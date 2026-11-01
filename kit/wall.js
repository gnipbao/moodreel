// The social wall (社媒口碑墙): a product's real posts, each recorded as its platform shows it (`moodreel wall`), as
// cards on a wall in perspective under one line of title. The values are the template's own, measured off the
// reference (skills/moodreel/references/produce/social-wall.md): a black ground under a faint 96 px grid; the cards in
// rows of one height, 31 px apart, with rounded corners; the wall turned 10.3° (its left side nearer) and coming round
// toward the viewer at 0.73° a second while it grows 0.66 % a second; the cards fading in one a frame, in reading
// order, each over 0.47 s (ease-out quart). Units are 4K pixels: the page is 3840 x 2160 and the stage scales it.
//
//   import { socialWall } from './kit/wall.js';
//   const wall = socialWall(media, spec, [canvas.width, canvas.height]);   // spec: wall.json (title, cards)
//   stage({ width: 3840, height: 2160, ..., draw: (g, t) => wall.draw(g, t) });
import { layer3d, THREE } from './three.js';

export const WALL = {
  ground: '#000000', grid: { step: 96, x: 48, y: 72, width: 2, colour: '#0c0c0c' },
  perspective: 3000,                      // the eye's distance from the frame, as CSS perspective
  centre: [64, 49], drift: -8.7,          // the wall's centre from the frame's (px) at t = 0, and its drift (px/s)
  yaw: 10.3, turn: -0.727,                // degrees at t = 0, and per second
  scale: 0.983, grow: 0.0066,             // at t = 0, and per second
  box: [2910, 1389], rowHeight: 679, gap: 31, radius: 0.036,   // the cards' box, a row's height at most, the gap
  stagger: 0.035, fade: 0.467,            // a card every 35 ms, each fading in this long
  title: { x: 1915, y: 210, size: 141, weight: 500, condense: 0.75, slant: 0.17, gap: 42, colour: '#fdfdfd', accent: '#7498f7',
    family: '"PingFang SC", "Noto Sans SC", "Source Han Sans SC", "Microsoft YaHei", sans-serif',
    // a Latin name is set in a condensed face of its own, taller than the CJK's Latin (cap height 110 px)
    latin: { size: 151, weight: 500, condense: 0.85, dy: 6, family: '"Avenir Next Condensed", "Roboto Condensed", "Arial Narrow", sans-serif' } },
};

const quartOut = u => 1 - (1 - Math.min(1, Math.max(0, u))) ** 4;

// The cards' places on the wall (px, from its centre, y down): in their order, in as many rows as make them biggest
// within the box, each row as tall as the others and centred, so reading order is top row first, left to right.
export function layout(aspects, { box = WALL.box, gap = WALL.gap, rowHeight = WALL.rowHeight } = {}) {
  const total = aspects.reduce((a, b) => a + b, 0);
  let best = null;
  for (let rows = 1; rows <= Math.min(5, aspects.length); rows++) {
    const groups = [[]];
    let acc = 0;
    aspects.forEach((a, i) => {                             // cut where the running width passes the next share
      if (groups.length < rows && groups.at(-1).length && acc + a / 2 > (total * groups.length) / rows) groups.push([]);
      groups.at(-1).push(i);
      acc += a;
    });
    if (groups.length < rows) continue;
    const h = Math.min(rowHeight, (box[1] - gap * (rows - 1)) / rows,
      ...groups.map(g => (box[0] - gap * (g.length - 1)) / g.reduce((s, i) => s + aspects[i], 0)));
    if (!best || h > best.h + 0.5) best = { groups, h };
  }
  const { groups, h } = best, H = groups.length * h + (groups.length - 1) * gap, cards = [];
  groups.forEach((g, r) => {
    const widths = g.map(i => aspects[i] * h);
    let x = -(widths.reduce((a, b) => a + b, 0) + gap * (g.length - 1)) / 2;
    g.forEach((i, j) => {
      cards[i] = { x: x + widths[j] / 2, y: -H / 2 + r * (h + gap) + h / 2, w: widths[j], h, row: r };
      x += widths[j] + gap;
    });
  });
  return cards;
}

function rounded(c, w, h, r) {
  c.beginPath();
  c.moveTo(r, 0); c.arcTo(w, 0, w, h, r); c.arcTo(w, h, 0, h, r); c.arcTo(0, h, 0, 0, r); c.arcTo(0, 0, w, 0, r);
  c.closePath();
}

// the ground and its grid, fixed to the frame
export function ground(g) {
  const { step, x, y, width, colour } = WALL.grid;
  g.fillStyle = WALL.ground; g.fillRect(0, 0, 3840, 2160);
  g.fillStyle = colour;
  for (let gx = x; gx < 3840; gx += step) g.fillRect(gx, 0, width, 2160);
  for (let gy = y; gy < 2160; gy += step) g.fillRect(0, gy, 3840, width);
}

// one line, centred: the lead in white, the product's name in the accent; condensed and slanted like the template's
export function title(g, lead, name) {
  const T = WALL.title, N = /^[\x20-\x7e]+$/.test(name) ? T.latin : T;     // a CJK name keeps the lead's face
  const leadFont = `${T.weight} ${T.size}px ${T.family}`, nameFont = `${N.weight} ${N.size}px ${N.family}`;
  g.save();
  g.textBaseline = 'alphabetic';
  g.font = leadFont; const a = g.measureText(lead).width * T.condense;
  g.font = nameFont; const b = g.measureText(name).width * N.condense;
  const gap = lead && name ? T.gap * T.condense : 0, span = a + gap + b;
  g.translate(T.x - span / 2, T.y);
  g.transform(1, 0, -T.slant, 1, 0, 0);
  g.save(); g.scale(T.condense, 1); g.font = leadFont; g.fillStyle = T.colour; g.fillText(lead, 0, 0); g.restore();
  g.translate(a + gap, N.dy || 0); g.scale(N.condense, 1); g.font = nameFont; g.fillStyle = T.accent; g.fillText(name, 0, 0);
  g.restore();
  return { x0: T.x - span / 2, x1: T.x + span / 2, y0: T.y - T.size * 0.92, y1: T.y + T.size * 0.12 };
}

// The wall: `media` from kit/media.js, `spec` from wall.json ({ title: [lead, name], cards: [{ name, aspect }] }),
// `pixels` the canvas's size, so the 3D layer renders at the output's resolution.
export function socialWall(media, spec, pixels) {
  const fov = (2 * Math.atan(1080 / WALL.perspective) * 180) / Math.PI;
  const L = layer3d(pixels[0], pixels[1], { fov, near: 10, far: 50000, toneMapping: 'none', background: null });
  L.look([0, 0, WALL.perspective], [0, 0, 0]);
  const group = new THREE.Group();
  L.scene.add(group);
  const places = layout(spec.cards.map(c => c.aspect));
  const cards = spec.cards.map((c, i) => {
    const first = media.frame(c.name, 0), cv = document.createElement('canvas');
    cv.width = first.naturalWidth || first.width; cv.height = first.naturalHeight || first.height;
    const tex = new THREE.CanvasTexture(cv);
    tex.colorSpace = THREE.SRGBColorSpace;
    tex.anisotropy = L.renderer.capabilities.getMaxAnisotropy();
    const mat = new THREE.MeshBasicMaterial({ map: tex, transparent: true, opacity: 0, depthWrite: false });
    const p = places[i], mesh = new THREE.Mesh(new THREE.PlaneGeometry(p.w, p.h), mat);
    mesh.position.set(p.x, -p.y, 0);
    group.add(mesh);
    return { name: c.name, from: c.from || 0, cv, ctx: cv.getContext('2d'), tex, mat, mesh };
  });
  const draw = (g, t) => {
    ground(g);
    group.rotation.y = ((WALL.yaw + WALL.turn * t) * Math.PI) / 180;
    group.scale.setScalar(WALL.scale + WALL.grow * t);
    group.position.set(WALL.centre[0] + WALL.drift * t, -WALL.centre[1], 0);
    cards.forEach((c, i) => {
      const o = quartOut((t - i * WALL.stagger) / WALL.fade);
      c.mesh.visible = o > 0;
      if (o <= 0) return;
      c.mat.opacity = o;
      const { width: w, height: h } = c.cv;
      c.ctx.clearRect(0, 0, w, h);
      c.ctx.save();
      rounded(c.ctx, w, h, WALL.radius * h);
      c.ctx.clip();
      c.ctx.drawImage(media.frame(c.name, t + c.from), 0, 0, w, h);
      c.ctx.restore();
      c.tex.needsUpdate = true;
    });
    L.draw(g, 0, 0, 3840, 2160);
    const [lead, name] = spec.title;
    return title(g, lead, name);
  };
  return { draw, places };
}
