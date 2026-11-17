# Lab 05: Fab outputs in CI

Writeup: [`docs/labs/lab-05-fab-outputs-in-ci-overview.md`](../../docs/labs/lab-05-fab-outputs-in-ci-overview.md)
· live: <https://uoftasic.com/ic103/labs/lab-05-fab-outputs-in-ci-overview.html>

You copy `starter/` into your board repository, finish its build script, write a `.gitignore`, write KiBot's configuration, and push, so that GitHub Actions checks your board and builds its fabrication files, review images and KiBot's outputs on every push. Then you break the board on purpose and fix it. Check it with:

```bash
cd ~/simproc-pmod                                                   # your board repository
cp -r ~/ic103/labs/lab-05-fab-outputs-in-ci/starter/. .             # once
~/ic103/labs/lab-05-fab-outputs-in-ci/check.sh                      # Parts 1 to 5
~/ic103/labs/lab-05-fab-outputs-in-ci/check.sh --planted <commit>   # after Part 6
```

`check.sh [--planted REV]` runs your `ci/build.sh` the way your workflow does, in three containers. First [`src/check_ci.py`](src/check_ci.py) `--stage build` runs `ci/build.sh all` (the check, fab and images stages, in one container instead of three) in the course's pinned KiCad image, through `labs/common/kicad.sh`. If that passed, `labs/common/kibot.sh` runs `ci/build.sh kibot` in the pinned KiBot image; if it didn't, KiBot is skipped, as in the workflow. Then `check_ci.py --stage grade` prints one row per check and a last line, `PASS` or `FAIL`. Exit status 0 is PASS, 1 FAIL, 2 couldn't run.

| Row | Passes when |
|---|---|
| workflow | a workflow in `.github/workflows/` runs `ci/build.sh check`, `fab`, `images` and `kibot` and uploads `out/`, and `ci/kicad-image.txt` and `ci/kibot-image.txt` name their images by digest |
| check | `ci/build.sh check` passes: the board check finds no ERC or DRC errors, no unconnected items and no parity items |
| gerbers | `out/fab/` has a Gerber for F.Cu, B.Cu, both masks, both silkscreens and Edge.Cuts, and a `.gbrjob` |
| drill | a `.drl` in `out/fab/` whose holes all lie inside the outline drawn in the Edge.Cuts Gerber |
| bom | a `.csv` with `bom` in its name in `out/assembly/` that lists every footprint the board puts in a BOM |
| position | a `.csv` with `pos` in its name in `out/assembly/`, KiCad's CSV format, with every part at its position on the board in mm |
| images | `out/review/` has a PNG with `top` and one with `bottom` in its name, an SVG with `F_Cu` and one with `B_Cu`, and a PDF |
| ibom | an interactive HTML BOM under `out/kibot/` whose BOM lists every footprint the board puts in a BOM, none marked DNP, and nothing that isn't on the board ([`src/ibom.py`](src/ibom.py) reads the page's board data) |
| report | a KiBot design report under `out/kibot/` whose board size matches the outline in the Edge.Cuts Gerber and whose drill tools add up to the holes in the drill file |
| gitignore | after the build `git status` lists no untracked files, and git tracks none of KiCad's local files |
| planted | with `--planted REV`: REV is an earlier commit on your branch, and `ci/build.sh check` fails there with a board check verdict |

| Repository | Last line of the check |
|---|---|
| Lab 04's `solutions/simproc-pmod/` with `starter/` copied in | `FAIL  pmod: 3 of 10 Lab 05 checks ok; add --planted REV once you've done Part 6` |
| the same with `solutions/simproc-pmod/` instead, after the planted commit and its fix | `PASS  pmod: 11 of 11 Lab 05 checks ok` |

`check_ci.py` run on its own, without `--stage`, builds and checks in one container and leaves out the KiBot rows and KiBot's part of the workflow row. The capstone's check runs it that way.

## Files

| File | What it is |
|---|---|
| `check.sh` | the lab's check, on your board repository |
| `starter/` | what you copy into your repository: `.github/workflows/board.yml`, `ci/build.sh` with five TODOs, `ci/board.kibot.yaml` with three, `ci/check_board.py` (a copy of [`labs/common/check_board.py`](../common/check_board.py)), `ci/kicad-image.txt` and `ci/kibot-image.txt` |
| `solutions/` | the files Lab 05 adds to Lab 04's reference board, finished; see its README |
| `src/check_ci.py` | the check itself |
| `src/ibom.py` | reads the board data out of an interactive HTML BOM; run on its own, it prints the BOM's rows |
| `src/planted.py` | the error the self-test plants: Lab 04's +3V3 track along the top edge dragged 1 mm down |
| `src/run_workflow.py` | runs a workflow's steps on this machine, the way a GitHub runner would; we used it to test the workflow without pushing |
| `src/selftest.py` | repositories with known verdicts, for testing the check itself; it runs `check.sh` in each, so it runs on the host |
| `results/` | local outputs; never committed |

```bash
python3 labs/lab-05-fab-outputs-in-ci/src/selftest.py                           # 12 of 12
python3 labs/lab-05-fab-outputs-in-ci/src/run_workflow.py labs/lab-05-fab-outputs-in-ci/results/selftest/reference
```

The first command is the self-test, which needs Python, git and Docker on the host, because every case runs `check.sh` and so starts containers of both images. In our run, with `IC103_DOCKER_ARGS="--cpus 1 --memory 2g"`, it took 201 s for its 12 cases: the copies of `check_board.py`, `kicad-image.txt` and `kibot-image.txt` in `starter/` and `solutions/` (6), the starter, the reference with its planted commit named, the planted commit, the reference with a good commit named, the reference with J4 marked DNP, and the same with the ibom's `dnf_filter` taken out, which must fail the `ibom` row. The second command needs the first to have built `results/selftest/reference`, and Python with PyYAML and Docker on the host. It runs the workflow's own `docker run` lines, so to limit them as we did, we put a `docker` on the `PATH` that adds `--cpus 1 --memory 2g` to `docker run`. On that repository it ran all seven steps in 30 s and copied 23 files into the artifact; on `results/selftest/planted` the board check step exited 1, the three steps after it were skipped, and the upload step copied the three reports.
