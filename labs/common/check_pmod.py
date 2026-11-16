#!/usr/bin/env python3
"""IC103 Pmod check: the board check, then where the Pmod connectors are and whether the
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
   as the connector other than the Pmods whose pin 1 is on GND), on the same net or through
   one series resistor. "switch" asks for a switch from the pin's line to the 3.3 V supply,
   and "pull": "down" for a resistor from the line to GND. A resistor counts if it's a
   two-pin part with a reference starting R, or one element of a bussed network
   (R_Network*) or an isolated array (R_Pack*).

With --protect (Lab 04), three more:

5. Every "crossing" pin reaches its part through exactly one series resistor. The check
   prints the current that resistor allows into a pin of an unpowered chip from a 3.3 V
   driver, (3.3 V - 0.6 V) / R, and fails above 20 mA, Horowitz and Hill's example of an
   input clamp current (The Art of Electronics, 3rd ed., p. 759).
6. Every pin of an external part other than GND has an ESD part on its net: a part with a
   reference starting D, or from KiCad's Power_Protection library, with another pin on GND.
7. A current-sense point: a two-pin resistor from the Pmod's 3.3 V net to a net of the
   board's own that feeds something, with a test point (reference TP...) on each side.

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
        tmp = tempfile.mkdtemp(prefix="ic103-pmod-")
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
            }
        self.nets = {}
        for n in children(child(root, "nets"), "net"):
            name = child(n, "name")[1]
            nodes = [(child(nd, "ref")[1], child(nd, "pin")[1]) for nd in children(n, "node")]
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
            tnet = nl.net(hdr, tpin)
            other = [p for p in tgt["pins"] if p not in (tpin, "1")]
            if tnet == n0 and not (protect and rule.get("crossing")):
                rep.add(True, name, f"{here} reaches {hdr} pin {tpin} ({what}) directly")
            elif tnet in near:
                r, val = near[tnet]
                msg = f"{here} reaches {hdr} pin {tpin} ({what}) through {r} ({val})"
                if protect and rule.get("crossing"):
                    ohms = parse_value(val)
                    if ohms is None or ohms <= 0:
                        rep.add(False, name, msg + f"\nits value {val!r} isn't a resistance the check can read")
                        continue
                    i = 2.7 / ohms
                    rise = 2.2 * ohms * 10e-12
                    ok = i <= 0.020
                    msg += (f"\ninto an unpowered chip: (3.3 V - 0.6 V) / {fmt_ohms(ohms)} = {fmt_amps(i)}"
                            f"{'' if ok else ', more than 20 mA'}; edge with 10 pF: 2.2RC = {fmt_secs(rise)}")
                    rep.add(ok, name, msg)
                else:
                    rep.add(True, name, msg)
            elif tnet == n0:
                rep.add(False, name, f"{here} reaches {hdr} pin {tpin} ({what}) directly, with no series "
                                     "resistor; this line crosses from another supply")
            else:
                swapped = [p for p in other if nl.net(hdr, p) in ({n0} | set(near))]
                if swapped:
                    p = swapped[0]
                    rep.add(False, name, f"{here} reaches {hdr} pin {p} ({tgt['pins'][p]}), not pin {tpin} "
                                         f"({what}): are TX and RX swapped?")
                else:
                    rep.add(False, name, f"{here} doesn't reach {hdr} pin {tpin} ({what})")
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
        spy = None
        for r, a, b, val in res:
            for x, y in ((a, b), (b, a)):
                if vcc and nl.net(r, x) == vcc:
                    yn = nl.net(r, y)
                    if yn and yn not in ("GND", vcc) and len(nl.nets.get(yn, [])) > 1:
                        spy = (r, val, yn)
        if spy is None:
            rep.add(False, "sense", f"no current-sense resistor between {vcc} and a net of the board's own")
        else:
            r, val, yn = spy
            tps = {n: [rr for rr, pp in nl.parts.items() if rr.startswith("TP") and n in pp["pins"].values()]
                   for n in (vcc, yn)}
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
    return f"{r / 1e3:g} kΩ" if r >= 1e3 else f"{r:g} Ω"


def fmt_amps(i):
    return f"{i * 1e3:.2g} mA" if i >= 1e-3 else f"{i * 1e6:.2g} µA"


def fmt_secs(t):
    return f"{t * 1e9:.3g} ns" if t < 1e-6 else f"{t * 1e6:.3g} µs"


def main():
    ap = argparse.ArgumentParser(description="The board check, then the Pmod connectors and the pin list.")
    ap.add_argument("project", help=".kicad_pro, or a folder with one")
    ap.add_argument("--pins", default=DEFAULT_PINS, help="the project's pin list (default: SimProc's)")
    ap.add_argument("--protect", action="store_true", help="Lab 04: series resistors, ESD and a current-sense point")
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

    print("IC103 Pmod check")
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
