# KiCad screenshots and figures

Two tools make the course's KiCad images. `render.sh` runs `kicad-cli` for 3D renders and SVG plots, which is all a figure needs when it only has to show a design. `shot.sh` takes real screenshots of KiCad's editors, for the steps where a student has to find something in the GUI. Both are tools for whoever writes the course pages, and we have run them only on Linux. Both use the KiCad pinned in [`labs/common/kicad-image.txt`](../../../labs/common/kicad-image.txt) (`kicad/kicad:10.0.8`, by digest).

## GUI screenshots

```bash
python3 labs/common/fetch_boards.py                     # the boards the shot files open
scripts/screenshots/kicad/shot.sh scripts/screenshots/kicad/shots/sky-breakout.sh
```

That writes three PNGs into `docs/assets/img/`, each 1600 × 1000, in about 80 s:

| File | What it shows |
|---|---|
| `kicad-schematic-editor-sky-breakout.png` | the Schematic Editor with Tiny Tapeout's SKY130 QFN breakout open |
| `kicad-pcb-editor-sky-breakout.png` | the PCB Editor with the same board |
| `kicad-footprint-editor-sky-breakout-u4.png` | the Footprint Editor with U4, the chip's QFN-64, opened from that board |

Two runs gave byte-identical PNGs, so a changed screenshot means KiCad or the board changed.

`shot.sh` builds the image `pb101/kicad-shot:10.0.8` the first time (`build.sh`; the [`Dockerfile`](Dockerfile) adds Xvfb, openbox, xdotool and ImageMagick to the pinned KiCad image, about 30 MB). It then starts a container with the repo mounted read-only, runs [`rig.sh`](rig.sh) in it, and removes the container when the shot ends, or after 10 minutes where GNU `timeout` is installed. Only the output folder is written.

Give the container at least 2 GB of memory. When the PCB Editor opens, KiCad loads every footprint library in the background, and with the Footprint Editor open, `ps` reported 2.2 GB resident for KiCad under a 2 GB limit (the run completed) and 2.4 GB under a 4 GB limit. We ran the shots with `PB101_DOCKER_ARGS="--cpus 1 --memory 2g"`.

### The first-run wizard

KiCad 10 opens a modal "KiCad Setup" wizard before any editor if its settings folder is missing any of these (from `common/startwizard/` in the 10.0.8 source):

- `kicad_common.json`;
- a readable `sym-lib-table`, `fp-lib-table` and `design-block-lib-table`;
- `do_not_show_again.update_check_prompt` and `do_not_show_again.data_collection_prompt` set to true in `kicad_common.json`.

Under Xvfb the wizard sits over the editor and the board never loads, which is what the course plan's first test ran into. `rig.sh` writes all of them before KiCad starts. It copies the two library tables from `/usr/share/kicad/template/` (the same files the image's own user has), writes an empty design-block table, runs `kicad-cli version` to get a default `kicad_common.json`, and ticks every "don't show again" box in it. KiCad then opens straight into the editor.

The rest of the rig:

- Xvfb gives a 1600 × 1000 screen (set `SCREEN=WxH` to change it), and openbox maximizes every editor window (dialogs keep their own size, see [`openbox-rc.xml`](openbox-rc.xml)), so each capture is the size of the screen.
- Captures use ImageMagick's `import -window root`. `xwd -root` returned the Footprint Editor's menus, toolbars and panels as solid black, because they are drawn in windows whose visual differs from the root window's.
- `capture` waits until the screen hasn't changed for 6 s before it grabs, because KiCad can draw an editor's canvas several seconds before its panels.
- PNGs are written without timestamps.

### Shot files

A shot file is a few lines of bash that `rig.sh` sources. [`shots/sky-breakout.sh`](shots/sky-breakout.sh) is the example:

| Function | Does |
|---|---|
| `work FOLDER` | copies a repo folder to `/tmp/work`, where KiCad may write its `.kicad_prl`, backups and lock files |
| `launch APP FILE TITLE` | starts `pcbnew` or `eeschema` on a file under `/tmp/work` and waits for a window whose title matches the regex `TITLE` |
| `wait_window TITLE [SECONDS]` | makes the newest window matching `TITLE` the current one, or fails with a `failed-*.png` of the screen |
| `focus` | gives the current window the keyboard focus again, after a dialog had it |
| `key KEYS...` | presses keys, in `xdotool` names (`ctrl+f`, `Return`, `Escape`) |
| `type_text TEXT` | types text into whatever has the focus |
| `pause SECONDS` | waits, for an editor still loading in the background |
| `capture NAME` | writes `NAME.png` to the output folder once the screen has settled |
| `quit APP` | ends an editor you've finished with |

KiCad's standalone editors have no command-line option to open the Footprint Editor, so the example opens it the way a student would: Edit → Find (Ctrl+F) for `U4`, then Edit Footprint (Ctrl+E).

The other shot files:

| Shot file | Writes | Needs first |
|---|---|---|
| [`shots/lab01-sky-breakout.sh`](shots/lab01-sky-breakout.sh) | the breakout's Symbol Fields Table, two zoomed schematic blocks, and the ERC dialog listing its errors | the fetched boards |
| [`shots/lab02-rhl0024a.sh`](shots/lab02-rhl0024a.sh) | Lab 02's reference footprint in the Footprint Editor, and the Pad Properties and Create Array dialogs | Lab 02's check run on `solutions/`, which writes the project the shot opens |

These two click at fixed screen positions, read off earlier captures and listed in each file's header. Typing into an editor's library filter right after it opens didn't always take in our runs; when a shot stops at a `wait_window`, run it again before changing anything.

## Renders and plots

```bash
R=scripts/screenshots/kicad/render.sh
B=labs/common/upstream/breakout-pcb/breakout-sky-qfn
$R 3d  $B/breakout-sky-qfn.kicad_pcb docs/assets/img/sky-breakout-3d.png          # top view
$R 3d  $B/breakout-sky-qfn.kicad_pcb docs/assets/img/sky-breakout-iso.png iso
$R pcb $B/breakout-sky-qfn.kicad_pcb docs/assets/img/sky-breakout-fcu.svg F.Cu,Edge.Cuts
$R sch $B/breakout-sky-qfn.kicad_sch docs/assets/img/sky-breakout-sch
$R fp  /usr/share/kicad/footprints/Package_DFN_QFN.pretty QFN-64-1EP_9x9mm_P0.5mm_EP7.65x7.65mm docs/assets/img
$R sym $B/../tinytapeout-kicad-libs/symbols/TinyTapeout.kicad_sym Openframe_QFN_TT06_REV2 docs/assets/img
```

`kicad-cli`'s SVG plots are transparent, and their colours were chosen for the background of the editor they come from, so on a page in the other colour mode they can be hard to read: the footprint's yellow silkscreen (`#F2EDA1`) has a contrast of 1.21:1 on the site's white page, and the symbol's dark red pins (`#840000`) 1.50:1 on its dark one. `--bg COLOR`, before the mode, puts an opaque rectangle of that colour behind a plot. Lab 02's two plots use the background their editors have, white for the symbol and `#001023` for the footprint (sampled from the PCB Editor and Footprint Editor screenshots), and were made from its reference solution, then copied to `docs/assets/img/lab02-rhl0024a-footprint.svg` and `lab02-sn74lvc8t245rhl-symbol.svg`:

```bash
L=labs/lab-02-a-footprint-from-a-datasheet/solutions
mkdir -p labs/common/results/figures
$R --bg '#001023' fp  $L/pb101.pretty RHL0024A labs/common/results/figures
$R --bg '#ffffff' sym $L/pb101.kicad_sym SN74LVC8T245RHL labs/common/results/figures
```

The top-view render took 12 s. The header of [`render.sh`](render.sh) lists the defaults it passes to `kicad-cli`. What we measured on the SKY130 breakout:

- Two runs give byte-identical SVGs, once the date that `kicad-cli` writes into each SVG's `<title>` is removed (the script removes it), and byte-identical top-view renders.
- The `iso` view differs between runs in about 4,000 of its 1.5 million pixels.
- A render asked for at 1600 × 1000 comes out 1568 × 984.
- The image has no 3D models of parts (`/usr/share/kicad/3dmodels` doesn't exist), so a render shows the bare board with its pads, silkscreen and holes. A render made in CI from the same image looks the same.

## Files

| File | What it is |
|---|---|
| `shot.sh` | runs one shot file in the screenshot image (host side) |
| `rig.sh` | runs inside the container: settings, Xvfb, openbox, and the functions shot files use |
| `shots/` | shot files, one per set of screenshots |
| `build.sh`, `Dockerfile` | build `pb101/kicad-shot:<version>` from the pinned KiCad image |
| `openbox-rc.xml` | maximizes editor windows |
| `render.sh` | `kicad-cli` renders and plots through `labs/common/kicad.sh` |
