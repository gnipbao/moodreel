// Signal Plates idiom: the prompt field. A plea typed as tokens into an input line, as it is sung: each token's
// letters appear between its start and end, the token being typed in signal with an underline and the caret after it,
// the ones before in bone, and under the newest one a tiny distribution of the alternatives the machine weighed
// (the chosen one in signal): its rows slide in top to bottom, `stagger` apart, with the style's entrance, and leave
// with its exit when the next token starts. The field itself pops in at `appear`. Drawn in 2D (on a plate's type
// layer, or straight on the stage).
//
//   prompt(q, t, { x: 150, y: 560, w: 1100, tokens: [
//     { text: 'save', t0: 1.0, t1: 1.2, alts: [['save', 0.71], ['close', 0.12], ['lose', 0.06]] }, ...] });
//
// Token times come from the song's data (kit/music.js span()/sung()), never read off frames.
import { PALETTE, SIZE } from './tokens.js';
import { MOTION } from './motion.js';
import { tween } from './core.js';
import { machine, font } from './signal.js';

// the style's entrance (every other one overshooting) and exit
const inn = (t, at, k) => tween(t, at, MOTION.enter.duration, k % 2 ? MOTION.enter.ease : MOTION.enter.overshoot_ease ?? MOTION.enter.ease);
const out = (t, at) => tween(t, at, MOTION.exit.duration, MOTION.exit.ease);

const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));

export function prompt(g, t, { x, y, w, tokens, px = Math.round(0.05 * SIZE[1]), chevron = '›', label = null,
  meta = null, caret = true, appear = 0, panel = 0.9, stagger = MOTION.stagger?.interval ?? 0.234 } = {}) {
  const pad = px * 0.55, h = px * 1.9, base = y + h * 0.5 + px * 0.36;
  const shown = inn(t, appear, 0);
  if (shown <= 0) return null;
  g.save();
  g.globalAlpha *= clamp(shown * 1.5);
  g.translate(x, y + h / 2); g.scale(0.94 + 0.06 * shown, 0.94 + 0.06 * shown); g.translate(-x, -y - h / 2);   // it pops in
  // the field: a panel one step lighter, a graphite hairline
  g.fillStyle = PALETTE.panel;
  g.globalAlpha *= panel;
  g.fillRect(x, y, w, h);
  g.globalAlpha /= panel;
  g.strokeStyle = PALETTE.graphite;
  g.lineWidth = 1;
  g.strokeRect(x + 0.5, y + 0.5, w - 1, h - 1);
  font(g, machine(px, 500));
  g.textBaseline = 'alphabetic';
  g.fillStyle = PALETTE.ash;
  g.fillText(chevron, x + pad, base);
  let cx = x + pad + g.measureText(chevron + ' ').width;
  const space = g.measureText(' ').width;
  let now = null, end = cx;
  const xs = [];
  for (const tok of tokens) {
    xs.push(cx);
    if (t < tok.t0) break;
    const n = [...tok.text].length, k = Math.min(n, Math.floor(n * clamp((t - tok.t0) / Math.max(1e-3, tok.t1 - tok.t0))) + 1);
    const part = [...tok.text].slice(0, k).join('');
    const typing = t < (tok.hold ?? tok.t1 + 0.35);
    g.fillStyle = typing ? PALETTE.signal : PALETTE.bone;
    g.fillText(part, cx, base);
    const tw = g.measureText(part).width;
    if (typing) { g.fillRect(cx, base + px * 0.22, tw, Math.max(2, px * 0.05)); now = tok; }
    cx += tw;
    end = cx;
    cx += space;
  }
  if (caret) {                                     // a block caret after the last letter, on while typing
    g.fillStyle = now ? PALETTE.signal : PALETTE.ash;
    g.globalAlpha *= now ? 1 : 0.6;
    g.fillRect(end + space * 0.25, base - px * 0.78, px * 0.5, px * 0.95);
  }
  g.restore();
  // the distribution under each token while it is the newest: bars as wide as their probability, tiny mono labels
  const sp = Math.max(11, Math.round(px * 0.26)), bw = px * 2.6;
  tokens.forEach((tok, k) => {
    const next = tokens[k + 1], gone = next ? out(t, next.t0) : 0;
    if (!tok.alts?.length || t < tok.t0 || xs[k] === undefined || gone >= 1) return;
    g.save();
    g.globalAlpha *= clamp(shown * 1.5) * (1 - gone);
    g.translate(0, gone * sp * 2);                          // leaving: it sinks and fades, faster and faster
    font(g, machine(sp, 400));
    tok.alts.slice(0, 4).forEach(([word, p], i) => {
      const a = inn(t, tok.t0 + i * stagger, i);           // each row slides in, top to bottom
      if (a <= 0) return;
      const yy = y + h + sp * 1.0 + i * sp * 1.45, chosen = word === tok.text;
      g.save();
      g.globalAlpha *= clamp(a * 1.5);
      g.translate(xs[k] - (1 - a) * 40, yy);
      g.fillStyle = chosen ? PALETTE.signal : PALETTE.graphite;
      g.fillRect(0, 0, Math.max(1, bw * p), sp * 0.62);
      g.fillStyle = chosen ? PALETTE.bone : PALETTE.ash;
      g.fillText(`${word} ${p.toFixed(2).replace(/^0/, '')}`, bw + sp * 0.6, sp * 0.62);
      g.restore();
    });
    g.restore();
  });
  // a label above the field and a meta line below it, tiny mono annotations
  g.save();
  g.globalAlpha *= shown;
  font(g, machine(sp, 500));
  if (label) { g.fillStyle = PALETTE.ash; g.fillText(label, x, y - sp * 0.8); }
  if (meta) { g.fillStyle = PALETTE.graphite; g.fillText(meta, x + w - g.measureText(meta).width, y - sp * 0.8); }
  g.restore();
  return { x, y, w, h, caret: end };
}
