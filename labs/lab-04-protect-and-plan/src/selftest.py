#!/usr/bin/env python3
"""Lab 04 self-test: boards and bring-up plans with known verdicts.

    labs/common/kicad.sh python3 labs/lab-04-protect-and-plan/src/selftest.py

Runs labs/common/check_pmod.py --protect on:

  - Lab 03's reference board with this lab's BRINGUP.md template, which is where a student
    starts: the five Lab 04 rows and the plan must FAIL;
  - this lab's reference solution: must PASS;
  - the solution with the template plan in place of its own: only the plan must FAIL;
  - and five copies of the solution, each changed by a text edit, with the rows that must FAIL:
      27k resistors and no buffer   U1 taken out of the schematic, and R1 and R2, now 27 kΩ,
                                    joined straight to the header: ui[0] and uo[0], with the
                                    100 µA and 15.4 kΩ reason
      buffer turned round on ui[0]  U1's first buffer drawn pointing the other way, so its
                                    input is on R1's side and its output on the header's: ui[0]
      R1 = 100 ohm                  below the 330 Ω end of the window: ui[0]
      R2 = 10k ohm                  above the 5.1 kΩ end: uo[0]
      C1 moved away from U1         C1 moved 34 mm to the right on the board, so no capacitor
                                    is within 3 mm of U1's VCC pin: ui[0] and uo[0], since both
                                    lines go through U1
Then check_bringup.py on the template (FAIL) and on the reference plan (PASS). The copies and
each case's output go in results/selftest/. Exit status 0 if every case gives its expected
verdict.
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
        if line.startswith("PCB101 Pmod check"):
            in_pmod = True
        elif line.startswith("PCB101 bring-up plan check"):
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


def edit(path, old, new):
    with open(path) as f:
        s = f.read()
    if s.count(old) != 1:
        raise SystemExit(f"selftest: expected one {old!r} in {path}, found {s.count(old)}")
    with open(path, "w") as f:
        f.write(s.replace(old, new))


def set_value(sch, ref, old, new):
    """Change a schematic symbol's value, as editing its Value field does."""
    with open(sch) as f:
        s = f.read()
    m = re.search(r'\(property "Reference" "%s"' % ref, s)
    v = s.index(f'(property "Value" "{old}"', m.start())
    with open(sch, "w") as f:
        f.write(s[:v] + f'(property "Value" "{new}"' + s[v + len(f'(property "Value" "{old}"'):])


def drop_symbol(sch, ref):
    """Delete every placed unit of a symbol, as selecting it and pressing Delete does."""
    with open(sch) as f:
        lines = f.read().split("\n")
    out, i, dropped = [], 0, 0
    while i < len(lines):
        if lines[i] == "\t(symbol":
            j = lines.index("\t)", i)
            if f'(property "Reference" "{ref}"' in "\n".join(lines[i:j + 1]):
                i, dropped = j + 1, dropped + 1
                continue
        out.append(lines[i])
        i += 1
    if not dropped:
        raise SystemExit(f"selftest: no {ref} in {sch}")
    with open(sch, "w") as f:
        f.write("\n".join(out))


def main():
    os.makedirs(OUT, exist_ok=True)
    start = copy(LAB03, "start", TEMPLATE_PLAN)
    no_plan = copy(SOLUTION, "template-plan", TEMPLATE_PLAN)

    resistors = copy(SOLUTION, "resistors-27k")
    sch = os.path.join(resistors, "pmod.kicad_sch")
    drop_symbol(sch, "U1")
    # The wires that ran from R1 and R2 to U1 now carry the header's nets.
    edit(sch, '(label "RX_BUF"\n\t\t(at 210.82 86.36 0)', '(label "DONGLE_TXD"\n\t\t(at 210.82 86.36 0)')
    edit(sch, '(label "TX_BUF"\n\t\t(at 247.65 99.06 0)', '(label "UART_TX"\n\t\t(at 247.65 99.06 0)')
    set_value(sch, "R1", "1k", "27k")
    set_value(sch, "R2", "1k", "27k")

    # U1's first buffer pointing right instead of left, moved 2.54 mm so that its pins still
    # land on the wires' ends: pin 1 (1A) on R1's wire and pin 6 (1Y) on the header's.
    turned = copy(SOLUTION, "turned-round")
    edit(os.path.join(turned, "pmod.kicad_sch"), "(at 233.68 86.36 180)", "(at 236.22 86.36 0)")

    small_r1 = copy(SOLUTION, "r1-100-ohm")
    set_value(os.path.join(small_r1, "pmod.kicad_sch"), "R1", "1k", "100")
    big_r2 = copy(SOLUTION, "r2-10k")
    set_value(os.path.join(big_r2, "pmod.kicad_sch"), "R2", "1k", "10k")

    far_c1 = copy(SOLUTION, "c1-moved")
    edit(os.path.join(far_c1, "pmod.kicad_pcb"), "(at 121 66.6375 -90)", "(at 155 66.6375 -90)")

    protect_rows = {"ui[0]", "uo[0]", "ESD J4.2", "ESD J4.3", "sense"}
    nb = ["--no-board-check"]
    cases = [
        # name, folder, args, exit, board check, plan, failing Pmod rows, text the output must have
        ("Lab 03 board, template plan", start, nb, 1, "-", "FAIL", protect_rows, "with no buffer"),
        ("reference solution", SOLUTION, [], 0, "PASS", "PASS", set(), "17 of 17"),
        ("solution, template plan", no_plan, nb, 1, "-", "FAIL", set(), ""),
        ("27k resistors and no buffer", resistors, nb, 1, "-", "PASS", {"ui[0]", "uo[0]"}, "15.4 kΩ"),
        ("buffer turned round on ui[0]", turned, nb, 1, "-", "PASS", {"ui[0]"}, "turned round"),
        ("solution, R1 = 100 ohm", small_r1, nb, 1, "-", "PASS", {"ui[0]"}, "below 330 Ω"),
        ("solution, R2 = 10k ohm", big_r2, nb, 1, "-", "PASS", {"uo[0]"}, "above 5.1 kΩ"),
        ("C1 moved away from U1", far_c1, nb, 1, "-", "PASS", {"ui[0]", "uo[0]"}, "no decoupling"),
    ]
    good, total = 0, 0
    for name, folder, args, rc_w, board_w, plan_w, fails_w, text_w in cases:
        rc, board, plan, fails, out = run_check(folder, *args)
        ok = (rc, board, plan, fails) == (rc_w, board_w, plan_w, fails_w) and text_w in out
        good += ok
        total += 1
        print(f"{'ok  ' if ok else 'BAD '} {name:30} exit {rc}, board check {board}, plan {plan}, "
              f"failing rows {', '.join(sorted(fails)) or 'none'}")
        with open(os.path.join(OUT, re.sub(r"\W+", "-", name).strip("-") + ".txt"), "w") as f:
            f.write(out)
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
