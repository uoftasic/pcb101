#!/usr/bin/env python3
"""Write the capstone's Brief D reference board: Lab 04's SimProc Pmod with a test point on
each UART line.

    labs/common/kicad.sh python3 labs/capstone-a-board-for-a-team-chip/src/make_brief_d.py OUT

It uses Lab 03's generator (labs/lab-03-a-pmod-for-one-projects-pins/src/make_reference.py)
for everything: Lab 04's schematic with two test points added, TP3 on UART_RX (ui[0], between
J1 and R1) and TP4 on DONGLE_RXD (uo[0], between R2 and the dongle header J4), and Lab 04's
board with TP3 beside R1 and TP4 beside the track from R2 to J4, each on a short track.
Files other than the KiCad project in OUT (DESIGN.md, BRINGUP.md, ci/, .github/) are left
alone. It runs inside the course's pinned KiCad image.
"""
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, os.path.join(REPO, "labs", "lab-03-a-pmod-for-one-projects-pins", "src"))
import make_reference as mr  # noqa: E402

TP3 = (117.3, 60.0)       # on UART_RX, right of R1, below J1's courtyard
TP4 = (162.3, 66.0)       # on DONGLE_RXD, right of R2's track down to J4


def schematic(s):
    mr.schematic(s, "04")
    s.place("TP3", "Connector:TestPoint", 241.3, 81.28, 0, value="TestPoint",
            footprint="TestPoint:TestPoint_Pad_D1.5mm", hide_value=True, ref_at=(243.84, 78.74, "left"))
    s.attach("TP3", "1", "L:UART_RX")
    s.place("TP4", "Connector:TestPoint", 241.3, 93.98, 0, value="TestPoint",
            footprint="TestPoint:TestPoint_Pad_D1.5mm", hide_value=True, ref_at=(243.84, 91.44, "left"))
    s.attach("TP4", "1", "L:DONGLE_RXD")
    s.text("TP3: ui[0], between J1 and R1.\nTP4: uo[0], between R2 and J4.", (248.92, 86.36))


_routes = mr.routes


def routes(lab, swapped=False):
    r = []
    for layer, width, pts in _routes(lab, swapped):
        if pts == [(114.70, mr.PMOD_Y), (114.70, 60.5)]:
            r.append((layer, width, [(114.70, mr.PMOD_Y), (114.70, 59.0), (114.70, 60.5)]))
            r.append((layer, width, [(114.70, 59.0), (TP3[0], 59.0), TP3]))
        elif pts[:2] == [(160.42, 62.5), (160.42, 79.0)]:
            r.append((layer, width, [(160.42, 62.5), (160.42, TP4[1])] + pts[1:]))
            r.append((layer, width, [(160.42, TP4[1]), TP4]))
        else:
            r.append((layer, width, pts))
    if len(r) != len(_routes(lab, swapped)) + 2:
        raise SystemExit("make_brief_d: Lab 04's UART tracks have moved; update this script")
    return r


def main():
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    for f in os.listdir(out):
        path = os.path.join(out, f)
        if f.startswith(mr.NAME + ".kicad_") or f.startswith(mr.NAME + "-backups") or \
                f in ("fp-info-cache", "lib", "fp-lib-table", "sym-lib-table"):
            shutil.rmtree(path) if os.path.isdir(path) else os.remove(path)
    work = tempfile.mkdtemp(prefix="pb101-brief-d-")
    mr.write_template(out)
    sheet = mr.Sheet(work, "SimProc Pmod, capstone", "PB101 capstone, Brief D reference")
    schematic(sheet)
    sch = os.path.join(out, mr.NAME + ".kicad_sch")
    sheet.write(sch)
    mr.run(["kicad-cli", "sch", "upgrade", "--force", sch])
    comps, pad_net = mr.netlist(sch, work)
    mr.routes = routes
    place = dict(mr.PLACE4, TP3=(TP3[0], TP3[1], 0), TP4=(TP4[0], TP4[1], 0))
    mr.build_board(os.path.join(out, mr.NAME + ".kicad_pcb"), comps, pad_net, place, "04", True, True)
    for f in (mr.NAME + ".kicad_prl",):
        if os.path.exists(os.path.join(out, f)):
            os.remove(os.path.join(out, f))
    shutil.rmtree(work, ignore_errors=True)
    print(f"wrote the Brief D reference board into {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
