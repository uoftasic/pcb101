# Notes on Tiny Tapeout's SKY130 QFN breakout, rev 3.2

<!-- Reference solution for Lab 01. check_notes.py prints PASS on it. -->

## Not fitted

R1, R3, R6, R7, R11, R12, U2, U3, J2, and the fiducials FID1, FID2 and FID3.

<!--
  The check reads every reference designator in this section, so the explanation is in a
  comment. The fiducials carry DNP as well, because there is nothing to place on them:
  each is a bare copper dot that the assembly machine's camera lines the board up by. The
  four test points are left out of the BOM but aren't DNP, because a test point here is a
  bare pad on the board rather than a part.
-->


## Supply rails

| Rail | Chip pins | Comes from | Through | Volts | Capacitors |
|---|---|---|---|---|---|
| VCCD | 18, 49, 63 | +3V3 | R2, U1, R14 | 1.8 | C1, C3, C5, C20, C23, C24 |
| VDD_IO | 17, 64 | +3V3 | R4, R8, R13 | 3.3 | C2, C4, C16, C17, C25 |
| VDDA | 9, 30, 40, 47 | +3V3 | R4, R8, R15 | 3.3 | C8, C10, C12, C14, C9, C11, C13, C15 |

+3V3 arrives on J1 pin 1 and J3 pins 8 and 10. U2, the second AP2112K-1.8, is DNP, and R8
connects its input net straight to its output net, so VDD_IO and VDDA get the demo board's
3.3 V with no regulator in between. +5V reaches the board on J3 pins 2 and 4 and goes
nowhere: R1 and R3, the links that would take it to the regulators, are DNP.

## Checks

| Check | Severity | Type | Count | What it means |
|---|---|---|---|---|
| ERC | error | all | 10 | |
| ERC | error | power_pin_not_driven | 8 | A power-input pin on a net that no power-output pin drives. +3V3, +5V and GND come in through the connectors, whose pins are passive, and VCCD, VDD_IO, VDDA and the two regulator inputs are fed through 0 ohm resistors, which ERC treats as passive too. ERC can't tell that anything powers them. |
| ERC | error | pin_to_pin | 2 | A PWR_FLAG (a power output) sits on each regulator's output net, which the regulator's VOUT pin already drives, so two power outputs are connected. |
| DRC | error | all | 0 | |
| DRC | excluded | all | 1 | |
| DRC | excluded | courtyards_overlap | 1 | The courtyards of J2 and TP4 overlap. The designer marked it as excluded in the board file, so it doesn't count as an error. J2 is DNP, so nothing is ever placed there to collide with TP4. |
| ERC | warning | lib_symbol_mismatch | 69 | The symbol saved in the schematic differs from the one in today's library. |
| DRC | warning | lib_footprint_issues | 76 | The board names footprint libraries this setup doesn't have: flyingcarsfootprints (the stitching vias and a logo) and Logos. |
