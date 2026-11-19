#!/usr/bin/env bash
# Run a command in the course's pinned KiBot image.
#
#   labs/common/kibot.sh kibot --help-output ibom
#   ~/pcb101/labs/common/kibot.sh bash ci/build.sh kibot     # in your board repository
#
# KiBot (https://github.com/INTI-CMNB/KiBot, AGPL-3.0) drives KiCad from a YAML file and makes
# outputs that kicad-cli doesn't, such as an interactive HTML BOM. It runs in its own image,
# named by digest in labs/common/kibot-image.txt: KiBot 1.9.1 with KiCad 10.0.5, KiCad's
# Ubuntu build. Everything else works as in kicad.sh, which this script calls: the folders it
# mounts, your uid, KiCad's default library tables, PCB101_DOCKER_ARGS and PCB101_QUIET.
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ "$#" -eq 0 ]; then
    sed -n '2,/^set -e/p' "$0" | grep '^#' | sed 's/^# \{0,1\}//'
    exit 2
fi

PCB101_IMAGE="$(head -n 1 "$here/kibot-image.txt" | tr -d '[:space:]')" PCB101_IMAGE_LABEL=KiBot \
    exec "$here/kicad.sh" "$@"
