// first-save: a hero walks out at dusk and the game saves, on 16-bit Pixel RPG (styles/pixel-rpg). Everything is
// drawn into a 320 x 180 indexed framebuffer and shown x6 with no smoothing; night falls by palette steps, not alpha.
import { stage, texts } from './kit/stage.js';
import { tween } from './kit/core.js';
import { pixels, stepTable, snap, text, textWidth } from './kit/pixel.js';

const PALETTE = ['#10121c', '#1d2b53', '#29366f', '#3b5dc9', '#73a7e8', '#b7dbf2', '#f4f4f4', '#94b0c2', '#566c86',
  '#1f4d3a', '#38b764', '#a7f070', '#6b4226', '#c08a5a', '#f2c48d', '#c83a3a', '#ffcd75', '#ef7d57',
  // protected duplicates for the UI: no palette effect touches them, so the windows stay legible at night
  '#10121c', '#1d2b53', '#29366f', '#f4f4f4', '#94b0c2', '#ffcd75', '#f2c48d', '#c83a3a', '#6b4226'];
const [INK, NIGHT, DEEP, BLUE, SKY, PALE, WHITE, SILVER, SLATE, PINE, GREEN, LIME, BARK, TAN, SKIN, RED, GOLD] = PALETTE.keys();
const [U_INK, U_NIGHT, U_DEEP, U_WHITE, U_SILVER, U_GOLD, U_SKIN, U_RED, U_BARK] = [18, 19, 20, 21, 22, 23, 24, 25, 26];
// ramps from dark to light: night steps every scene colour down its ramp (the sky toward deep blue, not black)
const RAMPS = [[NIGHT, DEEP, BLUE, SKY, PALE], [INK, PINE, GREEN, LIME], [INK, BARK, TAN, SKIN], [SLATE, SILVER, WHITE],
  [INK, RED, 17, GOLD]];
const NIGHTFALL = [0, 1, 2].map(k => stepTable(PALETTE.length, RAMPS, -k));
const P = pixels(320, 180, PALETTE);

const HERO = [                                           // two walk frames, 12 x 20
  ['....4444....', '...444444...', '...4eeee4...', '...eeeeee...', '...e.ee.e...', '....eeee....', '..rrrrrrrr..',
    '.rrrrrrrrrr.', '.ee.rrrr.ee.', '.ee.rrrr.ee.', '....rrrr....', '....bbbb....', '...bb..bb...', '...bb..bb...',
    '..bb....bb..', '..bb....bb..', '.kk......kk.', '............', '............', '............'],
  ['....4444....', '...444444...', '...4eeee4...', '...eeeeee...', '...e.ee.e...', '....eeee....', '..rrrrrrrr..',
    '.rrrrrrrrrr.', '.ee.rrrr.ee.', '.ee.rrrr.ee.', '....rrrr....', '....bbbb....', '....bbbb....', '....bbbb....',
    '....bbbb....', '....bbbb....', '....kkkk....', '............', '............', '............'],
];
const HERO_INK = { 4: BARK, e: SKIN, r: RED, b: DEEP, k: INK };
const PORTRAIT = ['..444444..', '.44444444.', '4444444444', '4eeeeeeee4', 'ee.eeee.ee', 'ee.eeee.ee', 'eeeeeeeeee',
  '.eeekkeee.', '..eeeeee..', 'rrrrrrrrrr'];
const LINES = [{ text: 'THE ROAD STARTS HERE.', at: 1.0 }, { text: 'ONE STEP AT A TIME.', at: 2.3 }];
const CPS = 20, BOX_IN = 0.8, BOX_OUT = 6.2, NIGHT_AT = 6.4, STOP = 7.0, SAVED = 7.5;

const box = (x, y, w, h) => {                            // layered rounded border, dithered dark-blue fill
  P.rect(x + 1, y, w - 2, h, U_INK); P.rect(x, y + 1, w, h - 2, U_INK);
  P.rect(x + 1, y + 1, w - 2, h - 2, U_WHITE); P.rect(x + 2, y + 2, w - 4, h - 4, U_SILVER);
  P.shade(x + 3, y + 3, w - 6, h - 6, U_NIGHT, U_DEEP, 0.5);
};
const PORTRAIT_INK = { 4: U_BARK, e: U_SKIN, r: U_RED, k: U_INK };
const ridge = (seed, base, amp, scroll, i) => {          // a skyline of hills, repeating every 160 px
  for (let x = 0; x < 320; x++) {
    const u = (x + scroll) / 160 * Math.PI * 2 + seed;
    const top = Math.round(base - amp * (0.6 * Math.sin(u) + 0.4 * Math.sin(2.3 * u + seed)));
    P.rect(x, top, 1, 140 - top, i);
  }
};

texts(t => LINES.filter(l => t >= l.at + l.text.length / CPS && t < BOX_OUT)
  .map((l, k) => ({ id: `line${k}`, text: l.text, x0: 46 * 6, y0: (144 + 10 * k) * 6, x1: (46 + textWidth(l.text)) * 6, y1: (151 + 10 * k) * 6 }))
  .concat(t >= SAVED + 0.3 ? [{ id: 'saved', text: 'GAME SAVED.', x0: 108 * 6, y0: 8 * 6, x1: 212 * 6, y1: 15 * 6 }] : []));

stage({ width: 1920, height: 1080, duration: 10, background: '#10121c', draw: (g, t) => {
  const walking = t < STOP;
  const cam = snap(24 * Math.min(t, STOP));               // the camera on ones, integer pixels
  P.clear(SKY);
  P.shade(0, 0, 320, 100, DEEP, BLUE, (x, y) => Math.min(1, y / 70));        // a dithered sky
  P.shade(0, 70, 320, 40, BLUE, SKY, (x, y) => (y - 70) / 40);
  ridge(1.3, 92, 18, snap(cam * 0.25), SLATE);            // far mountains
  ridge(4.1, 112, 10, snap(cam * 0.5), PINE);             // near hills
  P.shade(0, 118, 320, 22, PINE, GREEN, (x, y) => (y - 112) / 16);
  P.rect(0, 128, 320, 52, BARK);                          // the road
  for (let x = -((cam) % 16); x < 320; x += 16) { P.rect(x, 128, 8, 2, TAN); P.rect(x + 8, 132, 6, 1, TAN); }
  for (let k = 0; k < 4; k++) {                           // trees on the ground layer, at the camera's speed
    const tx = ((k * 97 - cam) % 388 + 388) % 388 - 40;
    P.rect(tx + 6, 110, 4, 18, BARK); P.disc(tx + 8, 104, 9, PINE); P.disc(tx + 6, 101, 5, GREEN);
  }
  const frame = walking ? Math.floor(t * 8) % 2 : 1;      // walk at 8 fps; breath 1 px when standing
  const breath = walking ? 0 : Math.floor(t * 2) % 2;
  P.sprite(HERO[frame], HERO_INK, 100, 109 - breath);
  const level = t < NIGHT_AT ? 0 : Math.min(2, 1 + Math.floor((t - NIGHT_AT) / 0.25));  // a palette step fade to dusk
  if (level >= 2) for (let k = 0; k < 24; k++) P.put((k * 53) % 320, (k * 29) % 60, WHITE);   // stars come out
  // the dialog box: slides in over 0.3 s (ease-out, integer px), types its lines, slides out
  const inY = snap(180 - 48 * tween(t, BOX_IN, 0.3, 'power2.out')), outY = snap(48 * tween(t, BOX_OUT, 0.3, 'power2.in'));
  const by = inY + outY;
  if (t >= BOX_IN && by < 180) {
    box(4, by, 312, 44);
    P.rect(9, by + 6, 34, 34, U_INK); P.shade(10, by + 7, 32, 32, U_DEEP, U_SILVER, 0.25);
    P.sprite(PORTRAIT.flatMap(r => [r, r]).map(r => r.replace(/./g, c => c + c + c)), PORTRAIT_INK, 11, by + 7);
    LINES.forEach((l, k) => {
      const shown = Math.max(0, Math.floor((t - l.at) * CPS));
      if (shown > 0) text(P, l.text.slice(0, shown), 46, by + 12 + 10 * k, U_WHITE);
    });
  }
  const sy = snap(-20 + 24 * tween(t, SAVED, 0.3, 'power2.out'));   // the system window: a thin top box
  if (t >= SAVED) { box(100, sy, 120, 18); text(P, 'GAME SAVED.', 108, sy + 6, U_GOLD); }
  P.present(g, { scale: 6, table: level ? NIGHTFALL[level] : null });
}});
