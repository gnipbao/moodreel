# Decisions — Ink Chronicle

Choices the measurements can't make. Each: the choice, the alternatives, the evidence, the cost. Proposed after eight
rounds of the remake (out/challenge4); revised after the user's notes (2026-10-29): at gate 1, distil only the style's
signature, don't constrain it, leave the model room to invent; at gate 3, the same style but never the reference's
scenes, so the kit carries primitives and every film invents its own scenes.

## 1. Name

- **Choice**: Ink Chronicle · 墨字列传, slug `ink-chronicle`: a life, an idea or a place told in its own words, set in
  type on paper and night (列传: the biographies of the old histories).
- **Alternatives**: Words as World · 字成世界 (names the signature, not the use); Paper, Ink and One Red · 纸墨一点红
  (names the palette).
- **Cost**: none.

## 2. What films it is for

- **Choice**: any film whose words can carry the picture: a person's or a place's story, a poem, an idea, a history,
  an essay, a brand's origin, an announcement with weight. Length, aspect, narration and music are each film's.
- **Alternatives**: narrow it to knowledge shorts of 45–90 s (the reference's own use): rejected at gate 1 by the
  user's note (distil the style's signature only, leave the model room).
- **Evidence**: ANALYSIS traits 1–5 describe a way of making type the world, not a genre.

## 3. Typefaces

- **Choice**: the style fixes classes, not faces: a heavy Song, a light Song, an upright Kai (or Fangsong), a mono.
  The pack ships defaults: **Noto Serif SC** (OFL; the only open Song with black weights and full GB coverage, shared
  with the reference), **LXGW WenKai** (OFL), **IBM Plex Mono** (OFL, in place of the reference's JetBrains Mono).
  A film may pick any other open faces of the same classes.
- **Alternative**: Zhuque Fangsong 朱雀仿宋 (OFL, a download of about 10 MB) as the default for the Kai role, so the
  defaults share only the Song with the reference.
- **Evidence**: rounds 2–3 of the remake: lines set in the wrong class cost their windows 0.92 to 0.79 until the right
  classes were used; the class carries the look more than the face.
- **Cost**: the CJK defaults are large (Noto Serif SC 25 MB, WenKai 2×26 MB); the pack carries them once, with their
  OFL texts.

## 4. How the materials are built

- **Choice** (revised at gate 3): the kit holds primitives, none of them compulsory: how type behaves (`typed()` with
  slam and split, `slam()`, `textPoints()`, `speckle()`, `shatter()`, `jumble()`, trembling `rows()`, `typeField()`
  over any region or polygon), marks for any shape (`stipple()`, `wash()`, `waves()`, `streaks()`, `glow()`) and a
  space to stage in (`typeSpace()`: text on any plane, characters as blocks; `fitCamera()`). The remake's set pieces
  (the floor of words and its tiles, the grove, the walker, the sea and its moon path, the peak, the bird, the crows)
  stay in the project's `studies/`, out of the pack.
- **Alternative**: the first version, which shipped those set pieces in the kit as examples a film may use, change or
  ignore: rejected at gate 3 by the user's note (keep the style, don't lock the scenes).
- **Evidence**: the first demo, drawn with that kit, re-staged them under a new subject (`moodreel scene-check`: 4 % of
  its frames copied a reference composition); the demo drawn from the primitives copies none, and 25 of its 26 sampled
  frames are new compositions.
- **Cost**: each film draws its own imagery from the primitives; three.js stays a dependency of the pack (`space.js`).

## 5. Content stand-ins

- **Choice**: the pack carries no text of the reference: the fields and planes of type take the film's own
  corpus (a parameter), never Su Shi's poems, its names or its layouts. Classical texts in the public domain may be a
  film's corpus; the style itself has none.
- **Cost**: each film supplies a few hundred characters of its own for the fields of type.

## 6. Sound for the demo

- **Choice**: an original score from `moodreel score` (sampled piano and low strings, a struck low drum under each
  slam, long rests), and foley from the timeline (paper, an ink drop, stone tiles, rain, wind); no narration.
- **Alternative**: synthesised plucked strings in place of a guqin (we have no guqin samples).
- **Evidence**: the reference has its own track and narration (MEASURE.md rhythm): not ours to take.
- **Cost**: the score is plainer than a produced track.

## 7. The demo (20–30 s, at gate 3)

- **Choice**: one film far from the reference's subject, to show the signature carrying something else: every trait of
  STYLE §1 on screen, the slam as the signature, the rest drawn freely rather than ticking the menus: "黄河" (the Yellow River from its source to the sea, in its places and
  distances).
- **Alternatives**: "活字" (movable type); a tea leaf's year; a subject the user names.
- **Cost**: none beyond the drawing.
