#!/bin/sh
# Ink Chronicle's default CJK faces, about 25 MB each, are too large for the repository: a copy without them gets them
# here from their publishers (OFL; the licences are beside them), each checked against the file the style was approved
# with. Faces already here are left as they are. Run `sh kit/fonts/fetch.sh`; demo/build.sh runs it first.
set -e
cd "$(dirname "$0")"
get() {                                               # file, url, sha256
  [ -f "$1" ] && return 0
  echo "fonts: fetching $1"
  curl -fsSL "$2" -o "$1.part"
  echo "$3  $1.part" | shasum -a 256 -c - >/dev/null 2>&1 || { echo "fonts: $1 from $2 is not the approved file" >&2; exit 1; }
  mv "$1.part" "$1"
}
get NotoSerifSC-wght.ttf https://raw.githubusercontent.com/google/fonts/main/ofl/notoserifsc/NotoSerifSC%5Bwght%5D.ttf 050080d9255a86808f2945bffac582b31ef32bc36411ce29563b4961670c66f9
get LXGWWenKai-Regular.ttf https://github.com/lxgw/LxgwWenKai/releases/download/v1.530/LXGWWenKai-Regular.ttf 2d73eea94ad808999d90c0000c239a84a33b09d4bc6ab6c5b8bbf1eda8a7fc8b
get LXGWWenKai-Medium.ttf https://github.com/lxgw/LxgwWenKai/releases/download/v1.530/LXGWWenKai-Medium.ttf f4b8a34d1f838fe411540cb7c97b1c384ac9738a876c4104500bc42508b2312a
