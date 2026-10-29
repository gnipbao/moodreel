#!/bin/sh
# Rebuild 黄河 from its source: sh build.sh  (OUT=<folder> to write elsewhere)
set -e
cd "$(dirname "$0")"
sh kit/fonts/fetch.sh                    # the CJK faces, when this copy has none (the repository keeps them out)
moodreel score .                         # the music, exactly: out/score.wav, score.js, music-data.js
node sfx.mjs > sfx.json                  # the sound effects, from the same timeline as the picture
moodreel film deliver . ${OUT:+--out "$OUT"}
if [ -z "$OUT" ]; then cp -f yellow-river.mp4 ../demo.mp4; fi
