"""From die to package: how a die's bond pads reach a QFN's leads, and the QFN on a board.

A sketch, not to scale. Left: a quarter of a die and its pad ring, with bond wires out to the
package's leads (on a chip-on-board module the wires land on bond pads on the PCB instead).
Right: a cut through a QFN soldered to a board. The two bonding rules marked on the left are
wafer.space's (github.com/wafer-space/chip-on-board-wire-bonded-pcbs, run-1/wirebonding/README.md
at 5cb4668): no crossing wires, and no wire more than 45 degrees off straight.

    python3 scripts/figures/qfn_package.py     # writes docs/assets/img/pkg-die-to-qfn.svg
"""
import os

import circuit_style  # noqa: F401  (sets the course's matplotlib defaults)
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle

plt.rcParams["font.family"] = "serif"
OUT = os.path.join(circuit_style.IMG_DIR, "pkg-die-to-qfn.svg")
COPPER, DIE, MOLD, BOARD, WIRE = "#c8553d", "#9aa7b8", "#3b3b3b", "#6d8f4e", "#d4a017"

fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 5.2), gridspec_kw={"width_ratios": [1, 1.4]})
for a in (a1, a2):
    a.axis("off")
a1.set_aspect("equal")
a2.set_aspect(2.2)   # the cut is drawn twice as tall as it is wide, so the layers show

# Left: top view of one corner. The die is at the lower left; leads run up the right edge.
a1.add_patch(Rectangle((0, 0), 4.2, 4.2, fc=DIE, ec="black", lw=0.8))
a1.text(1.6, 1.4, "die", fontsize=12, ha="center")
pads = [(4.0, 0.4 + 0.45 * k) for k in range(8)]           # bond pads along the die's right edge
leads = [(7.4, -0.9 + 0.8 * k) for k in range(8)]          # package leads, at a wider pitch
for (px, py), (lx, ly) in zip(pads, leads):
    a1.add_patch(Rectangle((px - 0.13, py - 0.13), 0.26, 0.26, fc="#e8e8e8", ec="black", lw=0.6))
    a1.add_patch(Rectangle((lx, ly - 0.17), 1.1, 0.34, fc=COPPER, ec="none"))
    a1.plot([px, lx + 0.15], [py, ly], color=WIRE, lw=1.4)
a1.add_patch(Rectangle((-0.3, -1.4), 9.1, 7.3, fc="none", ec="#777777", lw=0.8, ls=(0, (4, 3))))
a1.text(0.2, 4.55, "pad ring: bond pads at the die's edge", fontsize=10)
a1.text(8.6, 5.55, "leads", fontsize=10, ha="right")
a1.text(5.5, -1.15, "bond wires", fontsize=10, ha="center", color="#8a6a00")
a1.text(-0.2, 6.15, "package outline", fontsize=9.5, color="#555555")
a1.text(0.0, -2.2, "Wires may not cross, and none may run\nmore than 45° away from straight out.",
        fontsize=10, va="top")
a1.set_xlim(-0.6, 9.2)
a1.set_ylim(-3.3, 6.6)

# Right: a cut through the package and the board under it.
a2.add_patch(Rectangle((0, -1.6), 12, 1.6, fc=BOARD, ec="none"))                 # board
a2.text(6, -1.15, "board", fontsize=11, ha="center", color="white")
for x0, w in ((0.9, 1.4), (9.7, 1.4)):
    a2.add_patch(Rectangle((x0, 0), w, 0.18, fc=COPPER, ec="none"))               # lands
a2.add_patch(Rectangle((3.0, 0), 6.0, 0.18, fc=COPPER, ec="none"))               # EP land
for x in (3.6, 4.8, 6.0, 7.2, 8.4):
    a2.add_patch(Rectangle((x - 0.12, -1.6), 0.24, 1.6, fc="#b8b8b8", ec="none"))  # thermal vias
a2.add_patch(Rectangle((0.9, 0.18), 1.4, 0.22, fc="#c0c0c0", ec="none"))         # solder
a2.add_patch(Rectangle((9.7, 0.18), 1.4, 0.22, fc="#c0c0c0", ec="none"))
for x0, w in ((3.3, 1.6), (5.2, 1.6), (7.1, 1.6)):                                # EP solder, in windows
    a2.add_patch(Rectangle((x0, 0.18), w, 0.22, fc="#c0c0c0", ec="none"))
a2.add_patch(Polygon([(1.0, 0.4), (11.0, 0.4), (11.0, 2.6), (1.0, 2.6)], fc=MOLD, ec="none"))
a2.add_patch(Rectangle((1.0, 0.4), 1.2, 0.3, fc=COPPER, ec="none"))               # leads
a2.add_patch(Rectangle((9.8, 0.4), 1.2, 0.3, fc=COPPER, ec="none"))
a2.add_patch(Rectangle((3.1, 0.4), 5.8, 0.3, fc=COPPER, ec="none"))               # die pad
a2.add_patch(Rectangle((3.5, 0.7), 5.0, 0.55, fc=DIE, ec="black", lw=0.6))        # die
for xs, xe in ((3.7, 1.7), (8.3, 10.3)):
    xm = (xs + xe) / 2
    a2.plot([xs, xm, xe], [1.25, 1.95, 0.7], color=WIRE, lw=1.4)
a2.text(6.0, 0.86, "die", fontsize=10, ha="center")
a2.text(6.0, 2.15, "mould compound", fontsize=10, ha="center", color="white")
notes = [((1.6, 0.55), (0.2, 3.3), "lead"),
         ((2.75, 1.6), (2.2, 4.3), "bond wire"),
         ((6.0, 0.55), (5.2, 3.6), "die pad: the exposed pad"),
         ((10.4, 0.29), (12.3, 3.2), "solder on the land"),
         ((7.2, -0.8), (12.3, -1.9), "thermal vias"),
         ((5.8, 0.29), (12.3, 1.5), "solder paste in windows")]
for (x, y), (tx, ty), s in notes:
    a2.annotate(s, (x, y), (tx, ty), fontsize=10, ha="left" if tx > 6 else "left",
                arrowprops=dict(arrowstyle="-", lw=0.6, color="black"))
a2.set_xlim(-0.3, 16.5)
a2.set_ylim(-2.4, 4.6)

fig.savefig(OUT, format="svg", transparent=False, facecolor="white", bbox_inches="tight",
            pad_inches=0.05, metadata={"Date": None})
print(OUT)
