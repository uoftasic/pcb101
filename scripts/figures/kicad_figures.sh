#!/usr/bin/env bash
# The KiCad renders and plots on the guide pages "What a board does for a chip",
# "Tiny Tapeout's boards, part by part", "Schematics other people can read",
# "Symbols, footprints and libraries" and "Layers and fabricator rules".
#
#   python3 labs/common/fetch_boards.py        # the Tiny Tapeout boards, once
#   scripts/figures/kicad_figures.sh           # writes docs/assets/img/tt-*.png and kicad-*.png
#
# Every figure comes from kicad-cli through scripts/screenshots/kicad/render.sh: the plots
# in the pinned image (labs/common/kicad-image.txt), and the 3D renders in the render image
# (scripts/screenshots/kicad/render-image.txt), which has KiCad's 3D models of parts. The 3D
# renders are written as they come.
# The SVG plots go to labs/common/results/figures/ (gitignored), are cropped here where a
# figure shows part of a sheet, and are turned into PNGs on a white background by
# ImageMagick in ic103/kicad-shot (scripts/screenshots/kicad/build.sh builds it), so they
# read the same in the light and dark site themes. The schematic goes through PDF and
# needs pdftoppm (poppler-utils) on the host.
#
# Environment: IC103_DOCKER_ARGS as for labs/common/kicad.sh. We ran it with
# IC103_DOCKER_ARGS="--cpus 1 --memory 2g"; the whole script takes about a minute.
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root="$(cd "$here/../.." && pwd)"
cd "$root"
export IC103_QUIET=1

R=scripts/screenshots/kicad/render.sh
U=labs/common/upstream
IMG=docs/assets/img
TMP=labs/common/results/figures
SKY=$U/breakout-pcb/breakout-sky-qfn
DIP=$U/breakout-pcb/dip-dock
DEMO=$U/tt-demo-pcb

[ -f "$SKY/breakout-sky-qfn.kicad_pcb" ] || {
    echo "kicad_figures.sh: run python3 labs/common/fetch_boards.py first" >&2; exit 2; }
mkdir -p "$TMP"

base="$(head -n 1 labs/common/kicad-image.txt | tr -d '[:space:]')"
shot_image="ic103/kicad-shot:$(echo "${base%@*}" | sed 's/.*://')"
docker image inspect "$shot_image" >/dev/null 2>&1 || scripts/screenshots/kicad/build.sh >/dev/null

# crop SVG X Y W H: show only that rectangle of an SVG plot (in the plot's own units,
# which are millimetres on the page for every kicad-cli SVG export).
crop() {
    python3 - "$@" <<'EOF'
import re, sys
path, x, y, w, h = sys.argv[1], *sys.argv[2:6]
s = open(path).read()
# Embedded bitmaps (the logos on the sheet) stop ImageMagick's SVG reader; none is in a crop.
s = re.sub(r'<image\b.*?/>', '', s, flags=re.S)
s = re.sub(r'width="[^"]*" height="[^"]*" viewBox="[^"]*"',
           f'width="{w}mm" height="{h}mm" viewBox="{x} {y} {w} {h}"', s, count=1)
open(path, "w").write(s)
EOF
}

# png IN.svg OUT.png DENSITY: rasterize on white, with a 2 % white border.
png() {
    local in="$1" out="$2" density="$3"
    docker run --rm ${IC103_DOCKER_ARGS:-} --user "$(id -u):$(id -g)" -e HOME=/tmp/h \
        -v "$root":/w -w /w --entrypoint convert "$shot_image" \
        -density "$density" "$in" -background white -flatten \
        -bordercolor white -border 2% -depth 8 -strip "$out"
}

# 3D renders of the three boards, with the parts' 3D models.
$R 3d "$SKY/breakout-sky-qfn.kicad_pcb" "$IMG/tt-sky-breakout-top.png" top
$R 3d "$SKY/breakout-sky-qfn.kicad_pcb" "$IMG/tt-sky-breakout-bottom.png" bottom
$R 3d "$DEMO/tinytapeout-demo.kicad_pcb" "$IMG/tt-demo-board-top.png" top
$R 3d "$DIP/dip-dock.kicad_pcb" "$IMG/tt-dip-dock-top.png" top

# Copper layers: the 2-layer DIP dock and the inner layers of the 4-layer breakout.
for l in F.Cu B.Cu; do
    $R pcb "$DIP/dip-dock.kicad_pcb" "$TMP/dip-dock-$l.svg" "$l,Edge.Cuts"
    png "$TMP/dip-dock-$l.svg" "$IMG/tt-dip-dock-$(echo "${l%%.Cu}" | tr "A-Z" "a-z")cu.png" 300
done
$R pcb "$SKY/breakout-sky-qfn.kicad_pcb" "$TMP/sky-In1.Cu.svg" "In1.Cu,Edge.Cuts"
png "$TMP/sky-In1.Cu.svg" "$IMG/tt-sky-breakout-in1cu.png" 500

# The chip's footprint and symbol, as KiCad and Tiny Tapeout ship them.
$R fp /usr/share/kicad/footprints/Package_DFN_QFN.pretty QFN-64-1EP_9x9mm_P0.5mm_EP7.65x7.65mm \
    "$TMP/fp" --layers F.Cu,F.Paste,F.Mask,F.SilkS,F.Fab,F.CrtYd
crop "$TMP/fp/QFN-64-1EP_9x9mm_P0.5mm_EP7.65x7.65mm.svg" 12.4 0.9 11.4 11.4
png "$TMP/fp/QFN-64-1EP_9x9mm_P0.5mm_EP7.65x7.65mm.svg" "$IMG/kicad-qfn64-9x9-ep7.65-footprint.png" 1800
$R sym "$U/breakout-pcb/tinytapeout-kicad-libs/symbols/TinyTapeout.kicad_sym" \
    Openframe_QFN_TT06_REV2 "$TMP/sym"
png "$TMP/sym/Openframe_QFN_TT06_REV2_unit1.svg" "$IMG/tt-openframe-qfn-symbol.png" 250

# The breakout's schematic: its supply section, top left of the A3 sheet. ImageMagick's SVG
# reader drops the wires of a schematic plot, so this one goes through PDF and poppler's
# pdftoppm (poppler-utils) on the host. At 300 dpi, 1 mm is 300 / 25.4 pixels.
labs/common/kicad.sh kicad-cli sch export pdf --exclude-drawing-sheet \
    -o "$TMP/sky-sch.pdf" "$SKY/breakout-sky-qfn.kicad_sch"
px() { python3 -c "print(round($1 * 300 / 25.4))"; }
pdftoppm -r 300 -x "$(px 10)" -y "$(px 14)" -W "$(px 87)" -H "$(px 76.5)" -png -singlefile \
    "$TMP/sky-sch.pdf" "$IMG/tt-sky-breakout-sch-supplies"

ls -l "$IMG"/tt-*.png "$IMG"/kicad-qfn64-*.png
