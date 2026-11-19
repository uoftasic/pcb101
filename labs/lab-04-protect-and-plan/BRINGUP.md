# Bring-up plan: TODO (your board's name)

<!--
  PCB101 Lab 04. labs/common/check_bringup.py reads this file. Keep the five "##" headings,
  give every numbered item under "Before power" and "Steps" an "Expect:" with a value and
  its unit (3.3 V, 1.26 kΩ, 0.99 mA, 0xAA), and fill in every placeholder.
-->

The board: TODO (one line: what it is, which project it's for, and which commit of your repository this plan is for).

## Lines that leave the board

Every line between your board and anything else: what drives it, what it drives, and what happens when one side is powered and the other isn't.

| Line | Driven by | Drives | Kit off, dongle powered | Kit on, dongle unpowered |
|---|---|---|---|---|
| `ui[0]`, UART into the chip | TODO | TODO | TODO | TODO |
| `uo[0]`, UART out of the chip | TODO | TODO | TODO | TODO |
| `uio[0..7]`, the bit period | TODO | TODO | TODO | TODO |
| +3V3 from the Pmod sockets | TODO | TODO | TODO | TODO |

## Settings

- Current limit: TODO
- Demo board firmware mode: TODO
- Demo board DIP switches: TODO
- Your board's switches: TODO
- Clock: TODO

## Before power

Checks with nothing powered, on your board on its own.

1. TODO. Expect: TODO

## Steps

In order: your board alone, then the kit's power, clock, reset and project select, and the first functional test.

1. TODO. Expect: TODO

## When a reading is wrong

TODO
