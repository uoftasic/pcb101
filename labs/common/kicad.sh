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
# paths work the same inside as outside. The container runs as your uid and is removed
# when the command ends.
#
# Environment:
#   PB101_DOCKER_ARGS   extra `docker run` flags, for example "--cpus 1 --memory 2g"
#   PB101_QUIET=1       don't print the image line on stderr
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$(cd "$here/../.." && pwd)"
image="$(head -n 1 "$here/kicad-image.txt" | tr -d '[:space:]')"

if [ "$#" -eq 0 ]; then
    sed -n '2,/^set -e/p' "$0" | grep '^#' | sed 's/^# \{0,1\}//'
    exit 2
fi

# Map the current folder to the same place under /w; outside the repo, start at /w.
case "$PWD/" in
    "$root"/*) sub="${PWD#"$root"}" ;;
    *)         sub="" ;;
esac

if ! docker image inspect "$image" >/dev/null 2>&1; then
    echo "pb101: pulling $image (812 MB, once)" >&2
    docker pull "$image" >&2
fi

# Record exactly which image ran: the digest from the pin file, as Docker resolved it.
if [ "${PB101_QUIET:-0}" != "1" ]; then
    digest="$(docker image inspect --format '{{range .RepoDigests}}{{println .}}{{end}}' "$image" \
              | grep -m1 "${image#*@}" || true)"
    echo "pb101: KiCad image ${digest:-$image}" >&2
fi

name="pb101-kicad-$$-${RANDOM}"
trap 'docker rm -f "$name" >/dev/null 2>&1 || true' EXIT INT TERM

tty_flags=()
[ -t 0 ] && [ -t 1 ] && tty_flags=(-it)

# shellcheck disable=SC2086  # PB101_DOCKER_ARGS is a list of flags on purpose
docker run --rm --name "$name" ${tty_flags[@]+"${tty_flags[@]}"} ${PB101_DOCKER_ARGS:-} \
    --user "$(id -u):$(id -g)" \
    -e HOME=/tmp/home \
    -e PB101_KICAD_IMAGE="$image" \
    -v "$root":/w -w "/w$sub" \
    "$image" bash /w/labs/common/image-entry.sh "$@"
