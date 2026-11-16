"""Placement and routing: a 3D render of Tiny Tapeout's 2-layer DIP dock from above.

    python3 labs/common/fetch_boards.py
    IC103_DOCKER_ARGS="--cpus 1 --memory 2g" python3 scripts/figures/dip_dock_render.py

Runs `kicad-cli pcb render` in the pinned image through scripts/screenshots/kicad/render.sh
and writes docs/assets/img/ic103-dip-dock-top.png. The image has no 3D models of parts,
so the render shows the bare board: copper, mask, silkscreen and holes.
"""
import os
import subprocess

from plot_style import IMG_DIR, REPO

RENDER = os.path.join(REPO, "scripts", "screenshots", "kicad", "render.sh")
DOCK = os.path.join(REPO, "labs", "common", "upstream", "breakout-pcb", "dip-dock", "dip-dock.kicad_pcb")


def main():
    png = os.path.join(IMG_DIR, "ic103-dip-dock-top.png")
    subprocess.run([RENDER, "3d", os.path.relpath(DOCK, REPO), os.path.relpath(png, REPO), "top"],
                   check=True, cwd=REPO)
    print(os.path.normpath(png))


if __name__ == "__main__":
    main()
