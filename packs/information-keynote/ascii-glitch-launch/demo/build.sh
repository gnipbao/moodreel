#!/bin/sh
# Rebuild Tidepool from its source: sh build.sh  (OUT=<folder> to write elsewhere)
set -e
cd "$(dirname "$0")"
moodreel score .                         # the music, exactly: out/score.wav, score.js, music-data.js
node sfx.mjs > sfx.json                  # the sound effects, from the same timeline as the picture
moodreel film deliver . ${OUT:+--out "$OUT"}
if [ -z "$OUT" ]; then cp -f tidepool.mp4 ../demo.mp4; fi
