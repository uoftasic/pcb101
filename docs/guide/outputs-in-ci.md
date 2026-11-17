# Outputs in CI

This page answers: *how can a computer check your board and build its fabrication files on every push, and how do you know it ran the same KiCad, with the same settings, as the numbers on the lab pages?*

Continuous integration (CI) means that every time you push, a fresh machine checks out your commit and runs a fixed list of commands on it. You met it in IC102 for code. For a board, the commands are the checks you'd otherwise run by hand, ERC, DRC and schematic parity, followed by the [fabrication outputs](fabrication-outputs.md) and some images a reviewer can look at without opening KiCad. In [Lab 05](../labs/lab-05-fab-outputs-in-ci-overview.md) you add a workflow that does this to your board repository, then break the board on purpose and watch the run go red.

![A flow chart of one CI run: a push, a runner that checks out the commit, the pinned KiCad image, the checks, and either a failed run or the outputs uploaded as an artifact](../assets/img/ic103-ci-flow.svg)

*One CI run for a board. If ERC, DRC or schematic parity finds an error, the step fails and GitHub Actions skips the later steps, so a broken board never produces a set of Gerbers that looks ready to order. Made by [`scripts/figures/ci_flow.py`](https://github.com/uoftasic/ic103/blob/main/scripts/figures/ci_flow.py).*

Other KiCad projects already work this way. wafer.space's chip-on-board repository, for example, has a GitHub Actions workflow that runs in the `kicad/kicad:10.0` container, renders the top and bottom of each board with `kicad-cli pcb render`, plots the copper and silkscreen layers with `kicad-cli pcb export svg`, exports each schematic with `kicad-cli sch export pdf`, and commits the results back to the repository (`.github/workflows/release-docs.yml` and `.github/scripts/gen_docs.py` in `wafer-space/chip-on-board-wire-bonded-pcbs`). This course's own repository does the checking half: its [`labs.yml`](https://github.com/uoftasic/ic103/blob/main/.github/workflows/labs.yml) workflow runs the board check on every lab's reference solution whenever `labs/` changes, and once a week in case something outside the repository has moved.

## Checks that fail the run

A CI step fails when its command exits with a status other than 0, so the whole job comes down to choosing commands whose exit status means what you want. By default `kicad-cli` exits 0 even when it finds problems: on the DIP dock, ERC found 42 violations and DRC 156, and both exited 0. With `--exit-code-violations` it exits 5 when anything is reported, and the `--severity-...` options decide what counts. Here are both checks on Tiny Tapeout's DIP dock (`breakout-pcb` at 91a2bf1), in the course's pinned image. We've shortened the paths, and left out the line that says where each report was saved and the font message that each DRC run printed, which [Fonts and 3D models](#fonts-and-3d-models) explains:

```text
$ kicad-cli sch erc --severity-error --exit-code-violations -o erc.rpt dip-dock.kicad_sch
Found 2 violations
exit status 5
$ kicad-cli pcb drc --severity-error --schematic-parity --exit-code-violations -o drc.rpt dip-dock.kicad_pcb
Found 0 violations
Found 0 unconnected items
Found 0 schematic parity issues
exit status 0
```

ERC fails, on two `power_pin_not_driven` errors, and DRC passes. Run with `--severity-all` instead, the same DRC reports:

```text
Found 162 violations
Found 0 unconnected items
Found 3 schematic parity issues
exit status 5
```

The three parity issues were there in the first run too. KiCad reports schematic parity problems as warnings, so `--severity-error` filters them out, and in every project the course checked, that included a footprint that is in the schematic and missing from the board. On the DIP dock the three are about a logo (one footprint, `PSYLOGO01`, placed twice and not in the schematic), which is harmless. On your board the same filter would let a missing connector through with a green run.

That is why the labs don't use the plain `kicad-cli` flags as their "done when". They run [`labs/common/check_board.py`](https://github.com/uoftasic/ic103/blob/main/labs/common/check_board.py), which runs ERC and DRC with every severity, reads the JSON reports, and fails on any error, any unconnected item, and any parity item at all. On the DIP dock it took 28 s with the container limited to one CPU, and ended like this:

```text
                errors  warnings  excluded
  ERC                2        40         0
  DRC                0       156         6
  unconnected        0         0         0
  parity             0         3         0
...
FAIL  erc.error: 2 (want 0)
FAIL  parity.warning: 3 (want 0)
```

It exits 1 on a FAIL, so a workflow step that runs it fails the run. The 156 DRC warnings don't fail it: they are `lib_footprint_issues` and `lib_footprint_mismatch`, comparisons between the board and the libraries installed where the check runs, which is the subject of the next two sections.

## Pinning the image

A Docker image name such as `kicad/kicad:10.0` is a tag, and a tag is a pointer that the publisher moves. On Docker Hub, `kicad/kicad:10.0` and `kicad/kicad:10.0.8` were both last updated on October 30, 2026, and both are 812 MB, because `10.0` currently points at 10.0.8. KiCad posted 10.0.5 on July 22, 10.0.6 on August 29, 10.0.7 on October 7 and 10.0.8 on October 30, so a workflow that names `10.0` gets a new KiCad every few weeks without anyone committing anything. That is fine for pictures. For checks, it means a DRC count can change on a Monday morning for reasons that have nothing to do with your board.

A digest names one exact image, and Docker won't substitute another. The course's checks name `kicad/kicad:10.0.5@sha256:182c8005cb77…` (in full in [`labs/common/kicad-image.txt`](https://github.com/uoftasic/ic103/blob/main/labs/common/kicad-image.txt)), and `labs/common/kicad.sh` prints the digest it ran before every check, so a log always records which KiCad produced it. The course has changed its pin once: it was on 10.0.8 until November 16, 2026, when we moved it to 10.0.5 so that the checks, KiBot and the course's 3D renders all run the same KiCad (see [KiBot](#kibot) below). Moving the pin meant running every check again and copying the new counts onto every page, and before we did, we ran the checks in both releases. The course's own boards gave the same counts in both, but Tiny Tapeout's boards gave different warning counts, and one broken board a different number of DRC errors; [Getting started](getting-started.md#which-version-to-install) lists the differences. A move to a newer release will take the same work.

## The user and the library tables

Pinning the image isn't quite enough, because KiCad's warnings also depend on who runs it. Many warnings compare the parts in your design with the libraries KiCad knows about, and that list lives in the user's settings folder. A container that runs as root, or as your own uid with an empty home folder, has no library tables at all, and then every standard library looks missing. [Getting started](getting-started.md#your-kicad-and-the-courses-checks) shows the effect on the SKY130 breakout: 97 ERC warnings and 120 DRC warnings in the course's setup, 236 and 130 with no tables (and without Tiny Tapeout's own library beside the board), and the same 10 ERC errors and 0 DRC errors in both.

So `kicad.sh` runs the image as your uid and copies KiCad's default library tables into place first, and the course's `labs.yml` calls `kicad.sh` instead of running its steps in a job `container:`, so that CI sees the same tables as the counts on the lab pages. wafer.space's workflow runs its container with `--user root`. That's fine for renders and plots, but if it ran ERC and DRC, its warning counts wouldn't match ours.

## Fonts and 3D models

The image is built for `kicad-cli`, so it carries KiCad and its libraries and not much else. Two gaps show up in board outputs.

The first is fonts. The DIP dock's designer set three silkscreen labels, `ui_in`, `uio` and `uo_out`, in the FreeMono font, which the image doesn't have, and every export printed

```text
Font 'FreeMono' not found; substituting 'DejaVu Sans Mono Bold'.
```

so CI's silkscreen for those labels isn't drawn in the font the designer chose. Text in KiCad's own default font doesn't depend on the fonts installed on a machine, which makes it the safe choice for a board whose outputs come from CI.

The second is 3D models. The image doesn't include KiCad's 3D models of parts (`/usr/share/kicad/3dmodels` doesn't exist in it), so a render made in CI with this image shows the bare board, apart from any part whose model is saved inside the board file. The models are in `kicad/kicad:10.0.5-full`, a 1,444 MB download against 808 MB, which runs the same `kicad-cli` (we compared the two binaries' checksums) with the models added. The course's own figures are rendered in that image, named by its digest in [`scripts/screenshots/kicad/render-image.txt`](https://github.com/uoftasic/ic103/blob/main/scripts/screenshots/kicad/render-image.txt):

![A kicad-cli render of the top of the DIP dock, with its parts](../assets/img/dip-dock-3d-top.png)

*The top of Tiny Tapeout's DIP dock as `kicad-cli pcb render` draws it in `kicad/kicad:10.0.5-full`: copper under the green mask, gold pads, silkscreen and holes, and a 3D model for each part whose footprint names one the image has, such as the DIP switch, the push buttons and the 7-segment display. Made by [`scripts/figures/board_renders.sh`](https://github.com/uoftasic/ic103/blob/main/scripts/figures/board_renders.sh).*

For a reviewer, a render without the parts is often better, since the pads and the silkscreen are what they're checking, and that's what the plain image gives you.

## Outputs that repeat from run to run

It helps to know which outputs come out the same on every run, because then CI can tell you whether a commit changed them:

- SVG plots of layers were identical from run to run once the date that `kicad-cli` writes into each file's `<title>` was removed.
- A top-view render of the DIP dock came out byte-identical in two runs. A bottom view of the SKY130 breakout didn't: the two PNGs were 161,218 and 161,207 bytes, and 54 of their 1,542,912 pixels differed.
- Gerbers, the job file and the drill file carry the date of the export, as [Fabrication outputs](fabrication-outputs.md#dates-in-the-files) shows, so they're never identical as they stand.

The images are for people to look at. When a workflow needs to decide whether the board changed, compare the Gerbers with their date lines removed.

`kicad-cli` also writes a `.kicad_prl` file of local settings next to the project it reads, even for a check. In CI that doesn't matter, because the runner is thrown away afterwards; on your own machine it's one of the files [KiCad files in git](kicad-files-in-git.md) tells you to ignore.

## Jobsets

Instead of listing every export in the workflow, you can save the list in the project as a jobset, which `kicad-cli jobset run` then runs, so the list of outputs lives in one file next to the board. We haven't tried a jobset in this course yet.

## KiBot

[KiBot](https://github.com/INTI-CMNB/KiBot), licensed under the AGPL-3.0, is a tool that drives KiCad from a YAML file and produces outputs that `kicad-cli` doesn't, such as an interactive HTML BOM. In [Lab 05, Part 5](../labs/lab-05-fab-outputs-in-ci-overview.md#part-5-add-kibots-outputs), your workflow runs it after the checks, for an interactive BOM and a design report. Its newest release on November 16, 2026 was 1.9.1, dated 2026-07-28, and its changelog says its KiCad 10 3D rendering goes "through the kicad-cli interface" and "has various limitations". A few things about it matter for a pinned course:

- Its KiCad 10 images lag KiCad. The newest KiCad version in any `ghcr.io/inti-cmnb/kicad10_auto_full` tag was 10.0.5, three releases behind KiCad's own 10.0.8. The course pins its checks to 10.0.5 as well, because with the checks on 10.0.8 a workflow that also ran KiBot would run two different KiCads. Even on the same version, KiBot's image isn't the same build as `kicad/kicad:10.0.5`. In `1.9.1-2_k10.0.5_d13.2_b4.2.4LTS`, `kicad-cli version` prints `10.0.5`, but the KiCad in it is KiCad's Ubuntu package, `10.0.5-testing-188+202607221313~667fa36054~ubuntu25.10.1`, with the 10.0.4 symbol and footprint libraries and no 3D models. We ran the course's board check in it on the SKY130 breakout and on Lab 04's reference board, and it gave the same counts as `kicad/kicad:10.0.5` on both.
- Its GitHub Action for KiCad 10, `v2_k10`, builds `FROM ghcr.io/inti-cmnb/kicad10_auto_full:latest`, a moving tag. On November 16, 2026, `latest`, `1.9.1` and `1.9.1-2_k10.0.5_d13.2_b4.2.4LTS` all named the same image, `sha256:96e75f885b15…`. Lab 05's workflow doesn't use the action. It names the fixed tag and that digest in `ci/kibot-image.txt`, a copy of the course's [`labs/common/kibot-image.txt`](https://github.com/uoftasic/ic103/blob/main/labs/common/kibot-image.txt), and runs the image with `docker run` as the runner's uid, the same way it runs KiCad's image. On your own machine, `labs/common/kibot.sh` runs it the way `kicad.sh` runs KiCad's.
- The image runs as root unless you say otherwise, and it's large: a 1,347 MB download, 3.9 GB on disk. Lab 05's workflow pulls it in KiBot's own step, which GitHub skips when an earlier step has failed, so a run whose board check fails never downloads it.
- KiBot can run ERC and DRC itself, as preflights, and the course doesn't use them. Its DRC fails only on errors unless you tell it to fail on every warning, and KiCad reports a footprint missing from the board as a warning, so with its defaults it passed Lab 04's board with R3 deleted. The checks stay in [`check_board.py`](https://github.com/uoftasic/ic103/blob/main/labs/common/check_board.py), in `kicad/kicad:10.0.5`, and KiBot makes outputs. Lab 05, Part 5 has the runs.


## Check yourself

1. A workflow runs `kicad-cli pcb drc --severity-error --schematic-parity --exit-code-violations` and goes green, but the board is missing a footprint that the schematic has. How?

   <details>
   <summary>Answer</summary>

   KiCad reports schematic parity problems, including a missing footprint, as warnings, and `--severity-error` leaves warnings out, so DRC found nothing at error severity and exited 0. `check_board.py` fails on any parity item for this reason.

   </details>

2. Your workflow names `kicad/kicad:10.0`. One week the DRC warning count changes, and nobody has committed anything. What's the likeliest reason?

   <details>
   <summary>Answer</summary>

   The tag moved to a new 10.0 patch release, so CI ran a different KiCad. Naming the image by its digest, as `labs/common/kicad-image.txt` does, keeps it the same until you change it on purpose.

   </details>

3. You run ERC on the SKY130 breakout in a container as root and get 233 warnings. The lab page says 97. Which number is wrong?

   <details>
   <summary>Answer</summary>

   Neither. Root in the image has no library tables, so ERC reports the standard libraries as missing, and the warnings go up. The errors, 10, are the same in both setups. The lab pages quote warnings only for the course's setup, which `kicad.sh` gives you.

   </details>

4. The render in your CI artifact shows bare pads and no parts. Is your workflow broken?

   <details>
   <summary>Answer</summary>

   No. The `kicad/kicad:10.0.5` image has no 3D models of parts, so every render made in it shows the bare board. The `-full` image has them, and it's what the course's own figures are rendered in.

   </details>

Next: [KiCad files in git](kicad-files-in-git.md).
