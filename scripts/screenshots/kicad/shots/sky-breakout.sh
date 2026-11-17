# The three KiCad editors on Tiny Tapeout's SKY130 QFN breakout, rev 3.2
# (TinyTapeout/breakout-pcb at 91a2bf1, Apache-2.0), with tinytapeout-kicad-libs beside it,
# as Lab 01 has you open it. Fetch the boards first:
#   python3 labs/common/fetch_boards.py breakout-pcb tinytapeout-kicad-libs
# Writes kicad-schematic-editor-sky-breakout.png, kicad-pcb-editor-sky-breakout.png and
# kicad-footprint-editor-sky-breakout-u4.png.

work labs/common/upstream/breakout-pcb

launch eeschema breakout-sky-qfn/breakout-sky-qfn.kicad_sch 'breakout-sky-qfn.*Schematic Editor'
# KiCad 10.0.5 goes on loading the symbol libraries after the window opens, with a progress
# bar in the status bar. With one CPU it had finished 40 s later in our runs.
pause 40
capture kicad-schematic-editor-sky-breakout
quit eeschema

launch pcbnew breakout-sky-qfn/breakout-sky-qfn.kicad_pcb 'breakout-sky-qfn.*PCB Editor'
capture kicad-pcb-editor-sky-breakout

# Find U4 (the chip) with Edit > Find, which selects it, then Edit > Edit Footprint (Ctrl+E)
# opens that footprint, as placed on this board, in the Footprint Editor.
key ctrl+f
wait_window '^Find$' 20
type_text U4
key Return
key Escape
wait_window 'breakout-sky-qfn.*PCB Editor' 10
key ctrl+e
wait_window 'U4.*Footprint Editor' 60
pause 15
capture kicad-footprint-editor-sky-breakout-u4
