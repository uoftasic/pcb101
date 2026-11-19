#!/usr/bin/env python3
"""Does the Lab 02 check check? Seven folders with known verdicts.

    labs/common/kicad.sh python3 labs/lab-02-a-footprint-from-a-datasheet/src/selftest.py

1. The lab folder as shipped: pads.md all TODO, an empty library: must FAIL.
2. solutions/: must PASS.
3. The solution with KiCad's own QFN-24-1EP_4x4mm_P0.5mm_EP2.6x2.6mm saved as RHL0024A:
   must FAIL, naming the library footprint it copies.
4. The solution with every signal pad 0.32 mm wide, in pads.md and in the footprint: must
   FAIL, on the hand calculation and on DRC clearance in the fit project, because 0.32 mm
   pads at a 0.5 mm pitch leave 0.18 mm between them.
5. The solution with pin 25 (the exposed pad) left out of the symbol: must FAIL.
6. The solution with GND and VCCB drawn as KiCad 10 pin stacks, one pin numbered [11,12,13]
   and one numbered [23,24], in place of pins stacked on top of each other: must PASS.
7. The solution with the hidden VCCB pin 24 made a power input instead of passive: must
   FAIL on the symbol, because KiCad joins a hidden power input to a global net.

Exit status 0 when every case gives its expected verdict.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.dirname(HERE)
CHECK = os.path.join(HERE, "check_footprint.py")
SOLUTION = os.path.join(LAB, "solutions")
KICAD_QFN = "/usr/share/kicad/footprints/Package_DFN_QFN.pretty"
COPY = "QFN-24-1EP_4x4mm_P0.5mm_EP2.6x2.6mm"


def variant(work, name, edit):
    d = os.path.join(work, name)
    shutil.copytree(SOLUTION, d, ignore=shutil.ignore_patterns("README.md"))
    edit(d)
    return d


def sub(path, old, new, count=0):
    with open(path) as f:
        text = f.read()
    out = text.replace(old, new) if count == 0 else text.replace(old, new, count)
    assert out != text, f"{old!r} not found in {path}; update selftest.py"
    with open(path, "w") as f:
        f.write(out)


def main():
    work = tempfile.mkdtemp(prefix="pcb101-lab02-")
    fp = os.path.join("pcb101.pretty", "RHL0024A.kicad_mod")

    def copy_kicad(d):
        with open(os.path.join(KICAD_QFN, COPY + ".kicad_mod")) as f:
            text = f.read()
        with open(os.path.join(d, fp), "w") as f:
            f.write(text.replace(f'(footprint "{COPY}"', '(footprint "RHL0024A"', 1))

    def wide_pads(d):
        sub(os.path.join(d, "pads.md"), "| X | 0.26 | 0.26 |", "| X | 0.32 | 0.32 |")
        sub(os.path.join(d, fp), "(size 0.89 0.26)", "(size 0.89 0.32)")
        sub(os.path.join(d, fp), "(size 0.26 0.89)", "(size 0.32 0.89)")

    def no_pin_25(d):
        path = os.path.join(d, "pcb101.kicad_sym")
        with open(path) as f:
            text = f.read()
        out = re.sub(r'\(pin passive line\s*\(at [^)]*\)\s*\(length [^)]*\)\s*\(name "EP".*?\(number "25".*?\)\s*\)\s*\)\s*\)\s*\)',
                     "", text, flags=re.S)
        assert out != text, "pin 25 not found in the reference symbol; update selftest.py"
        with open(path, "w") as f:
            f.write(out)

    def pin_blocks(text):
        return re.findall(r'\t\t\t\(pin \w+ line\n.*?\n\t\t\t\)\n', text, flags=re.S)

    def number(block):
        return re.search(r'\(number "([^"]*)"', block).group(1)

    def native_stacks(d):
        path = os.path.join(d, "pcb101.kicad_sym")
        with open(path) as f:
            text = f.read()
        for b in pin_blocks(text):
            n = number(b)
            if n in ("12", "13", "24"):
                text = text.replace(b, "", 1)
            elif n in ("11", "23"):
                text = text.replace(b, b.replace(f'(number "{n}"', '(number "[11,12,13]"' if n == "11"
                                                 else '(number "[23,24]"'), 1)
        assert '"[11,12,13]"' in text and '"[23,24]"' in text, "stacked pins not found; update selftest.py"
        with open(path, "w") as f:
            f.write(text)

    def hidden_power_pin(d):
        path = os.path.join(d, "pcb101.kicad_sym")
        with open(path) as f:
            text = f.read()
        b = next(b for b in pin_blocks(text) if number(b) == "24")
        assert "(hide yes)" in b and b.startswith("\t\t\t(pin passive"), "pin 24 isn't hidden and passive; update selftest.py"
        with open(path, "w") as f:
            f.write(text.replace(b, b.replace("(pin passive", "(pin power_in", 1), 1))

    cases = [
        ("lab folder as shipped", LAB, 1, ["Z, long sides: TODO", "RHL0024A.kicad_mod yet"]),
        ("reference solution", SOLUTION, 0, ["PASS"]),
        ("KiCad's QFN-24 renamed", variant(work, "kicad-copy", copy_kicad), 1, [f"same as KiCad's {COPY}"]),
        ("0.32 mm pads", variant(work, "wide", wide_pads), 1, ["X, long sides: 0.32", "drc.error"]),
        ("no pin 25 in the symbol", variant(work, "no-ep-pin", no_pin_25), 1, ["no pin 25"]),
        ("KiCad 10 pin stacks", variant(work, "stacks", native_stacks), 0, ["PASS"]),
        ("hidden power-input pin 24", variant(work, "hidden-power", hidden_power_pin), 1,
         ["pin 24 (VCCB) is a hidden power input"]),
    ]
    results = []
    for label, folder, want_rc, want in cases:
        r = subprocess.run([sys.executable, CHECK, folder, "--out", os.path.join(work, "fit-" + label.split()[0])],
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        ok = r.returncode == want_rc and all(w in r.stdout for w in want)
        results.append(ok)
        verdict = {0: "PASS", 1: "FAIL"}.get(r.returncode, f"exit {r.returncode}")
        print(f"{'ok  ' if ok else 'BAD '} {label:26} {verdict:5} expects {', '.join(repr(w) for w in want)}")
        if not ok:
            print("     " + r.stdout.replace("\n", "\n     "))
    shutil.rmtree(work, ignore_errors=True)
    bad = results.count(False)
    print(f"{len(results) - bad} of {len(results)} cases gave the expected verdict")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
