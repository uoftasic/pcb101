# Reviewing and ordering a board

This page answers: *what does a review find that ERC and DRC can't, and what happens, at what cost, between a clean board and a box of them arriving in Toronto?*

By the end of Lab 05 your board passes every automatic check and CI builds its fabrication files on every push. Those checks compare the board with its own schematic and with a set of rules, and none of them knows what the board is *for*, so a board can pass all of them and still be wrong. This page is about the review that does, and then about ordering: what a fabricator asks for, what it costs, how long it takes, and what Canada charges at the border. In [Lab 06](../labs/lab-06-review-a-seeded-board-overview.md) you review a board we seeded with faults, then get a real quote and DFM report for your own.

## Mistakes the checks don't look for

Tiny Tapeout's breakout repository records two mistakes that were made into real boards:

- The TT07 breakout "has the ASIC project MUX `reset_n` and `increment` wires crossed and is thus mislabelled."
- The production run of the TT06 demo boards "had very low valued resistances which, if you wish to interact with analog projects, had to be removed or replaced."

Neither is the kind of mistake ERC, DRC or schematic parity looks for. Two signals swapped in the schematic are swapped the same way on the board, so the board matches its schematic perfectly, and a resistor's value is just a field on a symbol, which no check compares with what the circuit needs. Both are found by a person who reads the schematic against what the board has to do: the chip's pin list, the datasheets, and the supplies on either side of every connector.

The team doesn't yet have a member who has reviewed boards before. Until it does, the seeded board in Lab 06 and the course checklist are the review, and a second member reads every board's `BRINGUP.md` before a kit is powered from it ([Bringing up a chip](bringing-up-a-chip.md)).

## The checklist

The course checklist is the list Lab 06 has you review against. Each line comes from something earlier in the course, and each is something you can check in KiCad with the datasheet open beside it.

1. **Footprints against datasheets.** Every footprint matches the package of the part you'll actually buy, including the package variant, because one part number often comes in several packages. Lab 02 is the method.
2. **Pin 1.** The pin-1 mark on the silkscreen and the fabrication layer agrees with the footprint's pad 1 and with the datasheet's drawing.
3. **Connections against the pin list.** Every line goes where the project's pin list says, and a UART's TX goes to the other side's RX. Lab 03's connectivity check covers the nets it was told about; the review covers the rest.
4. **Decoupling.** Each capacitor is on the rail it was meant for and close to the pin it serves.
5. **I/O voltages.** Tiny Tapeout's SKY130 chips run their I/O at 3.3 V on the demo board, "The input pins are not 5V tolerant", and each output drives 4 mA ([GPIO spec](https://tinytapeout.com/specs/gpio/)). Every line that crosses from another supply has its series resistor ([Protecting the chip's I/O](protecting-the-chips-io.md)).
6. **ESD.** Every connector that leaves the board has a protection part. The demo board has 24 TVS diodes, 2 on its USB data lines and 22 on lines from the breakout connector that carry the chip's analog pads, so nothing on it protects the digital pins your Pmod touches ([Supplies, back-powering and ESD](supplies-back-powering-and-esd.md)).
7. **Back-powering.** The design note says what happens when either side is unpowered, and nothing on the board can drive a pin of an unpowered chip.
8. **Test points.** Every net that `BRINGUP.md` measures has a place to put a probe. The SKY130 breakout, for comparison, has four test points, on its reset, clock, `uio1` and `uin0` lines.
9. **Fabricator rules.** Silkscreen, text, annular rings and clearances meet the rules of the fabricator you'll order from, which may be stricter than KiCad's libraries (next section).
10. **Mechanical fit.** The Pmod connectors are 22.86 mm apart, as Tiny Tapeout's Pmod library places them, and nothing overhangs the demo board where it would hit something.

Write each finding down with the line it breaks and where on the board it is, so that the designer can go straight to it.

## Fabricator rules and KiCad's libraries

Every fabricator publishes minimum sizes. These are the ones for an ordinary 2-layer board at three of them, read on November 16, 2026, with KiCad's own library convention (KLC) for comparison:

| | Trace and space | Smallest drill | Annular ring | Silkscreen line |
|---|---|---|---|---|
| [JLCPCB](https://jlcpcb.com/capabilities/pcb-capabilities) | 0.10 / 0.10 mm | 0.15 mm | 0.18 mm minimum on 2 layers | at least 0.15 mm |
| [PCBWay](https://www.pcbway.com/capabilities.html) | 0.1 / 0.1 mm | 0.15 mm | 0.15 mm | |
| [OSH Park](https://docs.oshpark.com/services/), 2 layers | 0.1524 / 0.1524 mm (6 mil) | 0.254 mm (10 mil) | 0.127 mm (5 mil) | |
| KLC (KiCad's footprints) | | | at least 0.15 mm (rule F7.5) | nominally 0.12 mm (rule F5.1) |

JLCPCB also gives a minimum text height of 1.0 mm and 0.15 mm from a pad to silkscreen. The last two columns are where KiCad and the fabricators part ways: KiCad's own footprints are drawn to KiCad's convention, which isn't the same as any one fabricator's limits. Tiny Tapeout's DIP dock shows how far apart they can be. We counted its silkscreen: 441 lines, arcs and circles in its footprints are 0.12 mm wide, 98 of the 139 pieces of text placed on the board itself have 0.14 mm strokes, and 38 are less than 1.0 mm tall. By JLCPCB's published numbers, all of those are below its minimums, and the board's own DRC reports no errors, because its rules don't ask about them.

What a fabricator does with a 0.12 mm line, whether it prints it anyway, thickens it, or flags it, is what its DFM (design for manufacture) report tells you, which is one reason Lab 06 has you get one. When your board's design rules carry your fabricator's numbers, its DRC catches what KiCad can check, and the DFM report covers the rest.

## Ordering

Ordering a bare board means uploading a zip of the Gerbers and the drill file ([Fabrication outputs](fabrication-outputs.md)) to a fabricator's quote page, choosing the options (layers, thickness, finish, colour, quantity), and reading back a price, a build time and shipping choices. A fabricator can also check the files themselves and list the problems it finds, which is the DFM report Lab 06 asks you to record. We haven't checked whether each one asks for an account before it shows a quote; Lab 06 has you record that too.

Prices change, so treat these as what the fabricators' own pages said on November 16, 2026, in US dollars:

- **JLCPCB:** "From $2.00 / 5 pcs" with a "Build Time: 24 hours", and on its comparison page "From $2.00" for 5 boards of 1 to 4 layers at 100 × 100 mm.
- **PCBWay:** "$ 5.00 10 pcs 1-2 layer", "Build Time:24 hours".
- **OSH Park:** $5 per square inch for a set of 3 two-layer boards, made in 9 to 12 calendar days, with ENIG finish, 1.6 mm thick, and "shipped for free to anywhere in the world". Super Swift is $10 per square inch in 4 to 5 business days.

OSH Park's price depends only on area, so you can work it out yourself. A board that spans the demo board's three I/O Pmods is about 61 mm wide (two 22.86 mm spacings and one connector), and if it's 30 mm tall, that's 2.8 square inches, or about $14 for three boards, delivered. The DIP dock, at 85.05 × 85.05 mm, is 11.2 square inches, or $56.06 for three.

The build times don't include shipping. JLCPCB's shipping table is an image we couldn't read, so we have no confirmed transit time or shipping price to Canada; from the build times and OSH Park's lead time, expect one to three weeks between ordering and holding the boards. That's why the course suggests ordering as a group right after Lab 06, when everyone's board has been reviewed.

Assembly is optional in PB101, and most course boards are meant to be soldered by hand ([Parts you can solder by hand](parts-you-can-solder-by-hand.md)). If you do want it: JLCPCB's economic assembly has an $8.18 setup fee, $1.53 for the stencil, $3.07 to load each "extended" part and $0.0016 per solder joint (its price page, updated October 22, 2026), and PCBWay advertises "Only $ 29 in total for 1-20pcs assembly".

Two Toronto companies make boards too. Candor Industries (125 Martin Ross Avenue) does quick-turn, multilayer, impedance-controlled and RF boards, and Bittele Electronics, headquartered in Toronto with production in Markham, does fabrication, parts and assembly. Neither publishes prices or a student programme: Candor quotes on request, and Bittele through its online ordering system.

## Duties and tax

Bare printed circuit boards don't pay duty in Canada: tariff item 8534.00.00, "Printed circuits", has a most-favoured-nation rate of "Free" in the CBSA's 2026 Customs Tariff. They can still pay tax. For a shipment by courier, the CBSA's low-value rules (modified 2025-11-25) are:

| Shipment | Duty and tax free up to | Above that |
|---|---|---|
| Courier, from the US or Mexico | CA$40 | duty free up to CA$150, but taxes apply; above CA$150, both |
| Courier, from any other country | CA$20 | duties and taxes apply |
| Mail, from any country | CA$20 | duties and taxes apply |

JLCPCB's own page says "All duties and taxes for international shipments are the responsibility of the customer" and lists Canada's threshold as 20 CAD (updated November 10, 2026). The tax in Ontario is the 13 % HST. So a courier order of boards from China worth more than CA$20 pays 13 % HST on arrival and no duty on the boards themselves, and the courier may add a brokerage fee for collecting it, which we haven't researched. The thresholds are per shipment, so if a cohort pools its boards into one order, it's the total value that counts.

## Check yourself

1. A board passes ERC, DRC and parity with no errors, but the UART's TX on the chip is wired to the TX pin of the dongle header. Which check should have caught it?

   <details>
   <summary>Answer</summary>

   None of the automatic ones. The schematic and the board agree with each other, so parity is clean, and no rule knows which pin should be which. It's line 3 of the checklist, connections against the pin list, and in Lab 03 a connectivity check that was told about that net.

   </details>

2. Your board uses KiCad's library footprints, and you're ordering from JLCPCB. Their silkscreen is drawn with 0.12 mm lines. What do you do?

   <details>
   <summary>Answer</summary>

   Nothing about the footprints is wrong by KiCad's convention, but 0.12 mm is below JLCPCB's published 0.15 mm minimum line width. Read what JLCPCB's DFM report says about the upload, and if it flags the silkscreen, widen the lines or accept that some legend may not print.

   </details>

3. A courier delivers a CA$35 order of bare boards from China to you in Toronto. What do you pay at the border, before any brokerage fee?

   <details>
   <summary>Answer</summary>

   No duty, because printed circuits are tariff-free, but the order is above the CA$20 courier threshold for a country other than the US or Mexico, so the 13 % HST applies: 13 % of CA$35 is CA$4.55.

   </details>

4. Without opening OSH Park's site, what would three copies of a 50 × 50 mm 2-layer board cost there?

   <details>
   <summary>Answer</summary>

   50 mm is 1.97 inches, so the board is 3.88 square inches, and at $5 per square inch for a set of three that's about $19.38 (in US dollars, shipped).

   </details>

Next: [Lab 06: Review a seeded board](../labs/lab-06-review-a-seeded-board-overview.md).
