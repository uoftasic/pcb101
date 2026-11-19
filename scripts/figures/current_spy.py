"""Measuring current: a meter in series, and a sense resistor with two test points (a "current spy").

    python3 scripts/figures/current_spy.py

The right-hand circuit follows Horowitz and Hill, The Art of Electronics, 3rd ed.,
Fig. 10.93 (p. 754): a 10 ohm resistor in series with VDD, with the bypass capacitors
on the board's side of it.
"""
import schemdraw.elements as elm

from circuit_style import drawing, save


def main():
    d = drawing()
    # (a) a meter in series
    d.add(elm.Vdd().label("+3V3"))
    d.add(elm.MeterA().down().label("meter on a\ncurrent range", loc="bottom"))
    d.add(elm.Resistor().down().label("your\nboard", loc="bottom"))
    d.add(elm.Ground())
    d.add(elm.Label().at((0, 1.6)).label("(a)", fontsize=14))

    # (b) a sense resistor with test points
    d.here = (7.0, 0)
    d.add(elm.Vdd().label("+3V3"))
    d.add(elm.Line().down(0.6))
    tp1 = d.add(elm.Dot(open=True).label("TP1", loc="right"))
    d.add(elm.Resistor().down().label("$R_{sense}$\n10 Ω", loc="bottom"))
    tp2 = d.add(elm.Dot(open=True).label("TP2", loc="right"))
    d.add(elm.Line().down(0.5))
    node = d.add(elm.Dot())
    d.push()
    d.add(elm.Line().right(1.6))
    d.add(elm.Capacitor().down().label("bypass\ncapacitors", loc="bottom"))
    d.add(elm.Ground())
    d.pop()
    d.add(elm.Line().right(3.6))
    d.add(elm.Resistor().down().label("your\nboard's\nparts", loc="bottom"))
    d.add(elm.Ground())
    d.add(elm.Line().at(tp1.center).left(1.4))
    m = d.add(elm.MeterV().down().toy(tp2.center).label("meter on\na volts range", loc="top", ofst=0.25))
    d.add(elm.Line().right(1.4).at(m.end))
    d.add(elm.Label().at((7.0, 1.6)).label("(b)", fontsize=14))
    print(save(d, "pcb101-current-spy"))


if __name__ == "__main__":
    main()
