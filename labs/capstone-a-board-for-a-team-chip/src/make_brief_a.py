#!/usr/bin/env python3
"""Write the capstone's Brief A reference board: a source board for one analog pin.

    labs/common/kicad.sh python3 labs/capstone-a-board-for-a-team-chip/src/make_brief_a.py OUT

The board plugs onto the demo board's analog header J13 (TinyTapeout/tt-demo-pcb at bbf3dd1,
a 2 x 16 header) through a 2 x 16 socket on its underside, and drives J13 pin 4, the line
that carries an0 on the SKY130 breakout. The source is a 1 kOhm trimmer across the demo
board's 3.3 V, then a 1 kOhm and 10 nF RC filter at the pin, with a test point on each side
of the resistor. The socket goes on the bottom (B.Cu), flipped and turned 270 degrees, the
one placement whose pads lie over J13's pads pad for pad when both boards face up; the
script checks that against J13 in the fetched demo board when it's there.

It uses Lab 03's generator (labs/lab-03-a-pmod-for-one-projects-pins/src/make_reference.py)
for the template project, the schematic and the netlist, places the footprints itself, and
runs inside the course's pinned KiCad image.
"""
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path.insert(0, os.path.join(REPO, "labs", "lab-03-a-pmod-for-one-projects-pins", "src"))
import make_reference as mr  # noqa: E402

mr.NAME = "source"
mr.PRO["meta"]["filename"] = "source.kicad_pro"
BOARD = (100.0, 50.0, 150.0, 80.0)
C_FP = "Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder"
J13_GND = (1, 6, 9, 14, 17, 22, 25, 30, 31)
DEMO = os.path.join(REPO, "labs", "common", "upstream", "tt-demo-pcb", "tinytapeout-demo.kicad_pcb")


def schematic(s):
    s.place("J1", "Connector_Generic:Conn_02x16_Odd_Even", 76.2, 101.6, 0, value="J13 socket",
            footprint="Connector_PinSocket_2.54mm:PinSocket_2x16_P2.54mm_Vertical")
    for n in range(1, 33):
        if n in J13_GND:
            s.attach("J1", str(n), "P:GND")
        elif n == 32:
            s.attach("J1", str(n), "P:+3V3")
        elif n == 4:
            s.attach("J1", str(n), "L:AN0")
        else:
            s.attach("J1", str(n), "NC")
    s.text("J1: a socket on the underside that mates the demo board's\n"
           "analog header J13. Pin 4 is an0 on the SKY130 breakout.", (50.8, 55.88))
    s.place("RV1", "Device:R_Potentiometer", 165.1, 88.9, 0, value="1k",
            footprint="Potentiometer_THT:Potentiometer_Bourns_3296W_Vertical")
    s.attach("RV1", "1", "P:+3V3")
    s.attach("RV1", "3", "P:GND")
    s.attach("RV1", "2", "L:SET")
    s.place("R1", "Device:R", 190.5, 101.6, 90, value="1k", footprint=mr.R_FP)
    s.attach("R1", "1", "L:SET")
    s.attach("R1", "2", "L:AN0")
    s.place("C1", "Device:C", 215.9, 109.22, 0, value="10n", footprint=C_FP)
    s.attach("C1", "1", "L:AN0")
    s.attach("C1", "2", "P:GND")
    s.place("TP1", "Connector:TestPoint", 177.8, 124.46, 0, value="TestPoint",
            footprint="TestPoint:TestPoint_Pad_D1.5mm", hide_value=True, ref_at=(180.34, 121.92, "left"))
    s.attach("TP1", "1", "L:SET")
    s.place("TP2", "Connector:TestPoint", 203.2, 124.46, 0, value="TestPoint",
            footprint="TestPoint:TestPoint_Pad_D1.5mm", hide_value=True, ref_at=(205.74, 121.92, "left"))
    s.attach("TP2", "1", "L:AN0")
    s.text("RV1 sets the source from the demo board's 3.3 V. R1 and C1 filter it\n"
           "at the pin, and C1 holds the charge the pin's switch takes when it closes.",
           (152.4, 139.7))
    s.power("+3V3", (25.4, 177.8), 90)
    s.wire((25.4, 177.8), (25.4, 180.34))
    s.flag((25.4, 180.34), 180)
    s.power("GND", (38.1, 182.88), 270)
    s.wire((38.1, 180.34), (38.1, 182.88))
    s.flag((38.1, 180.34), 0)
    s.text("Power comes from J13, so PWR_FLAG tells ERC where it comes from.", (45.72, 177.8))


# (x, y, angle, flipped): J1's pad 1 at (106, 76), the rest along +x.
PLACE = {
    "J1": (106.0, 76.0, 270, True),
    "RV1": (134.0, 58.0, 0, False),
    "R1": (122.0, 62.0, 180, False),
    "C1": (112.0, 66.0, 270, False),
    "TP1": (131.46, 64.5, 0, False),
    "TP2": (116.0, 64.5, 0, False),
}
SILK = [("Source for an0", 102.0, 52.5), ("Plugs onto J13 of the demo board", 117.0, 79.0)]


def routes(pad):
    """[(layer, width, points)], from pad positions: pad(ref, num) -> (x, y)."""
    p32, p4 = pad("J1", "32"), pad("J1", "4")
    rv1, rv2 = pad("RV1", "1"), pad("RV1", "2")
    r1a, r1b = pad("R1", "1"), pad("R1", "2")
    c1 = pad("C1", "1")
    tp1, tp2 = pad("TP1", "1"), pad("TP2", "1")
    y = r1a[1]
    return [
        ("F.Cu", mr.PWR, [p32, (p32[0], rv1[1]), rv1]),
        ("F.Cu", mr.SIG, [rv2, (rv2[0], y), r1a]),
        ("F.Cu", mr.SIG, [(rv2[0], y), tp1]),
        ("F.Cu", mr.SIG, [r1b, (c1[0], y), (p4[0], y), p4]),
        ("F.Cu", mr.SIG, [(c1[0], y), c1]),
        ("F.Cu", mr.SIG, [(tp2[0], y), tp2]),
    ]


def main():
    import pcbnew
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    for f in os.listdir(out):
        path = os.path.join(out, f)
        if f.startswith(mr.NAME + ".kicad_") or f.startswith(mr.NAME + "-backups") or \
                f in ("fp-info-cache", "lib", "fp-lib-table", "sym-lib-table"):
            shutil.rmtree(path) if os.path.isdir(path) else os.remove(path)
    work = tempfile.mkdtemp(prefix="ic103-brief-a-")
    mr.write_template(out)
    sheet = mr.Sheet(work, "Source board for an0", "IC103 capstone, Brief A reference")
    schematic(sheet)
    sch = os.path.join(out, mr.NAME + ".kicad_sch")
    sheet.write(sch)
    mr.run(["kicad-cli", "sch", "upgrade", "--force", sch])
    comps, pad_net = mr.netlist(sch, work)

    pcb = os.path.join(out, mr.NAME + ".kicad_pcb")
    board = pcbnew.LoadBoard(pcb)
    nets = {}

    def net(name):
        if name not in nets:
            ni = board.FindNet(name)
            if ni is None:
                ni = pcbnew.NETINFO_ITEM(board, name)
                board.Add(ni)
            nets[name] = ni
        return nets[name]

    x0, y0, x1, y1 = BOARD
    edge = pcbnew.PCB_SHAPE(board)
    edge.SetShape(pcbnew.SHAPE_T_RECT)
    edge.SetStart(mr.pt(x0, y0))
    edge.SetEnd(mr.pt(x1, y1))
    edge.SetLayer(pcbnew.Edge_Cuts)
    edge.SetWidth(mr.mm(0.05))
    board.Add(edge)

    pads = {}
    for ref, (x, y, angle, flipped) in PLACE.items():
        c = comps[ref]
        lib, name = c["footprint"].split(":")
        fp = pcbnew.FootprintLoad(mr.footprint_path(lib), name)
        fp.SetFPID(pcbnew.LIB_ID(lib, name))
        fp.SetReference(ref)
        fp.SetValue(c["value"])
        fp.SetExcludedFromBOM(False)      # the test points are in the BOM, as in the schematic
        for k, v in c["fields"].items():
            if k not in ("Footprint", "Reference", "Value"):
                mr.set_field(fp, k, v)
        fp.SetPath(pcbnew.KIID_PATH("/" + c["tstamp"]))
        fp.SetSheetname("/")
        fp.SetSheetfile(mr.NAME + ".kicad_sch")
        board.Add(fp)
        fp.SetPosition(mr.pt(x, y))
        if flipped:
            fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
        fp.SetOrientationDegrees(angle)
        if ref == "J1":
            fp.SetLocked(True)
        for p in fp.Pads():
            n = pad_net.get((ref, p.GetNumber()))
            if n:
                p.SetNet(net(n))
            pos = p.GetPosition()
            pads[(ref, p.GetNumber())] = (round(pcbnew.ToMM(pos.x), 4), round(pcbnew.ToMM(pos.y), 4))

    # J1's pads, seen from above, must lie over J13's.
    if os.path.exists(DEMO):
        demo = pcbnew.LoadBoard(DEMO)
        j13 = [f for f in demo.GetFootprints() if f.GetReference() == "J13"][0]
        jp = {p.GetNumber(): (pcbnew.ToMM(p.GetPosition().x), pcbnew.ToMM(p.GetPosition().y)) for p in j13.Pads()}
        a, b = jp["1"], pads[("J1", "1")]
        for n in jp:
            d = (round(jp[n][0] - a[0], 3), round(jp[n][1] - a[1], 3))
            e = (round(pads[("J1", n)][0] - b[0], 3), round(pads[("J1", n)][1] - b[1], 3))
            if d != e:
                raise SystemExit(f"make_brief_a: J1 pad {n} is at {e} from pad 1; J13's is at {d}")
        print("J1's pads match J13's, pad for pad, seen from above")
    else:
        print("the demo board isn't fetched, so J1 wasn't compared with J13")

    def pad(ref, num):
        return pads[(ref, num)]

    def net_at(xy):
        for (ref, num), q in pads.items():
            if abs(q[0] - xy[0]) < 1e-3 and abs(q[1] - xy[1]) < 1e-3:
                return pad_net.get((ref, num))
        return None

    for layer, width, points in routes(pad):
        n = net_at(points[0]) or net_at(points[-1])
        if n is None:
            for t in board.GetTracks():
                for q in (t.GetStart(), t.GetEnd()):
                    if abs(pcbnew.ToMM(q.x) - points[0][0]) < 1e-3 and abs(pcbnew.ToMM(q.y) - points[0][1]) < 1e-3:
                        n = t.GetNet().GetNetname()
        if n is None:
            raise SystemExit(f"make_brief_a: no net for the track at {points[0]}")
        for a, b in zip(points, points[1:]):
            t = pcbnew.PCB_TRACK(board)
            t.SetStart(mr.pt(*a))
            t.SetEnd(mr.pt(*b))
            t.SetWidth(mr.mm(width))
            t.SetLayer(pcbnew.F_Cu if layer == "F.Cu" else pcbnew.B_Cu)
            t.SetNet(net(n))
            board.Add(t)

    for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
        z = pcbnew.ZONE(board)
        z.SetLayer(layer)
        z.SetNet(net("GND"))
        z.SetZoneName("GND")
        z.SetLocalClearance(mr.mm(0.3))
        z.SetMinThickness(mr.mm(0.25))
        z.SetThermalReliefGap(mr.mm(0.5))
        z.SetThermalReliefSpokeWidth(mr.mm(0.5))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
        ol = z.Outline()
        ol.NewOutline()
        for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
            ol.Append(mr.mm(x), mr.mm(y))
        board.Add(z)
    board.BuildConnectivity()
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())

    for text, x, y in SILK:
        t = pcbnew.PCB_TEXT(board)
        t.SetText(text)
        t.SetPosition(mr.pt(x, y))
        t.SetLayer(pcbnew.F_SilkS)
        t.SetTextSize(pcbnew.VECTOR2I(mr.mm(1.0), mr.mm(1.0)))
        t.SetTextThickness(mr.mm(0.15))
        t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_LEFT)
        board.Add(t)
    board.GetTitleBlock().SetTitle("Source board for an0")
    pcbnew.SaveBoard(pcb, board)
    for f in (mr.NAME + ".kicad_prl",):
        if os.path.exists(os.path.join(out, f)):
            os.remove(os.path.join(out, f))
    shutil.rmtree(work, ignore_errors=True)
    print(f"wrote the Brief A reference board into {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
