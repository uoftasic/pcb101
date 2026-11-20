"""Supplies, back-powering and ESD: a powered USB-UART dongle driving ui_in[0] of an unpowered kit.

    python3 scripts/figures/back_powering_path.py

(a) A series resistor alone on the line. The path follows the SKY130 breakout as fitted
(breakout-pcb 91a2bf1): the chip's VDD_IO reaches the demo board's +3V3 through the
0 ohm links R13, R8 and R4, so current that the dongle pushes through the pad's upper
clamp lands on the demo board's +3V3 net. On the demo board (tt-demo-pcb bbf3dd1) that
net has the RP2350 (U6), its flash W25Q32 (U7), the output of the TLV1117LV33 regulator
(the demo board's U1), and other parts. The figure leaves out the links' names, because
the Pmod in (b) has its own R4. With 1 kohm, 0.6 V across the diode and VDD_IO at 0 V,
the current is (3.3 - 0.6) V / 1 kohm = 2.7 mA, so the label says "up to about".

(b) Lab 04's reference board (labs/lab-04-protect-and-plan/solutions/simproc-pmod): the
dongle's TXD goes into U1, an SN74LVC2G17, and U1's output goes through R1 (1 kohm) to
ui_in[0]. R4 (100 kohm) pulls TXD up to +3V3, and U1 runs from the same +3V3, the kit's
3.3 V. With the kit off U1 is unpowered. TI's datasheet (SCES381N) gives Ioff as 10 uA
at most, at VCC = 0 V and VI or VO = 5.5 V, so at most 10 uA reaches ui_in[0]. With
+3V3 at 0 V, R4 puts 3.3 V / 100 kohm = 33 uA onto it, so that label says "up to about"
as well.
"""
import schemdraw.elements as elm
import schemdraw.logic as logic

from circuit_style import drawing, save

R_X = 4.3       # where R_S in (a) and R1 in (b) start, so the two line up
PAD_X = 8.6     # where ui_in[0] sits in both panels
RAIL_UP = 1.6   # how far (b)'s +3V3 wire runs above the chip's VDD_IO
Y_A = 9.5       # height of (a)'s signal line; (b)'s is at 0


def wire_to(d, x):
    """A wire right to x. (Line().right(0) would draw a wire of the default length.)"""
    if x - d.here[0] > 1e-6:
        d.add(elm.Line().right(x - d.here[0]))


def chip_and_rail(d, rest_label):
    """From ui_in[0] on: the pad's clamps, VDD_IO, the 0 ohm links and the demo board's +3V3.

    d.here must be at the pad. Returns the upper diode and the corner where the demo
    board's +3V3 turns down into the rest of its load.
    """
    pad = d.add(elm.Dot().label("ui_in[0]", loc="bottom", ofst=(0.75, 0)))
    d.push()
    dn = d.add(elm.Diode().down().reverse().label("$D_2$", loc="bottom"))
    g = d.add(elm.Ground())
    d.pop()
    up = d.add(elm.Diode().up().label("$D_1$", loc="bottom"))
    vio = d.add(elm.Dot().label("VDD_IO", loc="top"))
    d.add(elm.Line().right(2.3))
    d.add(elm.Resistor().right().label("0 Ω links\non the breakout", loc="top"))
    d.add(elm.Dot().label("+3V3", loc="bottom"))
    corner = d.add(elm.Line().right(1.2))
    d.add(elm.Resistor().down().label(rest_label, loc="bottom"))
    d.add(elm.Ground())
    d.add(elm.EncircleBox([pad, up, vio, dn, g], padx=0.6, pady=0.3).linestyle("--")
          .label("the chip, unpowered", loc="bottom", halign="left"))
    return up, corner.end


def main():
    d = drawing()

    # (a) a series resistor alone
    d.here = (0, Y_A)
    d.add(elm.Dot(open=True).label("dongle TX, high:\n3.3 V from the laptop", loc="left"))
    wire_to(d, R_X)
    rs = d.add(elm.Resistor().right().label("$R_S$, 1 kΩ", loc="bottom"))
    wire_to(d, PAD_X)
    up_a, _ = chip_and_rail(d, "the rest of the\ndemo board's +3V3:\nthe RP2350, its flash,\n"
                               "the TLV1117LV33's\noutput, and more")
    d.add(elm.CurrentLabel(top=True, ofst=0.45, length=1.4).at(rs).label("$I$, up to\nabout 2.7 mA"))
    d.add(elm.CurrentLabel(top=False, ofst=0.6, length=1.4).at(up_a).label("$I$"))
    d.add(elm.Label().at((0, Y_A + 3.4)).label("(a)", fontsize=14))

    # (b) Lab 04's board: U1 between the dongle and R1, R4 pulling the dongle's TX up
    d.here = (0, 0)
    d.add(elm.Dot(open=True).label("dongle TX, high:\n3.3 V from the laptop", loc="left"))
    d.add(elm.Line().right(1.0))
    d.add(elm.Dot())
    d.push()
    r4 = d.add(elm.Resistor().up().label("R4\n100 kΩ", loc="bottom"))
    rail_l = d.add(elm.Line().up(RAIL_UP)).end
    d.pop()
    d.add(elm.Line().right(0.8))
    u1 = d.add(logic.Schmitt().right().label("U1, 74LVC2G17,\nunpowered", loc="bottom", ofst=0.25))
    wire_to(d, R_X)
    r1 = d.add(elm.Resistor().right().label("R1, 1 kΩ", loc="bottom"))
    wire_to(d, PAD_X)
    _, corner = chip_and_rail(d, "the rest of the\ndemo board's +3V3")
    # R4's top and U1's VCC are on the kit's +3V3, the net the links feed
    d.add(elm.Dot().at(corner))
    d.add(elm.Line().at(corner).up(RAIL_UP))
    d.add(elm.Line().tox(rail_l[0]))
    vcc_x = u1.absanchors["in1"][0] + 0.25   # a point on the triangle's upper edge
    d.add(elm.Dot().at((vcc_x, rail_l[1])))
    d.add(elm.Line().at((vcc_x, rail_l[1])).down(rail_l[1] - 0.32))
    d.add(elm.Label().at((vcc_x + 0.12, 1.0)).label("VCC", halign="left"))
    d.add(elm.Label().at((rail_l[0] + 0.15, rail_l[1] + 0.35)).label("+3V3", halign="left"))
    d.add(elm.CurrentLabel(top=True, ofst=0.45, length=1.4).at(r4).label("up to about\n33 µA"))
    d.add(elm.CurrentLabel(top=True, ofst=0.45, length=1.4).at(r1).label("at most 10 µA\n($I_{off}$)"))
    d.add(elm.Label().at((0, 5.2)).label("(b)", fontsize=14))
    print(save(d, "pcb101-back-powering-path"))


if __name__ == "__main__":
    main()
