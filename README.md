# PB101 — PCB Design with KiCad

Design the boards a chip sits on: schematics, footprints from datasheets, layout, protection, fab outputs in CI, review, and a bring-up board for a team chip.

Part of the UofT ASIC Team education materials (`uoftasic`).
Course site: <https://uoftasic.com/pb101/> · Education hub: <https://edu.uoftasic.com/>

Students draw in KiCad 10.0 installed on their own computers ([Getting started](https://uoftasic.com/pb101/guide/getting-started.html) says what to install). Every check, and every count or message a lab page shows, comes from `kicad-cli` in the official image `kicad/kicad:10.0.8`, pinned by digest in [`labs/common/kicad-image.txt`](labs/common/kicad-image.txt). The course doesn't use the workbench.

## Quick start

You need Docker, git and Python 3. From a clone of this repo:

```bash
python3 labs/common/fetch_boards.py          # Tiny Tapeout's boards, at pinned commits, into labs/common/upstream/
labs/common/kicad.sh python3 labs/common/check_board.py labs/common/upstream/breakout-pcb/breakout-sky-qfn
```

The second command ends with `FAIL  erc.error: 10 (want 0)`, because Tiny Tapeout's SKY130 breakout has 10 ERC errors in KiCad 10.0.8. [`labs/common/README.md`](labs/common/README.md) explains the output, the checker's rules, and how a lab uses them.

## Lab packages

| Path | What it is | Writeup |
|---|---|---|
| `labs/lab-01-open-a-board-you-didnt-design/` | the notes template for Tiny Tapeout's SKY130 breakout, and the check that compares a student's notes with the board | [Lab 01](https://uoftasic.com/pb101/labs/lab-01-open-a-board-you-didnt-design-overview.html) |
| `labs/lab-02-a-footprint-from-a-datasheet/` | the RHL0024A drawing data, an empty footprint and symbol library, and the check that compares them with the student's own pad numbers | [Lab 02](https://uoftasic.com/pb101/labs/lab-02-a-footprint-from-a-datasheet-overview.html) |
| `labs/lab-03-a-pmod-for-one-projects-pins/` | the board template a student copies into their own repository, and the reference SimProc Pmod | [Lab 03](https://uoftasic.com/pb101/labs/lab-03-a-pmod-for-one-projects-pins-overview.html) |
| `labs/lab-04-protect-and-plan/` | the `BRINGUP.md` template, and the reference board with its protection and plan | [Lab 04](https://uoftasic.com/pb101/labs/lab-04-protect-and-plan-overview.html) |
| `labs/lab-05-fab-outputs-in-ci/` | the starter workflow and build script, and the check that runs the build in a student's repository and checks what it made and what git tracks | [Lab 05](https://uoftasic.com/pb101/labs/lab-05-fab-outputs-in-ci-overview.html) |
| `labs/lab-06-review-a-seeded-board/` | the seeded board, the `REVIEW.md` and `QUOTE.md` templates, and their check | [Lab 06](https://uoftasic.com/pb101/labs/lab-06-review-a-seeded-board-overview.html) |
| `labs/capstone-a-board-for-a-team-chip/` | the `DESIGN.md` template, the check for both briefs, and a reference board for each | [Capstone](https://uoftasic.com/pb101/labs/capstone-a-board-for-a-team-chip-overview.html) |
| `labs/common/` | the pinned-KiCad wrapper, the board checker, the Pmod and bring-up plan checks, and the script that fetches Tiny Tapeout's boards | used by every lab |

Reference solutions go in each package's `solutions/` folder. `.github/workflows/labs.yml` runs the board checker on every KiCad project there, in the pinned image, on every change to `labs/**` and once a week.

## Screenshots and figures

[`scripts/screenshots/kicad/`](scripts/screenshots/kicad/README.md) takes GUI screenshots of KiCad's editors under Xvfb in the pinned image, and makes 3D renders and SVG plots with `kicad-cli`. Images for the site go in `docs/assets/img/`. The guide pages' diagrams and plots are drawn by the scripts in [`scripts/figures/`](scripts/figures/), listed in [`scripts/README.md`](scripts/README.md).

## Docs

The course site is built with Quarto from `./docs`. `docs/_quarto.yml` holds the site, sidebar and navbar, and `docs/_quarto-pdf.yml` builds the whole course as one PDF. To preview it you need [Quarto](https://quarto.org/docs/get-started/) 1.11:

```bash
quarto preview docs                            # -> http://localhost:4200
quarto render docs --profile pdf --to typst    # whole course as one PDF in docs/_book/
```

| Path | On Pages? | Purpose |
|------|-----------|---------|
| `docs/` | Yes | The course site; `docs/index.md` is the home page and has the Course path |
| `docs/guide/` | Yes | Guide pages: reading only, no commands |
| `docs/labs/` | Yes | Lab writeups: every command a student runs, in numbered parts and steps |
| `labs/` | No | Lab packages, and the shared checks in `labs/common/` |
| `scripts/` | No | `check_site.py` (the link check for the rendered site), the KiCad screenshot tools, and the scripts that draw the guide pages' figures |

GitHub Pages is set to Source: GitHub Actions. `.github/workflows/site.yml` renders the site and the course PDF, checks the rendered site's links and anchors with `scripts/check_site.py`, and deploys `docs/_site`.

This repo was created from [uoftasic/course-template](https://github.com/uoftasic/course-template). `TEMPLATE.md` and `scripts/init-template.py` are that template's bootstrap files and aren't part of the course.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) and [AGENTS.md](AGENTS.md).

## License

[MIT](LICENSE). Copyright UofT ASIC Team / `uoftasic`. Tiny Tapeout's boards and libraries are fetched from their own repositories and keep their own licences, which [`labs/common/upstream.json`](labs/common/upstream.json) records.
