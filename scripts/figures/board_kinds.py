"""Boards for chips: where each kind of board attaches, from the chip outwards.

    pip install -r scripts/figures/requirements.txt
    python3 scripts/figures/board_kinds.py      # writes docs/assets/img/pb101-board-kinds.svg

Every connection drawn here is one the course names a source for: the DF12 pair and the
power they carry (Tiny Tapeout's SKY130 breakout, rev 3.2, at breakout-pcb 91a2bf1), the
demo board's I/O Pmods and analog header (tt-demo-pcb README at bbf3dd1), Tiny Tapeout's
DIP carrier and DIP dock (breakout-pcb 91a2bf1), and wafer.space's chip-on-board breakout
and its 70-pin 0.4 mm mezzanine connector (wafer-space/chip-on-board-wire-bonded-pcbs).
"""
import schemdraw.elements as elm
import schemdraw.flow as flow

from circuit_style import drawing, save

TEXT_DROP = 0.11    # schemdraw puts the baseline on y; this centres the letters on it instead
NOTE = 11           # font size for the labels on the connections
BOX_W, BOX_H = 4.8, 1.25
X_CARRIER, X_HOST, X_YOURS = 0.0, 8.6, 17.2   # box centres, one column each
ROW = 1.95          # distance between rows


def text(d, xy, s, halign="center", size=None, color="black"):
    """Text at xy. right() stops it inheriting the last element's direction."""
    d.add(elm.Label().right().at((xy[0], xy[1] - TEXT_DROP))
          .label(s, halign=halign, fontsize=size, color=color))


def box(d, x, y, label, dashed=False):
    b = flow.Box(w=BOX_W, h=BOX_H).anchor("center").at((x, y)).label(label, fontsize=12)
    if dashed:
        b = b.linestyle("--")
    return d.add(b)


def link(d, a, b, label, below=None):
    """An arrow from box a to box b with a label above it, and optionally one below."""
    d.add(elm.Arrow().at(a.E).to(b.W))
    mid = ((a.E[0] + b.W[0]) / 2, a.E[1])
    text(d, (mid[0], mid[1] + 0.3), label, size=NOTE)
    if below:
        text(d, (mid[0], mid[1] - 0.32), below, size=NOTE)


d = drawing()
d.config(margin=0.3)

# Column headings
for x, head in ((X_CARRIER, "carries the chip"), (X_HOST, "powers and drives it"),
                (X_YOURS, "the board you design")):
    text(d, (x, 1.25), head, size=12)

# 1. The devkit, with a Pmod on the demo board (Labs 03 and 04, Brief D)
y = 0.0
brk = box(d, X_CARRIER, y, "SKY130 breakout\nchip in a QFN-64")
demo = box(d, X_HOST, y, "Demo board\nRP2350, Pmods")
pmod = box(d, X_YOURS, y, "Pmod board\nLabs 03 and 04, Brief D")
link(d, brk, demo, "two DF12 connectors", "60 + 50 pins")
link(d, demo, pmod, "three I/O Pmods", "22.86 mm apart")

# 2. An analog source board on the demo board's analog header (Brief A)
y = -ROW
src = box(d, X_YOURS, y, "Analog source board\nBrief A")
d.add(elm.Line().at(demo.S).to((X_HOST, y)))
d.add(elm.Arrow().at((X_HOST, y)).to(src.W))
text(d, ((X_HOST + src.W[0]) / 2 + 0.6, y + 0.3), "100 mil analog header", size=NOTE)

# 3. A motherboard in place of the demo board
y = -2 * ROW
mb = box(d, X_YOURS, y, "Motherboard\ninstead of the demo board", dashed=True)
d.add(elm.Line().at(brk.S).to((X_CARRIER, y)))
d.add(elm.Arrow().at((X_CARRIER, y)).to(mb.W))
text(d, (X_HOST, y + 0.3), "the same two DF12 connectors", size=NOTE)
text(d, (X_HOST, y - 0.32), "power on them: +3V3, +5V and GND only", size=NOTE)

# 4. Chips from other shuttles: Tiny Tapeout's GF180 DIP carrier, and wafer.space's COB
y = -3 * ROW - 0.35
dip = box(d, X_CARRIER, y, "GF180 DIP carrier\nchip-on-board")
dock = box(d, X_HOST, y, "DIP dock\n2 layers")
yours_dip = box(d, X_YOURS, y, "a board of yours\non the dock's Pmods", dashed=True)
link(d, dip, dock, "32-pin DIP")
link(d, dock, yours_dip, "three Pmod sockets")

y = -4 * ROW - 0.35
cob = box(d, X_CARRIER, y, "wafer.space COB\nmodule, 14 × 16 mm")
mb2 = box(d, X_YOURS, y, "Motherboard\nfor the COB module", dashed=True)
d.add(elm.Arrow().at(cob.E).to(mb2.W))
text(d, (X_HOST, y + 0.3), "70-pin mezzanine connector", size=NOTE)
text(d, (X_HOST, y - 0.32), "0.4 mm pitch", size=NOTE)

# Legend
text(d, (X_CARRIER - BOX_W / 2, y - 1.35), "Dashed boxes: boards this course doesn't have you design.",
     halign="left", size=NOTE)

print(save(d, "pb101-board-kinds"))
