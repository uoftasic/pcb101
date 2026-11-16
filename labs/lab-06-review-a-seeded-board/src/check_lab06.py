#!/usr/bin/env python3
"""PB101 Lab 06 check: does your review find the planted faults, and does your quote record
describe your own board?

    labs/common/kicad.sh python3 /w/labs/lab-06-review-a-seeded-board/src/check_lab06.py REPO

Run it through the lab's check.sh, from your board repository. REPO (default: the current
folder) holds REVIEW.md, QUOTE.md and your board's KiCad project.

REVIEW.md is your review of the seeded board. Each row of its findings table names where the
fault is (a reference designator, or a file) and the checklist line it breaks. A row finds a
planted fault when a word of its Where cell and its Line both match that fault; each row can
find one fault, and each fault needs a row of its own. The review passes with at least 5 of
the 8 planted faults found, every row filled in, and no TODO left. The key is
data/review-key.json, which holds only hashes; see src/make_key.py.

QUOTE.md is the fabricator's quote for your own board. It passes with every field filled in
and no TODO, a date written YYYY-MM-DD, a price with a currency, a build time with a unit, a
whole-number quantity, a commit hash that this repository has, a layer count equal to your
board's copper layers, and a board size within 0.5 mm of your board's outline.

Exit status: 0 PASS, 1 FAIL, 2 the check couldn't run.
"""
import glob
import hashlib
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(LAB, "..", "common"))
from kicad_sexpr import parse, children, child  # noqa: E402

NEEDED = 5
FIELDS = ["Fabricator", "Date", "Account needed to see the price", "Files uploaded", "Board size",
          "Layers", "Thickness, finish and colour", "Quantity", "Price", "Build time",
          "Shipping to Toronto", "DFM"]


# --------------------------------------------------------------------------------------
# The review

def table_rows(text):
    """The data rows of the first Markdown table under '## Findings', as lists of cells."""
    m = re.search(r"^##\s+Findings\s*$(.*?)(?=^##\s|\Z)", text, re.M | re.S)
    if not m:
        return None
    lines = [l.strip() for l in m.group(1).splitlines() if l.strip().startswith("|")]
    rows = []
    for l in lines[2:]:
        cells = [c.strip() for c in l.strip("|").split("|")]
        rows.append(cells)
    return rows


def words(where):
    w = where.lower().replace("`", "")
    toks = re.findall(r"[a-z0-9_.+\-]+", w)
    toks = [t.strip(".") for t in toks] + toks
    toks += [f"{a} {b}" for a, b in zip(toks, toks[1:])]
    return set(t for t in toks if t)


def check_review(path, rows_out):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    with open(os.path.join(LAB, "data", "review-key.json")) as f:
        key = json.load(f)
    salt, faults = key["salt"], [set(h) for h in key["faults"]]

    todo = [i + 1 for i, l in enumerate(text.splitlines()) if "TODO" in l]
    rows_out.append((not todo, "TODO", "none left" if not todo else
                     f"{len(todo)} line(s) still say TODO: line {', '.join(map(str, todo[:8]))}"))
    rows = table_rows(text)
    if rows is None:
        rows_out.append((False, "findings", "no '## Findings' section with a table"))
        return []
    found, notes, bad = set(), [], []
    for i, cells in enumerate(rows, 1):
        if len(cells) < 5 or any(not c or c == "TODO" for c in cells[1:5]):
            bad.append(i)
            notes.append((i, "?", "?", "a cell is empty or says TODO"))
            continue
        where, line_cell = cells[1], cells[2]
        m = re.search(r"\b(10|[1-9])\b", line_cell)
        if not m:
            bad.append(i)
            notes.append((i, where, line_cell, "the Line cell needs a checklist line number, 1 to 10"))
            continue
        line = int(m.group(1))
        hashes = {hashlib.sha256(f"{salt}|{w}|{line}".encode()).hexdigest() for w in words(where)}
        hit = next((k for k, fh in enumerate(faults) if k not in found and hashes & fh), None)
        if hit is not None:
            found.add(hit)
            notes.append((i, where, line, "finds a planted fault"))
        elif any(hashes & fh for fh in faults):
            notes.append((i, where, line, "finds a fault another row already found"))
        else:
            notes.append((i, where, line, "doesn't find a planted fault"))
    rows_out.append((not bad and bool(rows), "findings",
                     f"{len(rows)} row(s), each with where, a line, what's wrong and what to change" if not bad
                     else f"row(s) {', '.join(map(str, bad))} incomplete"))
    rows_out.append((len(found) >= NEEDED, "faults",
                     f"{len(found)} of {len(faults)} planted faults found ({NEEDED} needed)"))
    return notes


# --------------------------------------------------------------------------------------
# The quote

def board_facts(repo):
    pros = glob.glob(os.path.join(repo, "*.kicad_pro"))
    if len(pros) != 1:
        return None, None, f"{len(pros)} .kicad_pro files in the folder"
    pcb = pros[0][:-len(".kicad_pro")] + ".kicad_pcb"
    with open(pcb, encoding="utf-8") as f:
        root = parse(f.read())
    layers = child(root, "layers") or []
    copper = [l for l in layers[1:] if isinstance(l, list) and len(l) > 1
              and isinstance(l[1], str) and l[1].endswith(".Cu")]
    xs, ys = [], []
    for kind in ("gr_rect", "gr_line", "gr_arc", "gr_circle", "gr_poly"):
        for g in children(root, kind):
            layer = child(g, "layer")
            if not layer or layer[1] != "Edge.Cuts":
                continue
            for tag in ("start", "end", "mid", "center"):
                p = child(g, tag)
                if p:
                    xs.append(float(p[1]))
                    ys.append(float(p[2]))
            pts = child(g, "pts")
            for p in children(pts, "xy") if pts else []:
                xs.append(float(p[1]))
                ys.append(float(p[2]))
    if not xs:
        return len(copper), None, "no outline on Edge.Cuts"
    return len(copper), (round(max(xs) - min(xs), 3), round(max(ys) - min(ys), 3)), ""


def check_quote(path, repo, rows_out):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    fields = {}
    for line in text.splitlines():
        m = re.match(r"^\s*[-*]\s+([^:]+):\s*(.*)$", line)
        if m:
            fields[m.group(1).strip()] = m.group(2).strip()
    todo = [i + 1 for i, l in enumerate(text.splitlines()) if "TODO" in l]
    missing = [f for f in FIELDS if not fields.get(f)]
    rows_out.append((not todo and not missing, "fields",
                     "every field filled in, no TODO" if not todo and not missing else
                     (f"missing or empty: {', '.join(missing)}" if missing else "")
                     + ("; " if missing and todo else "")
                     + (f"{len(todo)} line(s) still say TODO" if todo else "")))
    if missing:
        return
    bad = []
    if not re.search(r"\b20\d\d-\d\d-\d\d\b", fields["Date"]):
        bad.append("the date isn't written YYYY-MM-DD")
    if not (re.search(r"\d", fields["Price"]) and re.search(r"(\$|USD|CAD|EUR|€|£|GBP|CNY|¥)", fields["Price"])):
        bad.append("the price needs a number and its currency")
    if not re.search(r"\d+(\.\d+)?\s*(h\b|hours?|days?|business days?|weeks?)", fields["Build time"], re.I):
        bad.append("the build time needs a number and a unit (hours or days)")
    if not re.search(r"\b\d+\b", fields["Quantity"]):
        bad.append("the quantity needs a number")
    shas = re.findall(r"\b[0-9a-f]{7,40}\b", fields["Files uploaded"])
    known = [s for s in shas if subprocess.run(["git", "cat-file", "-e", s + "^{commit}"], cwd=repo,
                                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0]
    if not known:
        bad.append("Files uploaded doesn't give the hash of a commit in this repository")
    rows_out.append((not bad, "values", "date, price, build time, quantity and commit all readable" if not bad
                     else "; ".join(bad)))

    layers, size, why = board_facts(repo)
    if size is None:
        rows_out.append((False, "board", f"can't read your board: {why}"))
        return
    got_layers = re.findall(r"\d+", fields["Layers"])
    nums = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", fields["Board size"])]
    probs = []
    if not got_layers or int(got_layers[0]) != layers:
        probs.append(f"Layers says {fields['Layers']!r}; your board has {layers} copper layers")
    w, h = size
    if len(nums) < 2 or not any(abs(a - w) <= 0.5 and abs(b - h) <= 0.5 for a, b in ((nums[0], nums[1]), (nums[1], nums[0]))):
        probs.append(f"Board size says {fields['Board size']!r}; your board's outline is {w:g} x {h:g} mm")
    rows_out.append((not probs, "board", f"{layers} layers and {w:g} x {h:g} mm, as your board has" if not probs
                     else "; ".join(probs)))


def main():
    repo = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else ".")
    review, quote = os.path.join(repo, "REVIEW.md"), os.path.join(repo, "QUOTE.md")
    lost = [os.path.basename(p) for p in (review, quote) if not os.path.exists(p)]
    if lost:
        print(f"check_lab06: no {' or '.join(lost)} in {repo}; copy the lab's templates in first", file=sys.stderr)
        return 2

    print("PB101 Lab 06 check")
    print(f"  folder    {repo}")
    print()
    rrows = []
    notes = check_review(review, rrows)
    print("  REVIEW.md")
    for i, where, line, what in notes:
        print(f"    row {i:<3} {str(where)[:28]:28} line {str(line):3} {what}")
    print()
    for ok, what, detail in rrows:
        print(f"  {'ok  ' if ok else 'FAIL'}  {what:9} {detail}")
    print()
    qrows = []
    check_quote(quote, repo, qrows)
    print("  QUOTE.md")
    for ok, what, detail in qrows:
        print(f"  {'ok  ' if ok else 'FAIL'}  {what:9} {detail}")
    print()
    rv = all(ok for ok, *_ in rrows)
    qv = all(ok for ok, *_ in qrows)
    found = next((d for ok, w, d in rrows if w == "faults"), "")
    print(f"{'PASS' if rv and qv else 'FAIL'}  review {'PASS' if rv else 'FAIL'} ({found.split(' (')[0]}); "
          f"quote {'PASS' if qv else 'FAIL'}")
    return 0 if rv and qv else 1


if __name__ == "__main__":
    sys.exit(main())
