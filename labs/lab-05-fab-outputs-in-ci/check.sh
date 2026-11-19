#!/usr/bin/env bash
# The Lab 05 check, run on your own board repository:
#
#   ~/pcb101/labs/lab-05-fab-outputs-in-ci/check.sh [--planted REV]
#
# Run it from your repository's root folder; ~/pcb101 is wherever you cloned the course. It
# runs your ci/build.sh the way your workflow does: `all` (the check, fab and images stages)
# in the course's pinned KiCad image, then, if those passed, `kibot` in the pinned KiBot
# image. Then it checks the files they built and what git sees. With --planted REV it also
# builds the commit REV, where you planted an error in Part 6, and checks that it fails.
set -uo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
common="$here/../common"
check=/w/labs/lab-05-fab-outputs-in-ci/src/check_ci.py

# 1. bash ci/build.sh all, in the KiCad image: 0 passed, 1 failed, 2 the check couldn't run.
"$common/kicad.sh" python3 "$check" . --stage build "$@"
built=$?
if [ "$built" -ne 0 ] && [ "$built" -ne 1 ]; then
    exit 2
fi

# 2. bash ci/build.sh kibot, in the KiBot image. Your workflow skips this step when an earlier
#    one failed, and so does the check.
kibot=skipped
if [ "$built" -eq 0 ]; then
    echo "PCB101 Lab 05: bash ci/build.sh kibot, in the KiBot image"
    echo "------------------------------------------------------------------------"
    "$common/kibot.sh" bash ci/build.sh kibot
    kibot=$?
    echo "------------------------------------------------------------------------"
fi

# 3. One row per check.
exec "$common/kicad.sh" python3 "$check" . --stage grade --build-exit "$built" --kibot-exit "$kibot" "$@"
