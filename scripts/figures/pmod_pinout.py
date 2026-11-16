"""Pins, Pmods and planning a pinout: the demo board's three I/O Pmod sockets, with SimProc's pins.

Reads Tiny Tapeout's demo board (tt-demo-pcb at the commit in labs/common/upstream.json),
so fetch the boards first:

    python3 labs/common/fetch_boards.py
    python3 scripts/figures/pmod_pinout.py

Every pad is drawn where the board file puts it, seen from above, and labelled with the
net the board file gives it. SimProc's pin list is from its info.yaml and its top-level
RTL (uoftasic/simproc at 1d97772): ui[0] uart rx, uo[0] uart tx, uo[1] halt flag,
uo[2] done flag, uio[0..7] clk per bit, all eight uio pins inputs (uio_oe = 0).
"""
import os
import re

from matplotlib.patches import Circle, FancyArrowPatch, Rectangle

from kicad_sexpr import find, get, net_names, pad_position, parse, prop
from plot_style import ACCENT, GREY, INK, REPO, figure, save

BOARD = os.path.join(REPO, "labs", "common", "upstream", "tt-demo-pcb", "tinytapeout-demo.kicad_pcb")

SIMPROC = {
    "ui_in[0]": "uart rx",
    "uo_out[0]": "uart tx",
    "uo_out[1]": "halt",
    "uo_out[2]": "done",
}
SIMPROC.update({f"uio[{i}]": f"clk_per_bit[{i + 2}]" for i in range(8)})

TITLES = {"ui_in": "inputs", "uio": "bidirectional", "uo_out": "outputs"}


def tidy(net):
    """'/ui_in4' or 'ui_in4' -> 'ui_in[4]'; power nets unchanged."""
    m = re.fullmatch(r"/?(ui_in|uo_out|uio)(\d)", net)
    return f"{m.group(1)}[{m.group(2)}]" if m else net


def main():
    board = parse(open(BOARD, encoding="utf-8").read())
    name_of = net_names(board)
    sockets = []
    for fp in find(board, "footprint"):
        if "PMODHost" not in fp[1]:
            continue
        pads = []
        for pad in find(fp, "pad"):
            pads.append((pad[1], tidy(name_of(get(pad, "net"))), pad_position(fp, pad)))
        bus = next(re.match(r"(ui_in|uo_out|uio)", n).group(1) for _, n, _ in pads
                   if re.match(r"(ui_in|uo_out|uio)", n))
        x0 = float(get(fp, "at")[1])
        sockets.append((x0, prop(fp, "Reference"), bus, pads))
    sockets.sort()
    assert len(sockets) == 3, sockets

    fig, ax = figure(7.6, 4.8)
    ys = sorted({round(p[2][1], 2) for s in sockets for p in s[3]})
    y_top, y_bot = ys[0], ys[-1]
    for x0, ref, bus, pads in sockets:
        xs = [p[2][0] for p in pads]
        ax.add_patch(Rectangle((min(xs) - 1.5, y_top - 1.5), max(xs) - min(xs) + 3, y_bot - y_top + 3,
                               fill=False, ec=GREY, lw=0.8))
        for num, net, (x, y) in pads:
            used = net in SIMPROC
            colour = ACCENT if used else (INK if net in ("GND", "+3V3") else GREY)
            if num == "1":
                ax.add_patch(Rectangle((x - 0.8, y - 0.8), 1.6, 1.6, fc=colour, ec=colour))
            else:
                ax.add_patch(Circle((x, y), 0.8, fc=colour, ec=colour))
            ax.text(x, y, num, ha="center", va="center", fontsize=5.5, color="white")
            label = net + (f": {SIMPROC[net]}" if used else "")
            weight = "bold" if used else "normal"
            if abs(y - y_top) < 0.01:
                ax.text(x, y - 1.3, label, rotation=90, ha="center", va="bottom", fontsize=6.5,
                        color=colour, fontweight=weight)
            else:
                ax.text(x, y + 1.3, label, rotation=90, ha="center", va="top", fontsize=6.5,
                        color=colour, fontweight=weight)
        ax.text((min(xs) + max(xs)) / 2, y_top - 21, f"{ref}: {bus} ({TITLES[bus]})",
                ha="center", va="bottom", fontsize=9)

    centres = [s[0] for s in sockets]
    for a, b in zip(centres, centres[1:]):
        y = y_bot + 20
        ax.add_patch(FancyArrowPatch((a, y), (b, y), arrowstyle="<->", mutation_scale=8, lw=0.8, color=INK))
        ax.text((a + b) / 2, y + 0.6, f"{b - a:.2f} mm, pin 1 to pin 1", ha="center", va="top", fontsize=8)
        for x in (a, b):
            ax.plot([x, x], [y_bot + 15.5, y + 1.0], color=GREY, lw=0.5, ls=(0, (2, 2)))

    ax.set_xlim(centres[0] - 16, centres[-1] + 4)
    ax.set_ylim(y_bot + 24, y_top - 24)  # y down, as in KiCad
    ax.set_aspect("equal")
    ax.axis("off")
    print(save(fig, "ic103-pmod-pinout-simproc"))


if __name__ == "__main__":
    main()
