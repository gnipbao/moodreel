// GSAP-named eases, the same formulas as moodreel/motion/eases.py (a test keeps the two in step).
//   ease('power3.out')(u), ease('back.out(1.7)')(u), ease('elastic.out(1,0.3)')(u)      u in [0, 1]
// A measured style names its eases this way, so a style's motion.js drops straight into a page.

const directions = ein => ({
  in: ein,
  out: u => 1 - ein(1 - u),
  inOut: u => (u < 0.5 ? ein(2 * u) / 2 : 1 - ein(2 - 2 * u) / 2),
});

const BASE = { none: u => u };
for (let n = 1; n <= 4; n++) for (const [d, f] of Object.entries(directions(u => u ** (n + 1)))) BASE[`power${n}.${d}`] = f;
Object.assign(BASE, {
  'sine.in': u => 1 - Math.cos((u * Math.PI) / 2),
  'sine.out': u => Math.sin((u * Math.PI) / 2),
  'sine.inOut': u => -(Math.cos(Math.PI * u) - 1) / 2,
  'expo.in': u => (u <= 0 ? 0 : 2 ** (10 * u - 10)),
  'expo.out': u => (u >= 1 ? 1 : 1 - 2 ** (-10 * u)),
  'expo.inOut': u => (u <= 0 ? 0 : u >= 1 ? 1 : u < 0.5 ? 2 ** (20 * u - 10) / 2 : (2 - 2 ** (-20 * u + 10)) / 2),
  'circ.in': u => 1 - Math.sqrt(Math.max(0, 1 - u * u)),
  'circ.out': u => Math.sqrt(Math.max(0, 1 - (u - 1) ** 2)),
  'circ.inOut': u => (u < 0.5 ? (1 - Math.sqrt(Math.max(0, 1 - (2 * u) ** 2))) / 2
    : (Math.sqrt(Math.max(0, 1 - (-2 * u + 2) ** 2)) + 1) / 2),
  'bounce.out': u => {
    const n = 7.5625, d = 2.75;
    if (u < 1 / d) return n * u * u;
    if (u < 2 / d) return n * (u -= 1.5 / d) * u + 0.75;
    if (u < 2.5 / d) return n * (u -= 2.25 / d) * u + 0.9375;
    return n * (u -= 2.625 / d) * u + 0.984375;
  },
});

const cache = new Map();

export function ease(name) {
  if (cache.has(name)) return cache.get(name);
  const m = name.replace(/\s/g, '').match(/^([a-zA-Z0-9.]+)(?:\(([^)]*)\))?$/);
  if (!m) throw new Error(`bad ease ${name}`);
  const base = m[1], a = m[2] ? m[2].split(',').map(Number) : [];
  let f = BASE[base];
  if (!f) {
    const s = a[0] ?? 1.7;
    if (base === 'back.in') f = u => (s + 1) * u ** 3 - s * u ** 2;
    else if (base === 'back.out') f = u => 1 + (s + 1) * (u - 1) ** 3 + s * (u - 1) ** 2;
    else if (base === 'back.inOut') {
      const c = s * 1.525;
      f = u => (u < 0.5 ? ((2 * u) ** 2 * ((c + 1) * 2 * u - c)) / 2 : ((2 * u - 2) ** 2 * ((c + 1) * (u * 2 - 2) + c) + 2) / 2);
    } else if (base === 'elastic.out') {
      const amp = Math.max(a[0] ?? 1, 1), per = a[1] ?? 0.3, p3 = (per / (2 * Math.PI)) * Math.asin(1 / amp);
      f = u => (u >= 1 ? 1 : amp * 2 ** (-10 * u) * Math.sin(((u - p3) * 2 * Math.PI) / per) + 1);
    } else throw new Error(`unknown ease ${name}`);
  }
  cache.set(name, f);
  return f;
}

// cubic-bezier(x1, y1, x2, y2) as an ease: for measured curves that have no GSAP name
export function bezier(x1, y1, x2, y2) {
  return u => {
    let s = u;
    for (let i = 0; i < 12; i++) {
      const x = 3 * (1 - s) ** 2 * s * x1 + 3 * (1 - s) * s * s * x2 + s ** 3 - u;
      const dx = 3 * (1 - s) ** 2 * x1 + 6 * (1 - s) * s * (x2 - x1) + 3 * s * s * (1 - x2);
      s = Math.min(1, Math.max(0, s - x / (Math.abs(dx) < 1e-6 ? 1e-6 : dx)));
    }
    return 3 * (1 - s) ** 2 * s * y1 + 3 * (1 - s) * s * s * y2 + s ** 3;
  };
}

export const EASE_NAMES = Object.keys(BASE);
