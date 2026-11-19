# Lab 02's screenshots: the reference footprint RHL0024A and symbol SN74LVC8T245RHL in
# KiCad's Footprint Editor and Symbol Editor, with the dialogs the lab uses. Make the fit
# project first, which also checks the reference:
#   labs/common/kicad.sh python3 labs/lab-02-a-footprint-from-a-datasheet/src/check_footprint.py \
#       labs/lab-02-a-footprint-from-a-datasheet/solutions
# Its library tables point at solutions/, so the editors list the reference as library pcb101.
# Writes kicad-footprint-editor-rhl0024a.png, kicad-pad-properties-rhl0024a.png and
# kicad-create-array-rhl0024a.png. The symbol's figure is a kicad-cli plot (render.sh sym):
# in our runs the Symbol Editor's library filter didn't take typed text under Xvfb.
#
# The clicks are at fixed positions on the 1600x1000 screen, read off earlier captures: the
# PCB Editor's Footprint Editor button (850, 62), the footprint in the library tree (95, 197),
# and pads 1 and 2 in the Footprint Editor once the footprint is loaded.

click() { xdotool mousemove --sync "$1" "$2" click 1; sleep 1.5; }

work labs/lab-02-a-footprint-from-a-datasheet
launch pcbnew results/fit/fit.kicad_pcb 'fit.*PCB Editor'

# The Footprint Editor opens with nothing loaded and the library filter focused, so typing
# the footprint's name leaves it as the one item under pcb101 in the tree. In KiCad 10.0.5,
# Return in the filter didn't open it, and neither did a double-click on the item; clicking
# the item, at (95, 197) once the filter has run, and then pressing Return did.
click 850 62
wait_window 'Footprint Editor' 60
pause 15
type_text RHL0024A
pause 3
click 95 197
key Return
wait_window 'pcb101:RHL0024A.*Footprint Editor' 30
pause 5
capture kicad-footprint-editor-rhl0024a

# Pad 1, then E: the Pad Properties dialog.
click 925 300
key e
wait_window 'Pad Properties' 20
pause 3
capture kicad-pad-properties-rhl0024a
key Escape
wait_window 'pcb101:RHL0024A.*Footprint Editor' 10

# Pad 2, then Ctrl+T: the Create Array dialog.
click 846 320
key ctrl+t
wait_window 'Create Array' 20
pause 3
capture kicad-create-array-rhl0024a
key Escape
