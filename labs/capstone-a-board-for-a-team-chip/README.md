# Capstone: A board for a team chip

Writeup: [`docs/labs/capstone-a-board-for-a-team-chip-overview.md`](../../docs/labs/capstone-a-board-for-a-team-chip-overview.md)
· live: <https://uoftasic.com/pcb101/labs/capstone-a-board-for-a-team-chip-overview.html>

You take one board to an orderable state in a repository of your own, under one of two briefs: D, a bring-up Pmod for a digital project, or A, a source board for one analog pin on the demo board's analog header J13. Check it with:

```bash
cd ~/simproc-pmod                                                     # your board repository
cp ~/pcb101/labs/capstone-a-board-for-a-team-chip/DESIGN.md .          # once
~/pcb101/labs/capstone-a-board-for-a-team-chip/check.sh --brief D      # or --brief A; --pins FILE for Brief D
```

`check.sh --brief D|A [--pins FILE]` runs [`src/check_capstone.py`](src/check_capstone.py) in the course's pinned KiCad image. It prints one row per check and a last line, `PASS` or `FAIL`. Exit status 0 is PASS, 1 FAIL, 2 couldn't run.

| Row | Brief | Passes when |
|---|---|---|
| ci | both | Lab 05's check passes: `ci/build.sh` passes the board check, builds every output, and leaves nothing untracked |
| design | both | `DESIGN.md` has its four sections filled in and no TODO, at least 3 numbered requirements and 3 numbered decisions, every decision a value with its unit and a `Meets:` line, and every requirement met |
| history | both | at least 2 commits change a `.kicad_sch` or `.kicad_pcb` |
| pmod | D | Lab 04's check passes (`check_pmod.py --protect --bringup BRINGUP.md`, with `--pins` if given) |
| test points | D | every non-GND pin of a connector other than the Pmods has a test point on its net, or on the far side of a series resistor |
| connector | A | one `Conn_02x16` symbol, with pins 1, 6, 9, 14, 17, 22, 25, 30 and 31 on GND and pin 32 on a 3.3 V net or open, as J13 has them |
| pin | A | exactly one of J13's twelve analog lines connected (pins 4, 5, 7, 10, 12, 13, 20, 21, 23, 26, 28, 29), and none of the eight that are ground on the SKY130 breakout |
| filter | A | that pin's net has a two-pin capacitor to GND and a two-pin resistor to a source net |
| test points | A | a test point on the pin's net and on the source net |
| bringup | A | `BRINGUP.md` passes [`labs/common/check_bringup.py`](../common/check_bringup.py) |

J13's pinout is from `TinyTapeout/tt-demo-pcb` at bbf3dd1, where J13 is a `PinHeader_2x16_P2.54mm_Vertical` marked DNP, and the analog pad behind each line comes from the SKY130 breakout's J1 at `breakout-pcb` 91a2bf1.

| Repository | Last line of the check |
|---|---|
| Lab 04's board, Lab 05's CI and `DESIGN.md` from here, in one commit | `FAIL  pmod, Brief D: 2 of 5 capstone checks ok` |
| `solutions/simproc-pmod-brief-d/` on top of that, as a second commit | `PASS  pmod, Brief D: 5 of 5 capstone checks ok` |
| `solutions/source-board-brief-a/`, in two commits | `PASS  source, Brief A: 8 of 8 capstone checks ok` |

## Files

| File | What it is |
|---|---|
| `check.sh` | the capstone's check, on your board repository |
| `DESIGN.md` | the design note's template |
| `solutions/` | a reference for each brief; see its README |
| `src/check_capstone.py` | the check itself |
| `src/make_brief_d.py` | writes the Brief D reference board: Lab 04's, with TP3 and TP4 |
| `src/make_brief_a.py` | writes the Brief A reference board, and checks its socket's pads against J13's when the demo board is fetched |
| `src/selftest.py` | repositories with known verdicts, for testing the check itself (4 of 4; in our run it took 116 s with the container limited to one CPU) |
| `results/` | local outputs; never committed |

```bash
labs/common/kicad.sh python3 labs/capstone-a-board-for-a-team-chip/src/make_brief_d.py labs/capstone-a-board-for-a-team-chip/solutions/simproc-pmod-brief-d
python3 labs/common/fetch_boards.py tt-demo-pcb
labs/common/kicad.sh python3 labs/capstone-a-board-for-a-team-chip/src/make_brief_a.py labs/capstone-a-board-for-a-team-chip/solutions/source-board-brief-a
labs/common/kicad.sh python3 labs/capstone-a-board-for-a-team-chip/src/selftest.py
```
