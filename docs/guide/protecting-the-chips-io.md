# Protecting the chip's I/O

<!--
  Sources for this page (row 7 of the course path):
  - Tiny Tapeout GPIO spec, https://tinytapeout.com/specs/gpio/, and analog spec,
    https://tinytapeout.com/specs/analog/, read Nov 16, 2026.
  - SkyWater sky130_fd_io user guide,
    https://skywater-pdk.readthedocs.io/en/main/contents/libraries/sky130_fd_io/docs/user_guide.html,
    read Nov 16, 2026: feature list (hot swap and over-voltage tolerance for sio and
    gpio_ovtv2 only), "use the main Vddio/Vssio connections for their ESD current steering
    diodes". General Integration Requirements: a pin may be taken above vddio or below
    vssd_io "provided that the current flowing into/out of the pin is externally limited
    to 100uA". That is the guide's only current limit for a pin; an earlier search for
    "clamp current", "injection" and "absolute" missed it.
  - Horowitz and Hill, The Art of Electronics, 3rd ed. (printed pages): 718 (LVC accepts
    inputs to +5.5 V, including when unpowered), 759-760 (SCR
    latch-up, footnote 92: input clamp current e.g. 20 mA, series input resistor), 794
    (Fig. 12.3 caption: LVC outputs don't load lines when unpowered), 795 (input current,
    Fig. 12.4: 20-50 mA, 74HC clamps at +0.6 V, LVC/AUP tolerant when unpowered), 798-800
    (Fig. 12.9: 74LVC1T45, open drain, TXB0101), 802 (Fig. 12.13, 10k pull-up or
    pull-down), 806 (unused inputs).
  - Hall and Heck, eq. 8-8 (t_10-90 = 2.195 tau).
  - Demo board (tt-demo-pcb bbf3dd1): 510 ohm and a segment on each uo_out line.
  - SimProc (uoftasic/simproc 1d97772): info.yaml and top-level RTL.
-->

This page answers: *what can the board around a Tiny Tapeout chip do to the chip's digital pins, and what can you put between a pin and the outside world to protect it?*

The chip on a Tiny Tapeout breakout is the only one in the kit, so a mistake on your Pmod that damages a pin is expensive. This page gives the pins' ratings and says what happens when a pin is driven past them. Then it covers series resistors, which limit the current into a pin; buffers and translators, which change a signal's level; and pull resistors, which hold an input at a defined level when nothing drives it. [Supplies, back-powering and ESD](supplies-back-powering-and-esd.md) covers what happens when one board is powered and the other isn't, and what static discharge does to a pin. In [Lab 04](../labs/lab-04-protect-and-plan-overview.md) you'll put a series resistor on each UART line of your Lab 03 board.

## What the pins are rated for

Tiny Tapeout's [GPIO page](https://tinytapeout.com/specs/gpio/) says the chip uses the `sky130_ef_io_gpiov2_pad` macro for its I/O pads, and lists these limits for them:

| Parameter | Limit |
|---|---|
| I/O supply voltage | 1.71 V to 5.5 V; the demo board supplies 3.3 V |
| Drive strength, source or sink | 4 mA |
| Maximum output frequency | 33 MHz |
| Maximum input frequency | 66 MHz |

Below the table it says, "The input pins are not 5V tolerant." On the demo board the pads run from 3.3 V, so keep every input between 0 V and 3.3 V.

SkyWater's [user guide for its I/O cells](https://skywater-pdk.readthedocs.io/en/main/contents/libraries/sky130_fd_io/docs/user_guide.html) describes the circuit behind that limit. The guide says its GPIO cells "use the main Vddio/Vssio connections for their ESD current steering diodes", which means that each pad has a diode up to the I/O supply and another down to ground. Its feature list marks two cells, `sky130_fd_io__sio` and `sky130_fd_io__gpio_ovtv2`, as "Hot swap & over-voltage tolerant", and doesn't mark `sky130_fd_io__gpiov2`. The guide gives one current limit for a pin, in its integration requirements: "It is permissible to externally connect the I/O pin to a voltage above vddio or below vssd_io, provided that the current flowing into/out of the pin is externally limited to 100uA." It gives no other rating for the current through the diodes, and none for the current that damages a pin or starts latch-up. The arithmetic below therefore uses Horowitz and Hill's typical figures, and the limit you design to is a choice you make and write down.

## Beyond the rails

Between ground and its supply voltage, a CMOS input draws almost no current. Horowitz and Hill (*The Art of Electronics*, 3rd ed., p. 795) put the leakage at about $10^{-5}$ µA. Outside that range the protection diodes conduct. An input more than a diode drop above the supply pushes current through the upper diode into the supply rail, and an input more than a diode drop below ground pulls current out through the lower one. Horowitz and Hill warn that "Momentary currents greater than 20–50 mA through these diodes will damage or destroy the part, in some cases causing what's known as 'SCR latchup'". In latch-up, the current through the input diodes turns on a pair of parasitic transistors, which short the supply to ground, and the chip stays shorted and gets hot until you turn the power off (p. 759). In a footnote on the same page they add that manufacturers often guarantee no latch-up as long as the input current stays below a maximum "input clamp current", 20 mA for example, which means that "you can use a series input resistor to prevent latchup even with input-voltage overdrive" (p. 759).

![A series resistor in front of a chip input with its two clamp diodes](../assets/img/ic103-io-input-clamps.svg)

*A chip input, as it looks electrically from outside the chip. $D_1$ and $D_2$ are the pad's protection diodes, and $C_{in}$ is the capacitance of the pin, its trace and the connectors. When $V_{drive}$ rises more than a diode drop above $V_{DDIO}$, $D_1$ conducts, and $R_S$ is the only part on your board that limits the current.*

## Sizing a series resistor

With the input past the rail, the current through the resistor and the upper diode is

$$I = \frac{V_{drive} - V_{DDIO} - V_D}{R_S},$$

where $V_D$ is the diode's forward drop. We take it as 0.6 V, the level at which Horowitz and Hill say an unpowered 74HC input clamps (p. 795). For a 3.3 V source such as a USB-UART dongle, the worst case is a chip that isn't powered, with $V_{DDIO}$ near 0 V, because the whole 3.3 V then appears across the resistor and the diode:

| $R_S$ | $I = (3.3\ \text{V} - 0.6\ \text{V})/R_S$ |
|---|---|
| 100 Ω | 27 mA |
| 330 Ω | 8.2 mA |
| 1 kΩ | 2.7 mA |
| 4.7 kΩ | 0.57 mA |

Every row is above SkyWater's 100 µA limit, and the first, 27 mA, is also past Horowitz and Hill's 20 mA example. Choose a limit well below 20 mA, and work the resistor out from it. The next page follows this current further in the unpowered case, through the chip's I/O supply and onto the demo board's whole 3.3 V net.

A series resistor also slows the signal's edges. Together with the capacitance at the pin it forms an RC low-pass filter, whose 10–90 % rise time is $2.2RC$ (Hall and Heck, *Advanced Signal Integrity for High-Speed Digital Designs*, eq. 8-8, give $2.195\tau$). We have no figure for the pad's own capacitance, so suppose the pin, its trace and the connectors add up to 10 pF. Then 1 kΩ gives $\tau$ = 10 ns and an edge of 22 ns. For a UART at 115 200 baud, whose bits last 8.7 µs, an edge that long doesn't matter. For an input near the pads' 66 MHz rating, whose half period is 7.6 ns, the edge would last longer than the signal stays high, so a fast line can only have a small series resistor, of tens of ohms. A resistor of that size at the driving end is also the series termination that [Placement and routing](placement-and-routing.md#when-a-trace-stops-being-a-wire) describes for a logic output driving a cable.

## Outputs

Something outside can drive an output pin past its rails in the same way, through the pin's own protection diodes, and a load on your board can need more current than the pin's 4 mA. On the demo board, every `uo_out` line already drives one segment of the 7-segment display through a solder jumper and a 510 Ω resistor. An LED that your Pmod adds on the same line is a second load, and the LED and the segment then share the pin's 4 mA. A `uo_out` pin can also drive the input of something powered separately, such as the RX pin of a USB-UART dongle. When the chip is powered and the dongle isn't, a high output pushes current through the dongle's clamp diode, and that current loads the chip's output and feeds the dongle's supply. A series resistor on the line limits it.

## Buffers and translators

A series resistor limits current, but it doesn't change a signal's level. When the other side runs from a different supply voltage, you need a part in between that does. Horowitz and Hill give a set of recommended connections between logic families (pp. 798–800), and these four are the ones you'd use here:

- **A buffer with 5 V-tolerant inputs.** The 74LVC family accepts inputs up to 5.5 V "regardless of its own supply voltage (including when it is unpowered)" (p. 718), and its output stages are built not to load a shared line when the part is unpowered (p. 794). A single 74LVC buffer powered from your Pmod's 3.3 V turns a 5 V signal into a 3.3 V one for the chip's input.
- **A dual-supply translator**, such as the 74LVC1T45, runs each side from its own supply, anywhere from 1.8 V to 5 V, and has a direction pin that sets which way the signal goes. Use one when the other side is lower than 3.3 V, or when the line goes both ways.
- **An open-drain output with a pull-up to the receiving side's supply.** It's simple, and it can translate a signal up or down across a wide range of voltages. The pull-up resistor is a compromise, because a smaller one gives faster rising edges but draws more current while the line is low.
- **An auto-direction translator**, such as the TXB0101, senses transitions on either side, so it needs no direction pin, but the supply on its B side must be at least the supply on its A side.

The chip's analog pins carry an analog voltage rather than a logic level, so these parts don't apply to them. Tiny Tapeout's [analog page](https://tinytapeout.com/specs/analog/) gives the path from each analog pad to the project as under 500 Ω and under 5 pF, through an analog switch, with 4 mA at most. Brief A of the capstone, a source board for one analog pin, asks you to work with those numbers.

## Inputs that nobody drives

A CMOS input that nothing drives is left floating. Horowitz and Hill warn that an open input can float up to the logic threshold, which puts the gate's output at half the supply "with both MOS output transistors conducting", so the gate draws current and can oscillate (p. 806). So every input your board might leave undriven needs a resistor that holds it at a defined level. The usual case is a switch, which leaves its input undriven while it's open. Horowitz and Hill's circuit for a switch driving a logic input (p. 802) uses a 10 kΩ pull-up or pull-down, and with CMOS either one works. SimProc's `uio[0..7]` pins are all inputs (`uio_oe` is 0 in its RTL), and together they set its UART's bit period. On the Pmod you draw for it in Lab 03, each switch connects its `uio` line to +3V3, so each line needs a pull-down to ground. A closed switch then reads as 1, and an open one reads as 0 rather than as whatever the line picks up.

## Check yourself

1. A teammate wants to connect a 5 V Arduino output straight to `ui_in[2]`. What do you tell them, and what would you put in between?

   <details>
   <summary>Answer</summary>

   The pads aren't 5 V tolerant, and on the demo board they run at 3.3 V, so a 5 V high would push current through the pad's upper diode into the 3.3 V supply. Put a 74LVC buffer powered from 3.3 V in between (its inputs take up to 5.5 V), or a dual-supply translator. A series resistor alone would limit the current, but the pin would still sit a diode drop above its supply.

   </details>

2. A dongle's TX at 3.3 V drives `ui_in[0]` through 1 kΩ while the kit is switched off. Roughly how much current flows into the chip?

   <details>
   <summary>Answer</summary>

   With $V_{DDIO}$ near 0 V and about 0.6 V across the diode, $(3.3 - 0.6)\ \text{V} / 1\ \text{kΩ}$ = 2.7 mA.

   </details>

3. Why can a UART line take a 1 kΩ series resistor when a 50 MHz clock line can't?

   <details>
   <summary>Answer</summary>

   The resistor and the capacitance at the pin set the edge time, $2.2RC$. With the 10 pF supposed above, 1 kΩ gives edges of about 22 ns. That's a tiny fraction of a UART bit, which lasts microseconds, but it's longer than the whole 20 ns period of a 50 MHz clock.

   </details>

4. Why does each of SimProc's eight baud-rate switches need a pull-down?

   <details>
   <summary>Answer</summary>

   An open switch leaves its `uio` input undriven, and a floating CMOS input can drift to the logic threshold, where it can read as either value and the input stage draws current. The pull-down makes an open switch read as 0.

   </details>

Next: [Supplies, back-powering and ESD](supplies-back-powering-and-esd.md).
