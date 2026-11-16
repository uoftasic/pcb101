#!/usr/bin/env bash
# Build ic103/kicad-shot:<version>, the pinned KiCad image plus Xvfb, openbox, xdotool,
# xwd and ImageMagick. About 30 MB on top of the KiCad image.
#
#   scripts/screenshots/kicad/build.sh
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$(cd "$here/../../.." && pwd)"
base="$(head -n 1 "$root/labs/common/kicad-image.txt" | tr -d '[:space:]')"
version="$(echo "${base%@*}" | sed 's/.*://')"
tag="ic103/kicad-shot:$version"
docker build --build-arg KICAD_IMAGE="$base" -t "$tag" "$here" >&2
echo "$tag"
