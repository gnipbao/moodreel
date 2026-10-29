// Ink Chronicle: the grounds (STYLE §2). Paper, warm and smooth, its edges a little darker; night, near-black and warm at
// the middle; the corner label that keeps a film's index (place · year over a distance); a flash.
import { SIZE, INK } from './tokens.js';
import { clamp, hash } from './anim.js';
import { SONG, MONO, font } from './faces.js';

const [W, H] = SIZE;
export function canvas(w = W, h = H) { const c = document.createElement('canvas'); c.width = w; c.height = h; return [c, c.getContext('2d')]; }
export function fill(g, col) { g.fillStyle = col; g.fillRect(0, 0, W, H); }
export function vignette(g, a = 0.2, col = '0,0,0', inner = 0.3) {
  const r = g.createRadialGradient(W / 2, H / 2, H * inner, W / 2, H / 2, Math.hypot(W, H) / 2);
  r.addColorStop(0, `rgba(${col},0)`); r.addColorStop(1, `rgba(${col},${a})`);
  g.fillStyle = r; g.fillRect(0, 0, W, H);
}

// paper: a warm smooth ground, its corners a few levels darker and warmer (no fibres: the style's paper is clean)
export function paper(g, col = INK.paper, edge = 0.12) {
  fill(g, col);
  if (edge > 0) vignette(g, edge, '60,40,20', 0.35);
}
// night: near-black, warm at the middle and falling into shadow at the edges (the measured light: 16 levels at the
// centre, 8 at the corners), with a few still specks of dust
export function night(g, { col = '#090705', warm = 'rgba(32,27,19,0.5)', cx = 0.5, cy = 0.45, specks = 160 } = {}) {
  fill(g, col);
  const bg = g.createRadialGradient(cx * W, cy * H, 0, cx * W, cy * H, 0.65 * W); bg.addColorStop(0, warm); bg.addColorStop(1, 'rgba(0,0,0,0)');
  g.fillStyle = bg; g.fillRect(0, 0, W, H);
  if (specks) { g.fillStyle = '#d8ceb0'; for (let i = 0; i < specks; i++) { g.globalAlpha = 0.3 + 0.6 * hash(i, 414); const r = 1.4 + 2.2 * hash(i, 413) ** 3; g.fillRect(hash(i, 411) * W, hash(i, 412) * H, r, r); } g.globalAlpha = 1; }
}
// the corner label: where and when (the reference's top right, two lines, right-aligned)
export function label(g, line1, line2, col, a = 1) {
  if (a <= 0) return;
  g.save(); g.globalAlpha = a; g.fillStyle = col; g.textAlign = 'right';
  g.font = font(400, 19, SONG); g.fillText(line1, (W - 17), 70);
  if (line2) { g.font = `400 17px "${MONO}"`; g.fillText(line2, (W - 17), 98); }
  g.restore();
}
// a white flash over everything
export function flash(g, a, col = '#fff') { if (a <= 0) return; g.save(); g.globalAlpha = clamp(a); fill(g, col); g.restore(); }
