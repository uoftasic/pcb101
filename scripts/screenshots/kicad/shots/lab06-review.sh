# Lab 06: the seeded board as a reviewer opens it, and where a board's design rules live.
# Writes:
#   kicad-pcb-editor-seeded-board.png    the PCB Editor with labs/lab-06-review-a-seeded-board/board/
#   kicad-board-setup-constraints.png    Board Setup > Design Rules > Constraints on Lab 04's
#                                        reference board, which has the template's JLCPCB rules

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
