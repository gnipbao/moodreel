// Pictogram Motion, filled in from styles/pictogram-motion/STYLE.md §2-§4 for this film.
export const SIZE = [1920, 1080];
// §3: one chapter, one hue in five tones (a coastal teal here), one cream and one ink for every hue
export const PALETTE = { ground: '#17606B', ink: '#F4EBDD', accent: null,
  tones: ['#0E3B43', '#17606B', '#1F8A96', '#6DBDC5', '#BFE3E6'], cream: '#F4EBDD', dark: '#1B1A22', secondary: [] };
// §4: a 900-weight grotesk title, a heavy second-language line, mono meta text (system faces here)
export const TYPE = { title: 0.213, body: 0.067, titleWeight: 900, bodyWeight: 600,
  display: '"Inter Tight", system-ui, sans-serif', text: '"PingFang SC", system-ui, sans-serif',
  mono: '"DM Mono", "SF Mono", Menlo, monospace' };
// §2: one square grid, cell = 1/6 of the frame height; one text column, one stage
export const LAYOUT = { cell: 180, margin: 140, align: 'left' };
export const TEXTURE = { grain: 0, vignette: 0 };
