#!/bin/sh
# Rebuild the film from its source: sh build.sh  (OUT=<folder> to write elsewhere)
# The score plays sampled instruments: fetch them once first with `moodreel samples fetch` (272 MB, CC0).
set -e
cd "$(dirname "$0")"
moodreel film deliver . ${OUT:+--out "$OUT"} 
