#!/usr/bin/env bash
# Figures from kicad-cli: 3D renders, and SVG plots of a board, a schematic, a footprint or a
# symbol. Use these wherever a figure only has to show the design; use shot.sh when the
# student has to find something in the editor.
#
#   render.sh 3d  BOARD.kicad_pcb OUT.png [top|bottom|iso]     3D render, basic quality
#   render.sh pcb BOARD.kicad_pcb OUT.svg LAYERS                 board area only, e.g. F.Cu,Edge.Cuts
#   render.sh sch SCHEMATIC.kicad_sch OUT_DIR                    one SVG per sheet, named by KiCad
#   render.sh fp  LIBRARY.pretty FOOTPRINT OUT_DIR               writes OUT_DIR/FOOTPRINT.svg
#   render.sh sym LIBRARY.kicad_sym SYMBOL OUT_DIR               writes OUT_DIR/SYMBOL_unit1.svg, ...
#   render.sh --bg COLOR MODE ...                                an SVG plot on an opaque background
#
# kicad-cli's SVG plots are transparent, and their colours were chosen for the editor's own
# background: dark lines on white in the Schematic and Symbol Editors, and light ones on
# #001023 in the PCB and Footprint Editors (sampled from screenshots of both in the pinned
# image). On a page in the other colour mode they're hard to read, so give a
# plot the background its editor has, for example --bg '#ffffff' for a symbol or --bg
# '#001023' for a footprint. COLOR is #rrggbb.
#
# The plots run in the pinned image (labs/common/kicad-image.txt). The 3D renders run in the
# render image, which has KiCad's 3D models of parts as well: IC103_RENDER_IMAGE if it's
# set, otherwise the image named by digest in render-image.txt next to this script
# (kicad/kicad:10.0.5-full, the same kicad-cli build as the pinned image plus the models).
#
# Paths are relative to your current folder, and outputs have to be inside the repo (the
# container sees only the repo). A library path may also be one inside the image, such as
# /usr/share/kicad/footprints/Package_DFN_QFN.pretty. Any further arguments go to kicad-cli
# as they are.
#
# What we measured on the SKY130 breakout, with the plots in kicad/kicad:10.0.5 and the renders
# in kicad/kicad:10.0.5-full: two runs give byte-identical SVGs (once the date in <title> is
# removed, which this script does), so plots can be regenerated and compared. Two renders of
# the same view weren't always identical: of the 1,542,912 pixels, 1 differed between two top
# views, 54 between two bottom views and 4,025 between two iso views. Two top views of the DIP
# dock were byte-identical. A render asked for at 1600x1000 comes out 1568x984. The render
# image draws each part's 3D model where its footprint names one the image has; the pinned
# image has no 3D models (/usr/share/kicad/3dmodels doesn't exist), so a render made in it,
# as in a CI job that uses it, shows the bare board, pads, silkscreen and holes, and only the
# parts whose models are embedded in the board file (the breakout's two DF12 connectors).
set -euo pipefail

# kicad-cli writes the time of the run into each SVG's <title>; drop it so that the same
# input gives the same file. The sed runs in the image, so it's GNU sed on every host.
strip_dates() {
    local files=() f
    while IFS= read -r f; do files+=("$f"); done < <(find "$@" -name '*.svg' -newer "$stamp")
    [ "${#files[@]}" -gt 0 ] || return 0
    IC103_QUIET=1 "$kicad" sed -i -E \
        's#^(<title>SVG Image created as .*) date [0-9T:-]+ (</title>)$#\1\2#' "${files[@]}"
}
# --bg: an opaque rectangle of that colour behind everything else, just after <desc>.
add_bg() {
    [ -n "$bg" ] || return 0
    local files=() f
    while IFS= read -r f; do files+=("$f"); done < <(find "$@" -name '*.svg' -newer "$stamp")
    [ "${#files[@]}" -gt 0 ] || return 0
    IC103_QUIET=1 "$kicad" sed -i -E \
        "0,/<\/desc>/s|</desc>|&\n<rect x=\"0\" y=\"0\" width=\"100%\" height=\"100%\" fill=\"$bg\"/>|" \
        "${files[@]}"
    for f in "${files[@]}"; do
        grep -q "^<rect x=\"0\" y=\"0\" width=\"100%\" height=\"100%\" fill=\"$bg\"/>$" "$f" \
            || { echo "render.sh: no <desc> in $f, so no background was added" >&2; exit 1; }
    done
}
stamp="$(mktemp)"
trap 'rm -f "$stamp"' EXIT

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
kicad="$here/../../../labs/common/kicad.sh"
render_image="${IC103_RENDER_IMAGE:-$(head -n 1 "$here/render-image.txt" | tr -d '[:space:]')}"

usage() { sed -n '2,/^set -e/p' "$0" | grep '^#' | sed 's/^# \{0,1\}//'; exit 2; }
bg=""
if [ "${1:-}" = "--bg" ]; then
    [ "$#" -ge 2 ] && [[ "$2" =~ ^#[0-9A-Fa-f]{6}$ ]] || usage
    bg="$2"; shift 2
fi
[ "$#" -ge 3 ] || usage
mode="$1"; shift
[ -z "$bg" ] || [ "$mode" != 3d ] || usage

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
        IC103_IMAGE="$render_image" "$kicad" kicad-cli pcb render --quality basic --background opaque \
            --width 1600 --height 1000 "${side[@]}" "$@" -o "$out" "$board"
        ;;
    pcb)
        [ "$#" -ge 3 ] || usage
        board="$1" out="$2" layers="$3"; shift 3
        "$kicad" kicad-cli pcb export svg --mode-single --layers "$layers" \
            --page-size-mode 2 --exclude-drawing-sheet "$@" -o "$out" "$board"
        strip_dates "$(dirname "$out")"
        add_bg "$(dirname "$out")"
        ;;
    sch)
        sch="$1" out="$2"; shift 2
        mkdir -p "$out"
        "$kicad" kicad-cli sch export svg "$@" -o "$out" "$sch"
        strip_dates "$out"
        add_bg "$out"
        ;;
    fp)
        [ "$#" -ge 3 ] || usage
        lib="$1" name="$2" out="$3"; shift 3
        mkdir -p "$out"
        "$kicad" kicad-cli fp export svg --footprint "$name" "$@" -o "$out" "$lib"
        strip_dates "$out"
        add_bg "$out"
        ;;
    sym)
        [ "$#" -ge 3 ] || usage
        lib="$1" name="$2" out="$3"; shift 3
        mkdir -p "$out"
        "$kicad" kicad-cli sym export svg --symbol "$name" "$@" -o "$out" "$lib"
        strip_dates "$out"
        add_bg "$out"
        ;;
    *)
        usage
        ;;
esac
