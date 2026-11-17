#!/usr/bin/env python3
"""KiCad files in git: one real commit to Tiny Tapeout's demo board, as a picture.

Commit 293a3e2 of TinyTapeout/tt-demo-pcb (2026-06-23, "minor pcb cleanup") changed
tinytapeout-demo.kicad_pcb by 2,851 added and 2,919 removed lines. This script renders the
board's top before and after that commit with `kicad-cli pcb render` in the render image,
with the parts' 3D models (scripts/screenshots/kicad/render.sh), and writes
docs/assets/img/tt-demo-293a3e2-review.png:
the two renders side by side, and a third panel with every pixel that changed drawn in red,
thickened so that it survives the scaling, over a faded copy of the new board.

    python3 scripts/figures/review_diff.py

Needs Docker, git and Python 3 with Pillow and NumPy (both come with matplotlib, in
scripts/figures/requirements.txt). The board is Apache-2.0. The script clones the
repository's history without file contents into labs/common/results/figures/, which is
gitignored, and then fetches only the two versions of the board it renders.
"""
import os
import subprocess

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
WORK = os.path.join("labs", "common", "results", "figures", "tt-demo-review")
REPO_URL = "https://github.com/TinyTapeout/tt-demo-pcb.git"
COMMIT = "293a3e216aa00c69c30838bb283a3f2f5d20779b"
SHORT = COMMIT[:7]
BOARD = "tinytapeout-demo.kicad_pcb"
OUT = os.path.join("docs", "assets", "img", f"tt-demo-{SHORT}-review.png")
RENDER = os.path.join("scripts", "screenshots", "kicad", "render.sh")
PANEL_W = 760          # width of each panel in the figure, in pixels
THRESHOLD = 24         # a pixel counts as changed when any channel moved by more than this
GROW = 6               # pixels to thicken each change by, so it shows after scaling down


def run(cmd, **kw):
    return subprocess.run(cmd, cwd=kw.pop("cwd", ROOT), check=True, **kw)


def board_at(rev, name):
    """Write tinytapeout-demo.kicad_pcb as it was at rev to WORK/name; return the path."""
    clone = os.path.join(ROOT, WORK, "history")
    if not os.path.isdir(clone):
        run(["git", "clone", "--quiet", "--filter=blob:none", "--no-checkout", REPO_URL, clone])
    path = os.path.join(WORK, name)
    with open(os.path.join(ROOT, path), "wb") as f:
        run(["git", "show", f"{rev}:{BOARD}"], cwd=clone, stdout=f)
    return path


def render(board, png):
    run([RENDER, "3d", board, png, "top"], stdout=subprocess.DEVNULL)
    return Image.open(os.path.join(ROOT, png)).convert("RGB")


def label(img, text):
    """The image with a caption bar above it."""
    bar = 34
    out = Image.new("RGB", (img.width, img.height + bar), "white")
    out.paste(img, (0, bar))
    draw = ImageDraw.Draw(out)
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 20)
    except OSError:
        font = ImageFont.load_default()
    draw.text((img.width // 2, bar // 2), text, fill="black", font=font, anchor="mm")
    return out


def main():
    os.makedirs(os.path.join(ROOT, WORK), exist_ok=True)
    before = render(board_at(COMMIT + "^", "before.kicad_pcb"), os.path.join(WORK, "before.png"))
    after = render(board_at(COMMIT, "after.kicad_pcb"), os.path.join(WORK, "after.png"))

    a = np.asarray(before).astype(int)
    b = np.asarray(after).astype(int)
    changed = (np.abs(a - b) > THRESHOLD).any(axis=2)
    grey = np.asarray(after.convert("L").convert("RGB")).astype(float)
    grey = (255 - (255 - grey) * 0.35).astype(np.uint8)          # faded, so red stands out
    shown = changed.copy()
    for dy in range(-GROW, GROW + 1):
        for dx in range(-GROW, GROW + 1):
            shown |= np.roll(np.roll(changed, dy, axis=0), dx, axis=1)
    grey[shown] = (220, 30, 30)
    diff = Image.fromarray(grey)
    print(f"{changed.sum()} of {changed.size} pixels changed ({100 * changed.mean():.1f} %)")

    scale = PANEL_W / before.width
    size = (PANEL_W, round(before.height * scale))
    panels = [label(before.resize(size, Image.LANCZOS), f"before {SHORT}"),
              label(after.resize(size, Image.LANCZOS), f"after {SHORT}"),
              label(diff.resize(size, Image.LANCZOS), "changed pixels in red")]
    gap = 16
    fig = Image.new("RGB", (3 * PANEL_W + 2 * gap, panels[0].height), "white")
    for k, p in enumerate(panels):
        fig.paste(p, (k * (PANEL_W + gap), 0))
    fig.save(os.path.join(ROOT, OUT), optimize=True)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
