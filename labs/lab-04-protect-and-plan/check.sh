#!/usr/bin/env bash
# The Lab 04 check, run on your own board repository:
#
#   ~/ic103/labs/lab-04-protect-and-plan/check.sh [BOARD_FOLDER]
#
# BOARD_FOLDER is the folder with your .kicad_pro and BRINGUP.md (default: the current
# folder), and ~/ic103 is wherever you cloned the course. It runs everything Lab 03's check
# does, then the protection checks (series resistors, ESD, a current-sense point) and the
# bring-up plan check, in the course's pinned KiCad image.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
board="${1:-.}"
[ "$#" -gt 0 ] && shift
cd "$board"
exec "$here/../common/kicad.sh" python3 /w/labs/common/check_pmod.py . --protect --bringup BRINGUP.md "$@"
