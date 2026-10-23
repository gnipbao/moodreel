// The page contract the renderer drives (render/render.mjs):
//   window.DUR = seconds;  window.render = t => draw;  window.READY = true once fonts and images are ready
// stage() sets it up around a 2D canvas sized to the viewport, and draws in design units: a page written for
// 1920 x 1080 renders at any --size of the same aspect.
//
//   import { stage } from './kit/stage.js';
//   stage({ width: 1920, height: 1080, duration: 12, fonts: ['600 64px Archivo'], images: { logo: 'logo.png' },
//           draw: (g, t, assets) => { ... } });

export function stage({ width = 1920, height = 1080, duration, draw, fonts = [], images = {}, background = '#000' }) {
  const W = innerWidth, H = innerHeight;
  const canvas = document.createElement('canvas');
  canvas.width = W;
  canvas.height = H;
  Object.assign(canvas.style, { display: 'block' });
  Object.assign(document.body.style, { margin: 0, background, overflow: 'hidden' });
  document.body.appendChild(canvas);
  const g = canvas.getContext('2d');
  const k = Math.min(W / width, H / height);
  const assets = {};
  window.DUR = duration;
  window.render = t => {
    g.setTransform(1, 0, 0, 1, 0, 0);
    g.globalAlpha = 1;
    g.globalCompositeOperation = 'source-over';
    g.fillStyle = background;
    g.fillRect(0, 0, W, H);
    g.setTransform(k, 0, 0, k, (W - width * k) / 2, (H - height * k) / 2);
    draw(g, t, assets);
  };
  const loads = [
    ...fonts.map(f => document.fonts.load(f)),
    ...Object.entries(images).map(([name, src]) => new Promise((ok, fail) => {
      const im = new Image();
      im.onload = () => { assets[name] = im; ok(); };
      im.onerror = () => fail(new Error(`image ${src} did not load`));
      im.src = src;
    })),
  ];
  Promise.all(loads).then(() => document.fonts.ready).then(() => { window.render(0); window.READY = true; });
  return { canvas, g, width, height };
}

// optional: every on-screen text at time t, for the reading-time check ([{id, text, x0, y0, x1, y1}])
export function texts(fn) {
  window.TEXTS = fn;
}
