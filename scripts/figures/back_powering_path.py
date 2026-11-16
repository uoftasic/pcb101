"""Supplies, back-powering and ESD: a powered USB-UART dongle driving ui_in[0] of an unpowered kit.

    python3 scripts/figures/back_powering_path.py

The path follows the SKY130 breakout as fitted (breakout-pcb 91a2bf1): the chip's VDD_IO
reaches the demo board's +3V3 through the 0 ohm links R13, R8 and R4, so current that
the dongle pushes through the pad's upper clamp lands on the demo board's +3V3 net. On
the demo board (tt-demo-pcb bbf3dd1) that net has the RP2350 (U6), its flash W25Q32
(U7), the output of the TLV1117LV33 regulator (U1), and other parts.
"""
import schemdraw.elements as elm

from circuit_style import drawing, save


def main():
    d = drawing()
    d.add(elm.Dot(open=True).label("dongle TX, high:\n3.3 V from the laptop", loc="left"))
    rs = d.add(elm.Resistor().right().label("$R_S$ (Lab 04)", loc="top"))
    d.add(elm.Line().right(1.2))
    pad = d.add(elm.Dot().label("ui_in[0]", loc="bottom", ofst=(0.75, 0)))
    d.push()
    dn = d.add(elm.Diode().down().reverse().label("$D_2$", loc="bottom"))
    g = d.add(elm.Ground())
    d.pop()
    up = d.add(elm.Diode().up().label("$D_1$", loc="bottom"))
    vio = d.add(elm.Dot().label("VDD_IO", loc="left"))
    d.add(elm.Line().right(1.5))
    d.add(elm.Resistor().right().label("0 Ω links\nR13, R8, R4", loc="top"))
    d.add(elm.Dot().label("+3V3", loc="bottom"))
    d.add(elm.Line().right(1.2))
    d.add(elm.Resistor().down().label("the rest of the\ndemo board's +3V3:\nthe RP2350, its flash,\nthe TLV1117LV33's\noutput, and more", loc="bottom"))
    d.add(elm.Ground())
    d.add(elm.CurrentLabel(top=False, ofst=0.45, length=1.4).at(rs).label("$I$", loc="bottom"))
    d.add(elm.CurrentLabel(top=False, ofst=0.45, length=1.4).at(up).label("$I$"))
    d.add(elm.EncircleBox([pad, up, vio, dn, g], padx=0.75, pady=0.3).linestyle("--")
          .label("the chip, unpowered", loc="bottom", halign="left"))
    print(save(d, "ic103-back-powering-path"))


if __name__ == "__main__":
    main()
