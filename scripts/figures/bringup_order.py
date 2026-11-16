"""Bringing up a chip: the order of a first power-up, each step with the reading you expect.

    pip install -r scripts/figures/requirements.txt
    python3 scripts/figures/bringup_order.py    # writes docs/assets/img/ic103-bringup-order.svg

The steps are the ones an IC103 BRINGUP.md covers (Lab 04): checks before power, a current
limit, a known firmware mode, project select, clock and reset, a first functional test, and
only then anything with a supply of its own. The right-hand column is what you write down
before each step.
"""
import schemdraw.elements as elm
import schemdraw.flow as flow

from circuit_style import drawing, save

TEXT_DROP = 0.11    # schemdraw puts the baseline on y; this centres the letters on it instead
NOTE = 11
STEP_W, STEP_H = 6.0, 1.15
ROW = 1.75
X_STEP, X_NOTE = 0.0, 3.7     # step boxes centred on X_STEP; notes start at X_NOTE

STEPS = [
    ("1  Unpowered checks", "rail-to-ground resistance: no short"),
    ("2  Kit alone, current-limited", "supply current within your written range"),
    ("3  Firmware in a known mode", "the mode and switch positions you assumed"),
    ("4  Select the project", "the firmware reports it enabled"),
    ("5  Clock, then reset", "clock running; rst_n held low, then released"),
    ("6  First functional test", "the output your design note predicts"),
    ("7  Connect powered things last", "such as a USB-UART dongle, once the kit is up"),
]


def text(d, xy, s, halign="center", size=None):
    """Text at xy. right() stops it inheriting the last element's direction."""
    d.add(elm.Label().right().at((xy[0], xy[1] - TEXT_DROP)).label(s, halign=halign, fontsize=size))


d = drawing()
d.config(margin=0.3)

text(d, (X_STEP, 1.2), "step", size=12)
text(d, (X_NOTE + 0.4, 1.2), "the reading you wrote down beforehand", halign="left", size=12)

boxes = []
for k, (step, note) in enumerate(STEPS):
    y = -k * ROW
    b = d.add(flow.Box(w=STEP_W, h=STEP_H).anchor("center").at((X_STEP, y))
              .label(step, fontsize=12))
    if boxes:
        d.add(elm.Arrow().at(boxes[-1].S).to(b.N))
    boxes.append(b)
    d.add(elm.Line().at(b.E).to((X_NOTE + 0.25, y)).linestyle(":"))
    text(d, (X_NOTE + 0.4, y), note, halign="left", size=NOTE)

# Any reading that doesn't match sends you back off the bench, not on to the next step.
y_bottom = -(len(STEPS) - 1) * ROW
text(d, (X_STEP - STEP_W / 2, y_bottom - 1.4),
     "At any step, a reading that doesn't match: power off first, then find out why.",
     halign="left", size=NOTE)

print(save(d, "ic103-bringup-order"))
