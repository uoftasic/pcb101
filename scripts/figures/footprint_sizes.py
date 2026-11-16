"""Parts you can solder by hand: KiCad's footprints for common small parts, drawn to one scale.

Reads the footprints from the KiCad libraries in the course's pinned image, through
labs/common/kicad.sh, so it needs Docker:

    python3 scripts/figures/footprint_sizes.py

Copper pads are drawn from each footprint's pad list (pads on a copper layer only, so a
QFN's separate paste windows are left out) and the body from its F.Fab drawing, on a
1 mm grid. Nothing is redrawn by hand.
"""
import math
import os
import subprocess

from matplotlib.patches import Circle, FancyBboxPatch, Polygon, Rectangle
from matplotlib.transforms import Affine2D

from kicad_sexpr import find, get, parse
from plot_style import COPPER, GREY, INK, REPO, figure, save

LIB = "/usr/share/kicad/footprints"
ROWS = [
    [
        ("Resistor_SMD", "R_0402_1005Metric", "0402"),
        ("Resistor_SMD", "R_0603_1608Metric", "0603"),
        ("Resistor_SMD", "R_0603_1608Metric_Pad0.98x0.95mm_HandSolder", "0603\nHandSolder"),
        ("Resistor_SMD", "R_0805_2012Metric", "0805"),
        ("Resistor_SMD", "R_0805_2012Metric_Pad1.20x1.40mm_HandSolder", "0805\nHandSolder"),
        ("Resistor_SMD", "R_1206_3216Metric", "1206"),
    ],
    [
        ("Diode_SMD", "D_SOD-882", "SOD-882"),
        ("Package_TO_SOT_SMD", "SOT-23-5", "SOT-23-5"),
        ("Package_SO", "SOIC-8_3.9x4.9mm_P1.27mm", "SOIC-8"),
        ("Package_DFN_QFN", "QFN-64-1EP_9x9mm_P0.5mm_EP7.65x7.65mm", "QFN-64, 9 × 9 mm"),
    ],
]
ROW_X = [[0, 4.5, 9.5, 15, 20.5, 26.5], [0, 5.5, 13, 25]]
ROW_Y = [0, 13]


def read_footprints():
    paths = [f"{LIB}/{lib}.pretty/{name}.kicad_mod" for row in ROWS for lib, name, _ in row]
    script = 'for f in "$@"; do echo "### $f"; cat "$f"; done'
    out = subprocess.run([os.path.join(REPO, "labs", "common", "kicad.sh"), "bash", "-c", script, "_"] + paths,
                         check=True, capture_output=True, text=True, env={**os.environ, "PB101_QUIET": "1"}).stdout
    texts = {}
    for chunk in out.split("### ")[1:]:
        path, _, body = chunk.partition("\n")
        texts[path] = parse(body)
    return [[texts[f"{LIB}/{lib}.pretty/{name}.kicad_mod"] for lib, name, _ in row] for row in ROWS]


def on_copper(pad):
    layers = get(pad, "layers")[1:]
    return any(layer in ("F.Cu", "*.Cu") for layer in layers)


def draw_pad(ax, pad, ox, oy):
    at = get(pad, "at")
    x, y = float(at[1]) + ox, float(at[2]) + oy
    angle = float(at[3]) if len(at) > 3 else 0.0
    w, h = (float(v) for v in get(pad, "size")[1:3])
    shape = pad[3]
    turn = Affine2D().rotate_deg_around(x, y, -angle) + ax.transData
    if shape == "circle":
        ax.add_patch(Circle((x, y), w / 2, fc=COPPER, ec="none"))
    elif shape in ("roundrect", "oval"):
        r = min(w, h) / 2 if shape == "oval" else float(get(pad, "roundrect_rratio")[1]) * min(w, h)
        p = FancyBboxPatch((x - w / 2 + r, y - h / 2 + r), w - 2 * r, h - 2 * r,
                           boxstyle=f"round,pad={r}", fc=COPPER, ec="none")
        p.set_transform(turn)
        ax.add_patch(p)
    else:
        p = Rectangle((x - w / 2, y - h / 2), w, h, fc=COPPER, ec="none")
        p.set_transform(turn)
        ax.add_patch(p)
    drill = get(pad, "drill")
    if drill:
        ax.add_patch(Circle((x, y), float(drill[1]) / 2, fc="white", ec="none"))


def draw_fab(ax, fp, ox, oy):
    for kind in ("fp_line", "fp_rect", "fp_poly"):
        for item in find(fp, kind):
            if get(item, "layer")[1] != "F.Fab":
                continue
            if kind == "fp_poly":
                pts = [(float(p[1]) + ox, float(p[2]) + oy) for p in find(get(item, "pts"), "xy")]
                ax.add_patch(Polygon(pts, closed=True, fill=False, ec=INK, lw=0.7))
                continue
            (x1, y1), (x2, y2) = [(float(get(item, k)[1]) + ox, float(get(item, k)[2]) + oy) for k in ("start", "end")]
            if kind == "fp_rect":
                ax.add_patch(Rectangle((min(x1, x2), min(y1, y2)), abs(x2 - x1), abs(y2 - y1), fill=False, ec=INK, lw=0.7))
            else:
                ax.plot([x1, x2], [y1, y2], color=INK, lw=0.7)


def main():
    footprints = read_footprints()
    fig, ax = figure(7.6, 4.6)
    for gx in range(-3, 31):
        ax.plot([gx, gx], [-4, 20], color="#e6e6e6", lw=0.4, zorder=0)
    for gy in range(-4, 21):
        ax.plot([-3, 30], [gy, gy], color="#e6e6e6", lw=0.4, zorder=0)
    for row, fps, xs, oy in zip(ROWS, footprints, ROW_X, ROW_Y):
        for (lib, name, label), fp, ox in zip(row, fps, xs):
            for pad in find(fp, "pad"):
                if on_copper(pad):
                    draw_pad(ax, pad, ox, oy)
            draw_fab(ax, fp, ox, oy)
            below = 6.0 if lib == "Package_DFN_QFN" else (2.4 if oy == 0 else 4.2)
            ax.text(ox, oy + below, label, ha="center", va="top", fontsize=8)
    ax.plot([26, 31 - 1], [-2.5, -2.5], color=INK, lw=1.2)
    ax.text(28, -2.9, "5 mm", ha="center", va="bottom", fontsize=8)
    ax.set_xlim(-3, 31)
    ax.set_ylim(20.5, -4)
    ax.set_aspect("equal")
    ax.axis("off")
    print(save(fig, "pb101-footprint-sizes"))


if __name__ == "__main__":
    main()
