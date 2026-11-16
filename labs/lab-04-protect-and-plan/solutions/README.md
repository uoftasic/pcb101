# Lab 04 reference: the SimProc Pmod, protected

`simproc-pmod/` is Lab 03's reference board with the Lab 04 parts added, and its `BRINGUP.md`. It passes the Lab 04 check: `PASS  pmod.kicad_pro: board check PASS; 17 of 17 Pmod checks ok; bring-up plan PASS` (ERC 0, DRC 0 errors and 32 warnings, 0 unconnected, 0 parity, in `kicad/kicad:10.0.8`). It was written by Lab 03's [`make_reference.py`](../../lab-03-a-pmod-for-one-projects-pins/src/make_reference.py) `protected`.

| Part | Value | Footprint | Net | Where (mm, degrees) |
|---|---|---|---|---|
| R1 | 1 kΩ | `R_0805_2012Metric_Pad1.20x1.40mm_HandSolder` | `UART_RX` to `DONGLE_TXD` | (114.70, 61.5), 270° |
| R2 | 1 kΩ | same | `UART_TX` to `DONGLE_RXD` | (160.42, 61.5), 270° |
| D1 | `SP0502BAHT` | `Package_TO_SOT_SMD:SOT-23` | pins 1 and 2 on `DONGLE_TXD` and `DONGLE_RXD`, pin 3 on GND through a via | (113.9, 69.49), 0° |
| R3 | 10 Ω | `R_0805_2012Metric_Pad1.20x1.40mm_HandSolder` | `+3V3` to `+3V3_PMOD`, which feeds SW1 | (124.86, 66.4), 270° |
| TP1, TP2 | test points | `TestPoint:TestPoint_Pad_D1.5mm` | `+3V3`, `+3V3_PMOD` | (121.5, 63.0), (121.5, 70.0) |

The DRC warnings are Lab 03's 30 and 2 `silk_overlap`. Every expected value in `BRINGUP.md` is worked out from the part values, SimProc's RTL (`clk_per_bit` = `uio` × 4, `PING` answers 0xAA, `uo_out` = 3 while idle) and Tiny Tapeout's ETR demo board guide (180 to 200 mA at 5 V on the factory test). None of it has been measured, because no board has been made.
