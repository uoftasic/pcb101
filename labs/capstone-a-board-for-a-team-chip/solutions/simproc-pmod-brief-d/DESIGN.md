# Design note: SimProc Pmod

<!--
  IC103 capstone, Brief D reference. The numbers come from Labs 03 and 04, Tiny Tapeout's
  GPIO spec and demo board files, and SimProc's RTL, as the course pages cite them. Nothing
  on this board has been built or measured.
-->

Brief: D. Project: SimProc, `tt_um_ieeeuoftasic_simproc` (uoftasic/simproc), on a TTSKY25b kit. Board: a 2-layer Pmod across the demo board's three I/O sockets, with a header for a 3.3 V USB-UART dongle and eight switches that set SimProc's bit period.

## Requirements

1. Connect SimProc's UART: `ui[0]`, its receiver, to the dongle's TXD, and `uo[0]`, its transmitter, to the dongle's RXD.
2. Set `uio[0..7]`, which SimProc reads as `clk_per_bit` / 4, from switches, with each line at 0 V when its switch is off.
3. Fit the demo board's sockets: three Pmod connectors 22.86 mm apart, input, bidirectional and output from left to right.
4. Limit the current into a pin of an unpowered chip from the dongle to a few mA, well under the 20 mA at which Horowitz and Hill say clamp current starts to damage a part or latch it up.
5. Put an ESD clamp to ground on every signal pin of the dongle header, the board's only connection to a cable.
6. Keep each UART edge much shorter than one bit, 8.7 µs at 115,200 baud.
7. Stay inside the chip's I/O ratings on the demo board: 3.3 V logic, inputs not 5 V tolerant, 4 mA per output.
8. Give a multimeter somewhere to read the board's own current and both UART lines.
9. Use parts a student can solder with an iron: 0805 or larger, SOT-23, or through-hole.

## Decisions

1. J1, J2 and J3 are Tiny Tapeout's `PinHeader_2x06_P2.54mm_PMODPeriph2B`, at X 102.00, 124.86 and 147.72 mm, 22.86 mm apart, and locked, with J1 in the input socket, J2 in the bidirectional one and J3 in the output one.
   Meets: 1, 3
2. J4 is a 1 × 3 header with a 2.54 mm pitch: pin 1 GND, pin 2 to the dongle's TXD (`ui[0]`), pin 3 to its RXD (`uo[0]`). The dongle's VCC isn't connected, so the dongle never powers the board.
   Meets: 1, 7
3. SW1 is an 8-way DIP switch from `+3V3_PMOD` to each `uio` line, and RN1 a 10 kΩ bussed network that pulls each line to GND, so a switch that's off reads 0 V and one that's on draws 3.3 V / 10 kΩ = 0.33 mA.
   Meets: 2, 7
4. R1 and R2 are 1 kΩ in series with `ui[0]` and `uo[0]`. With the kit off and the dongle on, at most (3.3 V − 0.6 V) / 1 kΩ = 2.7 mA flows into `ui[0]`; R2 limits the current into the dongle's RXD the same way when the dongle is off. Into 10 pF, each makes an edge of 2.2 × 1 kΩ × 10 pF = 22 ns.
   Meets: 4, 6
5. D1 is an SP0502BAHT, a two-line TVS array with a 5.5 V standoff, in SOT-23, on J4 pins 2 and 3, with its common pin 3 to GND through a via. It sits between J4 and the series resistors, so a discharge from the cable meets the clamp before the resistor and the chip.
   Meets: 5, 9
6. R3 is a 10 Ω current spy from the sockets' +3V3 to `+3V3_PMOD`, which feeds SW1, with TP1 and TP2 on its two sides. With three switches on the board draws 0.99 mA and R3 drops 9.9 mV.
   Meets: 8
7. TP3 is on `ui[0]` between J1 and R1, and TP4 on `uo[0]` between R2 and J4, each a 1.5 mm pad.
   Meets: 8
8. The resistors are 0805 with hand-soldering pads, D1 is SOT-23, whose two leads on one side are 1.9 mm apart, and SW1, RN1 and the connectors are through-hole.
   Meets: 9
9. Nothing on the board drives a chip pin above 3.3 V: the switches take `+3V3_PMOD` from the demo board's own 3.3 V, and the dongle must be a 3.3 V one. The fastest signal is the UART at 113,636 baud, far below the 33 MHz the GPIO spec gives for outputs.
   Meets: 7

## Checks

- The board check passes in `kicad/kicad:10.0.5`: ERC 0, DRC 0 errors and 33 warnings (24 `silk_edge_clearance` and 6 `silk_over_copper` from Tiny Tapeout's Pmod footprint, 3 `silk_overlap`), 0 unconnected items, 0 parity items.
- Lab 04's check passes: 17 of 17 Pmod checks, and the bring-up plan.
- Lab 05's check passes on the repository: the fabrication files, the review images and the `.gitignore`.
- Against the course checklist: J4's pitch is 2.54 mm (line 1); the connections match SimProc's pin list, with switch *k* on `uio[k−1]` (line 3); there are no ICs, so nothing needs decoupling (line 4); D1's pin 3, its common pin, is on GND (line 6); `BRINGUP.md` unplugs the dongle before the kit is switched off (line 7) and measures only at TP1 to TP4 and connector pins (line 8); Board Setup holds JLCPCB's minimums, 1.0 mm text and 0.15 mm strokes (line 9).

## Open questions

- Whether the team has a TTSKY25b kit, with SimProc on it, to bring this board up on.
- SimProc's pinout puts its transmitter on `uo_out[0]`, which the RP2350 demo board's pin table gives a hardware UART receiver, and its receiver on `ui_in[0]`, which has no UART function there. Demo board firmware that drove `ui[0]` with a software UART would make this board unnecessary for a first test; Tiny Tapeout's firmware README doesn't mention one.
