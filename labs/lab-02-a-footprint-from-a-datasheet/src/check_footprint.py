#!/usr/bin/env python3
"""Lab 02 check: your pads, footprint and symbol for TI's RHL0024A.

    labs/common/kicad.sh python3 labs/lab-02-a-footprint-from-a-datasheet/src/check_footprint.py
    labs/common/kicad.sh python3 labs/lab-02-a-footprint-from-a-datasheet/src/check_footprint.py DIR

DIR defaults to the lab folder and must hold pads.md, ic103.pretty/RHL0024A.kicad_mod and
ic103.kicad_sym with the symbol SN74LVC8T245RHL. The check has four parts:

1. pads.md: your Z, G, X, pad lengths and pad centres against the course's own arithmetic
   from the drawing (src/land_pattern.py), within 0.02 mm.
2. The footprint against your pads.md and the drawing: 24 pads and an exposed pad 25 at
   the drawing's positions, each pad the size you worked out (within 0.01 mm), at least
   0.2 mm from the exposed pad, paste over 50 to 80 % of the exposed pad, a courtyard
   0.25 mm clear of everything, a body outline on F.Fab and a pin 1 mark on F.SilkS. It
   also compares your pads with every footprint in KiCad's Package_DFN_QFN library and
   fails if they're the same as one of them.
3. The symbol against Table 4-1 of the datasheet: pins 1 to 25, their names and types,
   and the Footprint field ic103:RHL0024A. A KiCad 10 pin stack such as [11,12,13] counts
   as each of its numbers. A hidden power-input pin fails, because KiCad joins it to a
   global net named after it.
4. A one-part project with your symbol and footprint (written to results/fit/), through
   labs/common/check_board.py: no ERC errors, no DRC errors, no parity items.

Exit status: 0 PASS, 1 FAIL, 2 the check couldn't run.
"""
import argparse
import glob
import json
import math
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(LAB))
COMMON = os.path.join(ROOT, "labs", "common")
sys.path.insert(0, COMMON)
sys.path.insert(0, HERE)
from kicad_sexpr import load, children, child, prop  # noqa: E402
from land_pattern import compute, drawing, EP_CLEARANCE, COURTYARD  # noqa: E402
import fit_project  # noqa: E402

FP_NAME = "RHL0024A"
SYM_NAME = "SN74LVC8T245RHL"
KICAD_QFN = "/usr/share/kicad/footprints/Package_DFN_QFN.pretty"
POWER_LIB = "/usr/share/kicad/symbols/power.kicad_sym"
HAND_TOL = 0.02
FP_TOL = 0.011


def shown(path):
    rel = os.path.relpath(path)
    return os.path.abspath(path) if rel.startswith("..") else rel


# --- pads.md ------------------------------------------------------------------------------

def read_pads(path):
    """{'z': (long, short), ..., 'ep': (x, y)} from pads.md; None where it's TODO."""
    with open(path, encoding="utf-8") as f:
        text = re.sub(r"<!--.*?-->", "", f.read(), flags=re.S)
    out = {}
    for line in text.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")] if line.strip().startswith("|") else []
        if len(cells) >= 3:
            k = cells[0].lower()
            key = {"z": "z", "g": "g", "x": "x", "pad length": "length", "pad centre": "centre",
                   "pad center": "centre"}.get(k)
            if key:
                out[key] = tuple(num(c) for c in cells[1:3])
    m = re.search(r"exposed pad\s*:\s*([^\n]*)", text, re.I)
    if m:
        nums = re.findall(r"-?\d+(?:\.\d+)?", m.group(1))
        out["ep"] = (float(nums[0]), float(nums[1])) if len(nums) >= 2 else (None, None)
    return out


def num(cell):
    m = re.match(r"^\s*(-?\d+(?:\.\d+)?)\s*(mm)?\s*$", cell)
    return float(m.group(1)) if m else None


# --- the footprint ------------------------------------------------------------------------

class Pad:
    def __init__(self, node):
        self.num = node[1]
        self.shape = node[3] if len(node) > 3 else ""
        at = child(node, "at")
        self.x, self.y = float(at[1]), float(at[2])
        angle = float(at[3]) if len(at) > 3 else 0.0
        size = child(node, "size")
        w, h = float(size[1]), float(size[2])
        if round(angle) % 180 == 90:
            w, h = h, w
        self.w, self.h = w, h
        self.layers = set(child(node, "layers")[1:])
        pm = child(node, "solder_paste_margin")
        pr = child(node, "solder_paste_margin_ratio")
        self.paste_margin = float(pm[1]) if pm else 0.0
        self.paste_ratio = float(pr[1]) if pr else 0.0

    def box(self):
        return (self.x - self.w / 2, self.y - self.h / 2, self.x + self.w / 2, self.y + self.h / 2)

    def copper(self):
        return "F.Cu" in self.layers or "*.Cu" in self.layers

    def paste_box(self):
        """The paste opening: the pad grown on each side by solder_paste_margin plus
        solder_paste_margin_ratio times the pad's size along that axis. We checked the
        ratio's meaning by plotting F.Paste with kicad-cli 10.0.5: a 2.05 x 4.05 mm pad with
        a ratio of -0.1 plotted as a 1.64 x 3.24 mm opening, 64 % of the pad."""
        if "F.Paste" not in self.layers:
            return None
        mx = self.paste_margin + self.paste_ratio * self.w
        my = self.paste_margin + self.paste_ratio * self.h
        x0, y0, x1, y1 = self.box()
        if x1 - x0 + 2 * mx <= 0 or y1 - y0 + 2 * my <= 0:
            return None
        return (x0 - mx, y0 - my, x1 + mx, y1 + my)


def area(b):
    return max(0.0, b[2] - b[0]) * max(0.0, b[3] - b[1])


def gap(a, b):
    """The distance between two rectangles (0 if they touch or overlap)."""
    dx = max(0.0, max(a[0], b[0]) - min(a[2], b[2]))
    dy = max(0.0, max(a[1], b[1]) - min(a[3], b[3]))
    return math.hypot(dx, dy)


def shapes(fp, layer):
    """Bounding boxes of the graphics on one layer (lines, rectangles, polygons, circles, arcs)."""
    out = []
    for kind in ("fp_line", "fp_rect", "fp_poly", "fp_circle", "fp_arc"):
        for g in children(fp, kind):
            ly = child(g, "layer")
            if not ly or ly[1] != layer:
                continue
            pts = []
            for k in ("start", "end", "mid", "center"):
                c = child(g, k)
                if c:
                    pts.append((float(c[1]), float(c[2])))
            p = child(g, "pts")
            if p:
                pts += [(float(xy[1]), float(xy[2])) for xy in p if isinstance(xy, list) and xy[0] == "xy"]
            if kind == "fp_circle" and len(pts) == 2:
                (cx, cy), (ex, ey) = pts
                r = math.hypot(ex - cx, ey - cy)
                pts = [(cx - r, cy - r), (cx + r, cy + r)]
            if pts:
                xs, ys = [p[0] for p in pts], [p[1] for p in pts]
                out.append((min(xs), min(ys), max(xs), max(ys)))
    return out


def union(boxes):
    return (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes))


def signature(pads):
    """Pad numbers, positions and sizes, rounded, for comparing two footprints."""
    return sorted((p.num, round(p.x, 2), round(p.y, 2), round(p.w, 2), round(p.h, 2)) for p in pads if p.num)


def library_match(pads):
    """The KiCad library footprint with the same pads as these, if there is one, and how
    many footprints the library holds (0 when it isn't there to search)."""
    if not os.path.isdir(KICAD_QFN):
        return None, 0
    mine = signature(pads)
    count = len(mine)
    paths = sorted(glob.glob(os.path.join(KICAD_QFN, "*.kicad_mod")))
    for path in paths:
        with open(path, encoding="utf-8") as f:
            text = f.read()
        if text.count('(pad "') - text.count('(pad ""') != count:
            continue
        from kicad_sexpr import parse
        theirs = signature([Pad(p) for p in children(parse(text), "pad")])
        if theirs == mine:
            return os.path.basename(path)[:-len(".kicad_mod")], len(paths)
    return None, len(paths)


def expected_positions(centre_long, centre_short):
    d = drawing()
    pitch, span, sp = d["pitch"], d["long_side_span"], d["short_side_spacing"]
    out = {"1": (-sp / 2, -centre_short), "12": (-sp / 2, centre_short), "13": (sp / 2, centre_short),
           "24": (sp / 2, -centre_short)}
    for i in range(10):
        out[str(2 + i)] = (-centre_long, -span / 2 + i * pitch)
        out[str(14 + i)] = (centre_long, span / 2 - i * pitch)
    return out


def check_footprint(path, mine, rows):
    label = "Footprint"
    if not os.path.exists(path):
        rows.append((False, label, f"no {shown(path)} yet"))
        return None
    fp = load(path)
    pads = [Pad(p) for p in children(fp, "pad")]
    copper = [p for p in pads if p.copper() and p.num]
    msgs = []
    nums = sorted(set(p.num for p in copper), key=lambda s: (len(s), s))
    want = [str(i) for i in range(1, 26)]
    if nums != want:
        missing = [n for n in want if n not in nums]
        extra = [n for n in nums if n not in want]
        if missing:
            msgs.append(f"no pad numbered {', '.join(missing[:6])}{' ...' if len(missing) > 6 else ''}")
        if extra:
            msgs.append(f"pads numbered {', '.join(extra[:6])} don't belong to this package")
    by_num = {}
    for p in copper:
        by_num.setdefault(p.num, []).append(p)
    for n in want[:24]:
        if len(by_num.get(n, [])) > 1:
            msgs.append(f"pad {n} appears {len(by_num[n])} times")

    lo, sh = mine.get("length", (None, None)), mine.get("centre", (None, None))
    xw = mine.get("x", (None, None))
    if None in lo or None in sh or None in xw:
        msgs.append("pads.md needs your X, pad lengths and pad centres before the pads can be checked")
    elif not msgs:
        exp = expected_positions(sh[0], sh[1])
        off = []
        for n in want[:24]:
            p = by_num[n][0]
            ex, ey = exp[n]
            long_side = int(n) not in (1, 12, 13, 24)
            ew, eh = (lo[0], xw[0]) if long_side else (xw[1], lo[1])
            if abs(p.x - ex) > FP_TOL or abs(p.y - ey) > FP_TOL:
                off.append(f"pad {n} is at ({p.x:g}, {p.y:g}); your numbers put it at ({ex:g}, {ey:g})")
            elif abs(p.w - ew) > FP_TOL or abs(p.h - eh) > FP_TOL:
                off.append(f"pad {n} is {p.w:g} x {p.h:g}; your numbers make it {ew:g} x {eh:g}")
            if not {"F.Paste", "F.Mask"} <= p.layers:
                off.append(f"pad {n} isn't on F.Paste and F.Mask")
        msgs += off[:4] + ([f"... and {len(off) - 4} more pads"] if len(off) > 4 else [])

    ep = by_num.get("25", [])
    ep_box = union([p.box() for p in ep]) if ep else None
    if ep_box:
        d = drawing()
        ew, eh = ep_box[2] - ep_box[0], ep_box[3] - ep_box[1]
        if abs((ep_box[0] + ep_box[2]) / 2) > FP_TOL or abs((ep_box[1] + ep_box[3]) / 2) > FP_TOL:
            msgs.append("the exposed pad isn't centred on the footprint's origin")
        if mine.get("ep") and None not in mine["ep"]:
            if abs(ew - mine["ep"][0]) > FP_TOL or abs(eh - mine["ep"][1]) > FP_TOL:
                msgs.append(f"the exposed pad is {ew:g} x {eh:g}; your pads.md says {mine['ep'][0]:g} x {mine['ep'][1]:g}")
        for axis, size, spec in (("width", ew, d["exposed_pad_x"]), ("height", eh, d["exposed_pad_y"])):
            if size > spec["nom"] + spec["tol"] + 1e-6:
                msgs.append(f"the exposed pad's {axis}, {size:g}, is bigger than the package's largest, "
                            f"{spec['nom'] + spec['tol']:g}")
        worst = min(((gap(ep_box, p.box()), p.num) for p in copper if p.num != "25"), default=(9, ""))
        if worst[0] < EP_CLEARANCE - 0.005:
            msgs.append(f"pad {worst[1]} is {worst[0]:.3f} mm from the exposed pad; KLC F6.3 asks for 0.2")
        paste = [b for b in (p.paste_box() for p in pads if (not p.num or p.num == "25")) if b]
        cover = sum(area(b) for b in paste if gap(b, ep_box) == 0) / area(ep_box)
        if not 0.5 <= cover <= 0.8:
            msgs.append(f"paste covers {100 * cover:.0f} % of the exposed pad; KLC F6.3 asks for 50 to 80 %")
    else:
        cover = 0.0

    body = shapes(fp, "F.Fab")
    d = drawing()
    bx = (d["body_x"]["min"] + d["body_x"]["max"]) / 2
    by = (d["body_y"]["min"] + d["body_y"]["max"]) / 2
    if not body:
        msgs.append("nothing on F.Fab: draw the body outline")
    else:
        b = union(body)
        if abs((b[2] - b[0]) - bx) > 0.1 or abs((b[3] - b[1]) - by) > 0.1:
            msgs.append(f"the F.Fab outline is {b[2] - b[0]:.2f} x {b[3] - b[1]:.2f}; the body is {bx:g} x {by:g}")
    crt = shapes(fp, "F.CrtYd")
    if not crt:
        msgs.append("no courtyard on F.CrtYd")
    elif copper:
        c = union(crt)
        need = union([p.box() for p in copper] + [(-bx / 2, -by / 2, bx / 2, by / 2)])
        margin = min(need[0] - c[0], need[1] - c[1], c[2] - need[2], c[3] - need[3])
        if margin < COURTYARD - 0.005:
            msgs.append(f"the courtyard is {margin:.2f} mm outside the pads and body; KLC F5.3 asks for 0.25")
    silk = shapes(fp, "F.SilkS")
    if not silk:
        msgs.append("nothing on F.SilkS: mark pin 1")
    elif not any(s[0] < 0 and s[1] < -by / 4 for s in silk):
        msgs.append("no silkscreen near pin 1, at the top left")

    name, searched = library_match(pads)
    if name:
        msgs.append(f"these pads are the same as KiCad's {name}: draw your own")
    if msgs:
        for i, m in enumerate(msgs):
            rows.append((False, label if i == 0 else "", m))
    else:
        lib = f"and matches none of KiCad's {searched} QFN footprints" if searched else "(KiCad's library not searched)"
        rows.append((True, label, f"25 pads where your numbers put them, paste {100 * cover:.0f} %, {lib}"))
    return fp


# --- the symbol ---------------------------------------------------------------------------

TYPE_OK = {
    "power": {"power_in"},
    "ground": {"power_in", "passive"},
    "bidirectional": {"bidirectional", "tri_state"},
    "input": {"input"},
    "passive": {"passive", "power_in", "unspecified", "bidirectional", "input"},
}


def check_symbol(path, rows):
    label = "Symbol"
    if not os.path.exists(path):
        rows.append((False, label, f"no {shown(path)} yet"))
        return None
    with open(path, encoding="utf-8") as f:
        text = f.read()
    sym = fit_project.symbol_text(text, SYM_NAME)
    if sym is None:
        rows.append((False, label, f"no symbol called {SYM_NAME} in {shown(path)}"))
        return None
    pins = fit_project.pins_of(sym, SYM_NAME)
    table = drawing()["pins"]
    msgs = []
    by_num = {}
    hidden_power = []
    for unit, num, name, etype, x, y, hidden in pins:
        by_num.setdefault(num, []).append((name, etype))
        if hidden and etype == "power_in":
            hidden_power.append((num, fit_project.plain_name(name)))
    dup = [n for n, v in by_num.items() if len(v) > 1]
    if dup:
        msgs.append(f"pin number {', '.join(sorted(dup, key=int if all(d.isdigit() for d in dup) else str))} "
                    f"used more than once")
    missing = [n for n in table if n not in by_num]
    extra = [n for n in by_num if n not in table]
    if missing:
        msgs.append(f"no pin {', '.join(missing[:8])}{' ...' if len(missing) > 8 else ''}")
    if extra:
        msgs.append(f"pin {', '.join(extra[:8])} isn't on this package")
    groups = {}
    for n, spec in table.items():
        if n not in by_num:
            continue
        name, etype = by_num[n][0]
        plain = fit_project.plain_name(name).upper()
        if n != "25" and plain != spec["name"]:
            msgs.append(f"pin {n} is called '{name}'; Table 4-1 calls it {spec['name']}")
        kind = {"power_in": "power", "input": "input", "bidirectional": "bidirectional",
                "passive": "passive"}[spec["type"]]
        if spec["name"] == "GND":
            kind = "ground"
        if spec["name"] in ("VCCA", "VCCB", "GND"):
            groups.setdefault(spec["name"], []).append(etype)
            if etype not in ("power_in", "passive"):
                msgs.append(f"pin {n} ({spec['name']}) is {etype}; make it power_in, or passive if it's stacked")
        elif etype not in TYPE_OK[kind]:
            others = sorted(TYPE_OK[kind] - {spec["type"]})
            msgs.append(f"pin {n} ({spec['name']}) is {etype}; make it {spec['type']}"
                        + (f" (or {either(others)})" if others else ""))
    for g, types in groups.items():
        if "power_in" not in types:
            msgs.append(f"none of the {g} pins is power_in, so ERC won't know it's a supply")
    for n, nm in hidden_power:
        msgs.append(f"pin {n} ({nm}) is a hidden power input, which KiCad joins to a global net "
                    f"called {nm}; make it passive, or stack the pins in one pin numbered like [23,24]")
    fp_field = None
    for c in re.finditer(r'\(property\s+"Footprint"\s+"([^"]*)"', sym):
        fp_field = c.group(1)
        break
    if fp_field != f"ic103:{FP_NAME}":
        msgs.append(f"the Footprint field is '{fp_field or ''}'; set it to ic103:{FP_NAME}")
    if msgs:
        for i, m in enumerate(msgs):
            rows.append((False, label if i == 0 else "", m))
    else:
        rows.append((True, label, f"25 pins with Table 4-1's names and types, footprint ic103:{FP_NAME}"))
    vals = {}
    for c in re.finditer(r'\(property\s+"(Value|Datasheet|Description)"\s+"((?:[^"\\]|\\.)*)"', sym):
        vals.setdefault(c.group(1), c.group(2))
    return vals


def either(items):
    """'A', 'A or B', 'A, B or C'."""
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " or " + items[-1]


def both(items):
    """'A', 'A and B', 'A, B and C'."""
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " and " + items[-1]


# --- main ---------------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="Check your Lab 02 pads, footprint and symbol.")
    ap.add_argument("dir", nargs="?", default=LAB, help="folder with pads.md, ic103.pretty and ic103.kicad_sym")
    ap.add_argument("--out", help="where to write the fit project (default: results/fit in the lab)")
    args = ap.parse_args()
    d = os.path.abspath(args.dir)
    pads_md = os.path.join(d, "pads.md")
    fp_dir = os.path.join(d, "ic103.pretty")
    fp_path = os.path.join(fp_dir, FP_NAME + ".kicad_mod")
    sym_path = os.path.join(d, "ic103.kicad_sym")
    out = os.path.abspath(args.out or os.path.join(LAB, "results", "fit"))

    print("IC103 Lab 02 check")
    print(f"  folder    {shown(d)}")
    print()
    rows = []

    # 1. pads.md
    c = compute()
    mine = read_pads(pads_md) if os.path.exists(pads_md) else {}
    if not mine:
        rows.append((False, "pads.md", f"no {shown(pads_md)}, or no table in it"))
    else:
        msgs = []
        course = {"z": (c["long"]["Z"], c["short"]["Z"]), "g": (c["long"]["G"], c["short"]["G"]),
                  "x": (c["long"]["X"], c["short"]["X"]),
                  "length": (c["long"]["length"], c["short"]["length"]),
                  "centre": (c["long"]["centre"], c["short"]["centre"])}
        names = {"z": "Z", "g": "G", "x": "X", "length": "Pad length", "centre": "Pad centre"}
        for k in ("z", "g", "x", "length", "centre"):
            vals = mine.get(k)
            for i, side in enumerate(("long", "short")):
                v = vals[i] if vals else None
                if v is None:
                    msgs.append(f"{names[k]}, {side} sides: TODO")
                elif abs(v - course[k][i]) > HAND_TOL:
                    msgs.append(f"{names[k]}, {side} sides: {v:g} is more than {HAND_TOL} mm from the course's value")
        ep = mine.get("ep")
        if not ep or None in ep:
            msgs.append("Exposed pad: TODO")
        if msgs:
            for i, m in enumerate(msgs):
                rows.append((False, "pads.md" if i == 0 else "", m))
        else:
            rows.append((True, "pads.md", "Z, G, X, pad lengths and centres within 0.02 mm of the course's"))

    # 2. the footprint, 3. the symbol
    fp = check_footprint(fp_path, mine, rows)
    fields = check_symbol(sym_path, rows)

    # 4. the fit project
    if fp is None or fields is None:
        rows.append((False, "Fit", "needs both the footprint and the symbol"))
    elif not os.path.exists(POWER_LIB):
        rows.append((False, "Fit", "run this through labs/common/kicad.sh: it needs KiCad's libraries"))
    else:
        fields.setdefault("Value", SYM_NAME)
        try:
            fit_project.build(out, sym_path, SYM_NAME, fp_dir, FP_NAME, fields, POWER_LIB)
        except Exception as e:      # a symbol KiCad couldn't have written, say
            rows.append((False, "Fit", f"couldn't build the test project: {e}"))
        else:
            print(f"  running labs/common/check_board.py on {shown(out)}/fit.kicad_pro ...", flush=True)
            print()
            summary = os.path.join(out, "summary.json")
            r = subprocess.run([sys.executable, os.path.join(COMMON, "check_board.py"),
                                os.path.join(out, "fit.kicad_pro"), "--summary", summary,
                                "--reports", os.path.join(out, "reports")],
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            with open(os.path.join(out, "check_board.txt"), "w") as f:
                f.write(r.stdout)
            if r.returncode == 2 or not os.path.exists(summary):
                rows.append((False, "Fit", "KiCad couldn't load the test project; see " +
                             shown(os.path.join(out, "check_board.txt"))))
            else:
                with open(summary) as f:
                    s = json.load(f)
                if s["verdict"] == "PASS":
                    k = s["counts"]
                    rows.append((True, "Fit", f"ERC, DRC and parity clean on a board with your part "
                                 f"({k.get('erc.warning', 0)} ERC and {k.get('drc.warning', 0)} DRC warnings)"))
                else:
                    for i, f_ in enumerate(s["failures"]):
                        kinds = [f"{t.split('.', 2)[2]} {n}" for t, n in s["by_type"].items()
                                 if t.startswith(f_["key"] + ".")]
                        rows.append((False, "Fit" if i == 0 else "",
                                     f"{f_['key']} {f_['got']}" + (f" ({', '.join(kinds)})" if kinds else "")))
                    rows.append((False, "", f"details: {shown(os.path.join(out, 'check_board.txt'))}"))

    for ok, label, msg in rows:
        print(f"  {'ok' if ok else 'MISMATCH':9} {label:10} {msg}")
    bad = sum(1 for ok, label, _ in rows if not ok and label)
    print()
    if bad:
        failing = [label for ok, label, _ in rows if not ok and label]
        print(f"FAIL  {bad} of {sum(1 for _, label, _ in rows if label)} parts "
              f"{'has' if bad == 1 else 'have'} a MISMATCH: {both(failing)}")
        return 1
    print(f"PASS  {shown(d)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
