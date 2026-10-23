// ASCII CRT, filled in from styles/ascii-crt/STYLE.md §2-§4 for this film.
export const SIZE = [1920, 1080];
// §3: one phosphor (P3 amber) in its own ramp on warm near-black glass; no second hue
export const PALETTE = { ground: '#140C05', ink: '#FFB000', accent: null, ramp: { dim: '#7A4300', normal: '#FFB000', bold: '#FFE3A0' },
  secondary: [] };
// §2: one monospace font on a 1:2 cell (VT323 in a published film; the system mono here), 80 columns at the base grid
export const TYPE = { cell: [24, 48], size: 40, title: 0.185, body: 0.037, titleWeight: 700, bodyWeight: 400,
  display: '"SF Mono", Menlo, Monaco, monospace', text: '"SF Mono", Menlo, Monaco, monospace' };
export const LAYOUT = { columns: 80, margin: 48, align: 'left' };
// §2: fine scanlines (every 6 px here), glow, no grain added, no RGB grille
export const TEXTURE = { grain: 0, vignette: 0, scanlines: { period_px: 6, strength: 0.35 }, glow: 14 };
