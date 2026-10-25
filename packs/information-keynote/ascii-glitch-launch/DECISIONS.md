# Decisions — ASCII Glitch Launch (gate 1)

Choices the measurements can't make. Each: the choice, the alternatives, the evidence, the cost. Approved by the user
at gate 1 on 2026-10-25, after five rounds of the remake.

## 1. Name

- **Choice**: ASCII Glitch Launch · 字符故障发布片, slug `ascii-glitch-launch` (the name the user gave, without "Video").
- **Alternatives**: Tracked Type · 追踪字 (names the signature, not the genre); Data Glitch Launch · 数据故障发布.
- **Cost**: none.

## 2. What films it is for

- **Choice**: launch and announcement teasers for software and digital products, 10–30 s, cut to a track with a pulse
  (100–130 BPM), 16:9 and 9:16. The copy is a short argument in phrases (problem, turn, answer, name).
- **Alternative**: also explainers. Possible, but the twelve-cuts-a-second montages tire over a minute.
- **Evidence**: ANALYSIS traits 3 and 4; the reference is a 15.8 s launch teaser.

## 3. Typefaces

- **Choice**: Inter (OFL) for the voice and JetBrains Mono (OFL) for coordinates, labels and dot-matrix words; both
  are on this machine (an Inter WOFF2 shipped with another app's OFL font set, JetBrains Mono from a local font cache),
  so no download. Their OFL texts are added to the kit with the files.
- **Alternatives**: (a) Geist and Geist Mono (OFL), closer to some launch films; needs a download; (b) the system's
  SF Pro: closest to the reference but not licensed for redistribution, so not in a pack.
- **Evidence**: type-lines.jpg (neutral grotesk, geometric mono); the remake used these two and matched sizes.
- **Cost**: the Inter file covers Latin only; CJK copy would need a second family (Noto Sans SC, OFL, also local).

## 4. How the materials are built

- **Choice**: one GPU cell pass as the style's core (`ascii`, `dots`, `pixelate`, `hatch`; darkest-tap rule so type
  survives), written and tested in the remake (`out/challenge2/film/cells.js`). Around it, 2D modules: the tracker
  (glyph boxes, labels, dashed paths, centre dots), the slot montage (a frame clock that re-dresses one object), grounds
  (studio with grain and scan lines; dark with the cross dither), light objects drawn in cells (tube, beam), particle
  fields (tunnel, ring), typing and number reels.
- **Alternative**: a filter-only approach (any scene, an ASCII effect on top). Faster to write, but loses what the
  reference does on purpose: type that stays legible, hatching and dots on letters only, boxes over the cells.
- **Evidence**: remake scores per scene: scenes built this way reached 0.58–0.78 (year, "BUT", "Great", "lives on",
  posts); the filtered-photo scenes (eye, mosaic) stayed under 0.2 in structure.
- **Cost**: about six modules with a test frame each; no 3D needed.

## 5. Content stand-ins

- **Choice**: the kit and demo draw every UI, icon, post and logo in code; no screenshot of a real product, no real
  person's post, no photographic footage (the reference's eye becomes a drawn iris or is left out).
- **Alternative**: let films load the user's own screenshots and footage through `kit/media.js` (allowed, they are the
  user's).
- **Cost**: drawn UIs read simpler than real ones; detail has to be budgeted (§2).

## 6. Sound for the demo

- **Choice**: an original 120 BPM track from `moodreel score` (kick, hats, bass, a bright lead, a stop before the end
  card) with the copy's phrases on its bars, and synthesised foley from the timeline (stutters on glitches, key ticks
  on typing, a whoosh into particles, a sub hit on the mark).
- **Alternative**: the reference's own track: not ours to ship.
- **Cost**: synth timbres are plainer than a produced track.

## 7. The demo (15–25 s, at gate 3)

- **Choice**: "Tidepool", a launch teaser for an invented tide-forecast API: "In 2026 / every boat can read the sea. /
  BUT / most still guess. / Good tides / start with / good data / and every good forecast / lives on / Tidepool." The
  year rolls and is tracked; a request is typed through eight API-console dresses; a wall of forecast cards turns;
  "guess" goes dot-matrix; harbour badges flash in a montage; a ring of wave particles; a beam of cells; the mark on white.
  Far from the reference's subject, and every §8 move appears once.
- **Alternatives**: a password manager ("everyone reuses the same password"); a font foundry tool ("every font looks
  the same").
- **Cost**: 1080p60, no motion blur needed (the reference shows little); renders in about two minutes.
