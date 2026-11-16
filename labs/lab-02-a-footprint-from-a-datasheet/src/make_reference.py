#!/usr/bin/env python3
"""Write Lab 02's reference solution from the course's arithmetic in land_pattern.py.

    python3 labs/lab-02-a-footprint-from-a-datasheet/src/make_reference.py

Writes, under labs/lab-02-a-footprint-from-a-datasheet/solutions/:
  pads.md                         the hand calculation, filled in
  pb101.pretty/RHL0024A.kicad_mod  the footprint
  pb101.kicad_sym                 the symbol SN74LVC8T245RHL

The files are text in KiCad 10's formats. Run them through `kicad-cli fp upgrade` and
`kicad-cli sym upgrade` afterwards (selftest.py shows how) so KiCad has written them once.
The output is the same on every run, because each uuid is derived from what it labels.
"""
import os
import uuid

from land_pattern import compute, drawing, COURTYARD

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.dirname(HERE)
OUT = os.path.join(LAB, "solutions")
NS = uuid.UUID("6f1f3c2e-9a51-4c4b-8f47-2f0a5b1d0c24")


def uid(*parts):
    return str(uuid.uuid5(NS, "/".join(str(p) for p in parts)))


def f(x):
    """A number the way KiCad writes it: no trailing zeros, no -0."""
    s = f"{x:.4f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def line(layer, x1, y1, x2, y2, width, tag):
    return (f'\t(fp_line\n\t\t(start {f(x1)} {f(y1)})\n\t\t(end {f(x2)} {f(y2)})\n'
            f'\t\t(stroke\n\t\t\t(width {f(width)})\n\t\t\t(type solid)\n\t\t)\n'
            f'\t\t(layer "{layer}")\n\t\t(uuid "{uid("line", tag)}")\n\t)\n')


def poly(layer, pts, width, fill, tag):
    xy = " ".join(f"(xy {f(x)} {f(y)})" for x, y in pts)
    return (f'\t(fp_poly\n\t\t(pts\n\t\t\t{xy}\n\t\t)\n\t\t(stroke\n\t\t\t(width {f(width)})\n'
            f'\t\t\t(type solid)\n\t\t)\n\t\t(fill {"yes" if fill else "no"})\n\t\t(layer "{layer}")\n'
            f'\t\t(uuid "{uid("poly", tag)}")\n\t)\n')


def text_prop(name, value, x, y, layer, hide=False, size=1.0, thickness=0.15):
    h = "\t\t(hide yes)\n" if hide else ""
    return (f'\t(property "{name}" "{value}"\n\t\t(at {f(x)} {f(y)} 0)\n\t\t(layer "{layer}")\n{h}'
            f'\t\t(uuid "{uid("prop", name)}")\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size {f(size)} {f(size)})\n'
            f'\t\t\t\t(thickness {f(thickness)})\n\t\t\t)\n\t\t)\n\t)\n')


def pad(num, x, y, w, h, layers, shape="roundrect", rratio=0.25, extra=""):
    rr = f"\t\t(roundrect_rratio {f(rratio)})\n" if shape == "roundrect" else ""
    lay = " ".join(f'"{l}"' for l in layers)
    return (f'\t(pad "{num}" smd {shape}\n\t\t(at {f(x)} {f(y)})\n\t\t(size {f(w)} {f(h)})\n'
            f'\t\t(layers {lay})\n{rr}{extra}\t\t(uuid "{uid("pad", num, x, y)}")\n\t)\n')


def pin_positions(c):
    """(number, x, y, horizontal) for pins 1-24, top view, pin 1 at top left (KLC F4.2).

    Pins 2-11 run down the left side and 14-23 up the right side, 0.5 mm apart over a
    4.5 mm span; 1 and 24 sit on the top short side and 12 and 13 on the bottom one,
    1.5 mm apart (drawing 4225250/C, and TI's land pattern on page 37)."""
    d = drawing()
    pitch, span, gap = d["pitch"], d["long_side_span"], d["short_side_spacing"]
    xl, ys = c["long"]["centre"], c["short"]["centre"]
    out = [("1", -gap / 2, -ys, False)]
    for i in range(10):
        out.append((str(2 + i), -xl, -span / 2 + i * pitch, True))
    out += [("12", -gap / 2, ys, False), ("13", gap / 2, ys, False)]
    for i in range(10):
        out.append((str(14 + i), xl, span / 2 - i * pitch, True))
    out.append(("24", gap / 2, -ys, False))
    return out


def footprint(c):
    d = drawing()
    bx = (d["body_x"]["min"] + d["body_x"]["max"]) / 2
    by = (d["body_y"]["min"] + d["body_y"]["max"]) / 2
    ep_x, ep_y = c["exposed_pad"]
    length, width = c["long"]["length"], c["long"]["X_r"]
    out_x = c["long"]["centre"] + length / 2
    out_y = c["short"]["centre"] + c["short"]["length"] / 2
    crt_x = round(max(out_x, bx / 2) + COURTYARD + 0.004, 2)
    crt_y = round(max(out_y, by / 2) + COURTYARD + 0.004, 2)

    s = ('(footprint "RHL0024A"\n\t(version 20260206)\n\t(generator "pcbnew")\n'
         '\t(generator_version "10.0")\n\t(layer "F.Cu")\n'
         '\t(descr "TI RHL0024A, VQFN-24, 3.5x5.5 mm body, 0.5 mm pitch, 2.05x4.05 mm exposed pad '
         '(SN74LVC8T245 datasheet SCES584D, https://www.ti.com/lit/ds/symlink/sn74lvc8t245.pdf, page 36). '
         'PB101 Lab 02 reference solution: IPC-7351B nominal goals, pads trimmed to 0.2 mm from the exposed pad.")\n'
         '\t(tags "VQFN RHL0024A")\n')
    s += text_prop("Reference", "REF**", 0, -crt_y - 1, "F.SilkS")
    s += text_prop("Value", "RHL0024A", 0, crt_y + 1, "F.Fab")
    s += text_prop("Datasheet", "https://www.ti.com/lit/ds/symlink/sn74lvc8t245.pdf", 0, 0, "F.Fab", hide=True, size=1.27)
    s += text_prop("Description", "TI RHL0024A VQFN-24, 0.5 mm pitch", 0, 0, "F.Fab", hide=True, size=1.27)
    s += '\t(attr smd)\n\t(duplicate_pad_numbers_are_jumpers no)\n'

    # F.Fab: the body, with its pin 1 corner cut at 45 degrees.
    hx, hy, ch = bx / 2, by / 2, 0.75
    s += poly("F.Fab", [(-hx + ch, -hy), (hx, -hy), (hx, hy), (-hx, hy), (-hx, -hy + ch)], 0.1, False, "fab")
    # F.SilkS: the four corners of the body, kept 0.2 mm clear of the copper, and a
    # triangle pointing at pin 1.
    sw = 0.12
    sx, sy = hx + 0.11, hy + 0.11
    clear = 0.2 + sw / 2
    long_y_end = d["long_side_span"] / 2 + width / 2 + clear      # past the last long-side pad
    short_x_end = d["short_side_spacing"] / 2 + width / 2 + clear  # past the short-side pads
    for mx in (-1, 1):
        for my in (-1, 1):
            if mx == -1 and my == -1:
                continue                     # pin 1 corner: the triangle marks it instead
            s += line("F.SilkS", mx * sx, my * sy, mx * short_x_end, my * sy, sw, f"silk-h{mx}{my}")
            s += line("F.SilkS", mx * sx, my * sy, mx * sx, my * long_y_end, sw, f"silk-v{mx}{my}")
    tx, ty = -sx, -sy - 0.1
    s += poly("F.SilkS", [(tx, ty), (tx - 0.3, ty - 0.24), (tx - 0.3, ty + 0.24)], sw, True, "pin1")
    # F.CrtYd: a rectangle 0.25 mm outside the pads and the body.
    for (x1, y1, x2, y2), tag in (((-crt_x, -crt_y, crt_x, -crt_y), "t"), ((crt_x, -crt_y, crt_x, crt_y), "r"),
                                  ((crt_x, crt_y, -crt_x, crt_y), "b"), ((-crt_x, crt_y, -crt_x, -crt_y), "l")):
        s += line("F.CrtYd", x1, y1, x2, y2, 0.05, "crt" + tag)
    s += ('\t(fp_text user "${REFERENCE}"\n\t\t(at 0 0 90)\n\t\t(layer "F.Fab")\n'
          f'\t\t(uuid "{uid("fabref")}")\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 0.8 0.8)\n'
          '\t\t\t\t(thickness 0.12)\n\t\t\t)\n\t\t)\n\t)\n')

    for num, x, y, horizontal in pin_positions(c):
        w, h = (length, width) if horizontal else (width, c["short"]["length"])
        s += pad(num, x, y, w, h, ["F.Cu", "F.Mask", "F.Paste"])
    # The exposed pad: copper and mask only. Its paste is printed through eight windows,
    # 2 across and 4 down, each 0.806 of its cell's width and height, so they cover 65 %
    # of the pad, the coverage KLC F6.3 recommends.
    s += pad("25", 0, 0, ep_x, ep_y, ["F.Cu", "F.Mask"], shape="rect", extra="\t\t(zone_connect 2)\n")
    k = 0.806
    cw, chh = ep_x / 2, ep_y / 4
    for i in range(2):
        for j in range(4):
            cx = -ep_x / 2 + cw * (i + 0.5)
            cy = -ep_y / 2 + chh * (j + 0.5)
            s += pad("", round(cx, 4), round(cy, 4), round(cw * k, 2), round(chh * k, 2), ["F.Paste"], rratio=0.25)
    s += "\t(embedded_fonts no)\n)\n"
    return s


def symbol():
    """SN74LVC8T245RHL: A side on the left, B side on the right, supplies on top, ground
    and the exposed pad underneath. Pins on the 2.54 mm grid (KLC S4.1), 2.54 mm long."""
    d = drawing()
    pins = d["pins"]
    g = 2.54
    left = [("1", 7), ("2", 5), ("22", 4)] + [(str(3 + i), 2 - i) for i in range(8)]   # VCCA, DIR, OE, A1-A8
    right = [("23", 7), ("24", 7)] + [(str(21 - i), 2 - i) for i in range(8)]          # VCCB (24 stacked), B1-B8
    bottom = [("11", -1), ("12", -1), ("13", -1), ("25", 1)]                           # GND (12, 13 stacked), EP
    body = (-5 * g, 9 * g, 5 * g, -7 * g)

    def pin(num, x, y, angle, hidden=False):
        p = pins[num]
        etype = p["type"]
        if hidden:
            etype = "passive"
        name = {"VCCA": "V_{CCA}", "VCCB": "V_{CCB}", "OE": "~{OE}"}.get(p["name"], p["name"])
        hide = "\t\t\t\t(hide yes)\n" if hidden else ""
        return (f'\t\t\t(pin {etype} line\n\t\t\t\t(at {f(x)} {f(y)} {angle})\n\t\t\t\t(length 2.54)\n{hide}'
                f'\t\t\t\t(name "{name}"\n\t\t\t\t\t(effects\n\t\t\t\t\t\t(font\n\t\t\t\t\t\t\t(size 1.27 1.27)\n'
                f'\t\t\t\t\t\t)\n\t\t\t\t\t)\n\t\t\t\t)\n\t\t\t\t(number "{num}"\n\t\t\t\t\t(effects\n'
                f'\t\t\t\t\t\t(font\n\t\t\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t\t\t)\n\t\t\t\t\t)\n\t\t\t\t)\n\t\t\t)\n')

    pins_s = ""
    for num, row in left:
        pins_s += pin(num, body[0] - g, row * g, 0)
    seen = set()
    for num, row in right:
        pins_s += pin(num, body[2] + g, row * g, 180, hidden=row in seen)
        seen.add(row)
    seen = set()
    for num, col in bottom:
        pins_s += pin(num, col * g, body[3] - g, 90, hidden=col in seen)
        seen.add(col)

    def sprop(name, value, x, y, hide=False):
        h = "\t\t\t(hide yes)\n" if hide else ""
        return (f'\t\t(property "{name}" "{value}"\n\t\t\t(at {f(x)} {f(y)} 0)\n{h}\t\t\t(effects\n'
                f'\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n')

    s = ('(kicad_symbol_lib\n\t(version 20251024)\n\t(generator "kicad_symbol_editor")\n'
         '\t(generator_version "10.0")\n\t(symbol "SN74LVC8T245RHL"\n'
         '\t\t(exclude_from_sim no)\n\t\t(in_bom yes)\n\t\t(on_board yes)\n')
    s += sprop("Reference", "U", body[0], body[1] + 1.27)
    s += sprop("Value", "SN74LVC8T245RHL", body[2] - 8, body[1] + 1.27)
    s += sprop("Footprint", "pb101:RHL0024A", 0, body[3] - 6, hide=True)
    s += sprop("Datasheet", "https://www.ti.com/lit/ds/symlink/sn74lvc8t245.pdf", 0, body[3] - 8, hide=True)
    s += sprop("Description", "8-bit dual-supply bus transceiver, VQFN-24 (RHL) with exposed pad", 0,
               body[3] - 10, hide=True)
    s += ('\t\t(symbol "SN74LVC8T245RHL_0_1"\n\t\t\t(rectangle\n'
          f'\t\t\t\t(start {f(body[0])} {f(body[1])})\n\t\t\t\t(end {f(body[2])} {f(body[3])})\n'
          '\t\t\t\t(stroke\n\t\t\t\t\t(width 0.254)\n\t\t\t\t\t(type default)\n\t\t\t\t)\n'
          '\t\t\t\t(fill\n\t\t\t\t\t(type background)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n')
    s += '\t\t(symbol "SN74LVC8T245RHL_1_1"\n' + pins_s + '\t\t)\n'
    s += '\t\t(embedded_fonts no)\n\t)\n)\n'
    return s


def pads_md(c):
    lo, sh = c["long"], c["short"]
    ep_x, ep_y = c["exposed_pad"]
    return f"""# Pads for TI's RHL0024A

<!-- Reference solution for Lab 02, written by src/make_reference.py. -->

Every length in mm. "Long sides" are pins 2 to 11 and 14 to 23, whose pads point along x;
"short sides" are pins 1, 12, 13 and 24, whose pads point along y.

| Quantity | Long sides | Short sides |
|---|---|---|
| Z | {lo['Z_r']:.2f} | {sh['Z_r']:.2f} |
| G | {lo['G_r']:.2f} | {sh['G_r']:.2f} |
| X | {lo['X_r']:.2f} | {sh['X_r']:.2f} |
| Pad length | {lo['length']:.2f} | {sh['length']:.2f} |
| Pad centre | {lo['centre']:.2f} | {sh['centre']:.2f} |

Exposed pad: {ep_x:.2f} x {ep_y:.2f}

At G, the inner end of each pad would be {lo['gap_at_G']:.2f} mm from the exposed pad, less
than the 0.2 mm KLC F6.3 asks for, so the inner ends move out to {lo['inner']:.3f} mm (long
sides) and {sh['inner']:.3f} mm (short sides) from the centre, and the pads get shorter.
"""


def main():
    c = compute()
    os.makedirs(os.path.join(OUT, "pb101.pretty"), exist_ok=True)
    with open(os.path.join(OUT, "pb101.pretty", "RHL0024A.kicad_mod"), "w") as fh:
        fh.write(footprint(c))
    with open(os.path.join(OUT, "pb101.kicad_sym"), "w") as fh:
        fh.write(symbol())
    with open(os.path.join(OUT, "pads.md"), "w") as fh:
        fh.write(pads_md(c))
    print(f"wrote {os.path.relpath(OUT)}/pads.md, pb101.pretty/RHL0024A.kicad_mod, pb101.kicad_sym")


if __name__ == "__main__":
    main()
