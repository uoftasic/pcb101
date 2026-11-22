#!/usr/bin/env python3
"""PCB101 Pmod check: the board check, then where the Pmod connectors are and whether the
board connects a project's pins the way its pin list says.

    labs/common/kicad.sh python3 labs/common/check_pmod.py BOARD [--pins FILE] [--protect] [--bringup FILE]

BOARD is a .kicad_pro, or a folder holding exactly one. The checks, in order:

1. labs/common/check_board.py on the project: ERC, DRC, unconnected items and schematic
   parity (see its docstring). Skip it with --no-board-check.
2. The Pmod connectors, found by their symbol (PMOD_PERIPH_2x6): one per socket the pin
   list names, all at the same angle, in a row 22.86 mm apart (0.9 in, Tiny Tapeout's
   spacing, to 0.02 mm), with every pad on the board and the pins' tips past the board's
   outline. Looking at the board with the pins pointing away from you, the connectors are
   the pin list's sockets from left to right (input, bidir, output).
3. Power: pins 6 and 12 of every connector on one net (the demo board's +3V3) and pins 5
   and 11 on GND.
4. Each pin in the pin list, from the schematic's netlist (kicad-cli sch export netlist).
   Pin numbers follow the demo board's sockets: bits 0-3 of a bus on pins 1-4, bits 4-7 on
   pins 7-10. "to" asks for the pin to reach a pin of another part (the dongle header, found
   as the connector other than the Pmods whose pin 1 is on GND), on the same net, through
   one series resistor, or through one of rule 5's buffers or translators the right way round
   (and a resistor, or not). "switch" asks for a switch from the pin's line to the 3.3 V supply,
   and "pull": "down" for a resistor from the line to GND. A resistor counts if it's a
   two-pin part with a reference starting R, or one element of a bussed network
   (R_Network*) or an isolated array (R_Pack*).

With --protect (Lab 04), three more:

5. Every "crossing" pin reaches its part through a buffer and then one resistor, or through
   a dual-supply translator (f), in the direction the line runs. On a ui or uio line, into
   the chip, the header pin's net is on the buffer's input (A) and its output (Y) reaches the
   Pmod pin through one resistor; on a uo line, out of the chip, the Pmod pin's net is on the
   input and the output reaches the header pin through one resistor. A and Y come from the
   pin numbers of KiCad's symbol, one channel at a time (1A with 1Y, 2A with 2Y), so a buffer
   turned round fails, and says so. The row prints what it measured, and also needs:
   a. the buffer to be one of BUFFERS, found by its symbol's name or its value: the 74LVC1G
      and 74LVC2G 17, 34 and 125, and the 74AUP1G17, 74AUP1G34 and 74AUP1G125, all in KiCad's
      74xGxx library. Each runs from one supply, and TI specifies each for partial power down:
      with its supply at 0 V, a pin passes at most 10 µA (Ioff). The 74AHC and 74HC parts
      have no Ioff, and the 1G07's output is open drain, so they aren't on the list. A 125's
      OE is active low, and must be on GND.
   b. its VCC pin on the Pmod's 3.3 V, on either side of the current-sense resistor: the net
      of pins 6 and 12, or the far side of a resistor of 100 Ω or less from it (Lab 04's
      +3V3_PMOD, past R3, where the current spy reads the buffer's current too). Its GND pin
      on GND.
   c. the resistor in its window, compared in ohms. On a ui line, 330 Ω to 8.2 kΩ: 3.3 V / R
      is the most current a fight with a pin driving the other way can pass (10 mA at 330 Ω),
      and 3.3 V × 36 kΩ / (36 kΩ + R) is the high level against the RP2350's strongest
      pull-down, which reaches the chip's 2.31 V input high at 15.4 kΩ. The window stops lower,
      at 8.2 kΩ, because of the RP2350's erratum E9: on its A2 stepping, a GPIO input leaks about
      120 µA and holds the line near 2.2 V, and Raspberry Pi says that a source of 8.2 kΩ or
      less overcomes it. On a uo line, 1 kΩ to
      5.1 kΩ: (3.3 V - 0.6 V) / R is the current into an unpowered dongle (2.7 mA at 1 kΩ),
      and 3.3 V × R / (R + 16.5 kΩ) is the low level against a CH340's strongest RX pull-up,
      which reaches its 0.8 V input low at 5.28 kΩ. The window ends at 5.1 kΩ, the E24 value
      under that, so that it ends on a value you can buy.
   d. a capacitor (reference C...) from the net the buffer's VCC pin is on to GND, with a pad
      within 3 mm (centre to centre) of the VCC pad on the board.
   e. on a ui or uio line, a resistor from the buffer's input to the 3.3 V (on either side of
      the current-sense resistor) or to GND, so that the input doesn't float while no dongle
      is plugged in. A uo line doesn't need one.
   f. Or a translator, one of TRANSLATORS: TI's SN74LVC1T45 (the DBV, DCK and DRL packages)
      and SN74LVC2T45 (DCU), in KiCad's Logic_LevelTranslator library, found by the symbol's
      name or its value. Each has two supplies, VCCA for its A port and VCCB for its B port,
      for a project whose other side runs at another voltage (a 1.8 V part, say). The rule
      relies on TI's datasheets, SCES515N and SCES516N (both revised June 2024):
        "VCC isolation feature – if either VCC input is at GND, both ports are in the
        high-impedance state"; "Ioff supports partial-power-down mode operation", with Ioff
        at most ±2 µA from -40 to 85 °C, on the A port with VCCA at 0 V and on the B port
        with VCCB at 0 V, for any pin voltage from 0 to 5.5 V;
        "DIR input circuit referenced to VCCA", and the function table: DIR low, "B data to
        A bus"; DIR high, "A data to B bus". The SN74LVC2T45's one DIR sets both channels,
        so its two channels run the same way.
      On each line it wants: A on the chip's side and B on the header's, the Pmod pin reaching
      A (through a resistor on a ui line) and the header pin on B's net, so that a translator
      turned round fails, and says so; VCCA on the Pmod's 3.3 V, as in b; VCCB on the net of
      a pin of the external header other than GND, the other side's own supply, so that B is
      unpowered whenever that side is (on the kit's 3.3 V it fails); GND on GND; DIR on GND
      on a ui line (B to A), and on VCCA's 3.3 V on a uo line (A to B), never on VCCB's net,
      since DIR's input levels are referenced to VCCA; and a capacitor as in d at each of the
      two VCC pins, from that pin's net to GND.
      The windows: on a ui line, a resistor between A and the Pmod pin is required, in c's
      window, for the same reasons as after a buffer, because A drives ui_in[0] against the
      RP2350's pull-down and its E9 leakage, and against any pin driving the line the other
      way. On a uo line none is needed: with the dongle unpowered, VCCB is at 0 V, both ports
      are high-impedance, and B passes at most Ioff (2 µA) into the dongle's RXD, so the
      current that a buffer's resistor limits there doesn't arise. A resistor between the
      Pmod pin and A is allowed on a uo line, and isn't sized. Rule e is for buffers; a
      translator's B port gets no pull. TI specifies VCC isolation with a supply at GND, and
      a dongle that is unplugged leaves VCCB floating unless something on the board pulls it
      down, which this check doesn't ask for.
      Not on the list: the SN74LVC2T45YZP, a ball-grid array; Nexperia's 74LVC2T45DC, whose
      datasheet we couldn't fetch to check (its site refused); and the 74LVCH parts, whose
      bus hold pushes current into a line.
   A line that reaches its header pin directly, or through resistors only, fails, with the
   reason in numbers: a resistor big enough for SkyWater's 100 µA into an unpowered chip
   (27 kΩ from a 3.3 V driver) is more than the 15.4 kΩ that still gives a valid high
   against the RP2350's pull-down (on a uo line: 10.5 kΩ from a CH340's 16.5 kΩ pull-up,
   against 5.28 kΩ for a valid low).
6. Every pin of an external part other than GND has an ESD part on its net: a part with a
   reference starting D, or from KiCad's Power_Protection library, with another pin on GND.
7. A current-sense point: a two-pin resistor from the Pmod's 3.3 V net to a net of the
   board's own that feeds something, with a test point (reference TP...) on each side. Of
   several such resistors (a pull-up is one too), the row reports the one with a test point
   on each side, or else the smallest.

--bringup FILE also runs check_bringup.py on a bring-up plan.

Exit status: 0 PASS, 1 FAIL, 2 the check couldn't run.
"""
import argparse
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from kicad_sexpr import parse, load, children, child, prop  # noqa: E402

DEFAULT_PINS = os.path.join(HERE, "pins", "simproc.json")
PMOD_PART = "PMOD_PERIPH_2x6"
SPACING = 22.86
TOL = 0.02
PIN_TIP = 12.64      # the pins' tips, along the footprint's x axis (6.64 mm body + 6 mm pins)
LOW, HIGH = ("1", "2", "3", "4"), ("7", "8", "9", "10")


def shown(path):
    rel = os.path.relpath(path)
    return os.path.abspath(path) if rel.startswith("..") else rel


def find_project(arg):
    if os.path.isdir(arg):
        pros = [f for f in sorted(os.listdir(arg)) if f.endswith(".kicad_pro")]
        if len(pros) != 1:
            raise SystemExit(f"check_pmod: {arg} holds {len(pros)} .kicad_pro files; name one")
        arg = os.path.join(arg, pros[0])
    stem, ext = os.path.splitext(arg)
    if ext not in (".kicad_pro", ".kicad_sch", ".kicad_pcb"):
        raise SystemExit(f"check_pmod: {arg} isn't a .kicad_pro, .kicad_sch or .kicad_pcb")
    return stem


# ---------------------------------------------------------------------------------------
# What the design says

class Netlist:
    def __init__(self, sch):
        tmp = tempfile.mkdtemp(prefix="pcb101-pmod-")
        out = os.path.join(tmp, "netlist.net")
        r = subprocess.run(["kicad-cli", "sch", "export", "netlist", "--format", "kicadsexpr", "-o", out, sch],
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        if r.returncode != 0 or not os.path.exists(out):
            raise RuntimeError(f"kicad-cli sch export netlist exited {r.returncode}:\n{r.stdout}")
        with open(out, encoding="utf-8") as f:
            root = parse(f.read())
        shutil.rmtree(tmp, ignore_errors=True)
        self.parts = {}
        for c in children(child(root, "components"), "comp"):
            ref = child(c, "ref")[1]
            src = child(c, "libsource")
            self.parts[ref] = {
                "value": (child(c, "value") or ["", ""])[1],
                "lib": (child(src, "lib") or ["", ""])[1] if src else "",
                "part": (child(src, "part") or ["", ""])[1] if src else "",
                "pins": {},
                "types": {},     # pin -> its electrical type in the symbol: input, output, ...
            }
        self.nets = {}
        for n in children(child(root, "nets"), "net"):
            name = child(n, "name")[1]
            nodes = [(child(nd, "ref")[1], child(nd, "pin")[1]) for nd in children(n, "node")]
            for nd in children(n, "node"):
                ref, pin = child(nd, "ref")[1], child(nd, "pin")[1]
                if ref in self.parts and child(nd, "pintype"):
                    self.parts[ref]["types"][pin] = child(nd, "pintype")[1]
            if name.startswith("unconnected-"):
                continue
            self.nets[name] = nodes
            for ref, pin in nodes:
                if ref in self.parts:
                    self.parts[ref]["pins"][pin] = name

    def net(self, ref, pin):
        return self.parts.get(ref, {}).get("pins", {}).get(pin)

    def resistors(self):
        """[(ref, pin_a, pin_b, value)] for every resistor element in the design."""
        out = []
        for ref, p in self.parts.items():
            part = p["part"]
            if part.startswith("R_Network"):
                n = int(re.sub(r"\D", "", part) or 0)
                out += [(ref, str(k), "1", p["value"]) for k in range(2, n + 2)]
            elif part.startswith("R_Pack"):
                n = int(re.sub(r"\D", "", part) or 0)
                out += [(ref, str(k), str(2 * n + 1 - k), p["value"]) for k in range(1, n + 1)]
            elif ref.startswith("R") and not ref.startswith("RN") and len(p["pins"]) <= 2 and part not in ("",):
                out.append((ref, "1", "2", p["value"]))
        return out

    def switches(self):
        """[(ref, pin_a, pin_b)] for every switch pole."""
        out = []
        for ref, p in self.parts.items():
            if not ref.startswith("SW"):
                continue
            m = re.match(r"SW_DIP_x(\d+)", p["part"])
            if m:
                n = int(m.group(1))
                out += [(ref, str(k), str(2 * n + 1 - k)) for k in range(1, n + 1)]
            else:
                out.append((ref, "1", "2"))
        return out


def parse_value(v):
    """'1k' -> 1000.0, '4k7' -> 4700.0, '10' -> 10.0, '100R' -> 100.0; None if unreadable."""
    s = v.strip().replace("Ω", "").replace("ohm", "").replace(" ", "")
    m = re.match(r"^(\d+(?:\.\d+)?)([RrkKmM]?)(\d*)$", s)
    if not m:
        return None
    mult = {"": 1, "R": 1, "r": 1, "k": 1e3, "K": 1e3, "m": 1e6, "M": 1e6}[m.group(2)]
    num = float(m.group(1) + ("." + m.group(3) if m.group(3) else ""))
    return num * mult


# The buffers rule 5 accepts on a line that crosses from another supply, as KiCad 10.0.5's
# 74xGxx library numbers their pins: ([(A, Y, OE), ...], VCC, GND). The 125s' OE is active low.
_1G = ([("2", "4", None)], "5", "3")
_1G125 = ([("2", "4", "1")], "5", "3")
_2G = ([("1", "6", None), ("3", "4", None)], "5", "2")
_2G125 = ([("2", "6", "1"), ("5", "3", "7")], "8", "4")
BUFFERS = {"74LVC1G17": _1G, "74LVC1G34": _1G, "74LVC1G125": _1G125,
           "74LVC2G17": _2G, "74LVC2G34": _2G, "74LVC2G125": _2G125,
           "74AUP1G17": _1G, "74AUP1G34": _1G, "74AUP1G125": _1G125}

# The dual-supply translators rule 5 also accepts, as KiCad 10.0.5's Logic_LevelTranslator
# library numbers their pins: ([(A, B), ...], DIR, VCCA, VCCB, GND). One DIR sets every
# channel's direction: high is A to B, low (GND) is B to A.
_1T = ([("3", "4")], "5", "1", "6", "2")
_2T = ([("2", "7"), ("3", "6")], "5", "1", "8", "4")
TRANSLATORS = {"SN74LVC1T45DBV": _1T, "SN74LVC1T45DCK": _1T, "SN74LVC1T45DRL": _1T, "SN74LVC2T45DCUR": _2T}

V = 3.3                    # the kit's I/O supply
VD = 0.6                   # a clamp diode's drop
I_PAD = 100e-6             # SkyWater's limit into an I/O pin beyond its supply
R_PD = 36e3                # the RP2350's strongest pull-down (36 to 113 kΩ), on ui_in[0]
VIH_CHIP = 0.7 * V         # SKY130's CMOS input high, 2.31 V
R_PU = 16.5e3              # a CH340's strongest RX pull-up: 3.3 V / 200 µA
VIL_DONGLE = 0.8           # a CH340's input low
R_UI = (330.0, 8.2e3)      # rule 5's window for a ui line's resistor (8.2 kΩ: RP2350-E9)
R_UO = (1e3, 5.1e3)        # and for a uo line's
DECOUPLE_MM = 3.0


def buffer_type(part):
    """'74LVC2G17' if a netlist part is one of BUFFERS, by its symbol's name or its value."""
    for s in (part["part"], part["value"]):
        m = re.search(r"74(?:LVC|AUP)[12]G(?:17|34|125)(?!\d)", s.upper())
        if m and m.group(0) in BUFFERS:
            return m.group(0)
    return None


def translator_type(part):
    """'SN74LVC1T45DBV' if a netlist part is one of TRANSLATORS, by its symbol's name or its
    value (with or without the R of a reel)."""
    for s in (part["part"], part["value"]):
        m = re.search(r"SN74LVC(?:1T45(DBV|DCK|DRL)|2T45DCU)R?(?![0-9A-Z])", s.upper())
        if m:
            return "SN74LVC1T45" + m.group(1) if m.group(1) else "SN74LVC2T45DCUR"
    return None


def fmt_volts(v):
    return f"{v:.2f} V"


class Board:
    def __init__(self, pcb):
        b = load(pcb)
        self.fps = {}
        for fp in children(b, "footprint"):
            ref = prop(fp, "Reference")
            at = child(fp, "at")
            x, y = float(at[1]), float(at[2])
            a = float(at[3]) if len(at) > 3 else 0.0
            pads = {}
            for p in children(fp, "pad"):
                pat = child(p, "at")
                pads.setdefault(p[1], (float(pat[1]), float(pat[2])))
            locked = child(fp, "locked") is not None and child(fp, "locked")[1:] == ["yes"]
            locked = locked or "locked" in fp[1:3]
            self.fps[ref] = {"name": fp[1], "x": x, "y": y, "angle": a, "pads": pads, "locked": locked}
        pts = []
        for kind in ("gr_line", "gr_rect", "gr_arc", "gr_poly", "gr_circle", "gr_curve"):
            for g in children(b, kind):
                lay = child(g, "layer")
                if not lay or lay[1] != "Edge.Cuts":
                    continue
                for key in ("start", "end", "mid"):
                    c = child(g, key)
                    if c:
                        pts.append((float(c[1]), float(c[2])))
                if kind == "gr_circle":
                    c, e = child(g, "center"), child(g, "end")
                    r = math.hypot(float(e[1]) - float(c[1]), float(e[2]) - float(c[2]))
                    pts += [(float(c[1]) - r, float(c[2]) - r), (float(c[1]) + r, float(c[2]) + r)]
                ptsn = child(g, "pts")
                for xy in children(ptsn, "xy") if ptsn else []:
                    pts.append((float(xy[1]), float(xy[2])))
        self.outline = (min(p[0] for p in pts), min(p[1] for p in pts),
                        max(p[0] for p in pts), max(p[1] for p in pts)) if pts else None

    def place(self, ref, lx, ly):
        """A footprint-local point on the board. KiCad's angles turn counter-clockwise as
        seen on screen, whose y axis points down."""
        f = self.fps[ref]
        a = math.radians(f["angle"])
        return (f["x"] + lx * math.cos(a) + ly * math.sin(a), f["y"] - lx * math.sin(a) + ly * math.cos(a))

    def inside(self, p):
        x0, y0, x1, y1 = self.outline
        return x0 <= p[0] <= x1 and y0 <= p[1] <= y1


# ---------------------------------------------------------------------------------------
# The checks

class Report:
    def __init__(self):
        self.rows = []

    def add(self, ok, what, detail):
        self.rows.append((ok, what, detail))

    def print(self):
        for ok, what, detail in self.rows:
            lines = detail.split("\n")
            print(f"  {'ok  ' if ok else 'FAIL'}  {what:12} {lines[0]}")
            for line in lines[1:]:
                print(f"  {'':4}  {'':12} {line}")

    @property
    def failed(self):
        return sum(1 for ok, *_ in self.rows if not ok)


def bus_pin(name):
    """'ui[3]' -> ('ui', '4'): the bus, and the Pmod pin number for that bit."""
    m = re.match(r"^(ui|uo|uio)\[(\d)\]$", name)
    if not m:
        raise SystemExit(f"check_pmod: pin list names {name!r}; use ui[n], uo[n] or uio[n]")
    bit = int(m.group(2))
    return m.group(1), (LOW + HIGH)[bit]


def check(stem, spec, protect):
    rep = Report()
    nl = Netlist(stem + ".kicad_sch")
    bd = Board(stem + ".kicad_pcb")
    res = nl.resistors()

    # --- connectors -----------------------------------------------------------------
    pmods = sorted(r for r, p in nl.parts.items() if p["part"] == PMOD_PART)
    sockets = spec["sockets"]
    role = {}
    if len(pmods) != len(sockets):
        rep.add(False, "connectors", f"the schematic has {len(pmods)} {PMOD_PART} "
                                     f"connector{'' if len(pmods) == 1 else 's'}; "
                                     f"this project needs {len(sockets)}, one per socket ({', '.join(sockets)})")
    else:
        missing = [r for r in pmods if r not in bd.fps]
        if missing:
            rep.add(False, "connectors", f"{', '.join(missing)} not on the board yet (Update PCB from Schematic, F8)")
        elif bd.outline is None:
            rep.add(False, "connectors", "the board has no outline on Edge.Cuts")
        else:
            angles = {round(bd.fps[r]["angle"] % 360, 3) for r in pmods}
            a = math.radians(bd.fps[pmods[0]]["angle"])
            u = (math.cos(a), -math.sin(a))            # the way the pins point
            left = (u[1], -u[0])                        # to your left, facing the way the pins point
            pos = {r: (bd.fps[r]["x"], bd.fps[r]["y"]) for r in pmods}
            order = sorted(pmods, key=lambda r: -(pos[r][0] * left[0] + pos[r][1] * left[1]))
            gaps, offs = [], []
            for p, q in zip(order, order[1:]):
                d = (pos[q][0] - pos[p][0], pos[q][1] - pos[p][1])
                gaps.append(-(d[0] * left[0] + d[1] * left[1]))
                offs.append(d[0] * u[0] + d[1] * u[1])
            where = ", ".join(f"{r} ({pos[r][0]:.2f}, {pos[r][1]:.2f})" for r in order)
            problems = []
            if len(angles) != 1:
                problems.append("they aren't all at the same angle: " +
                                ", ".join(f"{r} {bd.fps[r]['angle']:g}°" for r in pmods))
            else:
                bad = [g for g in gaps if abs(g - SPACING) > TOL]
                if bad:
                    problems.append("their spacing is " + " and ".join(f"{g:.2f}" for g in gaps) +
                                    f" mm; it must be {SPACING} mm")
                if any(abs(o) > TOL for o in offs):
                    problems.append("they aren't in a row: with the pins pointing away from you, " +
                                    " and ".join(f"{q} is {o:+.2f} mm from {p}"
                                                 for (p, q), o in zip(zip(order, order[1:]), offs)) +
                                    " (+ is further away from you, toward the pins' tips)")
                for r in pmods:
                    pads_in = all(bd.inside(bd.place(r, *xy)) for xy in bd.fps[r]["pads"].values())
                    tip = bd.place(r, PIN_TIP, 6.35)
                    if not pads_in:
                        problems.append(f"{r} has pads outside the board outline")
                    elif bd.inside(tip):
                        problems.append(f"{r}'s pins end inside the board outline; they must stick out "
                                        "past its edge to reach the demo board's sockets")
            unlocked = [r for r in pmods if not bd.fps[r]["locked"]]
            if problems:
                rep.add(False, "connectors", where + "\n" + "\n".join(problems))
            else:
                note = f", locked" if not unlocked else f"; {', '.join(unlocked)} not locked"
                rep.add(not unlocked, "connectors",
                        f"{where}: {SPACING} mm apart, in a row, pins past the edge{note}")
                role = dict(zip(sockets, order))
                bus = {"input": "ui", "bidir": "uio", "output": "uo"}
                rep.add(True, "sockets", ", ".join(f"{role[s]} {s} ({bus[s]})" for s in sockets) +
                        ", left to right with the pins pointing away from you")

    # --- power ----------------------------------------------------------------------------
    vcc = None
    if pmods:
        vccs = {nl.net(r, p) for r in pmods for p in ("6", "12")}
        gnds = {nl.net(r, p) for r in pmods for p in ("5", "11")}
        if len(vccs) == 1 and None not in vccs and gnds == {"GND"}:
            vcc = vccs.pop()
            rep.add(True, "power", f"{vcc} on pins 6 and 12, GND on pins 5 and 11, of every Pmod connector")
        else:
            rep.add(False, "power", "pins 6 and 12 of every Pmod connector must share one net (the demo "
                                    "board's 3.3 V), and pins 5 and 11 must be on GND; found "
                                    f"{net_names(vccs)} on pins 6 and 12, and {net_names(gnds)} on pins 5 and 11")

    if not role:
        rep.add(False, "pins", "not checked until the connectors pass")
        return rep, nl

    def series(net):
        """{other net: (resistor ref, value)} for resistors from `net` to a net that isn't
        GND or the supply."""
        out = {}
        for ref, a, b, val in res:
            na, nb = nl.net(ref, a), nl.net(ref, b)
            for x, y in ((na, nb), (nb, na)):
                if x == net and y and y not in ("GND", vcc):
                    out[y] = (ref, val)
        return out

    def hop(a, b):
        """How net a reaches net b: None if they're the same net, (resistor ref, value) if one
        series resistor joins them, False if neither."""
        if a == b:
            return None
        return series(a).get(b, False) if a else False

    # The Pmod's 3.3 V on either side of the current-sense resistor: vcc itself, and the net
    # on the far side of any resistor of 100 Ω or less from it, {net: that resistor}.
    far = {n: r for n, (r, v) in series(vcc).items() if (parse_value(v) or 1e9) <= 100} if vcc else {}
    pmod_3v3 = ({vcc} | set(far)) if vcc else set()

    def pmod_3v3_text():
        """'+3V3, the net of the Pmod pins 6 and 12, or /+3V3_PMOD, on the far side of R3'."""
        return f"{vcc}, the net of the Pmod pins 6 and 12" + "".join(
            f", or {n}, on the far side of {r}" for n, r in sorted(far.items()))

    def route(n0, hnet, into):
        """How the Pmod pin's net n0 reaches the header pin's net hnet, as a dict whose "kind"
        is direct, resistors (one or two in a row), buffer (a buffer from BUFFERS, driven from
        the side the line comes from), reversed (the same, turned round), translator (a
        channel of one of TRANSLATORS with A on the Pmod's side and B on the header's),
        translator-reversed (the same, turned round) or unlisted (another part that sits
        between them); None if it doesn't reach it. `into` is True for a line into the chip
        (ui, uio), whose header pin drives it."""
        if n0 is None or hnet is None:
            return None
        if n0 == hnet:
            return {"kind": "direct"}
        for r1, (ref1, v1) in series(n0).items():
            if r1 == hnet:
                return {"kind": "resistors", "res": [(ref1, v1)]}
            for r2, (ref2, v2) in series(r1).items():
                if r2 == hnet and ref2 != ref1:
                    return {"kind": "resistors", "res": [(ref1, v1), (ref2, v2)]}
        src, dst = (hnet, n0) if into else (n0, hnet)
        turned = None
        for ref, p in sorted(nl.parts.items()):
            t = buffer_type(p)
            for ch in BUFFERS[t][0] if t else []:
                na, ny = p["pins"].get(ch[0]), p["pins"].get(ch[1])
                if na is None or ny is None:
                    continue
                before, after = hop(src, na), hop(ny, dst)
                if before is not False and after is not False:
                    return {"kind": "buffer", "ref": ref, "type": t, "ch": ch, "before": before, "after": after}
                if hop(src, ny) is not False and hop(na, dst) is not False:
                    turned = turned or {"kind": "reversed", "ref": ref, "type": t, "ch": ch}
            t = translator_type(p)
            for ch in TRANSLATORS[t][0] if t else []:
                na, nb = p["pins"].get(ch[0]), p["pins"].get(ch[1])
                if na is None or nb is None:
                    continue
                a_side, b_side = hop(n0, na), hop(nb, hnet)
                if a_side is not False and b_side is not False:
                    return {"kind": "translator", "ref": ref, "type": t, "ch": ch, "a_side": a_side, "b_side": b_side}
                if hop(n0, nb) is not False and hop(na, hnet) is not False:
                    turned = turned or {"kind": "translator-reversed", "ref": ref, "type": t, "ch": ch}
        if turned:
            return turned
        near_src, near_dst = {src} | set(series(src)), {dst} | set(series(dst))
        for ref, p in sorted(nl.parts.items()):
            if ref.startswith(("U", "IC")) or p["lib"].startswith("74"):
                nets = set(p["pins"].values())
                if nets & near_src and nets & near_dst:
                    return {"kind": "unlisted", "ref": ref}
        return None

    def ends(here, there, into):
        """(the end that drives the line, the end it drives)."""
        return (there, here) if into else (here, there)

    def channel(t, ch, table):
        """'1' or '2' for a channel of a part with two, '' for a part with one."""
        chs = table[t][0]
        return str(chs.index(ch) + 1) if len(chs) > 1 else ""

    def listed(items):
        """'A', 'A and B', 'A, B and C'."""
        return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " and " + items[-1]

    def through(way, into):
        """'U1 (74LVC2G17, 1A pin 1 to 1Y pin 6) and R1 (1k)', or 'U1 (SN74LVC1T45DBV, B pin 4
        to A pin 3) and R1 (1k)': a buffer's or a translator's chain, in words, in the
        direction the line runs."""
        res = lambda r: f"{r[0]} ({r[1]})"  # noqa: E731
        if way["kind"] == "translator":
            ref, t, (a, b) = way["ref"], way["type"], way["ch"]
            n = channel(t, way["ch"], TRANSLATORS)
            if into:
                chain = [way["b_side"], f"{ref} ({t}, B{n} pin {b} to A{n} pin {a})", way["a_side"]]
            else:
                chain = [way["a_side"], f"{ref} ({t}, A{n} pin {a} to B{n} pin {b})", way["b_side"]]
            return listed([c if isinstance(c, str) else res(c) for c in chain if c])
        ref, t, (a, y, _) = way["ref"], way["type"], way["ch"]
        n = channel(t, way["ch"], BUFFERS)
        out = f"{ref} ({t}, {n}A pin {a} to {n}Y pin {y})"
        return out + (f" and {res(way['after'])}" if way["after"] else "")

    def turned_round(here, there, into, way):
        if way["kind"] == "translator-reversed":
            ref, t, (a, b) = way["ref"], way["type"], way["ch"]
            n = channel(t, way["ch"], TRANSLATORS)
            return (f"{ref} ({t}) is turned round on this line: its B{n} port (pin {b}) faces {here}, and its A{n} "
                    f"port (pin {a}) faces {there}\nthe A port, whose supply VCCA also powers DIR, must face the chip, "
                    f"and the B port {there.split(' (')[0]}")
        ref, t, (a, y, _) = way["ref"], way["type"], way["ch"]
        n = channel(t, way["ch"], BUFFERS)
        drv, rcv = ends(here, there, into)
        return (f"{ref} ({t}) is turned round on this line: its output, {n}Y (pin {y}), faces {drv}, and its "
                f"input, {n}A (pin {a}), faces {rcv}\n{drv.split(' (')[0]} drives the line, so it must reach "
                f"the input")

    def joined(here, there, into, way):
        """Lab 03's rule for a "to" pin: on one net, through one series resistor, or through
        a buffer or a translator the right way round."""
        k = way["kind"]
        if k == "direct":
            return True, f"{here} reaches {there} directly"
        if k == "resistors" and len(way["res"]) == 1:
            return True, f"{here} reaches {there} through {way['res'][0][0]} ({way['res'][0][1]})"
        if k in ("buffer", "translator"):
            drv, rcv = ends(here, there, into)
            return True, f"{drv} drives {rcv} through {through(way, into)}"
        if k in ("reversed", "translator-reversed"):
            return False, turned_round(here, there, into, way)
        return False, f"{here} doesn't reach {there}"

    def ui_window(rref, ohms):
        """(ok, text) for the resistor between a buffer's or a translator's output and a ui pin."""
        lo, hi = R_UI
        txt = (f"{rref} = {fmt_ohms(ohms)} ({fmt_ohms(lo)} to {fmt_ohms(hi)}): {V:g} V / {fmt_ohms(ohms)} = "
               f"{fmt_amps(V / ohms)} against a pin "
               f"driving the other way; {V:g} V × {fmt_ohms(R_PD)} / ({fmt_ohms(R_PD)} + {fmt_ohms(ohms)}) = "
               f"{fmt_volts(V * R_PD / (R_PD + ohms))} high against a {fmt_ohms(R_PD)} pull-down")
        if ohms < lo:
            return False, txt + f"\n{rref} is below {fmt_ohms(lo)}, so a fight can pass more than {fmt_amps(V / lo)}"
        if ohms > hi:
            return False, txt + (f"\n{rref} is above {fmt_ohms(hi)}, the most that still pulls the line low "
                                 f"against an A2 RP2350's input leakage (erratum E9)")
        return True, txt

    def uo_window(rref, ohms):
        """(ok, text) for the resistor between a buffer's output and a dongle's RXD."""
        lo, hi = R_UO
        txt = (f"{rref} = {fmt_ohms(ohms)} ({fmt_ohms(lo)} to {fmt_ohms(hi)}): ({V:g} V - {VD:g} V) / "
               f"{fmt_ohms(ohms)} = "
               f"{fmt_amps((V - VD) / ohms)} into an unpowered dongle; {V:g} V × {fmt_ohms(ohms)} / "
               f"({fmt_ohms(ohms)} + {fmt_ohms(R_PU)}) = {fmt_volts(V * ohms / (ohms + R_PU))} low "
               f"against a {fmt_ohms(R_PU)} pull-up")
        if ohms < lo:
            return False, txt + (f"\n{rref} is below {fmt_ohms(lo)}, so more than "
                                 f"{fmt_amps((V - VD) / lo)} can flow into an unpowered dongle")
        if ohms > hi:
            return False, txt + (f"\n{rref} is above {fmt_ohms(hi)}, so the low can be over the "
                                 f"{VIL_DONGLE:g} V a CH340 reads as low")
        return True, txt

    def decoupling(ref, vpin, net, name):
        """(ok, text) for the capacitor from `net` to GND nearest a part's supply pin, measured
        on the board."""
        if ref not in bd.fps or vpin not in bd.fps[ref]["pads"]:
            return False, f"{ref} isn't on the board yet, so its decoupling can't be measured"
        at = bd.place(ref, *bd.fps[ref]["pads"][vpin])
        caps = sorted((min(math.dist(at, bd.place(c, *xy)) for xy in bd.fps[c]["pads"].values()), c,
                       cp["value"]) for c, cp in nl.parts.items()
                      if c.startswith("C") and c in bd.fps and len(cp["pins"]) == 2
                      and set(cp["pins"].values()) == {net, "GND"})
        pin = f"{ref} pin {vpin}" + (f" ({name})" if name != "VCC" else "")
        if caps and caps[0][0] <= DECOUPLE_MM:
            return True, f"decoupling: {caps[0][1]} ({caps[0][2]}) from {net} to GND, a pad {caps[0][0]:.2f} mm from {pin}"
        if caps:
            return False, (f"no decoupling at {ref}'s {name}: the nearest capacitor from {net} to GND, "
                           f"{caps[0][1]}, has its nearest pad {caps[0][0]:.2f} mm from {pin}, "
                           f"more than {DECOUPLE_MM:g} mm")
        return False, (f"no capacitor from {net} to GND to decouple {ref}'s {name}; put one with a pad within "
                       f"{DECOUPLE_MM:g} mm of pin {vpin}")

    def crossing(here, there, into, way):
        """Rule 5, on a line that crosses from another supply: (ok, message)."""
        k = way["kind"]
        if k in ("direct", "resistors"):
            how = "directly" if k == "direct" else "through " + " and ".join(f"{r} ({v})" for r, v in way["res"])
            if into:
                why = (f"a resistor big enough for SkyWater's 100 µA ({fmt_ohms((V - VD) / I_PAD)}) is more than "
                       f"the {fmt_ohms(R_PD * (V / VIH_CHIP - 1))} that still gives a valid high against the "
                       f"RP2350's {fmt_ohms(R_PD)} pull-down")
            else:
                why = (f"a resistor big enough for SkyWater's 100 µA from a CH340's {fmt_ohms(R_PU)} RX pull-up "
                       f"({fmt_ohms((V - VD) / I_PAD - R_PU)}) is more than the "
                       f"{fmt_ohms(R_PU * VIL_DONGLE / (V - VIL_DONGLE))} that still gives a valid low at that RX")
            return False, f"{here} reaches {there} {how}, with no buffer\n{why}"
        if k == "unlisted":
            p = nl.parts[way["ref"]]
            return False, (f"{way['ref']} ({p['value']}) sits between {here} and {there}, and it isn't one of the "
                           f"parts this check accepts\nthose are single-supply buffers specified for partial power "
                           f"down (Ioff), {listed(list(BUFFERS))}, and dual-supply translators with Ioff on both "
                           f"ports, {listed(list(TRANSLATORS))}")
        if k in ("reversed", "translator-reversed"):
            return False, turned_round(here, there, into, way)
        if k == "translator":
            return crossing_translator(here, there, into, way)

        ref, t, (a, y, oe) = way["ref"], way["type"], way["ch"]
        drv, rcv = ends(here, there, into)
        p = nl.parts[ref]
        lines, bad = [f"{drv} drives {rcv} through {through(way, into)}"], []

        def problem(text):
            lines.append(text)
            bad.append(text)
        if way["before"]:
            problem(f"{way['before'][0]} sits between {drv.split(' (')[0]} and {ref}'s input; "
                    f"{drv.split(' (')[0]} must be on the input's net")
        if p["types"].get(a, "input") != "input" or p["types"].get(y, "output") not in ("output", "tri_state"):
            problem(f"{ref}'s pins {a} and {y} are {p['types'].get(a)} and {p['types'].get(y)} in its symbol; "
                    f"KiCad's {t} has them as input and output")

        # Its supply, on the Pmod's 3.3 V on either side of the current-sense resistor, and the
        # enable of a 125.
        vpin, gpin = BUFFERS[t][1], BUFFERS[t][2]
        vnet = nl.net(ref, vpin)
        sup = []
        if vcc is None:
            problem(f"{ref}'s supply isn't checked until the power row passes")
        elif vnet not in pmod_3v3:
            problem(f"{ref}'s VCC (pin {vpin}) is on {net_names({vnet})}; it must be on {pmod_3v3_text()}")
        else:
            sup.append(f"VCC (pin {vpin}) on {vnet}")
        if nl.net(ref, gpin) != "GND":
            problem(f"{ref}'s GND (pin {gpin}) is on {net_names({nl.net(ref, gpin)})}; it must be on GND")
        else:
            sup.append(f"GND (pin {gpin}) on GND")
        if oe:
            if nl.net(ref, oe) != "GND":
                problem(f"{ref}'s OE (pin {oe}) is on {net_names({nl.net(ref, oe)})}; a 125's OE is active "
                        "low, so tie it to GND")
            else:
                sup.append(f"OE (pin {oe}) on GND")
        if len(sup) == (3 if oe else 2):
            lines.append(f"{ref}: Ioff-rated, {', '.join(sup)}")

        # The resistor between its output and the far end.
        if not way["after"]:
            problem(f"{ref}'s output (pin {y}) reaches {rcv.split(' (')[0]} with no resistor between them")
        else:
            rref, rval = way["after"]
            ohms = parse_value(rval)
            if ohms is None or ohms <= 0:
                problem(f"{rref}'s value {rval!r} isn't a resistance the check can read")
            else:
                ok, txt = (ui_window if into else uo_window)(rref, ohms)
                (lines.append if ok else problem)(txt)

        # A decoupling capacitor at its VCC pin, on the net that pin is on.
        if vnet in pmod_3v3:
            ok, txt = decoupling(ref, vpin, vnet, "VCC")
            (lines.append if ok else problem)(txt)

        # A pull on the input of a buffer that brings a line into the chip.
        if into:
            na = nl.net(ref, a)
            rails = {"GND"} | pmod_3v3
            pull = None
            for r, x, w, val in res:
                for u, z in ((x, w), (w, x)):
                    if nl.net(r, u) == na and nl.net(r, z) in rails:
                        pull = (r, val, nl.net(r, z))
            if pull:
                lines.append(f"pull: {pull[0]} ({pull[1]}) from {ref}'s input ({na}) "
                             + ("down to GND" if pull[2] == "GND" else f"up to {pull[2]}"))
            else:
                problem(f"nothing pulls {ref}'s input ({na}) up or down, so it floats while no dongle is "
                        f"plugged in; add a resistor from it to {vcc or '3.3 V'} or GND")
        return not bad, "\n".join(lines)

    def crossing_translator(here, there, into, way):
        """Rule 5 on a line through a dual-supply translator: (ok, message)."""
        ref, t, (a, b) = way["ref"], way["type"], way["ch"]
        _, dpin, vapin, vbpin, gpin = TRANSLATORS[t]
        n = channel(t, way["ch"], TRANSLATORS)
        drv, rcv = ends(here, there, into)
        hpin = there.split(" (")[0]
        lines, bad = [f"{drv} drives {rcv} through {through(way, into)}"], []

        def problem(text):
            lines.append(text)
            bad.append(text)
        if way["b_side"]:
            problem(f"{way['b_side'][0]} sits between {hpin} and {ref}'s B{n}; {hpin} must be on B{n}'s net")

        # Its two supplies: VCCA on the Pmod's 3.3 V, VCCB on the other side's own supply.
        va, vb, g, d = (nl.net(ref, x) for x in (vapin, vbpin, gpin, dpin))
        hdr_pins = sorted((k for k, v in nl.parts[hdr]["pins"].items() if v == vb), key=lambda k: (len(k), k)) \
            if vb not in (None, "GND") else []
        sup = []
        if vcc is None:
            problem(f"{ref}'s supplies aren't checked until the power row passes")
        else:
            if va in pmod_3v3:
                sup.append(f"VCCA (pin {vapin}) on {va}")
            else:
                problem(f"{ref}'s VCCA (pin {vapin}) is on {net_names({va})}; the A port faces the chip, so VCCA must "
                        f"be on {pmod_3v3_text()}")
            if vb in pmod_3v3:
                problem(f"{ref}'s VCCB (pin {vbpin}) is on {vb}, the kit's 3.3 V, so the B port stays powered while "
                        f"the other side is off; VCCB must take that side's own supply, from a pin of {hdr}")
            elif not hdr_pins:
                problem(f"{ref}'s VCCB (pin {vbpin}) is on {net_names({vb})}, which no pin of {hdr} but GND is on; "
                        f"VCCB must take the supply of the side {hdr} connects to, from a pin of {hdr}")
            else:
                sup.append(f"VCCB (pin {vbpin}) on {vb}, {hdr} pin {hdr_pins[0]}")
        if g != "GND":
            problem(f"{ref}'s GND (pin {gpin}) is on {net_names({g})}; it must be on GND")
        else:
            sup.append(f"GND (pin {gpin}) on GND")
        if len(sup) == 3:
            lines.append(f"{ref}: Ioff on both ports, {', '.join(sup)}")

        # DIR: low (GND) sends B to A, high (VCCA's net) A to B. TI references DIR to VCCA.
        vcca = va if va in pmod_3v3 else vcc
        if into:
            if d == "GND":
                lines.append(f"DIR (pin {dpin}) on GND: B to A, the way this line runs")
            elif d is not None and d == vb:
                problem(f"{ref}'s DIR (pin {dpin}) is on {d}, VCCB's net, which TI's datasheet doesn't allow (DIR is "
                        f"referenced to VCCA), and high it sends A to B; this line runs from {hpin} into the chip, "
                        f"B to A, so DIR must be on GND")
            elif d in pmod_3v3:
                problem(f"{ref}'s DIR (pin {dpin}) is on {d}, high, which sends A to B; this line runs from {hpin} "
                        f"into the chip, B to A, so DIR must be on GND")
            else:
                problem(f"{ref}'s DIR (pin {dpin}) is on {net_names({d})}; this line runs from {hpin} into the chip, "
                        f"B to A, so tie DIR to GND")
        else:
            if d in pmod_3v3:
                lines.append(f"DIR (pin {dpin}) on {d}: A to B, the way this line runs")
            elif d == "GND":
                problem(f"{ref}'s DIR (pin {dpin}) is on GND, which sends B to A; this line runs from the chip out "
                        f"to {hpin}, A to B, so DIR must be on {vcca}, VCCA's net")
            elif d is not None and d == vb:
                problem(f"{ref}'s DIR (pin {dpin}) is on {d}, VCCB's net; TI's datasheet references DIR to VCCA, so "
                        f"tie it to {vcca}")
            else:
                problem(f"{ref}'s DIR (pin {dpin}) is on {net_names({d})}; this line runs from the chip out to "
                        f"{hpin}, A to B, so tie DIR to {vcca}, VCCA's net")

        # The resistor between A and the Pmod pin: R1's window on a ui line; none needed on a uo
        # line, where B is high-impedance whenever the dongle's VCC is at 0 V.
        if into:
            if not way["a_side"]:
                problem(f"{ref}'s A{n} (pin {a}) reaches {here} with no resistor between them; one of "
                        f"{fmt_ohms(R_UI[0])} to {fmt_ohms(R_UI[1])} caps a fight with a pin driving the line the "
                        f"other way")
            else:
                rref, rval = way["a_side"]
                ohms = parse_value(rval)
                if ohms is None or ohms <= 0:
                    problem(f"{rref}'s value {rval!r} isn't a resistance the check can read")
                else:
                    ok, txt = ui_window(rref, ohms)
                    (lines.append if ok else problem)(txt)
        elif way["a_side"]:
            lines.append(f"{way['a_side'][0]} ({way['a_side'][1]}) between {here} and {ref}'s A{n}: a uo line "
                         f"through a translator needs none, and the check doesn't size it")

        # A decoupling capacitor at each VCC pin, on the net that pin is on.
        for vpin, net, name, good in ((vapin, va, "VCCA", va in pmod_3v3), (vbpin, vb, "VCCB", bool(hdr_pins))):
            if good and vcc is not None:
                ok, txt = decoupling(ref, vpin, net, name)
                (lines.append if ok else problem)(txt)
        return not bad, "\n".join(lines)

    # --- the external header -----------------------------------------------------------
    hdr = None
    parts_spec = spec.get("parts", {})
    if "dongle" in parts_spec:
        cands = [r for r, p in nl.parts.items() if r.startswith("J") and r not in pmods
                 and nl.net(r, "1") == "GND" and "2" in p["pins"] and "3" in p["pins"]]
        if len(cands) > 1:
            # Prefer the one that reaches the most of the pin list's "to" pins.
            def score(r):
                s = 0
                for rule in spec["pins"]:
                    if "to" in rule:
                        busn, num = bus_pin(rule["pin"])
                        sock = {"ui": "input", "uio": "bidir", "uo": "output"}[busn]
                        n0 = nl.net(role[sock], num)
                        near = {n0} | set(series(n0))
                        s += sum(1 for p in ("2", "3") if nl.net(r, p) in near)
                return s
            cands.sort(key=score, reverse=True)
        hdr = cands[0] if cands else None
        if hdr is None:
            rep.add(False, "dongle", "no header for the dongle: a connector (reference J...) other than the "
                                     "Pmods, with pin 1 on GND and pins 2 and 3 for the dongle's TXD and RXD")
        else:
            rep.add(True, "dongle", f"{hdr}: pin 1 on GND, pins 2 and 3 for the dongle")

    # --- each pin --------------------------------------------------------------------------
    for rule in spec["pins"]:
        name = rule["pin"]
        busn, num = bus_pin(name)
        sock = {"ui": "input", "uio": "bidir", "uo": "output"}[busn]
        ref = role[sock]
        n0 = nl.net(ref, num)
        here = f"{ref} pin {num}"
        if n0 is None:
            rep.add(False, name, f"{here} isn't connected to anything")
            continue
        near = series(n0)
        if "to" in rule:
            tgt = parts_spec[rule["to"]["part"]]
            tpin = rule["to"]["pin"]
            what = tgt["pins"][tpin]
            if hdr is None:
                rep.add(False, name, f"{here}: no dongle header to reach")
                continue
            into = busn != "uo"
            there = f"{hdr} pin {tpin} ({what})"
            way = route(n0, nl.net(hdr, tpin), into)
            if way is None:
                other = [p for p in tgt["pins"] if p not in (tpin, "1")]
                swapped = [p for p in other if route(n0, nl.net(hdr, p), into) is not None]
                if swapped:
                    p = swapped[0]
                    rep.add(False, name, f"{here} reaches {hdr} pin {p} ({tgt['pins'][p]}), not pin {tpin} "
                                         f"({what}): are TX and RX swapped?")
                else:
                    rep.add(False, name, f"{here} doesn't reach {there}")
            elif protect and rule.get("crossing"):
                ok, msg = crossing(here, there, into, way)
                rep.add(ok, name, msg)
            else:
                ok, msg = joined(here, there, into, way)
                rep.add(ok, name, msg)
            continue
        line = {n0} | set(near)
        found, missing = [], []
        if "switch" in rule:
            sw = None
            for r, a, b in nl.switches():
                for x, y in ((a, b), (b, a)):
                    if nl.net(r, x) in line:
                        yn = nl.net(r, y)
                        if yn == vcc or any(nl.net(rr, pa) == vcc and nl.net(rr, pb) == yn or
                                            nl.net(rr, pb) == vcc and nl.net(rr, pa) == yn
                                            for rr, pa, pb, _ in res):
                            sw = f"switch {r} (pins {x}-{y}) to {yn}"
            (found if sw else missing).append(sw or "switch to the 3.3 V supply")
        if rule.get("pull") == "down":
            pd = None
            for r, a, b, val in res:
                for x, y in ((a, b), (b, a)):
                    if nl.net(r, x) in line and nl.net(r, y) == "GND":
                        pd = f"pull-down {r} ({val}{', pin ' + x if r.startswith('RN') else ''}) to GND"
            (found if pd else missing).append(pd or "pull-down resistor to GND")
        if missing:
            rep.add(False, name, f"{here} ({n0}) has no {' and no '.join(missing)}")
        else:
            rep.add(True, name, f"{here}: {', '.join(found)}")

    # --- protection (Lab 04) ---------------------------------------------------------------------
    if protect and hdr is not None:
        for part, ps in parts_spec.items():
            if not ps.get("external"):
                continue
            for p, what in ps["pins"].items():
                if what == "GND":
                    continue
                n = nl.net(hdr, p)
                esd = None
                for r, pp in nl.parts.items():
                    if not (r.startswith("D") or pp["lib"] == "Power_Protection"):
                        continue
                    pins_here = [k for k, v in pp["pins"].items() if v == n]
                    if pins_here and any(v == "GND" for v in pp["pins"].values()):
                        esd = f"{r} ({pp['value']}, pin {pins_here[0]}) to GND"
                (rep.add(True, f"ESD {hdr}.{p}", f"{n}: {esd}") if esd else
                 rep.add(False, f"ESD {hdr}.{p}", f"{n} ({what}) has no ESD part to GND on it"))
        def probes(n):
            return [rr for rr, pp in nl.parts.items() if rr.startswith("TP") and n in pp["pins"].values()]

        # Every resistor from the supply to a net that feeds something: the current spy, but
        # also a pull-up such as Lab 04's R4. The one with a test point on each side wins, then
        # the smallest.
        spies = []
        for r, a, b, val in res:
            for x, y in ((a, b), (b, a)):
                if vcc and nl.net(r, x) == vcc:
                    yn = nl.net(r, y)
                    if yn and yn not in ("GND", vcc) and len(nl.nets.get(yn, [])) > 1:
                        spies.append((not (probes(vcc) and probes(yn)), parse_value(val) or 1e12, r, val, yn))
        if not spies:
            rep.add(False, "sense", f"no current-sense resistor between {vcc} and a net of the board's own")
        else:
            _, _, r, val, yn = min(spies)
            tps = {n: probes(n) for n in (vcc, yn)}
            lacking = [n for n, t in tps.items() if not t]
            msg = f"{r} ({val}) from {vcc} to {yn}"
            if lacking:
                rep.add(False, "sense", msg + f"; no test point on {' or '.join(lacking)}")
            else:
                rep.add(True, "sense", msg + f", test points {tps[vcc][0]} and {tps[yn][0]}")
    return rep, nl


def net_names(nets):
    """'+3V3 and no net (a pin connected to nothing)': the nets a set of pins are on, as text.
    Netlist.net() gives None for a pin that's on no net, because KiCad puts an unconnected
    pin on a net of its own named unconnected-(...), which Netlist leaves out."""
    names = sorted(n for n in nets if n is not None)
    if None in nets:
        names.append("no net (a pin connected to nothing)")
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]


def fmt_ohms(r):
    return f"{r / 1e3:.3g} kΩ" if r >= 1e3 else f"{r:.3g} Ω"


def fmt_amps(i):
    """'3.3 mA', '270 µA': two significant figures, never in exponent form."""
    n = i * 1e3 if i >= 1e-3 else i * 1e6
    return f"{float(f'{n:.2g}'):g} {'mA' if i >= 1e-3 else 'µA'}"


def main():
    ap = argparse.ArgumentParser(description="The board check, then the Pmod connectors and the pin list.")
    ap.add_argument("project", help=".kicad_pro, or a folder with one")
    ap.add_argument("--pins", default=DEFAULT_PINS, help="the project's pin list (default: SimProc's)")
    ap.add_argument("--protect", action="store_true",
                    help="Lab 04: a buffer or translator on crossing lines, ESD and a current-sense point")
    ap.add_argument("--bringup", help="also check this BRINGUP.md")
    ap.add_argument("--no-board-check", action="store_true", help="skip check_board.py")
    args = ap.parse_args()

    stem = find_project(args.project)
    name = shown(stem + ".kicad_pro")
    for f in (stem + ".kicad_sch", stem + ".kicad_pcb"):
        if not os.path.exists(f):
            print(f"check_pmod: missing {shown(f)}", file=sys.stderr)
            return 2
    if shutil.which("kicad-cli") is None:
        print("check_pmod: kicad-cli isn't on the PATH. Run this through labs/common/kicad.sh.", file=sys.stderr)
        return 2
    with open(args.pins) as f:
        spec = json.load(f)

    board_rc = 0
    if not args.no_board_check:
        sys.stdout.flush()
        board_rc = subprocess.call([sys.executable, os.path.join(HERE, "check_board.py"), stem + ".kicad_pro"])
        if board_rc == 2:
            return 2
        print()

    print("PCB101 Pmod check")
    print(f"  project   {name}")
    print(f"  pins      {shown(args.pins)}: {spec['project']}")
    print(f"  rules     Lab 03{' and Lab 04 (--protect)' if args.protect else ''}")
    print()
    try:
        rep, _ = check(stem, spec, args.protect)
    except RuntimeError as e:
        print(f"check_pmod: {e}", file=sys.stderr)
        return 2
    rep.print()
    print()

    bring_rc = 0
    if args.bringup:
        sys.stdout.flush()
        if os.path.exists(args.bringup):
            bring_rc = subprocess.call([sys.executable, os.path.join(HERE, "check_bringup.py"), args.bringup])
        else:
            print(f"FAIL  {args.bringup}: not found; copy the bring-up plan template into your repository")
            bring_rc = 1
        if bring_rc == 2:
            return 2
        print()

    parts = []
    if not args.no_board_check:
        parts.append("board check " + ("PASS" if board_rc == 0 else "FAIL"))
    parts.append(f"{len(rep.rows) - rep.failed} of {len(rep.rows)} Pmod checks ok")
    if args.bringup:
        parts.append("bring-up plan " + ("PASS" if bring_rc == 0 else "FAIL"))
    ok = board_rc == 0 and rep.failed == 0 and bring_rc == 0
    print(f"{'PASS' if ok else 'FAIL'}  {name}: {'; '.join(parts)}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
