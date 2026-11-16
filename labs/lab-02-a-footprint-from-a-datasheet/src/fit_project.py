"""Build a one-part KiCad project around a symbol and a footprint, for the board check.

The project has a schematic with one instance of the symbol, a net label on every pin
and a PWR_FLAG on every net that has a power-input or input pin (so that ERC sees each one
driven, as the rest of a real schematic would drive it), and a board with the footprint
placed and each pad given its pin's net, as "Update PCB from Schematic" would leave it.
labs/common/check_board.py then runs ERC, DRC and schematic parity on it, which shows
that KiCad loads both files, that every pin has a pad and every pad a pin, and that no
two pads on different nets are closer than the board's clearance.

The files are written as text, in the formats KiCad 9 and 10 read, rather than through
KiCad's Python module (see labs/common/kicad_sexpr.py for why).
"""
import json
import os
import re
import uuid

from kicad_sexpr import parse

NS = uuid.UUID("0c9b1f7e-55d2-4e0e-9a0c-4a1f2f6b7d31")
X0, Y0 = 101.6, 101.6          # where the symbol and the footprint go (on the 2.54 mm grid)


def uid(*parts):
    return str(uuid.uuid5(NS, "/".join(str(p) for p in parts)))


def blocks(text, start=0):
    """The raw text of each top-level child of the S-expression that starts at `start`,
    as (begin, end) offsets. Strings are skipped, so parentheses inside them don't count."""
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


def symbol_text(lib_text, name):
    """The raw `(symbol "name" ...)` block from a .kicad_sym file."""
    for b, e in blocks(lib_text):
        chunk = lib_text[b:e]
        if re.match(r'\(symbol\s+"' + re.escape(name) + r'"', chunk):
            return chunk
    return None


def plain_name(name):
    """V_{CCA} -> VCCA, ~{OE} -> OE: the text without KiCad's markup."""
    return re.sub(r"[~_^]\{([^}]*)\}", r"\1", name).strip()


def pin_numbers(number):
    """The pad numbers of one pin. KiCad 10 writes a pin stack as one pin whose number is
    a list or a range in brackets, "[11,12,13]" or "[11-13]", and gives its net to every
    pad in it (KLC S4.3). Any other number is a single pad."""
    m = re.match(r"^\[(.*)\]$", number.strip())
    if not m:
        return [number]
    out = []
    for part in m.group(1).split(","):
        part = part.strip()
        r = re.match(r"^([A-Za-z]*)(\d+)-\1(\d+)$", part)
        if r and int(r.group(2)) <= int(r.group(3)):
            out += [f"{r.group(1)}{i}" for i in range(int(r.group(2)), int(r.group(3)) + 1)]
        elif part:
            out.append(part)
    return out


def pins_of(sym_text, name, stacks=True):
    """[(unit, number, name, type, x, y, hidden)] for every pin of the symbol. Each number
    of a pin stack gets its own entry; stacks=False keeps the number as the file has it."""
    sym = parse(sym_text)
    out = []
    for sub in sym:
        if not (isinstance(sub, list) and sub and sub[0] == "symbol"):
            continue
        m = re.match(re.escape(name) + r"_(\d+)_(\d+)$", sub[1])
        unit, style = (int(m.group(1)), int(m.group(2))) if m else (1, 1)
        if style not in (0, 1):
            continue
        for p in sub:
            if isinstance(p, list) and p and p[0] == "pin":
                at = next(c for c in p if isinstance(c, list) and c[0] == "at")
                nm = next((c[1] for c in p if isinstance(c, list) and c[0] == "name"), "")
                num = next((c[1] for c in p if isinstance(c, list) and c[0] == "number"), "")
                hidden = "hide" in p or ["hide", "yes"] in p
                for n in (pin_numbers(num) if stacks else [num]):
                    out.append((unit, n, nm, p[1], float(at[1]), float(at[2]), hidden))
    return out


def label(net, x, y, tag):
    return (f'\t(label "{net}"\n\t\t(at {x:g} {y:g} 0)\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.27 1.27)\n'
            f'\t\t\t)\n\t\t\t(justify left bottom)\n\t\t)\n\t\t(uuid "{uid("label", tag)}")\n\t)\n')


def prop_s(name, value, x, y, hide=False):
    h = "\t\t\t\t(hide yes)\n" if hide else ""
    return (f'\t\t(property "{name}" "{value}"\n\t\t\t(at {x:g} {y:g} 0)\n\t\t\t(effects\n\t\t\t\t(font\n'
            f'\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n{h}\t\t\t)\n\t\t)\n')


def build(out_dir, sym_lib, sym_name, fp_lib_dir, fp_name, fields, power_sym_lib):
    """Write fit.kicad_pro/.kicad_sch/.kicad_pcb, the library tables and check-expect.json
    into out_dir. Returns a dict of pad number -> net name."""
    os.makedirs(out_dir, exist_ok=True)
    root = uid("root")
    sym_uuid = uid("U1")

    with open(sym_lib, encoding="utf-8") as f:
        sym_lib_text = f.read()
    student = symbol_text(sym_lib_text, sym_name)
    with open(power_sym_lib, encoding="utf-8") as f:
        flag = symbol_text(f.read(), "PWR_FLAG")
    if student is None or flag is None:
        raise ValueError("symbol not found")
    cached = student.replace(f'(symbol "{sym_name}"', f'(symbol "pb101:{sym_name}"', 1)
    flag = flag.replace('(symbol "PWR_FLAG"', '(symbol "power:PWR_FLAG"', 1)

    pins = pins_of(student, sym_name)
    units = sorted(set(u for u, *_ in pins if u != 0)) or [1]
    nets, pad_net, points, power_nets = {}, {}, {}, set()
    for unit, num, name, etype, x, y, _hidden in pins:
        net = plain_name(name)
        if not net or net == "~":
            net = f"P{num}"
        targets = units if unit == 0 else [unit]
        for u in targets:
            ux = X0 + (u - 1) * 50.8
            pt = (round(ux + x, 4), round(Y0 - y, 4))       # symbol y is up, schematic y is down
            if pt in points and points[pt] != net:
                net = points[pt]                       # stacked pins share one net
            points[pt] = net
        pad_net[num] = net
        if etype in ("power_in", "input"):
            power_nets.add(net)

    sch = (f'(kicad_sch\n\t(version 20250114)\n\t(generator "pb101_lab02_fit")\n\t(generator_version "10.0")\n'
           f'\t(uuid "{root}")\n\t(paper "A4")\n\t(lib_symbols\n'
           + "\t\t" + cached.replace("\n", "\n\t") + "\n"
           + "\t\t" + flag.replace("\n", "\n\t") + "\n\t)\n")
    for i, (pt, net) in enumerate(sorted(points.items())):
        sch += label(net, pt[0], pt[1], f"pin{i}")
    for u in units:
        ux = X0 + (u - 1) * 50.8
        sch += (f'\t(symbol\n\t\t(lib_id "pb101:{sym_name}")\n\t\t(at {ux:g} {Y0:g} 0)\n\t\t(unit {u})\n'
                f'\t\t(exclude_from_sim no)\n\t\t(in_bom yes)\n\t\t(on_board yes)\n\t\t(dnp no)\n'
                f'\t\t(uuid "{sym_uuid if u == units[0] else uid("U1", u)}")\n')
        sch += prop_s("Reference", "U1", ux, Y0 - 30)
        sch += prop_s("Value", fields["Value"], ux, Y0 + 30)
        sch += prop_s("Footprint", f"pb101:{fp_name}", ux, Y0 + 32, hide=True)
        sch += prop_s("Datasheet", fields.get("Datasheet", ""), ux, Y0 + 34, hide=True)
        sch += prop_s("Description", fields.get("Description", ""), ux, Y0 + 36, hide=True)
        for unit, num, *_ in pins_of(student, sym_name, stacks=False):
            if unit in (0, u):
                sch += f'\t\t(pin "{num}"\n\t\t\t(uuid "{uid("pin", u, num)}")\n\t\t)\n'
        sch += (f'\t\t(instances\n\t\t\t(project "fit"\n\t\t\t\t(path "/{root}"\n\t\t\t\t\t(reference "U1")\n'
                f'\t\t\t\t\t(unit {u})\n\t\t\t\t)\n\t\t\t)\n\t\t)\n\t)\n')
    for i, net in enumerate(sorted(power_nets)):
        fx, fy = 30.48 + 12.7 * i, 30.48
        sch += label(net, fx, fy, f"flag{i}")
        sch += (f'\t(symbol\n\t\t(lib_id "power:PWR_FLAG")\n\t\t(at {fx:g} {fy:g} 0)\n\t\t(unit 1)\n'
                f'\t\t(exclude_from_sim no)\n\t\t(in_bom yes)\n\t\t(on_board yes)\n\t\t(dnp no)\n'
                f'\t\t(uuid "{uid("flag", net)}")\n')
        sch += prop_s("Reference", f"#FLG0{i + 1}", fx, fy - 2, hide=True)
        sch += prop_s("Value", "PWR_FLAG", fx, fy - 4)
        sch += prop_s("Footprint", "", fx, fy, hide=True)
        sch += prop_s("Datasheet", "~", fx, fy, hide=True)
        sch += prop_s("Description", "", fx, fy, hide=True)
        sch += f'\t\t(pin "1"\n\t\t\t(uuid "{uid("flagpin", net)}")\n\t\t)\n'
        sch += (f'\t\t(instances\n\t\t\t(project "fit"\n\t\t\t\t(path "/{root}"\n\t\t\t\t\t(reference "#FLG0{i + 1}")\n'
                f'\t\t\t\t\t(unit 1)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n\t)\n')
    sch += '\t(sheet_instances\n\t\t(path "/"\n\t\t\t(page "1")\n\t\t)\n\t)\n\t(embedded_fonts no)\n)\n'
    with open(os.path.join(out_dir, "fit.kicad_sch"), "w", encoding="utf-8") as f:
        f.write(sch)

    # The board: the footprint as it would be after Update PCB from Schematic.
    with open(os.path.join(fp_lib_dir, fp_name + ".kicad_mod"), encoding="utf-8") as f:
        fp = f.read()
    parts = []
    for b, e in blocks(fp):
        chunk = fp[b:e]
        head = re.match(r'\((\w+)', chunk).group(1)
        if head in ("version", "generator", "generator_version"):
            continue
        if head == "property":
            m = re.match(r'\(property\s+"([^"]*)"\s+"((?:[^"\\]|\\.)*)"', chunk)
            if m and m.group(1) in ("Reference", "Value", "Datasheet", "Description"):
                new = {"Reference": "U1"}.get(m.group(1), fields.get(m.group(1), ""))
                chunk = chunk[:m.start(2)] + new.replace('"', '\\"') + chunk[m.end(2):]
        if head == "pad":
            m = re.match(r'\(pad\s+"([^"]*)"', chunk)
            num = m.group(1) if m else ""
            if num and num in pad_net:
                chunk = chunk[:-1].rstrip() + f'\n\t\t(net "/{pad_net[num]}")\n\t)'
        parts.append(chunk)
        if head == "layer":
            parts.append(f'(uuid "{uid("fp")}")')
            parts.append(f"(at {X0:g} {Y0:g})")
            parts.append(f'(path "/{sym_uuid}")')
            parts.append('(sheetname "/")')
            parts.append('(sheetfile "fit.kicad_sch")')
    footprint = f'\t(footprint "pb101:{fp_name}"\n\t\t' + "\n\t\t".join(p.replace("\n", "\n\t") for p in parts) + "\n\t)\n"
    layers = ('\t(layers\n\t\t(0 "F.Cu" signal)\n\t\t(2 "B.Cu" signal)\n\t\t(9 "F.Adhes" user "F.Adhesive")\n'
              '\t\t(11 "B.Adhes" user "B.Adhesive")\n\t\t(13 "F.Paste" user)\n\t\t(15 "B.Paste" user)\n'
              '\t\t(5 "F.SilkS" user "F.Silkscreen")\n\t\t(7 "B.SilkS" user "B.Silkscreen")\n'
              '\t\t(1 "F.Mask" user)\n\t\t(3 "B.Mask" user)\n\t\t(17 "Dwgs.User" user "User.Drawings")\n'
              '\t\t(19 "Cmts.User" user "User.Comments")\n\t\t(21 "Eco1.User" user "User.Eco1")\n'
              '\t\t(23 "Eco2.User" user "User.Eco2")\n\t\t(25 "Edge.Cuts" user)\n\t\t(27 "Margin" user)\n'
              '\t\t(31 "F.CrtYd" user "F.Courtyard")\n\t\t(29 "B.CrtYd" user "B.Courtyard")\n'
              '\t\t(35 "F.Fab" user)\n\t\t(33 "B.Fab" user)\n\t)\n')
    pcb = ('(kicad_pcb\n\t(version 20260206)\n\t(generator "pb101_lab02_fit")\n\t(generator_version "10.0")\n'
           '\t(general\n\t\t(thickness 1.6)\n\t\t(legacy_teardrops no)\n\t)\n\t(paper "A4")\n' + layers +
           '\t(setup\n\t\t(pad_to_mask_clearance 0)\n\t\t(allow_soldermask_bridges_in_footprints no)\n\t)\n'
           + footprint +
           f'\t(gr_rect\n\t\t(start {X0 - 10:g} {Y0 - 10:g})\n\t\t(end {X0 + 10:g} {Y0 + 10:g})\n'
           '\t\t(stroke\n\t\t\t(width 0.05)\n\t\t\t(type default)\n\t\t)\n\t\t(fill no)\n'
           f'\t\t(layer "Edge.Cuts")\n\t\t(uuid "{uid("edge")}")\n\t)\n\t(embedded_fonts no)\n)\n')
    with open(os.path.join(out_dir, "fit.kicad_pcb"), "w", encoding="utf-8") as f:
        f.write(pcb)

    with open(os.path.join(out_dir, "fit.kicad_pro"), "w") as f:
        json.dump({"meta": {"filename": "fit.kicad_pro", "version": 3}}, f, indent=2)
    rel_fp = os.path.relpath(fp_lib_dir, out_dir)
    rel_sym = os.path.relpath(sym_lib, out_dir)
    with open(os.path.join(out_dir, "fp-lib-table"), "w") as f:
        f.write(f'(fp_lib_table\n\t(version 7)\n\t(lib (name "pb101")(type "KiCad")'
                f'(uri "${{KIPRJMOD}}/{rel_fp}")(options "")(descr "Lab 02"))\n)\n')
    with open(os.path.join(out_dir, "sym-lib-table"), "w") as f:
        f.write(f'(sym_lib_table\n\t(version 7)\n\t(lib (name "pb101")(type "KiCad")'
                f'(uri "${{KIPRJMOD}}/{rel_sym}")(options "")(descr "Lab 02"))\n)\n')
    # Unconnected items aren't counted: the pads that share a net (GND, VCCB) have no
    # tracks between them on a board with one part on it, and that's expected.
    with open(os.path.join(out_dir, "check-expect.json"), "w") as f:
        json.dump({"comment": "Lab 02 fit test: one part, no tracks, so unconnected items aren't checked.",
                   "erc.error": 0, "drc.error": 0, "parity.error": 0, "parity.warning": 0}, f, indent=2)
        f.write("\n")
    return pad_net
