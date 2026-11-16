"""Shared look for the course's matplotlib figures: plots, and boards or footprints drawn to scale.

    from plot_style import figure, save

save() writes docs/assets/img/<name>.svg on a white background with a fixed SVG id
salt and no date, so with the versions in requirements.txt a rerun reproduces the
committed file. circuit_style.py does the same for schemdraw circuit drawings.
"""
import os

import matplotlib

matplotlib.use("Agg")
matplotlib.rcParams["mathtext.fontset"] = "dejavuserif"
matplotlib.rcParams["svg.hashsalt"] = "uoftasic-figures"
matplotlib.rcParams["font.family"] = "serif"
matplotlib.rcParams["font.size"] = 10
import matplotlib.pyplot as plt  # noqa: E402

IMG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "docs", "assets", "img")
REPO = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

INK = "black"
GREY = "#8a8a8a"
COPPER = "#c9a227"
ACCENT = "#1f5fa8"
WARN = "#b03a2e"


def figure(width_in, height_in):
    fig, ax = plt.subplots(figsize=(width_in, height_in))
    return fig, ax


def save(fig, name):
    """Write docs/assets/img/<name>.svg and return its path."""
    path = os.path.normpath(os.path.join(IMG_DIR, name + ".svg"))
    fig.savefig(path, format="svg", transparent=False, facecolor="white", bbox_inches="tight",
                pad_inches=0.05, metadata={"Date": None})
    plt.close(fig)
    return path
