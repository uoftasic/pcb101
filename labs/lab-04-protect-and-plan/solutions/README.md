# Lab 04 reference: the protected SimProc Pmod

`simproc-pmod/` is Lab 03's reference board with the Lab 04 parts added, and its `BRINGUP.md`. It passes the Lab 04 check: `PASS  pmod.kicad_pro: board check PASS; 17 of 17 Pmod checks ok; bring-up plan PASS` (ERC 0, DRC 0 errors and 32 warnings, 0 unconnected, 0 parity, in `kicad/kicad:10.0.5`). It was written by Lab 03's [`make_reference.py`](../../lab-03-a-pmod-for-one-projects-pins/src/make_reference.py) `protected`. The outline is still 64 × 32 mm.

| Part | Value | Footprint | Net | Where (mm, degrees) |
|---|---|---|---|---|
| U1 | `74LVC2G17` | `Package_TO_SOT_SMD:SOT-23-6` | 1A (pin 1) `DONGLE_TXD`, 1Y (pin 6) `RX_BUF`, 2A (pin 3) `UART_TX`, 2Y (pin 4) `TX_BUF`, VCC (pin 5) `+3V3`, GND (pin 2) through a via | (117.8625, 64.6), 0° |
| R1 | 1 kΩ | `R_0805_2012Metric_Pad1.20x1.40mm_HandSolder` | `UART_RX` to `RX_BUF` | (114.70, 61.5), 270° |
| R2 | 1 kΩ | same | `TX_BUF` to `DONGLE_RXD`, which goes through a via at (119.0, 71.08) and along B.Cu to J4 pin 3 | (119.0, 68.6), 270° |
| R4 | 100 kΩ | same | `+3V3`, from J1 pin 6, to `DONGLE_TXD` | (112.4, 61.6), 270° |
| C1 | 100 nF | `C_0805_2012Metric_Pad1.18x1.45mm_HandSolder` | `+3V3` to GND through a via; pad 1 is 2.24 mm from U1 pin 5 | (121.0, 66.6375), 270° |
| D1 | `SP0502BAHT` | `Package_TO_SOT_SMD:SOT-23` | pins 1 and 2 on `DONGLE_TXD` and `DONGLE_RXD`, pin 3 on GND through a via | (113.9, 69.49), 0° |
| R3 | 10 Ω | `R_0805_2012Metric_Pad1.20x1.40mm_HandSolder` | `+3V3` to `+3V3_PMOD`, which feeds SW1 | (124.86, 66.4), 270° |
| TP1, TP2 | test points | `TestPoint:TestPoint_Pad_D1.5mm` | `+3V3`, `+3V3_PMOD` | (121.5, 63.0), (121.5, 70.0) |

The DRC warnings are Lab 03's 30 and 2 `silk_overlap` (R3's reference over SW1's outline). Two GND vias, at (106, 58.4) and (118, 58), connect pieces of the top layer's ground pour that R4's +3V3 track and the ring through R1, U1 and C1 cut off; without them DRC reports a `starved_thermal` error on J1's pads 5 and 11. Every expected value in `BRINGUP.md` is worked out from the part values, SimProc's RTL (`clk_per_bit` = `uio` × 4, `PING` answers 0xAA, `uo_out` = 3 while idle), TI's SN74LVC2G17 datasheet (Ioff, ICC) and Tiny Tapeout's ETR demo board guide (180 to 200 mA at 5 V on the factory test). None of it has been measured, because no board has been made.
