"""Two maps of Tiny Tapeout's SKY130 breakout, drawn to scale from the board file, with pads coloured by supply.

    python3 labs/common/fetch_boards.py
    python3 scripts/figures/sky_breakout_map.py

Reads breakout-pcb/breakout-sky-qfn/breakout-sky-qfn.kicad_pcb (rev 3.2, 91a2bf1) and writes:

- pcb101-sky-breakout-u4-decoupling.svg: the chip U4 and the capacitors around it
  (placement-and-routing).
- pcb101-sky-breakout-links.svg: the strip along the board's top edge with the
  regulators, the 0 ohm links and the header J2 (measuring-current).

Every pad is drawn at the position, size and angle the board file gives it, with the
footprint's F.Fab outline. Parts marked DNP are drawn dashed. Tracks and copper pours
are left out, because at this scale they hide the parts; the pads' colours show which
supply each one is on.
"""
import math
import os

from matplotlib.patches import Circle, Polygon, Rectangle
from matplotlib.lines import Line2D
from matplotlib.transforms import Affine2D

from kicad_sexpr import find, get, net_names, pad_position, parse, prop
from plot_style import REPO, figure, save

BOARD = os.path.join(REPO, "labs", "common", "upstream", "breakout-pcb", "breakout-sky-qfn",
                     "breakout-sky-qfn.kicad_pcb")

RAILS = [  # (net names, legend label, colour)
    (("VCCD",), "VCCD (1.8 V)", "#1f5fa8"),
    (("VDD_{IO}",), "VDD_IO (3.3 V)", "#c48a00"),
    (("VDDA",), "VDDA (3.3 V)", "#2e8b57"),
    (("+3V3", "/VCIN", "/VDIN", "VCC_{REG}", "VDD_{REG}"), "+3V3 and regulator nets", "#b03a2e"),
    (("GND",), "GND", "#4d4d4d"),
]
OTHER = "#c8c8c8"


def colour_of(net):
    for nets, _, colour in RAILS:
        if net in nets:
            return colour
    return OTHER


def local_to_board(fp, x, y):
    at = get(fp, "at")
    fx, fy = float(at[1]), float(at[2])
    t = math.radians(float(at[3])) if len(at) > 3 else 0.0
    return fx + x * math.cos(t) + y * math.sin(t), fy - x * math.sin(t) + y * math.cos(t)


def draw_footprint(ax, fp, name_of, box, label=True):
    dnp = "dnp" in (get(fp, "attr") or [])
    for pad in find(fp, "pad"):
        layers = get(pad, "layers")[1:]
        if not any(layer in ("F.Cu", "*.Cu") for layer in layers):
            continue
        x, y = pad_position(fp, pad)
        if not (box[0] - 3 < x < box[2] + 3 and box[1] - 3 < y < box[3] + 3):
            continue
        at = get(pad, "at")
        angle = float(at[3]) if len(at) > 3 else 0.0
        w, h = (float(v) for v in get(pad, "size")[1:3])
        colour = OTHER if dnp else colour_of(name_of(get(pad, "net")))
        if pad[3] == "circle":
            patch = Circle((x, y), w / 2)
        else:
            patch = Rectangle((x - w / 2, y - h / 2), w, h)
            patch.set_transform(Affine2D().rotate_deg_around(x, y, -angle) + ax.transData)
        patch.set_facecolor(colour)
        patch.set_edgecolor("none")
        ax.add_patch(patch)
        drill = get(pad, "drill")
        if drill and len(drill) > 1:
            ax.add_patch(Circle((x, y), float(drill[1]) / 2, fc="white", ec="none"))
    for kind in ("fp_line", "fp_rect", "fp_poly"):
        for item in find(fp, kind):
            if get(item, "layer")[1] != "F.Fab":
                continue
            style = dict(color="#7a7a7a", lw=0.6, ls=(0, (3, 2)) if dnp else "-")
            if kind == "fp_poly":
                pts = [local_to_board(fp, float(p[1]), float(p[2])) for p in find(get(item, "pts"), "xy")]
                ax.add_patch(Polygon(pts, closed=True, fill=False, ec=style["color"], lw=style["lw"], ls=style["ls"]))
            elif kind == "fp_rect":
                (x1, y1), (x2, y2) = [(float(get(item, k)[1]), float(get(item, k)[2])) for k in ("start", "end")]
                pts = [local_to_board(fp, *p) for p in ((x1, y1), (x2, y1), (x2, y2), (x1, y2))]
                ax.add_patch(Polygon(pts, closed=True, fill=False, ec=style["color"], lw=style["lw"], ls=style["ls"]))
            else:
                (x1, y1), (x2, y2) = [local_to_board(fp, float(get(item, k)[1]), float(get(item, k)[2]))
                                      for k in ("start", "end")]
                ax.plot([x1, x2], [y1, y2], **style)
    if label:
        x, y = (float(v) for v in get(fp, "at")[1:3])
        ref = prop(fp, "Reference") + (" (DNP)" if dnp else "")
        ax.text(x, y, ref, ha="center", va="center", fontsize=6.5, color="black", clip_on=True,
                bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none", alpha=0.85))


def draw(name, box, refs, size, legend_columns):
    board = parse(open(BOARD, encoding="utf-8").read())
    name_of = net_names(board)
    fig, ax = figure(*size)
    for fp in find(board, "footprint"):
        ref = prop(fp, "Reference")
        x, y = (float(v) for v in get(fp, "at")[1:3])
        inside = box[0] <= x <= box[2] and box[1] <= y <= box[3]
        if inside and (refs == "all" or ref in refs):
            draw_footprint(ax, fp, name_of, box, label=not ref.startswith(("STITCH", "FID", "kibuzzard")))
    handles = [Line2D([], [], marker="s", ls="", ms=7, color=c, label=t) for _, t, c in RAILS]
    handles.append(Line2D([], [], marker="s", ls="", ms=7, color=OTHER, label="other nets, and DNP parts"))
    ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.01), ncol=legend_columns,
              fontsize=7, frameon=False)
    ax.set_xlim(box[0], box[2])
    ax.set_ylim(box[3], box[1])  # y down, as in KiCad
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_color("#bbbbbb")
    print(save(fig, name))


def main():
    caps = {f"C{i}" for i in range(1, 26)}
    draw("pcb101-sky-breakout-u4-decoupling", (126.0, 62.0, 150.0, 86.0), caps | {"U4"}, (5.6, 6.2), 2)
    draw("pcb101-sky-breakout-links", (113.5, 49.5, 162.5, 62.0),
         caps | {"U1", "U2", "R2", "R4", "R8", "R13", "R14", "R15", "J2", "TP3", "TP4"}, (8.6, 3.0), 3)


if __name__ == "__main__":
    main()
