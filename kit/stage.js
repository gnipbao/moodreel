// The page contract the renderer drives (render/render.mjs):
//   window.DUR = seconds;  window.render = t => draw;  window.READY = true once fonts and images are ready
// stage() sets it up around a 2D canvas sized to the viewport, and draws in design units: a page written for
// 1920 x 1080 renders at any --size of the same aspect. Inside a host page (a HyperFrames composition from
// `moodreel export`), it fills the element #moodreel-stage instead and leaves the page's own styles alone.
//
//   import { stage } from './kit/stage.js';
//   stage({ width: 1920, height: 1080, duration: 12, fonts: ['600 64px Archivo'], images: { logo: 'logo.png' },
//           draw: (g, t, assets) => { ... }, finish: (g, t, src, assets) => { ... } });
//
// Font files: faces: { 'Archivo-1000-900': 'fonts/Archivo-w1000-900.ttf', 'Plex-500': { src: '...', featureSettings: '"lnum" 1' } }
// registers each file under its family name before the first frame (then `900 80px "Archivo-1000-900"` draws with it).
// prepare: async assets => { ... } runs once they are in, before the first frame: build what measures text or needs images.
//
// Motion blur: with window.MOTION_BLUR = { samples, shutter, fps } (render.mjs --samples N --shutter s), every frame is
// the average of `samples` sub-frames spread evenly over `shutter` of the frame's time, centred on t, so fast motion
// leaves a streak instead of jumping. draw() runs once per sub-frame and must depend on t alone. finish(), when given,
// runs once on the finished (averaged) frame, with `src` that frame's canvas: put there whatever must not be averaged
// or should be computed once (grain, vignette, flashes, bloom read from the frame). Without blur it runs all the same.

export function stage({ width = 1920, height = 1080, duration, draw, finish = null, fonts = [], faces = {}, images = {},
  prepare = null, background = '#000' }) {
  const mount = document.getElementById('moodreel-stage');
  const W = mount ? mount.clientWidth || width : innerWidth, H = mount ? mount.clientHeight || height : innerHeight;
  const canvas = document.createElement('canvas');
  canvas.width = W;
  canvas.height = H;
  Object.assign(canvas.style, { display: 'block', width: '100%', height: '100%' });
  if (!mount) Object.assign(document.body.style, { margin: 0, background, overflow: 'hidden' });
  (mount || document.body).appendChild(canvas);
  const g = canvas.getContext('2d');
  const k = Math.min(W / width, H / height), ox = (W - width * k) / 2, oy = (H - height * k) / 2;
  const assets = {};
  const offscreen = () => { const c = document.createElement('canvas'); c.width = W; c.height = H; return [c, c.getContext('2d')]; };
  const [FR, fr] = finish ? offscreen() : [canvas, g];                     // the frame drawn, before finish
  let sub = null;                                                           // [canvas, ctx] for sub-frames
  const blank = (c, cv) => {
    c.setTransform(1, 0, 0, 1, 0, 0); c.globalAlpha = 1; c.globalCompositeOperation = 'source-over'; c.filter = 'none';
    c.fillStyle = background; c.fillRect(0, 0, cv.width, cv.height);
    c.setTransform(k, 0, 0, k, ox, oy);
  };
  window.DUR = duration;
  window.render = t => {
    const mb = window.MOTION_BLUR, n = Math.max(1, Math.round(mb?.samples ?? 1));
    if (n === 1) { blank(fr, FR); draw(fr, t, assets); }
    else {
      sub = sub || offscreen();
      const [SB, sb] = sub, span = (mb.shutter ?? 0.2) / (mb.fps || 30);
      fr.setTransform(1, 0, 0, 1, 0, 0); fr.globalCompositeOperation = 'source-over'; fr.filter = 'none';
      for (let i = 0; i < n; i++) {                                         // a running average: sub-frame i weighs 1/(i+1)
        blank(sb, SB);
        draw(sb, t + ((i + 0.5) / n - 0.5) * span, assets);
        fr.setTransform(1, 0, 0, 1, 0, 0); fr.globalAlpha = 1 / (i + 1);
        fr.drawImage(SB, 0, 0);
      }
      fr.globalAlpha = 1;
    }
    if (!finish) return;
    g.setTransform(1, 0, 0, 1, 0, 0); g.globalAlpha = 1; g.globalCompositeOperation = 'source-over'; g.filter = 'none';
    g.drawImage(FR, 0, 0);
    g.setTransform(k, 0, 0, k, ox, oy);
    finish(g, t, FR, assets);
  };
  const loads = [
    ...Object.entries(faces).map(([family, f]) => {
      const { src, ...desc } = typeof f === 'string' ? { src: f } : f;
      return new FontFace(family, `url(${JSON.stringify(src)})`, desc).load().then(ff => document.fonts.add(ff));
    }),
    ...fonts.map(f => document.fonts.load(f)),
    ...Object.entries(images).map(([name, src]) => new Promise((ok, fail) => {
      const im = new Image();
      im.onload = () => { assets[name] = im; ok(); };
      im.onerror = () => fail(new Error(`image ${src} did not load`));
      im.src = src;
    })),
  ];
  Promise.all(loads).then(() => document.fonts.ready).then(() => prepare?.(assets))
    .then(() => { window.render(0); window.READY = true; });
  return { canvas, g, width, height };
}

// optional: every on-screen text at time t, for the reading-time check ([{id, text, x0, y0, x1, y1}])
export function texts(fn) {
  window.TEXTS = fn;
}
