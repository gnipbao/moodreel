// A page in perspective, and a lens focused on one line of it. The re-dressed prompt is a page (heading above, card
// below) seen at an angle: drawn flat on a canvas, then laid on the screen through a homography, tile by tile; the
// card goes soft below the line in focus through a gradient mask, the soft and sharp copies added, not stacked.
//
//   import { quadMap, onPlane, focusBelow } from './kit/plane.js';
//   const P = quadMap([[390, 426], [2230, 483], [2138, 1251], [330, 1000]]);   // the card's corners on screen
//   const at = (x, y) => P((x - px) / cw, (y - py) / ch);                      // page px -> screen
//   onPlane(sharpCtx, pageCanvas, at);
//   focusBelow(q, sharpCanvas, softCanvas, { origin: [450, 590], slope: 0.049, from: 50, to: 250 });
import { SIZE } from './tokens.js';

const [W, H] = SIZE;

// the unit square onto a quad (top-left, top-right, bottom-right, bottom-left): P(u, v) -> [x, y]; P.inv(x, y) -> [u, v]
export function quadMap([[x0, y0], [x1, y1], [x2, y2], [x3, y3]]) {
  const dx1 = x1 - x2, dx2 = x3 - x2, dx3 = x0 - x1 + x2 - x3, dy1 = y1 - y2, dy2 = y3 - y2, dy3 = y0 - y1 + y2 - y3;
  const den = dx1 * dy2 - dx2 * dy1, g = (dx3 * dy2 - dx2 * dy3) / den, h = (dx1 * dy3 - dx3 * dy1) / den;
  const a = x1 - x0 + g * x1, b = x3 - x0 + h * x3, d = y1 - y0 + g * y1, e = y3 - y0 + h * y3;
  const P = (u, v) => { const w = g * u + h * v + 1; return [(a * u + b * v + x0) / w, (d * u + e * v + y0) / w]; };
  const A = [[a, b, x0], [d, e, y0], [g, h, 1]];
  const det = A[0][0] * (A[1][1] * A[2][2] - A[1][2] * A[2][1]) - A[0][1] * (A[1][0] * A[2][2] - A[1][2] * A[2][0])
    + A[0][2] * (A[1][0] * A[2][1] - A[1][1] * A[2][0]);
  const I = [[A[1][1] * A[2][2] - A[1][2] * A[2][1], A[0][2] * A[2][1] - A[0][1] * A[2][2], A[0][1] * A[1][2] - A[0][2] * A[1][1]],
    [A[1][2] * A[2][0] - A[1][0] * A[2][2], A[0][0] * A[2][2] - A[0][2] * A[2][0], A[0][2] * A[1][0] - A[0][0] * A[1][2]],
    [A[1][0] * A[2][1] - A[1][1] * A[2][0], A[0][1] * A[2][0] - A[0][0] * A[2][1], A[0][0] * A[1][1] - A[0][1] * A[1][0]]]
    .map(r => r.map(v => v / det));
  P.inv = (x, y) => {
    const w = I[2][0] * x + I[2][1] * y + I[2][2];
    return [(I[0][0] * x + I[0][1] * y + I[0][2]) / w, (I[1][0] * x + I[1][1] * y + I[1][2]) / w];
  };
  return P;
}

// a canvas laid on a plane: cut into tiles, each mapped by its own three corners, overlapping 3 px (without it the
// ground shows through the seams as a row of specks along the perspective). at(x, y): canvas px -> screen
export function onPlane(q, img, at, nx = 28, ny = 12) {
  const sw = img.width / nx, sh = img.height / ny;
  for (let j = 0; j < ny; j++) for (let i = 0; i < nx; i++) {
    const p = at(i * sw, j * sh), r = at((i + 1) * sw, j * sh), b = at(i * sw, (j + 1) * sh);
    const w = Math.min(sw + 3, img.width - i * sw), h = Math.min(sh + 3, img.height - j * sh);
    q.setTransform((r[0] - p[0]) / sw, (r[1] - p[1]) / sw, (b[0] - p[0]) / sh, (b[1] - p[1]) / sh, p[0], p[1]);
    q.drawImage(img, i * sw, j * sh, w, h, 0, 0, w, h);
  }
  q.setTransform(1, 0, 0, 1, 0, 0);
}

// a lens focused on a line: sharp down to `from` px below it, soft by `to` px. sharp holds the page as laid on screen;
// soft is a spare canvas the size of the frame. The two are added on soft (their weights sum to one), then soft is
// laid on q; drawn one over the other, the ground would show through the band where both are partly transparent
export function focusBelow(q, sharp, soft, { origin = [450, 590], slope = 0.049, from = 50, to = 250, blur = 14 } = {}) {
  const sq = sharp.getContext('2d'), so = soft.getContext('2d');
  so.clearRect(0, 0, W, H); so.filter = `blur(${blur}px)`; so.drawImage(sharp, 0, 0); so.filter = 'none';
  const band = g => {
    g.translate(origin[0], origin[1]); g.rotate(Math.atan(slope));
    const m = g.createLinearGradient(0, from, 0, to);
    m.addColorStop(0, '#000'); m.addColorStop(1, 'rgba(0,0,0,0)');
    g.fillStyle = m; g.fillRect(-3000, -2000, 6000, 4000);
  };
  sq.save(); sq.globalCompositeOperation = 'destination-in'; band(sq); sq.restore();
  so.save(); so.globalCompositeOperation = 'destination-out'; band(so); so.restore();
  so.globalCompositeOperation = 'lighter'; so.drawImage(sharp, 0, 0); so.globalCompositeOperation = 'source-over';
  q.drawImage(soft, 0, 0);
}
