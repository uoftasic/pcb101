# Lab 03: A Pmod for one project's pins

Writeup: [`docs/labs/lab-03-a-pmod-for-one-projects-pins-overview.md`](../../docs/labs/lab-03-a-pmod-for-one-projects-pins-overview.md)
· live: <https://uoftasic.com/pcb101/labs/lab-03-a-pmod-for-one-projects-pins-overview.html>

You copy `template/` out of the course repo into a board repository of your own, draw a 2-layer Pmod for SimProc in it, and check it with:

```bash
cd ~/simproc-pmod                                              # your board repository
~/pcb101/labs/lab-03-a-pmod-for-one-projects-pins/check.sh      # ~/pcb101 is the course clone
```

`check.sh [FOLDER] [ARGS]` runs [`labs/common/check_pmod.py`](../common/check_pmod.py) on the project in FOLDER (default: the current folder) in the course's pinned KiCad image, through `labs/common/kicad.sh`. It prints the board check (ERC, DRC, unconnected items, schematic parity), then the Pmod check: the three connectors 22.86 mm apart, in a row, locked, with their pins past the board's edge, and every pin in SimProc's pin list, [`labs/common/pins/simproc.json`](../common/pins/simproc.json). It ends with one line, `PASS` or `FAIL`, and exits 0 for PASS, 1 for FAIL and 2 if it couldn't run. Extra arguments go to `check_pmod.py`; `--pins FILE` checks another project's pin list.

| Board | Last line of the check |
|---|---|
| `template/` as shipped | `FAIL  pmod.kicad_pro: board check FAIL; 0 of 2 Pmod checks ok` |
| `solutions/simproc-pmod/` | `PASS  pmod.kicad_pro: board check PASS; 14 of 14 Pmod checks ok` |

`check.sh` is bash, for Linux, macOS and WSL. Without bash, this does the same from your board repository; we have run it on Linux and not on Windows:

```bash
docker run --rm -v "${PWD}:/work" -v "<path to pcb101>:/w" -w /work kicad/kicad:10.0.5@sha256:182c8005cb775a2c448a4c18681d489f1ff472a761885eba3e08b07e3c0564de python3 /w/labs/common/check_pmod.py .
```

## Rows of the check

| Row | Passes when |
|---|---|
| connectors | three `PMOD_PERIPH_2x6` symbols, their footprints at one angle, in a row 22.86 mm apart (to 0.02 mm), every pad inside the outline, every pin tip outside it, all three locked |
| sockets | left to right, with the pins pointing away from you: input (`ui`), bidir (`uio`), output (`uo`) |
| power | pins 6 and 12 of every connector on one net, pins 5 and 11 on `GND` |
| dongle | a connector other than the Pmods with pin 1 on `GND` and pins 2 and 3 |
| `ui[0]`, `uo[0]` | the Pmod pin reaches the header's pin 2 (`ui[0]`) or pin 3 (`uo[0]`), on the same net, through one series resistor, or through a buffer or a translator the right way round (Lab 04's protection) |
| `uio[n]` | a switch from the line to the 3.3 V supply, and a resistor from the line to `GND` |

A resistor is a two-pin part whose reference starts with R, one element of a bussed network (`R_Network*`, pin 1 common) or one of an isolated array (`R_Pack*`). A switch is a part whose reference starts with SW; for `SW_DIP_xNN`, pin *k* pairs with pin 2NN + 1 − *k*.

## Files

| File | What it is |
|---|---|
| `check.sh` | the lab's check, on a board repository |
| `template/` | the board repository a student starts from: `pmod.kicad_pro` (JLCPCB's 2-layer limits in Board Setup), `pmod.kicad_dru` (the annular-ring rule), an empty schematic and board, and `lib/` with Tiny Tapeout's Pmod symbol and footprint (Apache-2.0, recorded in `lib/UPSTREAM.md`) |
| `solutions/` | the reference board; see its README |
| `src/make_reference.py` | writes the template's KiCad files and every stage of the reference boards, in the pinned image |
| `src/stages.sh` | writes every stage into `results/stages/` and runs the checks on each; the writeup's outputs come from there |
| `src/selftest.py` | boards with known verdicts, for testing the check itself |
| `results/` | local outputs; never committed |
