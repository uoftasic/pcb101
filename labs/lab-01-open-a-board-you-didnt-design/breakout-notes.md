# Notes on Tiny Tapeout's SKY130 QFN breakout, rev 3.2

<!--
  Lab 01: fill in every TODO. The writeup tells you where to look for each one:
  https://uoftasic.com/ic103/labs/lab-01-open-a-board-you-didnt-design-overview.html
  Check your notes with
    labs/common/kicad.sh python3 labs/lab-01-open-a-board-you-didnt-design/src/check_notes.py
  Keep the section headings and the table columns as they are, because the check reads them.
-->

## Not fitted

The parts that have a footprint on the board and are marked DNP (do not populate), as
reference designators separated by commas:

TODO

## Supply rails

One row for each supply that reaches the chip (U4). "Chip pins" are U4's pin numbers on
that rail. "Comes from" is the net the supply arrives on at the connectors. "Through" lists
the fitted parts the current passes through, in order from the connector to the rail.
"Capacitors" are the fitted capacitors from that rail to GND.

| Rail | Chip pins | Comes from | Through | Volts | Capacitors |
|---|---|---|---|---|---|
| VCCD | TODO | TODO | TODO | TODO | TODO |
| VDD_IO | TODO | TODO | TODO | TODO | TODO |
| VDDA | TODO | TODO | TODO | TODO | TODO |

## Checks

The counts from the board check in the pinned image. Keep the three "all" rows, and add
one row for each type of error and each type of excluded item, with what it means in
your own words. You may add rows for warnings too; the check doesn't read those.

| Check | Severity | Type | Count | What it means |
|---|---|---|---|---|
| ERC | error | all | TODO | |
| DRC | error | all | TODO | |
| DRC | excluded | all | TODO | |
