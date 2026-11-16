# Pins, Pmods and planning a pinout

<!--
  Sources for this page (row 5 of the course path):
  - Tiny Tapeout GPIO spec https://tinytapeout.com/specs/gpio/, pinouts
    https://tinytapeout.com/specs/pinouts/, and ETR demo board guide
    https://tinytapeout.com/guides/get-started-demoboard-etr/, all read Nov 16, 2026.
  - Demo board (tt-demo-pcb bbf3dd1): README (three I/O Pmods, "span at least two",
    RP2 pinout table) and board file (J14/J15/J16 positions and pad nets; DIP switch
    SW1 to +3V3 through 1 k; uo_out through JP2-JP9 and 510 ohm to the display).
  - kicad-tinytapeout-pmod-lib (9ee6345): README, PinHeader_2x06_P2.54mm_PMODPeriph2B,
    symbol PMOD_PERIPH_2x6.
  - SimProc (uoftasic/simproc 1d97772): info.yaml, src/tt_um_ieeeuoftasic_simproc.sv,
    docs/info.md.
-->

This page answers: *which of a Tiny Tapeout project's pins can a board of yours reach, through which connector pin, and what else on the demo board is already connected to each one?*

A Pmod is the simplest board you can make for a Tiny Tapeout chip: it plugs into the demo board's headers and never touches the chip's breakout. In [Lab 03](../labs/lab-03-a-pmod-for-one-projects-pins-overview.md) you'll draw one for a single project, and this page uses the team's SimProc as its example. To do that you need to know where each project pin comes out, what the demo board already hangs on it, and how the project's choice of pins helps or hinders the board. The last of those is something a team can still change before its chip is taped out, so this page ends with it.

## A project's pins

Tiny Tapeout's [GPIO page](https://tinytapeout.com/specs/gpio/) lists 26 pins for each project: the clock `clk`, the active-low reset `rst_n`, eight inputs `ui_in[7:0]`, eight outputs `uo_out[7:0]` and eight bidirectional pins `uio[7:0]`. The project decides the direction of each `uio` pin with its `uio_oe` output, 1 for output and 0 for input. The demo board's RP2350 microcontroller usually supplies the clock and drives the reset, so a Pmod usually deals with the other 24. Their electrical limits are on [Protecting the chip's I/O](protecting-the-chips-io.md).

## The three I/O Pmods

The demo board's README says the three Pmod headers along its bottom edge "provide access to all the project I/O in a logical fashion, with inputs, bidirectional pins and outputs available on their own distinct headers", and that "extension boards will often need to span at least two, and sometimes three, distinct headers." The ETR guide adds that the headers "follow the digilent PMOD spec and spacing".

![The demo board's three I/O Pmod sockets, with SimProc's pins](../assets/img/pb101-pmod-pinout-simproc.svg)

*The demo board's sockets J14, J15 and J16, seen from above, drawn from the board file (`TinyTapeout/tt-demo-pcb` at bbf3dd1) by [`scripts/figures/pmod_pinout.py`](https://github.com/uoftasic/pb101/blob/main/scripts/figures/pmod_pinout.py). Each pad carries the net the board file gives it; pin 1 is square. SimProc's pins are in blue with what they do, from its `info.yaml` and RTL. Every `uio` pin sets one bit of SimProc's `clk_per_bit`.*

Each socket has twelve pins in two rows of six. Pins 1 to 4 carry bits 0 to 3 of the bus, pins 7 to 10 carry bits 4 to 7, pins 5 and 11 are ground, and pins 6 and 12 are the demo board's +3V3. So a Pmod gets its power from those last four pins, at the same 3.3 V the chip's pads run from. The sockets' first pins are 22.86 mm apart, which is where [Placement and routing](placement-and-routing.md#connectors-first) gets that number.

On your board, Tiny Tapeout's Pmod library supplies the matching part. Its footprint, `PinHeader_2x06_P2.54mm_PMODPeriph2B`, is a through-hole angled header with "digilent numbering", and its symbol, `PMOD_PERIPH_2x6`, calls the eight signal pins `IO1` to `IO8`, with `GND` on pins 5 and 11 and `VCC` on 6 and 12. The library's README asks for the input connector on the left, the bidirectional one in the middle and the output one on the right, looking at the board from the top. That's the order of the sockets in the figure.

## What else is on each pin

Every pin your Pmod reaches already has something else on it. From the demo board's file, counting only the parts that are fitted:

- **`ui_in[0..7]`** go to the RP2350 (GPIO17 to GPIO24) and to an 8-way DIP switch. Each switch connects its line to +3V3 through a 1 kΩ resistor, so a switch that's on pulls its input high.
- **`uo_out[0..7]`** go to the RP2350 (GPIO33 to GPIO40), and each one drives a segment of the 7-segment display, A to G and the decimal point in that order, through a bridged solder jumper (JP2 to JP9) and a 510 Ω resistor.
- **`uio[0..7]`** go to the RP2350 (GPIO25 to GPIO32) and to nothing else that's fitted.

Two consequences follow, and the next two pages deal with them in detail. On an input, your Pmod is one of up to three drivers. The demo board's firmware has a mode in which the RP2350 drives the `ui_in` pins, `ASIC_RP_CONTROL`, which is the mode its example configuration starts in, and a closed DIP switch is another driver. The ETR guide even gives a symptom: when its browser app reports the shuttle as "unknown", the usual cause is "driving the ui_in pins through the INPUT Pmod port". On an output, your Pmod is a second load, because the display segment and its 510 Ω resistor are already there.

## The RP2350's UARTs and the recommended pinouts

Tiny Tapeout's [pinouts page](https://tinytapeout.com/specs/pinouts/) says "TT advocates to use common pinouts wherever possible", so that boards made for one project work for others. For a serial console it recommends one of two pairs, "ui_in[3] - RX" with "uo_out[4] - TX", or "ui_in[1] - RX" with "uo_out[0] - TX", and says you can reach either "via the builtin RP2040 on the demo board". The current demo board has an RP2350 instead, and its README's pin table shows which pins of it have a hardware UART:

| Project pin | RP2350 pin | UART function in the README's table |
|---|---|---|
| `ui_in[0]` | GPIO17 | none |
| `ui_in[1]` | GPIO18 | none |
| `ui_in[3]` | GPIO20 | UART1.tx |
| `uo_out[0]` | GPIO33 | UART0.rx |
| `uo_out[4]` | GPIO37 | UART1.rx |

The first recommended pair has a hardware UART at both ends on the RP2350 board: UART1 transmits into the project's RX on `ui_in[3]` and receives its TX on `uo_out[4]`. The second pair has a hardware receiver on `uo_out[0]`, and nothing on `ui_in[1]` to transmit with. So a pinout that was a recommendation on the older board can be half of one on the newer.

## SimProc's pins

SimProc's `info.yaml` and its top-level RTL (`uoftasic/simproc` at 1d97772) give this pinout:

| Pin | Use |
|---|---|
| `ui[0]` | UART receive |
| `uo[0]` | UART transmit |
| `uo[1]` | halt flag |
| `uo[2]` | done flag |
| `uio[0..7]` | inputs (`uio_oe` is 0) that set the UART's bit period: `clk_per_bit = {uio_in[7:0], 2'b00}` |

Its `info.yaml` gives the clock as 0 Hz, which means "not applicable", so the bit period in seconds depends on the clock the demo board supplies. Its documentation says to "Send commands using the UART RX pin (using a USB to UART conveter)" and to "Set UIO7-UIO0 to set the BAUD rate of the internal UART module."

Against the demo board, that pinout does three things. SimProc's transmit pin, `uo_out[0]`, lands on a hardware UART receiver in the RP2350. Its receive pin, `ui_in[0]`, lands on GPIO17, which has no UART function in the table. And its halt and done flags light segments B and C of the display already. So a Pmod that lets you talk to SimProc without depending on the demo board's firmware needs a header for a 3.3 V USB-UART dongle on `ui[0]` and `uo[0]`, as SimProc's documentation describes, and eight switches with pull-down resistors on `uio[0..7]`. It spans all three sockets, the case the README warns about. It needs no LEDs on the halt and done flags, because the display already shows them and an LED would be a second load on each pin.

## Planning a pinout before tapeout

Which pin a signal goes to costs nothing to change while the design is still RTL, and once the chip is made it decides what board or firmware the chip needs. Had SimProc put its UART on `ui_in[3]` and `uo_out[4]`, the RP2350 could talk to it with hardware UARTs in both directions. A few checks before a team submits a design are cheap:

- Check each pin against the demo board's current RP2 pin table, not only against the pinouts page, which still describes the RP2040 board.
- Use a recommended pinout when one fits, so that existing Pmods work with your project. The pinouts page gives them for UART, SPI, I2C, QSPI flash and PSRAM, VGA, audio and game controllers.
- Keep a peripheral's signals within one Pmod row when you can. The page's SPI, UART and I2C pinouts each use one row, "preferably the upper row".
- Say in `info.yaml` what every used pin does, so that whoever draws the board doesn't have to read the RTL to find out.

## Check yourself

1. Which pins of a Pmod socket carry power, and at what voltage?

   <details>
   <summary>Answer</summary>

   Pins 5 and 11 are ground, and pins 6 and 12 are the demo board's +3V3, so a Pmod's parts run from 3.3 V.

   </details>

2. On the SimProc Pmod, which socket and pin does the dongle's TX line connect to, and which one does its RX line connect to?

   <details>
   <summary>Answer</summary>

   The dongle's TX drives SimProc's receive pin, `ui_in[0]`, which is pin 1 of J14, the input socket. The dongle's RX listens to SimProc's transmit pin, `uo_out[0]`, which is pin 1 of J16, the output socket.

   </details>

3. You want an LED on your Pmod that shows `uo_out[1]`. What else does that pin already drive?

   <details>
   <summary>Answer</summary>

   Segment B of the demo board's display, through the solder jumper JP3 and a 510 Ω resistor, and an input of the RP2350. The pad is rated for 4 mA, and your LED would share it with the segment.

   </details>

4. Why can the RP2350 receive what SimProc transmits with a hardware UART, but not transmit to it the same way?

   <details>
   <summary>Answer</summary>

   SimProc transmits on `uo_out[0]`, which is GPIO33, listed as UART0.rx. It receives on `ui_in[0]`, which is GPIO17, and the README's table lists no UART function for that pin.

   </details>

Next: [Parts you can solder by hand](parts-you-can-solder-by-hand.md).
