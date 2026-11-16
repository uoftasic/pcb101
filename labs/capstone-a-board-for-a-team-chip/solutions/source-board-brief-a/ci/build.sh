#!/usr/bin/env bash
# Everything this board's CI does, in one script. It runs inside the pinned KiCad image named
# in ci/kicad-image.txt: .github/workflows/board.yml runs one stage per step, and the IC103
# Lab 05 check runs all of them on your own machine the same way.
#
#   bash ci/build.sh check     ERC, DRC and schematic parity; fails if the board check fails
#   bash ci/build.sh fab       Gerbers and drill file (out/fab), BOM and position file (out/assembly)
#   bash ci/build.sh images    renders, copper plots and the schematic (out/review)
#   bash ci/build.sh all       all three, in that order
#
# Run it from the repository's root folder, which holds exactly one .kicad_pro.
set -euo pipefail

pros=( *.kicad_pro )
if [ "${#pros[@]}" -ne 1 ] || [ ! -f "${pros[0]}" ]; then
    echo "build.sh: run me from the folder with your .kicad_pro (found ${#pros[@]})" >&2
    exit 2
fi
name="${pros[0]%.kicad_pro}"

# KiCad's default library tables, so the warnings match whoever runs this. A container that
# runs as your uid, or as GitHub's runner, starts with an empty home folder and none.
cfg="${HOME:-/tmp/home}/.config/kicad/10.0"
mkdir -p "$cfg"
for t in fp-lib-table sym-lib-table; do
    [ -f "$cfg/$t" ] || cp "/usr/share/kicad/template/$t" "$cfg/$t"
done

check() {
    echo "== ERC, DRC and schematic parity"
    mkdir -p out/reports
    # check_board.py exits 1 on any ERC or DRC error, any unconnected item and any parity
    # item, warnings included, so a step that runs it fails the run.
    python3 ci/check_board.py "$name.kicad_pro" --reports out/reports --summary out/reports/summary.json
}

fab() {
    echo "== Fabrication files"
    mkdir -p out/fab out/assembly
    # The layers ticked in the board's Plot dialog (File > Plot), with the board's own options.
    kicad-cli pcb export gerbers --board-plot-params -o out/fab/ "$name.kicad_pcb"
    # Holes, in the same origin as the Gerbers: the absolute origin, because the board's plot
    # settings leave "Use drill/place file origin" unticked.
    kicad-cli pcb export drill --drill-origin absolute -o out/fab/ "$name.kicad_pcb"
    # The parts list, from the schematic, with KiCad's default columns.
    kicad-cli sch export bom -o "out/assembly/$name-bom.csv" "$name.kicad_sch"
    # Where each part goes, for an assembler: CSV, in millimetres.
    kicad-cli pcb export pos --format csv --units mm -o "out/assembly/$name-pos.csv" "$name.kicad_pcb"
}

images() {
    echo "== Review images"
    mkdir -p out/review
    # 3D renders of both sides. The image has no 3D models of parts, so they show the bare board.
    kicad-cli pcb render --side top -o "out/review/$name-top.png" "$name.kicad_pcb"
    kicad-cli pcb render --side bottom -o "out/review/$name-bottom.png" "$name.kicad_pcb"
    # One plot per copper layer, each with the outline, cropped to the board.
    kicad-cli pcb export svg --mode-multi --layers F.Cu,B.Cu --common-layers Edge.Cuts \
        --page-size-mode 2 --exclude-drawing-sheet -o out/review/ "$name.kicad_pcb"
    # The schematic as one PDF.
    kicad-cli sch export pdf -o "out/review/$name-schematic.pdf" "$name.kicad_sch"
}

case "${1:-all}" in
    check)  check ;;
    fab)    fab ;;
    images) images ;;
    all)    check; fab; images ;;
    *)      echo "usage: bash ci/build.sh check|fab|images|all" >&2; exit 2 ;;
esac
