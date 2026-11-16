"""A small reader for KiCad's S-expression files (.kicad_pcb, .kicad_mod), for figure scripts.

    from kicad_sexpr import parse, find, get, prop, pad_position

parse() turns the file's text into nested lists of strings, with quotes removed. It
reads boards saved by KiCad 9 (nets as numbers with a table at the top) and by KiCad
10 (nets by name), and footprint files. It's enough for drawing figures from real
boards; the course's checks use kicad-cli instead.
"""
import math
import re

_TOKEN = re.compile(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()]+')


def parse(text):
    """Nested lists of strings; the first element of each list is its keyword."""
    stack = [[]]
    for m in _TOKEN.finditer(text):
        t = m.group(0)
        if t == "(":
            stack.append([])
        elif t == ")":
            node = stack.pop()
            stack[-1].append(node)
        else:
            stack[-1].append(t[1:-1] if t.startswith('"') else t)
    return stack[0][0]


def find(node, key):
    """The direct children of node whose keyword is key."""
    return [c for c in node if isinstance(c, list) and c and c[0] == key]


def get(node, key):
    """The first direct child with keyword key, or None."""
    found = find(node, key)
    return found[0] if found else None


def prop(footprint, name):
    """A footprint's property value, such as 'Reference' or 'Value'."""
    for p in find(footprint, "property"):
        if p[1] == name:
            return p[2]
    return None


def net_names(board):
    """Map from what a pad's (net ...) holds to the net's name, for KiCad 9 and 10 boards."""
    table = {n[1]: n[2] for n in find(board, "net") if len(n) > 2}
    return lambda net: table.get(net[1], net[1]) if net and len(net) > 1 else None


def pad_position(footprint, pad):
    """(x, y) of a pad on the board, in mm, from the footprint's position and rotation."""
    at = get(footprint, "at")
    x, y = float(at[1]), float(at[2])
    theta = math.radians(float(at[3])) if len(at) > 3 else 0.0
    px, py = float(get(pad, "at")[1]), float(get(pad, "at")[2])
    # KiCad's y axis points down and its angles turn counterclockwise on screen.
    return (x + px * math.cos(theta) + py * math.sin(theta),
            y - px * math.sin(theta) + py * math.cos(theta))
