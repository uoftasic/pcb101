# Scripts

Scripts for PB101 — PCB Design with KiCad (`uoftasic`): the link check for the rendered site, the KiCad screenshot and render tools, the scripts that draw the site's figures, and two small scripts left from the course template.

## Entry points

| Script | Purpose |
|--------|---------|
| `check_site.py` | Check that every local link and `#anchor` in the rendered site resolves; `.github/workflows/site.yml` runs it on `docs/_site` |
| `hello.py` | Smoke-check that Python runs in this clone |
| `init-template.py` | The template's bootstrap script, which fills in the course id, title and description in a repo made from the template. PB101's are already filled in; see [`TEMPLATE.md`](../TEMPLATE.md) |
| `screenshots/kicad/shot.sh` | KiCad GUI screenshots in the pinned image under Xvfb; see [`screenshots/kicad/README.md`](screenshots/kicad/README.md) |
| `screenshots/kicad/render.sh` | `kicad-cli` 3D renders and SVG plots of boards, schematics, footprints and symbols |
| `figures/kicad_figures.sh`, `figures/board_renders.sh` | The KiCad renders and plots on the guide pages, made with `render.sh`; `board_renders.sh` also renders Lab 03's and the capstone's boards for the lab pages. Both need the fetched boards, and both use ImageMagick in the `pb101/kicad-shot` image, which they build if it isn't there; `kicad_figures.sh` needs `pdftoppm` too |
| `figures/shots/fab-outputs-dip-dock.sh` | A shot file for `screenshots/kicad/shot.sh`: the DIP dock's Plot dialog and its Gerbers in GerbView, for the Fabrication outputs and KiCad files in git pages |
| `figures/*.py` | The diagrams and plots on the guide pages, drawn into `docs/assets/img/` with schemdraw and matplotlib. `pip install -r scripts/figures/requirements.txt`, then `python3 scripts/figures/<name>.py` rewrites that figure; each script's docstring says which page it's for. Scripts that read Tiny Tapeout's boards need `python3 labs/common/fetch_boards.py` first, and the four that run KiCad (`dip_dock_layers.py`, `dip_dock_render.py`, `footprint_sizes.py`, `review_diff.py`) need Docker |

## Usage

The `init-template.py` example is the template's own, for a course called DD103.

```bash
# From repo root
python3 scripts/hello.py

python3 scripts/init-template.py \
  --id dd103 \
  --title "DD103 — RTL on FPGAs & ASICs" \
  --description "RTL on FPGAs and open-source ASIC flows"
```

## Conventions

- Write scripts in Python where you can. HDL tooling belongs in `labs/` or the shared workbench.
- Keep secrets out of the repo. If a script needs configuration, add a `.env.example`.
- When you add a script, add it to the table above.
