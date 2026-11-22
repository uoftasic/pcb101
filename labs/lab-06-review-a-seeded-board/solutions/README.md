# Lab 06 reference: the planted faults

Don't read this until you've done the lab.

`board/` is Lab 04's reference SimProc Pmod with eight faults planted in it by [`../src/make_seeded.py`](../src/make_seeded.py). Its board check passes (ERC 0, DRC 0 errors and 32 warnings, 0 unconnected, 0 parity, in `kicad/kicad:10.0.5`), because every fault agrees with the board's own schematic and rules. Lab 04's check (`check_pmod.py --protect`) fails on the connectors row and passes the power row, and it checks none of the pins, the dongle header or the protection until the connectors pass. With J3 moved back to 22.86 mm, it fails on `ui[0]` (no capacitor within 3 mm of U1's VCC pin; the nearest, C1, is 35.50 mm away) and on `uo[0]` (U1 turned round on that line), so it looks for three of the faults, J3 among them, and not for the other five.

| # | Fault | Where | Checklist line | Found by Lab 04's check? |
|---|---|---|---|---|
| 1 | J4's footprint is `PinHeader_1x03_P2.00mm_Vertical`, a 2.00 mm header; a dongle's jumper wires fit 2.54 mm | J4 | 1, footprints against datasheets | no |
| 2 | `uio6` and `uio7` cross between RN1 and SW1, so switch 7 sets `uio7` and switch 8 sets `uio6`, against the other six and the silkscreen (Tiny Tapeout's TT07 breakout erratum, on a smaller scale) | SW1 (or RN1) | 3, connections against the pin list | no: it checks that each line has a switch, not which one |
| 3 | U1's second buffer is turned round: SimProc's TX (J3 pin 1) is on its output 2Y (pin 4), and its input 2A (pin 3) goes through R2 to the dongle's RXD, so U1 and SimProc drive `uo[0]` against each other and nothing drives the dongle's RXD | U1 | 3, connections against the pin list (or 5, I/O voltages) | yes, once J3 is put back: `uo[0]`, "U1 (74LVC2G17) is turned round on this line" |
| 4 | C1, U1's decoupling capacitor, is below J3 at the right of the board, 35.5 mm from U1's VCC pin | C1 (or U1) | 4, decoupling | yes, once J3 is put back: `ui[0]`, "no decoupling at U1's VCC" (`uo[0]` stops at the turned-round buffer before it measures) |
| 5 | `BRINGUP.md` switches the kit off before unplugging the dongle, at the end of the steps and when a reading is wrong; meanwhile the dongle drives U1's unpowered input, and R4 feeds up to 33 µA through R3 into the kit's +3V3 | `BRINGUP.md` | 7, back-powering | no |
| 6 | `BRINGUP.md` step 7 measures at TP3, which the board doesn't have | `BRINGUP.md` (or TP3) | 8, test points | no |
| 7 | Board Setup's minimum text height and thickness are 0.8 mm and 0.1 mm, under JLCPCB's 1.0 mm and 0.15 mm, and the "SimProc Pmod" legend is 0.8 mm high with 0.1 mm strokes, so DRC passes it | `pmod.kicad_pro`, the silkscreen | 9, fabricator rules | no; with the template's rules DRC gives a `text_height` and a `text_thickness` warning |
| 8 | J3 is at X 148.22 mm, 23.36 mm from J2 | J3 | 10, mechanical fit | yes, `connectors` |

Lines 2 (pin 1) and 6 (ESD) have no planted fault. [`faults.json`](faults.json) is the same list in the form `src/make_key.py` hashes into `data/review-key.json`, with the words of a Where cell that find each fault.

For fault 3, `uo[0]` comes up the right of R2 to U1's pin 4 at X 120.1 mm, where Lab 04's board has C1; that is the room fault 4 leaves. C1 takes its +3V3_PMOD from SW1's common, along a track from SW1's right end, and has its own via to ground at (156.0, 61.96); Lab 04's via beside C1's place on that board, at (122.94, 64.4), is left out. With C1 gone from beside U1, a piece of the top layer's ground pour between J1, R1, U1, TP2, R3 and J2 has no ground of its own, so the seeded board has a via at (118, 58) for it (without it DRC reports a `starved_thermal` error on J1's pad 11).

`simproc-pmod/REVIEW.md` finds all eight. `simproc-pmod/QUOTE.md` shows the format only: we didn't upload the files to a fabricator, so its price and build time are JLCPCB's advertised "From $2.00 / 5 pcs" and "Build Time: 24 hours", not a quote, and its DFM field says none was obtained. Its commit hash, `0000000`, is a placeholder that the self-test replaces with its own repository's.
