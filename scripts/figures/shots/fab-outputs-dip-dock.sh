# Tiny Tapeout's DIP dock (TinyTapeout/breakout-pcb at 91a2bf1, Apache-2.0), a 2-layer board,
# for the Fabrication outputs and KiCad files in git pages. Fetch the boards first:
#   python3 labs/common/fetch_boards.py breakout-pcb tinytapeout-kicad-libs
# Run it with:
#   scripts/screenshots/kicad/shot.sh scripts/figures/shots/fab-outputs-dip-dock.sh OUT_DIR
# and copy the two PNGs you want into docs/assets/img/. Writes to OUT_DIR:
#   kicad-plot-dialog-dip-dock.png   the PCB Editor's Plot dialog (File > Plot...), which holds
#                                    the board's own Gerber settings (--board-plot-params)
#   kicad-gerbview-dip-dock-drill-absolute.png
#                                    GerbView with the board's Gerbers and a drill file made with
#                                    kicad-cli's default (absolute) drill origin, which doesn't line up
#   kicad-gerbview-dip-dock.png      the same Gerbers with a drill file made with --drill-origin plot
#   files-*.txt, history-*.txt       what KiCad wrote next to the board when it was opened,
#                                    saved and closed, for the KiCad files in git page
#   dip-dock-saved.kicad_pcb         the board as KiCad saved it, unchanged otherwise

work labs/common/upstream/breakout-pcb
listing() { ( cd /tmp/work/dip-dock && find . -path ./.history/.git -prune -o -print | sort ) > "/out/files-$1.txt"; }
listing 0-copied

launch pcbnew dip-dock/dip-dock.kicad_pcb 'dip-dock.*PCB Editor'
pause 20
listing 1-open

# File > Plot... is two items up from the top of the File menu (Plot, then Quit).
key alt+f
key Up
key Up
key Return
wait_window '^Plot' 30
capture kicad-plot-dialog-dip-dock
key Escape
wait_window 'dip-dock.*PCB Editor' 10

# Save without changing anything, then quit the way a student would.
key ctrl+s
pause 5
listing 2-saved
key ctrl+q
pause 8
listing 3-closed
cp /tmp/work/dip-dock/dip-dock.kicad_pcb /out/dip-dock-saved.kicad_pcb
cat /tmp/work/dip-dock/.history/README.txt > /out/history-README.txt 2>/dev/null || true
cat /tmp/work/dip-dock/.history/.gitignore > /out/history-gitignore.txt 2>/dev/null || true
( cd /tmp/work/dip-dock/.history && git log --stat 2>&1 ) > /out/history-log.txt || true
find /tmp/home /tmp/work -name 'fp-info-cache*' > /out/files-fp-info-cache.txt 2>&1 || true

# The board's own Gerber settings, as Lab 05's CI makes them, and the drill file, twice:
# first with kicad-cli's default drill origin (absolute), then with --drill-origin plot.
# The board's plot settings tick "Use drill/place file origin", so only the second lines up.
B=/w/labs/common/upstream/breakout-pcb/dip-dock/dip-dock.kicad_pcb
mkdir -p /tmp/gerb /tmp/gerb-plot
kicad-cli pcb export gerbers --board-plot-params -o /tmp/gerb/ "$B" >/dev/null 2>&1
cp /tmp/gerb/*.gbr /tmp/gerb/*.gbrjob /tmp/gerb-plot/
kicad-cli pcb export drill -o /tmp/gerb/ "$B" >/dev/null 2>&1
kicad-cli pcb export drill --drill-origin plot -o /tmp/gerb-plot/ "$B" >/dev/null 2>&1
ls /tmp/gerb > /out/files-gerb.txt
head -12 /tmp/gerb/dip-dock.drl > /out/drill-absolute-head.txt
head -12 /tmp/gerb-plot/dip-dock.drl > /out/drill-plot-head.txt

gerbview /tmp/gerb/*.gbr /tmp/gerb/*.drl >/tmp/gerbview.log 2>&1 &
wait_window 'Gerber Viewer' 120
pause 5
capture kicad-gerbview-dip-dock-drill-absolute
quit gerbview

gerbview /tmp/gerb-plot/*.gbr /tmp/gerb-plot/*.drl >/tmp/gerbview2.log 2>&1 &
wait_window 'Gerber Viewer' 120
pause 5
capture kicad-gerbview-dip-dock
