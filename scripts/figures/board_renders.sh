#!/usr/bin/env bash
# 3D renders of Tiny Tapeout's boards for the guide pages, and of the course's own boards
# for the lab pages, from kicad-cli in the pinned image (scripts/screenshots/kicad/render.sh).
# Fetch the boards first:
#   python3 labs/common/fetch_boards.py breakout-pcb tinytapeout-kicad-libs
#   scripts/figures/board_renders.sh
#
# Writes into docs/assets/img/:
#   dip-dock-3d-top.png           the DIP dock (breakout-pcb 91a2bf1, Apache-2.0), top, as a
#                                 render in CI shows it: the image has no 3D models of parts
#   sky-breakout-3d-bottom.png    the SKY130 QFN breakout rev 3.2, bottom: the two DF12
#                                 connectors and the unfitted supply header J2
#   pmod-connectors-top.png       Lab 03's board with only its three Pmod connectors placed
#                                 (make_reference.py's connectors stage), top
#   pmod-simproc-lab03-top.png    Lab 03's reference board, top
#   capstone-brief-d-top.png      the capstone's Brief D reference board, top
#   capstone-brief-a-top.png      the capstone's Brief A reference board, top
#
# The two Lab 03 figures are the middle 1060 x 580 pixels of render.sh's 1568 x 984 render,
# cut out by ImageMagick in pb101/kicad-shot (scripts/screenshots/kicad/build.sh builds it),
# because the 64 x 32 mm board fills only the middle of the full render. The intermediate
# files go in Lab 03's results/figures/ (gitignored).
#
# In kicad/kicad:10.0.8, two runs of the DIP dock's top view gave byte-identical PNGs; two
# runs of the breakout's bottom view didn't (161,264 and 161,266 bytes), so compare that
# one by eye. When we ran this script on November 16, 2026, `cmp` found the four figures of
# the course's boards byte-identical to the ones in the repo.
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$(cd "$here/../.." && pwd)"
cd "$root"
R=scripts/screenshots/kicad/render.sh
U=labs/common/upstream/breakout-pcb
I=docs/assets/img

"$R" 3d "$U/dip-dock/dip-dock.kicad_pcb" "$I/dip-dock-3d-top.png" top >/dev/null
"$R" 3d "$U/breakout-sky-qfn/breakout-sky-qfn.kicad_pcb" "$I/sky-breakout-3d-bottom.png" bottom >/dev/null

# The course's own boards. The capstone's go in as rendered.
C=labs/capstone-a-board-for-a-team-chip/solutions
"$R" 3d "$C/simproc-pmod-brief-d/pmod.kicad_pcb" "$I/capstone-brief-d-top.png" top >/dev/null
"$R" 3d "$C/source-board-brief-a/source.kicad_pcb" "$I/capstone-brief-a-top.png" top >/dev/null

# Lab 03's two, rendered into results/figures/ and then cropped.
L3=labs/lab-03-a-pmod-for-one-projects-pins
T=$L3/results/figures
mkdir -p "$T"
labs/common/kicad.sh python3 "$L3/src/make_reference.py" connectors "$T/connectors" >"$T/make_reference.txt" 2>&1
"$R" 3d "$T/connectors/pmod.kicad_pcb" "$T/pmod-connectors-top.png" top >/dev/null
"$R" 3d "$L3/solutions/simproc-pmod/pmod.kicad_pcb" "$T/pmod-simproc-lab03-top.png" top >/dev/null
base="$(head -n 1 labs/common/kicad-image.txt | tr -d '[:space:]')"
shot_image="pb101/kicad-shot:$(echo "${base%@*}" | sed 's/.*://')"
docker image inspect "$shot_image" >/dev/null 2>&1 || scripts/screenshots/kicad/build.sh >/dev/null
for f in pmod-connectors-top pmod-simproc-lab03-top; do
    docker run --rm ${PB101_DOCKER_ARGS:-} --user "$(id -u):$(id -g)" -e HOME=/tmp/h \
        -v "$root":/w -w /w --entrypoint convert "$shot_image" \
        "$T/$f.png" -crop 1060x580+254+202 +repage -strip "$I/$f.png"
done

ls -l "$I/dip-dock-3d-top.png" "$I/sky-breakout-3d-bottom.png" "$I"/pmod-connectors-top.png \
    "$I"/pmod-simproc-lab03-top.png "$I"/capstone-brief-[ad]-top.png
