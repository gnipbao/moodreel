#!/bin/sh
# Rebuild the film from its source: sh build.sh  (OUT=<folder> to write elsewhere)
set -e
cd "$(dirname "$0")"
moodreel film deliver . ${OUT:+--out "$OUT"} 
