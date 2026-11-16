#!/usr/bin/env python3
"""PB101 bring-up plan check: is every part of BRINGUP.md filled in, and does every step say
what you expect to read?

    python3 labs/common/check_bringup.py BRINGUP.md

It needs only Python, so it runs with or without labs/common/kicad.sh. The plan must have
these sections, as level-2 headings, each with something in it:

  ## Lines that leave the board   a table with a row per line and no empty cells
  ## Settings                     a list; one item gives a current limit with its unit (mA or A)
  ## Before power                 a numbered list of checks, at least 2
  ## Steps                        a numbered list of steps, at least 4
  ## When a reading is wrong      what to do

Every numbered item under "Before power" and "Steps" must say "Expect" and give a value: a
number with a unit (Ω, kΩ, MΩ, V, mV, A, mA, µA, Hz, kHz, MHz, baud, s, ms, µs, %) or a byte
written in hex or binary (0xAA, 0b0000_0011), for a step whose result is a value read from the
chip. The word TODO anywhere fails the check, so the template fails as shipped.

Exit status: 0 PASS, 1 FAIL, 2 the file couldn't be read.
"""
import re
import sys

SECTIONS = ["Lines that leave the board", "Settings", "Before power", "Steps", "When a reading is wrong"]
MIN_ITEMS = {"Before power": 2, "Steps": 4}
UNIT = (r"(?:[kKMmµu]?(?:Ω|ohms?)|[kKM]?R\b|[mµu]?V\b|[mµu]?A\b|[kM]?Hz\b|baud\b|bit/s\b|"
        r"[mµun]?s\b|%)")
NUMBER = r"[-+]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?"
VALUE = re.compile(rf"(?:{NUMBER}\s*{UNIT}|\b0x[0-9A-Fa-f_]+\b|\b0b[01_]+\b)")


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
    """The numbered items in a section, each with its continuation lines."""
    items, cur = [], None
    for line in lines:
        if re.match(r"^\d+\.\s", line):
            cur = [line]
            items.append(cur)
        elif cur is not None and (line.startswith(" ") or line.startswith("\t")) and line.strip():
            cur.append(line)
        elif cur is not None and not line.strip():
            continue
        elif cur is not None:
            cur = None
    return [" ".join(s.strip() for s in it) for it in items]


def counted(items, one, many):
    """'line 3' or 'lines 3, 5': a label in the singular or plural, then the numbers."""
    return f"{one if len(items) == 1 else many} {', '.join(map(str, items))}"


def has_expect(item):
    """True if the item says Expect and gives a value after it."""
    m = re.search(r"(?i)\bexpect", item)
    return bool(m and VALUE.search(item[m.start():]))


def main():
    if len(sys.argv) != 2:
        print(__doc__.split("\n\n")[1], file=sys.stderr)
        return 2
    path = sys.argv[1]
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except OSError as e:
        print(f"check_bringup: {e}", file=sys.stderr)
        return 2

    rows = []
    secs = sections(text)
    todo = [i + 1 for i, line in enumerate(text.splitlines()) if "TODO" in line]
    rows.append((not todo, "TODO", "none left" if not todo else
                 f"{len(todo)} line{' still says' if len(todo) == 1 else 's still say'} TODO: "
                 f"{counted(todo[:8], 'line', 'lines')}"
                 + (" ..." if len(todo) > 8 else "")))
    for name in SECTIONS:
        body = secs.get(name)
        if body is None:
            rows.append((False, name, "section missing (a '## " + name + "' heading)"))
            continue
        content = [l for l in body if l.strip() and l.strip() != "TODO" and not l.strip().startswith("<!--")]
        if not content:
            rows.append((False, name, "empty"))
            continue
        if name == "Lines that leave the board":
            table = [l for l in content if l.strip().startswith("|")]
            data = [l for l in table[2:]] if len(table) > 2 else []
            empty = [i + 1 for i, l in enumerate(data)
                     if any(not c.strip() or c.strip() == "TODO" for c in l.strip().strip("|").split("|"))]
            if not data:
                rows.append((False, name, "no table rows"))
            elif empty:
                rows.append((False, name, f"{len(data)} rows; "
                                         f"{counted(empty, 'row', 'rows')} {'has' if len(empty) == 1 else 'have'} "
                                         "a cell that's empty or says TODO"))
            else:
                rows.append((True, name, f"{len(data)} rows, every cell filled in"))
        elif name == "Settings":
            limit = [l for l in content if re.search(r"(?i)current limit", l)]
            ok = any(re.search(rf"{NUMBER}\s*[mµu]?A\b", l) for l in limit)
            rows.append((ok, name, f"{len([l for l in content if l.strip().startswith(('-', '*'))])} items; "
                         + ("a current limit with its unit" if ok else "no 'current limit' item with a value in mA or A")))
        elif name in MIN_ITEMS:
            items = numbered(body)
            bad = [i + 1 for i, it in enumerate(items) if not has_expect(it)]
            if len(items) < MIN_ITEMS[name]:
                rows.append((False, name, f"{len(items)} numbered item{'' if len(items) == 1 else 's'}; "
                                          f"at least {MIN_ITEMS[name]} needed"))
            elif bad:
                rows.append((False, name, f"{len(items)} items; {counted(bad, 'item', 'items')} "
                             f"{'has' if len(bad) == 1 else 'have'} no 'Expect' with a value and its unit"))
            else:
                rows.append((True, name, f"{len(items)} items, each with an expected value and its unit"))
        else:
            rows.append((True, name, f"{len(content)} line{'' if len(content) == 1 else 's'}"))

    print("PB101 bring-up plan check")
    print(f"  file      {path}")
    print()
    for ok, what, detail in rows:
        print(f"  {'ok  ' if ok else 'FAIL'}  {what:27} {detail}")
    failed = sum(1 for ok, *_ in rows if not ok)
    print()
    print(f"{'PASS' if not failed else 'FAIL'}  {path}: {len(rows) - failed} of {len(rows)} parts ok")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
