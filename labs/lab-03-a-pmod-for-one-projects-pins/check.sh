#!/usr/bin/env bash
# The Lab 03 check, run on your own board repository:
#
#   ~/pcb101/labs/lab-03-a-pmod-for-one-projects-pins/check.sh [BOARD_FOLDER]
#
# BOARD_FOLDER is the folder with your .kicad_pro (default: the current folder), and ~/pcb101
# is wherever you cloned the course. It runs labs/common/check_pmod.py in the course's pinned
# KiCad image: the board check (ERC, DRC, unconnected items, schematic parity), then the Pmod
# connectors' placement and SimProc's pin list. Extra arguments go to check_pmod.py, for
# example --pins my-project.json for a project other than SimProc.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
board="${1:-.}"
[ "$#" -gt 0 ] && shift
cd "$board"
exec "$here/../common/kicad.sh" python3 /w/labs/common/check_pmod.py . "$@"
