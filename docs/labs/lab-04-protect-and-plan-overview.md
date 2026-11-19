# Lab 04: Protect and plan

In this lab you make your Lab 03 board safe to plug into a Tiny Tapeout kit, and you write a plan for bringing it up with the kit. A kit has only one chip, so a mistake on your board that damages one of the chip's pins is expensive. On the board, you'll put a series resistor on each UART line, an ESD array on the dongle header and a current-sense point in the board's own supply. The plan is a file in your repository, `BRINGUP.md`. It says what drives each line that leaves the board and what happens when one side is powered and the other isn't, it lists the checks you make before anything is powered, and it gives the reading you expect at every step.

The lab's files are in [`labs/lab-04-protect-and-plan/`](https://github.com/uoftasic/pcb101/tree/main/labs/lab-04-protect-and-plan) in the course repo.

## Before you start

- Finish [Lab 03](lab-03-a-pmod-for-one-projects-pins-overview.md), so that its check passes on your own repository.
- Read the pages on row 7 of the [course path](../index.md#course-path): [Protecting the chip's I/O](../guide/protecting-the-chips-io.md), [Supplies, back-powering and ESD](../guide/supplies-back-powering-and-esd.md), [Measuring current](../guide/measuring-current.md) and [Bringing up a chip](../guide/bringing-up-a-chip.md). The numbers that this lab asks you to work out come from those pages.

The lab takes about 1 hour 30 minutes, roughly 20 minutes for Part 1, 15 for each of Parts 2 to 4, and 25 for the bring-up plan. Those times are our estimates. We did time the check itself, which took 18 seconds in our run with the container limited to one CPU.

Copy the bring-up plan's template into your repository and run the Lab 04 check on the board as Lab 03 left it:

```bash
cd ~/simproc-pmod
cp ~/pcb101/labs/lab-04-protect-and-plan/BRINGUP.md .
git add BRINGUP.md
~/pcb101/labs/lab-04-protect-and-plan/check.sh
```

The check runs everything that Lab 03's check runs, then the rows that Lab 04 adds, then the check of the bring-up plan. On our Lab 03 board the board check still passes, and five Pmod rows fail:

```text
  FAIL  ui[0]        J1 pin 1 reaches J4 pin 2 (the dongle's TXD) directly, with no series resistor; this line crosses from another supply
  FAIL  uo[0]        J3 pin 1 reaches J4 pin 3 (the dongle's RXD) directly, with no series resistor; this line crosses from another supply
...
  FAIL  ESD J4.2     /UART_RX (the dongle's TXD) has no ESD part to GND on it
  FAIL  ESD J4.3     /UART_TX (the dongle's RXD) has no ESD part to GND on it
  FAIL  sense        no current-sense resistor between +3V3 and a net of the board's own
...
FAIL  pmod.kicad_pro: board check PASS; 12 of 17 Pmod checks ok; bring-up plan FAIL
```

All six rows of the bring-up plan check fail as well, although the excerpt above leaves them out. The template still says TODO in every section, and its Before power and Steps sections have one item each, where the check wants at least two and four. In Parts 2 to 4 you fix the five Pmod rows, and in Parts 1 and 5 you fill in the plan.

## Part 1: Every line that leaves the board

For each line between your board and something else, what drives it, what does it drive, and what happens when one side is powered and the other isn't?

1. Fill in the table under "Lines that leave the board" in `BRINGUP.md`. It has a row each for `ui[0]`, `uo[0]`, `uio[0..7]` and the 3.3 V that your board takes from the sockets. [Pins, Pmods and planning a pinout](../guide/pins-pmods-and-planning-a-pinout.md) lists what else the demo board connects to each pin.

2. Start with the worst case, which is the `ui[0]` row with the kit switched off. The dongle is plugged into a laptop, and its TXD idles high at 3.3 V into `ui[0]`. On the board as Lab 03 left it, what limits the current that flows into the chip?

   <details>
   <summary>Answer</summary>

   Nothing on your board does. The current flows from the dongle's TXD through the pad's upper protection diode into `VDD_IO`, and from there onto the demo board's +3V3, and it's limited only by the dongle's own output stage and the diode's drop. Horowitz and Hill warn that momentary currents of more than 20 to 50 mA through those diodes can damage the part, and in some cases latch it up. [Supplies, back-powering and ESD](../guide/supplies-back-powering-and-esd.md) draws this path in a figure.

   </details>

3. Your board drives `ui[0]`, and two things on the demo board can drive it too. Under Settings, write which firmware mode and which DIP-switch positions your board needs, and why.

   <details>
   <summary>Answer</summary>

   In the firmware's `ASIC_RP_CONTROL` mode, which the example configuration sets as the default, the RP2350 drives the `ui_in` pins, so SimProc's section of `config.ini` has to select `ASIC_MANUAL_INPUTS`. The demo board's DIP switch 1 connects `ui_in[0]` to +3V3 through 1 kΩ, so it has to be off. If it were on, then whenever the dongle drove the line low, 3.3 V / 1 kΩ = 3.3 mA would flow into the dongle's TXD.

   </details>

You should see the check's `Lines that leave the board` row go to `ok` once no cell is empty or says TODO.

## Part 2: Series resistors

How big a resistor keeps the current into an unpowered chip small, and still lets the UART's edges through?

1. Choose a limit for the current into a pin of an unpowered chip, and write it in your plan with your reason for it. The one current limit for a pin that we found in SkyWater's I/O guide is 100 µA, for a pin connected to a voltage above its I/O supply or below ground, and we found no rating there for the current that damages a pin or starts latch-up. So the limit you design to is your choice. More than 20 to 50 mA through the diodes can damage the part (Part 1, step 2), so choose a limit well below 20 mA.

2. Work out the smallest resistor that meets your limit when the chip's `VDD_IO` is near 0 V, $R \ge (3.3\ \text{V} - 0.6\ \text{V}) / I_{max}$, and write it down before you choose a standard value.

3. Work out how long an edge takes through your resistor, $2.2RC$ with 10 pF at the pin, and compare it with the length of one bit of the UART. At 115,200 baud a bit lasts 8.7 µs.

4. In the schematic, put the resistor between J1 pin 1 and the header's pin 2, and another between J3 pin 1 and the header's pin 3. Give the header side of each its own net name; ours are `DONGLE_TXD` and `DONGLE_RXD`. Update the board (F8), place each resistor on its line and route.

5. Run the check. You should see both UART rows pass, with the current and the edge time worked out for your resistor. With our 1 kΩ resistors they read:

   ```text
     ok    ui[0]        J1 pin 1 reaches J4 pin 2 (the dongle's TXD) through R1 (1k)
                        into an unpowered chip: (3.3 V - 0.6 V) / 1 kΩ = 2.7 mA; edge with 10 pF: 2.2RC = 22 ns
     ok    uo[0]        J3 pin 1 reaches J4 pin 3 (the dongle's RXD) through R2 (1k)
                        into an unpowered chip: (3.3 V - 0.6 V) / 1 kΩ = 2.7 mA; edge with 10 pF: 2.2RC = 22 ns
   ```

   The check fails any resistor below 135 Ω, which would let more than 20 mA through. The resistor on `uo[0]` also protects something other than the chip. What does it protect, and when?

   <details>
   <summary>Answer</summary>

   It protects the dongle. With the kit on and the dongle unplugged from the laptop, SimProc's TX idles high into the dongle's unpowered RXD, and current flows through the dongle's own clamp diode into its supply. R2 limits that current in the same way that R1 limits the current into the chip.

   </details>

## Part 3: ESD on the dongle header

Where does static get onto your board, and where does the protection have to sit?

1. Add a two-line ESD array to the schematic (press A, then type in the filter to find it). Ours is `Power_Protection:SP0502BAHT`, which KiCad's library describes as "TVS Diode Array, 5.5V Standoff, 2 Channels, SOT-23 package". Its footprint is `Package_TO_SOT_SMD:SOT-23`, whose leads come out beside the body, where you can reach them with an iron.

   ![The Choose Symbol dialog filtered to SP0502](../assets/img/kicad-symbol-chooser-sp0502.png)

   *Choose Symbol in KiCad 10.0.5, filtered to `SP0502`. Pins 1 and 2 are the two protected lines and pin 3 goes to GND.*

2. Connect its pins 1 and 2 to the header's pins 2 and 3, on the header side of the series resistors, and pin 3 to GND. Why there, rather than at the Pmod connectors?

   <details>
   <summary>Answer</summary>

   Static arrives on the dongle's cable, so the clamp should be the first thing it meets, close to the header and with a short path to ground. The series resistor then sits between the clamp and the chip, and limits the current from whatever gets past the clamp. Horowitz and Hill estimate that a 2.5 kV discharge delivers 15 µJ to an unprotected input, and that a pair of external clamp diodes with a series resistor on each side of them cuts that to about 0.1 µJ. The demo board has TVS diodes only on the USB data lines and the analog lines, so the array on your header is the only TVS protection that any of your digital pins get.

   </details>

3. Place the array next to the header with a via from pin 3 to the ground plane, route it, and run the check. You should see:

   ```text
     ok    ESD J4.2     /DONGLE_TXD: D1 (SP0502BAHT, pin 1) to GND
     ok    ESD J4.3     /DONGLE_RXD: D1 (SP0502BAHT, pin 2) to GND
   ```

The check counts a part as ESD protection if it has one pin on the line and another on GND, and either its reference starts with D or it comes from KiCad's `Power_Protection` library.

## Part 4: A current-sense point

What should your board draw from the demo board's 3.3 V, and how will you read it?

1. Give your board's parts a supply net of their own. Put a 10 Ω resistor from the sockets' `+3V3` to a new net (ours is `+3V3_PMOD`), and move the common side of the switches onto that net. Put a test point on each side of the resistor, using the symbol `Connector:TestPoint` with the footprint `TestPoint:TestPoint_Pad_D1.5mm`.

2. Each switch that's on draws 3.3 V / 10 kΩ through its pull-down. Work out what your board draws with the switches set the way you'll use them, and the voltage that this current puts across the 10 Ω, and write both numbers in your plan.

   <details>
   <summary>Answer</summary>

   Each switch that's on draws 0.33 mA. With three on, the board draws 0.99 mA, which drops 9.9 mV across 10 Ω, and with all eight on it draws 2.64 mA and drops 26.4 mV. A multimeter on its millivolt range can read either.

   </details>

3. Can this resistor tell you what the chip draws?

   <details>
   <summary>Answer</summary>

   No. The chip's supplies stay on the breakout, so the current through this resistor is only what your board's own parts draw. With your board on the demo board and no rework on the breakout, the only current you can read that includes the chip's is the whole kit's, at the USB input, and Tiny Tapeout's ETR guide puts that at 180 to 200 mA with the factory test project running. [Measuring current](../guide/measuring-current.md) explains why. It also describes a board that takes the demo board's place, which can measure the breakout's total current on +3V3.

   </details>

4. Update the board, place the resistor and the test points, route, and run the check. You should see:

   ```text
     ok    sense        R3 (10) from +3V3 to /+3V3_PMOD, test points TP1 and TP2
   ```

## Part 5: The bring-up plan

What do you check before power, and what should you read at each step?

1. Under "Before power", list the checks you'd make with a multimeter on your board on its own, with nothing powered: the resistance from +3V3 to GND with every switch off and again with every switch on, the resistance across each series resistor, and the resistance from each of the header's two signal pins to GND. Give each check an `Expect:` with its value. With every switch on, ours is 10 Ω + 10 kΩ / 8 = 1.26 kΩ.

2. Fill in the rest of Settings: the current limit for your supplies (with its unit), your board's switches and the clock. The firmware mode and the DIP switches are there already from Part 1. SimProc's bit period is `clk_per_bit` = `uio` × 4 clocks, so with a 10 MHz clock and the switches set to 22, the UART runs at 10 MHz / 88 = 113,636 baud.

3. Under "Steps", write the bring-up in order: your board alone on a bench supply, then the kit's power, the clock, reset and project select, and the first functional test. Give each step an `Expect:` with a value and its unit, or with a byte in hex. You can take two of the values from DD104's [SimProc in one page](https://uoftasic.com/dd104/guide/simproc-in-one-page.html). After reset `uo_out` reads 0x03, because TX idles high and `halt` is high, so the demo board lights segments A and B. When you send SimProc `PING`, the three bytes F0 00 00, it replies 0xAA.

4. Under "When a reading is wrong", say what you do first and what each wrong reading points to. Also write down the order for unplugging, in which the dongle comes off J4 before the kit is switched off.

5. Run the check. You should see the bring-up plan pass:

   ```text
     ok    TODO                        none left
     ok    Lines that leave the board  4 rows, every cell filled in
     ok    Settings                    5 items; a current limit with its unit
     ok    Before power                4 items, each with an expected value and its unit
     ok    Steps                       7 items, each with an expected value and its unit
     ok    When a reading is wrong     6 lines
   ```

   Your counts may differ from ours. To pass, the plan needs at least two checks under Before power and four steps under Steps, each with an `Expect:` and a value, a current limit with its unit, and no TODO anywhere. The check can't tell whether your expected values are right, so someone else should read your plan before any kit is powered from your board.

## Finishing

You're done when `~/pcb101/labs/lab-04-protect-and-plan/check.sh`, run in your own repository, ends with `PASS  pmod.kicad_pro: board check PASS; 17 of 17 Pmod checks ok; bring-up plan PASS`, and the files it checked are committed and pushed to GitHub.

Questions:

1. You power your board alone from a bench supply, with three switches on. What current does the supply show, and what voltage do you read between your two test points?

   <details>
   <summary>Answer</summary>

   The supply shows 0.99 mA, and the meter across the test points reads 9.9 mV, the drop across the 10 Ω resistor that you worked out in Part 4, step 2.

   </details>

2. Why does the dongle come off J4 before the kit is switched off?

   <details>
   <summary>Answer</summary>

   If the kit goes off first, the dongle is still connected and powered, and its TXD drives `ui[0]` of an unpowered chip. Your series resistor limits that current, and unplugging the dongle first keeps it from flowing at all.

   </details>

Submit: nothing for this lab. Keep `BRINGUP.md` in your repository, because the capstone asks for a bring-up plan, and for Brief D you start from this one.

## Going further (optional)

- Hold `ui[0]` high when no dongle is plugged in. With J4 empty, the RP2350 in `ASIC_MANUAL_INPUTS` and DIP switch 1 off, nothing drives the line, so its level isn't defined. A pull-up from the header side of R1 to `+3V3_PMOD` would make it idle high, as a UART line should. Work out a value that the dongle can still pull low.
- Replace the series resistor on `ui[0]` with a 74LVC buffer powered from your board's 3.3 V, as [Protecting the chip's I/O](../guide/protecting-the-chips-io.md) describes. The check's `ui[0]` row looks for a resistor and fails with a buffer in its place, so keep that change on a branch of its own.

Next on the [Course path](../index.md#course-path): read [Fabrication outputs](../guide/fabrication-outputs.md), [Outputs in CI](../guide/outputs-in-ci.md) and [KiCad files in git](../guide/kicad-files-in-git.md), then do [Lab 05: Fab outputs in CI](lab-05-fab-outputs-in-ci-overview.md).
