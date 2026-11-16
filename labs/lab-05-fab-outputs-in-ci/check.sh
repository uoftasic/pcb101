#!/usr/bin/env bash
# The Lab 05 check, run on your own board repository:
#
#   ~/pb101/labs/lab-05-fab-outputs-in-ci/check.sh [--planted REV]
#
# Run it from your repository's root folder; ~/pb101 is wherever you cloned the course. It
# runs your ci/build.sh in the course's pinned KiCad image, the same script and stages your
# workflow runs, then checks the files it built and what git sees. With --planted REV it also
# builds the commit REV, where you planted an error in Part 5, and checks that it fails.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$here/../common/kicad.sh" python3 /w/labs/lab-05-fab-outputs-in-ci/src/check_ci.py . "$@"
