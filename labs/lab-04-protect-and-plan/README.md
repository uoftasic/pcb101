# Lab 04: Protect and plan

Writeup: [`docs/labs/lab-04-protect-and-plan-overview.md`](../../docs/labs/lab-04-protect-and-plan-overview.md)
· live: <https://uoftasic.com/pcb101/labs/lab-04-protect-and-plan-overview.html>

You add a buffer and a resistor on each UART line, an ESD array and a current-sense point to the board you drew in Lab 03, in your own board repository, and write its bring-up plan from the template here. Check it with:

```bash
cd ~/simproc-pmod                                        # your board repository
cp ~/pcb101/labs/lab-04-protect-and-plan/BRINGUP.md .     # once
~/pcb101/labs/lab-04-protect-and-plan/check.sh
```

`check.sh [FOLDER] [ARGS]` runs [`labs/common/check_pmod.py`](../common/check_pmod.py) with `--protect --bringup BRINGUP.md` on the project in FOLDER (default: the current folder), in the course's pinned KiCad image. It prints everything Lab 03's check prints, then three more kinds of Pmod row and the bring-up plan check ([`labs/common/check_bringup.py`](../common/check_bringup.py)), and ends with one line, `PASS` or `FAIL`. Exit status 0 is PASS, 1 FAIL, 2 couldn't run. Without bash, add `--protect --bringup BRINGUP.md` to the `docker run` in [Lab 03's README](../lab-03-a-pmod-for-one-projects-pins/README.md).

| Board | Last line of the check |
|---|---|
| Lab 03's `solutions/simproc-pmod/` with `BRINGUP.md` from here, as a student starts | `FAIL  pmod.kicad_pro: board check PASS; 12 of 17 Pmod checks ok; bring-up plan FAIL` |
| `solutions/simproc-pmod/` | `PASS  pmod.kicad_pro: board check PASS; 17 of 17 Pmod checks ok; bring-up plan PASS` |

## Rows Lab 04 adds to Lab 03's check

| Row | Passes when |
|---|---|
| `ui[0]`, `uo[0]` | the line runs through a buffer and then one resistor, the way it flows: on `ui[0]` the header pin is on the buffer's input (A) and its output (Y) reaches the Pmod pin through the resistor; on `uo[0]` the Pmod pin is on the input and the output reaches the header pin through the resistor. The buffer is a 74LVC1G or 74LVC2G 17, 34 or 125, or a 74AUP1G17, 74AUP1G34 or 74AUP1G125 (single supply, with Ioff; a 125's OE on GND), its VCC on the sockets' 3.3 V and its GND on GND, with a capacitor from that 3.3 V to GND whose pad is within 3 mm of its VCC pad. The resistor is 330 Ω to 15 kΩ on `ui[0]` and 1 kΩ to 5.1 kΩ on `uo[0]`, and the buffer's input on `ui[0]` has a resistor to 3.3 V or GND. A line with no buffer fails, and so does a buffer turned round |
| ESD J4.2, J4.3 | the header pin's net has a part whose reference starts with D, or from KiCad's `Power_Protection` library, with another pin on `GND` |
| sense | a two-pin resistor from the sockets' 3.3 V to a net of the board's own that feeds something, with a test point (reference TP…) on each side |
| bring-up plan | the five sections of the template filled in, no TODO left, a current limit with its unit, at least 2 checks under Before power and 4 steps under Steps, each with `Expect:` and a value with a unit (or a byte in hex or binary) |

## Files

| File | What it is |
|---|---|
| `check.sh` | the lab's check, on a board repository |
| `BRINGUP.md` | the bring-up plan's template; copy it into your repository |
| `solutions/` | the reference board and its bring-up plan; see its README |
| `src/selftest.py` | boards and plans with known verdicts, for testing the check itself |
| `results/` | local outputs; never committed |

The reference board is written by Lab 03's [`src/make_reference.py`](../lab-03-a-pmod-for-one-projects-pins/src/make_reference.py) (`protected` stage).
