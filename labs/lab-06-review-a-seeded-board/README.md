# Lab 06: Review a seeded board

Writeup: [`docs/labs/lab-06-review-a-seeded-board-overview.md`](../../docs/labs/lab-06-review-a-seeded-board-overview.md)
· live: <https://uoftasic.com/ic103/labs/lab-06-review-a-seeded-board-overview.html>

You review `board/`, a SimProc Pmod with faults planted in it, against the course checklist and write your findings in `REVIEW.md`; then you get a fabricator's quote for your own board and record it in `QUOTE.md`. Both files go in your board repository. Check them with:

```bash
cp -r ~/ic103/labs/lab-06-review-a-seeded-board/board ~/seeded-review          # a copy to open and poke at
cd ~/simproc-pmod                                                              # your board repository
cp ~/ic103/labs/lab-06-review-a-seeded-board/REVIEW.md ~/ic103/labs/lab-06-review-a-seeded-board/QUOTE.md .   # once
~/ic103/labs/lab-06-review-a-seeded-board/check.sh
```

`check.sh [FOLDER]` runs [`src/check_lab06.py`](src/check_lab06.py) on the folder (default: the current one) in the course's pinned KiCad image. It needs only Python and git there, and reads your board's outline and layers with [`labs/common/kicad_sexpr.py`](../common/kicad_sexpr.py). It prints one line per row of your findings table, then the review's rows and the quote's rows, and ends with `PASS` or `FAIL`. Exit status 0 is PASS, 1 FAIL, 2 couldn't run.

| Row | Passes when |
|---|---|
| TODO | `REVIEW.md` has no TODO left |
| findings | every row of the table under `## Findings` has Where, Line, What's wrong and What to change filled in |
| faults | at least 5 of the 8 planted faults are found: a row finds a fault when a word of its Where cell and its Line both match it, and each row finds at most one |
| fields | every field of `QUOTE.md` filled in, no TODO |
| values | a date written YYYY-MM-DD, a price with a number and a currency, a build time with a unit, a quantity, and the hash of a commit in this repository under Files uploaded |
| board | Layers equals your board's copper layers, and Board size is within 0.5 mm of your board's outline, either way round |

| Files | Last line of the check |
|---|---|
| `REVIEW.md` and `QUOTE.md` from here, as shipped | `FAIL  review FAIL (0 of 8 planted faults found); quote FAIL` |
| `solutions/simproc-pmod/REVIEW.md` and `QUOTE.md` | `PASS  review PASS (8 of 8 planted faults found); quote PASS` |

The key the check uses, `data/review-key.json`, holds only SHA-256 hashes of the words and lines that find each fault. That keeps the answers out of sight while you work; it won't stop someone who wants to guess, and the plain list is in `solutions/`, which you shouldn't open until you've finished.

## Files

| File | What it is |
|---|---|
| `board/` | the seeded board: a KiCad 10 project and its `BRINGUP.md`, written by `src/make_seeded.py` |
| `REVIEW.md`, `QUOTE.md` | the templates you copy into your repository |
| `check.sh` | the lab's check, on your board repository |
| `data/BRINGUP-seeded.md` | the seeded board's bring-up plan, which `make_seeded.py` copies into `board/` |
| `data/review-key.json` | the hashed key, written by `src/make_key.py` from `solutions/faults.json` |
| `solutions/` | the planted faults and a reference review and quote record; see its README |
| `src/make_seeded.py` | writes `board/` with Lab 03's generator, in the pinned image |
| `src/check_lab06.py` | the check itself |
| `src/selftest.py` | the seeded board and review records with known verdicts, for testing the checks themselves (8 of 8; in our runs it took 18 to 54 s with the container limited to one CPU) |
| `results/` | local outputs; never committed |

```bash
labs/common/kicad.sh python3 labs/lab-06-review-a-seeded-board/src/make_seeded.py labs/lab-06-review-a-seeded-board/board
python3 labs/lab-06-review-a-seeded-board/src/make_key.py
labs/common/kicad.sh python3 labs/lab-06-review-a-seeded-board/src/selftest.py
```
