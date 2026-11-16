#!/usr/bin/env bash
# Writes every stage of the Lab 03 and Lab 04 boards into results/stages/ and runs the checks
# on each, keeping the output in results/stages/<stage>.txt. The writeups' "You should see"
# blocks are copied from these files. Run it from the repo root, in the pinned image:
#
#   labs/common/kicad.sh bash labs/lab-03-a-pmod-for-one-projects-pins/src/stages.sh
#
# It takes about 4 minutes with one CPU.
set -uo pipefail
L=labs/lab-03-a-pmod-for-one-projects-pins
S=$L/results/stages
mkdir -p "$S"
for st in noflags schematic connectors placed routed swapped protected; do
    python3 $L/src/make_reference.py "$st" "$S/$st" 2>&1 | grep -v ' Debug: '
done
rm -rf "$S/template"
cp -r $L/template "$S/template"

cp labs/lab-04-protect-and-plan/BRINGUP.md "$S/routed/BRINGUP.md"
cp labs/lab-04-protect-and-plan/solutions/simproc-pmod/BRINGUP.md "$S/protected/BRINGUP.md"

check() {   # check NAME STAGE ARGS...: run the check in the stage's folder, as a student would
    local name="$1" stage="$2"; shift 2
    ( cd "$S/$stage" && python3 /w/labs/common/check_pmod.py . "$@" ) > "$S/$name.txt" 2>&1
    echo "$name: exit $?  ($(tail -n 1 "$S/$name.txt"))"
}
check template   template
check noflags    noflags
check schematic  schematic
check connectors connectors
check placed     placed
check routed     routed
check swapped    swapped
check protected-as-lab03 protected
check routed-as-lab04    routed    --protect --bringup BRINGUP.md
check protected  protected --protect --bringup BRINGUP.md
( cd "$S/routed" && python3 /w/labs/common/check_bringup.py BRINGUP.md ) > "$S/bringup-template.txt" 2>&1
echo "bringup-template: exit $?"
