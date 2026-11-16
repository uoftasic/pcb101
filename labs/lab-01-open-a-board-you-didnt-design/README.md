# Lab 01: Open a board you didn't design

Writeup: [`docs/labs/lab-01-open-a-board-you-didnt-design-overview.md`](../../docs/labs/lab-01-open-a-board-you-didnt-design-overview.md)
· live: <https://uoftasic.com/pb101/labs/lab-01-open-a-board-you-didnt-design-overview.html>

You read Tiny Tapeout's SKY130 QFN breakout (rev 3.2), which `labs/common/fetch_boards.py`
fetches into `labs/common/upstream/breakout-pcb/breakout-sky-qfn/`, and write what you find
in `breakout-notes.md`. Then the check compares your notes with the board. Run it from the
repo root:

```bash
python3 labs/common/fetch_boards.py          # once, if you haven't
labs/common/kicad.sh python3 labs/lab-01-open-a-board-you-didnt-design/src/check_notes.py
```

It takes about 20 s, most of it ERC and DRC on the breakout, and ends with `PASS` or `FAIL`.
On the shipped `breakout-notes.md`, which is all TODO, it prints `FAIL  5 of 5 rows disagree
with the board`.

## Files

| File | What it is |
|---|---|
| `breakout-notes.md` | the file you fill in: the parts that aren't fitted, the three supply rails, and the ERC and DRC counts |
| `src/check_notes.py` | the check; it works out its answers from the board file and from `labs/common/check_board.py`, and stores no answer key |
| `src/selftest.py` | five sets of notes with known verdicts, which show that the check checks |
| `solutions/breakout-notes.md` | the reference notes; open them after your own check says PASS |
| `results/` | local outputs; never committed |

`labs/common/kicad.sh python3 labs/lab-01-open-a-board-you-didnt-design/src/selftest.py`
runs the self-test in about 40 s and ends with `5 of 5 cases gave the expected verdict`.
