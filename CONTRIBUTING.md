# Contributing to Moodreel

Issues and pull requests are welcome. Moodreel is [MIT](LICENSE), and contributions are accepted under the same
licence.

## Set up

You need [uv](https://docs.astral.sh/uv/), ffmpeg and Node 20+:

```bash
git clone https://github.com/gnipbao/moodreel && cd moodreel
uv sync && npm install
uv run --group dev pytest
```

The tests run on synthetic data and download nothing. One test checks the Remotion export and is skipped unless
`MOODREEL_REMOTION_MODULES` points at a `node_modules` folder that holds remotion.

Some downloads are optional:
- the style embeddings and the sampled instruments, fetched only when you ask for them by name;
- a pack's large fonts, fetched by `sh demo/build.sh` when they are missing.

The README's "Try it" section says what each is for.

## Ground rules

These are the rules the code and the director's skill (`skills/moodreel`) follow. A change should keep them true.

- **A film is a function of time.** `window.render(t)` draws the whole frame from `t` alone. No clocks, no unseeded
  randomness, and no state carried between frames (`skills/moodreel/references/produce/drawing.md`).
- **Every number has a source.** A value in a style's STYLE.md is in its LEDGER.md with its basis.
  `moodreel pack --strict` refuses values it cannot trace.
- **Grammar, not content.** A style takes a reference's rhythm, palette logic, motion and framing. Never commit a
  reference's frames, footage, music, typefaces or names into a film, a pack, a test or the docs. References stay in
  `out/`, which git ignores. A pack keeps only their checksums, plus a contact sheet when they are the user's own work.
- **Code draws everything.** No generated images or video. Fonts, images, samples and data must be openly licensed
  (OFL, CC0, CC BY, MIT and similar), and each film lists them in its CREDITS.
  - Code adapted from another project goes in [NOTICE](NOTICE) with its licence.
  - Files too large for the repository are fetched by a script that checks their checksums (a pack's
    `kit/fonts/fetch.sh`).
- **Generated folders are generated.**
  - `styles/` comes from lemo-opuscar through `scripts/import_lemo_styles.py`.
  - `packs/` comes from your style library through `scripts/packs.py export`.
  - Change their source, then regenerate them.
- **No keys in the repository.** The Jev checks read `TYPESAFE_API_KEY` from the environment and never write it out.

## Pull requests

- Branch from `main` and keep each pull request to one change.
- Run the tests, and add a test for new behaviour where it can be tested on synthetic data.
- Add a line to `CHANGELOG.md` under the current "Unreleased" heading.
- For a change to how films look or move, say what you checked: stills, a contact sheet, or a check's numbers before
  and after.
