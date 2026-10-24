// Glyph outlines from a TrueType font file, for drawing type as paths: breaking a word into strokes that fly apart,
// filling letters with particles, tracing a glyph with the spark. Static TrueType (glyf) fonts only: simple and composite
// glyphs, cmap formats 4 and 12, advances from hmtx. No kerning or shaping: place glyphs where a layout puts them.
//
//   const font = outline(await (await fetch('fonts/Archivo-w1000-900.ttf')).arrayBuffer());
//   font.charToGlyph('P').getPath(x, baseline, 300).commands   // [{ type: 'M' | 'L' | 'Q' | 'Z', x, y, x1, y1 }], y down
//   font.path2D('P', x, baseline, 300)                         // a Path2D to fill or stroke
//
// The shape of the result follows opentype.js (MIT), so code written against it reads the same.

export function outline(buffer) {
  const v = new DataView(buffer);
  const tag = o => String.fromCharCode(v.getUint8(o), v.getUint8(o + 1), v.getUint8(o + 2), v.getUint8(o + 3));
  const sfnt = v.getUint32(0);
  if (sfnt === 0x4f54544f) throw new Error('outline: a CFF (OTTO) font; only TrueType outlines are read');
  const tables = {};
  for (let i = 0, n = v.getUint16(4); i < n; i++) {
    const r = 12 + i * 16;
    tables[tag(r)] = { offset: v.getUint32(r + 8), length: v.getUint32(r + 12) };
  }
  for (const t of ['head', 'maxp', 'hhea', 'hmtx', 'loca', 'glyf', 'cmap'])
    if (!tables[t]) throw new Error(`outline: no ${t} table`);
  const head = tables.head.offset;
  const unitsPerEm = v.getUint16(head + 18), longLoca = v.getInt16(head + 50) === 1;
  const numGlyphs = v.getUint16(tables.maxp.offset + 4);
  const nHM = v.getUint16(tables.hhea.offset + 34);
  const advance = g => v.getUint16(tables.hmtx.offset + 4 * Math.min(g, nHM - 1));
  const loca = g => (longLoca ? v.getUint32(tables.loca.offset + 4 * g) : v.getUint16(tables.loca.offset + 2 * g) * 2);
  const glyphOf = cmap(v, tables.cmap.offset);

  // a glyph's contours in font units, y up: [[{ x, y, on }]]
  const cache = new Map();
  function contours(g, depth = 0) {
    if (cache.has(g)) return cache.get(g);
    let out = [];
    const a = loca(g), b = loca(g + 1);
    if (g < numGlyphs && b > a && depth < 8) {
      const o = tables.glyf.offset + a, n = v.getInt16(o);
      out = n >= 0 ? simple(v, o, n) : composite(v, o, depth, contours);
    }
    cache.set(g, out);
    return out;
  }

  function glyph(index) {
    return { index, advanceWidth: advance(index),
      getPath(x = 0, y = 0, size = 72) {
        const k = size / unitsPerEm, commands = [];
        for (const c of contours(index)) commands.push(...quads(c, p => [x + p.x * k, y - p.y * k]));
        return { commands };
      } };
  }
  const charToGlyph = ch => glyph(glyphOf(ch.codePointAt(0)));
  return { unitsPerEm, numGlyphs, charToGlyph, glyph,
    // a whole string by advances alone (no kerning)
    getPath(text, x = 0, y = 0, size = 72) {
      const commands = [];
      for (const ch of text) {
        const gl = charToGlyph(ch);
        commands.push(...gl.getPath(x, y, size).commands);
        x += gl.advanceWidth * size / unitsPerEm;
      }
      return { commands };
    },
    path2D(text, x = 0, y = 0, size = 72) { return toPath2D(this.getPath(text, x, y, size).commands); } };
}

export function toPath2D(commands) {
  const p = new Path2D();
  for (const c of commands) {
    if (c.type === 'M') p.moveTo(c.x, c.y);
    else if (c.type === 'L') p.lineTo(c.x, c.y);
    else if (c.type === 'Q') p.quadraticCurveTo(c.x1, c.y1, c.x, c.y);
    else if (c.type === 'C') p.bezierCurveTo(c.x1, c.y1, c.x2, c.y2, c.x, c.y);
    else if (c.type === 'Z') p.closePath();
  }
  return p;
}

function cmap(v, base) {
  let best = null;
  for (let i = 0, n = v.getUint16(base + 2); i < n; i++) {
    const r = base + 4 + i * 8, pid = v.getUint16(r), eid = v.getUint16(r + 2), off = base + v.getUint32(r + 4);
    const fmt = v.getUint16(off), unicode = pid === 0 || (pid === 3 && (eid === 1 || eid === 10));
    if (!unicode || (fmt !== 4 && fmt !== 12)) continue;
    if (!best || fmt === 12) best = { fmt, off };
  }
  if (!best) throw new Error('outline: no Unicode cmap (format 4 or 12)');
  const { fmt, off } = best;
  if (fmt === 12) {
    const n = v.getUint32(off + 12);
    return cp => {
      for (let i = 0; i < n; i++) {
        const r = off + 16 + i * 12, s = v.getUint32(r), e = v.getUint32(r + 4);
        if (cp >= s && cp <= e) return v.getUint32(r + 8) + cp - s;
      }
      return 0;
    };
  }
  const seg = v.getUint16(off + 6) / 2, ends = off + 14, starts = ends + seg * 2 + 2, deltas = starts + seg * 2, ranges = deltas + seg * 2;
  return cp => {
    for (let i = 0; i < seg; i++) {
      if (cp > v.getUint16(ends + 2 * i)) continue;
      const s = v.getUint16(starts + 2 * i);
      if (cp < s) return 0;
      const ro = v.getUint16(ranges + 2 * i), d = v.getInt16(deltas + 2 * i);
      if (!ro) return (cp + d) & 0xffff;
      const g = v.getUint16(ranges + 2 * i + ro + 2 * (cp - s));
      return g ? (g + d) & 0xffff : 0;
    }
    return 0;
  };
}

function simple(v, o, n) {
  const ends = [];
  for (let i = 0; i < n; i++) ends.push(v.getUint16(o + 10 + 2 * i));
  const count = n ? ends[n - 1] + 1 : 0;
  let p = o + 10 + 2 * n;
  p += 2 + v.getUint16(p);                                   // instructions
  const flags = [];
  while (flags.length < count) {
    const f = v.getUint8(p++);
    flags.push(f);
    if (f & 8) for (let r = v.getUint8(p++); r > 0; r--) flags.push(f);
  }
  const coords = (short, same) => {
    const out = [];
    let c = 0;
    for (const f of flags) {
      if (f & short) { const d = v.getUint8(p++); c += f & same ? d : -d; }
      else if (!(f & same)) { c += v.getInt16(p); p += 2; }
      out.push(c);
    }
    return out;
  };
  const xs = coords(2, 16), ys = coords(4, 32), out = [];
  let s = 0;
  for (const e of ends) {
    const c = [];
    for (let i = s; i <= e; i++) c.push({ x: xs[i], y: ys[i], on: (flags[i] & 1) === 1 });
    out.push(c);
    s = e + 1;
  }
  return out;
}

function composite(v, o, depth, contours) {
  const out = [];
  let p = o + 10, more = true;
  while (more) {
    const f = v.getUint16(p), g = v.getUint16(p + 2);
    p += 4;
    let dx, dy;
    if (f & 1) { dx = v.getInt16(p); dy = v.getInt16(p + 2); p += 4; }
    else { dx = v.getInt8(p); dy = v.getInt8(p + 1); p += 2; }
    if (!(f & 2)) { dx = 0; dy = 0; }                        // point-matched placement: not supported, placed at the origin
    let a = 1, b = 0, c = 0, d = 1;
    const f2 = q => v.getInt16(q) / 16384;
    if (f & 8) { a = d = f2(p); p += 2; }
    else if (f & 0x40) { a = f2(p); d = f2(p + 2); p += 4; }
    else if (f & 0x80) { a = f2(p); b = f2(p + 2); c = f2(p + 4); d = f2(p + 6); p += 8; }
    for (const ct of contours(g, depth + 1))
      out.push(ct.map(q => ({ x: a * q.x + c * q.y + dx, y: b * q.x + d * q.y + dy, on: q.on })));
    more = (f & 0x20) !== 0;
  }
  return out;
}

// a quadratic contour (implied on-curve points between two off-curve ones) as M / L / Q / Z commands
function quads(c, map) {
  if (!c.length) return [];
  const pts = c.map(q => ({ ...q }));
  let start = pts.findIndex(q => q.on);
  if (start < 0) {                                           // all off-curve: start at a midpoint
    const a = pts[0], b = pts[1 % pts.length];
    pts.unshift({ x: (a.x + b.x) / 2, y: (a.y + b.y) / 2, on: true });
    start = 0;
  }
  const ring = [...pts.slice(start), ...pts.slice(0, start)];
  const P = q => map(q), cmds = [];
  const [mx, my] = P(ring[0]);
  cmds.push({ type: 'M', x: mx, y: my });
  let ctrl = null;
  for (let i = 1; i <= ring.length; i++) {
    const q = ring[i % ring.length];
    if (q.on) {
      const [x, y] = P(q);
      if (ctrl) { cmds.push({ type: 'Q', x1: ctrl[0], y1: ctrl[1], x, y }); ctrl = null; }
      else cmds.push({ type: 'L', x, y });
    } else if (ctrl) {
      const [cx, cy] = P(q), x = (ctrl[0] + cx) / 2, y = (ctrl[1] + cy) / 2;
      cmds.push({ type: 'Q', x1: ctrl[0], y1: ctrl[1], x, y });
      ctrl = [cx, cy];
    } else ctrl = P(q);
  }
  cmds.push({ type: 'Z' });
  return cmds;
}
