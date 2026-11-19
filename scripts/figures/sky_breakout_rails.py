"""Supplies, back-powering and ESD: where each of the chip's supplies comes from on the SKY130 breakout.

    python3 scripts/figures/sky_breakout_rails.py

Drawn from Tiny Tapeout's breakout-pcb/breakout-sky-qfn (rev 3.2) at 91a2bf1, parsed
pad by pad. Fitted parts: R2, U1 (AP2112K-1.8) and R14 make VCCD from +3V3; R4 and R8
take +3V3 to VDD_REG past U2's empty place; R13 and R15 tie VDD_IO and VDDA to it.
U2 and the header J2 carry the dnp attribute. Capacitors per net, from their pads:
/VCIN C6 10 uF; /VDIN C7 10 uF; VCC_REG C18 1 uF, C21 100 nF; VDD_REG C19 1 uF,
C22 100 nF; VCCD C1 C3 C5 1 uF, C20 C23 C24 100 nF; VDD_IO C2 C4 1 uF, C16 C17
C25 100 nF; VDDA C8 C10 C12 C14 1 uF, C9 C11 C13 C15 100 nF. J2's pads reach VCCD,
VDD_IO, VDDA, VCC_REG and VDD_REG (and GND and three other signals).
"""
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

from plot_style import ACCENT, GREY, INK, figure, save

W, H = 3.2, 1.5
XS = [0, 4.0, 8.0, 12.0, 16.0, 20.0]
TOP, MID, LOW = 4.4, 1.0, -1.1


def box(ax, x, y, title, lines=(), dashed=False, colour=INK):
    edge = GREY if dashed else colour
    ax.add_patch(FancyBboxPatch((x - W / 2, y - H / 2), W, H, boxstyle="round,pad=0.04",
                                fill=False, ec=edge, lw=1.0, ls=(0, (3, 2)) if dashed else "-"))
    ax.text(x, y + 0.4, title, ha="center", va="center", fontsize=7.5, fontweight="bold", color=edge)
    for k, line in enumerate(lines):
        ax.text(x, y - 0.1 - 0.36 * k, line, ha="center", va="center", fontsize=6.8,
                color=GREY if dashed else INK)


def arrow(ax, a, b, dashed=False):
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle="-|>", mutation_scale=8, lw=0.9,
                                 color=GREY if dashed else INK, ls=(0, (3, 2)) if dashed else "-",
                                 shrinkA=0, shrinkB=0))


def main():
    fig, ax = figure(9.5, 4.3)
    e = W / 2 + 0.06

    box(ax, XS[0], MID, "+3V3", ["from the demo", "board, via J1, J3"])
    box(ax, XS[1], TOP, "R2, 0 Ω", ["/VCIN: 10 µF"])
    box(ax, XS[2], TOP, "U1", ["AP2112K-1.8"], colour=ACCENT)
    box(ax, XS[3], TOP, "VCC_REG", ["1 µF, 100 nF"])
    box(ax, XS[4], TOP, "R14, 0 Ω", ["0805"])
    box(ax, XS[5], TOP, "VCCD, 1.8 V", ["3 × 100 nF", "3 × 1 µF"], colour=ACCENT)

    box(ax, XS[1], MID, "R4, 0 Ω", ["/VDIN: 10 µF"])
    box(ax, XS[2], MID, "R8, 0 Ω", ["in U2's place"])
    box(ax, XS[2], (TOP + MID) / 2, "U2", ["not fitted"], dashed=True)
    box(ax, XS[3], MID, "VDD_REG", ["1 µF, 100 nF"])
    box(ax, XS[4], MID, "R13, 0 Ω", ["0805"])
    box(ax, XS[5], MID, "VDD_IO, 3.3 V", ["3 × 100 nF", "2 × 1 µF"], colour=ACCENT)
    box(ax, XS[4], LOW, "R15, 0 Ω", ["0805"])
    box(ax, XS[5], LOW, "VDDA, 3.3 V", ["4 × 100 nF", "4 × 1 µF"], colour=ACCENT)

    arrow(ax, (XS[0] + e, MID + 0.3), (XS[1] - e, TOP))
    arrow(ax, (XS[0] + e, MID), (XS[1] - e, MID))
    for row in (TOP, MID):
        for a, b in zip(XS[1:5], XS[2:6]):
            arrow(ax, (a + e, row), (b - e, row))
    arrow(ax, (XS[3] + e, MID - 0.3), (XS[4] - e, LOW))
    arrow(ax, (XS[4] + e, LOW), (XS[5] - e, LOW))

    j2 = XS[5] + 4.2
    box(ax, j2, MID, "J2", ["not fitted:", "1 × 12 header"], dashed=True)
    for row in (TOP, MID, LOW):
        arrow(ax, (XS[5] + e, row), (j2 - e, MID + (row - MID) * 0.3), dashed=True)

    ax.text(XS[0] - W / 2, LOW - 0.1, "U4, the chip, gets VCCD, VDD_IO and VDDA.\n"
            "None of the three reaches the DF12 connectors.", ha="left", va="center", fontsize=7.5, color=INK)
    ax.set_xlim(XS[0] - W / 2 - 0.2, j2 + W / 2 + 0.2)
    ax.set_ylim(LOW - H / 2 - 0.2, TOP + H / 2 + 0.2)
    ax.set_aspect("equal")
    ax.axis("off")
    print(save(fig, "pcb101-sky-breakout-rails"))


if __name__ == "__main__":
    main()
