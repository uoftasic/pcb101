# `labs/common`: the pinned KiCad, the board check and Tiny Tapeout's boards

Every PB101 lab uses the files in this folder. They run KiCad's command-line program, `kicad-cli`, in one pinned build of KiCad's official Docker image, check a board with it, and fetch the Tiny Tapeout boards the labs open. Students draw in their own KiCad ([Getting started](https://uoftasic.com/pb101/guide/getting-started.html)); everything here is for checking and doesn't need KiCad installed on your machine, only Docker. The fetch script also needs git and Python 3, or you can run it in the image.

```bash
python3 labs/common/fetch_boards.py
labs/common/kicad.sh python3 labs/common/check_board.py labs/common/upstream/breakout-pcb/breakout-sky-qfn
```

The first command fetches the boards (84 MB, about 7 s). The second checks Tiny Tapeout's SKY130 breakout in about 30 s, and ends like this:

```text
                errors  warnings  excluded
  ERC               10       103         0
  DRC                0       123         1
  unconnected        0         0         0
  parity             0         0         0
...
FAIL  erc.error: 10 (want 0)
```

That FAIL is correct. The breakout has 10 ERC errors in KiCad 10.0.8, and the check below explains the rest of its output.

## Files

| File | What it is |
|---|---|
| `kicad-image.txt` | the pinned image, `kicad/kicad:10.0.8@sha256:3f4a01786dfbe803a65f345c3342b765db9add913f5e9448f8356793714ddc34`; every other script reads it from here |
| `kicad.sh` | runs any command in the pinned image, as your uid, with the repo mounted |
| `image-entry.sh` | runs inside the image before the command, and gives your uid the image's default library tables |
| `check_board.py` | the board check: ERC, DRC, unconnected items and schematic parity, with PASS or FAIL |
| `check_solutions.py` | runs the board check on every lab's reference solution; CI runs this |
| `kicad_sexpr.py` | a small reader for KiCad's S-expression files, which the lab checkers use instead of KiCad's `pcbnew` Python module |
| `selftest_check.py`, `selftest/` | four boards with known verdicts, which show that the check checks |
| `fetch_boards.py`, `upstream.json` | fetches Tiny Tapeout's boards and libraries at pinned commits |
| `upstream/` | where the fetched boards go; gitignored |
| `results/` | reports from `check_solutions.py`; gitignored |

## The pinned image: `kicad.sh`

```bash
labs/common/kicad.sh kicad-cli version                       # 10.0.8
labs/common/kicad.sh kicad-cli pcb drc --format json -o drc.json board.kicad_pcb
labs/common/kicad.sh python3 labs/common/check_board.py board.kicad_pro
```

`kicad.sh` runs its arguments as a command in `kicad/kicad:10.0.8`, named by digest, so it's the same build on every machine whatever tag Docker Hub moves later. It pulls the image the first time (812 MB to download, 2.6 GB on disk). Before each run it prints the digest Docker resolved, which is the record of exactly which KiCad ran:

```text
pb101: KiCad image kicad/kicad@sha256:3f4a01786dfbe803a65f345c3342b765db9add913f5e9448f8356793714ddc34
```

The repo root is mounted at `/w`, and the command runs in the folder that matches your current one, so relative paths work the same inside and outside. The container runs as your uid, so any files it writes are yours, and it's removed when the command ends. Set `PB101_DOCKER_ARGS` to add `docker run` flags (we ran everything here with `--cpus 1 --memory 2g`), and `PB101_QUIET=1` to drop the digest line.

Running as your uid means starting with an empty home folder, and so with no KiCad library tables. Without them, ERC and DRC report every standard library as missing, and the SKY130 breakout's ERC warnings go from 103 to 236 and its DRC warnings from 123 to 130 (the errors stay 10 and 0). The image's own user, `kicad`, has the two tables in `/home/kicad/.config/kicad/10.0/`, but that folder is readable only by `kicad`. Its `fp-lib-table` and `sym-lib-table` are byte-for-byte the defaults KiCad ships in `/usr/share/kicad/template/` (we compared them with `cmp`), so `image-entry.sh` copies those. Every run then sees the same libraries as the image's default user, whoever runs it.

`kicad.sh` is a bash script, for Linux, macOS and WSL. Without bash, the plain `docker run` below does the same check. It runs as the image's own user, which already has the library tables, and on Linux it printed the same counts as `kicad.sh`. We haven't run it on Windows.

```bash
docker run --rm -v "${PWD}:/w" -w /w kicad/kicad:10.0.8@sha256:3f4a01786dfbe803a65f345c3342b765db9add913f5e9448f8356793714ddc34 python3 labs/common/check_board.py labs/common/upstream/breakout-pcb/breakout-sky-qfn
```

## The board check: `check_board.py`

```bash
labs/common/kicad.sh python3 labs/common/check_board.py PROJECT [--expect FILE] [--reports DIR] [--summary FILE] [--no-refill] [--show N]
```

`PROJECT` is a `.kicad_pro`, `.kicad_sch` or `.kicad_pcb`, or a folder with exactly one `.kicad_pro` in it. The schematic and the board must have the project's name, as KiCad saves them. The check runs two `kicad-cli` reports with every severity included:

```text
kicad-cli sch erc --format json --severity-all --units mm
kicad-cli pcb drc --format json --severity-all --schematic-parity --refill-zones --units mm
```

It then counts the JSON. Each item is counted under its check (ERC, DRC, unconnected or parity) and its severity (error or warning), except that an item the designer marked as excluded in KiCad is counted as excluded, whatever its severity, and never fails the check. The output lists every error (the first 20 of each check unless you pass `--show`), the warnings by type, and then PASS or FAIL.

With no expectations file the check PASSes when there are no ERC errors, no DRC errors, no unconnected items, and no parity items at all. Parity warnings fail it too, because KiCad reports parity problems as warnings in every project we checked, including a footprint that is in the schematic and missing from the board (`missing_footprint`). A check that ignored warnings would pass that board.

DRC refills the zones first, so a board saved with stale zones is checked as it would be after refilling; `--no-refill` checks the zones as saved. Neither changes the board file (its SHA-256 was the same after the check). `kicad-cli` does write a `.kicad_prl` file of local settings next to the project.

| Exit status | Means |
|---|---|
| 0 | PASS |
| 1 | FAIL; each failed rule is printed as `FAIL  <key>: <count> (want <n>)` |
| 2 | the check couldn't run: a file is missing, `kicad-cli` isn't on the path, or `kicad-cli` couldn't load the design |

`--reports DIR` keeps `erc.json` and `drc.json`, and `--summary FILE` writes the counts, the verdict, the KiCad version and the image as JSON.

### Expected counts: `check-expect.json`

A board that has errors on purpose, such as a board with planted faults for a review lab, carries its expected counts in a `check-expect.json` next to its `.kicad_pro` (or a file named with `--expect`). Each key is `<check>.<severity>` or `<check>.<severity>.<type>`, where the check is `erc`, `drc`, `unconnected` or `parity` and the severity is `error`, `warning` or `excluded`. The check PASSes only if every listed count matches exactly, and anything not listed isn't checked. [`selftest/sky-breakout-expect.json`](selftest/sky-breakout-expect.json) is the example:

```json
{
  "erc.error": 10,
  "erc.error.power_pin_not_driven": 8,
  "erc.error.pin_to_pin": 2,
  "erc.warning": 103,
  "drc.error": 0,
  "drc.warning": 123,
  "drc.excluded": 1,
  "drc.excluded.courtyards_overlap": 1,
  "unconnected.error": 0,
  "parity.error": 0,
  "parity.warning": 0
}
```

### Tiny Tapeout's boards in the check

Counts from `check_board.py` through `kicad.sh`, at the commits in `upstream.json`, on November 16, 2026:

| Board | ERC errors | ERC warnings | DRC errors | DRC warnings | DRC excluded | Parity |
|---|---|---|---|---|---|---|
| `breakout-pcb/breakout-sky-qfn` | 10 | 103 | 0 | 123 | 1 | 0 |
| `breakout-pcb/dip-dock` | 2 | 44 | 0 | 159 | 6 | 3 warnings |
| `tt-demo-pcb` (`tinytapeout-demo`) | 8 | 103 | 0 | 277 | 8 | 5 warnings |

None has unconnected items. By type:

- SKY130 breakout. ERC errors: `power_pin_not_driven` 8, `pin_to_pin` 2. ERC warnings: `lib_symbol_mismatch` 69, `lib_symbol_issues` 22, `isolated_pin_label` 11, `multiple_net_names` 1. DRC warnings: `lib_footprint_issues` 76, `lib_footprint_mismatch` 47. Excluded: one `courtyards_overlap`.
- DIP dock. ERC errors: `power_pin_not_driven` 2. Parity: `duplicate_footprints` 1 and `extra_footprint` 2, all for the logo footprint `PSYLOGO01`. DRC warnings: `lib_footprint_issues` 111, `lib_footprint_mismatch` 48. Excluded: six `courtyards_overlap`.
- Demo board. ERC errors: `pin_not_connected` 4, `power_pin_not_driven` 3, `pin_to_pin` 1. Parity: `footprint_symbol_field_mismatch` 2 (a DigiKey part number on J2 and J3), `missing_footprint` 1 (J17), `extra_footprint` 2 (the logos `PSYLOGO` and `PSYLOGOB`). DRC warnings: `lib_footprint_issues` 166, `lib_footprint_mismatch` 111. Excluded: six `courtyards_overlap` and two `items_not_allowed`.

So none of Tiny Tapeout's boards passes the check as it stands, which is one reason a lab's "You're done when" always runs it on the student's own board.

## The self-test: `selftest_check.py`

```bash
labs/common/kicad.sh python3 labs/common/selftest_check.py
```

```text
ok   pic_programmer as shipped                    PASS  
ok   pic_programmer, one footprint deleted        FAIL  parity.warning.missing_footprint = 1
ok   pic_programmer, GND track across VCC         FAIL  drc.error = 2
ok   SKY130 breakout against its expected counts  PASS  
4 of 4 cases gave the expected verdict
```

`pic_programmer` is one of the demo projects that ship in the image (`/usr/share/kicad/demos/`), and of the ones we ran it's one of three that pass as shipped. The test copies it and breaks the copy in two ways: it deletes the first footprint from the board, and it lays a 0.25 mm GND track across a 0.8 mm VCC track. The last case needs the fetched boards, and is skipped without them. The whole run took 69 s.

## Reference solutions and CI

A lab's reference solution is a KiCad project anywhere under `labs/<lab-id>/solutions/`. `check_solutions.py` finds every `.kicad_pro` there, runs the board check on each (reading its `check-expect.json` if it has one), keeps the reports in `results/<lab-id>/<project>/`, and prints a table. With no solutions yet it prints `No reference solutions yet: nothing matches labs/*/solutions/**/*.kicad_pro.` and exits 0.

[`.github/workflows/labs.yml`](../../.github/workflows/labs.yml) runs, on every change to `labs/**`, once a week and by hand: it pulls the pinned image, fetches the boards, runs the self-test, then runs `check_solutions.py` and uploads the reports. It calls `kicad.sh` like everyone else rather than running as a job `container:`, so CI sees the same user setup and library tables as the counts on the lab pages.

## Tiny Tapeout's boards: `fetch_boards.py`

```bash
python3 labs/common/fetch_boards.py                 # everything in upstream.json
python3 labs/common/fetch_boards.py breakout-pcb    # one source
python3 labs/common/fetch_boards.py --list          # sources, commits and licences
labs/common/kicad.sh python3 labs/common/fetch_boards.py   # the same, in the image
```

The labs open Tiny Tapeout's own board files, and this repo doesn't store copies of them. `fetch_boards.py` checks each source in `upstream.json` out at a pinned commit into `upstream/`, using git's partial clone and sparse checkout so that only the files a lab needs are downloaded. A source that is already at its commit is left alone, so running it again is quick. If you have changed a fetched file (by saving a board in KiCad, say), it stops and tells you which file, and `--force` puts the pinned version back. Untracked files, such as the backups and `.kicad_prl` files KiCad writes next to a board you open, don't count as changes.

| Source | Commit | Date | Licence | Size | Used for |
|---|---|---|---|---|---|
| `TinyTapeout/breakout-pcb` | `91a2bf1` | 2026-10-29 | Apache-2.0 | 21.0 MB | the SKY130 QFN breakout (Lab 01), the IHP breakout's QFN-64 footprint (Lab 02), the DIP dock (Lab 03's closest reference) |
| `TinyTapeout/tinytapeout-kicad-libs` | `0e99691` | 2026-10-24 | Apache-2.0 | 28.5 MB | Tiny Tapeout's symbols and footprints, placed where the boards' library tables look for them |
| `TinyTapeout/tt-demo-pcb` | `bbf3dd1` | 2026-08-29 | Apache-2.0 (board), CC0 (documentation) | 12.8 MB | the RP2350 demo board |
| `TinyTapeout/kicad-tinytapeout-pmod-lib` | `9ee6345` | 2024-07-10 | Apache-2.0 | 0.4 MB | Tiny Tapeout's Pmod connector footprints (Lab 03) |
| `TinyTapeout/pcb-files` | `ca5fd72` | 2026-09-19 | no licence file | 0.3 MB | the production BOM for the SKY130 breakout rev 3.2 (Lab 01) |

`upstream.json` has the full commit hashes, the exact paths fetched from each repository, and what each one is for. `pcb-files` has no licence file, so it is fetched for reading only. The others are Apache-2.0, which would allow copying them into the repo with their notices, but fetching keeps the repo small and makes it obvious which upstream commit every count in the course comes from.

`tinytapeout-kicad-libs` goes inside `upstream/breakout-pcb/`, because the breakouts' library tables look for it at `${KIPRJMOD}/../tinytapeout-kicad-libs` and the demo board's at `${KIPRJMOD}/../breakout-pcb/tinytapeout-kicad-libs`, and that one folder satisfies both. `breakout-pcb`'s `.gitmodules` points that submodule at `psychogenic/tinytapeout-kicad-libs`. The same commit is in `TinyTapeout/tinytapeout-kicad-libs`, which is the one we fetch.

To add a board, add an entry to `upstream.json` with the full commit hash, the date, the licence and the paths to fetch, then run `fetch_boards.py` and check the files you need are there. The paths are git sparse-checkout patterns: `/dir/` for a folder, `/file` for one file, and `!/dir/*.wrl` to leave something out.
