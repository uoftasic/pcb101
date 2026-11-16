"""What a board does for a chip: the parts of a Tiny Tapeout devkit and where a Pmod plugs in.

Every label comes from Tiny Tapeout's own sources, as the page that shows this figure cites them:
the tt-demo-pcb README and board file (bbf3dd1), the ETR demo board guide and the FAQ.

    python3 scripts/figures/devkit_blocks.py     # writes docs/assets/img/tt-devkit-blocks.svg
"""
import os

import circuit_style  # noqa: F401  (sets the course's matplotlib defaults)
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

OUT = os.path.join(circuit_style.IMG_DIR, "tt-devkit-blocks.svg")
INK = "black"
SOFT = "#eef2f7"   # fill for the boards
PART = "white"     # fill for the parts on them


def box(ax, x, y, w, h, title, lines=(), fill=PART, size=10.5, bold=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.12",
                                fc=fill, ec=INK, lw=1.1))
    ax.text(x + w / 2, y + h - 0.28, title, ha="center", va="top", fontsize=size,
            family="serif", weight="bold" if bold else "normal")
    for k, s in enumerate(lines):
        ax.text(x + w / 2, y + h - 0.68 - 0.36 * k, s, ha="center", va="top", fontsize=9,
                family="serif")


def arrow(ax, p, q, both=False, label=None, off=(0, 0.15), ha="center"):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="<|-|>" if both else "-|>",
                                 mutation_scale=11, lw=1.1, color=INK))
    if label:
        ax.text((p[0] + q[0]) / 2 + off[0], (p[1] + q[1]) / 2 + off[1], label, ha=ha,
                va="bottom", fontsize=9, family="serif")


fig, ax = plt.subplots(figsize=(11, 5.6))
ax.set_xlim(0, 18.2)
ax.set_ylim(0, 9.1)
ax.axis("off")

# The demo board and what is on it.
box(ax, 0.3, 0.3, 11.6, 8.5, "Demo board: 85 × 85 mm, 4 copper layers", fill=SOFT, size=11.5, bold=True)
box(ax, 0.7, 5.6, 3.4, 2.3, "USB-C", ["5 V in", "3.3 V regulator"])
box(ax, 4.4, 5.6, 3.6, 2.3, "RP2350", ["selects the project,", "usually drives the clock,",
                                      "can drive or read pins"])
box(ax, 8.3, 5.6, 3.2, 2.3, "Analog header", ["100 mil; each line", "pulled down by 10 MΩ"])
box(ax, 0.7, 2.9, 3.4, 2.2, "8 DIP switches", ["each one: ui_in to", "3.3 V through 1 kΩ"])
box(ax, 4.4, 2.9, 3.6, 2.2, "7-segment display", ["each uo_out lights one", "segment through 510 Ω"])
box(ax, 8.3, 2.9, 3.2, 2.2, "DF12 sockets", ["60 + 50 pins: power", "and every chip signal"])
box(ax, 0.7, 0.6, 10.8, 1.8, "Three I/O Pmods, 22.86 mm apart",
    ["ui_in[7:0]    ·    uio[7:0]    ·    uo_out[7:0]"])

# The breakout, plugged into the demo board's sockets.
box(ax, 13.3, 4.0, 4.6, 4.0, "Breakout: 50 × 50 mm, 4 layers", fill=SOFT, size=10, bold=True)
box(ax, 13.7, 4.3, 3.8, 2.6, "The chip", ["QFN-64 (SKY130)", "and the parts that", "make its supplies"])
arrow(ax, (11.5, 4.0), (13.3, 5.0), both=True)
ax.text(12.4, 3.55, "two Hirose DF12\nconnectors", ha="center", va="top", fontsize=9, family="serif")

# A board of your own, on the Pmods.
box(ax, 13.3, 0.6, 4.6, 2.4, "Your Pmod board (Lab 03)", ["the parts one project", "needs that the demo", "board doesn't have"])
arrow(ax, (11.5, 1.5), (13.3, 1.5), both=True)

fig.savefig(OUT, format="svg", transparent=False, facecolor="white", bbox_inches="tight",
            pad_inches=0.05, metadata={"Date": None})
print(OUT)
