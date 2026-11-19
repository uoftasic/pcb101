#!/usr/bin/env python3
"""Lab 06 self-test: the seeded board and review records with known verdicts.

    labs/common/kicad.sh python3 labs/lab-06-review-a-seeded-board/src/selftest.py

The seeded board (board/), as shipped:
  - the board check must PASS: every planted fault agrees with the schematic and the rules
    the board carries, so ERC, DRC and parity have nothing to report;
  - Lab 04's check (check_pmod.py --protect) must FAIL on the connectors and pins rows only:
    the connectors row fails because J3 is 0.5 mm out, and the pins row fails with "not
    checked until the connectors pass" (the power row is checked anyway, and passes);
  - with J3 put back at 22.86 mm, Lab 04's check must FAIL on the ui[0] and uo[0] rows only:
    ui[0] because no capacitor is within 3 mm of U1's VCC pin, uo[0] because U1's second
    buffer is turned round. With J3's spacing, those are the three of the eight faults it
    looks for, and it doesn't look for the other five.

The Lab 06 check, on a board repository like a student's after Lab 05 (Lab 04's reference
board with Lab 05's reference files, in results/selftest/repo):
  - the templates as shipped must FAIL the review and the quote;
  - the reference REVIEW.md and QUOTE.md must PASS, with all 8 faults found;
  - the reference review cut to its first four rows must FAIL (4 found, 5 needed);
  - the reference review with every row's line changed to 2 must FAIL (0 found);
  - the reference quote with a board size of 50 x 50 mm must FAIL on the board row.

Exit status 0 if every case gives its expected verdict.
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
GIT = ["git", "-c", "user.name=PCB101 selftest", "-c", "user.email=selftest@example.com",
       "-c", "init.defaultBranch=main", "-c", "commit.gpgsign=false"]


def run(cmd, cwd=None):
    return subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)


def pmod_fails(folder, *args):
    r = run([sys.executable, os.path.join(COMMON, "check_pmod.py"), folder, "--protect", *args])
    rows = {}
    in_pmod = False
    for line in r.stdout.splitlines():
        if line.startswith("PCB101 Pmod check"):
            in_pmod = True
        elif in_pmod and re.match(r"^  (ok  |FAIL)  ", line):
            rows[line[8:21].strip()] = line[2:6].strip()
    return r.returncode, {k for k, v in rows.items() if v == "FAIL"}, r.stdout


def edit(path, old, new, count=1):
    with open(path) as f:
        s = f.read()
    if s.count(old) != count:
        raise SystemExit(f"selftest: expected {count} of {old!r} in {path}, found {s.count(old)}")
    with open(path, "w") as f:
        f.write(s.replace(old, new))


def main():
    os.makedirs(OUT, exist_ok=True)
    good = cases = 0

    def report(name, ok, detail, out=""):
        nonlocal good, cases
        cases += 1
        good += ok
        print(f"{'ok  ' if ok else 'BAD '} {name:44} {detail}")
        if not ok and out:
            print(out)

    # The seeded board.
    board = os.path.join(OUT, "board")
    shutil.rmtree(board, ignore_errors=True)
    shutil.copytree(os.path.join(LAB, "board"), board)
    r = run([sys.executable, os.path.join(COMMON, "check_board.py"), board])
    report("seeded board: board check", r.returncode == 0, f"exit {r.returncode}, {r.stdout.strip().splitlines()[-1]}", r.stdout)
    rc, fails, out = pmod_fails(board, "--no-board-check")
    report("seeded board: Lab 04 check", rc == 1 and fails == {"connectors", "pins"},
           f"exit {rc}, failing rows {', '.join(sorted(fails))}", out)
    edit(os.path.join(board, "pmod.kicad_pcb"), "(at 148.22 56.35 90)", "(at 147.72 56.35 90)")
    rc, fails, out = pmod_fails(board, "--no-board-check")
    report("seeded board, J3 put back: Lab 04 check",
           rc == 1 and fails == {"ui[0]", "uo[0]"} and "no decoupling" in out and "turned round" in out,
           f"exit {rc}, failing rows {', '.join(sorted(fails))}", out)

    # A board repository as a student's stands after Lab 05.
    repo = os.path.join(OUT, "repo")
    shutil.rmtree(repo, ignore_errors=True)
    shutil.copytree(os.path.join(REPO, "labs", "lab-04-protect-and-plan", "solutions", "simproc-pmod"), repo)
    shutil.copytree(os.path.join(REPO, "labs", "lab-05-fab-outputs-in-ci", "solutions", "simproc-pmod"), repo,
                    dirs_exist_ok=True)
    for f in ("pmod.kicad_prl",):
        if os.path.exists(os.path.join(repo, f)):
            os.remove(os.path.join(repo, f))
    for cmd in (["init", "-q"], ["add", "-A"], ["commit", "-q", "-m", "Lab 04 board and Lab 05 CI"]):
        r = run(GIT + cmd, repo)
        if r.returncode:
            raise SystemExit(r.stdout)
    sha = run(["git", "rev-parse", "--short", "HEAD"], repo).stdout.strip()

    check = os.path.join(HERE, "check_lab06.py")

    def lab06(name, review, quote, want_rc, want):
        shutil.copy(review, os.path.join(repo, "REVIEW.md"))
        shutil.copy(quote, os.path.join(repo, "QUOTE.md"))
        edit(os.path.join(repo, "QUOTE.md"), "commit 0000000", f"commit {sha}", count=open(quote).read().count("commit 0000000"))
        r = run([sys.executable, check, repo])
        last = r.stdout.strip().splitlines()[-1]
        report(name, r.returncode == want_rc and want in last, f"exit {r.returncode}, {last}", r.stdout)
        with open(os.path.join(OUT, re.sub(r"\W+", "-", name).strip("-") + ".txt"), "w") as f:
            f.write(r.stdout)

    sol = os.path.join(LAB, "solutions", "simproc-pmod")
    lab06("templates as shipped", os.path.join(LAB, "REVIEW.md"), os.path.join(LAB, "QUOTE.md"),
          1, "review FAIL (0 of 8 planted faults found); quote FAIL")
    lab06("reference review and quote", os.path.join(sol, "REVIEW.md"), os.path.join(sol, "QUOTE.md"),
          0, "PASS  review PASS (8 of 8 planted faults found); quote PASS")

    four = os.path.join(OUT, "REVIEW-four.md")
    with open(os.path.join(sol, "REVIEW.md")) as f:
        lines = f.read().splitlines()
    with open(four, "w") as f:
        f.write("\n".join(l for l in lines if not re.match(r"^\| [5-8] \|", l)) + "\n")
    lab06("review with four findings", four, os.path.join(sol, "QUOTE.md"), 1, "review FAIL (4 of 8")

    wrong = os.path.join(OUT, "REVIEW-wrong-lines.md")
    with open(wrong, "w") as f:
        f.write("\n".join(re.sub(r"^(\| \d \| [^|]+\| )(\d+)( \|)", r"\g<1>2\3", l) for l in lines) + "\n")
    lab06("review with every line set to 2", wrong, os.path.join(sol, "QUOTE.md"), 1, "review FAIL (0 of 8")

    q50 = os.path.join(OUT, "QUOTE-50x50.md")
    shutil.copy(os.path.join(sol, "QUOTE.md"), q50)
    edit(q50, "64 × 32 mm", "50 × 50 mm")
    lab06("quote with the wrong board size", os.path.join(sol, "REVIEW.md"), q50, 1, "quote FAIL")

    print(f"{good} of {cases} cases gave the expected verdict")
    return 0 if good == cases else 1


if __name__ == "__main__":
    sys.exit(main())
