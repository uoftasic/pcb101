#!/usr/bin/env python3
"""Run the board check on every lab's reference solution. This is what CI runs.

    labs/common/kicad.sh python3 labs/common/check_solutions.py

A reference solution is any KiCad project under labs/<lab>/solutions/: every .kicad_pro
found there is checked with check_board.py, which also reads a check-expect.json next to
it if there is one. The raw ERC and DRC reports and a summary.json for each project go in
labs/common/results/<lab>/<project>/. Exit status 0 when every project passes, or when
there are none yet (which it says).
"""
import glob
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
RESULTS = os.path.join(HERE, "results")


def main():
    os.chdir(ROOT)
    projects = sorted(p for p in glob.glob("labs/*/solutions/**/*.kicad_pro", recursive=True)
                      if not p.startswith("labs/common/"))
    if not projects:
        print("No reference solutions yet: nothing matches labs/*/solutions/**/*.kicad_pro.")
        return 0

    rows, failed = [], 0
    for pro in projects:
        lab = pro.split(os.sep)[1]
        name = os.path.splitext(os.path.basename(pro))[0]
        out = os.path.join(RESULTS, lab, name)
        os.makedirs(out, exist_ok=True)
        summary = os.path.join(out, "summary.json")
        r = subprocess.run([sys.executable, os.path.join(HERE, "check_board.py"), pro,
                            "--reports", out, "--summary", summary],
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        print(r.stdout)
        verdict = {0: "PASS", 1: "FAIL"}.get(r.returncode, "ERROR")
        counts = {}
        if os.path.exists(summary):
            with open(summary) as f:
                counts = json.load(f).get("counts", {})
        rows.append((verdict, pro, counts))
        failed += verdict != "PASS"

    print(f"{'':6}{'ERC err':>8}{'DRC err':>8}{'unconn':>8}{'parity':>8}  project")
    for verdict, pro, c in rows:
        parity = c.get("parity.error", 0) + c.get("parity.warning", 0)
        print(f"{verdict:6}{c.get('erc.error', 0):>8}{c.get('drc.error', 0):>8}"
              f"{c.get('unconnected.error', 0):>8}{parity:>8}  {pro}")
    print(f"\n{len(rows) - failed} of {len(rows)} reference solutions pass")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
