# Bring-up plan: source board for an0

<!--
  PB101 capstone, Brief A reference. Every expected value is worked out from the part values
  and the demo board figures in DESIGN.md. Nothing here has been measured.
-->

The board: the Brief A source board, on the demo board's analog header J13, driving J13 pin 4 (an0 on the SKY130 breakout) from the trimmer RV1 through R1 (1 kΩ) and C1 (10 nF), with TP1 on the trimmer's wiper and TP2 on the pin.

## Lines that leave the board

| Line | Driven by | Drives | Kit off, board plugged in | Kit on, board unplugged |
|---|---|---|---|---|
| J13 pin 4, an0 | RV1's wiper through R1 (1 kΩ), held by C1 | the chip's analog pad through its switch (under 500 Ω, under 5 pF), and the demo board's 10 MΩ pull-down | the board's only supply is the kit's 3.3 V, so the line sits at 0 V and nothing flows | the pin floats on the demo board, pulled to 0 V by 10 MΩ |
| J13 pin 32, +3V3 | the demo board's regulator | RV1, 3.3 V / 1 kΩ = 3.3 mA | 0 V; the board has no supply of its own | not connected |
| J13 GND pins | the demo board | the board's ground | 0 V | not connected |

## Settings

- Current limit: 10 mA on the bench supply for the board alone; the kit runs from USB through a USB power meter, and we stop if it reads more than 250 mA.
- Demo board firmware mode: the project selected with its clock at 4 MHz; the RP2350 doesn't touch the analog header.
- Demo board DIP switches: as the project's documentation asks; they don't reach J13.
- Your board's switches: none; RV1 starts at its middle, 1.65 V.
- Clock: 4 MHz, CrossWalk's `clock_hz`.

## Before power

Checks with nothing powered, on the board on its own, with a multimeter.

1. Resistance from J1 pin 32 (+3V3) to J1 pin 1 (GND). Expect: 1.00 kΩ, RV1 end to end.
2. Resistance from TP1 to TP2, across R1. Expect: 1.00 kΩ.
3. Resistance from TP2 to GND with RV1 turned fully towards its GND end. Expect: 1.00 kΩ, R1 alone.

## Steps

In order: the board alone, then the kit's power, the project, and the first reading.

1. Power the board alone from a bench supply at 3.3 V, limited to 10 mA, on J1 pin 32 (+) and pin 1 (−). Expect: 3.3 mA from the supply.
2. Turn RV1 until TP1 reads half the supply. Expect: 1.65 V at TP1, and the same 1.65 V at TP2, because nothing draws current through R1.
3. Switch off, plug the board onto J13 of the kit with the kit unpowered, and power the kit from USB through the USB power meter. Expect: about 200 mA at 5 V, the ETR guide's 180–200 mA for the factory test project; RV1's 3.3 mA at 3.3 V adds at most 3.3 mA to that.
4. Measure TP1 and TP2 again, before the project is selected. Expect: 1.65 V at both; the 10 MΩ pull-down moves TP2 by 1.65 V × 1.25 kΩ / 10 MΩ = 0.2 mV, below what a hand-held meter shows.
5. Select the project with its clock at 4 MHz and start conversions. Expect: TP2 below TP1 by no more than 8.3 mV, the droop decision 5 of DESIGN.md works out for 400 kS/s.
6. Turn RV1 slowly and read the codes. Expect: one code per 12.9 mV at TP2, if the converter's full scale is 3.3 V; record what its full scale turns out to be.

To finish, switch the kit off before you unplug the board, and unplug it straight up so that J13's pins don't bend.

## When a reading is wrong

Switch the kit off first, then unplug the board, before you look for the cause.

- A resistance in Before power that is low where it should be 1.00 kΩ points to a solder bridge, most likely between neighbouring pins of J1.
- The board alone drawing much more than 3.3 mA means a short from +3V3 to GND: check J1 against J13's pinout before it goes near a kit.
- TP2 far from TP1 with the kit off means R1 or C1 is damaged or C1 is leaking; with the kit on and the project selected, a large difference means the pin draws more than the sampling estimate, so measure the current through R1 as the voltage across it divided by 1 kΩ.
- No change in the codes as RV1 turns: check that the project is selected, that the pin is an0, and that J13 is fitted and its pin 4 reaches the breakout.
