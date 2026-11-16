#!/usr/bin/env python3
"""Does the Lab 01 check check? Five sets of notes with known verdicts.

    labs/common/kicad.sh python3 labs/lab-01-open-a-board-you-didnt-design/src/selftest.py

1. The starter breakout-notes.md, all TODO: must FAIL.
2. solutions/breakout-notes.md: must PASS.
3. The solution with the course plan's first-draft mistake, VDD_IO regulated by U2
   (which is DNP) instead of passing through R8: must FAIL on that row.
4. The solution with TP1 added to "Not fitted": must FAIL on that row.
5. The solution with the volts written the schematic's way, 1V8 and 3V3: must PASS.

The board check runs once, and every case reuses its counts. Needs the fetched boards.
Exit status 0 when every case gives its expected verdict.
"""
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(LAB))
CHECK = os.path.join(HERE, "check_notes.py")
BOARD = os.path.join(ROOT, "labs", "common", "upstream", "breakout-pcb", "breakout-sky-qfn")
SOLUTION = os.path.join(LAB, "solutions", "breakout-notes.md")
STARTER = os.path.join(LAB, "breakout-notes.md")


def main():
    if not os.path.isdir(BOARD):
        print("selftest: fetch the boards first: python3 labs/common/fetch_boards.py")
        return 2
    work = tempfile.mkdtemp(prefix="pb101-lab01-")
    summary = os.path.join(work, "board.json")
    r = subprocess.run([sys.executable, os.path.join(ROOT, "labs", "common", "check_board.py"), BOARD,
                        "--summary", summary, "--show", "0"], stdout=subprocess.PIPE, text=True)
    if not os.path.exists(summary):
        print(r.stdout)
        return 2

    with open(SOLUTION) as f:
        solution = f.read()
    u2 = solution.replace("| VDD_IO | 17, 64 | +3V3 | R4, R8, R13 | 3.3 |",
                          "| VDD_IO | 17, 64 | +3V3 | R4, U2, R13 | 1.8 |")
    tp1 = solution.replace("R1, R3, R6, R7, R11, R12, U2, U3, J2,", "R1, R3, R6, R7, R11, R12, U2, U3, J2, TP1,")
    v3v3 = solution.replace("| 1.8 |", "| 1V8 |").replace("| 3.3 |", "| 3V3 |")
    assert u2 != solution and tp1 != solution and v3v3.count("| 3V3 |") == 2 and "| 1V8 |" in v3v3, \
        "solutions/breakout-notes.md changed; update selftest.py"
    cases = [("starter, all TODO", STARTER, 1, "Chip pins: TODO"),
             ("reference solution", SOLUTION, 0, "PASS"),
             ("VDD_IO through U2 (DNP)", u2, 1, "U2 is marked DNP"),
             ("TP1 listed as not fitted", tp1, 1, "TP1 is not marked DNP"),
             ("volts written 1V8 and 3V3", v3v3, 0, "PASS")]
    results = []
    for label, notes, want_rc, want_text in cases:
        if not os.path.exists(notes):
            path = os.path.join(work, label.split()[0] + ".md")
            with open(path, "w") as f:
                f.write(notes)
            notes = path
        r = subprocess.run([sys.executable, CHECK, notes, "--board-summary", summary],
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        ok = r.returncode == want_rc and want_text in r.stdout
        results.append(ok)
        verdict = {0: "PASS", 1: "FAIL"}.get(r.returncode, f"exit {r.returncode}")
        print(f"{'ok  ' if ok else 'BAD '} {label:28} {verdict:5} expects '{want_text}'")
        if not ok:
            print("     " + r.stdout.replace("\n", "\n     "))
    bad = results.count(False)
    print(f"{len(results) - bad} of {len(results)} cases gave the expected verdict")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
