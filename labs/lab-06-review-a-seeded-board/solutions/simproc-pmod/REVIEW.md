# Review: the seeded SimProc Pmod

<!--
  PCB101 Lab 06 reference review. It finds all eight planted faults; the course check needs 5.
-->

Reviewer: PCB101 reference

Board: `labs/lab-06-review-a-seeded-board/board/` in the course repo.

## Findings

| # | Where | Line | What's wrong | What to change |
|---|---|---|---|---|
| 1 | J4 | 1 | The footprint is `PinHeader_1x03_P2.00mm_Vertical`, a 2.00 mm header. The dongle's jumper wires fit 2.54 mm pins, and the silkscreen labels beside J4 are spaced for 2.54 mm. | Use `Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical` and re-route pins 2 and 3. |
| 2 | SW1 | 3 | `uio6` and `uio7` are crossed between RN1 and SW1: switch 7 sets `uio7` and switch 8 sets `uio6`, the reverse of the other six switches and of the silkscreen, which puts `uio7` at switch 8. Set by the legend, the bit period is wrong whenever those two bits differ. | Connect SW1 pin 7 to `UIO6` and pin 8 to `UIO7`, and route them straight down as the others are. |
| 3 | U1 | 3 | U1's second buffer is turned round: SimProc's TX on J3 pin 1 goes to its output, 2Y (pin 4), and its input, 2A (pin 3), goes through R2 to the dongle's RXD. With the kit on, U1 and SimProc both drive `uo[0]`, with nothing between them, and nothing drives the dongle's RXD. On the schematic the second triangle points at J3. | Turn it round: J3 pin 1 to 2A (pin 3), and 2Y (pin 4) through R2 to J4 pin 3, as `BRINGUP.md` describes, then re-route the two tracks. |
| 4 | C1 | 4 | C1, U1's decoupling capacitor, is below J3 at the right of the board, 35.5 mm from U1's VCC pin, so it does nothing for U1. | Move C1 next to U1, with its +3V3_PMOD pad within a few millimetres of pin 5 and a via to ground beside its other pad. |
| 5 | BRINGUP.md | 7 | The plan switches the kit off before the dongle comes off J4, at the end of the steps and when a reading is wrong, against checklist line 7. Every time the kit goes off first, the powered dongle drives U1's unpowered input and, through R4 and R3, feeds up to 33 µA into the kit's +3V3. | Unplug the dongle from J4 first, then switch the kit off, in both places. |
| 6 | BRINGUP.md, TP3 | 8 | Step 7 measures `ui[0]` at TP3, and the board has no TP3, only TP1 and TP2. | Add a test point on `UART_RX`, or measure at J1 pin 1 and say so in the step. |
| 7 | pmod.kicad_pro, silkscreen | 9 | Board Setup's minimum text height and thickness are 0.8 mm and 0.1 mm, below JLCPCB's 1.0 mm and 0.15 mm, so DRC passes the "SimProc Pmod" legend, which is 0.8 mm high with 0.1 mm strokes. | Put the minimums back to 1.0 mm and 0.15 mm, and make the legend 1.0 mm high with 0.15 mm strokes. |
| 8 | J3 | 10 | J3 is at X 148.22 mm, 23.36 mm from J2 instead of 22.86 mm, so the board won't plug into the demo board's three sockets. | Move J3 to X 147.72 mm with Position Relative To, lock it, and re-route the tracks from its pins 1 and 6. |
