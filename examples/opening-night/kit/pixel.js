// Pixel art: an indexed framebuffer at a low resolution, shown through a palette (index -> colour) and scaled up by
// whole pixels with no smoothing. A palette change recolours the whole picture in one frame (fades, colour depth as
// time, a palette swap as a cut); light steps along ramps of indices; gradients are ordered (Bayer) dither. The same
// names as what `moodreel measure` reads from pixel references (texture.json `pixel`: scale, palette size, dither).

export const BAYER4 = [0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5].map(v => (v + 0.5) / 16);

export const hex = s => [1, 3, 5].map(i => parseInt(s.slice(i, i + 2), 16));

// the palette index nearest a colour (in RGB, weighted toward green as the eye is)
export function nearest(palette, rgb) {
  let best = 0, bd = Infinity;
  palette.forEach((p, i) => {
    const c = typeof p === 'string' ? hex(p) : p;
    const d = 2 * (c[0] - rgb[0]) ** 2 + 4 * (c[1] - rgb[1]) ** 2 + 3 * (c[2] - rgb[2]) ** 2;
    if (d < bd) { bd = d; best = i; }
  });
  return best;
}

// a table sending each index to the nearest of `keep` (indices): a reduced colour depth, as a lookup
export function reduce(palette, keep) {
  const sub = keep.map(i => palette[i]);
  return palette.map(p => keep[nearest(sub, typeof p === 'string' ? hex(p) : p)]);
}

// a table moving each index one step along its ramp (ramps: lists of indices, dark to light): light = +1, dark = -1
export function stepTable(n, ramps, by = 1) {
  const table = [...Array(n).keys()];
  for (const r of ramps) r.forEach((i, k) => { table[i] = r[Math.max(0, Math.min(r.length - 1, k + by))]; });
  return table;
}

export function pixels(w, h, palette) {
  const fb = new Uint8Array(w * h);
  const rgb = palette.map(p => (typeof p === 'string' ? hex(p) : p));
  const canvas = document.createElement('canvas');
  canvas.width = w;
  canvas.height = h;
  const q = canvas.getContext('2d'), img = q.createImageData(w, h);
  const P = {
    w, h, fb, palette: rgb,
    clear(i = 0) { fb.fill(i); return P; },
    put(x, y, i) {
      x = Math.floor(x); y = Math.floor(y);
      if (x >= 0 && y >= 0 && x < w && y < h && i != null) fb[y * w + x] = i;
    },
    get: (x, y) => fb[Math.floor(y) * w + Math.floor(x)],
    rect(x, y, rw, rh, i) {
      for (let yy = Math.max(0, Math.floor(y)); yy < Math.min(h, Math.floor(y + rh)); yy++)
        fb.fill(i, yy * w + Math.max(0, Math.floor(x)), yy * w + Math.min(w, Math.floor(x + rw)));
    },
    line(x0, y0, x1, y1, i) {                            // Bresenham: one pixel wide, no anti-aliasing
      x0 = Math.round(x0); y0 = Math.round(y0); x1 = Math.round(x1); y1 = Math.round(y1);
      const dx = Math.abs(x1 - x0), dy = -Math.abs(y1 - y0), sx = x0 < x1 ? 1 : -1, sy = y0 < y1 ? 1 : -1;
      let err = dx + dy;
      for (;;) {
        P.put(x0, y0, i);
        if (x0 === x1 && y0 === y1) break;
        const e2 = 2 * err;
        if (e2 >= dy) { err += dy; x0 += sx; }
        if (e2 <= dx) { err += dx; y0 += sy; }
      }
    },
    disc(cx, cy, r, i) {
      for (let y = -r; y <= r; y++) for (let x = -r; x <= r; x++) if (x * x + y * y <= r * r + r * 0.8) P.put(cx + x, cy + y, i);
    },
    // a share u (0-1) of index b over index a, as an ordered dither; u may be a function of (x, y): a gradient
    shade(x, y, rw, rh, a, b, u) {
      for (let yy = Math.floor(y); yy < Math.floor(y + rh); yy++)
        for (let xx = Math.floor(x); xx < Math.floor(x + rw); xx++) {
          const v = typeof u === 'function' ? u(xx, yy) : u;
          P.put(xx, yy, v > BAYER4[(yy & 3) * 4 + (xx & 3)] ? b : a);
        }
    },
    // a sprite from rows of characters: legend maps each character to an index ('.' and ' ' are see-through)
    sprite(rows, legend, x, y, { flip = false } = {}) {
      rows.forEach((row, j) => [...row].forEach((ch, k) => {
        if (ch !== '.' && ch !== ' ' && ch in legend) P.put(x + (flip ? row.length - 1 - k : k), y + j, legend[ch]);
      }));
    },
    // a one-pixel outline in index i around everything that isn't the background index
    outline(i, background = 0) {
      const src = fb.slice();
      for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
        if (src[y * w + x] !== background) continue;
        if ((x > 0 && src[y * w + x - 1] !== background) || (x < w - 1 && src[y * w + x + 1] !== background)
          || (y > 0 && src[(y - 1) * w + x] !== background) || (y < h - 1 && src[(y + 1) * w + x] !== background)) fb[y * w + x] = i;
      }
    },
    // draw the framebuffer onto g at (x, y), each pixel `scale` px square; `table` remaps indices first (light,
    // colour depth), `colours` overrides the palette (a fade or a swap of the whole picture)
    present(g, { x = 0, y = 0, scale = 1, table = null, colours = rgb } = {}) {
      const d = img.data;
      for (let k = 0; k < fb.length; k++) {
        const c = colours[table ? table[fb[k]] : fb[k]];
        d[4 * k] = c[0]; d[4 * k + 1] = c[1]; d[4 * k + 2] = c[2]; d[4 * k + 3] = 255;
      }
      q.putImageData(img, 0, 0);
      g.save();
      g.imageSmoothingEnabled = false;
      g.drawImage(canvas, Math.round(x), Math.round(y), w * scale, h * scale);
      g.restore();
    },
  };
  return P;
}

// a camera or a layer moves by whole pixels (each parallax layer rounds its own offset)
export const snap = v => Math.round(v);

// An original 5x7 pixel font (capitals, digits, common punctuation), variable width: each glyph is as wide as its
// ink, plus one pixel between glyphs. Rows top to bottom, '#' = ink.
const GLYPHS = {
  A: '.###./#...#/#...#/#####/#...#/#...#/#...#', B: '####./#...#/#...#/####./#...#/#...#/####.',
  C: '.###./#...#/#..../#..../#..../#...#/.###.', D: '####./#...#/#...#/#...#/#...#/#...#/####.',
  E: '#####/#..../#..../####./#..../#..../#####', F: '#####/#..../#..../####./#..../#..../#....',
  G: '.###./#...#/#..../#.###/#...#/#...#/.####', H: '#...#/#...#/#...#/#####/#...#/#...#/#...#',
  I: '###/.#./.#./.#./.#./.#./###', J: '..###/...#./...#./...#./#..#./#..#./.##..',
  K: '#...#/#..#./#.#../##.../#.#../#..#./#...#', L: '#..../#..../#..../#..../#..../#..../#####',
  M: '#...#/##.##/#.#.#/#.#.#/#...#/#...#/#...#', N: '#...#/##..#/#.#.#/#..##/#...#/#...#/#...#',
  O: '.###./#...#/#...#/#...#/#...#/#...#/.###.', P: '####./#...#/#...#/####./#..../#..../#....',
  Q: '.###./#...#/#...#/#...#/#.#.#/#..#./.##.#', R: '####./#...#/#...#/####./#.#../#..#./#...#',
  S: '.####/#..../#..../.###./....#/....#/####.', T: '#####/..#../..#../..#../..#../..#../..#..',
  U: '#...#/#...#/#...#/#...#/#...#/#...#/.###.', V: '#...#/#...#/#...#/#...#/#...#/.#.#./..#..',
  W: '#...#/#...#/#...#/#.#.#/#.#.#/##.##/#...#', X: '#...#/#...#/.#.#./..#../.#.#./#...#/#...#',
  Y: '#...#/#...#/.#.#./..#../..#../..#../..#..', Z: '#####/....#/...#./..#../.#.../#..../#####',
  0: '.###./#...#/#..##/#.#.#/##..#/#...#/.###.', 1: '.#./##./.#./.#./.#./.#./###',
  2: '.###./#...#/....#/...#./..#../.#.../#####', 3: '####./....#/....#/.###./....#/....#/####.',
  4: '#..#./#..#./#..#./#####/...#./...#./...#.', 5: '#####/#..../####./....#/....#/#...#/.###.',
  6: '.###./#..../#..../####./#...#/#...#/.###.', 7: '#####/....#/...#./..#../.#.../.#.../.#...',
  8: '.###./#...#/#...#/.###./#...#/#...#/.###.', 9: '.###./#...#/#...#/.####/....#/....#/.###.',
  '.': './././././#', ',': '../../../../../.#/#.', '!': '#/#/#/#/#/./#', '?': '.###./#...#/....#/...#./..#../...../..#..',
  "'": '#/#/./././././.', '-': '..../..../..../####/..../..../....', ':': './#/./././#/.', ' ': '../../../../../../..',
};
const FONT = Object.fromEntries(Object.entries(GLYPHS).map(([k, v]) => [k, v.split('/')]));

// how wide a line of text is, in native pixels
export const textWidth = s => [...s.toUpperCase()].reduce((w, c) => w + (FONT[c] || FONT[' '])[0].length + 1, -1);

// a line of text in the 5x7 font, in index i (and an 8-neighbour outline in `outline`, for titles over pictures)
export function text(P, s, x, y, i, { outline = null } = {}) {
  const draw = (ox, oy, k) => {
    let cx = x;
    for (const c of s.toUpperCase()) {
      const g = FONT[c] || FONT[' '];
      g.forEach((row, r) => [...row].forEach((on, q) => { if (on === '#') P.put(cx + q + ox, y + r + oy, k); }));
      cx += g[0].length + 1;
    }
  };
  if (outline != null) for (const [ox, oy] of [[-1, -1], [0, -1], [1, -1], [-1, 0], [1, 0], [-1, 1], [0, 1], [1, 1]]) draw(ox, oy, outline);
  draw(0, 0, i);
}
