# Boards for chips: carriers, motherboards and characterization boards

This page answers: *the Pmod you drew is one kind of board a chip needs. What are the others, and what does each ask of you that a Pmod didn't?*

Everything you've drawn in this course plugs into Tiny Tapeout's demo board, and the demo board does a lot of the work. It powers the chip, selects the project through the chip's on-board multiplexer, usually provides the clock, and gives you every project pin through its DIP switches, its 7-segment display, its Pmods and its RP2350. A Pmod adds only the hardware one project needs on top of that, which is why it made a good first board. The other boards a team ends up needing take over more of those jobs, or carry a different chip altogether. This page goes through them, from the ones closest to what you've done to the ones furthest away, so that when the team needs one you know what it involves. The capstone asks for a Pmod or for the first kind below.

![A diagram of where each kind of board attaches: the SKY130 breakout to the demo board through two DF12 connectors, the demo board to a Pmod board and to an analog source board, the breakout to a motherboard, a GF180 DIP carrier to the DIP dock, and a wafer.space chip-on-board module to a motherboard through a 70-pin mezzanine connector](../assets/img/ic103-board-kinds.svg)

*Where each kind of board attaches, from the chip outwards. The solid boxes are boards that exist, or that you design in this course; the dashed ones are boards a team could design next. Made by [`scripts/figures/board_kinds.py`](https://github.com/uoftasic/pb101/blob/main/scripts/figures/board_kinds.py).*

## A board for an analog pin

CrossWalk, one of the team's designs, is an 8-bit SAR ADC with two analog pins (its `info.yaml` says `analog_pins: 2` and `clock_hz: 4000000`). Testing it means driving an analog pin with a voltage you know, cleanly enough that the converter's errors aren't hidden under the source's.

The path from the demo board's header to the ADC's input isn't a wire. On SKY130 chips, Tiny Tapeout's [analog spec](https://tinytapeout.com/specs/analog/) gives each analog pin's path to its pad as "Resistance: < 500 ohm", "Capacitance: < 5 pf" and "Max current: 4 mA", with an analog switch, `tt_asw_3v3`, in series. The chips have 12 pins for analog and a project may use up to 6 of them, and on the demo board each analog line comes out on a 100 mil header and is "pulled down with a large 10 MegaOhm resistance" ([demo board guide](https://tinytapeout.com/guides/get-started-demoboard-etr/)).

Those numbers are what a source board's design note works with. Two examples of the arithmetic, which are ours and not Tiny Tapeout's:

- The 10 MΩ pull-down and your source's output resistance form a divider. A source with 10 kΩ of output resistance loses 10 kΩ / 10 MΩ = 0.1 % of its voltage, which is a quarter of one step of an 8-bit converter (1/256 is 0.39 %). A buffered source, with an output resistance of ohms, loses nothing you could measure.
- The path's resistance and capacitance set a time constant. With the 500 Ω and 5 pF limits alone it's 2.5 ns, but a 10 kΩ source driving the same 5 pF makes it 50 ns, and settling to within half a step of 8 bits (1/512) takes ln 512 ≈ 6.2 time constants, about 310 ns. At CrossWalk's 4 MHz clock, a cycle is 250 ns.

Brief A of the capstone is this board in its simplest form: one analog pin driven from a known, filtered source, with test points and a design note that does the arithmetic above for your own parts.

The full characterization board, the one that measures the converter, is a bigger design, and it's PB201's. It needs a source good enough to test with. Steve Arar's article on the [sine-wave histogram method](https://www.allaboutcircuits.com/technical-articles/adc-linearity-testing-introduction-to-sinusoidal-histogram-method/) (All About Circuits, October 20, 2023) explains why a sine rather than a ramp: "the linearity of the ramp signal produced by typical signal generators is limited to 8 to 10 bits", not much better than an 8-bit converter itself, whereas "we can filter out the harmonics of a sinusoidal signal". You drive the converter with a sine slightly larger than its full-scale range (the article's example uses 1.1 V on a 1 V converter, so that "we can be sure that the input exercises all codes"), at a frequency that isn't a subharmonic of the sampling rate (390.3 Hz against 40 kHz, with 80,000 samples), and count how often each code appears. Normalized to what an ideal converter would give, "Subtracting one from the bin counts therefore produces the DNL information." The board also needs a reference, and Horowitz and Hill point out that in a precision converter circuit the reference usually sets the noise: their example's ADR445 contributes about 2 µV peak-to-peak from 0.1 to 10 Hz (*The Art of Electronics*, 3rd ed., chapter 13).

There's no CrossWalk silicon to test yet. It's tagged for Tiny Tapeout's TTSKY26d shuttle, which closes on 2026-11-30 and whose chips are expected on 2027-05-25, with an estimated shipping date of 2027-06-25 ([chips page](https://tinytapeout.com/chips/)). Until then a CrossWalk board is a design exercise, and doing it now, while the chip is still being designed, means either one can still change to suit the other.

## A motherboard for the breakout

Tiny Tapeout's advice to anyone making their own board is in its [FAQ](https://tinytapeout.com/faq/): "we recommend that you design your PCB to interface with our breakout board", which "will provide you with 2 connectors where you get all of the signals of the chip." A board that takes the breakout's two DF12 connectors replaces the demo board, so it takes over all of the demo board's jobs: power, selecting the project through the chip's multiplexer, the clock and reset, and whatever drives and reads the pins.

It can't reach the chip's supplies, though. We followed every power net of the SKY130 breakout (rev 3.2, `breakout-pcb` at 91a2bf1). The 60-pin connector J1 has one +3V3 pin and 24 ground pins among its power nets, and the 50-pin J3 has two +5V, two +3V3 and 13 ground. The chip's own rails stay on the breakout: `VCCD` (1.8 V) comes from the breakout's one fitted regulator through a 0 Ω link, and `VDD_IO` and `VDDA` come from +3V3 through 0 Ω links. So a motherboard can measure the breakout's total current on +3V3, or change `VDD_IO` and `VDDA` together by changing +3V3, and it can't do either for one rail alone. That needs the rework described on the breakout's silkscreen: take off a 0805 link and fit the header J2, which isn't fitted on the boards Tiny Tapeout ships ([Bringing up a chip](bringing-up-a-chip.md) shows it). That's rework on the board that carries the kit's only chip.

It's also a bigger board to draw than a Pmod. Tiny Tapeout's breakouts and demo board are all 4 copper layers, and the DF12 connectors have 0.5 mm pitch (their footprints are `HRS_DF12NB-60DS-0.5V_51` and `HRS_DF12NB-50DS-0.5V_51`), far finer than anything this course has you solder ([Parts you can solder by hand](parts-you-can-solder-by-hand.md)). And because the motherboard now selects the project, its multiplexer control lines are the ones a mistake would break, the same lines Tiny Tapeout's TT07 breakout got wrong: it "has the ASIC project MUX `reset_n` and `increment` wires crossed and is thus mislabelled".

Clocking is the other job a motherboard inherits. On the RP2040 version of the demo board the microcontroller could "generate the clock signal for your design, up to 50 MHz" ([PCB spec](https://tinytapeout.com/specs/pcb/)). Tiny Tapeout's [GPIO spec](https://tinytapeout.com/specs/gpio/) gives the SKY130 pins' official limits as 33 MHz for an output and 66 MHz for an input, and reports a worst-case round trip through the multiplexer of 20 ns, measured on TT3.5 silicon. A motherboard that clocks the chip itself, or reads back an output in the same cycle, has to stay inside those numbers.

## Boards for chips from other shuttles

All of the team's chips so far come from Tiny Tapeout's SKY130 and IHP shuttles, in a QFN on a breakout. Other routes to silicon put the die on something else, and the board around it changes.

### Tiny Tapeout's GF180 shuttles

These don't package the die at all: they "have the die bonded to a PCB directly (called chip-on-board, or COB)", in the FAQ's words. Tiny Tapeout's "TT GF180 CoB DIP Breakout" carries the die on a 32-pin DIP and brings out "all the I/O (8 in, 8 out and 8 bidirectional)", "the project clock and reset" and "the Tiny Tapeout project MUX, to select the design", with an optional CH32X035 microcontroller on board. Its host is the DIP dock, which you met in [Fabrication outputs](fabrication-outputs.md): a board that "is very simple, and designed using only two layers", with the demo board's DIP switches, 7-segment display, Pmods and manual clock and reset. It's a board you could have drawn after Lab 03.

### wafer.space

wafer.space runs GF180MCU shuttles of 1,000 dies per slot. On November 16, 2026, its [site](https://wafer.space/) listed Run 3 at $8,000 for a 3.93 × 5.12 mm slot, with chip-on-board packaging as a $1,500 add-on ($1.50 per die) that "Requires the default pad ring for wire bonding", no QFN option, a purchase deadline of 9 December 2026 and parts shipping in Q2 2027. Its [chip-on-board repository](https://github.com/wafer-space/chip-on-board-wire-bonded-pcbs) (Apache-2.0) shows what the board side of that looks like. The die is bonded to a 14 × 16 mm breakout with 74 pads, following "the Tiny Tapeout convention of 74 pads", which plugs into a motherboard through a 70-pin, 0.4 mm-pitch mezzanine connector, and the repository has example motherboards in KiCad. Its Run 1 table maps each bond pad on the die to a pad on the breakout and a Tiny Tapeout function: bond pad 0 goes to breakout pad 1, `ctrl_ena`; bond pads 9 to 16 go to breakout pads 10 to 17, `uo[0]` to `uo[7]`; bond pads 19 to 24 carry `analog[0]` to `analog[5]`; and bond pads 17 and 73 are VDD IO. Its wire-bonding rules read: "No wires may cross", "Wire angle must be not greater than 45°", "Maximum wire length must be less than 3 mm", a minimum of 1 mm or twice the die thickness, and "No solder mask is allowed in the area to be bonded". Matching the die to the board is still done by hand, because "there are no real exchange formats yet that tie the die layout to the breakout PCB", so wafer.space wrote a script that "walks pin-for-pin around the padframe" of the GDS and the KiCad file together.

### ChipFoundry's chipIgnite

On SkyWater 130, [chipIgnite](https://chipfoundry.io/) is "$14,950" for up to 15 mm² with "38 fully -configurable I/Os", and the "Option of 100 QFN-packaged parts or Bare Die", with an evaluation board. Its CI2612 shuttle tapes out on December 7, 2026, for delivery on May 25, 2027. A QFN from there would need a board much like Tiny Tapeout's breakout, decoupling and all, which is PB201 material.

### A bare die of your own

Packaging one locally is possible. The Toronto Nanofabrication Centre's January 2026 price list has a TPT HB16 wire bonder at $49 an hour for UofT users, with staff service at $60 an hour from 9 am to 5 pm. [CMC Microsystems](https://www.cmc.ca/package-assembly/) packages dies in DIP 40, CFP 24, CQFP 44, 80 and 120, and CPGA from 69 to 209 pins, wire-bonds bare dies directly to a substrate, and does flip-chip, and "All of the above services are also accessible to non-subscribers", by quotation. Europractice publishes the bonding rules an assembly house works to (pad size and pitch, wire length and angle, no crossing wires) in its [ASIC Package Design Rules](https://europractice-ic.com/wp-content/uploads/2020/06/ASIC_Prototype_Packaging_Design_Rules_2024.pdf); every page of that document is marked confidential although it's posted publicly, so we link to it rather than copy it. [From die to package](from-die-to-package.md) covers what a bond plan is.

None of these is a course exercise. The team has no chip from these shuttles yet, so this part of the page is about being ready: knowing that a chip-on-board module needs a fine-pitch connector and a motherboard, that a QFN needs its own decoupled carrier, and that a bare die needs a package and a bond plan before it needs a board.

## Check yourself

1. Your source board drives a CrossWalk input from a 47 kΩ potentiometer wiper with no buffer. Using the numbers on this page, what does the demo board's pull-down cost you?

   <details>
   <summary>Answer</summary>

   The worst-case output resistance of a 47 kΩ pot's wiper is about a quarter of 47 kΩ, roughly 12 kΩ, and against the 10 MΩ pull-down that loses about 0.12 % of the voltage, about a third of an 8-bit step, and it changes as you turn the knob. A buffer after the pot removes it.

   </details>

2. Someone suggests a motherboard for the SKY130 breakout so the team can measure `VCCD` on its own. What does the board file say about that?

   <details>
   <summary>Answer</summary>

   It can't, as the breakout is built. The DF12 connectors carry only +3V3, +5V and ground, and `VCCD` stays on the breakout, fed from its regulator through a 0 Ω link. Measuring it means removing that link and fitting J2 on the breakout, which is rework on the kit's only chip.

   </details>

3. Why does Tiny Tapeout's GF180 chip sit on a DIP carrier, when the SKY130 chips come in a QFN?

   <details>
   <summary>Answer</summary>

   The GF180 shuttles don't package the die: it's bonded straight to a board (chip-on-board). Tiny Tapeout's carrier for it is a small board in a 32-pin DIP shape, which plugs into the DIP dock the way a DIP chip would.

   </details>

Next: [Capstone: A board for a team chip](../labs/capstone-a-board-for-a-team-chip-overview.md).
