// Ink Chronicle: the type's faces. Three classes, four voices (STYLE §4): a heavy Song for blows, titles and lines that
// address the viewer, the same Song light for the quiet voice, an upright Kai for quotations and reflection, a mono for
// numbers. These are the defaults (OFL, kit/fonts); a film may load other open faces of the same classes.
export const SONG = 'InkSong', KAI = 'InkKai', MONO = 'InkMono';
export const font = (w, px, fam = SONG) => `${w} ${px}px "${fam}"`;

// load the default faces from kit/fonts (once, before drawing: stage({ prepare: () => loadFaces() }))
export async function loadFaces(base = new URL('./fonts/', import.meta.url)) {
  const faces = [[SONG, 'NotoSerifSC-wght.ttf', '200 900'], [KAI, 'LXGWWenKai-Regular.ttf', '300 400'], [KAI, 'LXGWWenKai-Medium.ttf', '500 900'],
    [MONO, 'IBMPlexMono-Regular.ttf', '100 400'], [MONO, 'IBMPlexMono-Medium.ttf', '500 900']];
  const loaded = await Promise.all(faces.map(([n, f, w]) => new FontFace(n, `url(${new URL(f, base)})`, { weight: w }).load()));
  for (const f of loaded) document.fonts.add(f);
}
