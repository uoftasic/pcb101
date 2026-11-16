#!/usr/bin/env python3
"""Lab 04 self-test: boards and bring-up plans with known verdicts.

    labs/common/kicad.sh python3 labs/lab-04-protect-and-plan/src/selftest.py

Runs labs/common/check_pmod.py --protect on Lab 03's reference board with this lab's
BRINGUP.md template, which is where a student starts (the five Lab 04 rows and the plan
must FAIL); on this lab's reference solution (must PASS); on the solution with the template
plan in place of its own (only the plan must FAIL); and on the solution with R1 changed to
100 ohms (the ui[0] row must FAIL, since 2.7 V / 100 ohms is more than 20 mA). Then
check_bringup.py on the template (FAIL) and on the reference plan (PASS). Copies go in
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
COMMON = os.path.join(REPO, "labs", "common")
OUT = os.path.join(LAB, "results", "selftest")
LAB03 = os.path.join(REPO, "labs", "lab-03-a-pmod-for-one-projects-pins", "solutions", "simproc-pmod")
SOLUTION = os.path.join(LAB, "solutions", "simproc-pmod")
TEMPLATE_PLAN = os.path.join(LAB, "BRINGUP.md")


def run(cmd):
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    return r.returncode, r.stdout


def run_check(folder, *args):
    rc, out = run([sys.executable, os.path.join(COMMON, "check_pmod.py"), folder, "--protect",
                   "--bringup", os.path.join(folder, "BRINGUP.md"), *args])
    rows, in_pmod = {}, False
    for line in out.splitlines():
        if line.startswith("IC103 Pmod check"):
            in_pmod = True
        elif line.startswith("IC103 bring-up plan check"):
            in_pmod = False
        elif in_pmod and re.match(r"^  (ok  |FAIL)  ", line):
            rows[line[8:20].strip()] = line[2:6].strip()
    board = "PASS" if "board check PASS" in out else ("FAIL" if "board check FAIL" in out else "-")
    plan = "PASS" if "bring-up plan PASS" in out else "FAIL"
    return rc, board, plan, {k for k, v in rows.items() if v == "FAIL"}, out


def copy(src, name, plan=None):
    dst = os.path.join(OUT, name)
    shutil.rmtree(dst, ignore_errors=True)
    shutil.copytree(src, dst)
    if plan:
        shutil.copy(plan, os.path.join(dst, "BRINGUP.md"))
    return dst


def main():
    os.makedirs(OUT, exist_ok=True)
    start = copy(LAB03, "start", TEMPLATE_PLAN)
    no_plan = copy(SOLUTION, "template-plan", TEMPLATE_PLAN)
    small_r = copy(SOLUTION, "r1-100-ohm")
    sch = os.path.join(small_r, "pmod.kicad_sch")
    with open(sch) as f:
        s = f.read()
    m = re.search(r'\(property "Reference" "R1"', s)
    v = s.index('(property "Value" "1k"', m.start())
    s = s[:v] + '(property "Value" "100"' + s[v + len('(property "Value" "1k"'):]
    with open(sch, "w") as f:
        f.write(s)

    protect_rows = {"ui[0]", "uo[0]", "ESD J4.2", "ESD J4.3", "sense"}
    cases = [
        # name, folder, args, exit, board check, plan, failing Pmod rows
        ("Lab 03 board, template plan", start, ["--no-board-check"], 1, "-", "FAIL", protect_rows),
        ("reference solution", SOLUTION, [], 0, "PASS", "PASS", set()),
        ("solution, template plan", no_plan, ["--no-board-check"], 1, "-", "FAIL", set()),
        ("solution, R1 = 100 ohm", small_r, ["--no-board-check"], 1, "-", "PASS", {"ui[0]"}),
    ]
    good, total = 0, 0
    for name, folder, args, rc_w, board_w, plan_w, fails_w in cases:
        rc, board, plan, fails, out = run_check(folder, *args)
        ok = (rc, board, plan, fails) == (rc_w, board_w, plan_w, fails_w)
        good += ok
        total += 1
        print(f"{'ok  ' if ok else 'BAD '} {name:30} exit {rc}, board check {board}, plan {plan}, "
              f"failing rows {', '.join(sorted(fails)) or 'none'}")
        if not ok:
            print(out)
    for name, plan, want in (("template BRINGUP.md", TEMPLATE_PLAN, 1),
                             ("reference BRINGUP.md", os.path.join(SOLUTION, "BRINGUP.md"), 0)):
        rc, out = run([sys.executable, os.path.join(COMMON, "check_bringup.py"), plan])
        ok = rc == want
        good += ok
        total += 1
        print(f"{'ok  ' if ok else 'BAD '} {name:30} exit {rc}: {out.strip().splitlines()[-1]}")
        if not ok:
            print(out)
    print(f"{good} of {total} cases gave the expected verdict")
    return 0 if good == total else 1


if __name__ == "__main__":
    sys.exit(main())
