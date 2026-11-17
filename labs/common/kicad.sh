#!/usr/bin/env bash
# Run a command in the course's pinned KiCad image.
#
#   labs/common/kicad.sh kicad-cli version
#   labs/common/kicad.sh kicad-cli pcb drc --format json -o drc.json board.kicad_pcb
#   labs/common/kicad.sh python3 labs/common/check_board.py path/to/board.kicad_pro
#
# The image is named by digest in labs/common/kicad-image.txt, so every run uses the
# same KiCad build whatever tag Docker Hub points at today. The repo root is mounted at
# /w and the command runs in the folder that matches your current one, so relative
# paths work the same inside as outside. Run from outside the repo (a board repository
# of your own), it also mounts the current folder at /work and runs there; the course's
# scripts are then under /w. The container runs as your uid and is removed when the
# command ends.
#
# Environment:
#   IC103_DOCKER_ARGS   extra `docker run` flags, for example "--cpus 1 --memory 2g"
#   IC103_QUIET=1       don't print the image line on stderr
#   IC103_IMAGE         run this image (name@digest) instead of the pinned one; the course's
#                       render script uses it for 3D renders, which need KiCad's 3D models,
#                       and kibot.sh for the KiBot image
#   IC103_IMAGE_LABEL   the word in the image line on stderr (default KiCad; kibot.sh sets KiBot)
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$(cd "$here/../.." && pwd)"
pinned="$(head -n 1 "$here/kicad-image.txt" | tr -d '[:space:]')"
image="${IC103_IMAGE:-$pinned}"

if [ "$#" -eq 0 ]; then
    sed -n '2,/^set -e/p' "$0" | grep '^#' | sed 's/^# \{0,1\}//'
    exit 2
fi

# Map the current folder to the same place under /w. Outside the repo (in a board
# repository of your own, from Lab 03 on), mount the current folder at /work as well and
# start there, so the command sees your files and the course's scripts are under /w.
extra=()
case "$PWD/" in
    "$root"/*) workdir="/w${PWD#"$root"}" ;;
    *)         workdir="/work"; extra=(-v "$PWD":/work) ;;
esac

if ! docker image inspect "$image" >/dev/null 2>&1; then
    if [ "$image" = "$pinned" ]; then
        echo "ic103: pulling $image (808 MB, once)" >&2
    else
        echo "ic103: pulling $image" >&2
    fi
    docker pull "$image" >&2
fi

# Record exactly which image ran: the digest from the pin file, as Docker resolved it.
if [ "${IC103_QUIET:-0}" != "1" ]; then
    digest="$(docker image inspect --format '{{range .RepoDigests}}{{println .}}{{end}}' "$image" \
              | grep -m1 "${image#*@}" || true)"
    echo "ic103: ${IC103_IMAGE_LABEL:-KiCad} image ${digest:-$image}" >&2
fi

name="ic103-kicad-$$-${RANDOM}"
trap 'docker rm -f "$name" >/dev/null 2>&1 || true' EXIT INT TERM

tty_flags=()
[ -t 0 ] && [ -t 1 ] && tty_flags=(-it)

# shellcheck disable=SC2086  # IC103_DOCKER_ARGS is a list of flags on purpose
docker run --rm --name "$name" ${tty_flags[@]+"${tty_flags[@]}"} ${IC103_DOCKER_ARGS:-} \
    --user "$(id -u):$(id -g)" \
    -e HOME=/tmp/home \
    -e IC103_KICAD_IMAGE="$image" \
    -v "$root":/w ${extra[@]+"${extra[@]}"} -w "$workdir" \
    "$image" bash /w/labs/common/image-entry.sh "$@"
