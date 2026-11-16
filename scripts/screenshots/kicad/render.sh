#!/usr/bin/env bash
# Figures from kicad-cli in the pinned image: 3D renders, and SVG plots of a board, a
# schematic, a footprint or a symbol. Use these wherever a figure only has to show the
# design; use shot.sh when the student has to find something in the editor.
#
#   render.sh 3d  BOARD.kicad_pcb OUT.png [top|bottom|iso]     3D render, basic quality
#   render.sh pcb BOARD.kicad_pcb OUT.svg LAYERS                 board area only, e.g. F.Cu,Edge.Cuts
#   render.sh sch SCHEMATIC.kicad_sch OUT_DIR                    one SVG per sheet, named by KiCad
#   render.sh fp  LIBRARY.pretty FOOTPRINT OUT_DIR               writes OUT_DIR/FOOTPRINT.svg
#   render.sh sym LIBRARY.kicad_sym SYMBOL OUT_DIR               writes OUT_DIR/SYMBOL_unit1.svg, ...
#
# Paths are relative to your current folder, and outputs have to be inside the repo (the
# container sees only the repo). A library path may also be one inside the image, such as
# /usr/share/kicad/footprints/Package_DFN_QFN.pretty. Any further arguments go to kicad-cli
# as they are.
#
# What we measured in kicad/kicad:10.0.8 on the SKY130 breakout: two runs give byte-identical
# SVGs (once the date in <title> is removed, which this script does) and byte-identical top
# renders, so those figures can be regenerated and compared. The iso view differs
# between runs in about 4,000 of its 1.5 million pixels. A render asked for at 1600x1000
# comes out 1568x984. The image has no 3D models of parts, so renders show the bare board,
# pads, silkscreen and holes, which is also what a render in CI shows.
set -euo pipefail

# kicad-cli writes the time of the run into each SVG's <title>; drop it so that the same
# input gives the same file. The sed runs in the image, so it's GNU sed on every host.
strip_dates() {
    local files=() f
    while IFS= read -r f; do files+=("$f"); done < <(find "$@" -name '*.svg' -newer "$stamp")
    [ "${#files[@]}" -gt 0 ] || return 0
    PB101_QUIET=1 "$kicad" sed -i -E \
        's#^(<title>SVG Image created as .*) date [0-9T:-]+ (</title>)$#\1\2#' "${files[@]}"
}
stamp="$(mktemp)"
trap 'rm -f "$stamp"' EXIT

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
kicad="$here/../../../labs/common/kicad.sh"

usage() { sed -n '2,/^set -e/p' "$0" | grep '^#' | sed 's/^# \{0,1\}//'; exit 2; }
[ "$#" -ge 3 ] || usage
mode="$1"; shift

case "$mode" in
    3d)
        board="$1" out="$2"; shift 2
        view="top"
        if [ "$#" -gt 0 ] && [[ "$1" != -* ]]; then view="$1"; shift; fi
        case "$view" in
            top|bottom) side=(--side "$view") ;;
            iso)        side=(--side top --rotate '-45,0,45') ;;
            *)          usage ;;
        esac
        "$kicad" kicad-cli pcb render --quality basic --background opaque \
            --width 1600 --height 1000 "${side[@]}" "$@" -o "$out" "$board"
        ;;
    pcb)
        [ "$#" -ge 3 ] || usage
        board="$1" out="$2" layers="$3"; shift 3
        "$kicad" kicad-cli pcb export svg --mode-single --layers "$layers" \
            --page-size-mode 2 --exclude-drawing-sheet "$@" -o "$out" "$board"
        strip_dates "$(dirname "$out")"
        ;;
    sch)
        sch="$1" out="$2"; shift 2
        mkdir -p "$out"
        "$kicad" kicad-cli sch export svg "$@" -o "$out" "$sch"
        strip_dates "$out"
        ;;
    fp)
        [ "$#" -ge 3 ] || usage
        lib="$1" name="$2" out="$3"; shift 3
        mkdir -p "$out"
        "$kicad" kicad-cli fp export svg --footprint "$name" "$@" -o "$out" "$lib"
        strip_dates "$out"
        ;;
    sym)
        [ "$#" -ge 3 ] || usage
        lib="$1" name="$2" out="$3"; shift 3
        mkdir -p "$out"
        "$kicad" kicad-cli sym export svg --symbol "$name" "$@" -o "$out" "$lib"
        strip_dates "$out"
        ;;
    *)
        usage
        ;;
esac
