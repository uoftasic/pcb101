# Lab 05: Fab outputs in CI

Writeup: [`docs/labs/lab-05-fab-outputs-in-ci-overview.md`](../../docs/labs/lab-05-fab-outputs-in-ci-overview.md)
· live: <https://uoftasic.com/pb101/labs/lab-05-fab-outputs-in-ci-overview.html>

You copy `starter/` into your board repository, finish its build script, write a `.gitignore`, and push, so that GitHub Actions checks your board and builds its fabrication files and review images on every push. Then you break the board on purpose and fix it. Check it with:

```bash
cd ~/simproc-pmod                                                   # your board repository
cp -r ~/pb101/labs/lab-05-fab-outputs-in-ci/starter/. .             # once
~/pb101/labs/lab-05-fab-outputs-in-ci/check.sh                      # Parts 1 to 4
~/pb101/labs/lab-05-fab-outputs-in-ci/check.sh --planted <commit>   # after Part 5
```

`check.sh [--planted REV]` runs [`src/check_ci.py`](src/check_ci.py) in the course's pinned KiCad image, through `labs/common/kicad.sh`. It runs your `ci/build.sh all` (the same script and stages your workflow runs, in one container instead of three), prints its output, then one row per check and a last line, `PASS` or `FAIL`. Exit status 0 is PASS, 1 FAIL, 2 couldn't run.

| Row | Passes when |
|---|---|
| workflow | a workflow in `.github/workflows/` runs `ci/build.sh check`, `fab` and `images` and uploads `out/`, and `ci/kicad-image.txt` names the image by its digest |
| check | `ci/build.sh check` passes: the board check finds no ERC or DRC errors, no unconnected items and no parity items |
| gerbers | `out/fab/` has a Gerber for F.Cu, B.Cu, both masks, both silkscreens and Edge.Cuts, and a `.gbrjob` |
| drill | a `.drl` in `out/fab/` whose holes all lie inside the outline drawn in the Edge.Cuts Gerber |
| bom | a `.csv` with `bom` in its name in `out/assembly/` that lists every footprint the board puts in a BOM |
| position | a `.csv` with `pos` in its name in `out/assembly/`, KiCad's CSV format, with every part at its position on the board in mm |
| images | `out/review/` has a PNG with `top` and one with `bottom` in its name, an SVG with `F_Cu` and one with `B_Cu`, and a PDF |
| gitignore | after the build `git status` lists no untracked files, and git tracks none of KiCad's local files |
| planted | with `--planted REV`: REV is an earlier commit on your branch, and `ci/build.sh check` fails there with a board check verdict |

| Repository | Last line of the check |
|---|---|
| Lab 04's `solutions/simproc-pmod/` with `starter/` copied in | `FAIL  pmod: 3 of 8 Lab 05 checks ok; add --planted REV once you've done Part 5` |
| the same with `solutions/simproc-pmod/` instead, after the planted commit and its fix | `PASS  pmod: 9 of 9 Lab 05 checks ok` |

## Files

| File | What it is |
|---|---|
| `check.sh` | the lab's check, on your board repository |
| `starter/` | what you copy into your repository: `.github/workflows/board.yml`, `ci/build.sh` with five TODOs, `ci/check_board.py` (a copy of [`labs/common/check_board.py`](../common/check_board.py)) and `ci/kicad-image.txt` |
| `solutions/` | the files Lab 05 adds to Lab 04's reference board, finished; see its README |
| `src/check_ci.py` | the check itself |
| `src/planted.py` | the error the self-test plants: Lab 04's +3V3 track along the top edge dragged 1 mm down |
| `src/run_workflow.py` | runs a workflow's steps on this machine, the way a GitHub runner would; we used it to test the workflow without pushing |
| `src/selftest.py` | repositories with known verdicts, for testing the check itself |
| `results/` | local outputs; never committed |

```bash
labs/common/kicad.sh python3 labs/lab-05-fab-outputs-in-ci/src/selftest.py     # 8 of 8
python3 labs/lab-05-fab-outputs-in-ci/src/run_workflow.py labs/lab-05-fab-outputs-in-ci/results/selftest/reference
```

The first command is the self-test. In our runs it took about 5 to 6 min with the container limited to one CPU. The second needs the first to have built `results/selftest/reference`, and Python with PyYAML and Docker on the host. On that repository it ran all six steps in 11 s and copied 21 files into the artifact; on `results/selftest/planted` the board check step exited 1, the two steps after it were skipped, and the upload step copied the three reports.
