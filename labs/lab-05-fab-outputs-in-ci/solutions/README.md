# Lab 05 reference: CI for the SimProc Pmod

`simproc-pmod/` holds only the files Lab 05 adds to a board repository. Copied on top of Lab 04's reference board ([`../../lab-04-protect-and-plan/solutions/simproc-pmod/`](../../lab-04-protect-and-plan/solutions/simproc-pmod/)), they make the repository the lab's self-test checks.

| File | What it is |
|---|---|
| `.github/workflows/board.yml` | the workflow: pull the image named in `ci/kicad-image.txt`, run `ci/build.sh check`, `fab` and `images` in it as the runner's uid, then pull the image named in `ci/kibot-image.txt` and run `ci/build.sh kibot` in it the same way, and upload `out/` even when a step failed |
| `ci/build.sh` | the starter's build script with its five TODOs done: the drill file (`--drill-origin absolute`, because the board's plot settings don't use the drill/place origin), the BOM, the position file (`--format csv --units mm`), top and bottom renders, and an SVG of each copper layer with the outline |
| `ci/board.kibot.yaml` | KiBot's configuration: a `generic` filter with `exclude_kicad_dnp: true`, an `ibom` output that names it as its `dnf_filter`, and a `report` output with the default template |
| `ci/check_board.py`, `ci/kicad-image.txt`, `ci/kibot-image.txt` | copies of `labs/common/`'s; the self-test checks they're identical |
| `.gitignore` | Tiny Tapeout's (`tt-demo-pcb` at bbf3dd1), with `.history/` and `out/` added |

What the build wrote for Lab 04's board in `kicad/kicad:10.0.5`, and what KiBot wrote in its own image:

| Folder | Files |
|---|---|
| `out/reports/` | `erc.json`, `drc.json`, `summary.json`: ERC 0, DRC 0 errors and 32 warnings, 0 unconnected, 0 parity |
| `out/fab/` | 9 Gerbers (`pmod-F_Cu.gbr`, `-B_Cu`, `-F_Paste`, `-B_Paste`, `-F_Silkscreen`, `-B_Silkscreen`, `-F_Mask`, `-B_Mask`, `-Edge_Cuts`), `pmod-job.gbrjob`, `pmod.drl` (70 holes: 6 of 0.3 mm, the vias; 25 of 0.8 mm; 39 of 1.0 mm) |
| `out/assembly/` | `pmod-bom.csv` (15 rows), `pmod-pos.csv` (13 parts: the test points TP1 and TP2 are excluded from position files by their footprint) |
| `out/review/` | `pmod-top.png`, `pmod-bottom.png` (1568 × 872), `pmod-F_Cu.svg`, `pmod-B_Cu.svg`, `pmod-schematic.pdf` |
| `out/kibot/` | `pmod-ibom.html` (15 parts in 11 rows), `pmod-report.txt` (64.0 × 32.0 mm; drill tools 0.4 mm × 6, 0.9 mm × 25, 1.1 mm × 39, which are the 70 holes with 0.1 mm added to each plated one) |

The planted commit in the self-test is [`../src/planted.py`](../src/planted.py) applied to the board. Its board check fails with `drc.error: 2 (want 0)`: a `clearance` error between the moved +3V3 track and J1's pad 7 (0.1600 mm against 0.2000 mm), and a `starved_thermal` error on J1's pad 11, whose connection to the GND zone the track now blocks.
