# Bring-up plan: SimProc Pmod

<!--
  PCB101 capstone, Brief D reference: Lab 04's plan, with steps 6 and 7 read at the test
  points TP4 and TP3 that the capstone board adds. Every expected value is worked out from
  the schematic's part values, SimProc's RTL (clk_per_bit = uio x 4, PING answers 0xAA,
  uo_out = 3 while idle), TI's SN74LVC2G17 datasheet (Ioff and ICC at most 10 uA, II at most
  5 uA), the RP2350's 36-113 kOhm pull-down and Tiny Tapeout's ETR demo board guide
  (180-200 mA at 5 V on the factory test). Nothing here has been measured.
-->

The board: the SimProc Pmod from PCB101 Labs 03 and 04 and the capstone, for `tt_um_ieeeuoftasic_simproc` on a TTSKY25b kit, with the buffer U1 and the resistors R1 and R2 on the UART lines, the ESD array D1, the current spy R3, and test points TP3 on `ui[0]` and TP4 on `uo[0]`.

## Lines that leave the board

| Line | Driven by | Drives | Kit off, dongle powered | Kit on, dongle unpowered |
|---|---|---|---|---|
| `ui[0]`, UART into the chip | U1's first buffer, through R1 (1 kΩ); U1's input is the dongle's TXD, held high by R4 (100 kΩ) when no dongle is plugged in | SimProc's UART receiver, the RP2350's GPIO17 (pulled down by 36 to 113 kΩ), and the demo board's DIP switch 1 when it's on | U1 is unpowered, so its input takes TXD's 3.3 V, and at most 10 µA (Ioff) gets through it to `ui[0]`. R4 passes at most 3.3 V / 100 kΩ = 33 µA from TXD into +3V3_PMOD, and through R3 into the kit's +3V3 | U1 drives `ui[0]` from its input; an unpowered dongle's TXD can pull R4's 100 kΩ down to about 0.6 V through its own clamp diode, so U1 then holds `ui[0]` low; keep the dongle powered whenever it's plugged into J4 |
| `uo[0]`, UART out of the chip | SimProc's TX; past U1's second buffer, U1 drives J4 through R2 (1 kΩ) | U1's input (at most 5 µA), the RP2350's GPIO33 (UART0 RX), and segment A of the display through 510 Ω; through U1 and R2, the dongle's RXD | SimProc's output and U1 are unpowered; the dongle's RXD pull-up pushes at most 10 µA (Ioff) into U1's output through R2, and none of it reaches `uo[0]`, on U1's input side | U1 drives the dongle's unpowered RXD high; R2 limits the current through the dongle's clamp diode to at most (3.3 − 0.6) V / 1 kΩ = 2.7 mA |
| `uio[0..7]`, the bit period | SW1, from `+3V3_PMOD` (+3V3 after R3), with RN1 (10 kΩ) pulling each line to GND | SimProc's `uio` inputs (`uio_oe` is 0) and the RP2350's GPIO25 to GPIO32 | the switches take their 3.3 V from the kit: a line whose switch is off sits at 0 V, and one whose switch is on sits wherever R4's 33 µA lifts `+3V3_PMOD` (see the +3V3 row) | not affected by the dongle; a switch that's on drives 3.3 V, so the RP2350 must not drive these pins |
| +3V3 from the Pmod sockets | the demo board's regulator, through pins 6 and 12 of J1 to J3 | through R3 (+3V3_PMOD): U1 (at most 10 µA, decoupled by C1), R4 and SW1's commons; the pull-downs draw 0.33 mA per switch that's on | 0 V from the kit, but the dongle's TXD feeds up to 33 µA into it through R4 and R3, which lifts the kit's +3V3 by an amount set by its load | 3.3 V |

## Settings

- Current limit: 10 mA on the bench supply for the board alone; the kit runs from USB through a USB power meter, and we stop if it reads more than 250 mA.
- Demo board firmware mode: `ASIC_MANUAL_INPUTS` in SimProc's section of `config.ini`, so the RP2350 doesn't drive `ui[0]`, and none of the RP2350's `uio` pins set as outputs.
- Demo board DIP switches: all off. Switch 1 would pull `ui[0]` to +3V3 through 1 kΩ against U1 and R1, which leaves the line at 3.3 V × 1 kΩ / 2 kΩ = 1.65 V whenever U1 drives it low.
- Your board's switches: `uio` = 22 (0b0001_0110), so switches 2, 3 and 5 on and the rest off.
- Clock: 10 MHz from the demo board, so `clk_per_bit` = 22 × 4 = 88 and the UART runs at 10 MHz / 88 = 113,636 baud, 1.4 % below 115,200.

## Before power

Checks with nothing powered, on the board on its own, with a multimeter.

1. Resistance from TP1 (+3V3) to J4 pin 1 (GND), with every switch of SW1 off. Expect: more than 1 MΩ (the meter shows OL) once C1 has charged, after a moment in which the reading climbs, because only C1 and U1's supply pins, through R3, join +3V3 to GND while the switches are off.
2. The same with all eight switches on. Expect: R3 plus the eight pull-downs in parallel, 10 Ω + 10 kΩ / 8 = 1.26 kΩ.
3. Resistance across R1, from J1 pin 1 to R1's other pad, and across R2, from J4 pin 3 to R2's other pad. Expect: 1.00 kΩ each. U1 is between J4 and J1, and between J3 and J4, so a reading from header to header says nothing.
4. Resistance from J4 pin 2 to TP2. Expect: 100 kΩ, R4, which goes to +3V3_PMOD.
5. Resistance from J4 pin 2 to GND and from J4 pin 3 to GND, with every switch off. Expect: more than 1 MΩ each, because D1 doesn't conduct below its 5.5 V standoff voltage and U1's pins are inputs or unpowered outputs. With switches on, J4 pin 2 reads R4 plus the eight pull-downs in parallel, 100 kΩ + 1.25 kΩ, about 101 kΩ.

## Steps

In order: the board alone, then the kit's power, the clock, reset and project select, and the first functional test. Set the switches as in Settings before step 1.

1. Power the board alone from a bench supply at 3.3 V, limited to 10 mA, on J2 pin 6 (+) and J2 pin 5 (−), with a 10 kΩ resistor from J3 pin 1 to J3 pin 5, so that U1's second input, which the chip drives once the board is in the kit, doesn't float. Expect: 3 × 3.3 V / 10 kΩ = 0.99 mA from the supply, plus at most 15 µA for U1 (10 µA of supply current, ICC, and 5 µA into its first input through R4, II), and 9.9 mV to 10.05 mV between TP1 and TP2, 10 Ω times all of that, because U1 and R4 take their 3.3 V after R3.
2. Still on the bench supply, voltage at J1 pin 1 (`ui[0]`) and at J4 pin 3 to GND. Expect: 3.3 V at J1 pin 1, because R4 holds U1's first input high, and 0 V at J4 pin 3, because the 10 kΩ holds its second input low.
3. Take the bench supply and the 10 kΩ off. With the kit unplugged, plug the board into the demo board's three I/O Pmod sockets, with nothing on J4. Power the kit from USB through the USB power meter. Expect: about 200 mA at 5 V, close to the ETR guide's 180–200 mA for the factory test project; above 250 mA, switch off.
4. Measure between TP1 and TP2. Expect: 11.1 mV to 13.7 mV. That's step 1's reading plus 10 Ω times the current that now flows into the RP2350's pull-downs, which the firmware turns on for `ui[0]` and the `uio` lines in `ASIC_MANUAL_INPUTS` mode. On `ui[0]`, U1 drives the pull-down through R1: 3.3 V / (1 kΩ + 113 kΩ) to 3.3 V / (1 kΩ + 36 kΩ) = 29 µA to 89 µA. On each `uio` line whose switch is on, the current is 3.3 V / 113 kΩ to 3.3 V / 36 kΩ = 29 µA to 92 µA, so the three lines whose switches are on take 87 µA to 275 µA in all. More means something else on the demo board is loading the lines.
5. In the demo board's firmware, select `tt_um_ieeeuoftasic_simproc` with its clock at 10 MHz, then pulse reset. Expect: `uo_out` = 0x03, so segments A (TX idles high) and B (halt is high in `IDLE`) lit and C (done) dark.
6. Voltage at J3 pin 1 (`uo[0]`) and at TP4 (`uo[0]`, between R2 and J4) to GND. Expect: 3.3 V at both, the idle level of the UART, at TP4 through U1 and R2.
7. Plug the dongle into the laptop, then wire its GND, TXD and RXD to J4 pins 1, 2 and 3. Voltage at TP3 (`ui[0]`, between J1 and R1) to GND. Expect: 3.21 V to 3.3 V, U1's high through R1 against the RP2350's pull-down, 3.3 V × 36 kΩ / 37 kΩ = 3.21 V at its strongest.
8. Open a terminal on the dongle at 113,636 baud, 8N1, and send the three bytes F0 00 00 (SimProc's `PING`). Expect: one byte back, 0xAA.

To finish, unplug the dongle from J4 before you switch the kit off, so that the dongle never feeds the unpowered kit: up to 33 µA through R4 and R3 into its +3V3, and its TXD on U1's unpowered input.

## When a reading is wrong

Stop and unplug the dongle first, then the kit's USB cable, before you look for the cause.

- A resistance in Before power that is low where it should be open points to a solder bridge or a part on the wrong pads; compare the board with the schematic before anything is powered.
- The board alone drawing much more than 0.99 mA, or the supply hitting its 10 mA limit, means a short from +3V3 to GND on the board, or U1 fitted turned round: don't plug it into the kit.
- J1 pin 1 low in step 2: check that R4 is fitted, and U1's pin-1 mark against the silkscreen.
- The kit drawing more than 250 mA, or anything warm, can mean that a chip has latched up: switch off, wait, and try the kit without your board to see whether the current is the board's or the kit's.
- `uo_out` other than 0x03 after reset: check the project selection and the clock in the firmware before suspecting the chip.
- No reply to `PING`: check that the dongle's TXD is on J4 pin 2 and its RXD on pin 3, that the terminal's baud rate matches `clk_per_bit` and the clock, and that the demo board's DIP switch 1 is off.
