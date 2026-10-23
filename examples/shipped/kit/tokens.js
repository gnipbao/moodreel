// Dark Keynote, filled in from styles/dark-keynote/STYLE.md §2-§4 for this film.
export const SIZE = [1920, 1080];
// §3: a cool neutral ladder (stage, three surfaces, three text greys) and one accent (lime here)
export const PALETTE = { ground: '#0B0D12', ink: '#E9EDF5', accent: '#B7F34A',
  surfaces: ['#141821', '#1B2030', '#232A3B'], text: ['#E9EDF5', '#A2ABBD', '#5F687B'], secondary: [] };
// §4: Inter for UI and headlines, Inter Tight 600 for the big number, a mono for labels (system faces here)
export const TYPE = { title: 0.26, body: 0.033, titleWeight: 600, bodyWeight: 500,
  display: '"Inter Tight", "Inter", system-ui, sans-serif', text: '"Inter", system-ui, sans-serif',
  mono: '"JetBrains Mono", "SF Mono", Menlo, monospace' };
// §2: a 48 px module with a hairline grid; generous negative space
export const LAYOUT = { module: 48, align: 'centre' };
// §2: no grain; a 50-55 % corner vignette, a radial lift at the upper centre, one cool glow off-centre
export const TEXTURE = { grain: 0, vignette: 0.5 };
