"""A small reader for KiCad's S-expression files (.kicad_pcb, .kicad_sch, .kicad_sym,
.kicad_mod), for the lab checkers.

The checkers read KiCad's files directly rather than importing KiCad's `pcbnew` Python
module, because KiCad plans to remove that module in KiCad 11 (course plan, K11), and a
checker that parses the files keeps working whatever happens to it.

    from kicad_sexpr import load, children, child, prop
    board = load("board.kicad_pcb")
    for fp in children(board, "footprint"):
        print(prop(fp, "Reference"), child(fp, "attr"))

A node is a Python list whose first item is its keyword, so `(at 1 2 90)` reads as
["at", "1", "2", "90"]. Atoms stay strings; use float() where you need a number.
"""
import re

_TOKEN = re.compile(r'\s*(?:(\()|(\))|"((?:[^"\\]|\\.)*)"|([^\s()"]+))', re.S)


def parse(text):
    """Parse one S-expression (the whole file) into nested lists of strings."""
    stack = [[]]
    pos = 0
    while True:
        m = _TOKEN.match(text, pos)
        if not m:
            break
        pos = m.end()
        if m.group(1):
            stack.append([])
        elif m.group(2):
            node = stack.pop()
            stack[-1].append(node)
        elif m.group(3) is not None:
            stack[-1].append(re.sub(r'\\(.)', r'\1', m.group(3)))
        else:
            stack[-1].append(m.group(4))
    if len(stack) != 1 or not stack[0]:
        raise ValueError("unbalanced parentheses or empty file")
    return stack[0][0]


def load(path):
    with open(path, encoding="utf-8") as f:
        return parse(f.read())


def children(node, name):
    """Every direct child node whose keyword is `name`."""
    return [c for c in node if isinstance(c, list) and c and c[0] == name]


def child(node, name):
    """The first direct child node whose keyword is `name`, or None."""
    for c in node:
        if isinstance(c, list) and c and c[0] == name:
            return c
    return None


def value(node, name, default=None):
    """The first atom of the child `name`: value(pad, "pinfunction") -> "VIN"."""
    c = child(node, name)
    return c[1] if c is not None and len(c) > 1 else default


def prop(node, name, default=None):
    """A footprint's or symbol's property: prop(fp, "Reference") -> "U1"."""
    for c in children(node, "property"):
        if len(c) > 2 and c[1] == name:
            return c[2]
    return default


def flags(node, name):
    """The atoms of a child such as (attr smd dnp), as a set."""
    c = child(node, name)
    return set(a for a in c[1:] if isinstance(a, str)) if c else set()


def xy(node, name="at"):
    """(x, y) and the angle of an (at x y [angle]) child, as floats."""
    c = child(node, name)
    if c is None:
        return None
    nums = [float(a) for a in c[1:] if isinstance(a, str) and re.match(r'^-?[0-9.]+$', a)]
    while len(nums) < 3:
        nums.append(0.0)
    return nums[0], nums[1], nums[2]


def net_name(pad):
    """The net of a pad. KiCad 9 writes (net 3 "VDDA"), KiCad 10 (net "VDDA")."""
    c = child(pad, "net")
    return c[-1] if c is not None and len(c) > 1 else ""
