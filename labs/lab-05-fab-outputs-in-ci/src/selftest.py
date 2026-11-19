#!/usr/bin/env python3
"""Lab 05 self-test: board repositories with known verdicts, which show that the check checks.

    python3 labs/lab-05-fab-outputs-in-ci/src/selftest.py

Run it on the host, not through kicad.sh: every case runs the lab's check.sh, which starts
containers of two images, the pinned KiCad image and the pinned KiBot image. It needs Python 3,
git and Docker, and passes PCB101_DOCKER_ARGS on to every container.

It builds git repositories in results/selftest/, each starting from Lab 04's reference board
(labs/lab-04-protect-and-plan/solutions/simproc-pmod/), the way a student's repository stands
when Lab 05 starts:

  starter    the board with the lab's starter/ added and committed, as at the end of Part 1,
             step 3. The check must FAIL on drill, bom, position, images, ibom, report and
             gitignore.
  reference  the board with solutions/simproc-pmod/ added, then the commit with the planted
             error (planted.py), then the commit that takes it out again. The check with
             --planted on the planted commit must PASS on all eleven rows; the planted commit
             on its own must FAIL the check row and the rows for every file the later stages
             make; and --planted on the first commit, where the board was fine, must FAIL the
             planted row.
  dnp        the reference with J4 marked Do not populate, in the schematic and on the board:
             the check must PASS, with J4 left out of the interactive BOM.
  dnp-no-filter  the same with the ibom output's dnf_filter taken out of ci/board.kibot.yaml,
             the mistake the ibom row is there for: the check must FAIL on ibom only.

It also checks that the starter's and the reference's copies of check_board.py,
kicad-image.txt and kibot-image.txt are the same as labs/common's, so the copy a student
commits doesn't drift from the one the labs use. Exit status 0 if every case gives its
expected verdict.
"""
import filecmp
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.dirname(HERE)
REPO = os.path.dirname(os.path.dirname(LAB))
BOARD = os.path.join(REPO, "labs", "lab-04-protect-and-plan", "solutions", "simproc-pmod")
OUT = os.path.join(LAB, "results", "selftest")
CHECK = os.path.join(LAB, "check.sh")
sys.path.insert(0, HERE)
import planted  # noqa: E402

GIT = ["git", "-c", "user.name=PCB101 selftest", "-c", "user.email=selftest@example.com",
       "-c", "init.defaultBranch=main", "-c", "commit.gpgsign=false"]


def sh(cmd, cwd):
    r = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if r.returncode != 0:
        raise SystemExit(f"selftest: {' '.join(cmd)} exited {r.returncode}:\n{r.stdout}")
    return r.stdout.strip()


def commit(repo, msg):
    sh(GIT + ["add", "-A"], repo)
    sh(GIT + ["commit", "-q", "-m", msg], repo)
    return sh(GIT + ["rev-parse", "HEAD"], repo)


def make(name, extra):
    repo = os.path.join(OUT, name)
    shutil.rmtree(repo, ignore_errors=True)
    shutil.copytree(BOARD, repo)
    for f in ("pmod.kicad_prl",):
        if os.path.exists(os.path.join(repo, f)):
            os.remove(os.path.join(repo, f))
    sh(GIT + ["init", "-q"], repo)
    shutil.copytree(extra, repo, dirs_exist_ok=True)
    return repo


def check(repo, *args):
    """The lab's check.sh, run in REPO as a student runs it."""
    r = subprocess.run(["bash", CHECK, *args], cwd=repo, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, text=True)
    fails = set(re.findall(r"^  FAIL  (\S+)", r.stdout, re.M))
    return r.returncode, fails, r.stdout


def edit_block(path, start, ref, old, new):
    """In the top-level block of PATH that starts with START and holds REF's Reference
    property, replace OLD with NEW, once."""
    with open(path) as f:
        lines = f.read().split("\n")
    done = 0
    i = 0
    while i < len(lines):
        if lines[i].startswith(start):
            j = i
            while lines[j] != "\t)":
                j += 1
            block = "\n".join(lines[i:j + 1])
            if f'(property "Reference" "{ref}"' in block:
                if block.count(old) != 1:
                    raise SystemExit(f"selftest: expected one {old!r} in {ref}'s block of {path}")
                lines[i:j + 1] = block.replace(old, new).split("\n")
                done += 1
            i = j + 1
        else:
            i += 1
    if done != 1:
        raise SystemExit(f"selftest: found {done} blocks for {ref} in {path}")
    with open(path, "w") as f:
        f.write("\n".join(lines))


def mark_dnp(repo, ref):
    """What ticking "Do not populate" in the symbol's properties, then updating the PCB, does."""
    edit_block(os.path.join(repo, "pmod.kicad_sch"), "\t(symbol", ref, "(dnp no)", "(dnp yes)")
    edit_block(os.path.join(repo, "pmod.kicad_pcb"), "\t(footprint ", ref,
               "(attr through_hole)", "(attr through_hole dnp)")


def main():
    if not shutil.which("docker"):
        print("selftest: no docker here; run this on the host, not through kicad.sh", file=sys.stderr)
        return 2
    os.makedirs(OUT, exist_ok=True)
    good, cases = 0, 0

    for copy in ("starter", os.path.join("solutions", "simproc-pmod")):
        for f in ("check_board.py", "kicad-image.txt", "kibot-image.txt"):
            cases += 1
            a = os.path.join(LAB, copy, "ci", f)
            b = os.path.join(REPO, "labs", "common", f)
            same = filecmp.cmp(a, b, shallow=False)
            good += same
            print(f"{'ok  ' if same else 'BAD '} {copy}/ci/{f} is {'the same as' if same else 'NOT the same as'} labs/common/{f}")

    starter = make("starter", os.path.join(LAB, "starter"))
    commit(starter, "Lab 04 board, and the Lab 05 starter")

    ref = make("reference", os.path.join(LAB, "solutions", "simproc-pmod"))
    first = commit(ref, "Lab 04 board, and the Lab 05 workflow, finished")
    pcb = os.path.join(ref, "pmod.kicad_pcb")
    with open(pcb) as f:
        good_board = f.read()
    with open(pcb, "w") as f:
        f.write(planted.plant(good_board))
    plant = commit(ref, "Drag the +3V3 track down 1 mm, into J1's pads (planted)")

    plant_only = os.path.join(OUT, "planted")
    shutil.rmtree(plant_only, ignore_errors=True)
    shutil.copytree(ref, plant_only)
    sh(GIT + ["checkout", "-q", plant], plant_only)

    with open(pcb, "w") as f:
        f.write(good_board)
    commit(ref, "Put the +3V3 track back")

    dnp = os.path.join(OUT, "dnp")
    shutil.rmtree(dnp, ignore_errors=True)
    shutil.copytree(ref, dnp)
    mark_dnp(dnp, "J4")
    commit(dnp, "Mark J4 Do not populate")

    nofilter = os.path.join(OUT, "dnp-no-filter")
    shutil.rmtree(nofilter, ignore_errors=True)
    shutil.copytree(dnp, nofilter)
    cfg = os.path.join(nofilter, "ci", "board.kibot.yaml")
    with open(cfg) as f:
        text = f.read()
    if text.count("    options:\n      dnf_filter: dnp\n") != 1:
        raise SystemExit("selftest: no dnf_filter in the ibom output of the reference's ci/board.kibot.yaml")
    with open(cfg, "w") as f:
        f.write(text.replace("    options:\n      dnf_filter: dnp\n", ""))
    commit(nofilter, "Take the DNP filter out of the ibom output")

    all_rows = {"workflow", "check", "gerbers", "drill", "bom", "position", "images", "ibom", "report",
                "gitignore", "planted"}
    tests = [
        # name, repo, args, expected exit, expected failing rows
        ("starter, as copied in", starter, [], 1, {"drill", "bom", "position", "images", "ibom", "report",
                                                   "gitignore"}),
        ("reference, planted commit named", ref, ["--planted", plant], 0, set()),
        ("reference, at the planted commit", plant_only, [], 1, {"check", "gerbers", "drill", "bom",
                                                                "position", "images", "ibom", "report"}),
        ("reference, a good commit named", ref, ["--planted", first], 1, {"planted"}),
        ("reference, J4 marked DNP", dnp, [], 0, set()),
        ("J4 marked DNP, ibom without a filter", nofilter, [], 1, {"ibom"}),
    ]
    for name, repo, args, rc_want, fail_want in tests:
        cases += 1
        rc, fails, out = check(repo, *args)
        ok = rc == rc_want and fails == fail_want
        good += ok
        print(f"{'ok  ' if ok else 'BAD '} {name:37} exit {rc}, failing rows {', '.join(sorted(fails)) or 'none'}",
              flush=True)
        with open(os.path.join(OUT, re.sub(r"\W+", "-", name).strip("-") + ".txt"), "w") as f:
            f.write(out)
        if not ok:
            print(out)
    assert all_rows  # the rows a full run prints
    print(f"{good} of {cases} cases gave the expected verdict")
    return 0 if good == cases else 1


if __name__ == "__main__":
    sys.exit(main())
