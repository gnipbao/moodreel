# Pictogram Tiles — Style Prompt

Pictogram Tiles · 图标瓷砖 · 1920×1080, 24 fps

> Flat vector cards in one family of teals: a full-bleed mosaic of circles and quarter-circles behind a big pale disc
> holding a capsule-limbed pictogram, a heavy caps word with its Chinese line beneath, and a mono counter. Each card
> pops together in under a second, the figure makes one small gesture, and a hard cut brings the next card.
> References (grammar only): Bauhaus and Swiss geometric tile patterns, public-signage pictograms, numbered
> step-by-step cards. Take the tile grammar, the one-colour value system and the card rhythm; never a reference's
> words, figure poses or layout literally.

## 1. Essence, and what it is not

1. **A mosaic ground.** The whole frame (margins 0 %, content 67 %) is a grid of tiles cut from circles: full
   discs, halves, quarters and squares (by eye), in three or four teal values.
2. **One family, many values.** Teals from deep to pale plus one cream; nothing warm, no saturated colour
   (saturated area 0 %).
3. **A disc as the stage.** A large pale disc (~63 % of frame height, centred ~73 % across) holds the subject, a
   pictogram built from capsules and a round head, front limbs cream, back limbs paler.
4. **Bilingual card type.** A heavy caps word, its CJK translation under it, a letter-spaced mono label top-left
   and a mono `NN / NN` counter top-right.
5. **Cards and cuts.** Equal-length cards (4 s each in the references) joined by hard cuts; motion is short pops,
   not camera.

**Not** Material/flat UI illustration (no shadows, no gradients, no brand primaries). **Not** an infographic (no
charts, no arrows, the figure acts rather than points). **Not** a Memphis pattern (no squiggles, no clashing hues,
the tiles are one hue family on a strict grid).

## 2. Materials & rendering

- **Flat vector only:** solid fills, crisp edges (sharpness 0.457), no grain (0.09: none), no vignette (0.00), no
  halftone, no texture. The measured "paper" mottle (1.68) is the tile mosaic's slow variation, not a surface
  (inferred): do not add paper.
- **Tile grid (by eye):** square cells of ~1/6 of the frame height, each cell one shape (disc, half, quarter or
  square) in one of the teal values, rotated in 90° steps; neighbours merge into larger organic forms. Generate it
  from a seed per card; keep it fixed for the card.
- **Layers:** mosaic → disc (`accent`) → pictogram (back limbs pale, body and front limbs cream) → type → micro UI.
  No overlaps other than the disc covering the mosaic and type sitting on it.
- **Pictogram:** a circle head and rounded rectangles (capsules) for torso and limbs, all with full round caps; no
  face, no hands, no outline.

## 3. Colour logic

- **One teal family** (Lab hue 206–221°) in ordered values: deep #0e3c45 (24 %) < ground #175f6b (34 %) < #217480 <
  mid #208995 (19 %) < disc #6dbcc3 (13.5 %) < pale #b5d2cd < cream #f2eadb (4.3 %).
- **The ground is mid-dark teal** (L* 36.6). The mosaic uses only deep, ground and mid values, so it stays a
  texture, never an image.
- **The disc is the one pale field** (accent role, 3.34:1 against the ground): one per card, only for the subject.
- **Cream is reserved** for the subject and the words (ink, contrast 6.09:1 on the ground). Nothing else is cream.
- **Depth by value, not colour:** the far limbs are pale #b5d2cd, the near ones cream.
- **Never:** a warm hue, a gradient, a shadow, pure white or black. A topic colour change would shift the whole
  family's hue together (inferred), never add a second hue.

Example palette (measured): #0e3c45 · #175f6b · #208995 · #6dbcc3 · #f2eadb.

## 4. Type & subtitles

- **Title:** a heavy grotesque sans in capitals (by eye: wide, flat-sided, closed apertures). Licence-free: Inter
  Display Black, Archivo ExtraBold, Work Sans ExtraBold (OFL). One short word, ink ~15.5 % of frame height (kit font
  size 0.226 H, weight 600 measured; draw it heavier by eye).
- **CJK line:** a bold CJK sans (Noto Sans SC Bold, OFL) at ~6.7 % H, directly under the title, flush with it.
- **Micro type:** a monospace (JetBrains Mono, IBM Plex Mono, OFL) at ~1.8–2.1 % H: a letter-spaced caps label
  top-left, a `01 / 03` counter top-right.
- **Positions (measured boxes):** label and counter on the 7.2 % top line; label and title at x ≈ 7.3–7.9 %;
  counter ends at 92.4 % (right margin ~7.6 %); title top at 36.5 % H, CJK line top at 57.2 % H.
- **Progress bars:** bottom-left, one short bar per card, the current one tall and cream, the others short and dim
  (by eye).
- **Subtitles** are the CJK line itself: one short phrase per card, never a running caption. Hold ≥ max(1.8 s,
  speech + 0.6 s) and ≥ CJK chars / 4.5 + other chars / 15 + 1.5 s; a card is long enough for both lines.

## 5. Motion quality

- **24 fps on ones.** Motion ~0.44 of the time; holds short (median 0.29 s, p75 0.66 s).
- **Moves are quick:** 0.31–0.50 s (median 0.42). No ease family was claimed; the curves read as fast-out (expo.out,
  power4.out) for arrivals and sine.inOut for gestures (unconfirmed guesses: 7 sine.inOut, 3 expo.out, 2 power4.out
  of 20). Use expo.out / power4.out for pops, sine.inOut for acting.
- **Disc pop:** scales from ~0.65–0.74 to 1 in ~0.3 s, a hair of overshoot (1–2 %).
- **Figure assembly:** head, torso and limbs arrive one after another from offset positions just after the disc (by
  eye, within ~0.6 s).
- **Title rise:** the word rises out of a slot (clip from its baseline), ~0.3–0.5 s, fast-out; the CJK line follows
  a beat later.
- **Gesture:** late in the card the figure makes one small move: a nod or limb lift of ~2 % of frame height over
  ~0.5 s (sine.inOut), or a small mark pops off upward (one reading back.in, 0.1 s).
- **Nothing exits within a card.** The cut removes everything at once.
- **Never moves:** the mosaic within a card, the micro labels, the margins. No camera.

## 6. Camera grammar

Locked frame (3 of 3 shots locked); the card changes, the camera never does.

| Move | What it expresses | Can serve |
|---|---|---|
| Hard cut to a new card | the next step, cleanly | a sequence; a routine; a numbered list |
| Disc pop | "this is the subject" | introducing a person, an object, a tool |
| Figure gesture | the step being done | an action; a habit; a reaction |
| Counter + progress update | where we are | chapters; a recipe; a countdown |
| Mosaic reshuffle at the cut | time moved on | morning → noon; a new place; a new mood |

- **Transitions:** hard cuts only (2 cuts, no dissolves, no dips). Cards are equal in length (4 s each measured),
  so the rhythm is a steady count.
- **Framing:** text in the left half from x ≈ 7.5 %; the disc on the right (centre ~73 % across, ~56 % down); micro
  UI in the 7 % frame; nothing touches the disc's edge.

## 7. Sound palette

All inferred (silent references).

- **Instruments:** mallets (marimba, vibraphone), soft pizzicato, a clean muted pluck; bright, clean, no distortion.
- **Foley:** a rounded "pop" on the disc, light ticks as limbs snap on, a soft paper-slide on the title rise, a tiny
  click on the counter.
- **Rhythm:** one card per bar or two; the cut lands on a downbeat (suggested by the equal card lengths).
- **Silence:** a breath at the cut is enough; no long silences.
- **Mix:** dry, light, −14 LUFS; music ducks under a voice. Voice: friendly, clear, short sentences, one per card.

## 8. Native moves

- **Step card.** Disc pops, figure assembles, word rises, figure acts, cut. *Fits content like:* a safety
  procedure; a recipe's steps; an onboarding flow.
- **Pictogram swap.** The same figure, new card, one limb in a new pose. *Fits content like:* exercises; sign
  language basics; dance steps.
- **Mosaic reshuffle.** The tile grid regenerates at the cut with a new seed. *Fits content like:* days of the
  week; rooms of a house; seasons.
- **Counter beat.** `01 / 05` ticks and a progress bar grows with each card. *Fits content like:* a top-five list;
  stages of a process; chapters of a talk.
- **Bilingual pair.** Caps word with its CJK line. *Fits content like:* vocabulary lessons; airport-style
  wayfinding; a bilingual menu.

## 9. Pitfalls of the medium

- **Mosaic too busy.** Using the disc's pale value or cream in tiles makes the background compete; tiles stay in the
  three darker values.
- **Tiles off the grid.** A shape not snapped to the cell grid breaks the pattern; round to the cell, rotate in 90°.
- **Anti-aliased seams.** Adjacent tiles of equal colour drawn separately show hairlines; draw same-colour runs as
  one path or overlap by 1 px.
- **Pictogram with detail.** Faces, fingers or outlines turn a sign into an illustration; capsules only.
- **CJK fallback.** A missing CJK face renders in a default font; load it through `fonts:` before frame 0.
- **Eases that bounce.** Overshoot beyond a few percent makes the cards toy-like; the measured overshoot is 1–2 %.

## 10. Engine

What the kit needs (`kit/tokens.js`, `kit/motion.js`, a style module `kit/tiles.js` to write):

- `tokens.js` as measured: `PALETTE` (ground, ink cream, accent disc, secondary deep / mid / #217480), `TYPE.title`
  0.2256 and `TYPE.body` 0.0211 of height; set families to the title, CJK and mono faces; `TEXTURE` all off.
- `motion.js`: only `move` is filled (0.417 s, ease unread). Add roles by eye: `pop` (0.3 s, `'expo.out'`, from
  0.7), `rise` (0.45 s, `'expo.out'`), `gesture` (0.5 s, `'sine.inOut'`), all marked inferred; `shot: 4.0`.
- `tiles.js` (to write): `mosaic(g, seed, cell, values)` the seeded grid of disc/half/quarter/square tiles, cached
  per seed; `figure(g, pose, x, y, s)` capsule pictogram with front/back limb values; `card(g, t, at, {word, cjk,
  n, of})` the card's choreography; `progress(g, i, n)` the bars.

Minimal example (not in the references: a card of a cyclist counting to five):

```js
draw: (g, t) => {
  const i = Math.floor(t / MOTION.shot), lt = t - i * MOTION.shot;
  mosaic(g, 100 + i, 180, [PALETTE.secondary[0], PALETTE.ground, PALETTE.secondary[1]]);
  const s = lerp(0.7, 1, tween(lt, 0, 0.3, 'expo.out'));
  g.fillStyle = PALETTE.accent; g.beginPath(); g.arc(1400, 605, 340 * s, 0, TAU); g.fill();
  figure(g, { pose: 'ride', lift: 0.02 * tween(lt, 2.6, 0.5, 'sine.inOut') }, 1400, 605, s);
  card(g, lt, 0.9, { word: 'PEDAL', cjk: '骑行', n: i + 1, of: 5 });
}
```

## 11. Variation space

Each film decides the number of cards, the words, the poses, the mosaic seeds, the hue of the family (one hue
only) and whether a counter is shown.

- **Structures:** (1) a countdown where cards get shorter as the count rises; (2) two figures alternating across
  cards, a dialogue of gestures; (3) one long card where the figure performs three gestures while only the CJK line
  changes.
- **Openings:** (1) the mosaic alone, tiles flipping into place one by one; (2) the disc already filling the frame, shrinking
  to card size; (3) the counter `00 / 05` alone on the ground.
- **Endings:** (1) all figures from the film side by side in small discs; (2) the last card holds and the mosaic
  fills the disc; (3) the counter reaches the end and the bars all turn cream.
