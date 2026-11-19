#!/usr/bin/env python3
"""Lab 01 check: do your notes on Tiny Tapeout's SKY130 breakout agree with the board?

    labs/common/kicad.sh python3 labs/lab-01-open-a-board-you-didnt-design/src/check_notes.py
    labs/common/kicad.sh python3 labs/lab-01-open-a-board-you-didnt-design/src/check_notes.py NOTES.md

NOTES.md defaults to breakout-notes.md in the lab folder. The check works out its own
answers from the files, and never from a stored answer key:

- "Not fitted": every footprint on the board whose attributes include `dnp`.
- "Supply rails": for each supply net on the chip (U4's power-input pins, except GND),
  the chip's pins on it, the fitted capacitors from it to GND, and the path back to the
  connectors, following only fitted parts: 0-ohm links (a two-pad part whose value is
  0 or 0R) and regulators (from a VOUT pad back to the VIN pad). The voltage is the
  regulator's, from its value (AP2112K-1.8 is 1.8 V), or else the connector rail's.
- "Checks": the ERC and DRC error and excluded counts, by type, from
  labs/common/check_board.py run on the board in the pinned image.

Exit status: 0 PASS, 1 FAIL, 2 the check couldn't run.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(LAB))
COMMON = os.path.join(ROOT, "labs", "common")
sys.path.insert(0, COMMON)
from kicad_sexpr import load, children, child, prop, flags, net_name  # noqa: E402

BOARD_DIR = os.path.join(COMMON, "upstream", "breakout-pcb", "breakout-sky-qfn")
CHIP = "U4"
GROUND = "GND"
REF = re.compile(r"\b([A-Z]{1,4}[0-9]{1,3})\b")


def shown(path):
    rel = os.path.relpath(path)
    return os.path.abspath(path) if rel.startswith("..") else rel


def plain(net):
    """VDD_{IO} -> VDD_IO, the way you'd type it."""
    return net.replace("{", "").replace("}", "")


def key(name):
    """Compare net names loosely: VDD_{IO}, VDD_IO and vddio are the same rail;
    +3V3, 3V3 and 3.3V are the same connector rail."""
    s = name.strip().strip("`").upper().replace("{", "").replace("}", "")
    s = s.replace("_", "").replace(" ", "").lstrip("+")
    m = re.match(r"^(\d+)\.(\d+)V$", s)
    if m:
        s = f"{m.group(1)}V{m.group(2)}"
    return s


def volts_of_net(net):
    """+3V3 -> 3.3, +5V -> 5.0, otherwise None."""
    m = re.match(r"^\+?(\d+)V(\d*)$", net.strip())
    if not m:
        return None
    return float(f"{m.group(1)}.{m.group(2) or 0}")


# --- What the board says ------------------------------------------------------------------

class Part:
    def __init__(self, fp):
        self.ref = prop(fp, "Reference", "?")
        self.value = prop(fp, "Value", "")
        self.attrs = flags(fp, "attr")
        self.fitted = "dnp" not in self.attrs
        self.pads = []
        for pad in children(fp, "pad"):
            fn = child(pad, "pinfunction")
            pt = child(pad, "pintype")
            self.pads.append({"num": pad[1], "net": net_name(pad),
                              "func": fn[1] if fn else "", "type": pt[1] if pt else ""})

    def nets(self):
        return [p["net"] for p in self.pads if p["net"]]


def board_facts(board_dir):
    pcbs = [f for f in os.listdir(board_dir) if f.endswith(".kicad_pcb")]
    if len(pcbs) != 1:
        raise SystemExit(f"check_notes: expected one .kicad_pcb in {board_dir}")
    pcb = load(os.path.join(board_dir, pcbs[0]))
    tb = child(pcb, "title_block")
    rev = date = ""
    if tb is not None:
        rev = (child(tb, "rev") or ["", ""])[1]
        date = (child(tb, "date") or ["", ""])[1]

    parts = {}
    for fp in children(pcb, "footprint"):
        p = Part(fp)
        parts.setdefault(p.ref, p)        # logos can repeat a reference; keep the first
    if CHIP not in parts:
        raise SystemExit(f"check_notes: no {CHIP} on the board")

    dnp = sorted((r for r, p in parts.items() if not p.fitted), key=natural)
    connectors = [p for p in parts.values() if p.fitted and p.ref.startswith("J")]
    connector_nets = set(n for p in connectors for n in p.nets())

    chip = parts[CHIP]
    rails = {}
    for pad in chip.pads:
        if pad["type"] == "power_in" and pad["net"] and pad["net"] != GROUND:
            rails.setdefault(pad["net"], []).append(pad["num"])

    def is_link(p):
        return len(p.pads) == 2 and p.value.strip().upper() in ("0", "0R", "0Ω", "0OHM")

    facts = {}
    for rail, pins in rails.items():
        caps = sorted((p.ref for p in parts.values()
                       if p.fitted and p.ref.startswith("C") and len(p.pads) == 2
                       and sorted(p.nets()) == sorted([rail, GROUND])), key=natural)
        path, net, volts, seen = [], rail, None, {rail}
        while net not in connector_nets:
            step = None
            for p in parts.values():
                if not p.fitted or p.ref == CHIP:
                    continue
                if is_link(p) and net in p.nets():
                    other = [n for n in p.nets() if n != net]
                    if other and other[0] not in seen:
                        step = (p, other[0])
                        break
                outs = [q for q in p.pads if q["func"] == "VOUT" and q["net"] == net]
                ins = [q for q in p.pads if q["func"] == "VIN"]
                if outs and ins and ins[0]["net"] not in seen:
                    step = (p, ins[0]["net"])
                    m = re.search(r"-(\d+(?:\.\d+)?)$", p.value)
                    if m and volts is None:
                        volts = float(m.group(1))
                    break
            if step is None:
                raise SystemExit(f"check_notes: couldn't follow {plain(rail)} back to a connector "
                                 f"(stuck at {plain(net)})")
            path.insert(0, step[0].ref)
            net = step[1]
            seen.add(net)
        if volts is None:
            volts = volts_of_net(net)
        facts[rail] = {"pins": sorted(pins, key=natural), "caps": caps, "path": path,
                       "source": net, "volts": volts}
    return {"file": os.path.join(board_dir, pcbs[0]), "rev": rev, "date": date,
            "parts": parts, "dnp": dnp, "rails": facts}


def natural(s):
    return [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", s)]


# --- What your notes say ------------------------------------------------------------------

def sections(text):
    """{'not fitted': '...', 'supply rails': '...', 'checks': '...'} from ## headings."""
    out, name, buf = {}, None, []
    for line in text.splitlines():
        m = re.match(r"^##\s+(.*?)\s*$", line)
        if m:
            if name is not None:
                out[name] = "\n".join(buf)
            name, buf = m.group(1).strip().lower(), []
        elif name is not None:
            buf.append(line)
    if name is not None:
        out[name] = "\n".join(buf)
    return out


def strip_comments(text):
    return re.sub(r"<!--.*?-->", "", text, flags=re.S)


def table(text):
    """A Markdown table as a list of dicts keyed by lower-case header."""
    rows = [l.strip() for l in text.splitlines() if l.strip().startswith("|")]
    if len(rows) < 2:
        return []
    cells = lambda l: [c.strip() for c in l.strip().strip("|").split("|")]
    head = [h.lower() for h in cells(rows[0])]
    out = []
    for l in rows[1:]:
        c = cells(l)
        if all(re.match(r"^:?-+:?$", x) for x in c if x):
            continue
        out.append(dict(zip(head, c + [""] * (len(head) - len(c)))))
    return out


def todo(cell):
    return not cell.strip() or "TODO" in cell.upper()


def refs_in(cell):
    return REF.findall(cell.upper())


def numbers_in(cell):
    return re.findall(r"\d+", cell)


# --- The check ----------------------------------------------------------------------------

def run_board_check(board_dir):
    """labs/common/check_board.py on the board, for the ERC and DRC counts by type."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as t:
        summary = t.name
    r = subprocess.run([sys.executable, os.path.join(COMMON, "check_board.py"), board_dir,
                        "--summary", summary, "--show", "0"],
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    data = {}
    if os.path.exists(summary) and os.path.getsize(summary):
        with open(summary) as f:
            data = json.load(f)
    os.unlink(summary)
    if r.returncode == 2 or not data:
        sys.stdout.write(r.stdout)
        raise SystemExit(2)
    return data


def main():
    ap = argparse.ArgumentParser(description="Check your Lab 01 notes against the SKY130 breakout.")
    ap.add_argument("notes", nargs="?", default=os.path.join(LAB, "breakout-notes.md"))
    ap.add_argument("--board", default=BOARD_DIR, help="the board folder (default: the fetched breakout)")
    ap.add_argument("--board-summary", help="reuse a check_board.py --summary file instead of running it "
                    "(selftest.py uses this to run the board check once)")
    args = ap.parse_args()

    if not os.path.isdir(args.board):
        print(f"check_notes: no board at {shown(args.board)}. Fetch it first:\n"
              f"  python3 labs/common/fetch_boards.py", file=sys.stderr)
        return 2
    if not os.path.exists(args.notes):
        print(f"check_notes: no notes file at {shown(args.notes)}", file=sys.stderr)
        return 2

    facts = board_facts(args.board)
    with open(args.notes, encoding="utf-8") as f:
        notes = sections(strip_comments(f.read()))

    print("PCB101 Lab 01 check")
    print(f"  notes     {shown(args.notes)}")
    print(f"  board     {shown(facts['file'])} (rev {facts['rev']}, {facts['date']})")
    print()

    rows = []          # (ok, label, message)

    # Not fitted
    dnp = set(facts["dnp"])
    fiducials = set(r for r in dnp if r.startswith("FID"))
    parts_only = dnp - fiducials
    text = notes.get("not fitted")
    if text is None:
        rows.append((False, "Not fitted", "no '## Not fitted' section"))
    else:
        theirs = set(refs_in(text))
        theirs_parts = theirs - fiducials
        missing = parts_only - theirs_parts
        extra = sorted(theirs_parts - dnp, key=natural)
        msgs = []
        if extra:
            unknown = [r for r in extra if r not in facts["parts"]]
            fitted = [r for r in extra if r in facts["parts"]]
            if fitted:
                msgs.append(f"{', '.join(fitted)} {'is' if len(fitted) == 1 else 'are'} not marked DNP")
            if unknown:
                msgs.append(f"no part called {', '.join(unknown)} on this board")
        if not theirs:
            msgs.append("TODO")
        elif missing:
            msgs.append(f"{len(missing)} of the {len(parts_only)} DNP parts are missing from your list")
        if msgs:
            rows.append((False, "Not fitted", "; ".join(msgs)))
        else:
            fid = " and the fiducials" if fiducials <= theirs else ""
            rows.append((True, "Not fitted", f"{len(parts_only)} parts{fid}"))

    # Supply rails
    rails_text = notes.get("supply rails")
    their_rows = {}
    if rails_text is None:
        rows.append((False, "Supply rails", "no '## Supply rails' section"))
    else:
        for r in table(rails_text):
            name = r.get("rail", "")
            if name and not todo(name):
                their_rows[key(name)] = r
    order = list(their_rows)
    for rail, f in sorted(facts["rails"].items(),
                          key=lambda kv: (order.index(key(kv[0])) if key(kv[0]) in order else 99, kv[0])):
        label = plain(rail)
        r = their_rows.get(key(rail))
        if rails_text is None:
            continue
        if r is None:
            rows.append((False, label, "no row for this rail"))
            continue
        msgs = []

        cell = r.get("chip pins", "")
        if todo(cell):
            msgs.append("Chip pins: TODO")
        else:
            theirs, truth = set(numbers_in(cell)), set(f["pins"])
            if theirs != truth:
                wrong = sorted(theirs - truth, key=natural)
                if wrong:
                    msgs.append(f"Chip pins: {', '.join(wrong)} {'is' if len(wrong) == 1 else 'are'} "
                                f"not on {label}")
                if truth - theirs:
                    msgs.append(f"Chip pins: {label} is on {len(truth)} of {CHIP}'s pins, and your row "
                                f"has {len(truth & theirs)} of them")

        cell = r.get("comes from", "")
        if todo(cell):
            msgs.append("Comes from: TODO")
        elif key(cell) != key(f["source"]):
            msgs.append(f"Comes from: the supply doesn't enter on '{cell}'")

        cell = r.get("through", "")
        if todo(cell):
            msgs.append("Through: TODO")
        else:
            theirs = [x for x in refs_in(cell) if not x.startswith("J")]
            truth = f["path"]
            if theirs != truth:
                dnp_named = [x for x in theirs if x in dnp]
                off = [x for x in theirs if x not in truth and x not in dnp]
                if dnp_named:
                    msgs.append(f"Through: {', '.join(dnp_named)} {'is' if len(dnp_named) == 1 else 'are'} "
                                f"marked DNP, so no current flows through {'it' if len(dnp_named) == 1 else 'them'}")
                if off:
                    msgs.append(f"Through: {', '.join(off)} {'is' if len(off) == 1 else 'are'} not on the "
                                f"way from the connector to {label}")
                if not dnp_named and not off:
                    if set(theirs) == set(truth):
                        msgs.append("Through: the right parts, but not in order from the connector to the chip")
                    else:
                        msgs.append(f"Through: the path passes through {len(truth)} fitted parts, and "
                                    f"your row has {len(set(theirs) & set(truth))} of them")

        cell = r.get("volts", "")
        if todo(cell):
            msgs.append("Volts: TODO")
        else:
            # 3.3, 3,3 V and the schematic's own 3V3 (or 1v8) all mean the same voltage
            v = re.sub(r"(\d+)[Vv](\d+)", r"\1.\2", cell.replace(",", "."))
            m = re.search(r"\d+(?:\.\d+)?", v)
            if not m or f["volts"] is None or abs(float(m.group(0)) - f["volts"]) > 0.05:
                msgs.append(f"Volts: {cell} isn't what reaches the chip")

        cell = r.get("capacitors", "")
        if todo(cell):
            msgs.append("Capacitors: TODO")
        else:
            theirs, truth = set(refs_in(cell)), set(f["caps"])
            extra = sorted(theirs - truth, key=natural)
            for x in extra:
                p = facts["parts"].get(x)
                if p is None:
                    msgs.append(f"Capacitors: no part called {x}")
                elif not x.startswith("C"):
                    msgs.append(f"Capacitors: {x} isn't a capacitor")
                else:
                    other = [plain(n) for n in p.nets() if n != GROUND]
                    msgs.append(f"Capacitors: {x} is on {', '.join(other) or '?'}, not {label}")
            if truth - theirs:
                msgs.append(f"Capacitors: {len(truth)} capacitors decouple {label}, and your row has "
                            f"{len(truth & theirs)} of them")

        if msgs:
            for i, m in enumerate(msgs):
                rows.append((False, label if i == 0 else "", m))
        else:
            rows.append((True, label, f"{len(f['pins'])} pins, from {plain(f['source'])} through "
                         f"{', '.join(f['path'])}, {f['volts']:g} V, {len(f['caps'])} capacitors"))
    for k, r in their_rows.items():
        if k not in [key(x) for x in facts["rails"]]:
            rows.append((False, r.get("rail", "?"), "isn't one of the chip's supply rails on this board"))

    # Checks
    checks_text = notes.get("checks")
    if checks_text is None:
        rows.append((False, "Checks", "no '## Checks' section"))
    else:
        if args.board_summary:
            with open(args.board_summary) as f:
                data = json.load(f)
        else:
            print("  running labs/common/check_board.py on the breakout (about a minute with one CPU) ...", flush=True)
            print()
            data = run_board_check(args.board)
        by_type, counts = data.get("by_type", {}), data.get("counts", {})
        want = {}
        for check in ("erc", "drc"):
            for sev in ("error", "excluded"):
                want[(check, sev, "all")] = counts.get(f"{check}.{sev}", 0)
                for k, n in by_type.items():
                    c, s, t = k.split(".", 2)
                    if c == check and s == sev:
                        want[(check, sev, t)] = n
        got, msgs = {}, []
        for r in table(checks_text):
            c, s, t, n = (r.get(h, "").strip().strip("`").lower() for h in ("check", "severity", "type", "count"))
            if c not in ("erc", "drc") or s not in ("error", "excluded"):
                continue                      # warnings depend on your setup; not checked
            t = t or "all"
            if todo(n) or not re.match(r"^\d+$", n):
                got[(c, s, t)] = None
                msgs.append(f"{c.upper()} {s} {t}: the count is {'TODO' if todo(n) else repr(n)}")
                continue
            got[(c, s, t)] = int(n)
            if t != "all" and int(n) and todo(r.get("what it means", "")):
                msgs.append(f"{c.upper()} {s} {t}: say what it means")
        required = [("erc", "error"), ("drc", "error"), ("drc", "excluded")]
        for c, s in [("erc", "error"), ("erc", "excluded"), ("drc", "error"), ("drc", "excluded")]:
            label = f"{c.upper()} {s}"
            k = (c, s, "all")
            if k not in got:
                if (c, s) in required:
                    msgs.append(f"{label} all: no row")
            elif got[k] is not None and got[k] != want[k]:
                msgs.append(f"{label} all: you have {got[k]}, and the check counts a different number")
            types = {t for (cc, ss, t), n in want.items() if cc == c and ss == s and t != "all" and n}
            listed = {t for (cc, ss, t) in got if cc == c and ss == s and t != "all"}
            for t in sorted(listed & types):
                if got[(c, s, t)] is not None and got[(c, s, t)] != want[(c, s, t)]:
                    msgs.append(f"{label} {t}: you have {got[(c, s, t)]}, and the check counts "
                                f"a different number")
            for t in sorted(listed - types):
                if got[(c, s, t)]:
                    msgs.append(f"{label} {t}: the check found none of these")
            if types - listed:
                msgs.append(f"{label}: the check finds {len(types)} type{'s' if len(types) > 1 else ''}, "
                            f"and your table has {len(types & listed)} of them")
        if msgs:
            for i, m in enumerate(msgs):
                rows.append((False, "Checks" if i == 0 else "", m))
        else:
            kinds = [f"{k[0].upper()} {k[1]} {k[2]} {n}" for k, n in sorted(want.items()) if k[2] != "all" and n]
            rows.append((True, "Checks", "; ".join(kinds) if kinds else "no errors"))

    for ok, label, msg in rows:
        print(f"  {'ok' if ok else 'MISMATCH':9} {label:13} {msg}")
    bad = sum(1 for ok, label, _ in rows if not ok and label)
    print()
    if bad:
        print(f"FAIL  {bad} of {sum(1 for _, label, _ in rows if label)} rows disagree with the board")
        return 1
    print(f"PASS  {shown(args.notes)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
