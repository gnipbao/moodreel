# Contributing to Moodreel

Use [GitHub Issues](https://github.com/gnipbao/moodreel/issues) to report a bug, suggest a feature or flag unclear documentation. For a bug, include the command you ran, the expected result, the actual output and your OS. A small synthetic example helps others reproduce a measurement or rendering issue without needing your reference footage.

## Set up a development checkout

Install [uv](https://docs.astral.sh/uv/), Node.js 22.18 or newer with npm, and FFmpeg with both `ffmpeg` and `ffprobe` on your path. Moodreel uses Python 3.11 or newer. If you plan to submit a pull request, clone your fork in place of the URL below.

```sh
git clone https://github.com/gnipbao/moodreel.git
cd moodreel
uv sync --locked --group dev
npm ci
```

## Run the tests

For a quick check, run the measurement tests on synthetic images. To exercise the full suite and see why optional tests were skipped, run the second command.

```sh
uv run pytest -q tests/test_measure_units.py
uv run pytest -rs
```

The default suite uses local fixtures. Tests for optional features run when their dependencies are available. For example, `moodreel csd setup` installs style embeddings and `moodreel samples fetch` installs sampled instruments. The Remotion render test looks for `MOODREEL_REMOTION_MODULES` pointing to a `node_modules` directory containing `remotion` and `@remotion/cli`.

## Working on films, styles and packs

- **Draw from time.** A film’s `window.render(t)` must draw the same frame for the same `t`, including after a seek. Use seeded randomness and derive animation from time. See the [drawing guide](skills/moodreel/references/produce/drawing.md).
- **Trace style values.** Give each numeric value in `STYLE.md` a basis in `LEDGER.md`. Run `moodreel pack` with `--strict` to catch untraced values. See the [ledger format](skills/moodreel/references/distill/ledger.md).
- **Keep reference material local.** Derive rhythm, palette, motion and framing from references. Keep their footage, frames, music, typefaces and names out of films, packs, tests and documentation. Local references belong in the ignored `out/` directory. Packs retain checksums and may include a contact sheet when all references are the contributor’s own work.
- **Credit what you ship.** Draw film imagery in code and keep AI-generated imagery and video out of contributions. For fonts, images, samples and data, use openly licensed material and record the source and licence in the film’s `CREDITS`. Record adapted code and its licence in [NOTICE](NOTICE). A pack that downloads large fonts uses `kit/fonts/fetch.sh` to verify their checksums.
- **Edit the source of generated files.** Rebuild imported style documents with [the lemo-opuscar importer](scripts/import_lemo_styles.py). For a distilled pack, edit the installed pack in your style library and run `uv run python scripts/packs.py export <slug>`. See the [pack catalog](packs/README.md).
- **Keep credentials local.** The optional Jev checks can read `TYPESAFE_API_KEY` from the environment. Keep keys out of commits, issue reports and captured output.

Original contributions are accepted under the [MIT licence](LICENSE). Preserve third-party notices, including [the imported styles’ MIT notice](styles/LICENSE-lemo-opuscar) and [the 3DCodeVerse port’s CC BY-NC-SA 4.0 terms](kit/3dcv/LICENSE).

## Submit a pull request

1. Branch from `main` and keep the pull request focused on one change.
2. Describe the user-visible effect and how you checked it. For a change to motion or appearance, include representative stills, a contact sheet or before-and-after measurements.
3. Run the tests and add a synthetic regression case when new behaviour can be tested that way.
4. Add an entry under the current “Unreleased” heading in the [changelog](CHANGELOG.md).
