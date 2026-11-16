# Bring-up plan: SimProc Pmod

<!--
  PB101 capstone, Brief D reference: Lab 04's plan, with steps 5 and 6 read at the test
  points TP4 and TP3 that the capstone board adds. Every
  expected value is worked out from the schematic's part values, SimProc's RTL
  (clk_per_bit = uio x 4, PING answers 0xAA, uo_out = 3 while idle) and Tiny Tapeout's ETR
  demo board guide (180-200 mA at 5 V on the factory test). Nothing here has been measured.
-->

The board: the SimProc Pmod from PB101 Labs 03 and 04 and the capstone, for `tt_um_ieeeuoftasic_simproc` on a TTSKY25b kit, with series resistors R1 and R2, the ESD array D1, the current spy R3, and test points TP3 on `ui[0]` and TP4 on `uo[0]`.

## Lines that leave the board

| Line | Driven by | Drives | Kit off, dongle powered | Kit on, dongle unpowered |
|---|---|---|---|---|
| `ui[0]`, UART into the chip | the dongle's TXD, through R1 (1 kΩ) | SimProc's UART receiver, the RP2350's GPIO17, and the demo board's DIP switch 1 when it's on | TXD idles high, so current flows through R1 and the pad's upper diode into `VDD_IO` and the demo board's +3V3: at most (3.3 − 0.6) V / 1 kΩ = 2.7 mA | nothing on the board drives the line, so its level isn't defined; keep the dongle powered whenever it's plugged into J4 |
| `uo[0]`, UART out of the chip | SimProc's TX, through R2 (1 kΩ) to J4 | the dongle's RXD, the RP2350's GPIO33 (UART0 RX), and segment A of the display through 510 Ω | SimProc's output is unpowered and the dongle's RXD is an input, so neither drives the line | TX idles high into the dongle's unpowered RXD; R2 limits the current through the dongle's clamp diode to at most (3.3 − 0.6) V / 1 kΩ = 2.7 mA |
| `uio[0..7]`, the bit period | SW1, from +3V3 after R3, with RN1 (10 kΩ) pulling each line to GND | SimProc's `uio` inputs (`uio_oe` is 0) and the RP2350's GPIO25 to GPIO32 | the switches take their 3.3 V from the kit, so every line sits at 0 V and no current flows | not affected by the dongle; a switch that's on drives 3.3 V, so the RP2350 must not drive these pins |
| +3V3 from the Pmod sockets | the demo board's regulator, through pins 6 and 12 of J1 to J3 | R3 and SW1's commons; the pull-downs draw 0.33 mA per switch that's on | 0 V from the kit, but the dongle's 2.7 mA through `ui[0]` lifts the kit's +3V3 by an amount set by its load | 3.3 V |

## Settings

- Current limit: 10 mA on the bench supply for the board alone; the kit runs from USB through a USB power meter, and we stop if it reads more than 250 mA.
- Demo board firmware mode: `ASIC_MANUAL_INPUTS` in SimProc's section of `config.ini`, so the RP2350 doesn't drive `ui[0]`, and none of the RP2350's `uio` pins set as outputs.
- Demo board DIP switches: all off. Switch 1 would pull `ui[0]` to +3V3 through 1 kΩ against the dongle.
- Your board's switches: `uio` = 22 (0b0001_0110), so switches 2, 3 and 5 on and the rest off.
- Clock: 10 MHz from the demo board, so `clk_per_bit` = 22 × 4 = 88 and the UART runs at 10 MHz / 88 = 113,636 baud, 1.4 % below 115,200.

## Before power

Checks with nothing powered, on the board on its own, with a multimeter.

1. Resistance from TP1 (+3V3) to J4 pin 1 (GND), with every switch of SW1 off. Expect: an open circuit, more than 1 MΩ (the meter shows OL), because nothing on the board joins +3V3 to GND while the switches are off.
2. The same with all eight switches on. Expect: R3 plus the eight pull-downs in parallel, 10 Ω + 10 kΩ / 8 = 1.26 kΩ.
3. Resistance from J4 pin 2 to J1 pin 1, across R1, and from J3 pin 1 to J4 pin 3, across R2. Expect: 1.00 kΩ each.
4. Resistance from J4 pin 2 to GND and from J4 pin 3 to GND. Expect: more than 1 MΩ each, because D1 doesn't conduct below its 5.5 V standoff voltage.

## Steps

In order: the board alone, then the kit's power, the clock, reset and project select, and the first functional test. Set the switches as in Settings before step 1.

1. Power the board alone from a bench supply at 3.3 V, limited to 10 mA, on J2 pin 6 (+) and J2 pin 5 (−). Expect: 3 × 3.3 V / 10 kΩ = 0.99 mA from the supply, and 0.99 mA × 10 Ω = 9.9 mV between TP1 and TP2.
2. With the kit unplugged, plug the board into the demo board's three I/O Pmod sockets, with nothing on J4. Power the kit from USB through the USB power meter. Expect: about 200 mA at 5 V, close to the ETR guide's 180–200 mA for the factory test project; above 250 mA, switch off.
3. Measure between TP1 and TP2. Expect: 9.9 mV, the same as step 1. More means something on the demo board is loading the `uio` lines.
4. In the demo board's firmware, select `tt_um_ieeeuoftasic_simproc` with its clock at 10 MHz, then pulse reset. Expect: `uo_out` = 0x03, so segments A (TX idles high) and B (halt is high in `IDLE`) lit and C (done) dark.
5. Voltage at TP4 (`uo[0]`, between R2 and J4) to GND. Expect: 3.3 V, the idle level of the UART.
6. Plug the dongle into the laptop, then wire its GND, TXD and RXD to J4 pins 1, 2 and 3. Voltage at TP3 (`ui[0]`, between J1 and R1) to GND. Expect: 3.3 V, from the dongle's idle TXD through R1.
7. Open a terminal on the dongle at 113,636 baud, 8N1, and send the three bytes F0 00 00 (SimProc's `PING`). Expect: one byte back, 0xAA.

To finish, unplug the dongle from J4 before you switch the kit off, so that the dongle never drives `ui[0]` of an unpowered chip.

## When a reading is wrong

Stop and unplug the dongle first, then the kit's USB cable, before you look for the cause.

- A resistance in Before power that is low where it should be open points to a solder bridge or a part on the wrong pads; compare the board with the schematic before anything is powered.
- The board alone drawing much more than 0.99 mA, or the supply hitting its 10 mA limit, means a short from +3V3 to GND on the board: don't plug it into the kit.
- The kit drawing more than 250 mA, or anything warm, can be a latched-up chip: switch off, wait, and try the kit without your board to see whether the current is the board's or the kit's.
- `uo_out` other than 0x03 after reset: check the project selection and the clock in the firmware before suspecting the chip.
- No reply to `PING`: check that the dongle's TXD is on J4 pin 2 and its RXD on pin 3, that the terminal's baud rate matches `clk_per_bit` and the clock, and that the demo board's DIP switch 1 is off.
