#!/bin/sh
# Rebuild Battery Low from its source: sh build.sh  (OUT=<folder> to write elsewhere)
set -e
cd "$(dirname "$0")"
moodreel score .                         # the music, exactly: out/score.wav, score.js, lyrics.json, music-data.js
node sfx.mjs > sfx.json                  # the sound effects, from the same timeline as the picture
moodreel film deliver . ${OUT:+--out "$OUT"}
if [ -z "$OUT" ]; then cp -f battery-low.mp4 ../demo.mp4; fi
