"""Measuring current: the voltage a series resistor drops, against the current through it.

    python3 scripts/figures/shunt_drop.py

V = I R for three resistor values. The two marked ranges are sourced: a multimeter on a
current range drops 0.1 V to 0.25 V at full scale (Horowitz and Hill, The Art of
Electronics, 3rd ed., p. 10, "voltage burden"), and the demo board running its factory
test draws about 180 mA to 200 mA from 5 V (Tiny Tapeout's ETR demo board guide).
"""
import numpy as np

from plot_style import ACCENT, GREY, INK, figure, save


def main():
    i = np.logspace(-6, 0, 200)  # A
    fig, ax = figure(6.4, 3.8)
    styles = {0.1: (0, (1, 2)), 1.0: (0, (5, 3)), 10.0: "-"}
    for r, ls in styles.items():
        ax.loglog(i, i * r, color=INK, lw=1.6, ls=ls)
        x = 2e-5
        ax.text(x, x * r * 1.6, f"{r:g} Ω", fontsize=8.5, rotation=24, rotation_mode="anchor")

    ax.axhspan(0.1, 0.25, color=ACCENT, alpha=0.12, lw=0)
    ax.text(1.5e-6, 0.16, "a multimeter's burden at full scale, 0.1 to 0.25 V", fontsize=8, color=ACCENT, va="center")
    ax.axvspan(0.18, 0.20, color=GREY, alpha=0.35, lw=0)
    ax.text(0.17, 1.5e-6, "kit on its factory test,\n180 to 200 mA at 5 V", fontsize=7.5, color=INK,
            ha="right", va="bottom")
    for r in (10.0, 1.0, 0.1):
        ax.plot([0.2], [0.2 * r], marker="o", ms=4, color=INK)
        ax.text(0.16, 0.2 * r * 1.15, f"{0.2 * r:g} V", fontsize=8, ha="right", va="bottom")
    ax.plot([1e-3], [1e-2], marker="o", ms=4, color=INK)
    ax.text(8e-4, 1.2e-2, "10 Ω at 1 mA: 10 mV", fontsize=8, ha="right", va="bottom")

    ax.set_xlim(1e-6, 1)
    ax.set_ylim(1e-6, 10)
    ax.set_xlabel("current (A)")
    ax.set_ylabel("voltage across the resistor (V)")
    ax.grid(True, which="major", color="#e6e6e6", lw=0.5)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    print(save(fig, "pcb101-shunt-drop"))


if __name__ == "__main__":
    main()
