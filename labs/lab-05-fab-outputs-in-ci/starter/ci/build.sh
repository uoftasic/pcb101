#!/usr/bin/env bash
# Everything this board's CI does, in one script. The check, fab and images stages run inside
# the pinned KiCad image named in ci/kicad-image.txt, and the kibot stage inside the pinned
# KiBot image named in ci/kibot-image.txt: .github/workflows/board.yml runs one stage per step,
# and the IC103 Lab 05 check runs them on your own machine the same way.
#
#   bash ci/build.sh check     ERC, DRC and schematic parity; fails if the board check fails
#   bash ci/build.sh fab       Gerbers and drill file (out/fab), BOM and position file (out/assembly)
#   bash ci/build.sh images    renders, copper plots and the schematic (out/review)
#   bash ci/build.sh kibot     KiBot's outputs, from ci/board.kibot.yaml (out/kibot)
#   bash ci/build.sh all       check, fab and images, in that order; kibot needs its own image
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
# runs as your uid, or as GitHub's runner, starts with an empty home folder and none. Both
# images have the defaults in /usr/share/kicad/template/.
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
    # TODO (Lab 05, Part 3): the drill file, into out/fab/, in the same origin as the Gerbers.
    #   kicad-cli pcb export drill --help
    # TODO: the BOM, from the schematic, as out/assembly/$name-bom.csv.
    #   kicad-cli sch export bom --help
    # TODO: the position file, as out/assembly/$name-pos.csv: CSV, in millimetres.
    #   kicad-cli pcb export pos --help
}

images() {
    echo "== Review images"
    mkdir -p out/review
    # TODO (Lab 05, Part 3): 3D renders of the top and the bottom, as out/review/$name-top.png
    # and out/review/$name-bottom.png.
    #   kicad-cli pcb render --help
    # TODO: one SVG plot per copper layer, each with the board outline, into out/review/.
    #   kicad-cli pcb export svg --help
    # The schematic as one PDF.
    kicad-cli sch export pdf -o "out/review/$name-schematic.pdf" "$name.kicad_sch"
}

kibot_outputs() {
    echo "== KiBot outputs"
    # The outputs listed in ci/board.kibot.yaml, written into out/kibot/.
    kibot -c ci/board.kibot.yaml -b "$name.kicad_pcb" -e "$name.kicad_sch" -d out/kibot
}

case "${1:-all}" in
    check)  check ;;
    fab)    fab ;;
    images) images ;;
    kibot)  kibot_outputs ;;
    all)    check; fab; images ;;
    *)      echo "usage: bash ci/build.sh check|fab|images|kibot|all" >&2; exit 2 ;;
esac
