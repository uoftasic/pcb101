# Lab 01's screenshots of Tiny Tapeout's SKY130 QFN breakout, rev 3.2 (TinyTapeout/breakout-pcb
# at 91a2bf1, Apache-2.0), in the Schematic Editor. Fetch the boards first:
#   python3 labs/common/fetch_boards.py breakout-pcb tinytapeout-kicad-libs
# Writes kicad-symbol-fields-table-sky-breakout.png, kicad-schematic-sky-breakout-core-voltage.png,
# kicad-schematic-sky-breakout-supply-headers.png and kicad-erc-sky-breakout-errors.png.
#
# The clicks are at fixed screen positions on the 1600x1000 screen, read off earlier captures:
# the toolbar's Symbol Fields Table button (1197, 62) and Electrical Rules Checker button
# (1102, 62), and the ERC dialog's Run ERC button and Errors check box. A KiCad update that
# moves a button moves these too; the failed-*.png a stuck shot leaves shows where things went.

click() { xdotool mousemove --sync "$1" "$2" click 1; sleep 1.5; }
# zoom_at X Y N: N steps of the mouse wheel at a point, which zooms in around it.
zoom_at() { local i; xdotool mousemove --sync "$1" "$2"; for i in $(seq 1 "$3"); do xdotool click 4; sleep 0.4; done; sleep 2; }

work labs/common/upstream/breakout-pcb
launch eeschema breakout-sky-qfn/breakout-sky-qfn.kicad_sch 'breakout-sky-qfn.*Schematic Editor'

# The Core Voltage Selection block (top left of the sheet), then the MUX and Supply Headers
# block (right of the title), each zoomed from the whole-sheet view the editor opens with.
zoom_at 540 273 6
capture kicad-schematic-sky-breakout-core-voltage
key Home
zoom_at 1180 340 6
capture kicad-schematic-sky-breakout-supply-headers
key Home

# Tools > Edit Symbol Fields, from its toolbar button. It opens on the view preset saved in
# the project, Tiny Tapeout's "populatedlcsc".
click 1197 62
wait_window 'Symbol Fields Table' 30
pause 3
capture kicad-symbol-fields-table-sky-breakout
key Escape
wait_window 'breakout-sky-qfn.*Schematic Editor' 10

# Inspect > Electrical Rules Checker, Run ERC, then tick "Errors" to list them.
click 1102 62
wait_window 'Electrical Rules Checker' 30
click 1080 726
pause 15
click 624 677
pause 3
capture kicad-erc-sky-breakout-errors
