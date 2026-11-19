"""Placement and routing: how long a trace can be before its delay matters, against rise time.

    python3 scripts/figures/trace_length_limits.py

Two rules of thumb from Hall and Heck, Advanced Signal Integrity for High-Speed Digital
Designs: a piece of line can be modelled as one lumped L and C when its delay is at most
t_r/10 (ch. 3, pp. 93-94), and reflections are masked by the edge itself when
t_r > 2 t_d (ch. 3, p. 144). The speed is c / sqrt(eps_r) with eps_r = 4.5, the value
Hall and Heck use for FR-4 in their Example 3-1; a trace on an outer layer runs partly
in air and is a little faster, so these lengths are on the short (safe) side.
"""
import numpy as np

from plot_style import ACCENT, GREY, INK, figure, save

C_MM_PER_NS = 299.792458
EPS_R = 4.5
V = C_MM_PER_NS / np.sqrt(EPS_R)  # mm per ns


def main():
    tr = np.logspace(np.log10(0.3), np.log10(20), 200)  # ns
    lumped = tr * V / 10
    masked = tr * V / 2

    fig, ax = figure(6.4, 3.8)
    ax.loglog(tr, masked, color=INK, lw=1.6)
    ax.loglog(tr, lumped, color=INK, lw=1.6, ls=(0, (5, 3)))
    ax.text(0.42, 0.42 * V / 2 * 1.25, "reflections hidden by the edge\nbelow this line: $\\ell < t_r v/2$",
            fontsize=8.5, color=INK, rotation=28, rotation_mode="anchor")
    ax.text(0.42, 0.42 * V / 10 * 1.25, "one lumped L and C is a fair model\nbelow this line: $\\ell < t_r v/10$",
            fontsize=8.5, color=INK, rotation=28, rotation_mode="anchor")

    ax.axhline(61, xmin=0.45, color=ACCENT, lw=1.0)
    ax.text(14, 66, "61 mm: across a three-Pmod board", color=ACCENT, fontsize=8, ha="right", va="bottom")
    ax.axvline(2, color=GREY, lw=0.8, ls=(0, (2, 2)))
    ax.text(2.1, 2.2, "2 ns edges\n(74LVC example,\nHorowitz and Hill)", color=GREY, fontsize=7.5, va="bottom")
    for y in (2 * V / 10, 2 * V / 2):
        ax.plot([2], [y], marker="o", ms=4, color=INK)
        ax.text(2.25, y, f"{y:.0f} mm", fontsize=8, va="center")

    ax.set_xlim(0.3, 20)
    ax.set_ylim(2, 3000)
    ax.set_xlabel("rise time $t_r$ (ns)")
    ax.set_ylabel("trace length $\\ell$ (mm)")
    ax.grid(True, which="major", color="#e6e6e6", lw=0.5)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.set_title(f"FR-4, $\\varepsilon_r$ = {EPS_R}: $v = c/\\sqrt{{\\varepsilon_r}}$ = {V:.0f} mm/ns", fontsize=9)
    print(save(fig, "pcb101-trace-length-limits"))


if __name__ == "__main__":
    main()
