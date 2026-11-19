"""Placement and routing: a 3D render of Tiny Tapeout's 2-layer DIP dock from above.

    python3 labs/common/fetch_boards.py
    PCB101_DOCKER_ARGS="--cpus 1 --memory 2g" python3 scripts/figures/dip_dock_render.py

Runs `kicad-cli pcb render` through scripts/screenshots/kicad/render.sh, in the render image
(kicad/kicad:10.0.5-full, which has KiCad's 3D models of parts), and writes
docs/assets/img/pcb101-dip-dock-top.png: the board with its parts.
"""
import os
import subprocess

from plot_style import IMG_DIR, REPO

RENDER = os.path.join(REPO, "scripts", "screenshots", "kicad", "render.sh")
DOCK = os.path.join(REPO, "labs", "common", "upstream", "breakout-pcb", "dip-dock", "dip-dock.kicad_pcb")


def main():
    png = os.path.join(IMG_DIR, "pcb101-dip-dock-top.png")
    subprocess.run([RENDER, "3d", os.path.relpath(DOCK, REPO), os.path.relpath(png, REPO), "top"],
                   check=True, cwd=REPO)
    print(os.path.normpath(png))


if __name__ == "__main__":
    main()
