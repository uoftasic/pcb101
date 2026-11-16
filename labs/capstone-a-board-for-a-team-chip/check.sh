#!/usr/bin/env bash
# The capstone check, run on your own board repository:
#
#   ~/ic103/labs/capstone-a-board-for-a-team-chip/check.sh --brief D [--pins my-project.json]
#   ~/ic103/labs/capstone-a-board-for-a-team-chip/check.sh --brief A
#
# Run it from your repository's root folder; ~/ic103 is wherever you cloned the course. It
# runs Lab 05's check (your CI build and its outputs), checks DESIGN.md and your history,
# then the brief's own checks, in the course's pinned KiCad image.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$here/../common/kicad.sh" python3 /w/labs/capstone-a-board-for-a-team-chip/src/check_capstone.py . "$@"
