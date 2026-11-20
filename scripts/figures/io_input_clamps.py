"""Protecting the chip's I/O: a series resistor in front of a chip input and its clamp diodes.

    python3 scripts/figures/io_input_clamps.py

D1 and D2 stand for the pad's diodes. SkyWater's sky130_fd_io user guide says its GPIO
cells "use the main Vddio/Vssio connections for their ESD current steering diodes". When
the pad is more than a diode drop above VDDIO, D1 conducts and R_S sets the current I.
The same guide allows a pin to be taken above vddio or below vssd_io only if the current
into or out of it is limited to 100 uA, so the label on I gives that limit. The chip's
input is labelled its input stage, because the page uses "buffer" for a part on your
board (Lab 04's U1, a 74LVC2G17).
"""
import schemdraw.elements as elm
import schemdraw.logic as logic

from circuit_style import drawing, save


def main():
    d = drawing()
    d.add(elm.Dot(open=True).label("another board's\noutput, $V_{drive}$", loc="left"))
    rs = d.add(elm.Resistor().right().label("$R_S$, on your board", loc="top"))
    d.add(elm.Line().right(2.2))
    pad = d.add(elm.Dot().label("pad", loc="bottom", ofst=(0.45, 0)))
    d.push()
    up = d.add(elm.Diode().up().label("$D_1$", loc="bottom"))
    vdd = d.add(elm.Vdd().label("$V_{DDIO}$"))
    d.pop()
    d.push()
    dn = d.add(elm.Diode().down().reverse().label("$D_2$", loc="bottom"))
    g1 = d.add(elm.Ground())
    d.pop()
    d.add(elm.Line().right(2))
    d.push()
    c = d.add(elm.Capacitor().down().label("$C_{in}$", loc="bottom"))
    g2 = d.add(elm.Ground())
    d.pop()
    d.add(elm.Line().right(1))
    buf = d.add(logic.Buf().right().label("input\nstage", loc="top", ofst=0.3))
    d.add(elm.CurrentLabel(top=False, ofst=0.6, length=1.4).at(up).label("$I$"))
    d.add(elm.CurrentLabel(top=False, ofst=0.45, length=1.4).at(rs)
          .label("$I$: past a rail,\nSkyWater allows\nat most 100 µA", loc="bottom"))
    d.add(elm.EncircleBox([pad, up, vdd, dn, g1, c, g2, buf], padx=0.6, pady=0.3).linestyle("--")
          .label("the chip", loc="top", halign="left"))
    print(save(d, "pcb101-io-input-clamps"))


if __name__ == "__main__":
    main()
