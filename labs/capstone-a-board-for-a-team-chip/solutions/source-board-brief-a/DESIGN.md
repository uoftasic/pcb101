# Design note: source board for an0

<!--
  PB101 capstone, Brief A reference. The pin path figures are Tiny Tapeout's analog spec and
  ETR demo board guide, as "Boards for chips" quotes them; J13's pins come from
  TinyTapeout/tt-demo-pcb at bbf3dd1 and the SKY130 breakout's J1 at breakout-pcb 91a2bf1.
  The sample rate in decision 5 is our assumption. Nothing here has been built or measured.
-->

Brief: A. Project: CrossWalk, the team's 8-bit SAR ADC (uoftasic/crosswalk, `clock_hz: 4000000`), or any project with an analog input on an0. Board: a 50 × 30 mm 2-layer board that plugs onto the demo board's analog header J13 and drives J13 pin 4 from a trimmer through an RC filter.

## Requirements

1. Drive one analog pin through the demo board's analog header J13: pin 4, line /C, which carries an0 on the SKY130 breakout.
2. Mate J13, a 2 × 16 header with a 2.54 mm pitch, from above, pad for pad, with GND on its nine ground pins and power from its 3.3 V pin 32.
3. Set the voltage anywhere from 0 V to 3.3 V, the demo board's supply.
4. Keep the error from the demo board's 10 MΩ pull-down under a tenth of one 8-bit step (0.04 %).
5. Keep the error from the pin's sampling capacitance, under 5 pF behind under 500 Ω and an analog switch, under half a step for one sample (1/512, or 0.2 %), and under one step (1/256, or 0.39 %) on average while the converter samples.
6. Keep the current into the pin under the path's 4 mA maximum, even if the chip holds the pin at 0 V.
7. Give a probe a place on the source and on the pin.
8. Use parts a student can solder with an iron.

## Decisions

1. J1 is a `PinSocket_2x16_P2.54mm_Vertical`, two rows of 16 at a 2.54 mm pitch, on the bottom of the board, flipped and turned 270°: the one placement of it whose 32 pads lie over J13's, pad for pad, when both boards face up. The generator compares the two pad patterns against the demo board's file.
   Meets: 2
2. J1's pins 1, 6, 9, 14, 17, 22, 25, 30 and 31 are on GND and pin 32 on +3V3, as on J13; pin 4 carries AN0, through R1's 1 kΩ from the source; the other 21 pins are left open, so nothing drives the lines that are ground or other analog pads on the breakout.
   Meets: 1, 2
3. RV1 is a 1 kΩ Bourns 3296W trimmer across +3V3 and GND, so its wiper, SET, goes from 0 V to 3.3 V, and it draws 3.3 V / 1 kΩ = 3.3 mA from the demo board.
   Meets: 3, 8
4. R1 is 1 kΩ from SET to AN0. The source's resistance is at most 1 kΩ / 4 = 250 Ω from the trimmer (wiper in the middle) plus 1 kΩ, 1.25 kΩ in all, and against the 10 MΩ pull-down that's an error of 1.25 kΩ / 10 MΩ = 0.0125 %. If the chip held the pin at 0 V, at most 3.3 V / 1 kΩ = 3.3 mA would flow, under 4 mA.
   Meets: 4, 6
5. C1 is 10 nF from AN0 to GND, at the pin. When the pin's switch connects up to 5 pF, the charge it takes from C1 moves the voltage by 5 pF / 10 nF = 0.05 %. On average, sampling at an assumed 400 kS/s (one sample every 10 clocks at 4 MHz) draws 5 pF × 3.3 V × 400 kHz = 6.6 µA, which drops 6.6 µA × 1.25 kΩ = 8.3 mV, 0.64 of one step of 3.3 V / 256 = 12.9 mV. So one sample moves the pin by 0.05 %, under half a step, and the average droop is under one step. With the source's resistance at its largest, 1.25 kΩ, C1 makes a time constant of 12.5 µs, a 12.7 kHz corner, and the pin settles to half a step in 6.2 × 12.5 µs = 78 µs after the trimmer moves.
   Meets: 5
6. TP1 is on SET and TP2 on AN0, each a 1.5 mm pad, on either side of R1.
   Meets: 7
7. R1 and C1 are 0805 parts, 2.0 × 1.25 mm, with hand-soldering pads; the trimmer and the socket are through-hole.
   Meets: 8

## Checks

- The board check passes in `kicad/kicad:10.0.8`: ERC 0, DRC 0 errors and 0 warnings, 0 unconnected items, 0 parity items.
- `src/make_brief_a.py` compared J1's 32 pads with J13's in the demo board file, relative to pad 1, and they match.
- Lab 05's check passes on the repository: the fabrication files, the review images and the `.gitignore`.
- Against the course checklist: the footprints are the parts named (line 1); J1's pin 1 is at J13's pin 1 (line 2); only J13 pin 4 is driven (line 3); there is no IC, so nothing needs decoupling (line 4); J1 mates a header on the demo board rather than a cable, so it has no ESD part (line 6); TP1 and TP2 are where `BRINGUP.md` measures (line 8); Board Setup holds JLCPCB's minimums (line 9).

## Open questions

- J13 is marked DNP in the demo board's files at bbf3dd1, while Tiny Tapeout's ETR guide says analog signals come out on a 100 mil header. Someone with a kit should check whether J13 is fitted on it before this board is ordered.
- CrossWalk's sample rate and full scale aren't written down yet. Decision 5 assumes 400 kS/s; at a higher rate the droop grows in proportion, and a buffer amplifier between the trimmer and R1 would remove most of it.
- The source is only as good as the demo board's 3.3 V, which is the trimmer's reference. A characterization board needs a reference of its own, which is PB201's.
- Which analog pin CrossWalk's two analog pins land on: its `info.yaml` pinout is still empty.
