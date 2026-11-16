# Lab 05: what a student looks at once CI has built the fabrication files, and the planted
# error in the PCB Editor. Opens Lab 04's reference board with Lab 05's finished ci/ added.
# Writes:
#   kicad-gerbview-simproc-pmod.png    GerbView with the Gerbers and the drill file that
#                                      `bash ci/build.sh fab` writes for that board
#   kicad-drc-planted-clearance.png    the PCB Editor's DRC dialog on the same board with the
#                                      error Lab 05, Part 5 plants (src/planted.py)

work labs/lab-04-protect-and-plan/solutions/simproc-pmod
cp -r /w/labs/lab-05-fab-outputs-in-ci/solutions/simproc-pmod/ci /tmp/work/
( cd /tmp/work && bash ci/build.sh fab ) >/tmp/fab.log 2>&1
gerbview /tmp/work/out/fab/*.gbr /tmp/work/out/fab/*.drl >/tmp/gerbview.log 2>&1 &
wait_window 'Gerber Viewer' 120
pause 5
capture kicad-gerbview-simproc-pmod
quit gerbview

# The planted error: the +3V3 track along the top edge dragged 1 mm down, into J1's pads.
python3 /w/labs/lab-05-fab-outputs-in-ci/src/planted.py /tmp/work/pmod.kicad_pcb
launch pcbnew pmod.kicad_pcb 'pmod.*PCB Editor'
pause 10
# The Design Rules Checker button on the top toolbar (Inspect > Design Rules Checker), at
# this place on a 1600 x 1000 screen, then Run DRC, the dialog's default button.
xdotool mousemove 989 63 click 1
wait_window 'Design Rules Checker' 30
pause 2
key Return
pause 15
capture kicad-drc-planted-clearance
key Escape
quit pcbnew
