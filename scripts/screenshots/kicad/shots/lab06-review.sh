# Lab 06: the seeded board as a reviewer opens it, and where a board's design rules live.
# Writes:
#   kicad-pcb-editor-seeded-board.png    the PCB Editor with labs/lab-06-review-a-seeded-board/board/
#   kicad-board-setup-constraints.png    Board Setup > Design Rules > Constraints on Lab 04's
#                                        reference board, which has the template's JLCPCB rules
#   kicad-properties-j4.png              J4 selected on the same board, its footprint in the
#                                        Properties panel and the status bar
#   kicad-footprint-properties-j4.png    J4's Footprint Properties dialog (E)

work labs/lab-06-review-a-seeded-board/board
launch pcbnew pmod.kicad_pcb 'pmod.*PCB Editor'
pause 10
capture kicad-pcb-editor-seeded-board
quit pcbnew

work labs/lab-04-protect-and-plan/solutions/simproc-pmod
launch pcbnew pmod.kicad_pcb 'pmod.*PCB Editor'
pause 10
# The Board Setup button on the top toolbar (File > Board Setup), at this place on a
# 1600 x 1000 screen.
xdotool mousemove 125 63 click 1
wait_window 'Board Setup' 30
pause 3
# Design Rules > Constraints, in the tree on the left of the dialog.
xdotool mousemove 394 462 click 1
pause 3
# Scroll the page down to the silkscreen and text rules.
xdotool mousemove 740 600 click --repeat 15 --delay 100 5
pause 3
capture kicad-board-setup-constraints
key Escape
quit pcbnew

# J4 selected on Lab 04's reference board, where the Properties panel shows a footprint's
# details; then its Footprint Properties dialog (E).
launch pcbnew pmod.kicad_pcb 'pmod.*PCB Editor'
pause 10
key ctrl+f
wait_window '^Find$' 20
type_text J4
key Return
key Escape
wait_window 'pmod.*PCB Editor' 10
pause 3
capture kicad-properties-j4
key e
wait_window 'Footprint Properties' 30
pause 3
capture kicad-footprint-properties-j4
key Escape
quit pcbnew
