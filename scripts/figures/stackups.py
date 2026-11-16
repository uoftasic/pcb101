"""Layers and fabricator rules: the stackups of Tiny Tapeout's 2-layer DIP dock and 4-layer SKY130
breakout, read from the (stackup ...) block of each board file.

The boards are fetched at pinned commits (labs/common/upstream.json), so fetch them first:

    python3 labs/common/fetch_boards.py
    python3 scripts/figures/stackups.py     # writes docs/assets/img/layers-two-stackups.svg

The drawing isn't to scale: copper and mask are drawn thicker than they are, so that they show.
The labels give each layer's thickness as the board file states it.
"""
import os
import re

import circuit_style  # noqa: F401  (sets the course's matplotlib defaults)
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

plt.rcParams["font.family"] = "serif"
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
UP = os.path.join(ROOT, "labs", "common", "upstream", "breakout-pcb")
OUT = os.path.join(circuit_style.IMG_DIR, "layers-two-stackups.svg")
BOARDS = [("DIP dock: 2 copper layers", os.path.join(UP, "dip-dock", "dip-dock.kicad_pcb")),
          ("SKY130 breakout: 4 copper layers",
           os.path.join(UP, "breakout-sky-qfn", "breakout-sky-qfn.kicad_pcb"))]
COLOUR = {"copper": "#c8553d", "prepreg": "#d9cf9b", "core": "#c9bd7a", "mask": "#4f7a4f"}


def stackup(path):
    """The board's physical layers, top to bottom: (name, kind, thickness in mm, material, er)."""
    text = open(path).read()
    start = text.index("(stackup")
    block = text[start:text.index("(copper_finish", start)]
    layers = []
    for m in re.finditer(r'\(layer "([^"]+)"(.*?)\n\t\t\t\)', block, re.S):
        name, body = m.group(1), m.group(2)
        kind = re.search(r'\(type "([^"]+)"\)', body).group(1)
        th = re.search(r'\(thickness ([0-9.]+)\)', body)
        if th is None:
            continue                      # silkscreen and paste have no thickness here
        mat = re.search(r'\(material "([^"]+)"\)', body)
        er = re.search(r'\(epsilon_r ([0-9.]+)\)', body)
        k = ("copper" if kind == "copper" else "mask" if "Mask" in kind else kind)
        layers.append((name, k, float(th.group(1)), mat.group(1) if mat else "",
                       er.group(1) if er else ""))
    return layers


fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
for ax, (title, path) in zip(axes, BOARDS):
    layers = stackup(path)
    total = sum(t for _, _, t, _, _ in layers)
    y = 0.0
    for name, kind, t, mat, er in layers:
        h = {"copper": 0.35, "mask": 0.22}.get(kind, 0.4 + 2.2 * t)   # drawn height, not to scale
        y -= h
        ax.add_patch(Rectangle((0, y), 3.0, h, fc=COLOUR.get(kind, "#cccccc"), ec="white", lw=0.6))
        if kind == "copper":
            label = f"{name}, copper, {t * 1000:.0f} µm"
        elif kind == "mask":
            label = f"{name}, solder mask, {t * 1000:.0f} µm"
        else:
            label = f"{kind}, {mat}, {t} mm, εr {er}"
        ax.text(3.2, y + h / 2, label, va="center", fontsize=10)
    ax.text(0, 0.35, f"{title}, {total:.3f} mm in all", fontsize=11.5, weight="bold")
    ax.set_xlim(-0.1, 9.5)
    ax.set_ylim(-6.3, 0.8)
    ax.axis("off")
    print(title, f"{total:.3f} mm", [(n, t) for n, _, t, _, _ in layers])

fig.savefig(OUT, format="svg", transparent=False, facecolor="white", bbox_inches="tight",
            pad_inches=0.05, metadata={"Date": None})
print(OUT)
