# Figures (source)

PCB101 keeps nothing here; the folder is left from the course template. The site's figures come from these scripts, which write them straight into `docs/assets/img/`:

- the diagrams and plots on the guide pages, by the Python scripts in `scripts/figures/` (schemdraw and matplotlib), and the KiCad renders and plots on them by `scripts/figures/kicad_figures.sh` and `board_renders.sh`;
- GUI screenshots of KiCad's editors, by `scripts/screenshots/kicad/shot.sh`, and other 3D renders and SVG plots by `scripts/screenshots/kicad/render.sh`.

[`scripts/README.md`](../scripts/README.md) lists the scripts and what each one needs.

A figure drawn by hand, with no script behind it, would keep its source (SVG, draw.io, a schematic) here, with a small web-ready copy in `docs/assets/img/`.
