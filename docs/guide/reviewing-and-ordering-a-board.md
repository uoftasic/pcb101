# Reviewing and ordering a board

This page answers: *what does a review find that ERC and DRC can't, and once a board passes both, what does it cost to have it made and shipped to Toronto, and how long does that take?*

By the end of Lab 05 your board passes every check you've run on it, and CI builds its fabrication files on every push. ERC, DRC and parity compare the board with its own schematic and with the rules saved in it, so a mistake that is in the schematic or in the rules passes all three. The Pmod check also compares the schematic with the project's pin list, but it can only check what the list asks for, so a board can pass every check and still be wrong. The first half of this page is about the review, in which a person checks the board against what it has to do. The second half is about ordering the board. It covers what you send a fabricator, the prices and build times that three fabricators publish, and the duty and tax that Canada charges when the boards arrive. In [Lab 06](../labs/lab-06-review-a-seeded-board-overview.md) you review a board that we seeded with eight faults, and then you get a fabricator's quote and DFM report for your own board, without ordering it.

## Mistakes the checks don't look for

Tiny Tapeout's breakout repository records two mistakes that ended up on manufactured boards:

- The TT07 breakout "has the ASIC project MUX `reset_n` and `increment` wires crossed and is thus mislabelled."
- The production run of the TT06 demo boards "had very low valued resistances which, if you wish to interact with analog projects, had to be removed or replaced."

ERC, DRC and schematic parity don't look for either kind of mistake. When two signals are swapped in the schematic, they're swapped the same way on the board, so the board still matches its schematic. A resistor's value is a field on its symbol, and none of those three checks compares it with what the circuit needs. A person finds mistakes like these by reading the schematic against the chip's pin list, the datasheets of the parts, and the supplies on either side of every connector, which together say what the board has to do.

The team doesn't yet have a member who has reviewed boards before. Until it does, the review is the course checklist below, which you first use on the seeded board in Lab 06, and a second member reads every board's `BRINGUP.md` before a kit is powered from it ([Bringing up a chip](bringing-up-a-chip.md)).

## The checklist

The course checklist is the list that Lab 06 has you review against. Each line comes from something earlier in the course, and you can check each one in KiCad, with the datasheets, the project's pin list and the board's `BRINGUP.md` open beside it.

1. **Footprints against datasheets.** Every footprint matches the package of the part you'll actually buy, including the package variant, because one part number often comes in several packages. You checked a footprint against a datasheet's package drawing in Lab 02.
2. **Pin 1.** The pin-1 marks on the silkscreen and on the fabrication layer agree with the footprint's pad 1 and with the datasheet's drawing.
3. **Connections against the pin list.** Every line goes where the project's pin list says, and a UART's TX goes to the other side's RX. Lab 03's Pmod check compares the schematic with the pin list, and it checks that each `uio` line has a switch, but not which switch it is.
4. **Decoupling.** Each capacitor is on the rail it was meant for and close to the pin it serves.
5. **I/O voltages.** On the demo board, Tiny Tapeout's SKY130 chips run their I/O at 3.3 V. The [GPIO spec](https://tinytapeout.com/specs/gpio/) says "The input pins are not 5V tolerant", and gives each output's drive as 4 mA. Every line that crosses from another supply goes through a buffer that's powered from the kit's 3.3 V and rated for partial power down (Ioff). With the kit off, at most 10 µA reaches the chip's pin, under the 100 µA that SkyWater's I/O guide allows for a pin driven past its supply. On each line, the part that sends the signal (the dongle on a line into the chip, the chip on a line out) is on the buffer's input, and the buffer's output goes through a series resistor of 330 Ω to 8.2 kΩ on a line into the chip, or 1 kΩ to 5.1 kΩ on a line out to the dongle ([Protecting the chip's I/O](protecting-the-chips-io.md)). A line whose other side runs at another voltage can go through one of TI's dual-supply translators instead, an SN74LVC1T45 or SN74LVC2T45. Its A port faces the chip, with VCCA on the kit's 3.3 V, and its B port faces the connector the other side plugs into, with VCCB on that side's own supply, brought in on a pin of the same connector. DIR is on GND for a line into the chip and on VCCA's 3.3 V for a line out, each of its two VCC pins has its own capacitor (line 4), and a line into the chip still has a resistor of 330 Ω to 8.2 kΩ, between A and the Pmod pin ([Changing a signal's level](protecting-the-chips-io.md#changing-a-signals-level)).
6. **ESD.** Every connector that an outside cable plugs into, such as the dongle header, has an ESD part from each of its signal pins to ground. The demo board has 24 TVS diodes. Two are on its USB data lines, and the other 22 are on lines from the breakout's connector. Of those 22 lines, 14 carry the chip's analog pads and 8 are grounds. None of the 24 is on a digital project pin, so the pins your Pmod reaches have only the chip's own protection ([Supplies, back-powering and ESD](supplies-back-powering-and-esd.md)).
7. **Back-powering.** `BRINGUP.md`'s table of the lines that leave the board says what happens on each line when one side is powered and the other isn't. Nothing on the board can drive a pin of an unpowered chip. The plan's steps plug in anything with a supply of its own only once the kit is up, and unplug it before the kit is switched off.
8. **Test points.** Every net that `BRINGUP.md` measures has a place to put a probe. The SKY130 breakout, for comparison, has four test points, on its reset, clock, `uio1` and `uin0` lines.
9. **Fabricator rules.** Silkscreen lines, text, annular rings and clearances meet the rules of the fabricator you'll order from, which may be stricter than KiCad's libraries (next section).
10. **Mechanical fit.** The Pmod connectors are 22.86 mm apart, as Tiny Tapeout's Pmod library places them, and nothing overhangs the demo board where it would hit something.

Write each finding down with the number of the line it breaks and the part or file it's in, so that the designer can go straight to it.

## Fabricator rules and KiCad's libraries

Every fabricator publishes the smallest sizes it can make. The table gives them for an ordinary 2-layer board at three fabricators, as their pages read on November 16, 2026, with the numbers from KiCad's own library convention (KLC) for comparison:

| | Trace and space | Smallest drill | Annular ring | Silkscreen line |
|---|---|---|---|---|
| [JLCPCB](https://jlcpcb.com/capabilities/pcb-capabilities) | 0.10 / 0.10 mm | 0.15 mm | 0.18 mm minimum on 2 layers | at least 0.15 mm |
| [PCBWay](https://www.pcbway.com/capabilities.html) | 0.1 / 0.1 mm | 0.15 mm | 0.15 mm | |
| [OSH Park](https://docs.oshpark.com/services/), 2 layers | 0.1524 / 0.1524 mm (6 mil) | 0.254 mm (10 mil) | 0.127 mm (5 mil) | |
| KLC (KiCad's footprints) | | | at least 0.15 mm (rule F7.5) | nominally 0.12 mm (rule F5.1) |

JLCPCB also gives a minimum text height of 1.0 mm, and a minimum of 0.15 mm between a pad and the silkscreen. KiCad's numbers differ from the fabricators' in the last two columns. KLC's minimum annular ring of 0.15 mm is under JLCPCB's 2-layer minimum of 0.18 mm, and KLC's nominal silkscreen line of 0.12 mm is under JLCPCB's minimum of 0.15 mm. KiCad's own footprints are drawn to KLC, which is written for a library that has to work for everyone rather than for any one fabricator, so a board drawn with them can still break one fabricator's rules.

We counted the silkscreen on Tiny Tapeout's DIP dock. In its footprints, 441 lines, arcs and circles are 0.12 mm wide. Of the 139 pieces of text placed on the board itself, 98 have 0.14 mm strokes, and 38 are less than 1.0 mm tall. All of those are below JLCPCB's published minimums, but the board's own DRC reports no errors, because the rules saved in the board ask only for text at least 0.8 mm high and 0.08 mm thick, and have no rule for the width of a silkscreen line.

A DFM (design for manufacture) report is a fabricator's own check of your files, and it's where you'd find out whether the fabricator prints a 0.12 mm line anyway, thickens it or flags it. That's one reason Lab 06 has you get one. We haven't been able to get a DFM report ourselves (Lab 06 says why), so we can't tell you which of those JLCPCB does. If your board's design rules have your fabricator's numbers in them, DRC checks the board against those numbers before you upload anything.

## Ordering

Ordering a bare board means uploading a zip of the Gerbers and the drill file ([Fabrication outputs](fabrication-outputs.md)) to a fabricator's quote page, choosing the options (layers, thickness, finish, colour and quantity), and reading the price, the build time and the shipping choices that the page gives you. Lab 06 asks you to record those, and the DFM report as well. We haven't checked whether each fabricator asks you to make an account before it shows a price, and Lab 06 has you record that too.

Prices change, so treat these as what the fabricators' own pages said on November 16, 2026, in US dollars:

- JLCPCB advertises "From $2.00 / 5 pcs" with a "Build Time: 24 hours", and its comparison page gives "From $2.00" for 5 boards of 1 to 4 layers at 100 × 100 mm.
- PCBWay advertises "$ 5.00 10 pcs 1-2 layer", with "Build Time:24 hours".
- OSH Park charges $5 per square inch for a set of 3 two-layer boards, made in 9 to 12 calendar days, with ENIG finish, 1.6 mm thick, and "shipped for free to anywhere in the world". Its Super Swift service is $10 per square inch, in 4 to 5 business days.

OSH Park's price depends only on the board's area, so you can work it out yourself. A board that spans the demo board's three I/O Pmod sockets is about 61 mm wide, which is two 22.86 mm spacings plus the width of one connector. If it's 30 mm tall, it's 2.8 square inches, and three of them cost about $14, delivered. The DIP dock, at 85.05 × 85.05 mm, is 11.2 square inches, so three of them cost $56.06.

The build times don't include shipping. JLCPCB's shipping table is an image that we couldn't read, so we have no confirmed transit time or shipping price to Canada. From the build times and OSH Park's lead time, we'd expect one to three weeks between ordering and holding the boards. The course doesn't require you to order a board. If you want to, the capstone's Going further section suggests ordering with your cohort, after a second person has read your `BRINGUP.md`.

Assembly by the fabricator is optional in PCB101, and most course boards are meant to be soldered by hand ([Parts you can solder by hand](parts-you-can-solder-by-hand.md)). If you do want it, JLCPCB's economic assembly has an $8.18 setup fee, $1.53 for the stencil, $3.07 to load each "extended" part and $0.0016 per solder joint (its price page, updated October 22, 2026). PCBWay advertises "Only $ 29 in total for 1-20pcs assembly".

Two Toronto companies also make boards. Candor Industries, at 125 Martin Ross Avenue, makes quick-turn, multilayer, impedance-controlled and RF boards. Bittele Electronics has its headquarters in Toronto and its production in Markham, and it does fabrication, parts and assembly. Neither publishes prices or a student programme. Candor quotes on request, and Bittele quotes through its online ordering system.

## Duties and tax

Canada charges no duty on bare printed circuit boards. In the CBSA's 2026 Customs Tariff, tariff item 8534.00.00, "Printed circuits", has a most-favoured-nation rate of "Free". The boards can still be taxed, and whether they are depends on how they're shipped and what the shipment is worth. These are the CBSA's rules for low-value shipments, from its page modified 2025-11-25:

| Shipment | Duty and tax free up to | Above that |
|---|---|---|
| Courier, from the US or Mexico | CA$40 | duty free up to CA$150, but taxes apply; above CA$150, both |
| Courier, from any other country | CA$20 | duties and taxes apply |
| Mail, from any country | CA$20 | duties and taxes apply |

JLCPCB's own page says "All duties and taxes for international shipments are the responsibility of the customer" and lists Canada's threshold as 20 CAD (updated November 10, 2026). The tax in Ontario is the 13 % HST. So a courier order of boards from China worth more than CA$20 pays 13 % HST on arrival and no duty on the boards themselves. The courier may also charge a brokerage fee for collecting the tax, which we haven't researched. The thresholds are per shipment, so if a cohort pools its boards into one order, the total value of that order is what counts.

## Check yourself

1. A board passes ERC, DRC and parity with no errors, but the chip's UART TX is wired to the TX pin of the dongle header. Which check should have caught it?

   <details>
   <summary>Answer</summary>

   ERC, DRC and parity can't catch it. The schematic and the board agree with each other, so parity is clean, and no rule in the board says which pin should be which. Lab 03's Pmod check catches it, because it compares the schematic with SimProc's pin list. When we made a board with TX and RX swapped this way, the check failed its `ui[0]` and `uo[0]` rows. In a review, it breaks line 3 of the checklist, connections against the pin list.

   </details>

2. Your board uses KiCad's library footprints, and you're ordering from JLCPCB. The footprints' silkscreen is drawn with 0.12 mm lines. What do you do?

   <details>
   <summary>Answer</summary>

   The footprints are right by KiCad's convention, but 0.12 mm is below JLCPCB's published minimum line width of 0.15 mm. Read what JLCPCB's DFM report says about your upload. If it flags the silkscreen, widen the lines in a copy of the footprint, or accept that JLCPCB may print them poorly.

   </details>

3. A courier delivers a CA$35 order of bare boards from China to you in Toronto. What do you pay at the border, before any brokerage fee?

   <details>
   <summary>Answer</summary>

   You pay no duty, because printed circuits are tariff-free. The order is above the CA$20 courier threshold for a country other than the US or Mexico, though, so the 13 % HST applies, and 13 % of CA$35 is CA$4.55.

   </details>

4. Without opening OSH Park's site, what would three copies of a 50 × 50 mm 2-layer board cost there?

   <details>
   <summary>Answer</summary>

   50 mm is 1.97 inches, so the board is 3.88 square inches, and at $5 per square inch for a set of three that's about $19.38 (in US dollars, shipped).

   </details>

Next: [Lab 06: Review a seeded board](../labs/lab-06-review-a-seeded-board-overview.md).
