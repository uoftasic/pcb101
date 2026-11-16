# Lab 03 reference: the SimProc Pmod

`simproc-pmod/` is one board that passes the Lab 03 check: `PASS  pmod.kicad_pro: board check PASS; 14 of 14 Pmod checks ok` (ERC 0, DRC 0 errors and 30 warnings, 0 unconnected, 0 parity, in `kicad/kicad:10.0.8`). Open it after your own check passes. It was written by [`../src/make_reference.py`](../src/make_reference.py) `routed`, not drawn by hand, so its schematic is tidy rather than pretty.

| Part | Value | Footprint | Where (mm, degrees) |
|---|---|---|---|
| J1, J2, J3 | `PMOD_PERIPH_2x6` | `TinyTapeout_PMOD:PinHeader_2x06_P2.54mm_PMODPeriph2B` | (102.00, 56.35), (124.86, 56.35), (147.72, 56.35), all 90°, locked |
| J4 | 1 × 3 header: 1 GND, 2 `UART_RX`, 3 `UART_TX` | `Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical` | (110.0, 66.0), 0° |
| SW1 | `SW_DIP_x08`, switch *k* on `uio[k-1]` | `Button_Switch_THT:SW_DIP_SPSTx08_Slide_9.78x22.5mm_W7.62mm_P2.54mm` | (146.45, 67.0), 270° |
| RN1 | 10 kΩ × 8, bussed (`R_Network08`) | `Resistor_THT:R_Array_SIP9` | (126.13, 62.5), 0° |

| | |
|---|---|
| Outline | 64 × 32 mm, (100, 50) to (164, 82); the top edge 6.35 mm above each connector's lower row of pads |
| Tracks | 0.25 mm for signals, 0.4 mm for `+3V3` |
| `uio[7:4]` | from J2's upper row through the gaps of its lower row, straight down on F.Cu |
| `uio[3:0]` | from J2's lower row on B.Cu, across to the right, then F.Cu to SW1 |
| `+3V3` | pins 12 joined along the top edge, each pin 6 to its pin 12, J2's pin 6 down the left of RN1 to SW1's lower row |
| GND | a zone on each layer over the whole board |

The 30 DRC warnings all come from Tiny Tapeout's Pmod footprint: 24 `silk_edge_clearance` (seven silkscreen segments and the reference of each connector past the edge) and 6 `silk_over_copper` (silkscreen around pads 5 and 11).
