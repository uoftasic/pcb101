#!/usr/bin/env bash
# 3D renders of Tiny Tapeout's boards for the guide pages, from kicad-cli in the pinned image
# (scripts/screenshots/kicad/render.sh). Fetch the boards first:
#   python3 labs/common/fetch_boards.py breakout-pcb tinytapeout-kicad-libs
#   scripts/figures/board_renders.sh
#
# Writes into docs/assets/img/:
#   dip-dock-3d-top.png           the DIP dock (breakout-pcb 91a2bf1, Apache-2.0), top, as a
#                                 render in CI shows it: the image has no 3D models of parts
#   sky-breakout-3d-bottom.png    the SKY130 QFN breakout rev 3.2, bottom: the two DF12
#                                 connectors and the unfitted supply header J2
#
# In kicad/kicad:10.0.8, two runs of the DIP dock's top view gave byte-identical PNGs; two
# runs of the breakout's bottom view didn't (161,264 and 161,266 bytes), so compare that
# one by eye.
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$(cd "$here/../.." && pwd)"
cd "$root"
R=scripts/screenshots/kicad/render.sh
U=labs/common/upstream/breakout-pcb
I=docs/assets/img

"$R" 3d "$U/dip-dock/dip-dock.kicad_pcb" "$I/dip-dock-3d-top.png" top >/dev/null
"$R" 3d "$U/breakout-sky-qfn/breakout-sky-qfn.kicad_pcb" "$I/sky-breakout-3d-bottom.png" bottom >/dev/null
ls -l "$I/dip-dock-3d-top.png" "$I/sky-breakout-3d-bottom.png"
