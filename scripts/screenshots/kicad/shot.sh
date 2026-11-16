#!/usr/bin/env bash
# Take KiCad GUI screenshots: run one shot file in the screenshot image.
#
#   scripts/screenshots/kicad/shot.sh scripts/screenshots/kicad/shots/sky-breakout.sh
#   scripts/screenshots/kicad/shot.sh SHOT_FILE OUT_DIR      # default OUT_DIR: docs/assets/img
#
# Builds ic103/kicad-shot first if it isn't there. The repo is mounted read-only; only
# OUT_DIR is written. The container runs as your uid and is removed when the shot ends,
# or after 10 minutes where GNU timeout is installed.
#
# Environment:
#   SCREEN              virtual screen size, default 1600x1000 (each editor fills it)
#   IC103_DOCKER_ARGS   extra `docker run` flags, for example "--cpus 1 --memory 2g"
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$(cd "$here/../../.." && pwd)"

if [ "$#" -lt 1 ]; then
    sed -n '2,/^set -e/p' "$0" | grep '^#' | sed 's/^# \{0,1\}//'
    exit 2
fi
shot="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
case "$shot" in
    "$root"/*) ;;
    *) echo "shot.sh: the shot file must be inside the repo: $1" >&2; exit 2 ;;
esac
out="${2:-$root/docs/assets/img}"
mkdir -p "$out"
out="$(cd "$out" && pwd)"

base="$(head -n 1 "$root/labs/common/kicad-image.txt" | tr -d '[:space:]')"
version="$(echo "${base%@*}" | sed 's/.*://')"
image="ic103/kicad-shot:$version"
docker image inspect "$image" >/dev/null 2>&1 || "$here/build.sh" >/dev/null
echo "shot.sh: $image, built from $base" >&2

name="ic103-shot-$$-${RANDOM}"
trap 'docker rm -f "$name" >/dev/null 2>&1 || true' EXIT INT TERM

# GNU timeout ends a stuck shot after 10 minutes; macOS has no `timeout` unless coreutils
# is installed, and then the shot simply has no time limit.
limit=()
command -v timeout >/dev/null 2>&1 && limit=(timeout 600)

# shellcheck disable=SC2086  # IC103_DOCKER_ARGS is a list of flags on purpose
${limit[@]+"${limit[@]}"} docker run --rm --name "$name" ${IC103_DOCKER_ARGS:-} \
    --user "$(id -u):$(id -g)" \
    -e SCREEN="${SCREEN:-1600x1000}" \
    -v "$root":/w:ro -v "$here":/rig:ro -v "$out":/out \
    -w /tmp \
    "$image" bash /rig/rig.sh "/w/${shot#"$root"/}"
