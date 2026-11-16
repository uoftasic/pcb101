#!/usr/bin/env python3
"""Lab 03 self-test: boards with known verdicts, which show that the Pmod check checks.

    labs/common/kicad.sh python3 labs/lab-03-a-pmod-for-one-projects-pins/src/selftest.py

Runs labs/common/check_pmod.py on the template as shipped (must FAIL on its connectors), on
the reference solution (must PASS), and on three copies of the reference built or edited
here: the dongle header's TXD and RXD swapped in the schematic and routed to match (the
board check must PASS and only the ui[0] and uo[0] rows FAIL), J2 moved 0.5 mm, and the
connectors unlocked (both must FAIL on the connectors row). The copies go in
results/selftest/. Exit status 0 if every case gives its expected verdict.
"""
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.dirname(HERE)
REPO = os.path.dirname(os.path.dirname(LAB))
CHECK = os.path.join(REPO, "labs", "common", "check_pmod.py")
OUT = os.path.join(LAB, "results", "selftest")


def run_check(folder, *args):
    r = subprocess.run([sys.executable, CHECK, folder, *args], stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, text=True)
    rows, in_pmod = {}, False
    for line in r.stdout.splitlines():
        if line.startswith("PB101 Pmod check"):
            in_pmod = True
        elif line.startswith("PB101 bring-up plan check"):
            in_pmod = False
        elif in_pmod and re.match(r"^  (ok  |FAIL)  ", line):
            rows[line[8:20].strip()] = line[2:6].strip()
    board = "PASS" if "board check PASS" in r.stdout else ("FAIL" if "board check FAIL" in r.stdout else "-")
    last = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else ""
    return r.returncode, board, {k for k, v in rows.items() if v == "FAIL"}, last, r.stdout


def copy(src, name):
    dst = os.path.join(OUT, name)
    shutil.rmtree(dst, ignore_errors=True)
    shutil.copytree(src, dst)
    return dst


def edit(path, old, new):
    with open(path) as f:
        s = f.read()
    if old not in s:
        raise SystemExit(f"selftest: {old!r} not in {path}")
    with open(path, "w") as f:
        f.write(s.replace(old, new))


def main():
    os.makedirs(OUT, exist_ok=True)
    solution = os.path.join(LAB, "solutions", "simproc-pmod")
    template = copy(os.path.join(LAB, "template"), "template")

    swapped = os.path.join(OUT, "swapped")
    r = subprocess.run([sys.executable, os.path.join(HERE, "make_reference.py"), "swapped", swapped],
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if r.returncode != 0:
        print(r.stdout)
        return 2

    moved = copy(solution, "moved")
    edit(os.path.join(moved, "pmod.kicad_pcb"), "(at 124.86 56.35 90)", "(at 125.36 56.35 90)")
    unlocked = copy(solution, "unlocked")
    pcb = os.path.join(unlocked, "pmod.kicad_pcb")
    with open(pcb) as f:
        s = f.read()
    with open(pcb, "w") as f:
        f.write(s.replace("\t\t(locked yes)\n", ""))

    cases = [
        # name, folder, args, expected exit, expected board check, expected failing rows
        ("template as shipped", template, [], 1, "FAIL", {"connectors", "pins"}),
        ("reference solution", solution, [], 0, "PASS", set()),
        ("TXD and RXD swapped", swapped, [], 1, "PASS", {"ui[0]", "uo[0]"}),
        ("J2 moved 0.5 mm", moved, ["--no-board-check"], 1, "-", {"connectors", "pins"}),
        ("connectors unlocked", unlocked, ["--no-board-check"], 1, "-", {"connectors"}),
    ]
    good = 0
    for name, folder, args, rc_want, board_want, fail_want in cases:
        rc, board, fails, last, out = run_check(folder, *args)
        ok = rc == rc_want and board == board_want and fails == fail_want
        good += ok
        print(f"{'ok  ' if ok else 'BAD '} {name:22} exit {rc}, board check {board}, "
              f"failing rows {', '.join(sorted(fails)) or 'none'}")
        if not ok:
            print(out)
    print(f"{good} of {len(cases)} cases gave the expected verdict")
    return 0 if good == len(cases) else 1


if __name__ == "__main__":
    sys.exit(main())
