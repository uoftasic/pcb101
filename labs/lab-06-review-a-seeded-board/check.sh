#!/usr/bin/env bash
# The Lab 06 check, run on your own board repository:
#
#   ~/pcb101/labs/lab-06-review-a-seeded-board/check.sh [BOARD_FOLDER]
#
# BOARD_FOLDER is the folder with your REVIEW.md, QUOTE.md and .kicad_pro (default: the
# current folder), and ~/pcb101 is wherever you cloned the course. It checks your review of
# the seeded board against the faults we planted, and your quote record against your board.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
board="${1:-.}"
[ "$#" -gt 0 ] && shift
cd "$board"
exec "$here/../common/kicad.sh" python3 /w/labs/lab-06-review-a-seeded-board/src/check_lab06.py . "$@"
