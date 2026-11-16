#!/usr/bin/env python3
"""Fabrication outputs: the DIP dock's layers, one panel per Gerber file.

Plots six layers of Tiny Tapeout's DIP dock (TinyTapeout/breakout-pcb at 91a2bf1,
Apache-2.0) with `kicad-cli pcb export svg` in the pinned image, through
scripts/screenshots/kicad/render.sh, and puts them side by side in one SVG,
docs/assets/img/dip-dock-gerber-layers.svg. Each panel is labelled with the Gerber file
that `kicad-cli pcb export gerbers --board-plot-params` writes for that layer and the file
function KiCad records for it in the Gerber job file.

    python3 labs/common/fetch_boards.py breakout-pcb tinytapeout-kicad-libs
    python3 scripts/figures/dip_dock_layers.py

Needs Docker (for render.sh) and Python 3; nothing else. The panels are KiCad's SVG plots
of the same layers the Gerbers hold, drawn in black on white, not renders of the Gerber
files themselves. Holes aren't drawn, because they're in the drill file, not in any Gerber
(the board's own plot settings have drill marks set to None). render.sh removes the date kicad-cli writes into each SVG, so the same
board gives the same figure.
"""
import os
import re
import subprocess

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
BOARD = "labs/common/upstream/breakout-pcb/dip-dock/dip-dock.kicad_pcb"
WORK = "labs/common/results/figures/dip-dock-layers"      # gitignored, and inside the repo
OUT = "docs/assets/img/dip-dock-gerber-layers.svg"
RENDER = "scripts/screenshots/kicad/render.sh"

# (layer, Gerber file, the file function in dip-dock-job.gbrjob, a note)
PANELS = [
    ("F.Cu", "dip-dock-F_Cu.gbr", "Copper, L1, Top", ""),
    ("B.Cu", "dip-dock-B_Cu.gbr", "Copper, L2, Bot", "seen from the top"),
    ("F.Mask", "dip-dock-F_Mask.gbr", "SolderMask, Top", "shapes are openings"),
    ("F.Silkscreen", "dip-dock-F_Silkscreen.gbr", "Legend, Top", ""),
    ("F.Paste", "dip-dock-F_Paste.gbr", "SolderPaste, Top", "for the stencil"),
    ("Edge.Cuts", "dip-dock-Edge_Cuts.gbr", "Profile", "the board outline"),
]

COLS = 3
GAP = 10.0         # mm between panels
LABEL = 16.0       # mm of label space under each panel
MARGIN = 4.0       # mm around the whole figure
PX_PER_MM = 5.0    # the figure's size on the page


def plot(layer):
    """Plot one layer, with the board outline, to WORK/<layer>.svg; return its text."""
    out = os.path.join(WORK, layer + ".svg")
    layers = layer if layer == "Edge.Cuts" else layer + ",Edge.Cuts"
    subprocess.run([RENDER, "pcb", BOARD, out, layers, "--black-and-white", "--drill-shape-opt", "0"],
                   cwd=ROOT, check=True, stdout=subprocess.DEVNULL)
    with open(os.path.join(ROOT, out)) as f:
        return f.read()


def inner(svg):
    """The size, viewBox and contents of a kicad-cli SVG, without its outer <svg> tag."""
    head = re.search(r"<svg\b[^>]*>", svg, re.S)
    attrs = head.group(0)
    width = float(re.search(r'width="([\d.]+)mm"', attrs).group(1))
    height = float(re.search(r'height="([\d.]+)mm"', attrs).group(1))
    viewbox = re.search(r'viewBox="([^"]+)"', attrs).group(1)
    body = svg[head.end():svg.rindex("</svg>")]
    return width, height, viewbox, body


def main():
    os.makedirs(os.path.join(ROOT, WORK), exist_ok=True)
    plots = [inner(plot(layer)) for layer, _, _, _ in PANELS]
    pw = max(p[0] for p in plots)
    ph = max(p[1] for p in plots)
    rows = (len(PANELS) + COLS - 1) // COLS
    total_w = 2 * MARGIN + COLS * pw + (COLS - 1) * GAP
    total_h = 2 * MARGIN + rows * (ph + LABEL) + (rows - 1) * (GAP - 4)

    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>\n',
        f'<svg xmlns="http://www.w3.org/2000/svg" version="1.1" '
        f'width="{total_w * PX_PER_MM:.0f}" height="{total_h * PX_PER_MM:.0f}" '
        f'viewBox="0 0 {total_w:.3f} {total_h:.3f}">\n',
        "<title>The DIP dock's layers, one panel per Gerber file</title>\n",
        f'<rect x="0" y="0" width="{total_w:.3f}" height="{total_h:.3f}" fill="#ffffff"/>\n',
    ]
    for k, ((layer, gbr, function, note), (w, h, viewbox, body)) in enumerate(zip(PANELS, plots)):
        col, row = k % COLS, k // COLS
        x = MARGIN + col * (pw + GAP)
        y = MARGIN + row * (ph + LABEL + GAP - 4)
        parts.append(f'<rect x="{x - 0.5:.3f}" y="{y - 0.5:.3f}" width="{pw + 1:.3f}" '
                     f'height="{ph + 1:.3f}" fill="none" stroke="#bbbbbb" stroke-width="0.3"/>\n')
        parts.append(f'<svg x="{x:.3f}" y="{y:.3f}" width="{w:.4f}" height="{h:.4f}" '
                     f'viewBox="{viewbox}">{body}</svg>\n')
        cx = x + pw / 2
        parts.append(f'<text x="{cx:.3f}" y="{y + ph + 6.5:.3f}" text-anchor="middle" '
                     f'font-family="DejaVu Sans Mono, Menlo, Consolas, monospace" font-size="4.6" '
                     f'fill="#000000">{gbr}</text>\n')
        caption = function + (f" ({note})" if note else "")
        parts.append(f'<text x="{cx:.3f}" y="{y + ph + 12.5:.3f}" text-anchor="middle" '
                     f'font-family="DejaVu Sans, Helvetica, Arial, sans-serif" font-size="4.2" '
                     f'fill="#333333">{caption}</text>\n')
    parts.append("</svg>\n")
    with open(os.path.join(ROOT, OUT), "w") as f:
        f.write("".join(parts))
    print(f"wrote {OUT} ({os.path.getsize(os.path.join(ROOT, OUT)) / 1000:.0f} kB)")


if __name__ == "__main__":
    main()
