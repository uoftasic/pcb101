#!/usr/bin/env python3
"""Capstone self-test: board repositories with known verdicts, which show that the check checks.

    labs/common/kicad.sh python3 labs/capstone-a-board-for-a-team-chip/src/selftest.py

Each case is a git repository built in results/selftest/:

  starter   the student's repository as the capstone starts: Lab 04's reference board, Lab
            05's reference CI files, Lab 04's BRINGUP.md and the capstone's DESIGN.md
            template, in one commit. Brief D must FAIL on design, history and test points.
  brief-d   the same first commit, then a second one with solutions/simproc-pmod-brief-d/
            (the board with TP3 and TP4, its DESIGN.md and BRINGUP.md). Brief D must PASS;
            checked as Brief A it must FAIL on its connector.
  brief-a   solutions/source-board-brief-a/, in two commits (the schematic, then the board
            and the notes), if that reference exists. Brief A must PASS.

Exit status 0 if every case gives its expected verdict.
"""
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.dirname(HERE)
LABS = os.path.dirname(LAB)
OUT = os.path.join(LAB, "results", "selftest")
CHECK = os.path.join(HERE, "check_capstone.py")
GIT = ["git", "-c", "user.name=IC103 selftest", "-c", "user.email=selftest@example.com",
       "-c", "init.defaultBranch=main", "-c", "commit.gpgsign=false"]


def sh(cmd, cwd):
    r = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if r.returncode:
        raise SystemExit(f"selftest: {' '.join(cmd)}:\n{r.stdout}")


def commit(repo, msg):
    for f in os.listdir(repo):
        if f.endswith(".kicad_prl"):
            os.remove(os.path.join(repo, f))
    sh(GIT + ["add", "-A"], repo)
    sh(GIT + ["commit", "-q", "-m", msg], repo)


def fresh(name):
    repo = os.path.join(OUT, name)
    shutil.rmtree(repo, ignore_errors=True)
    os.makedirs(repo)
    sh(GIT + ["init", "-q"], repo)
    return repo


def copy_in(src, repo):
    shutil.copytree(src, repo, dirs_exist_ok=True)


def check(repo, *args):
    r = subprocess.run([sys.executable, CHECK, repo, *args], stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, text=True)
    fails = set(re.findall(r"^  FAIL  (\S+(?: points)?)", r.stdout, re.M))
    return r.returncode, fails, r.stdout


def main():
    os.makedirs(OUT, exist_ok=True)
    lab04 = os.path.join(LABS, "lab-04-protect-and-plan", "solutions", "simproc-pmod")
    lab05 = os.path.join(LABS, "lab-05-fab-outputs-in-ci", "solutions", "simproc-pmod")
    sol_d = os.path.join(LAB, "solutions", "simproc-pmod-brief-d")
    sol_a = os.path.join(LAB, "solutions", "source-board-brief-a")

    starter = fresh("starter")
    copy_in(lab04, starter)
    copy_in(lab05, starter)
    shutil.copy(os.path.join(LAB, "DESIGN.md"), os.path.join(starter, "DESIGN.md"))
    commit(starter, "Labs 03 to 05")

    brief_d = fresh("brief-d")
    copy_in(lab04, brief_d)
    copy_in(lab05, brief_d)
    commit(brief_d, "Labs 03 to 05")
    copy_in(sol_d, brief_d)
    commit(brief_d, "Capstone: test points on both UART lines, design note, bring-up plan")

    cases = [
        ("starter, Brief D", starter, ["--brief", "D"], 1, {"design", "history", "test points"}),
        ("reference, Brief D", brief_d, ["--brief", "D"], 0, set()),
        ("Brief D reference checked as Brief A", brief_d, ["--brief", "A"], 1, {"connector"}),
    ]
    if os.path.isdir(sol_a):
        brief_a = fresh("brief-a")
        copy_in(sol_a, brief_a)
        pcb = os.path.join(brief_a, "source.kicad_pcb")
        with open(pcb) as f:
            board = f.read()
        os.rename(pcb, pcb + ".later")
        shutil.copy(os.path.join(LABS, "lab-03-a-pmod-for-one-projects-pins", "template", "pmod.kicad_pcb"), pcb)
        commit(brief_a, "Schematic")
        os.remove(pcb)
        os.rename(pcb + ".later", pcb)
        commit(brief_a, "Board, design note and bring-up plan")
        cases.append(("reference, Brief A", brief_a, ["--brief", "A"], 0, set()))

    good = 0
    for name, repo, args, rc_want, fail_want in cases:
        rc, fails, out = check(repo, *args)
        ok = rc == rc_want and fails == fail_want
        good += ok
        print(f"{'ok  ' if ok else 'BAD '} {name:38} exit {rc}, failing rows {', '.join(sorted(fails)) or 'none'}")
        with open(os.path.join(OUT, re.sub(r"\W+", "-", name).strip("-") + ".txt"), "w") as f:
            f.write(out)
        if not ok:
            print(out)
    print(f"{good} of {len(cases)} cases gave the expected verdict")
    return 0 if good == len(cases) else 1


if __name__ == "__main__":
    sys.exit(main())
