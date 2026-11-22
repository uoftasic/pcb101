# Capstone references

Each folder is a whole board repository: the KiCad project, `DESIGN.md`, `BRINGUP.md`, and Lab 05's `ci/`, `.github/workflows/board.yml` and `.gitignore`. Nothing in either has been built or measured; every expected value is worked out from part values and the sources each `DESIGN.md` names.

| Folder | Brief | Board check in `kicad/kicad:10.0.5` | Capstone check |
|---|---|---|---|
| `simproc-pmod-brief-d/` | D: the SimProc Pmod | ERC 0; DRC 0 errors, 32 warnings (24 `silk_edge_clearance`, 6 `silk_over_copper`, 2 `silk_overlap`); 0 unconnected; 0 parity | `PASS  pmod, Brief D: 5 of 5 capstone checks ok` |
| `source-board-brief-a/` | A: a source for an0 on J13 | ERC 0; DRC 0 errors, 0 warnings; 0 unconnected; 0 parity | `PASS  source, Brief A: 8 of 8 capstone checks ok` |

## Brief D

Lab 04's reference board with two test points, written by [`../src/make_brief_d.py`](../src/make_brief_d.py):

| Part | Footprint | Net | Where (mm) |
|---|---|---|---|
| TP3 | `TestPoint:TestPoint_Pad_D1.5mm` | `UART_RX` (`ui[0]`, between J1 and R1) | (117.3, 60.0), on a track from (114.70, 59.0) |
| TP4 | same | `DONGLE_RXD` (`uo[0]`, between R2 and J4) | (119.0, 73.2), on a track from the via under R2 at (119.0, 71.08) |

TP3 sits below the Pmod connectors' courtyards, which reach down to Y 58.2 mm. Its reference is above it and 1 mm to the right, clear of R1's, which is above R1. TP4's reference is moved under it, clear of TP2's. `BRINGUP.md` is Lab 04's, with steps 6 and 7 read at TP4 and TP3. The two `silk_overlap` warnings are Lab 04's, R3's reference over SW1's outline.

## Brief A

A 50 × 30 mm board, written by [`../src/make_brief_a.py`](../src/make_brief_a.py):

| Part | Value | Footprint | Nets | Where (mm, degrees) |
|---|---|---|---|---|
| J1 | socket for J13 | `Connector_PinSocket_2.54mm:PinSocket_2x16_P2.54mm_Vertical`, on the bottom | GND on 1, 6, 9, 14, 17, 22, 25, 30, 31; +3V3 on 32; AN0 on 4; the rest open | pad 1 at (106, 76), flipped, 270° |
| RV1 | 1 kΩ | `Potentiometer_THT:Potentiometer_Bourns_3296W_Vertical` | +3V3, SET, GND | (134, 58), 0° |
| R1 | 1 kΩ | `Resistor_SMD:R_0805_2012Metric_Pad1.20x1.40mm_HandSolder` | SET to AN0 | (122, 62), 180° |
| C1 | 10 nF | `Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder` | AN0 to GND | (112, 66), 270° |
| TP1, TP2 | test points | `TestPoint:TestPoint_Pad_D1.5mm` | SET, AN0 | (131.46, 64.5), (116, 64.5) |

Of the eight ways to place J1 (four angles, either side), only flipped and turned 270° puts its 32 pads over J13's, pad for pad, seen from above; the generator compares the two patterns against the fetched demo board and stops if they differ. `DESIGN.md` assumes a sample rate of 400 kS/s for the droop in its decision 5, and says so; CrossWalk's documentation doesn't give one yet.
