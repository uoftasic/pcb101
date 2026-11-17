# Agent guide: UofT ASIC course repos

This is IC103, PCB Design with KiCad, a course repository for the UofT ASIC Team (`uoftasic`). The course comes third in the IC track, after IC101 and IC102. It teaches students to design the boards a chip sits on, in KiCad 10: schematics, footprints from datasheets, layout, protection, fabrication outputs in CI, review, and a bring-up board for a team chip. The site under `docs/` is built with Quarto and published on GitHub Pages by `.github/workflows/site.yml`. Everything students run lives outside `docs/`, in the lab packages under `labs/`.

Write for a student working through the course, not for whoever maintains the template. Concrete labs and pages a student can follow from start to finish are worth more than meta documentation.

## Goals

- Teach PCB design for the boards that carry a chip, in KiCad 10, with Tiny Tapeout's boards as the worked examples.
- Keep reading and doing apart. Guide pages explain; lab writeups are the only pages that ask the student to run anything; `labs/` holds what they run.
- Never publish grades, solution keys or PII under `docs/`. Put keys in `labs/**/solutions/` and gitignore them on student forks when policy requires.

## Layout

Keep each kind of file in the folder listed for it.

| Path | Published? | Put here |
|------|------------|----------|
| `docs/index.md` | Yes | Home page with the course path table |
| `docs/guide/` | Yes | Guide pages: concepts, figures, worked examples. Reading only. |
| `docs/labs/` | Yes | Lab writeups only (`lab-NN-*-overview.md`, and the capstone's `capstone-*-overview.md`) |
| `docs/reference/` | Yes | Optional lookup pages: cheat sheets, troubleshooting tables. IC103 has none. |
| `docs/assets/img/` | Yes | Figures for the site: diagrams, plots, KiCad renders and screenshots, each made by a script |
| `labs/<lab-id>/` | No | A lab's package: its checks and generators in `src/` (Python), inputs in `data/`, reference solutions in `solutions/`, local outputs in `results/`, and the templates, KiCad projects and `check.sh` a student uses |
| `labs/common/` | No | What every lab uses: `kicad.sh` and the pinned image, the board, Pmod and bring-up plan checks, and `fetch_boards.py`, which fetches Tiny Tapeout's boards into `labs/common/upstream/` |
| `scripts/` | No | `check_site.py`, the KiCad screenshot and render tools in `screenshots/kicad/`, and the scripts in `figures/` that draw the site's figures |
| `notebooks/` | No | Exploratory or assignment notebooks. IC103 has none. |
| `data/`, `figures/` | No | Shared datasets and source figures. IC103 keeps none: each lab's inputs are in its own `data/`, and every figure is made by a script. |

Three files wire up the site. `docs/_quarto.yml` holds the site settings, sidebar, navbar and per-page PDFs; `docs/_quarto-pdf.yml` builds the whole course as one PDF; and `docs/_filters/course.lua` turns `<details>` answers into collapsed callouts (in PDFs it moves them to an Answers section at the end of each page). Write math as `$inline$` or `$$display$$`. In a repo made from the template, `scripts/init-template.py` fills in the `{{...}}` tokens for the course id, title and description; IC103's are already filled in, and no tokens are left (see `TEMPLATE.md`).

## Course structure

Every course follows the same shape, so a student always knows whether they should be reading or doing, and what comes next. The sample pages in [course-template](https://github.com/uoftasic/course-template) show it: `docs/index.md`, `docs/guide/getting-started.md` and `docs/labs/lab-01-overview.md`. IC103 removed its copy of the sample lab.

### Home page

`docs/index.md` says who the course is for, the prerequisites and the total time, then has a numbered course path table. Every course uses the same table format:

```
| # | | What | Time |
|---|---|---|---|
| 1 | Read | [Page](guide/page.md) · [Page](guide/page.md) | 45 min |
| 2 | Do | [Lab 01: Title](labs/lab-01-...-overview.md). One sentence on what you'll do. | 1.5 h |
```

- Each row is either Read (one or more guide pages) or Do (one lab), in plain text. Read and Do rows alternate in the order a student should work.
- Every Do row ends with one sentence on what the student does in the lab.
- The row times add up to the total time stated on the home page. Leave optional lab parts out of the row times.
- Lab titles take the form "Lab 01: Title" in the table, in the lab page's `#` header and in the sidebar.

The sidebar in `docs/_quarto.yml` and the chapter list in `docs/_quarto-pdf.yml` list the same pages in the same order. The Previous and Next links at the bottom of each page (`page-navigation: true` in `docs/_quarto.yml`) follow the sidebar, so they walk the course path too.

### Guide pages

`docs/guide/` is reading only. No commands the student has to run. If a page needs the student to run or build something, make it a numbered step in the matching lab writeup and leave a one-line pointer in the guide ("You'll measure this yourself in Lab 02, Part 3."). Pencil-and-paper questions can go in a short "Check yourself" block at the end of the page.

### Lab writeups

`docs/labs/<lab-id>-overview.md` is the one place for doing. In this order:

1. What the student will build or measure, in two or three lines, and a link to `labs/<lab-id>/`.
2. Before you start: which guide pages to read first, and any setup.
3. A time estimate. Leave optional parts out of it, or give their time separately ("about 2 h, plus 20 min for the optional part").
4. Numbered parts, each with numbered steps. Open each part with the one question it answers, and end it with a concrete "You should see …" check. A setup part, such as the sample lab's Part 1, can skip the question.
5. Optional parts, if any, after all the required parts, with "(optional)" in the header. If a required part depends on an optional one, the optional part is really required: make it required, or change the required part so it no longer depends on it.
6. Finishing, with these three things in this order:
   1. You're done when: one checkable line tied to the student's own work, such as `make` printing PASS on the deck they edited. A PASS from the shipped package doesn't count, because it passes before the student has done anything.
   2. Questions, if there are any. Ask only what the student can answer from their own work, and give each one a collapsed answer or a pointer to the step that answers it.
   3. Submit: what to submit, or "Nothing to submit."
7. Going further (optional), if you have extra reading or experiments that no part depends on.
8. A last line, "Next on the [Course path](../index.md#course-path): …", that names the next row.

Inside the parts:

- At least one required part has the student produce something: edit a deck or file, write a test, draw a cell, or work out a number and write it down before checking it. A lab where the student runs the shipped package and reads its output doesn't meet this.
- Use prediction steps ("write down what you expect before you run it") wherever the student can reasonably predict the result.
- Keep the observed numbers and outputs in "You should see". They're how the student knows they're on track. If the check would also explain why, ask the why as a question at that step and put the answer in a collapsed block directly under it:

  ```html
  <details>
  <summary>Answer</summary>

  The text of the answer, with Markdown and $math$ as usual. Leave the blank lines.

  </details>
  ```

  Inside a numbered step, indent the block to line up with the step's text, as the sample lab does.
- Copy every expected output from a real run, on the course image if the lab uses the EDA tools.
- Put each question at the step where it comes up.
- As a rough guide, split or trim a part with more than eight steps. Steps that don't help answer the part's question go in Going further.
- Keep a writeup under about 2,500 words. Move lookup material (troubleshooting tables, warning catalogues, full tool output) to `docs/reference/` and link it from the step where it comes up. Don't cut teaching content, numbers, caveats or warnings to get there.

For a course that runs on the workbench, Lab 01 Part 1 is "Load the course", in about 30 lines:

- One line: if you haven't set up the workbench, do [IC101 Lab 03](https://uoftasic.com/ic101/labs/lab-03-launch-the-workbench-overview.html) first.
- Start the desktop, load `.designinit`, and run `mod add <course-id>`.
- Check the course-specific tool versions that the printed outputs depend on.
- List only the troubleshooting rows specific to this course, and link IC101's [Troubleshooting](https://uoftasic.com/ic101/reference/troubleshooting.html) page for the rest. Keep fallback routes that work without `mod`.

The sample lab needs only Python, so its Part 1 installs the Python requirements instead.

### Package READMEs and reference pages

`labs/<lab-id>/README.md` is short: a link to the writeup, how to run, a table of make targets if there is a Makefile, and the file list. Don't repeat the teaching from the writeup.

Reference pages (`docs/reference/`) and `solutions/` READMEs are lookup-shaped: tables and short entries.

## Adding a lab

Labs are the main unit of coursework. Name them `lab-NN-short-name` (for example `lab-02-counter-sv`). The sample lab is just `lab-01`; give real labs a short name.

1. Create `labs/<lab-id>/` with at least:
   - `README.md`: link to the writeup and how to run
   - `src/`: HDL, Python and entry points
   - `data/`: small inputs (large binaries go in Git LFS or external storage)
   - `results/`: local outputs
   - `requirements.txt` or tool notes when needed
2. Add `docs/labs/<lab-id>-overview.md` in the writeup shape above.
3. Add a Do row to the course path table on the home page, in the format above. Add an entry "Lab NN: Title" at the same position in the sidebar in `docs/_quarto.yml`, and the writeup to the chapters in `docs/_quarto-pdf.yml`. Update the row times and the total time so they still add up. Add the lab to the navbar in `docs/_quarto.yml` only if it belongs in the top nav.
4. Cross-link: the writeup links to `labs/<lab-id>/` on GitHub, and the package README links to `docs/labs/<lab-id>-overview.md`.

Don't paste long HDL into site pages. Link to the files under `labs/` instead.

## Adding a guide page

1. Add a kebab-case Markdown file under `docs/guide/` (for example `yosys-synth.md`).
2. Add it to a Read row in the course path table, to the sidebar in `docs/_quarto.yml`, and to the chapters in `docs/_quarto-pdf.yml`, at the same position in each.
3. Put images in `docs/assets/img/`.
4. Link to `labs/` and `scripts/` with GitHub URLs (`https://github.com/uoftasic/<course-id>/tree/main/labs/...`).

Quarto resolves page links and images the same way: relative to the page they're written in.

- From a page in `docs/guide/` or `docs/labs/`, another page is `../labs/lab-01-overview.md` or `../guide/yosys-synth.md`, the home page is `../index.md`, and an image is `../assets/img/foo.png`.
- From `docs/index.md`, they're `guide/yosys-synth.md`, `labs/lab-01-overview.md` and `assets/img/foo.png`.

The link check in `.github/workflows/docs-link-check.yml` reads the Markdown with the same rules, and `scripts/check_site.py` checks every local link and anchor in the rendered site when `.github/workflows/site.yml` builds it.

## Pedagogy checklist

- Say what the student will do in their own terms ("You'll synthesize a counter and inspect the netlist").
- Assume the student has cloned this repo. Courses that need EDA tools (LibreLane, SKY130, IIC-OSIC-TOOLS) run in the shared [workspace](https://github.com/uoftasic/workspace) that students set up in IC101. Point to IC101 for that setup, and document the steps specific to your course in the course, such as `mod add <course-id>` (the workspace command that clones a course into it). Don't invent a one-off container setup or bundle Docker in every lab unless the course already does.
- Keep steps copy-pasteable: `cd`, install, simulate or synthesize, check the output.
- End every lab part with an expected result (a printout, a waveform check, an area or timing ballpark, a golden hash) so students know they succeeded.
- Raise the difficulty from lab to lab, and reuse naming and directory conventions so later labs feel familiar.
- Prefer small, inspectable designs over opaque blobs. When you use IP or PDK files, keep secrets and huge binaries out of git.

## Writing style

- Write in the second person, in plain and friendly language, for a 2nd–3rd year ECE student. Short sentences for facts, longer ones for reasoning.
- Headers are labels ("Load lines", "Part 2: Sweep V_GS"), not verdicts.
- Use bold only for a term where it's defined, or for a real warning. Use em dashes rarely.
- Say each thing once. Don't cut numbers, caveats, warnings or troubleshooting to make a page shorter.

## Tooling

- Python helpers and graders go under `labs/<id>/src/` or `scripts/`. List entry points in the nearest `README.md`.
- SystemVerilog/Verilog goes under `labs/<id>/src/`, or `rtl/` and `tb/` if you split them. Stay consistent within the course.
- Heavy outputs (GDS, large FSDB/VCD, PDK caches) go in a local `results/` or in LFS, never under `docs/`.
- Preview the site locally with `quarto preview docs`, then open http://localhost:4200.

## Don't

- Don't add maintainer-only pages to the published site (contributing guides, template notes, notation stubs "for debugging").
- Don't put solution keys or rubrics in `docs/`.
- Don't replace student-facing content with template or bootstrap instructions. Point people at `CONTRIBUTING.md` or `TEMPLATE.md` only when they're bootstrapping a repo or changing its conventions.
- Don't change the org assumptions: the GitHub org is `uoftasic`, and the course id matches the repo name.

## Quick references

- Repo conventions: `CONTRIBUTING.md`
- Bootstrap tokens and Pages checklist: `TEMPLATE.md`
- Sample lab: `labs/lab-01/` and `docs/labs/lab-01-overview.md` in [course-template](https://github.com/uoftasic/course-template)
- IC103's KiCad tooling: the section below, `labs/common/README.md` and `scripts/screenshots/kicad/README.md`

## IC103 specifics

IC103 teaches PCB design in KiCad rather than an IC flow, so it departs from the template in a few places. Where this section and the rest of the file disagree, this section wins for this repo.

- No workbench: students install KiCad 10.0 natively, 10.0.5 where they can ([Getting started](docs/guide/getting-started.md)). Lab 01 Part 1 installs KiCad and checks its version instead of "Load the course".
- The pinned KiCad is 10.0.5, everywhere: every expected output on a page comes from a run in `kicad/kicad:10.0.5`, by the digest in `labs/common/kicad-image.txt`, through `labs/common/kicad.sh` (as your uid, with the image's default library tables). 3D renders run the same `kicad-cli` binary in `kicad/kicad:10.0.5-full`, which adds the 3D models, by the digest in `scripts/screenshots/kicad/render-image.txt`. KiBot runs in its own image, `ghcr.io/inti-cmnb/kicad10_auto_full:1.9.1-2_k10.0.5_d13.2_b4.2.4LTS@sha256:96e75f885b15617c6b38aef11db7856a93f4367cab7a0b6c2b30465557619330`, by the digest in `labs/common/kibot-image.txt`, through `labs/common/kibot.sh`; its `kicad-cli` is also 10.0.5 (KiCad's Ubuntu build, with the 10.0.4 libraries and no 3D models). Lab 05 runs it for an interactive BOM and a design report, and copies of both pin files sit in the lab's `starter/ci/` and `solutions/simproc-pmod/ci/`. Change all three images together. What a check gets from KiCad itself (ERC, DRC, parity, netlists, plots and renders) comes from `kicad-cli`, and the rest is Python that reads Markdown, git or KiCad's files directly. `check_bringup.py` and Lab 06's `check_lab06.py` are made only of that Python, so they don't use KiCad at all. Warning counts depend on the library tables, so quote them only for that environment. Error counts were the same in every library setup we tried, but not always across KiCad releases: a broken copy of KiCad's pic_programmer demo gave 3 DRC errors in 10.0.5 and 2 in 10.0.8.
- The board check: `labs/common/check_board.py` prints ERC, DRC, unconnected and parity counts and PASS or FAIL. It fails on any parity item, warnings included, because in every project we checked KiCad reported a missing footprint as a warning. A lab's "You're done when" runs it on the student's own files.
- Reference solutions go in `labs/<lab-id>/solutions/`. CI (`.github/workflows/labs.yml`) checks every `.kicad_pro` under them. A board that is meant to have errors carries a `check-expect.json` next to its `.kicad_pro` (format in `check_board.py`'s docstring).
- Upstream boards: Tiny Tapeout's boards are fetched at pinned commits by `labs/common/fetch_boards.py` into `labs/common/upstream/` (gitignored), never copied into the repo. To add one, add it to `labs/common/upstream.json` with its commit and licence.
- Images: GUI screenshots come from `scripts/screenshots/kicad/shot.sh` (KiCad under Xvfb in the pinned image), and 3D renders and plots from `scripts/screenshots/kicad/render.sh` (renders in the render image, with the parts' 3D models; plots in the pinned image). Use a render or plot wherever it shows what the step needs, and a GUI screenshot where the student has to find something in the editor.
- Empty folders: `data/`, `figures/` and `notebooks/` hold only a README and a `.gitkeep`. Each lab's inputs are in `labs/<lab-id>/data/`, and every figure is made by a script in `scripts/figures/` or `scripts/screenshots/kicad/` straight into `docs/assets/img/`.
