# Labs 03 and 04: where a student finds Tiny Tapeout's Pmod symbol, KiCad's Position Relative
# To dialog, and the ESD array. Opens the board template and the Lab 03 reference board, both
# in the repo. Writes kicad-symbol-chooser-pmod.png, kicad-position-relative-to.png and
# kicad-symbol-chooser-sp0502.png.

# The symbol chooser (Place > Place Symbols, A), filtered to the Pmod connector, in the template
# a student starts from.
work labs/lab-03-a-pmod-for-one-projects-pins/template
# Wait for KiCad 10.0.5 to finish loading the symbol libraries before opening the chooser:
# opened while they were still loading, the chooser didn't take the typed filter.
launch eeschema pmod.kicad_sch 'pmod.*Schematic Editor'
pause 45
key a
wait_window 'Choose Symbol' 90
pause 10
type_text PMOD_PERIPH
pause 5
capture kicad-symbol-chooser-pmod
key Escape
quit eeschema

# Position Relative To (Shift+P) on J2 of the Lab 03 reference board, with the connectors
# unlocked as they are before a student locks them.
work labs/lab-03-a-pmod-for-one-projects-pins/solutions/simproc-pmod
sed -i '/(locked yes)/d' /tmp/work/pmod.kicad_pcb
launch pcbnew pmod.kicad_pcb 'pmod.*PCB Editor'
pause 10
key ctrl+f
wait_window '^Find$' 20
type_text J2
key Return
key Escape
wait_window 'pmod.*PCB Editor' 10
key shift+p
wait_window 'Position Relative To' 30
pause 3
capture kicad-position-relative-to
key Escape
quit pcbnew

# The symbol chooser again, filtered to the two-line ESD array Lab 04 adds.
launch eeschema pmod.kicad_sch 'pmod.*Schematic Editor'
pause 45
key a
wait_window 'Choose Symbol' 90
pause 10
type_text SP0502
pause 5
capture kicad-symbol-chooser-sp0502
