#!/usr/bin/env bash
# Runs inside the pinned KiCad image, in front of whatever command kicad.sh was given.
#
# The image's own user, `kicad`, has KiCad's global library tables in
# /home/kicad/.config/kicad/10.0/ (fp-lib-table and sym-lib-table). kicad.sh runs the
# container as *your* uid instead, so that the files it writes into the repo belong to
# you, and that uid starts with an empty HOME and no library tables. Without them, ERC
# and DRC report every standard library as missing and the warning counts change (the
# course plan's fact T12). /home/kicad is readable only by `kicad`, but its two tables are
# byte-for-byte the defaults KiCad ships in /usr/share/kicad/template/ (checked with cmp
# in kicad/kicad:10.0.8), so we copy those. Every run then sees the same configuration as
# the image's default user, whoever runs it.
set -euo pipefail

cfg="${HOME:-/tmp/home}/.config/kicad/10.0"
if [ ! -f "$cfg/fp-lib-table" ] || [ ! -f "$cfg/sym-lib-table" ]; then
    mkdir -p "$cfg"
    cp /usr/share/kicad/template/fp-lib-table /usr/share/kicad/template/sym-lib-table "$cfg/"
fi

exec "$@"
