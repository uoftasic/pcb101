"""From die to package: the land pattern of a QFN-64, 9 x 9 mm, worked out from its drawing.

Repeats, by hand, what KiCad's footprint generator does for the footprint on Tiny Tapeout's
SKY130 breakout, QFN-64-1EP_9x9mm_P0.5mm_EP7.65x7.65mm, and draws the result.

The numbers come from gitlab.com/kicad/libraries/kicad-footprint-generator at 090252c:
  data/package/no_lead/qfn-6x.yaml            the package's dimensions (from Atmel's
                                              ATmega2560 datasheet, page 415)
  src/kilibs/config/ipc_configs/ipc_7351b.yaml the toe, heel and side goals for a flat no-lead
                                              part at nominal density, rounded to 0.05 mm
  src/generators/package/no_lead/footprint.py  F = 0.1 mm and P = 0.05 mm, and the 0.2 mm
                                              minimum from the exposed pad to the other pads
  src/kilibs/util/toleranced_size.py          how tolerances add (root sum of squares)
The pads this prints match the footprint in kicad/kicad:10.0.8 (0.85 x 0.25 mm at x = -4.45 mm).

    python3 scripts/figures/qfn_land_pattern.py   # prints the working and writes
                                                  # docs/assets/img/pkg-qfn64-land-pattern.svg
"""
import math
import os

import circuit_style  # noqa: F401  (sets the course's matplotlib defaults)
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

plt.rcParams["font.family"] = "serif"

OUT = os.path.join(circuit_style.IMG_DIR, "pkg-qfn64-land-pattern.svg")

# The package drawing: minimum and maximum, in mm.
D = (8.9, 9.1)      # body width, which for a QFN is also the span across the leads' outer ends
L = (0.35, 0.45)    # lead length
W = (0.18, 0.30)    # lead width
EP = 7.65           # exposed pad, nominal
PITCH, PER_SIDE = 0.5, 16
# The goals for a flat no-lead lead at nominal density, and the board maker's tolerances.
TOE, HEEL, SIDE = 0.30, 0.0, -0.04
F, P = 0.10, 0.05
ROUND = 0.05
MIN_EP_CLEARANCE = 0.2


def rnd(v):
    return round(v / ROUND) * ROUND


tol_D = D[1] - D[0]
tol_W = W[1] - W[0]
# The span between the leads' inner ends, S = D - 2L, and its tolerance added as a root sum of
# squares (2L has tolerance 0.1 * sqrt(2), as the generator computes it).
tol_2L = (L[1] - L[0]) * math.sqrt(2)
S = (D[0] - 2 * L[1], D[1] - 2 * L[0])
tol_S = math.hypot(tol_D, tol_2L)
S_max_rms = S[1] - ((S[1] - S[0]) - tol_S) / 2

Z = rnd(D[0] + 2 * TOE + math.sqrt(tol_D ** 2 + F ** 2 + P ** 2))
G = rnd(S_max_rms - 2 * HEEL - math.sqrt(tol_S ** 2 + F ** 2 + P ** 2))
X = rnd(W[0] + 2 * SIDE + math.sqrt(tol_W ** 2 + F ** 2 + P ** 2))
G = max(G, EP + 2 * MIN_EP_CLEARANCE)   # the generator would shorten the heel if needed
pad_len = (Z - G) / 2
pad_x = (Z + G) / 4

print(f"S = {S[0]:.2f} to {S[1]:.2f} mm, RMS tolerance {tol_S:.4f}, S_max(RMS) = {S_max_rms:.4f}")
print(f"Z = {D[0]} + 2 x {TOE} + sqrt({tol_D:.2f}^2 + {F}^2 + {P}^2) -> {Z:.2f} mm")
print(f"G = {S_max_rms:.4f} - 2 x {HEEL} - sqrt({tol_S:.4f}^2 + {F}^2 + {P}^2) -> {G:.2f} mm")
print(f"X = {W[0]} + 2 x ({SIDE}) + sqrt({tol_W:.2f}^2 + {F}^2 + {P}^2) -> {X:.2f} mm")
print(f"pad {pad_len:.2f} x {X:.2f} mm, centre at {pad_x:.2f} mm; "
      f"exposed pad to pads {(G - EP) / 2:.2f} mm")

# The drawing: the pads, the exposed pad and the three dimensions.
fig, ax = plt.subplots(figsize=(6.4, 6.4))
ax.set_aspect("equal")
ax.axis("off")
COPPER = "#c8553d"
first = -(PER_SIDE - 1) / 2 * PITCH
for k in range(PER_SIDE):
    c = first + k * PITCH
    for (x, y, w, h) in ((-pad_x, c, pad_len, X), (pad_x, c, pad_len, X),
                         (c, -pad_x, X, pad_len), (c, pad_x, X, pad_len)):
        ax.add_patch(Rectangle((x - w / 2, y - h / 2), w, h, fc=COPPER, ec="none"))
ax.add_patch(Rectangle((-EP / 2, -EP / 2), EP, EP, fc=COPPER, ec="none", alpha=0.55))
ax.add_patch(Rectangle((-D[1] / 2 + 0.1, -D[1] / 2 + 0.1), D[1] - 0.2, D[1] - 0.2, fc="none",
                       ec="#555555", lw=0.8, ls=(0, (4, 3))))
ax.text(0, 0.35, f"exposed pad\n{EP} × {EP} mm", ha="center", va="center", fontsize=11)
ax.text(0, -1.0, "package body (dashed), 9 × 9 mm", ha="center", va="center", fontsize=9.5,
        color="#555555")


def dim(y, a, b, label, above=True):
    ax.annotate("", (a, y), (b, y), arrowprops=dict(arrowstyle="<|-|>", lw=0.9, color="black",
                                                       shrinkA=0, shrinkB=0, mutation_scale=9))
    ax.text((a + b) / 2, y + (0.12 if above else -0.12), label, ha="center",
            va="bottom" if above else "top", fontsize=11)


dim(-6.0, -Z / 2, Z / 2, f"Z = {Z:.2f} mm, outer edge to outer edge", above=False)
dim(-2.6, -G / 2, G / 2, f"G = {G:.2f} mm, inner edge to inner edge")
for x in (-Z / 2, Z / 2):
    ax.plot([x, x], [-pad_x - 0.6, -6.1], color="black", lw=0.6)
for x in (-G / 2, G / 2):
    ax.plot([x, x], [first - X / 2 - 0.05, -2.7], color="black", lw=0.6)
# X, on the top pad of the left column.
yt = -first
ax.annotate(f"X = {X:.2f} mm wide,\n{pad_len:.2f} mm long", (-pad_x - pad_len / 2, yt),
            (-6.9, yt + 1.2), fontsize=10.5, ha="left", va="bottom",
            arrowprops=dict(arrowstyle="-", lw=0.7, color="black"))
ax.set_xlim(-7.0, 6.0)
ax.set_ylim(-6.7, 6.0)
fig.savefig(OUT, format="svg", transparent=False, facecolor="white", bbox_inches="tight",
            pad_inches=0.05, metadata={"Date": None})
print(OUT)
