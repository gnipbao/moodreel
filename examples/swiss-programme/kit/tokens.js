// Swiss Motion Graphics, filled in from styles/swiss-motion/STYLE.md §2-§4 for this film.
export const SIZE = [1920, 1080];
// §3: paper, ink, greys and one signal colour (here red)
export const PALETTE = { ground: '#EAE9E5', ink: '#111111', grid: '#C9C8C4', note: '#8C8B87', accent: '#E30613', secondary: [] };
// §4: one neo-grotesque family, several weights (a system face here; an OFL face like Archivo in a published film)
export const TYPE = { title: 0.09, body: 0.024, titleWeight: 700, bodyWeight: 500,
  display: '"Helvetica Neue", Helvetica, Arial, sans-serif', text: '"Helvetica Neue", Helvetica, Arial, sans-serif' };
// §2: 12 columns, ~96 px side margins, 24 px gutters, 24 px baseline
export const LAYOUT = { margin: 96, columns: 12, gutter: 24, baseline: 24, align: 'left' };
// §2: no gradients, shadows, particles or grain
export const TEXTURE = { grain: 0, vignette: 0 };
