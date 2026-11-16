# PB101 — PCB Design with KiCad

In this course you design the boards a chip sits on. You start by reading Tiny Tapeout's own boards, the ones the team's chips arrive on, and then you draw a footprint from a package drawing, lay out a small board for one project's pins, protect it and write its bring-up plan, build its fabrication files in CI, and review a board before anyone pays to have it made. The capstone takes a board for one of the team's chips as far as an orderable design, in a repository of your own.

PB101 is part of the UofT ASIC Team education materials, published at <https://uoftasic.com/pb101/>. Unlike the analog and digital courses, it doesn't run in the workbench. You install KiCad 10.0 on your own computer, and the course's checks run in KiCad's own Docker image. [Getting started](guide/getting-started.md) explains why, and what to install on Windows, macOS and Linux.

## Who this course is for

The course is for anyone on the team who will bring up, measure or demonstrate one of the team's chips, from either track. Today that means the people working on SimProc, CrossWalk, Sentry and HART-1, and later it means whoever brings up the next shuttle's chips. The team has no board designs of its own yet, so the course teaches toward the boards those chips need: first a Pmod for one project's pins, and then, on the last reading row, the carriers, motherboards and characterization boards that come after it.

You don't need to have designed a board before. You do need the circuits you learned in class, because the impedance of a capacitor, an RC time constant and the current through a series resistor are what the arguments about decoupling, filtering and protection rest on.

| | |
|---|---|
| Prerequisites | [IC101](https://uoftasic.com/ic101/), then IC102 (either version), and circuits from class. [AD103](https://uoftasic.com/ad103/) helps with the analog capstone brief and [DD102](https://uoftasic.com/dd102/) with the digital one. |
| Tools | KiCad 10.0 on your own computer; Docker, which you set up in IC101, for the checks; git and a GitHub account. |
| Checks | `kicad/kicad:10.0.8`, pinned by digest. Every count and message the labs show comes from a run in that image. |
| Total time | About 21 hours, self-paced. The course path rows below add up to 21 h 0 min. |

IC102 is on the list because from Lab 03 on you work in a board repository of your own on GitHub: every later lab commits to it, Lab 05 runs GitHub Actions on it, and you hand in the capstone as a repository and a commit.

## The capstone

There is one capstone with two briefs, and you pick one. Both are 2-layer boards of about the same size.

- **Brief D, a bring-up Pmod for a digital project**: SimProc, Sentry, or a Tiny Tapeout project of your own. If you built the SimProc Pmod in Labs 03 and 04, you can carry that board through.
- **Brief A, a source board for one analog pin**: for CrossWalk or an ASIC Zoo cell. It plugs onto the demo board's analog header and drives one analog pin from a known, filtered source.

For either brief you hand in the KiCad project, a design note (`DESIGN.md`), a bring-up plan (`BRINGUP.md`) and a green CI run, all in your own GitHub repository. Ordering the board and bringing it up are a separate step, which depends on the team's budget and on there being a chip to put on it, and the course doesn't require either.

## Course path

Work down the table in order. A Read row points you to one or more guide pages, which are for reading only, so there's nothing to run. A Do row is a lab, where you run things, make something of your own and check your results. Each lab's "Before you start" section repeats which pages it expects you to have read.

| # | | What | Time |
|---|---|---|---|
| 1 | Read | [Getting started](guide/getting-started.md) · [What a board does for a chip](guide/what-a-board-does-for-a-chip.md) · [Tiny Tapeout's boards, part by part](guide/tiny-tapeouts-boards-part-by-part.md) | 45 min |
| 2 | Do | [Lab 01: Open a board you didn't design](labs/lab-01-open-a-board-you-didnt-design-overview.md). Install KiCad 10.0, open Tiny Tapeout's SKY130 breakout, find which parts are fitted, trace each supply through its regulator and 0 Ω links to the chip's pins, and explain each error and each kind of warning that ERC and DRC report. | 1 h 30 min |
| 3 | Read | [Schematics other people can read](guide/schematics-other-people-can-read.md) · [Symbols, footprints and libraries](guide/symbols-footprints-and-libraries.md) · [From die to package](guide/from-die-to-package.md) | 1 h |
| 4 | Do | [Lab 02: A footprint from a datasheet](labs/lab-02-a-footprint-from-a-datasheet-overview.md). Work out the pads of a QFN from a package drawing that KiCad's library doesn't cover, then build its symbol and footprint and check them against your own numbers. | 2 h |
| 5 | Read | [Layers and fabricator rules](guide/layers-and-fabricator-rules.md) · [Placement and routing](guide/placement-and-routing.md) · [Pins, Pmods and planning a pinout](guide/pins-pmods-and-planning-a-pinout.md) · [Parts you can solder by hand](guide/parts-you-can-solder-by-hand.md) | 1 h |
| 6 | Do | [Lab 03: A Pmod for one project's pins](labs/lab-03-a-pmod-for-one-projects-pins-overview.md). Start your board repository, then draw and lay out a 2-layer Pmod for a Tiny Tapeout project until ERC, DRC and parity are clean and its connections match the project's pin list. | 4 h |
| 7 | Read | [Protecting the chip's I/O](guide/protecting-the-chips-io.md) · [Supplies, back-powering and ESD](guide/supplies-back-powering-and-esd.md) · [Measuring current](guide/measuring-current.md) · [Bringing up a chip](guide/bringing-up-a-chip.md) | 1 h |
| 8 | Do | [Lab 04: Protect and plan](labs/lab-04-protect-and-plan-overview.md). Add series resistors, ESD protection and a current-sense point to your Lab 03 board, and write its `BRINGUP.md` with the checks before power and an expected reading for every step. | 1 h 30 min |
| 9 | Read | [Fabrication outputs](guide/fabrication-outputs.md) · [Outputs in CI](guide/outputs-in-ci.md) · [KiCad files in git](guide/kicad-files-in-git.md) | 45 min |
| 10 | Do | [Lab 05: Fab outputs in CI](labs/lab-05-fab-outputs-in-ci-overview.md). Add a workflow to your board repository that fails on ERC or DRC errors and builds the fabrication files and review images, then break it on purpose and fix it. | 1 h 15 min |
| 11 | Read | [Reviewing and ordering a board](guide/reviewing-and-ordering-a-board.md) | 30 min |
| 12 | Do | [Lab 06: Review a seeded board](labs/lab-06-review-a-seeded-board-overview.md). Find the faults planted in a board we ship, using the course checklist, then record a fabricator's quote and DFM report for your Lab 03 board. | 1 h 15 min |
| 13 | Read | [Boards for chips](guide/boards-for-chips.md) | 30 min |
| 14 | Do | [Capstone: A board for a team chip](labs/capstone-a-board-for-a-team-chip-overview.md). Take a bring-up Pmod for a digital project, or a small source board for an analog pin, to an orderable state with a design note, a bring-up plan and CI passing in your own repository. | 4 h |

## Getting help

Ask in the [team Discord](https://discord.gg/hrJnP5UsGz), where no question is too basic. [Getting started](guide/getting-started.md#getting-help) says what to include so that someone can answer quickly.
