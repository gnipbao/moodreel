#!/bin/sh
# Rebuild the film from its source: sh build.sh  (OUT=<folder> to write elsewhere)
# The footage is Moodreel's own example films (MIT, this repository): deliver them, then take their clips in.
set -e
cd "$(dirname "$0")"
for f in harbour-dawn tide-town first-save quiz-night; do
  [ -f "../$f/$f.mp4" ] || moodreel film deliver "../$f"
done
add() { moodreel media add . "../$1/$1.mp4" --name "$2" --start "$3" --end "$4" --width 1280 \
  --source "Moodreel example film $1 (examples/$1 in this repository)" --license "MIT (this repository)" > /dev/null; }
add quiz-night show 4.0 7.6
add harbour-dawn harbour 4.6 8.0
add tide-town island 2.0 5.4
add first-save save 6.5 10.0
moodreel film deliver . ${OUT:+--out "$OUT"}
