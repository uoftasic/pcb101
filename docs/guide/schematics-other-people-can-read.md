# Schematics other people can read

This page answers: *KiCad drew every wire where I put it, so what is ERC complaining about, and what makes a schematic that the next person can check?*

A schematic is read far more often than it's drawn. The person who reviews your board reads it, so does whoever brings the board up, and so do you, six months later, with a probe in one hand. ERC, KiCad's electrical rules check, is the first of those readers, and the most literal. It can only check what the schematic says about itself, so a schematic that states its intent clearly is easier for ERC and for people alike. This page covers how KiCad decides what is connected, what ERC checks, the ten ERC errors on Tiny Tapeout's SKY130 breakout that you met in [Lab 01](../labs/lab-01-open-a-board-you-didnt-design-overview.md), and the habits that make a schematic readable.

Every count and message on this page comes from `kicad-cli` 10.0.8 in the course's pinned image, on the breakout at `TinyTapeout/breakout-pcb` 91a2bf1, the same setup as Lab 01.

## Nets, labels and power symbols

A **net** is a set of pins that are connected to each other, and it's what the board will eventually turn into copper. KiCad joins pins into nets in four ways:

- **Wires**, which connect where they end on a pin or on another wire, and **junctions**, the dots that join wires that cross.
- **Labels**. A local label joins everything on the same sheet that carries a label with the same name. A global label does the same across every sheet of the design, and a hierarchical label connects a sheet to a pin on the symbol of that sheet in its parent.
- **Power symbols**, such as `+3V3` and `GND`. In KiCad a power symbol makes a net that is global across the whole design, named by the symbol's value.
- **Pins on top of each other**: two pins at the same point are connected, and you don't need a wire between them.

The breakout's schematic is one sheet with 333 wires, 46 junctions and 128 local labels, and no global or hierarchical labels, since there's no second sheet to reach. The difference between a label and a power symbol shows up in the net names the board file uses. A local label's net is named with the sheet's path in front, so the label `VCIN` makes the net `/VCIN`, while a power symbol's net has no prefix: `+3V3`, `GND` and `VCCD`.

Because a power symbol's value is its net's name, one library symbol can make any number of supply nets. The breakout uses KiCad's `power:+3V3` symbol, with its value changed, for `VCCD`, `VDDA`, `VDD_{IO}`, `VCC_{REG}` and `VDD_{REG}` as well as for `+3V3` itself. (`_{IO}` is KiCad's markup for a subscript, so `VDD_{IO}` is drawn as VDD with a small IO after it.) ERC confirms that they're separate nets, as you'll see below, because it reports each of them on its own.

Two names on one net is a mistake KiCad warns about. On the breakout, ERC reports one `multiple_net_names` warning, "Both GND and res_an7 are attached to the same items; GND will be used in the netlist", and eleven `isolated_pin_label` warnings, "Label connected to only one pin", for labels such as `res_an16` and `res_an19` that name a net with nothing else on it. A pin that is meant to be left unconnected should carry a **no-connect flag** (the small cross KiCad places on a pin), which tells ERC the pin is open on purpose. The breakout has eleven.

## Pin types and what ERC checks

Every pin of every symbol has an **electrical type**, which says what the pin does to a net. KiCad's symbol format has twelve, and the standard libraries in the course's image use all of them: input, output, bidirectional, tri-state, passive, free, unspecified, power input, power output, open collector, open emitter and not connected. Resistors, capacitors and connector pins are passive, which means they carry a signal without driving it.

ERC goes through every net and checks the types of the pins on it against a table of which combinations are fine, which deserve a warning and which are errors. Two outputs on one net are an error, for example, because two drivers would fight over the net's voltage.

Power pins have a rule of their own. A net that has a **power input** pin on it, such as a chip's supply pin or a ground symbol, must also have a **power output** pin on it, such as a regulator's output. If it doesn't, ERC reports "Input Power pin not driven by any Output Power pins". The rule catches a supply you forgot to connect, but it also fires whenever a supply reaches a net through passive parts, because ERC can't see a source through a passive pin. A supply that comes in on a connector, or through a 0 Ω link, looks to ERC like no supply at all.

The fix is a **power flag**, `PWR_FLAG` in KiCad's `power` library. It's a symbol with a single power-output pin and no footprint, so it puts nothing on the board, and placing it on a net tells ERC that the net is driven from somewhere ERC can't see.

## The breakout's ten errors

You found ten ERC errors on the breakout in Lab 01. Here they all are, with the net each one is on:

| Where ERC reports it | Net | Type |
|---|---|---|
| `#PWR01` (a `VCCD` power symbol) | `VCCD` | `power_pin_not_driven` |
| `#PWR02` (a `GND` symbol) | `GND` | `power_pin_not_driven` |
| `#PWR03` (a `+5V` symbol) | `+5V` | `power_pin_not_driven` |
| `#PWR04` (a `+3V3` symbol) | `+3V3` | `power_pin_not_driven` |
| `#PWR09` (a `VDD_{IO}` symbol) | `VDD_{IO}` | `power_pin_not_driven` |
| `#PWR013` (a `VDDA` symbol) | `VDDA` | `power_pin_not_driven` |
| U1 pin 1, VIN | `/VCIN` | `power_pin_not_driven` |
| U2 pin 1, VIN | `/VDIN` | `power_pin_not_driven` |
| `#FLG01` and U1 pin 5, VOUT | `VCC_{REG}` | `pin_to_pin`: "Pins of type Power output and Power output are connected" |
| `#FLG02` and U2 pin 5, VOUT | `VDD_{REG}` | `pin_to_pin`, the same message |

ERC reports an undriven net once, at one of its power pins, however many power pins it has. The `VCCD` net has power symbols all over the sheet, and ERC names only `#PWR01`, so the first eight rows are eight nets that have no source.

![The supply section of the SKY130 breakout's schematic](../assets/img/tt-sky-breakout-sch-supplies.png){fig-alt="Part of a KiCad schematic titled Core Voltage Selection, with two near-identical blocks. In the upper block, VCC* SUPPLY, a dotted box labelled SRC select holds +5V and +3V3 power symbols, each feeding a 0 ohm resistor, R1 (crossed out) and R2, to a net labelled VCIN. VCIN goes to pins 1 and 3 of U1, an AP2112K-1.8, with a 10 uF capacitor C6 to ground. U1's pin 5, VOUT, connects to C18, 1 uF, C21, 100 nF, a small diamond-shaped power flag and a power symbol labelled VCC REG. A crossed-out 0 ohm resistor R7, labelled bypass, runs from VCIN to the output. The lower block, VDD* SUPPLY, has the same shape with R3 (crossed out) and R4 feeding VDIN, a crossed-out U2, and R8, labelled bypass, not crossed out, joining VDIN to VDD REG. A note at the top right reads: Breakout is fed 3v3 (guaranteed) and 5V (assumes USB supply) and regulates core voltages as needed. Each LDO has jumpers to select source or bypass completely. A note at the bottom right reads: For Sky: VCC* 1v8, VDD* 3v3."}

*The supply section of the breakout's schematic, rev 3.1 by its title block, plotted by `kicad-cli` 10.0.8. The crossed-out symbols are the DNP parts. The small diamonds by `VCC_{REG}` and `VDD_{REG}` are the two power flags. Made by [`scripts/figures/kicad_figures.sh`](https://github.com/uoftasic/pb101/blob/main/scripts/figures/kicad_figures.sh).*

All ten come from the supply section in the figure. `+3V3`, `+5V` and `GND` reach the breakout on the pins of its two DF12 connectors, and every pin of both connector symbols is passive, so ERC sees no source for any of them. `/VCIN` and `/VDIN`, the regulators' inputs, are fed from `+3V3` through the 0 Ω links R2 and R4, which are passive resistors, so those nets have power-input pins (the regulators' VIN) and no power output. `VCCD`, `VDD_{IO}` and `VDDA`, the chip's three supplies, are each joined to a regulator's output net through another 0 Ω link (R14, R13 and R15), so they have the same problem.

The two power flags are on the two nets that didn't need one. `VCC_{REG}` and `VDD_{REG}` already have a power output on them, the VOUT pin of each regulator, and the flag adds a second one, which is the "Power output and Power output" error.

We checked this by editing a copy of the schematic and running ERC on it again. With the two power flags deleted, ERC reported 8 errors, all `power_pin_not_driven`, on the same eight nets as before, plus 2 new `unconnected_wire_endpoint` warnings for the wires the flags had been on. With a power flag added on each of those eight nets as well, ERC reported no errors at all. The breakout was built and shipped with these errors in it, because they don't change the copper: they're errors in what the schematic tells ERC rather than in the circuit. They're still worth fixing in a board of your own, because a schematic with ten known errors is one where an eleventh, real one is easy to miss.

So put a power flag where a supply enters through parts that ERC treats as passive, such as a connector or a link, and never on a regulator's output.

## Warnings that come from the libraries

Besides the ten errors, ERC reports 103 warnings on the breakout in the course's setup: 69 `lib_symbol_mismatch`, such as "Symbol 'GND' doesn't match copy in library 'power'", 22 `lib_symbol_issues`, such as "The current configuration does not include the symbol library 'psypassives'", and the 12 label warnings above. The first two kinds compare the copies of symbols saved in the schematic with the libraries KiCad has set up, which is why their counts change from one KiCad installation to another. [Symbols, footprints and libraries](symbols-footprints-and-libraries.md) explains where those copies come from.

## Habits that make a schematic readable

ERC can only check what's written down, so the rest of a schematic's quality is up to you. These are the habits we'd ask for in this course, each one shown by the breakout:

- **Group by function and say what each group is for.** The supply section above sits in a box titled "Core Voltage Selection", with sub-blocks titled "VCC\* SUPPLY" and "VDD\* SUPPLY" and dotted boxes marked "SRC select". A reader finds the regulators without searching for them.
- **Write the intent on the sheet.** The note "Breakout is fed 3v3 (guaranteed) and 5V (assumes USB supply) and regulates core voltages as needed" tells a reviewer what to check the circuit against. Without it, they can only check the circuit against itself.
- **Name the nets that matter.** `VCIN` and `VDD_{REG}` tell you what a net is. When nobody names a net, KiCad makes up a name from a part and pad, which is how the demo board ends up with nets like `Net-(R1-Pad2)`. That's fine for a net between a switch and its resistor, but a net you'd want to probe deserves a name.
- **Draw supplies up and ground down.** Power symbols that point up for supplies and down for ground, as the breakout's do, let a reader see a circuit's supply rails at a glance.
- **Mark parts that aren't fitted.** The crossed-out symbols tell the reader which way this revision is built. Lab 01 showed that the board file and the production BOM have to agree with them.
- **Keep the title block current.** The breakout's schematic says rev 3.1, dated 2025-12-02, and its board file says rev 3.2, dated 2025-10-04. Someone comparing a printed schematic with a board in their hand would reasonably wonder whether they had the right files. In a repository of your own, the git history keeps the real record, and the title block should agree with it.

## Check yourself

1. Your Pmod board gets 3.3 V from a pin of a Pmod connector, and ERC reports "Input Power pin not driven by any Output Power pins" at your `+3V3` symbol. Why, and what's the fix?

   <details>
   <summary>Answer</summary>

   A connector's pins are passive, so ERC sees nothing driving the `+3V3` net, which has power-input pins on it (the power symbol and your parts' supply pins). Put a `PWR_FLAG` on the net, near the connector where the supply comes in.

   </details>

2. Why did the two power flags on the breakout cause errors rather than fix them?

   <details>
   <summary>Answer</summary>

   They're on `VCC_{REG}` and `VDD_{REG}`, the regulators' output nets, which already have a power output pin each (VOUT). A power flag is another power output, and two power outputs on one net is an error in ERC's table, "Pins of type Power output and Power output are connected".

   </details>

3. ERC lists one `power_pin_not_driven` error for `VCCD`, at `#PWR01`, but there are many `VCCD` power symbols on the sheet. How many power flags does it take to clear it?

   <details>
   <summary>Answer</summary>

   One, anywhere on the `VCCD` net. ERC reports each undriven net once, and a single power output anywhere on a net drives the whole net.

   </details>

4. A wire on your schematic carries two labels, `SDA` and `I2C_SDA`. What does ERC report, and what should you do?

   <details>
   <summary>Answer</summary>

   A `multiple_net_names` warning, in the form "Both … and … are attached to the same items; … will be used in the netlist", naming the label KiCad picked. Decide which name you want and delete the other, so the net has one name everywhere: on the schematic, in the board and in the fabrication files.

   </details>

Next: [Symbols, footprints and libraries](symbols-footprints-and-libraries.md).
