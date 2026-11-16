# Lab 01 reference solution

| File | What it is |
|---|---|
| `breakout-notes.md` | notes on the SKY130 breakout that `src/check_notes.py` passes |

| Rail | Comes from | Through | Volts | Capacitors |
|---|---|---|---|---|
| VCCD | +3V3 | R2, U1, R14 | 1.8 | 6 (3 × 1 µF, 3 × 100 nF) |
| VDD_IO | +3V3 | R4, R8, R13 | 3.3 | 5 (2 × 1 µF, 3 × 100 nF) |
| VDDA | +3V3 | R4, R8, R15 | 3.3 | 8 (4 × 1 µF, 4 × 100 nF) |

Not fitted: R1, R3, R6, R7, R11, R12, U2, U3 and J2, and the fiducials FID1 to FID3.
