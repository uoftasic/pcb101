# Lab 06 reference: the planted faults

Don't read this until you've done the lab.

`board/` is Lab 04's reference SimProc Pmod with eight faults planted in it by [`../src/make_seeded.py`](../src/make_seeded.py). Its board check passes (ERC 0, DRC 0 errors and 32 warnings, 0 unconnected, 0 parity, in `kicad/kicad:10.0.8`), because every fault agrees with the board's own schematic and rules. Lab 04's check (`check_pmod.py --protect`) fails on the connectors row and passes the power row, and it checks none of the pins, the dongle header or the protection until the connectors pass. With J3 moved back to 22.86 mm, it fails on `ui[0]`, `ESD J4.2` and `ESD J4.3`, so it looks for three of the faults and not for the other five.

| # | Fault | Where | Checklist line | Found by Lab 04's check? |
|---|---|---|---|---|
| 1 | J4's footprint is `PinHeader_1x03_P2.00mm_Vertical`, a 2.00 mm header; a dongle's jumper wires fit 2.54 mm | J4 | 1, footprints against datasheets | no |
| 2 | `uio6` and `uio7` cross between RN1 and SW1, so switch 7 sets `uio7` and switch 8 sets `uio6`, against the other six and the silkscreen (Tiny Tapeout's TT07 breakout erratum, on a smaller scale) | SW1 (or RN1) | 3, connections against the pin list | no: it checks that each line has a switch, not which one |
| 3 | R1 is 0 Ω, so nothing limits the current from the dongle into `ui[0]` of an unpowered chip | R1 | 5, I/O voltages (or 7, back-powering) | yes, `ui[0]`: "its value '0' isn't a resistance the check can read" |
| 4 | D1's pin 3, the SP0502BAHT's common pin, is on +3V3 instead of GND | D1 | 6, ESD | yes, `ESD J4.2` and `ESD J4.3` |
| 5 | `BRINGUP.md` switches the kit off before unplugging the dongle, at the end of the steps and when a reading is wrong | `BRINGUP.md` | 7, back-powering | no |
| 6 | `BRINGUP.md` step 6 measures at TP3, which the board doesn't have | `BRINGUP.md` (or TP3) | 8, test points | no |
| 7 | Board Setup's minimum text height and thickness are 0.8 mm and 0.1 mm, under JLCPCB's 1.0 mm and 0.15 mm, and the "SimProc Pmod" legend is 0.8 mm high with 0.1 mm strokes, so DRC passes it | `pmod.kicad_pro`, the silkscreen | 9, fabricator rules | no; with the template's rules DRC gives a `text_height` and a `text_thickness` warning |
| 8 | J3 is at X 148.22 mm, 23.36 mm from J2 | J3 | 10, mechanical fit | yes, `connectors` |

Lines 2 (pin 1) and 4 (decoupling) have no planted fault. [`faults.json`](faults.json) is the same list in the form `src/make_key.py` hashes into `data/review-key.json`, with the words of a Where cell that find each fault.

To make room for fault 4, Lab 04's GND via at (116, 69.49), which carried D1's pin 3 to the ground plane, moves to (118, 58), between J1 and J2. Without a via there, the top layer's ground pour between the connectors is an island connected only to J1's pad 11, and DRC reports a `starved_thermal` error on that pad.

`simproc-pmod/REVIEW.md` finds all eight. `simproc-pmod/QUOTE.md` shows the format only: we didn't upload the files to a fabricator, so its price and build time are JLCPCB's advertised "From $2.00 / 5 pcs" and "Build Time: 24 hours", not a quote, and its DFM field says none was obtained. Its commit hash, `0000000`, is a placeholder that the self-test replaces with its own repository's.
