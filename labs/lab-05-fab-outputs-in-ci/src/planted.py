#!/usr/bin/env python3
"""The error we plant in Lab 05, Part 5, on Lab 04's reference board.

    python3 labs/lab-05-fab-outputs-in-ci/src/planted.py BOARD.kicad_pcb

It does to the board file what dragging a track does in the PCB Editor: the 0.4 mm +3V3
track that runs along the top edge from J1 to J2, at y = 51.6 mm, moves 1 mm down to
y = 52.6 mm, and the two tracks it meets stretch to follow it. Its lower edge is then
0.16 mm from the upper row of J1's pads, less than the 0.2 mm clearance, so DRC reports a
clearance error for each of those pads that isn't on +3V3. Nothing is disconnected.
"""
import sys

EDITS = [
    # The run along the top edge, J1 to J2.
    ("\t\t(start 102 51.6)\n\t\t(end 124.86 51.6)\n",
     "\t\t(start 102 52.6)\n\t\t(end 124.86 52.6)\n"),
    # J1's stub up to it gets shorter.
    ("\t\t(start 102 53.81)\n\t\t(end 102 51.6)\n",
     "\t\t(start 102 53.81)\n\t\t(end 102 52.6)\n"),
    # J2's stub is split where the moved run now meets it, so the run on to J3 stays connected.
    ("\t(segment\n\t\t(start 124.86 51.6)\n\t\t(end 124.86 53.81)\n",
     "\t(segment\n\t\t(start 124.86 51.6)\n\t\t(end 124.86 52.6)\n\t\t(width 0.4)\n\t\t(layer \"F.Cu\")\n"
     "\t\t(net \"+3V3\")\n\t\t(uuid \"0b5e0b05-0000-4000-8000-00000000a001\")\n\t)\n"
     "\t(segment\n\t\t(start 124.86 52.6)\n\t\t(end 124.86 53.81)\n"),
]


def plant(text):
    for old, new in EDITS:
        if text.count(old) != 1:
            raise SystemExit(f"planted: expected one {old!r} in the board, found {text.count(old)}")
        text = text.replace(old, new)
    return text


if __name__ == "__main__":
    path = sys.argv[1]
    with open(path) as f:
        s = f.read()
    with open(path, "w") as f:
        f.write(plant(s))
