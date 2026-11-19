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
| 3 | R1 | 5 | R1 is 0 Ω, so with the kit off and the dongle on, nothing limits the current from the dongle's TXD into `ui[0]`. `BRINGUP.md` says R1 is 1 kΩ. | Make R1 1 kΩ, as `BRINGUP.md` assumes: at most 2.7 mA into an unpowered chip, and a 22 ns edge with 10 pF. |
| 4 | D1 | 6 | D1's pin 3, the SP0502BAHT's common pin, is on +3V3 instead of GND, so neither dongle line has a clamp to ground. | Connect pin 3 to GND with a short track and a via, next to J4. |
| 5 | BRINGUP.md | 7 | The plan switches the kit off before the dongle comes off J4, at the end of the steps and when a reading is wrong, so the powered dongle drives `ui[0]` of an unpowered chip every time the kit is switched off. | Unplug the dongle from J4 first, then switch the kit off, in both places. |
| 6 | BRINGUP.md, TP3 | 8 | Step 6 measures `ui[0]` at TP3, and the board has no TP3, only TP1 and TP2. | Add a test point on `UART_RX`, or measure at J1 pin 1 and say so in the step. |
| 7 | pmod.kicad_pro, silkscreen | 9 | Board Setup's minimum text height and thickness are 0.8 mm and 0.1 mm, below JLCPCB's 1.0 mm and 0.15 mm, so DRC passes the "SimProc Pmod" legend, which is 0.8 mm high with 0.1 mm strokes. | Put the minimums back to 1.0 mm and 0.15 mm, and make the legend 1.0 mm high with 0.15 mm strokes. |
| 8 | J3 | 10 | J3 is at X 148.22 mm, 23.36 mm from J2 instead of 22.86 mm, so the board won't plug into the demo board's three sockets. | Move J3 to X 147.72 mm with Position Relative To, lock it, and move R2 with it. |
