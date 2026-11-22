#!/usr/bin/env python3
"""Write the Lab 06 seeded board: Lab 04's SimProc Pmod with faults planted in it.

    labs/common/kicad.sh python3 labs/lab-06-review-a-seeded-board/src/make_seeded.py OUT

It uses Lab 03's generator (labs/lab-03-a-pmod-for-one-projects-pins/src/make_reference.py)
for everything that isn't a fault: the template project, the symbols and footprints, the
netlist, placing footprints, routing and zone fills. Only the schematic, the placements and
the tracks differ from Lab 04's reference board, and they differ only where a fault is.
The faults are listed in labs/lab-06-review-a-seeded-board/solutions/README.md, which a
student shouldn't read before doing the lab. The seeded BRINGUP.md is copied from
data/BRINGUP-seeded.md.

It runs inside the course's pinned KiCad image, because the generator needs kicad-cli and
KiCad's pcbnew Python module.
"""
import json
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.dirname(HERE)
REPO = os.path.dirname(os.path.dirname(LAB))
sys.path.insert(0, os.path.join(REPO, "labs", "lab-03-a-pmod-for-one-projects-pins", "src"))
import make_reference as mr  # noqa: E402

PMOD_Y = mr.PMOD_Y
J3_X = mr.PMOD_X[2] + 0.5                      # 23.36 mm from J2, not 22.86
HDR_FP = "Connector_PinHeader_2.00mm:PinHeader_1x03_P2.00mm_Vertical"
HDR_Y = (66.0, 68.0, 70.0)                     # J4's pins at a 2.00 mm pitch


def schematic(s):
    """Lab 04's schematic (make_reference.schematic, lab "04") with the seeded changes."""
    for ref, y, role, used in (("J1", 50.8, "INPUT socket: ui_in[0..7]", {1: "L:UART_RX"}),
                               ("J2", 101.6, "BIDIR socket: uio[0..7]",
                                {i: f"L:UIO{i - 1}" for i in range(1, 9)}),
                               ("J3", 152.4, "OUTPUT socket: uo_out[0..7]", {1: "L:UART_TX"})):
        s.place(ref, mr.PMOD, 76.2, y, 0, footprint=mr.PMOD_FP)
        for io in range(1, 9):
            s.attach(ref, mr.pmod_pins(io), used.get(io, "NC"))
        for num in ("5", "11"):
            s.attach(ref, num, "P:GND")
        for num in ("6", "12"):
            s.attach(ref, num, "P:+3V3")
        s.text(f"{ref}, {role}", (63.5, y - 20.32))

    s.place("SW1", "Switch:SW_DIP_x08", 165.1, 101.6, 0, value="SW_DIP_x08",
            footprint="Button_Switch_THT:SW_DIP_SPSTx08_Slide_9.78x22.5mm_W7.62mm_P2.54mm")
    for k in range(1, 9):
        net = {7: "UIO7", 8: "UIO6"}.get(k, f"UIO{k - 1}")
        s.attach("SW1", str(k), f"L:{net}")
    s.bus("SW1", [str(n) for n in range(16, 8, -1)], "L:+3V3_PMOD")
    s.text("SW1: uio[7:0] sets SimProc's UART bit period,\nclk_per_bit = uio x 4. A switch that is on reads 1.",
           (152.4, 116.84))
    s.place("RN1", "Device:R_Network08", 165.1, 139.7, 180, value="10k",
            footprint="Resistor_THT:R_Array_SIP9",
            ref_at=(151.13, 138.43, "right"), value_at=(151.13, 140.97, "right"))
    for k in range(2, 10):
        s.attach("RN1", str(k), f"L:UIO{9 - k}")
    s.attach("RN1", "1", "P:GND")
    s.text("RN1: a pull-down on every uio line, so a switch\nthat is off reads 0 rather than floating.",
           (152.4, 152.4))

    s.place("J4", "Connector_Generic:Conn_01x03", 228.6, 50.8, 180, value="USB-UART", footprint=HDR_FP)
    s.attach("J4", "1", "P:GND")
    s.attach("J4", "2", "L:DONGLE_TXD")
    s.attach("J4", "3", "L:DONGLE_RXD")
    s.text("J4: header for a 3.3 V USB-UART dongle.\nPin 2 goes to the dongle's TXD, pin 3 to its RXD.\n"
           "Leave the dongle's VCC unconnected.", (205.74, 60.96))

    s.place("R1", "Device:R", 205.74, 86.36, 90, value="1k", footprint=mr.R_FP)
    s.attach("R1", "1", "L:UART_RX")
    s.place("U1", mr.BUF, 233.68, 86.36, 180, value="74LVC2G17", footprint=mr.SOT6_FP, unit=1,
            ref_at=(233.68, 76.2, None), value_at=(233.68, 78.74, None))
    s.wire(s.points[("R1", "2")][:2], s.points[("U1", "6")][:2])
    s.label("RX_BUF", (210.82, 86.36), 0)
    s.place("R4", "Device:R", 264.16, 82.55, 0, value="100k", footprint=mr.R_FP,
            ref_at=(266.7, 81.28, "left"), value_at=(266.7, 83.82, "left"))
    end, _ = s.stub("R4", "1")
    s.wire(end, (end[0] + 2.54, end[1]))
    s.label("+3V3_PMOD", (end[0] + 2.54, end[1]), 0)
    s.wire(s.points[("U1", "1")][:2], s.points[("R4", "2")][:2])
    s.label("DONGLE_TXD", (250.19, 86.36), 0)
    s.place("U1", mr.BUF, 231.14, 99.06, 180, value="74LVC2G17", footprint=mr.SOT6_FP, unit=2,
            ref_at=(231.14, 109.22, None), value_at=(231.14, 111.76, None))
    s.attach("U1", "4", "L:UART_TX")
    s.place("R2", "Device:R", 261.62, 99.06, 90, value="1k", footprint=mr.R_FP)
    s.wire(s.points[("U1", "3")][:2], s.points[("R2", "1")][:2])
    s.label("TX_BUF", (247.65, 99.06), 0)
    s.attach("R2", "2", "L:DONGLE_RXD")
    s.place("U1", mr.BUF, 264.16, 127.0, 0, value="74LVC2G17", footprint=mr.SOT6_FP, unit=3,
            ref_at=(256.54, 125.73, "right"), value_at=(256.54, 128.27, "right"))
    s.attach("U1", "2", "P:GND")
    s.place("C1", "Device:C", 279.4, 127.0, 0, value="100n", footprint=mr.C_FP,
            ref_at=(276.86, 125.73, "right"), value_at=(276.86, 128.27, "right"))
    vcc, _ = s.stub("U1", "5")
    top, _ = s.stub("C1", "1")
    s.wire(vcc, (top[0], vcc[1]))
    s.wire(top, (top[0], vcc[1]))
    s.wire(vcc, (vcc[0] - 5.08, vcc[1]))
    s.junction(vcc)
    s.label("+3V3_PMOD", (vcc[0] - 5.08, vcc[1]), 180)
    s.attach("C1", "2", "P:GND")
    s.text("U1: two Schmitt-trigger buffers on the kit's 3.3 V,\n"
           "after R3, so the current spy sees U1's current.\n"
           "With the kit off, each pin of U1 passes at most\n"
           "10 uA (Ioff), so the dongle can't power the chip.\n"
           "R1: at most 3.3 V / 1k = 3.3 mA if something\n"
           "drives ui[0] the other way.\n"
           "R2: at most (3.3 - 0.6) V / 1k = 2.7 mA into an\n"
           "unpowered dongle.\n"
           "R4 holds U1's input high with no dongle in J4.\n"
           "C1 decouples U1.", (185.42, 120.65))
    s.place("D1", "Power_Protection:SP0502BAHT", 266.7, 50.8, 0, value="SP0502BAHT",
            ref_at=(271.78, 49.53, "left"), value_at=(271.78, 52.07, "left"))
    s.attach("D1", "1", "L:DONGLE_TXD")
    s.attach("D1", "2", "L:DONGLE_RXD")
    s.attach("D1", "3", "P:GND")
    s.text("D1: ESD protection on the\npins a cable plugs into.", (256.54, 63.5))
    s.place("R3", "Device:R", 215.9, 147.32, 90, value="10", footprint=mr.R_FP)
    s.attach("R3", "1", "P:+3V3")
    s.attach("R3", "2", "L:+3V3_PMOD")
    s.place("TP1", "Connector:TestPoint", 241.3, 152.4, 180, value="TestPoint",
            footprint="TestPoint:TestPoint_Pad_D1.5mm", hide_value=True, ref_at=(243.84, 154.94, "left"))
    s.attach("TP1", "1", "P:+3V3")
    s.place("TP2", "Connector:TestPoint", 254.0, 142.24, 0, value="TestPoint",
            footprint="TestPoint:TestPoint_Pad_D1.5mm", hide_value=True, ref_at=(256.54, 139.7, "left"))
    s.attach("TP2", "1", "L:+3V3_PMOD")
    s.text("R3: a 10 ohm current spy in the Pmod's own supply.\n"
           "The voltage between TP1 and TP2 is 10 ohm x the current.", (198.12, 157.48))

    s.power("+3V3", (25.4, 177.8), 90)
    s.wire((25.4, 177.8), (25.4, 180.34))
    s.flag((25.4, 180.34), 180)
    s.power("GND", (38.1, 182.88), 270)
    s.wire((38.1, 180.34), (38.1, 182.88))
    s.flag((38.1, 180.34), 0)
    s.text("Power enters through the Pmod connectors,\nso PWR_FLAG tells ERC where it comes from.", (45.72, 177.8))
    s.flag((50.8, 190.5), 0)
    s.wire((50.8, 190.5), (55.88, 190.5))
    s.label("+3V3_PMOD", (55.88, 190.5), 0)
    s.text("+3V3_PMOD is fed through R3, a passive part,\nso it needs a PWR_FLAG of its own.", (71.12, 187.96))


C1_AT = (154.5, 63.0)                          # below J3, under its pins 4 and 3
PLACE = dict(mr.PLACE4, **{"J3": (J3_X, PMOD_Y, 90), "C1": (C1_AT[0], C1_AT[1], 90)})
C1_VIA = (156.0, C1_AT[1] - 1.0375)            # GND, beside C1's upper pad


def routes(lab, swapped=False):
    """Lab 04's tracks (make_reference.routes, lab "04"), moved and changed where a fault is."""
    P, S = mr.PWR, mr.SIG
    x1, x2, x3 = mr.PMOD_X[0], mr.PMOD_X[1], J3_X
    r = []
    r.append(("F.Cu", P, [(x1, 53.81), (x1, 51.6), (x2, 51.6), (x3, 51.6), (x3, 53.81)]))
    r.append(("F.Cu", P, [(x2, 51.6), (x2, 53.81)]))
    for x in (x1, x2, x3):
        r.append(("F.Cu", P, [(x, 53.81), (x, PMOD_Y)]))
    # uio[7:4] from J2's upper row, straight down to RN1, except uio7 and uio6, which cross
    # between RN1 and SW1: uio7 on the top layer to SW1 pin 7, uio6 on the bottom to pin 8.
    for x in (135.02, 137.56):
        r.append(("F.Cu", S, [(x, 53.81), (x - 1.27, 55.08), (x - 1.27, 62.5), (x - 1.27, 67.0)]))
    r.append(("F.Cu", S, [(129.94, 53.81), (128.67, 55.08), (128.67, 62.5), (128.67, 63.6),
                          (131.21, 66.14), (131.21, 67.0)]))
    r.append(("F.Cu", S, [(132.48, 53.81), (131.21, 55.08), (131.21, 62.5)]))
    r.append(("B.Cu", S, [(131.21, 62.5), (131.21, 63.6), (128.67, 66.14), (128.67, 67.0)]))
    for x, y in ((129.94, 60.4), (132.48, 59.6), (135.02, 58.8), (137.56, 58.0)):
        r.append(("B.Cu", S, [(x, PMOD_Y), (x, y), (x + 8.89, y), (x + 8.89, 62.5)]))
        r.append(("F.Cu", S, [(x + 8.89, 62.5), (x + 8.89, 67.0)]))
    sw_low = [(146.45 - 2.54 * k, 74.62) for k in range(7, -1, -1)]
    r.append(("F.Cu", P, [(x2, PMOD_Y), (x2, 63.0), (x2, 65.4)]))
    r.append(("F.Cu", P, [(x2, 63.0), (121.5, 63.0)]))
    r.append(("F.Cu", P, [(x2, 67.4), (x2, 70.0), (x2, 74.62)] + sw_low))
    r.append(("F.Cu", P, [(x2, 70.0), (121.5, 70.0)]))
    # ui[0], and R4's +3V3_PMOD under U1 and R1, as on Lab 04's board; J4's pins are 2.00 mm apart.
    r.append(("F.Cu", S, [(114.70, PMOD_Y), (114.70, 60.5)]))
    r.append(("F.Cu", S, [(114.70, 62.5), (119.0, 62.5), (119.0, 63.65)]))
    r.append(("F.Cu", S, [(116.725, 63.65), (113.6, 63.65), (113.6, 67.9025), (112.9625, 68.54),
                          (110.0, HDR_Y[1])]))
    r.append(("F.Cu", S, [(112.4, 62.6), (112.4, 63.65), (113.6, 63.65)]))
    # U1's VCC (pin 5) straight up from TP2's +3V3_PMOD, past the via that takes it to R4,
    # and its GND (pin 2) to a via.
    r.append(("F.Cu", P, [(121.5, 70.0), (121.5, 65.4), (120.7, 64.6), (120.4, 64.6)]))
    r.append(("F.Cu", P, [(119.0, 64.6), (120.4, 64.6)]))
    r.append(("B.Cu", P, [(120.4, 64.6), (115.1, 59.3), (112.4, 59.3)]))
    r.append(("F.Cu", P, [(112.4, 59.3), (112.4, 60.6)]))
    r.append(("F.Cu", P, [(116.725, 64.6), (115.5, 64.6)]))
    # C1 from SW1's +3V3_PMOD common, past the right end of SW1; its other pad to a via.
    c1a, c1b = (C1_AT[0], C1_AT[1] + 1.0375), (C1_AT[0], C1_AT[1] - 1.0375)
    r.append(("F.Cu", P, [sw_low[-1], (150.0, 74.62), (c1a[0], 70.12), c1a]))
    r.append(("F.Cu", P, [c1b, C1_VIA]))
    # uo[0]: J3 pin 1 around the bottom and up the right of R2 to U1's pin 4; pin 3 down to R2,
    # then R2 to a via, and along the bottom layer to J4's pin 3.
    xt = x3 + 12.7
    r.append(("F.Cu", S, [(xt, PMOD_Y), (xt, 79.0), (120.1, 79.0), (120.1, 66.2), (119.0, 65.55)]))
    r.append(("F.Cu", S, [(116.725, 65.55), (118.05, 66.875), (119.0, 67.6)]))
    r.append(("F.Cu", S, [(119.0, 69.6), (119.0, 71.08)]))
    r.append(("B.Cu", S, [(119.0, 71.08), (111.08, 71.08), (110.0, HDR_Y[2])]))
    r.append(("F.Cu", S, [(110.0, HDR_Y[2]), (112.9625, 70.44)]))
    r.append(("F.Cu", S, [(114.8375, 69.49), (116.0, 69.49)]))
    return r


SILK = [s for s in mr.SILK if s[0] not in ("SimProc Pmod", "OUTPUT")] + [("OUTPUT", 154.57, 59.7)]
TITLE_TEXT = ("SimProc Pmod", 106.5, 80.6)


def main():
    out = sys.argv[1]
    if os.path.isdir(out):
        for f in os.listdir(out):
            path = os.path.join(out, f)
            if f.startswith(mr.NAME + ".kicad_") or f.startswith(mr.NAME + "-backups") or \
                    f in ("fp-info-cache", "lib", "fp-lib-table", "sym-lib-table"):
                shutil.rmtree(path) if os.path.isdir(path) else os.remove(path)
    work = tempfile.mkdtemp(prefix="pcb101-seeded-")
    mr.write_template(out)

    sheet = mr.Sheet(work, "SimProc Pmod", "PCB101 Lab 06 board for review")
    schematic(sheet)
    sch = os.path.join(out, mr.NAME + ".kicad_sch")
    sheet.write(sch)
    mr.run(["kicad-cli", "sch", "upgrade", "--force", sch])
    comps, pad_net = mr.netlist(sch, work)

    mr.routes = routes
    # Lab 04's vias, less the one beside C1's old place, one for C1's GND pad, and one at
    # (118, 58) for the piece of the top layer's ground pour that the ring of J1 pin 1, R1,
    # U1, TP2, R3 and J2's +3V3 closes off. On Lab 04's board C1's via is inside that ring;
    # without one, DRC reports a starved_thermal error on J1's pad 11.
    mr.VIAS = {"04": [v for v in mr.VIAS["04"] if v != (122.9375, 64.4)] + [C1_VIA, (118.0, 58.0)]}
    # C1's reference stays with C1, where its footprint puts it, not where Lab 04's board
    # moves it.
    mr.REF_AT["04"] = {k: v for k, v in mr.REF_AT["04"].items() if k != "C1"}
    mr.SILK = SILK
    pcb = os.path.join(out, mr.NAME + ".kicad_pcb")
    mr.build_board(pcb, comps, pad_net, PLACE, "04", True, True)

    # The title legend, smaller and thinner than JLCPCB prints.
    import pcbnew
    board = pcbnew.LoadBoard(pcb)
    t = pcbnew.PCB_TEXT(board)
    t.SetText(TITLE_TEXT[0])
    t.SetPosition(mr.pt(TITLE_TEXT[1], TITLE_TEXT[2]))
    t.SetLayer(pcbnew.F_SilkS)
    t.SetTextSize(pcbnew.VECTOR2I(mr.mm(0.8), mr.mm(0.8)))
    t.SetTextThickness(mr.mm(0.1))
    board.Add(t)
    pcbnew.SaveBoard(pcb, board)

    # The board's text rules relaxed to what its own legend uses. This comes last, because
    # kicad-cli and pcbnew write the project file again whenever they save.
    pro_path = os.path.join(out, mr.NAME + ".kicad_pro")
    with open(pro_path) as f:
        pro = json.load(f)
    pro["board"]["design_settings"]["rules"]["min_text_height"] = 0.8
    pro["board"]["design_settings"]["rules"]["min_text_thickness"] = 0.1
    with open(pro_path, "w") as f:
        json.dump(pro, f, indent=2)
        f.write("\n")

    shutil.copy(os.path.join(LAB, "data", "BRINGUP-seeded.md"), os.path.join(out, "BRINGUP.md"))
    for f in (mr.NAME + ".kicad_prl",):
        if os.path.exists(os.path.join(out, f)):
            os.remove(os.path.join(out, f))
    shutil.rmtree(work, ignore_errors=True)
    print(f"wrote the seeded board into {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
