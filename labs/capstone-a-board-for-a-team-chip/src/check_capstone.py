#!/usr/bin/env python3
"""PCB101 capstone check: is your board for a team chip ready to order?

    labs/common/kicad.sh python3 /w/labs/capstone-a-board-for-a-team-chip/src/check_capstone.py REPO --brief D|A [--pins FILE]

Run it through the capstone's check.sh, from your board repository (REPO, default the current
folder). It runs, in the course's pinned KiCad image:

  ci        Lab 05's check (labs/lab-05-fab-outputs-in-ci/src/check_ci.py): your ci/build.sh
            passes the board check and builds every fabrication file and review image, and
            git sees nothing untracked after it
  design    DESIGN.md: its four sections filled in, no TODO, at least 3 numbered requirements
            and 3 numbered decisions, every decision with a value and its unit and a
            "Meets:" line, and every requirement met by a decision
  history   at least 2 commits change the schematic or the board, so the work shows in git
            (a single commit that adds everything isn't accepted for certification either)

then, for Brief D (a bring-up Pmod for a digital project):

  pmod      Lab 04's check (labs/common/check_pmod.py --protect --bringup BRINGUP.md), with
            your project's pin list if you give one with --pins
  test points  a test point on every signal pin of the board's external connector, on
            either side of its series resistor

or, for Brief A (a source board for one analog pin):

  connector a 2 x 16 connector that mates the demo board's analog header J13: GND on the
            nine pins J13 has on GND, and pin 32 on the 3.3 V supply or left open
  pin       exactly one of the twelve J13 pins that carry an analog pad on the SKY130
            breakout is driven, and none of the pins that are ground on the breakout
  filter    that pin's net has a capacitor to GND and a series resistor from a source net
  test points  a test point on the pin's net and one on the source net
  bringup   BRINGUP.md passes labs/common/check_bringup.py

The J13 facts come from TinyTapeout/tt-demo-pcb at bbf3dd1, where J13 is a 2 x 16 header
marked DNP, and the analog pads behind each of its lines from breakout-pcb at 91a2bf1
(breakout-sky-qfn's J1). Exit status: 0 PASS, 1 FAIL, 2 the check couldn't run.
"""
import argparse
import glob
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.dirname(HERE)
LABS = os.path.dirname(LAB)
COMMON = os.path.join(LABS, "common")
sys.path.insert(0, COMMON)
from check_pmod import Netlist, parse_value  # noqa: E402

UNIT = (r"(?:[kKMmµu]?(?:Ω|ohms?)|[kKM]?R\b|[mµun]?V\b|[mµun]?A\b|[kKMG]?Hz\b|baud\b|bit/s\b|"
        r"[mµunp]?F\b|[mµunp]s\b|s\b|%|mm\b|mil\b|LSB\b|°C\b)")
NUMBER = r"[-+]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?"
VALUE = re.compile(rf"{NUMBER}\s*{UNIT}")

# The demo board's analog header J13 (tt-demo-pcb bbf3dd1), pin by pin.
J13_GND = {"1", "6", "9", "14", "17", "22", "25", "30", "31"}
J13_3V3 = "32"
J13_ANALOG = {"4": "an0", "5": "an1", "7": "an2", "10": "an3", "12": "an4", "13": "an5",
              "29": "an6", "28": "an7", "26": "an8", "23": "an9", "21": "an10", "20": "an11"}
J13_LETTER = {"2": "A", "3": "B", "4": "C", "5": "D", "7": "F", "8": "E", "10": "G", "11": "H", "12": "J",
              "13": "K", "15": "M", "16": "L", "18": "N", "19": "P", "20": "Q", "21": "R", "23": "T",
              "24": "S", "26": "U", "27": "V", "28": "W", "29": "X"}
J13_SKY_GND = {"2", "3", "8", "11", "15", "16", "18", "19"}


def run(cmd, cwd=None):
    return subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)


# --------------------------------------------------------------------------------------

def sections(text):
    out, cur = {}, None
    for line in text.splitlines():
        m = re.match(r"^##\s+(.*?)\s*$", line)
        if m and not line.startswith("###"):
            cur = m.group(1)
            out[cur] = []
        elif cur is not None:
            out[cur].append(line)
    return out


def numbered(lines):
    items, cur = [], None
    for line in lines:
        m = re.match(r"^(\d+)\.\s", line)
        if m:
            cur = [int(m.group(1)), line]
            items.append(cur)
        elif cur is not None and (line.startswith(" ") or line.startswith("\t")) and line.strip():
            cur.append(line)
        elif cur is not None and line.strip():
            cur = None
    return [(it[0], " ".join(s.strip() for s in it[1:])) for it in items]


def counted(items, one, many):
    """'decision 1' or 'decisions 1, 2': a label in the singular or plural, then the numbers."""
    return f"{one if len(items) == 1 else many} {', '.join(map(str, items))}"


def either(items):
    """'A', 'A or B', 'A, B or C'."""
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " or " + items[-1]


def check_design(path, rows):
    if not os.path.exists(path):
        rows.append((False, "design", "no DESIGN.md; copy the capstone's template into your repository"))
        return
    with open(path, encoding="utf-8") as f:
        text = f.read()
    secs = sections(text)
    probs = []
    todo = [i + 1 for i, l in enumerate(text.splitlines()) if "TODO" in l]
    if todo:
        probs.append(f"{len(todo)} line{' still says' if len(todo) == 1 else 's still say'} TODO")
    for name in ("Requirements", "Decisions", "Checks", "Open questions"):
        body = [l for l in secs.get(name, []) if l.strip() and not l.strip().startswith("<!--")]
        if name not in secs:
            probs.append(f"no '## {name}' section")
        elif not body:
            probs.append(f"'{name}' is empty")
    reqs = numbered(secs.get("Requirements", []))
    decs = numbered(secs.get("Decisions", []))
    if len(reqs) < 3:
        probs.append(f"{'only ' + str(len(reqs)) if reqs else 'no'} numbered "
                     f"requirement{'' if len(reqs) == 1 else 's'}, and at least 3 are needed")
    if len(decs) < 3:
        probs.append(f"{'only ' + str(len(decs)) if decs else 'no'} numbered "
                     f"decision{'' if len(decs) == 1 else 's'}, and at least 3 are needed")
    met = set()
    no_value, no_meets = [], []
    for n, item in decs:
        m = re.search(r"Meets:\s*([^.]*)", item)
        if not m or not re.findall(r"\d+", m.group(1)):
            no_meets.append(n)
        else:
            met.update(int(x) for x in re.findall(r"\d+", m.group(1)))
        body = item[:m.start()] if m else item
        if not VALUE.search(body):
            no_value.append(n)
    if no_meets:
        probs.append(f"{counted(no_meets, 'decision', 'decisions')} {'has' if len(no_meets) == 1 else 'have'} "
                     "no 'Meets:' line naming requirements")
    if no_value:
        probs.append(f"{counted(no_value, 'decision', 'decisions')} "
                     f"{'gives no value with its unit' if len(no_value) == 1 else 'give no value with their units'}")
    unmet = [n for n, _ in reqs if n not in met]
    if reqs and decs and unmet:
        probs.append(f"{counted(unmet, 'requirement', 'requirements')} {'isn' if len(unmet) == 1 else 'aren'}'t "
                     "met by any decision")
    rows.append((not probs, "design", f"{len(reqs)} requirements, {len(decs)} decisions, every requirement met"
                 if not probs else "; ".join(probs)))


def check_history(repo, rows):
    r = run(["git", "log", "--format=%h", "--", "*.kicad_sch", "*.kicad_pcb"], repo)
    commits = [l for l in r.stdout.split() if l]
    rows.append((len(commits) >= 2, "history", f"{len(commits)} commit{'' if len(commits) == 1 else 's'} change{'s' if len(commits) == 1 else ''} the schematic or the board"
                 + ("" if len(commits) >= 2 else "; at least 2 needed")))


def test_points(nl):
    """{net: [TP refs]} for every one-pin part whose reference starts with TP."""
    out = {}
    for ref, p in nl.parts.items():
        if ref.startswith("TP") and len(p["pins"]) == 1:
            out.setdefault(next(iter(p["pins"].values())), []).append(ref)
    return out


def neighbours(nl, net):
    """Nets one two-pin resistor away from net."""
    out = []
    for ref, a, b, _ in nl.resistors():
        na, nb = nl.net(ref, a), nl.net(ref, b)
        if na == net and nb:
            out.append((ref, nb))
        elif nb == net and na:
            out.append((ref, na))
    return out


def check_brief_d(repo, pro, pins, rows):
    cmd = [sys.executable, os.path.join(COMMON, "check_pmod.py"), repo, "--protect", "--no-board-check",
           "--bringup", "BRINGUP.md"] + (["--pins", pins] if pins else [])
    r = run(cmd, repo)
    last = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else ""
    fails = [l.strip() for l in r.stdout.splitlines() if l.startswith("  FAIL")]
    rows.append((r.returncode == 0, "pmod", last if r.returncode == 0 else
                 (last + "; " + "; ".join(fails[:3]))))

    nl = Netlist(pro[:-len(".kicad_pro")] + ".kicad_sch")
    tps = test_points(nl)
    ext = [ref for ref, p in nl.parts.items() if ref.startswith("J") and p["part"] != "PMOD_PERIPH_2x6"
           and "GND" in p["pins"].values()]
    if not ext:
        rows.append((False, "test points", "no external connector (a J part other than the Pmods, with a GND pin)"))
        return
    bad, good = [], []
    for ref in sorted(ext):
        for pin, net in sorted(nl.parts[ref]["pins"].items()):
            if net == "GND":
                continue
            cands = [net] + [n for _, n in neighbours(nl, net)]
            hit = [(n, t) for n in cands for t in tps.get(n, [])]
            if hit:
                good.append(f"{ref} pin {pin}: {hit[0][1]}")
            else:
                bad.append(f"{ref} pin {pin} ({net})")
    rows.append((not bad and bool(good), "test points",
                 ", ".join(good) if not bad else "no test point on " + either(bad)
                 + (", or on the other side of its series resistor" if len(bad) == 1
                    else ", or on the other side of their series resistors")))


def check_brief_a(repo, pro, rows):
    nl = Netlist(pro[:-len(".kicad_pro")] + ".kicad_sch")
    conns = [ref for ref, p in nl.parts.items() if re.match(r"Conn_02x16", p["part"])]
    if len(conns) != 1:
        rows.append((False, "connector", f"{len(conns)} Conn_02x16 connectors; Brief A needs one, to mate J13"))
        return
    j = conns[0]
    pins = nl.parts[j]["pins"]
    not_gnd = sorted((p for p in J13_GND if pins.get(p) != "GND"), key=int)
    v33 = pins.get(J13_3V3)
    if not_gnd:
        rows.append((False, "connector", f"{j} pins {', '.join(not_gnd)} aren't on GND; J13 has GND there"))
    elif v33 and "3V3" not in v33.upper() and "3.3" not in v33:
        rows.append((False, "connector", f"{j} pin 32 is on {v33}; J13 has +3V3 there"))
    else:
        rows.append((True, "connector", f"{j} mates J13: GND on its 9 GND pins, pin 32 "
                     + (f"on {v33}" if v33 else "left open")))

    driven = [p for p in J13_ANALOG if pins.get(p)]
    shorted = sorted((p for p in J13_SKY_GND if pins.get(p) and pins.get(p) != "GND"), key=int)
    if len(driven) != 1 or shorted:
        rows.append((False, "pin", (f"{len(driven)} of the analog pins are connected; drive exactly one"
                                    if len(driven) != 1 else "")
                     + ("; " if len(driven) != 1 and shorted else "")
                     + (f"pins {', '.join(shorted)} are ground on the SKY130 breakout and must not be driven"
                        if shorted else "")))
        return
    p = driven[0]
    net = pins[p]
    rows.append((True, "pin", f"{j} pin {p} (J13 line /{J13_LETTER[p]}, {J13_ANALOG[p]} on the SKY130 breakout), net {net}"))

    caps = []
    for ref, part in nl.parts.items():
        if ref.startswith("C") and len(part["pins"]) == 2 and set(part["pins"].values()) == {net, "GND"}:
            caps.append(f"{ref} ({part['value']})")
    series = neighbours(nl, net)
    series = [(r, n) for r, n in series if n != "GND"]
    if not caps or not series:
        rows.append((False, "filter", ("no capacitor from " + net + " to GND" if not caps else "")
                     + ("; " if not caps and not series else "") + ("no series resistor into " + net if not series else "")))
        return
    rref, src = series[0]
    rows.append((True, "filter", f"{rref} ({nl.parts[rref]['value']}) from {src}, {caps[0]} to GND"))
    tps = test_points(nl)
    lost = [n for n in (src, net) if not tps.get(n)]
    rows.append((not lost, "test points", f"{tps.get(src, ['?'])[0]} on {src}, {tps.get(net, ['?'])[0]} on {net}"
                 if not lost else "no test point on " + " or ".join(lost)))
    b = run([sys.executable, os.path.join(COMMON, "check_bringup.py"), "BRINGUP.md"], repo)
    lastb = b.stdout.strip().splitlines()[-1] if b.stdout.strip() else "no output"
    rows.append((b.returncode == 0, "bringup", lastb))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("repo", nargs="?", default=".")
    ap.add_argument("--brief", choices=["D", "A", "d", "a"], required=True)
    ap.add_argument("--pins", help="Brief D: your project's pin list (default: SimProc's)")
    args = ap.parse_args()
    repo = os.path.abspath(args.repo)
    brief = args.brief.upper()
    pros = glob.glob(os.path.join(repo, "*.kicad_pro"))
    if len(pros) != 1:
        print(f"check_capstone: {repo} holds {len(pros)} .kicad_pro files", file=sys.stderr)
        return 2
    rows = []

    ci = run([sys.executable, os.path.join(LABS, "lab-05-fab-outputs-in-ci", "src", "check_ci.py"), repo])
    ci_fails = [l.strip()[6:] for l in ci.stdout.splitlines() if l.startswith("  FAIL")]
    rows.append((ci.returncode == 0, "ci", "Lab 05's check passes: the board check, every output, and .gitignore"
                 if ci.returncode == 0 else "Lab 05's check fails: " + "; ".join(ci_fails[:3])))
    check_design(os.path.join(repo, "DESIGN.md"), rows)
    check_history(repo, rows)
    if brief == "D":
        check_brief_d(repo, pros[0], args.pins, rows)
    else:
        check_brief_a(repo, pros[0], rows)

    print(f"PCB101 capstone check, Brief {brief}")
    print(f"  repository  {repo}")
    print()
    for ok, what, detail in rows:
        print(f"  {'ok  ' if ok else 'FAIL'}  {what:12} {detail}")
    failed = sum(1 for ok, *_ in rows if not ok)
    print()
    name = os.path.basename(pros[0])[:-len(".kicad_pro")]
    print(f"{'PASS' if not failed else 'FAIL'}  {name}, Brief {brief}: {len(rows) - failed} of {len(rows)} capstone checks ok")
    if not ci.returncode == 0:
        print("\nLab 05's check said:\n" + ci.stdout[-3000:])
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
