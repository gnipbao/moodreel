// Type on a canvas: fitting, wrapping and per-glyph layout for staggered text.

// the largest size (px) at which `text` fits `width`, between min and max
export function fit(g, text, font, width, { min = 8, max = 400 } = {}) {
  let lo = min, hi = max;
  while (hi - lo > 0.5) {
    const mid = (lo + hi) / 2;
    g.font = font.replace('{size}', `${mid}px`);
    if (g.measureText(text).width <= width) lo = mid;
    else hi = mid;
  }
  return Math.floor(lo);
}

// lines that fit `width`, breaking at spaces (and anywhere in CJK text)
export function wrap(g, text, width) {
  const cjk = /[　-鿿가-힯]/.test(text);
  const tokens = cjk ? [...text] : text.split(/(\s+)/);
  const lines = [];
  let line = '';
  for (const tok of tokens) {
    const next = line + tok;
    if (line && g.measureText(next.trimEnd()).width > width) {
      lines.push(line.trimEnd());
      line = tok.trimStart();
    } else line = next;
  }
  if (line.trim()) lines.push(line.trimEnd());
  return lines;
}

// glyph positions for text drawn centred at x (or from x when align is 'left'), for per-letter animation
export function glyphs(g, text, x, { align = 'center' } = {}) {
  const chars = [...text], widths = chars.map(c => g.measureText(c).width);
  let cx = align === 'center' ? x - widths.reduce((a, b) => a + b, 0) / 2 : x;
  let n = 0;
  return chars.map((c, i) => {
    const out = { char: c, x: cx + widths[i] / 2, width: widths[i], index: c.trim() ? n++ : -1 };
    cx += widths[i];
    return out;
  });
}
