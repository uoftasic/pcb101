# Lab 02: A footprint from a datasheet

Writeup: [`docs/labs/lab-02-a-footprint-from-a-datasheet-overview.md`](../../docs/labs/lab-02-a-footprint-from-a-datasheet-overview.md)
· live: <https://uoftasic.com/pb101/labs/lab-02-a-footprint-from-a-datasheet-overview.html>

You work out the land pattern for TI's RHL0024A package (VQFN-24, 3.5 × 5.5 mm), which
KiCad's library doesn't have, from the drawing on page 36 of the
[SN74LVC8T245 datasheet](https://www.ti.com/lit/ds/symlink/sn74lvc8t245.pdf) (SCES584D),
then draw its footprint and the chip's symbol in this folder's KiCad project. Check them
from the repo root:

```bash
labs/common/kicad.sh python3 labs/lab-02-a-footprint-from-a-datasheet/src/check_footprint.py
```

It takes about 20 s once your footprint and symbol exist, and ends with `PASS` or `FAIL`.
On the folder as shipped it prints
`FAIL  4 of 4 parts have a MISMATCH: pads.md, Footprint, Symbol and Fit`.

## Files

| File | What it is |
|---|---|
| `lab02.kicad_pro`, `fp-lib-table`, `sym-lib-table` | the KiCad project you open; its library tables add `pb101.pretty` and `pb101.kicad_sym` as the project library `pb101` |
| `pads.md` | the file you fill in: your hand calculation |
| `pb101.pretty/` | your footprint goes here, as `RHL0024A.kicad_mod` |
| `pb101.kicad_sym` | your symbol goes here, as `SN74LVC8T245RHL` |
| `data/rhl0024a.json` | the drawing's numbers and Table 4-1's pins, with the page each comes from |
| `src/land_pattern.py` | the course's arithmetic; `python3 src/land_pattern.py` prints it, so open it only after your own numbers are written down |
| `src/check_footprint.py` | the check: your numbers, your footprint, your symbol, and a one-part board built from them through `labs/common/check_board.py` |
| `src/fit_project.py` | writes that one-part board into `results/fit/` |
| `src/make_reference.py` | writes the reference solution from `land_pattern.py` |
| `src/selftest.py` | seven folders with known verdicts, for testing the check itself |
| `solutions/` | the reference `pads.md`, footprint and symbol |
| `results/` | local outputs; never committed |

`labs/common/kicad.sh python3 labs/lab-02-a-footprint-from-a-datasheet/src/selftest.py` runs
the self-test in about 3 min (196 s in our run, with `--cpus 1`) and ends with `7 of 7 cases gave
the expected verdict`.

The datasheet is TI's and isn't copied here; `data/rhl0024a.json` holds only the numbers
the lab uses, each with the page it's on.
