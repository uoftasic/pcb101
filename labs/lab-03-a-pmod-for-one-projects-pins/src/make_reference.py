#!/usr/bin/env python3
"""Write the board template, the Lab 03 and Lab 04 reference boards, and the stages in between.

    labs/common/kicad.sh python3 labs/lab-03-a-pmod-for-one-projects-pins/src/make_reference.py STAGE OUT

STAGE is one of:

  template    the empty board repository a student starts from (Lab 03, Part 1)
  noflags     Lab 03's schematic without its PWR_FLAGs, and an empty board
  schematic   Lab 03's schematic, finished, and an empty board
  connectors  that schematic, and a board with only the three Pmod connectors and the outline
  placed      every footprint placed, nothing routed
  routed      Lab 03's reference board, routed and filled
  swapped     the routed board with the dongle header's TXD and RXD swapped in the schematic
  protected   Lab 04's reference board: a buffer and a resistor on each UART line, ESD, a
              current-sense point
  translated  Lab 04's board with a dual-supply translator (SN74LVC1T45) on each UART line
              instead of the buffers, and the dongle's VCC on a fourth pin of J4, placed but
              not routed; Lab 04's self-test checks it

It runs inside the course's pinned KiCad image, because it needs kicad-cli (to upgrade the
schematic to KiCad 10's format and to export its netlist) and KiCad's pcbnew Python module
(to place footprints, route and fill zones). pcbnew's SWIG module is deprecated and due to go
in KiCad 11, so this script will need rewriting then; the checkers don't import it, and the
files it writes are ordinary KiCad 10 files.

The schematic is written as text with every connection made at a pin's end (a short wire and
a label, a power symbol or a no-connect flag), and the board is built from the netlist
kicad-cli exports for that schematic, so the two agree the way "Update PCB from Schematic"
would leave them. Coordinates are in millimetres. The layout is described in the README of
labs/lab-03-a-pmod-for-one-projects-pins/solutions/.
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
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.dirname(HERE)
REPO = os.path.dirname(os.path.dirname(LAB))
sys.path.insert(0, os.path.join(REPO, "labs", "common"))
from kicad_sexpr import parse, children, child  # noqa: E402

TEMPLATE = os.path.join(LAB, "template")
SYMDIR = "/usr/share/kicad/symbols"
FPDIR = "/usr/share/kicad/footprints"
NAME = "pmod"
NS = uuid.UUID("5b1c2a7e-3f0d-4c1e-9a55-0b101c0de303")


def uid(*parts):
    return str(uuid.uuid5(NS, "/".join(str(p) for p in parts)))


def run(cmd):
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if r.returncode != 0:
        raise SystemExit(f"{' '.join(cmd)} exited {r.returncode}:\n{r.stdout}")
    return r.stdout


# --------------------------------------------------------------------------------------
# Symbol libraries

def blocks(text, start=0):
    """(begin, end) offsets of each top-level child of the S-expression at `start`."""
    out, depth, i, in_str, begin = [], 0, start, False, None
    while i < len(text):
        c = text[i]
        if in_str:
            if c == "\\":
                i += 1
            elif c == '"':
                in_str = False
        elif c == '"':
            in_str = True
        elif c == "(":
            depth += 1
            if depth == 2:
                begin = i
        elif c == ")":
            if depth == 2:
                out.append((begin, i + 1))
            depth -= 1
            if depth == 0:
                return out
        i += 1
    raise ValueError("unbalanced parentheses")


_LIBS = {}


def lib_text(lib, workdir):
    """A symbol library's text in KiCad 10's format. Tiny Tapeout's Pmod library is saved by
    KiCad 7, so it goes through `kicad-cli sym upgrade` first (a temporary copy)."""
    if lib not in _LIBS:
        if lib == "TinyTapeout_PMOD":
            src = os.path.join(TEMPLATE, "lib", "TinyTapeout_PMOD.kicad_sym")
            dst = os.path.join(workdir, "TinyTapeout_PMOD.kicad_sym")
            shutil.copy(src, dst)
            run(["kicad-cli", "sym", "upgrade", "--force", dst])
            path = dst
        else:
            path = os.path.join(SYMDIR, lib + ".kicad_sym")
        with open(path, encoding="utf-8") as f:
            _LIBS[lib] = f.read()
    return _LIBS[lib]


class Sym:
    """One library symbol: its raw text (for lib_symbols) and its pins."""

    def __init__(self, lib_id, workdir):
        self.lib_id = lib_id
        lib, name = lib_id.split(":")
        text = lib_text(lib, workdir)
        raw = None
        for b, e in blocks(text):
            if re.match(r'\(symbol\s+"' + re.escape(name) + r'"', text[b:e]):
                raw = text[b:e]
        if raw is None:
            raise SystemExit(f"no symbol {lib_id}")
        self.raw = raw.replace(f'(symbol "{name}"', f'(symbol "{lib_id}"', 1)
        node = parse(raw)
        self.props = {p[1]: p[2] for p in children(node, "property")}
        self.pins = {}          # number -> (x, y, angle) in symbol coordinates (y up)
        self.unit = {}          # number -> the unit the pin belongs to; 0 for every unit
        for sub in children(node, "symbol"):
            m = re.match(re.escape(name) + r"_(\d+)_(\d+)$", sub[1])
            if m and m.group(2) not in ("0", "1"):
                continue
            for p in children(sub, "pin"):
                at = child(p, "at")
                num = child(p, "number")[1]
                self.pins[num] = (float(at[1]), float(at[2]), float(at[3]) if len(at) > 3 else 0.0)
                self.unit[num] = int(m.group(1)) if m else 0


# --------------------------------------------------------------------------------------
# The schematic

def fmt(v):
    return f"{round(v, 4):g}"


def rot(x, y, deg):
    """Rotate (x, y) counter-clockwise by deg, in y-up coordinates."""
    a = math.radians(deg)
    c, s = round(math.cos(a)), round(math.sin(a))
    return x * c - y * s, x * s + y * c


DIR = {0: (2.54, 0), 90: (0, -2.54), 180: (-2.54, 0), 270: (0, 2.54)}   # outward stub, on the sheet (y down)


class Sheet:
    def __init__(self, workdir, title, comment):
        self.workdir = workdir
        self.root = uid("root")
        self.title, self.comment = title, comment
        self.syms = {}
        self.items = []        # raw text of wires, labels, junctions, flags, texts
        self.instances = []    # raw text of placed symbols
        self.npwr = 0
        self.points = {}       # (ref, pin) -> (x, y, outward angle)

    def sym(self, lib_id):
        if lib_id not in self.syms:
            self.syms[lib_id] = Sym(lib_id, self.workdir)
        return self.syms[lib_id]

    def place(self, ref, lib_id, x, y, angle=0, value=None, footprint=None, fields=None, hide_value=False,
              ref_at=None, value_at=None, unit=1):
        """Place a symbol, or one unit of a symbol that has several (U1's two buffers and its
        power pins are units 1, 2 and 3, each placed with the same reference). The reference
        goes above the unit's pins and the value below them, unless ref_at or value_at give
        (x, y, justify) for them."""
        s = self.sym(lib_id)
        props = dict(s.props)
        props["Reference"] = ref
        if value is not None:
            props["Value"] = value
        if footprint is not None:
            props["Footprint"] = footprint
        for k in ("Datasheet", "Description"):
            props.setdefault(k, "")
        if fields:
            props.update(fields)
        pts = []
        for num, (px, py, pa) in s.pins.items():
            if s.unit[num] not in (0, unit):
                continue
            rx, ry = rot(px, py, angle)
            self.points[(ref, num)] = (round(x + rx, 4), round(y - ry, 4), int((pa + 180 + angle) % 360))
            pts.append(self.points[(ref, num)][1])
        ref_at = ref_at or (x, min(pts) - 2.54, None)
        value_at = value_at or (x, max(pts) + 2.54, None)
        tag = ref if unit == 1 else f"{ref}/{unit}"
        out = [f'\t(symbol\n\t\t(lib_id "{lib_id}")\n\t\t(at {fmt(x)} {fmt(y)} {angle})\n\t\t(unit {unit})\n'
               f'\t\t(exclude_from_sim no)\n\t\t(in_bom yes)\n\t\t(on_board yes)\n\t\t(dnp no)\n'
               f'\t\t(uuid "{uid("sym", tag)}")\n']
        power = ref.startswith("#")
        for k, v in props.items():
            if k.startswith("ki_"):
                continue
            hide = k not in ("Reference", "Value") or (k == "Reference" and power) or (k == "Value" and hide_value)
            just = None
            if k == "Reference":
                px, py, just = ref_at
            elif k == "Value":
                px, py, just = value_at
            else:
                px, py = x, y
            v = v.replace("\\", "\\\\").replace('"', '\\"')
            out.append(f'\t\t(property "{k}" "{v}"\n\t\t\t(at {fmt(px)} {fmt(py)} 0)\n\t\t\t(effects\n'
                       f'\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n'
                       + (f"\t\t\t\t(justify {just})\n" if just else "")
                       + ("\t\t\t\t(hide yes)\n" if hide else "") + "\t\t\t)\n\t\t)\n")
        for num in s.pins:          # every pin of the symbol, in each unit, as KiCad writes them
            out.append(f'\t\t(pin "{num}"\n\t\t\t(uuid "{uid("pin", tag, num)}")\n\t\t)\n')
        out.append(f'\t\t(instances\n\t\t\t(project "{NAME}"\n\t\t\t\t(path "/{self.root}"\n'
                   f'\t\t\t\t\t(reference "{ref}")\n\t\t\t\t\t(unit {unit})\n\t\t\t\t)\n\t\t\t)\n\t\t)\n\t)\n')
        self.instances.append("".join(out))
        return s

    def wire(self, a, b):
        self.items.append(f'\t(wire\n\t\t(pts\n\t\t\t(xy {fmt(a[0])} {fmt(a[1])}) (xy {fmt(b[0])} {fmt(b[1])})\n'
                          f'\t\t)\n\t\t(stroke\n\t\t\t(width 0)\n\t\t\t(type default)\n\t\t)\n'
                          f'\t\t(uuid "{uid("wire", a, b)}")\n\t)\n')

    def junction(self, p):
        self.items.append(f'\t(junction\n\t\t(at {fmt(p[0])} {fmt(p[1])})\n\t\t(diameter 0)\n\t\t(color 0 0 0 0)\n'
                          f'\t\t(uuid "{uid("junction", p)}")\n\t)\n')

    def label(self, name, p, angle):
        just = "left bottom" if angle in (0, 90) else "right bottom"
        a = {0: 0, 90: 90, 180: 180, 270: 270}[angle]
        self.items.append(f'\t(label "{name}"\n\t\t(at {fmt(p[0])} {fmt(p[1])} {a})\n\t\t(effects\n\t\t\t(font\n'
                          f'\t\t\t\t(size 1.27 1.27)\n\t\t\t)\n\t\t\t(justify {just})\n\t\t)\n'
                          f'\t\t(uuid "{uid("label", name, p)}")\n\t)\n')

    def no_connect(self, p):
        self.items.append(f'\t(no_connect\n\t\t(at {fmt(p[0])} {fmt(p[1])})\n\t\t(uuid "{uid("nc", p)}")\n\t)\n')

    def text(self, s, p, size=1.27):
        s = s.replace('"', '\\"').replace("\n", "\\n")
        self.items.append(f'\t(text "{s}"\n\t\t(exclude_from_sim no)\n\t\t(at {fmt(p[0])} {fmt(p[1])} 0)\n'
                          f'\t\t(effects\n\t\t\t(font\n\t\t\t\t(size {size} {size})\n\t\t\t)\n'
                          f'\t\t\t(justify left top)\n\t\t)\n\t\t(uuid "{uid("text", s)}")\n\t)\n')

    def power(self, net, p, outward):
        """A power symbol (+3V3 or GND) at p, its graphic pointing `outward` (degrees, y up),
        and its name written level, beyond the end of the graphic."""
        self.npwr += 1
        default = 90 if net != "GND" else 270
        at = {0: (p[0] + 3.81, p[1], "left"), 180: (p[0] - 3.81, p[1], "right"),
              90: (p[0], p[1] - 3.81, None), 270: (p[0], p[1] + 3.81, None)}[outward]
        self.place(f"#PWR0{self.npwr:02d}", f"power:{net}", p[0], p[1], (outward - default) % 360, value_at=at)

    def flag(self, p, angle):
        self.npwr += 1
        self.place(f"#FLG0{self.npwr:02d}", "power:PWR_FLAG", p[0], p[1], angle)

    def stub(self, ref, num, length=2.54):
        x, y, o = self.points[(ref, num)]
        dx, dy = DIR[o]
        k = length / 2.54
        end = (round(x + dx * k, 4), round(y + dy * k, 4))
        self.wire((x, y), end)
        return end, o

    def attach(self, ref, num, what):
        """Connect one pin: 'L:NAME' (wire and label), 'P:NET' (wire and power symbol) or 'NC'."""
        if what == "NC":
            x, y, _ = self.points[(ref, num)]
            self.no_connect((x, y))
        elif what.startswith("L:"):
            end, o = self.stub(ref, num)
            self.label(what[2:], end, o)
        elif what.startswith("P:"):
            end, o = self.stub(ref, num)
            self.power(what[2:], end, o)
        else:
            raise ValueError(what)

    def bus(self, ref, nums, top_what, reach=5.08):
        """Join pins on one side of a part with stubs and a wire along their ends, and put
        a power symbol or label on a wire leaving the first pin's end (outward-up)."""
        ends = [self.stub(ref, n, reach)[0] for n in nums]
        for a, b in zip(ends, ends[1:]):
            self.wire(a, b)
        for e in ends[1:-1]:
            self.junction(e)
        top = (ends[0][0], ends[0][1] - 5.08)
        self.wire(ends[0], top)
        self.junction(ends[0])
        if top_what.startswith("P:"):
            self.power(top_what[2:], top, 90)
        else:
            self.label(top_what[2:], top, 90)

    def write(self, path):
        head = (f'(kicad_sch\n\t(version 20260306)\n\t(generator "eeschema")\n\t(generator_version "10.0")\n'
                f'\t(uuid "{self.root}")\n\t(paper "A4")\n\t(title_block\n\t\t(title "{self.title}")\n'
                f'\t\t(date "2026-11-16")\n\t\t(rev "1")\n\t\t(company "UofT ASIC Team, PCB101")\n'
                f'\t\t(comment 1 "{self.comment}")\n\t)\n\t(lib_symbols\n')
        libs = "".join("\t\t" + s.raw.replace("\n", "\n\t\t") + "\n" for s in self.syms.values())
        body = "".join(self.items) + "".join(self.instances)
        tail = '\t(sheet_instances\n\t\t(path "/"\n\t\t\t(page "1")\n\t\t)\n\t)\n\t(embedded_fonts no)\n)\n'
        with open(path, "w", encoding="utf-8") as f:
            f.write(head + libs + "\t)\n" + body + tail)


PMOD = "TinyTapeout_PMOD:PMOD_PERIPH_2x6"
PMOD_FP = "TinyTapeout_PMOD:PinHeader_2x06_P2.54mm_PMODPeriph2B"
R_FP = "Resistor_SMD:R_0805_2012Metric_Pad1.20x1.40mm_HandSolder"
C_FP = "Capacitor_SMD:C_0805_2012Metric_Pad1.18x1.45mm_HandSolder"
# TI's SN74LVC2G17: units 1 and 2 are the buffers (1A pin 1 to 1Y pin 6, 2A pin 3 to 2Y pin 4),
# unit 3 holds GND (pin 2) and VCC (pin 5), as in the DBV package's pinout. KiCad's symbol
# has no footprint, so the schematic gives the DBV package's, SOT-23-6.
BUF = "74xGxx:74LVC2G17"
SOT6_FP = "Package_TO_SOT_SMD:SOT-23-6"


TRANSLATOR = "Logic_LevelTranslator:SN74LVC1T45DBV"


def supply(s, ref, num, net, toward):
    """A supply pin at the top of a symbol: a stub up, a short wire left or right, and the
    net's label at its end, written level."""
    end, _ = s.stub(ref, num)
    far = (end[0] + (5.08 if toward == "right" else -5.08), end[1])
    s.wire(end, far)
    s.label(net, far, 0 if toward == "right" else 180)


def translators(s):
    """The translated variant's UART lines (stage translated): each through one TI
    SN74LVC1T45, a dual-supply translator with Ioff on both ports, its A port on +3V3_PMOD and
    its B port on the dongle's own VCC (J4 pin 4). U1 carries ui[0] from B to A (DIR on GND)
    and on through R1; U2 carries uo[0] from A to B (DIR on +3V3_PMOD, VCCA's net). A
    capacitor sits at each VCC pin, and R4 holds DONGLE_VCC at GND while no dongle is plugged
    in, so that both ports then go high-impedance."""
    s.place("R1", "Device:R", 205.74, 86.36, 90, value="1k", footprint=R_FP)
    s.attach("R1", "1", "L:UART_RX")
    for ref, y, a, b, d in (("U1", 86.36, "RX_BUF", "DONGLE_TXD", "P:GND"),
                            ("U2", 116.84, "UART_TX", "DONGLE_RXD", "L:+3V3_PMOD")):
        s.place(ref, TRANSLATOR, 233.68, y, 0, value="SN74LVC1T45DBV",
                ref_at=(238.76, y + 10.16, "left"), value_at=(238.76, y + 12.7, "left"))
        if ref == "U1":
            s.wire(s.points[("R1", "2")][:2], s.points[("U1", "3")][:2])
            s.label("RX_BUF", (210.82, 86.36), 0)
        else:
            s.attach(ref, "3", f"L:{a}")
        s.attach(ref, "4", f"L:{b}")
        s.attach(ref, "5", d)
        s.attach(ref, "2", "P:GND")
        supply(s, ref, "1", "+3V3_PMOD", "left")
        supply(s, ref, "6", "DONGLE_VCC", "right")
    for ref, x, y, net in (("C1", 264.16, 137.16, "+3V3_PMOD"), ("C2", 274.32, 137.16, "DONGLE_VCC"),
                           ("C3", 269.24, 157.48, "+3V3_PMOD"), ("C4", 279.4, 157.48, "DONGLE_VCC")):
        s.place(ref, "Device:C", x, y, 0, value="100n", footprint=C_FP,
                ref_at=(x - 2.54, y - 1.27, "right"), value_at=(x - 2.54, y + 1.27, "right"))
        s.attach(ref, "1", f"L:{net}")
        s.attach(ref, "2", "P:GND")
    s.place("R4", "Device:R", 271.78, 86.36, 0, value="100k", footprint=R_FP,
            ref_at=(274.32, 85.09, "left"), value_at=(274.32, 87.63, "left"))
    s.attach("R4", "1", "L:DONGLE_VCC")
    s.attach("R4", "2", "P:GND")
    s.text("U1, U2: SN74LVC1T45, A on the kit's 3.3 V\n"
           "after R3, B on the dongle's VCC. U1: B to A\n"
           "(DIR on GND); U2: A to B (DIR on VCCA).\n"
           "R4 holds the dongle's VCC at 0 V while it's\n"
           "unplugged; C1 to C4 decouple the VCC pins.", (185.42, 132.08))


def pmod_pins(io):
    """Pmod symbol pin number for IO1..IO8."""
    return str(io) if io <= 4 else str(io + 2)


def schematic(sheet, lab, flags=True, swap=False, translated=False):
    s = sheet
    protect = lab == "04"
    rx_hdr = "DONGLE_TXD" if protect else "UART_RX"     # the net on the header's pin 2
    tx_hdr = "DONGLE_RXD" if protect else "UART_TX"     # the net on the header's pin 3
    if swap:
        rx_hdr, tx_hdr = tx_hdr, rx_hdr

    # The three Pmod connectors, top to bottom on the sheet: input, bidirectional, output.
    for ref, y, role, used in (("J1", 50.8, "INPUT socket: ui_in[0..7]", {1: "L:UART_RX"}),
                               ("J2", 101.6, "BIDIR socket: uio[0..7]",
                                {i: f"L:UIO{i - 1}" for i in range(1, 9)}),
                               ("J3", 152.4, "OUTPUT socket: uo_out[0..7]", {1: "L:UART_TX"})):
        s.place(ref, PMOD, 76.2, y, 0, footprint=PMOD_FP)
        for io in range(1, 9):
            s.attach(ref, pmod_pins(io), used.get(io, "NC"))
        for num in ("5", "11"):
            s.attach(ref, num, "P:GND")
        for num in ("6", "12"):
            s.attach(ref, num, "P:+3V3")
        s.text(f"{ref}, {role}", (63.5, y - 20.32))

    # The baud-rate switches and their pull-downs.
    s.place("SW1", "Switch:SW_DIP_x08", 165.1, 101.6, 0, value="SW_DIP_x08",
            footprint="Button_Switch_THT:SW_DIP_SPSTx08_Slide_9.78x22.5mm_W7.62mm_P2.54mm")
    for k in range(1, 9):
        s.attach("SW1", str(k), f"L:UIO{k - 1}")
    s.bus("SW1", [str(n) for n in range(16, 8, -1)], "L:+3V3_PMOD" if protect else "P:+3V3")
    s.text("SW1: uio[7:0] sets SimProc's UART bit period,\nclk_per_bit = uio x 4. A switch that is on reads 1.",
           (152.4, 116.84))
    s.place("RN1", "Device:R_Network08", 165.1, 139.7, 180, value="10k",
            footprint="Resistor_THT:R_Array_SIP9",
            ref_at=(151.13, 138.43, "right"), value_at=(151.13, 140.97, "right"))
    for k in range(2, 10):
        s.attach("RN1", str(k), f"L:UIO{9 - k}")
    s.attach("RN1", "1", "P:GND")
    s.text("RN1: a pull-down on every uio line, so a switch\nthat is off reads 0 rather than floating.",
           (152.4, 152.4))

    # The header for the USB-UART dongle.
    if translated:
        s.place("J4", "Connector_Generic:Conn_01x04", 228.6, 50.8, 180, value="USB-UART",
                footprint="Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical")
        s.attach("J4", "4", "L:DONGLE_VCC")
        s.text("J4: a dongle at 1.65 V to 5.5 V. Pin 2 to its\nTXD, pin 3 to its RXD, pin 4 to its VCC.",
               (205.74, 60.96))
    else:
        s.place("J4", "Connector_Generic:Conn_01x03", 228.6, 50.8, 180, value="USB-UART",
                footprint="Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical")
        s.text("J4: header for a 3.3 V USB-UART dongle.\nPin 2 goes to the dongle's TXD, pin 3 to its RXD.\n"
               "Leave the dongle's VCC unconnected.", (205.74, 60.96))
    s.attach("J4", "1", "P:GND")
    s.attach("J4", "2", f"L:{rx_hdr}")
    s.attach("J4", "3", f"L:{tx_hdr}")

    if protect and translated:
        translators(s)
    elif protect:
        # Each UART line goes through one buffer of U1 and then a resistor. ui[0] runs from
        # the dongle header on the right of the sheet to the input socket on the left, so its
        # buffer (unit 1) points left; uo[0]'s (unit 2) points right.
        s.place("R1", "Device:R", 205.74, 86.36, 90, value="1k", footprint=R_FP)
        s.attach("R1", "1", "L:UART_RX")
        s.place("U1", BUF, 233.68, 86.36, 180, value="74LVC2G17", footprint=SOT6_FP, unit=1,
                ref_at=(233.68, 76.2, None), value_at=(233.68, 78.74, None))
        s.wire(s.points[("R1", "2")][:2], s.points[("U1", "6")][:2])
        s.label("RX_BUF", (210.82, 86.36), 0)
        s.place("R4", "Device:R", 264.16, 82.55, 0, value="100k", footprint=R_FP,
                ref_at=(266.7, 81.28, "left"), value_at=(266.7, 83.82, "left"))
        end, _ = s.stub("R4", "1")
        s.wire(end, (end[0] + 2.54, end[1]))
        s.label("+3V3_PMOD", (end[0] + 2.54, end[1]), 0)
        s.wire(s.points[("U1", "1")][:2], s.points[("R4", "2")][:2])
        s.label("DONGLE_TXD", (250.19, 86.36), 0)
        s.place("U1", BUF, 233.68, 99.06, 0, value="74LVC2G17", footprint=SOT6_FP, unit=2,
                ref_at=(233.68, 109.22, None), value_at=(233.68, 111.76, None))
        s.attach("U1", "3", "L:UART_TX")
        s.place("R2", "Device:R", 261.62, 99.06, 90, value="1k", footprint=R_FP)
        s.wire(s.points[("U1", "4")][:2], s.points[("R2", "1")][:2])
        s.label("TX_BUF", (247.65, 99.06), 0)
        s.attach("R2", "2", "L:DONGLE_RXD")
        s.place("U1", BUF, 264.16, 127.0, 0, value="74LVC2G17", footprint=SOT6_FP, unit=3,
                ref_at=(256.54, 125.73, "right"), value_at=(256.54, 128.27, "right"))
        s.attach("U1", "2", "P:GND")
        s.place("C1", "Device:C", 279.4, 127.0, 0, value="100n", footprint=C_FP,
                ref_at=(276.86, 125.73, "right"), value_at=(276.86, 128.27, "right"))
        # U1's VCC and C1's top on one wire, labelled +3V3_PMOD at its left end.
        vcc, _ = s.stub("U1", "5")
        top, _ = s.stub("C1", "1")
        corner = (top[0], vcc[1])
        s.wire(vcc, corner)
        s.wire(top, corner)
        s.wire(vcc, (vcc[0] - 5.08, vcc[1]))
        s.junction(vcc)
        s.label("+3V3_PMOD", (vcc[0] - 5.08, vcc[1]), 180)
        s.attach("C1", "2", "P:GND")
        s.text("U1: two Schmitt-trigger buffers on the kit's 3.3 V,\n"
               "after R3, so the current spy sees U1's current.\n"
               "With the kit off, each pin of U1 passes at most\n"
               "10 uA (Ioff), so the dongle can't power the chip.\n"
               "R1: at most 3.3 V / 1k = 3.3 mA if something\n"
               "drives ui[0] the other way.\n"
               "R2: at most (3.3 - 0.6) V / 1k = 2.7 mA into an\n"
               "unpowered dongle.\n"
               "R4 holds U1's input high with no dongle in J4.\n"
               "C1 decouples U1, next to its VCC pin.", (185.42, 120.65))
    if protect:
        s.place("D1", "Power_Protection:SP0502BAHT", 266.7, 50.8, 0, value="SP0502BAHT",
                ref_at=(271.78, 49.53, "left"), value_at=(271.78, 52.07, "left"))
        s.attach("D1", "1", "L:DONGLE_TXD")
        s.attach("D1", "2", "L:DONGLE_RXD")
        s.attach("D1", "3", "P:GND")
        s.text("D1: ESD protection on the\npins a cable plugs into.", (256.54, 63.5))
        s.place("R3", "Device:R", 215.9, 147.32, 90, value="10", footprint=R_FP)
        s.attach("R3", "1", "P:+3V3")
        s.attach("R3", "2", "L:+3V3_PMOD")
        s.place("TP1", "Connector:TestPoint", 241.3, 152.4, 180, value="TestPoint",
                footprint="TestPoint:TestPoint_Pad_D1.5mm", hide_value=True,
                ref_at=(243.84, 154.94, "left"))
        s.attach("TP1", "1", "P:+3V3")
        s.place("TP2", "Connector:TestPoint", 254.0, 142.24, 0, value="TestPoint",
                footprint="TestPoint:TestPoint_Pad_D1.5mm", hide_value=True,
                ref_at=(256.54, 139.7, "left"))
        s.attach("TP2", "1", "L:+3V3_PMOD")
        s.text("R3: a 10 ohm current spy in the Pmod's own supply.\n"
               "The voltage between TP1 and TP2 is 10 ohm x the current.", (198.12, 157.48))

    if flags:
        s.power("+3V3", (25.4, 177.8), 90)
        s.wire((25.4, 177.8), (25.4, 180.34))
        s.flag((25.4, 180.34), 180)
        s.power("GND", (38.1, 182.88), 270)
        s.wire((38.1, 180.34), (38.1, 182.88))
        s.flag((38.1, 180.34), 0)
        s.text("Power enters through the Pmod connectors,\nso PWR_FLAG tells ERC where it comes from.",
               (45.72, 177.8))
        if protect:
            # U1's VCC is a power input on +3V3_PMOD, which takes its supply through R3, a
            # passive part, so ERC needs a PWR_FLAG on that net too.
            s.flag((50.8, 190.5), 0)
            s.wire((50.8, 190.5), (55.88, 190.5))
            s.label("+3V3_PMOD", (55.88, 190.5), 0)
            s.text("+3V3_PMOD is fed through R3, a passive part,\nso it needs a PWR_FLAG of its own.",
                   (71.12, 187.96))
        if translated:
            # The translators' VCCB pins are power inputs on DONGLE_VCC, which only J4 feeds.
            s.flag((50.8, 198.12), 0)
            s.wire((50.8, 198.12), (55.88, 198.12))
            s.label("DONGLE_VCC", (55.88, 198.12), 0)


# --------------------------------------------------------------------------------------
# The netlist

def netlist(sch, workdir):
    out = os.path.join(workdir, "pmod.net")
    run(["kicad-cli", "sch", "export", "netlist", "--format", "kicadsexpr", "-o", out, sch])
    with open(out, encoding="utf-8") as f:
        root = parse(f.read())
    comps = {}
    for c in children(child(root, "components"), "comp"):
        ref = child(c, "ref")[1]
        fields = {}
        fl = child(c, "fields")
        for fd in children(fl, "field") if fl else []:
            name = child(fd, "name")[1]
            fields[name] = fd[2] if len(fd) > 2 and isinstance(fd[2], str) else ""
        comps[ref] = {"value": child(c, "value")[1],
                      "footprint": (child(c, "footprint") or ["", ""])[1],
                      "fields": fields,
                      "tstamp": child(c, "tstamps")[1]}
    pad_net = {}
    for n in children(child(root, "nets"), "net"):
        name = child(n, "name")[1]
        for node in children(n, "node"):
            pad_net[(child(node, "ref")[1], child(node, "pin")[1])] = name
    return comps, pad_net


# --------------------------------------------------------------------------------------
# The board

BOARD = (100.0, 50.0, 164.0, 82.0)          # outline: left, top, right, bottom
PMOD_X = (102.0, 124.86, 147.72)            # pin 6 of J1, J2 and J3; 22.86 mm apart
PMOD_Y = 56.35                              # the row of pins 1 to 6; pins 7 to 12 at 53.81

PLACE3 = {
    "J1": (PMOD_X[0], PMOD_Y, 90), "J2": (PMOD_X[1], PMOD_Y, 90), "J3": (PMOD_X[2], PMOD_Y, 90),
    "J4": (110.0, 66.0, 0),
    "RN1": (126.13, 62.5, 0),
    "SW1": (146.45, 67.0, 270),
}
# Lab 04 puts the protection between J1 and the dongle header J4: D1 at the header, U1 to its
# upper right, R1 between U1 and J1's pin 1 (ui[0]), R2 under U1's 2Y pin, C1 to the right of
# U1's VCC pin, and R4 above J4. U1 at 0 degrees has pins 1 to 3 down its left side (1A, GND,
# 2A) and 6 to 4 down its right (1Y, VCC, 2Y).
PLACE4 = dict(PLACE3, **{
    "R1": (114.70, 61.5, 270), "R2": (119.0, 68.6, 270), "R3": (124.86, 66.4, 270),
    "R4": (112.4, 61.6, 270),
    "U1": (117.8625, 64.6, 0), "C1": (121.9, 66.0, 0),
    "D1": (113.9, 69.49, 0),
    "TP1": (121.5, 63.0, 0), "TP2": (121.5, 70.0, 0),
})

# The translated variant (stage translated), placed but not routed: Lab 04's board with U1's
# two buffers, R2 and C1 replaced by two SN74LVC1T45s turned round (180 degrees), so that each
# has B (pin 4), DIR (5) and VCCB (6) down its left side, toward J4, and A (3), GND (2) and
# VCCA (1) down its right. U1 sits where Lab 04's U1 does, U2 below it, a capacitor beside
# each VCC pin, and J4 has a fourth pin for the dongle's VCC.
PLACE_T = dict({k: v for k, v in PLACE4.items() if k not in ("R2", "R4", "C1")}, **{
    "U1": (117.8625, 64.6, 180), "U2": (117.8625, 72.0, 180),
    "C1": (121.9, 66.0, 0), "C2": (117.0, 67.3, 0), "C3": (121.9, 74.6, 0), "C4": (117.0, 74.7, 0),
    "R4": (112.6, 76.4, 0),
})

SIG, PWR = 0.25, 0.4


def routes(lab, swapped=False):
    """[(layer, width, [points])]. Nets come from the pads the tracks start or end on."""
    r = []
    # +3V3: pins 12 joined along the top edge, each pin 6 to its pin 12.
    r.append(("F.Cu", PWR, [(102.0, 53.81), (102.0, 51.6), (124.86, 51.6), (147.72, 51.6), (147.72, 53.81)]))
    r.append(("F.Cu", PWR, [(124.86, 51.6), (124.86, 53.81)]))
    for x in PMOD_X:
        r.append(("F.Cu", PWR, [(x, 53.81), (x, PMOD_Y)]))
    # uio[7:4] from J2's upper row, through the gaps of its lower row, on the top layer.
    for x in (129.94, 132.48, 135.02, 137.56):
        r.append(("F.Cu", SIG, [(x, 53.81), (x - 1.27, 55.08), (x - 1.27, 62.5), (x - 1.27, 67.0)]))
    # uio[3:0] from J2's lower row, on the bottom layer, across to RN1 pins 6 to 9.
    for x, y in ((129.94, 60.4), (132.48, 59.6), (135.02, 58.8), (137.56, 58.0)):
        r.append(("B.Cu", SIG, [(x, PMOD_Y), (x, y), (x + 8.89, y), (x + 8.89, 62.5)]))
        r.append(("F.Cu", SIG, [(x + 8.89, 62.5), (x + 8.89, 67.0)]))
    sw_low = [(146.45 - 2.54 * k, 74.62) for k in range(7, -1, -1)]      # SW1 pins 9 .. 16
    if lab == "03" and swapped:
        # The header's pins 2 and 3 swapped in the schematic, and routed to match.
        r.append(("F.Cu", PWR, [(124.86, PMOD_Y), (124.86, 74.62)] + sw_low))
        r.append(("F.Cu", SIG, [(114.70, PMOD_Y), (114.70, 71.08), (110.0, 71.08)]))
        r.append(("F.Cu", SIG, [(160.42, PMOD_Y), (160.42, 79.0), (107.0, 79.0), (107.0, 68.54), (110.0, 68.54)]))
    elif lab == "03":
        r.append(("F.Cu", PWR, [(124.86, PMOD_Y), (124.86, 74.62)] + sw_low))
        r.append(("F.Cu", SIG, [(114.70, PMOD_Y), (114.70, 68.54), (110.0, 68.54)]))
        r.append(("F.Cu", SIG, [(160.42, PMOD_Y), (160.42, 79.0), (110.0, 79.0), (110.0, 71.08)]))
    else:
        r.append(("F.Cu", PWR, [(124.86, PMOD_Y), (124.86, 63.0), (124.86, 65.4)]))
        r.append(("F.Cu", PWR, [(124.86, 63.0), (121.5, 63.0)]))
        r.append(("F.Cu", PWR, [(124.86, 67.4), (124.86, 70.0), (124.86, 74.62)] + sw_low))
        r.append(("F.Cu", PWR, [(124.86, 70.0), (121.5, 70.0)]))
        # U1, C1 and R4 take their 3.3 V from +3V3_PMOD, after R3, so that the current spy
        # sees their current too: TP2 up to C1's pad 1, and C1's pad 1 to U1's VCC (pin 5)
        # past a via that takes +3V3_PMOD to R4. C1's other pad goes up to a via into the
        # bottom layer's ground.
        r.append(("F.Cu", PWR, [(121.5, 70.0), (121.5, 67.4), (120.8625, 66.7625), (120.8625, 66.0)]))
        r.append(("F.Cu", PWR, [(119.0, 64.6), (120.4, 64.6), (120.8625, 65.0625), (120.8625, 66.0)]))
        r.append(("F.Cu", PWR, [(122.9375, 66.0), (122.9375, 64.4)]))
        # ui[0]: J1 pin 1 to R1, R1 to U1's 1Y (pin 6) over the top of U1, and U1's 1A (pin 1)
        # out to D1 pin 1 and J4 pin 2, with R4's lower pad joining it.
        r.append(("F.Cu", SIG, [(114.70, PMOD_Y), (114.70, 60.5)]))
        r.append(("F.Cu", SIG, [(114.70, 62.5), (119.0, 62.5), (119.0, 63.65)]))
        r.append(("F.Cu", SIG, [(116.725, 63.65), (113.6, 63.65), (113.6, 67.9025), (112.9625, 68.54),
                                (110.0, 68.54)]))
        r.append(("F.Cu", SIG, [(112.4, 62.6), (112.4, 63.65), (113.6, 63.65)]))
        # R4's +3V3_PMOD is on the far side of the ui[0] line (J1 pin 1, R1, U1) from C1, so it
        # goes down the via beside U1's VCC pin, along the bottom layer under U1 and R1, and up
        # a via above R4. U1's GND (pin 2) goes to a via into the bottom layer's ground.
        r.append(("B.Cu", PWR, [(120.4, 64.6), (115.1, 59.3), (112.4, 59.3)]))
        r.append(("F.Cu", PWR, [(112.4, 59.3), (112.4, 60.6)]))
        r.append(("F.Cu", PWR, [(116.725, 64.6), (115.5, 64.6)]))
        # uo[0]: J3 pin 1 around the bottom of the board to U1's 2A (pin 3); 2Y (pin 4) down to
        # R2, then R2 to a via, and along the bottom layer under D1 to J4's pin 3, which is a
        # through-hole pad. That is the one place two lines cross: 2Y is beside VCC, and 2A
        # sits between 2Y and the pins whose lines go to J4.
        r.append(("F.Cu", SIG, [(160.42, PMOD_Y), (160.42, 79.0), (117.2, 79.0), (117.2, 66.0), (116.725, 65.55)]))
        r.append(("F.Cu", SIG, [(119.0, 65.55), (119.0, 67.6)]))
        r.append(("F.Cu", SIG, [(119.0, 69.6), (119.0, 71.08)]))
        r.append(("B.Cu", SIG, [(119.0, 71.08), (110.0, 71.08)]))
        r.append(("F.Cu", SIG, [(110.0, 71.08), (112.32, 71.08), (112.9625, 70.44)]))
        r.append(("F.Cu", SIG, [(114.8375, 69.49), (116.0, 69.49)]))
    return r


# Vias take the net of a track that ends on them (GND if none does). Lab 04's take GND down
# from D1, U1 and C1, DONGLE_RXD under D1 to J4, and +3V3_PMOD under U1 and R1 to R4.
VIAS = {"03": [], "04": [(116.0, 69.49), (115.5, 64.6), (122.9375, 64.4), (119.0, 71.08), (120.4, 64.6),
                         (112.4, 59.3)]}

# Reference designators moved off their library positions, as (x, y) or (x, y, angle): R4's
# and R2's onto the left of them and TP2's under it, where they would print over a
# neighbour's pads; C1's under it, off TP1; and R1's above it and level, where it would crowd
# U1's.
REF_AT = {"03": {}, "04t": {}, "04": {"R4": (110.6, 61.6), "R2": (117.3, 68.6), "TP2": (121.5, 71.75),
                           "C1": (122.2, 67.95), "R1": (114.7, 58.95, 0)}}

SILK = [
    ("INPUT", 108.35, 59.7), ("BIDIR", 131.21, 59.7), ("OUTPUT", 154.07, 59.7),
    ("GND", 106.6, 66.0), ("TXD", 106.6, 68.54), ("RXD", 106.6, 71.08),
    ("uio7", 128.67, 77.0), ("ON = 1", 137.56, 77.0), ("uio0", 146.45, 77.0),
    ("SimProc Pmod", 106.5, 80.6),
]


def mm(v):
    import pcbnew
    return pcbnew.FromMM(v)


def pt(x, y):
    import pcbnew
    return pcbnew.VECTOR2I(mm(x), mm(y))


def footprint_path(lib):
    if lib == "TinyTapeout_PMOD":
        return os.path.join(TEMPLATE, "lib", "TinyTapeout_PMOD.pretty")
    return os.path.join(FPDIR, lib + ".pretty")


def set_field(fp, name, value):
    """Give a footprint the symbol's field, as Update PCB from Schematic does."""
    import pcbnew
    f = None
    try:
        if fp.HasFieldByName(name):
            f = fp.GetFieldByName(name)
    except Exception:
        f = None
    if f is None:
        f = pcbnew.PCB_FIELD(fp, pcbnew.FIELD_T_USER, name)
        f.SetLayer(pcbnew.F_Fab)
        f.SetVisible(False)
        fp.Add(f)
    f.SetText(value)


def build_board(pcb_path, comps, pad_net, place, lab, route, zones, swapped=False):
    import pcbnew
    board = pcbnew.LoadBoard(pcb_path)
    nets = {}

    def net(name):
        if name not in nets:
            ni = board.FindNet(name)
            if ni is None:
                ni = pcbnew.NETINFO_ITEM(board, name)
                board.Add(ni)
            nets[name] = ni
        return nets[name]

    if place:
        x0, y0, x1, y1 = BOARD
        edge = pcbnew.PCB_SHAPE(board)
        edge.SetShape(pcbnew.SHAPE_T_RECT)
        edge.SetStart(pt(x0, y0))
        edge.SetEnd(pt(x1, y1))
        edge.SetLayer(pcbnew.Edge_Cuts)
        edge.SetWidth(mm(0.05))
        board.Add(edge)

    pads = {}
    for ref, (x, y, angle) in place.items():
        if ref not in comps:
            continue
        c = comps[ref]
        lib, name = c["footprint"].split(":")
        fp = pcbnew.FootprintLoad(footprint_path(lib), name)
        fp.SetFPID(pcbnew.LIB_ID(lib, name))
        fp.SetReference(ref)
        fp.SetValue(c["value"])
        for k, v in c["fields"].items():
            if k in ("Footprint", "Reference", "Value"):
                continue
            set_field(fp, k, v)
        fp.SetExcludedFromBOM(False)      # every symbol here is in the BOM, test points too
        fp.SetPath(pcbnew.KIID_PATH("/" + c["tstamp"]))
        fp.SetSheetname("/")
        fp.SetSheetfile(NAME + ".kicad_sch")
        board.Add(fp)
        fp.SetPosition(pt(x, y))
        fp.SetOrientationDegrees(angle)
        if ref in ("J1", "J2", "J3"):
            fp.SetLocked(True)
        if ref in REF_AT.get(lab, {}):
            at = REF_AT[lab][ref]
            fp.Reference().SetPosition(pt(at[0], at[1]))
            if len(at) > 2:
                fp.Reference().SetTextAngle(pcbnew.EDA_ANGLE(at[2], pcbnew.DEGREES_T))
        for p in fp.Pads():
            n = pad_net.get((ref, p.GetNumber()))
            if n:
                p.SetNet(net(n))
            pos = p.GetPosition()
            pads[(round(pcbnew.ToMM(pos.x), 3), round(pcbnew.ToMM(pos.y), 3))] = p

    def net_at(xy):
        p = pads.get((round(xy[0], 3), round(xy[1], 3)))
        return p.GetNet() if p is not None else None

    if route:
        for layer, width, points in routes(lab, swapped):
            ni = net_at(points[0]) or net_at(points[-1])
            if ni is None:
                for q in points:
                    ni = net_at(q)
                    if ni is not None:
                        break
            if ni is None:
                # A branch that starts on another track: take that track's net.
                for t in board.GetTracks():
                    for q in (t.GetStart(), t.GetEnd()):
                        if (round(pcbnew.ToMM(q.x), 3), round(pcbnew.ToMM(q.y), 3)) == \
                                (round(points[0][0], 3), round(points[0][1], 3)):
                            ni = t.GetNet()
            for a, b in zip(points, points[1:]):
                t = pcbnew.PCB_TRACK(board)
                t.SetStart(pt(*a))
                t.SetEnd(pt(*b))
                t.SetWidth(mm(width))
                t.SetLayer(pcbnew.F_Cu if layer == "F.Cu" else pcbnew.B_Cu)
                t.SetNet(ni)
                board.Add(t)
        for x, y in VIAS[lab]:
            v = pcbnew.PCB_VIA(board)
            v.SetPosition(pt(x, y))
            v.SetWidth(mm(0.6))
            v.SetDrill(mm(0.3))
            ni = net("GND")
            for t in board.GetTracks():
                if t.Type() == pcbnew.PCB_TRACE_T and any(
                        (round(pcbnew.ToMM(q.x), 3), round(pcbnew.ToMM(q.y), 3)) == (round(x, 3), round(y, 3))
                        for q in (t.GetStart(), t.GetEnd())):
                    ni = t.GetNet()
            v.SetNet(ni)
            board.Add(v)

    if zones:
        x0, y0, x1, y1 = BOARD
        for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
            z = pcbnew.ZONE(board)
            z.SetLayer(layer)
            z.SetNet(net("GND"))
            z.SetZoneName("GND")
            z.SetLocalClearance(mm(0.3))
            z.SetMinThickness(mm(0.25))
            z.SetThermalReliefGap(mm(0.5))
            z.SetThermalReliefSpokeWidth(mm(0.5))
            z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
            ol = z.Outline()
            ol.NewOutline()
            for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
                ol.Append(mm(x), mm(y))
            board.Add(z)
        # The filler drops every island that touches no pad of its net, and it can only tell
        # which pads those are once the board's connectivity has been built.
        board.BuildConnectivity()
        pcbnew.ZONE_FILLER(board).Fill(board.Zones())

    if route:
        for text, x, y in SILK:
            t = pcbnew.PCB_TEXT(board)
            t.SetText(text)
            t.SetPosition(pt(x, y))
            t.SetLayer(pcbnew.F_SilkS)
            t.SetTextSize(pcbnew.VECTOR2I(mm(1.0), mm(1.0)))
            t.SetTextThickness(mm(0.15))
            board.Add(t)

    tb = board.GetTitleBlock()
    tb.SetTitle("SimProc Pmod" if place else "Pmod for a Tiny Tapeout project")
    pcbnew.SaveBoard(pcb_path, board)


# --------------------------------------------------------------------------------------
# The template project

PRO = {
    "board": {
        "design_settings": {
            "defaults": {"silk_line_width": 0.15, "silk_text_size_h": 1.0, "silk_text_size_v": 1.0,
                         "silk_text_thickness": 0.15},
            "rules": {
                "min_clearance": 0.1, "min_connection": 0.1, "min_track_width": 0.1,
                "min_through_hole_diameter": 0.15, "min_via_diameter": 0.25, "min_via_annular_width": 0.05,
                "min_copper_edge_clearance": 0.5, "min_hole_clearance": 0.25, "min_hole_to_hole": 0.25,
                "min_text_height": 1.0, "min_text_thickness": 0.15, "min_silk_clearance": 0.0,
            },
            "track_widths": [0.0, 0.25, 0.4],
            "via_dimensions": [{"diameter": 0.0, "drill": 0.0}, {"diameter": 0.6, "drill": 0.3}],
        }
    },
    "net_settings": {
        "classes": [{"name": "Default", "clearance": 0.2, "track_width": 0.25, "via_diameter": 0.6,
                     "via_drill": 0.3, "microvia_diameter": 0.3, "microvia_drill": 0.1,
                     "diff_pair_gap": 0.25, "diff_pair_via_gap": 0.25, "diff_pair_width": 0.2,
                     "wire_width": 6, "bus_width": 12, "line_style": 0, "priority": 2147483647,
                     "pcb_color": "rgba(0, 0, 0, 0.000)", "schematic_color": "rgba(0, 0, 0, 0.000)"}],
        "meta": {"version": 4},
    },
    "meta": {"filename": NAME + ".kicad_pro", "version": 3},
}

DRU = """(version 1)
# JLCPCB's limit for the annular ring of a plated through hole on a 2-layer board with
# 1 oz copper: "absolute minimum 0.18 mm" (https://jlcpcb.com/capabilities/pcb-capabilities,
# read Nov 16, 2026). The limits Board Setup can hold itself (track width and clearance
# 0.10 mm, drill 0.15 mm, via 0.25 mm, silkscreen text 1.0 mm high and 0.15 mm thick) are
# in pmod.kicad_pro, under Board Setup > Design Rules > Constraints.

(rule "JLCPCB 2-layer PTH annular ring"
   (condition "A.Type == 'Pad' && A.Pad_Type == 'Through-hole'")
   (constraint annular_width (min 0.18mm)))
"""

EMPTY_PCB = """(kicad_pcb
\t(version 20260206)
\t(generator "pcbnew")
\t(generator_version "10.0")
\t(general
\t\t(thickness 1.6)
\t\t(legacy_teardrops no)
\t)
\t(paper "A4")
\t(layers
\t\t(0 "F.Cu" signal)
\t\t(2 "B.Cu" signal)
\t\t(9 "F.Adhes" user "F.Adhesive")
\t\t(11 "B.Adhes" user "B.Adhesive")
\t\t(13 "F.Paste" user)
\t\t(15 "B.Paste" user)
\t\t(5 "F.SilkS" user "F.Silkscreen")
\t\t(7 "B.SilkS" user "B.Silkscreen")
\t\t(1 "F.Mask" user)
\t\t(3 "B.Mask" user)
\t\t(17 "Dwgs.User" user "User.Drawings")
\t\t(19 "Cmts.User" user "User.Comments")
\t\t(21 "Eco1.User" user "User.Eco1")
\t\t(23 "Eco2.User" user "User.Eco2")
\t\t(25 "Edge.Cuts" user)
\t\t(27 "Margin" user)
\t\t(31 "F.CrtYd" user "F.Courtyard")
\t\t(29 "B.CrtYd" user "B.Courtyard")
\t\t(35 "F.Fab" user)
\t\t(33 "B.Fab" user)
\t)
\t(setup
\t\t(pad_to_mask_clearance 0)
\t\t(allow_soldermask_bridges_in_footprints no)
\t)
\t(net 0 "")
\t(embedded_fonts no)
)
"""


def write_template(out):
    """The empty project: rules, libraries, an empty schematic and an empty board."""
    os.makedirs(out, exist_ok=True)
    if os.path.abspath(out) != os.path.abspath(TEMPLATE):
        for f in ("fp-lib-table", "sym-lib-table"):
            shutil.copy(os.path.join(TEMPLATE, f), os.path.join(out, f))
        shutil.copytree(os.path.join(TEMPLATE, "lib"), os.path.join(out, "lib"), dirs_exist_ok=True)
    with open(os.path.join(out, NAME + ".kicad_pro"), "w") as f:
        json.dump(PRO, f, indent=2)
    with open(os.path.join(out, NAME + ".kicad_dru"), "w") as f:
        f.write(DRU)
    with open(os.path.join(out, NAME + ".kicad_pcb"), "w") as f:
        f.write(EMPTY_PCB)
    sheet = Sheet(out, "Pmod for a Tiny Tapeout project", "Your name")
    sheet.write(os.path.join(out, NAME + ".kicad_sch"))
    run(["kicad-cli", "sch", "upgrade", "--force", os.path.join(out, NAME + ".kicad_sch")])
    import pcbnew
    board = pcbnew.LoadBoard(os.path.join(out, NAME + ".kicad_pcb"))
    board.GetTitleBlock().SetTitle("Pmod for a Tiny Tapeout project")
    pcbnew.SaveBoard(os.path.join(out, NAME + ".kicad_pcb"), board)
    for f in (NAME + ".kicad_prl",):
        if os.path.exists(os.path.join(out, f)):
            os.remove(os.path.join(out, f))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("stage", choices=["template", "noflags", "schematic", "connectors", "placed", "routed",
                                      "swapped", "protected", "translated"])
    ap.add_argument("out", help="folder to write the project into; its KiCad files are replaced")
    args = ap.parse_args()
    out = args.out

    if args.stage == "template":
        write_template(out)
        print(f"wrote the template into {out}")
        return 0

    # Replace the KiCad files in OUT and leave anything else there (a BRINGUP.md, a README).
    if os.path.isdir(out):
        for f in os.listdir(out):
            path = os.path.join(out, f)
            if f.startswith(NAME + ".kicad_") or f.startswith(NAME + "-backups") or \
                    f in ("fp-lib-table", "sym-lib-table", "lib", "fp-info-cache"):
                shutil.rmtree(path) if os.path.isdir(path) else os.remove(path)
    work = tempfile.mkdtemp(prefix="pcb101-ref-")
    write_template(out)
    lab = "04" if args.stage in ("protected", "translated") else "03"
    title = "SimProc Pmod" + (", protected" if lab == "04" else "")
    sheet = Sheet(work, title, f"PCB101 Lab {lab} reference" + (", translators" if args.stage == "translated" else ""))
    schematic(sheet, lab, flags=args.stage != "noflags", swap=args.stage == "swapped",
              translated=args.stage == "translated")
    sch = os.path.join(out, NAME + ".kicad_sch")
    sheet.write(sch)
    run(["kicad-cli", "sch", "upgrade", "--force", sch])
    comps, pad_net = netlist(sch, work)
    place = PLACE4 if lab == "04" else PLACE3
    if args.stage == "translated":
        place, lab = PLACE_T, "04t"
    if args.stage in ("noflags", "schematic"):
        place = {}
    elif args.stage == "connectors":
        place = {k: v for k, v in place.items() if k in ("J1", "J2", "J3")}
    routed = args.stage in ("routed", "swapped", "protected")
    build_board(os.path.join(out, NAME + ".kicad_pcb"), comps, pad_net, place, lab, routed, routed,
                swapped=args.stage == "swapped")
    for f in (NAME + ".kicad_prl",):
        if os.path.exists(os.path.join(out, f)):
            os.remove(os.path.join(out, f))
    shutil.rmtree(work, ignore_errors=True)
    print(f"wrote stage {args.stage} into {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
