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
  protected   Lab 04's reference board: series resistors, ESD, a current-sense point

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
        for sub in children(node, "symbol"):
            m = re.match(re.escape(name) + r"_(\d+)_(\d+)$", sub[1])
            if m and m.group(2) not in ("0", "1"):
                continue
            for p in children(sub, "pin"):
                at = child(p, "at")
                num = child(p, "number")[1]
                self.pins[num] = (float(at[1]), float(at[2]), float(at[3]) if len(at) > 3 else 0.0)


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

    def place(self, ref, lib_id, x, y, angle=0, value=None, footprint=None, fields=None, hide_value=False):
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
        tag = ref
        out = [f'\t(symbol\n\t\t(lib_id "{lib_id}")\n\t\t(at {fmt(x)} {fmt(y)} {angle})\n\t\t(unit 1)\n'
               f'\t\t(exclude_from_sim no)\n\t\t(in_bom yes)\n\t\t(on_board yes)\n\t\t(dnp no)\n'
               f'\t\t(uuid "{uid("sym", tag)}")\n']
        power = ref.startswith("#")
        for i, (k, v) in enumerate(props.items()):
            if k.startswith("ki_"):
                continue
            hide = k not in ("Reference", "Value") or (k == "Reference" and power) or (k == "Value" and hide_value)
            # Reference above the part, value below, the rest hidden at the origin.
            if k == "Reference":
                px, py = (x, y - 3.81) if not power else (x, y)
            elif k == "Value":
                px, py = (x, y + 3.81) if not power else (x, y - 3.81 if angle in (0,) else y + 3.81)
            else:
                px, py = x, y
            v = v.replace("\\", "\\\\").replace('"', '\\"')
            out.append(f'\t\t(property "{k}" "{v}"\n\t\t\t(at {fmt(px)} {fmt(py)} 0)\n\t\t\t(effects\n'
                       f'\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n'
                       + ("\t\t\t\t(hide yes)\n" if hide else "") + "\t\t\t)\n\t\t)\n")
        for num in s.pins:
            out.append(f'\t\t(pin "{num}"\n\t\t\t(uuid "{uid("pin", tag, num)}")\n\t\t)\n')
        out.append(f'\t\t(instances\n\t\t\t(project "{NAME}"\n\t\t\t\t(path "/{self.root}"\n'
                   f'\t\t\t\t\t(reference "{ref}")\n\t\t\t\t\t(unit 1)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n\t)\n')
        self.instances.append("".join(out))
        for num, (px, py, pa) in s.pins.items():
            rx, ry = rot(px, py, angle)
            self.points[(ref, num)] = (round(x + rx, 4), round(y - ry, 4), int((pa + 180 + angle) % 360))
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
        """A power symbol (+3V3 or GND) at p, its graphic pointing `outward` (degrees, y up)."""
        self.npwr += 1
        default = 90 if net != "GND" else 270
        self.place(f"#PWR0{self.npwr:02d}", f"power:{net}", p[0], p[1], (outward - default) % 360)

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
                f'\t\t(date "2026-11-16")\n\t\t(rev "1")\n\t\t(company "UofT ASIC Team, PB101")\n'
                f'\t\t(comment 1 "{self.comment}")\n\t)\n\t(lib_symbols\n')
        libs = "".join("\t\t" + s.raw.replace("\n", "\n\t\t") + "\n" for s in self.syms.values())
        body = "".join(self.items) + "".join(self.instances)
        tail = '\t(sheet_instances\n\t\t(path "/"\n\t\t\t(page "1")\n\t\t)\n\t)\n\t(embedded_fonts no)\n)\n'
        with open(path, "w", encoding="utf-8") as f:
            f.write(head + libs + "\t)\n" + body + tail)


PMOD = "TinyTapeout_PMOD:PMOD_PERIPH_2x6"
PMOD_FP = "TinyTapeout_PMOD:PinHeader_2x06_P2.54mm_PMODPeriph2B"
R_FP = "Resistor_SMD:R_0805_2012Metric_Pad1.20x1.40mm_HandSolder"


def pmod_pins(io):
    """Pmod symbol pin number for IO1..IO8."""
    return str(io) if io <= 4 else str(io + 2)


def schematic(sheet, lab, flags=True, swap=False):
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
            footprint="Resistor_THT:R_Array_SIP9")
    for k in range(2, 10):
        s.attach("RN1", str(k), f"L:UIO{9 - k}")
    s.attach("RN1", "1", "P:GND")
    s.text("RN1: a pull-down on every uio line, so a switch\nthat is off reads 0 rather than floating.",
           (152.4, 152.4))

    # The header for the USB-UART dongle.
    s.place("J4", "Connector_Generic:Conn_01x03", 228.6, 50.8, 180, value="USB-UART",
            footprint="Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical")
    s.attach("J4", "1", "P:GND")
    s.attach("J4", "2", f"L:{rx_hdr}")
    s.attach("J4", "3", f"L:{tx_hdr}")
    s.text("J4: header for a 3.3 V USB-UART dongle.\nPin 2 goes to the dongle's TXD, pin 3 to its RXD.\n"
           "Leave the dongle's VCC unconnected.", (205.74, 60.96))

    if protect:
        s.place("R1", "Device:R", 215.9, 81.28, 90, value="1k", footprint=R_FP)
        s.attach("R1", "1", "L:UART_RX")
        s.attach("R1", "2", "L:DONGLE_TXD")
        s.place("R2", "Device:R", 215.9, 93.98, 90, value="1k", footprint=R_FP)
        s.attach("R2", "1", "L:UART_TX")
        s.attach("R2", "2", "L:DONGLE_RXD")
        s.text("R1, R2: series resistors. With the kit off and the dongle on,\n"
               "R1 limits the current into ui_in[0] to (3.3 - 0.6) V / 1k = 2.7 mA.", (198.12, 101.6))
        s.place("D1", "Power_Protection:SP0502BAHT", 266.7, 50.8, 0, value="SP0502BAHT")
        s.attach("D1", "1", "L:DONGLE_TXD")
        s.attach("D1", "2", "L:DONGLE_RXD")
        s.attach("D1", "3", "P:GND")
        s.text("D1: ESD protection on the pins a cable plugs into.", (248.92, 66.04))
        s.place("R3", "Device:R", 215.9, 152.4, 90, value="10", footprint=R_FP)
        s.attach("R3", "1", "P:+3V3")
        s.attach("R3", "2", "L:+3V3_PMOD")
        s.place("TP1", "Connector:TestPoint", 241.3, 157.48, 180, value="TP_3V3",
                footprint="TestPoint:TestPoint_Pad_D1.5mm")
        s.attach("TP1", "1", "P:+3V3")
        s.place("TP2", "Connector:TestPoint", 254.0, 147.32, 0, value="TP_3V3_PMOD",
                footprint="TestPoint:TestPoint_Pad_D1.5mm")
        s.attach("TP2", "1", "L:+3V3_PMOD")
        s.text("R3: a 10 ohm current spy in the Pmod's own supply.\n"
               "The voltage between TP1 and TP2 is 10 ohm x the current.", (198.12, 165.1))

    if flags:
        s.power("+3V3", (25.4, 177.8), 90)
        s.wire((25.4, 177.8), (25.4, 180.34))
        s.flag((25.4, 180.34), 180)
        s.power("GND", (38.1, 182.88), 270)
        s.wire((38.1, 180.34), (38.1, 182.88))
        s.flag((38.1, 180.34), 0)
        s.text("Power enters through the Pmod connectors,\nso PWR_FLAG tells ERC where it comes from.",
               (45.72, 177.8))


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
PLACE4 = dict(PLACE3, **{
    "R1": (114.70, 61.5, 270), "R2": (160.42, 61.5, 270), "R3": (124.86, 66.4, 270),
    "D1": (113.9, 69.49, 0),
    "TP1": (121.5, 63.0, 0), "TP2": (121.5, 70.0, 0),
})

SIG, PWR = 0.25, 0.4


def routes(lab):
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
    if lab == "03":
        r.append(("F.Cu", PWR, [(124.86, PMOD_Y), (124.86, 74.62)] + sw_low))
        r.append(("F.Cu", SIG, [(114.70, PMOD_Y), (114.70, 68.54), (110.0, 68.54)]))
        r.append(("F.Cu", SIG, [(160.42, PMOD_Y), (160.42, 79.0), (110.0, 79.0), (110.0, 71.08)]))
    else:
        r.append(("F.Cu", PWR, [(124.86, PMOD_Y), (124.86, 63.0), (124.86, 65.4)]))
        r.append(("F.Cu", PWR, [(124.86, 63.0), (121.5, 63.0)]))
        r.append(("F.Cu", PWR, [(124.86, 67.4), (124.86, 70.0), (124.86, 74.62)] + sw_low))
        r.append(("F.Cu", PWR, [(124.86, 70.0), (121.5, 70.0)]))
        r.append(("F.Cu", SIG, [(114.70, PMOD_Y), (114.70, 60.5)]))
        r.append(("F.Cu", SIG, [(114.70, 62.5), (114.70, 68.54), (112.9625, 68.54), (110.0, 68.54)]))
        r.append(("F.Cu", SIG, [(160.42, PMOD_Y), (160.42, 60.5)]))
        r.append(("F.Cu", SIG, [(160.42, 62.5), (160.42, 79.0), (110.0, 79.0), (110.0, 71.08)]))
        r.append(("F.Cu", SIG, [(110.0, 71.08), (112.32, 71.08), (112.9625, 70.44)]))
        r.append(("F.Cu", SIG, [(114.8375, 69.49), (116.0, 69.49)]))
    return r


VIAS = {"03": [], "04": [(116.0, 69.49)]}

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


def build_board(pcb_path, comps, pad_net, place, lab, route, zones):
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
        for layer, width, points in routes(lab):
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
            v.SetNet(net("GND"))
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

    if place:
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
                                      "swapped", "protected"])
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
    work = tempfile.mkdtemp(prefix="pb101-ref-")
    write_template(out)
    lab = "04" if args.stage == "protected" else "03"
    title = "SimProc Pmod" + (", protected" if lab == "04" else "")
    sheet = Sheet(work, title, f"PB101 Lab {lab} reference")
    schematic(sheet, lab, flags=args.stage != "noflags", swap=args.stage == "swapped")
    sch = os.path.join(out, NAME + ".kicad_sch")
    sheet.write(sch)
    run(["kicad-cli", "sch", "upgrade", "--force", sch])
    comps, pad_net = netlist(sch, work)
    place = PLACE4 if lab == "04" else PLACE3
    if args.stage in ("noflags", "schematic"):
        place = {}
    elif args.stage == "connectors":
        place = {k: v for k, v in place.items() if k in ("J1", "J2", "J3")}
    routed = args.stage in ("routed", "swapped", "protected")
    build_board(os.path.join(out, NAME + ".kicad_pcb"), comps, pad_net, place, lab, routed, routed)
    for f in (NAME + ".kicad_prl",):
        if os.path.exists(os.path.join(out, f)):
            os.remove(os.path.join(out, f))
    shutil.rmtree(work, ignore_errors=True)
    print(f"wrote stage {args.stage} into {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
