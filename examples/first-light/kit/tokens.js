// Risograph Print, filled in from styles/risograph/STYLE.md §2-§4 for this film.
export const SIZE = [1920, 1080];
// §3: two spot inks on warm paper; every other colour is an overprint (multiply) or a halftone tint
export const PALETTE = { ground: '#F4EEE2', ink: '#00838A', accent: '#FF7477', secondary: [] };
export const INKS = [{ name: 'teal', color: '#00838A', dx: 0, dy: 0, angle: 15 }, { name: 'orange', color: '#FF7477', dx: 4, dy: -3, angle: 75 }];
// §4: a heavy grotesque for titles (a system face here; an OFL face like Bricolage Grotesque in a published film)
export const TYPE = { title: 0.14, body: 0.04, titleWeight: 800, bodyWeight: 500,
  display: '"Avenir Next", "Helvetica Neue", Arial, sans-serif', text: '"Avenir Next", "Helvetica Neue", Arial, sans-serif' };
export const LAYOUT = { margin: 140, align: 'left' };
// §2: halftone ~7 px at 1080p in stepped tints, ink grain, paper mottle and fibres; no vignette
export const TEXTURE = { grain: 4, mottle: 1.5, vignette: 0, halftone: { period_px: 7, tints: [0.2, 0.4] } };
