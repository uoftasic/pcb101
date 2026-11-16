#!/usr/bin/env python3
"""Does the board checker check? Four boards with known answers, inside the pinned image.

    labs/common/kicad.sh python3 labs/common/selftest_check.py

1. KiCad's own pic_programmer demo, which is clean in 10.0.8: must PASS.
2. The same board with one footprint deleted: must FAIL on a missing_footprint parity item.
3. The same board with a GND track laid across a VCC track: must FAIL on a DRC error.
4. Tiny Tapeout's SKY130 breakout against selftest/sky-breakout-expect.json: must PASS,
   which checks the counting itself (10 ERC errors, 1 excluded DRC error, and so on).
   It needs the fetched boards (python3 labs/common/fetch_boards.py) and is skipped
   without them.

Exit status 0 when every case gives its expected verdict.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
CHECK = os.path.join(HERE, "check_board.py")
DEMO = "/usr/share/kicad/demos/pic_programmer"
SKY = os.path.join(HERE, "upstream", "breakout-pcb", "breakout-sky-qfn", "breakout-sky-qfn.kicad_pro")


def remove_first_block(text, head):
    """Delete the first top-level S-expression that starts with `head`, by counting
    parentheses outside quoted strings."""
    start = text.index(head)
    depth, i, in_str = 0, start, False
    while True:
        c = text[i]
        if in_str:
            if c == "\\":
                i += 1
            elif c == '"':
                in_str = False
        elif c == '"':
            in_str = True
        elif c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return text[:start] + text[i + 1:]
        i += 1


def check(project, expect=None):
    cmd = [sys.executable, CHECK, project, "--show", "3"]
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as t:
        summary = t.name
    cmd += ["--summary", summary]
    if expect:
        cmd += ["--expect", expect]
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    data = {}
    if os.path.exists(summary) and os.path.getsize(summary):
        with open(summary) as f:
            data = json.load(f)
    os.unlink(summary)
    return r.returncode, r.stdout, data


def main():
    work = tempfile.mkdtemp(prefix="ic103-selftest-")
    results = []

    def case(label, project, want_rc, want_key=None, expect=None):
        rc, out, data = check(project, expect)
        n = data.get("by_type", {}).get(want_key, 0) if want_key and want_key.count(".") == 2 \
            else data.get("counts", {}).get(want_key, 0) if want_key else None
        ok = rc == want_rc and (want_key is None or n > 0)
        verdict = data.get("verdict", f"exit {rc}")
        detail = f"{want_key} = {n}" if want_key else ""
        results.append(ok)
        print(f"{'ok  ' if ok else 'BAD '} {label:44} {verdict:5} {detail}")
        if not ok:
            print("     " + out.replace("\n", "\n     "))

    clean = os.path.join(work, "clean")
    shutil.copytree(DEMO, clean)
    case("pic_programmer as shipped", os.path.join(clean, "pic_programmer.kicad_pro"), 0)

    nofp = os.path.join(work, "missing-footprint")
    shutil.copytree(DEMO, nofp)
    pcb = os.path.join(nofp, "pic_programmer.kicad_pcb")
    with open(pcb) as f:
        text = f.read()
    with open(pcb, "w") as f:
        f.write(remove_first_block(text, "\t(footprint "))
    case("pic_programmer, one footprint deleted", os.path.join(nofp, "pic_programmer.kicad_pro"), 1,
         "parity.warning.missing_footprint")

    short = os.path.join(work, "crossing-track")
    shutil.copytree(DEMO, short)
    pcb = os.path.join(short, "pic_programmer.kicad_pcb")
    with open(pcb) as f:
        text = f.read()
    # The first segment in the file is VCC, 0.8 mm wide, from (110.49, 124.155) to
    # (110.49, 119.38) on F.Cu. Lay a GND track straight across its middle.
    assert re.search(r'\(start 110\.49 124\.155\)\s*\(end 110\.49 119\.38\)', text), "demo board changed"
    track = ('\t(segment\n\t\t(start 108.49 121.7)\n\t\t(end 112.49 121.7)\n\t\t(width 0.25)\n'
             '\t\t(layer "F.Cu")\n\t\t(net "GND")\n\t\t(uuid "0b5e1e57-0000-4000-8000-000000000001")\n\t)\n')
    i = text.index("\t(segment")
    with open(pcb, "w") as f:
        f.write(text[:i] + track + text[i:])
    case("pic_programmer, GND track across VCC", os.path.join(short, "pic_programmer.kicad_pro"), 1,
         "drc.error")

    if os.path.exists(SKY):
        case("SKY130 breakout against its expected counts", SKY, 0, None,
             os.path.join(HERE, "selftest", "sky-breakout-expect.json"))
    else:
        print(f"skip {'SKY130 breakout (not fetched)':44}")

    shutil.rmtree(work, ignore_errors=True)
    bad = results.count(False)
    print(f"{len(results) - bad} of {len(results)} cases gave the expected verdict")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
