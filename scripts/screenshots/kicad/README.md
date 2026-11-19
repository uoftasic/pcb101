# KiCad screenshots and figures

Two tools make the course's KiCad images. `render.sh` runs `kicad-cli` for 3D renders and SVG plots, which is all a figure needs when it only has to show a design. `shot.sh` takes real screenshots of KiCad's editors, for the steps where a student has to find something in the GUI. Both are tools for whoever writes the course pages, and we have run them only on Linux. Both use KiCad 10.0.5. `shot.sh`, and the plots from `render.sh`, use the image pinned in [`labs/common/kicad-image.txt`](../../../labs/common/kicad-image.txt) (`kicad/kicad:10.0.5`, by digest). The 3D renders from `render.sh` use the image in [`render-image.txt`](render-image.txt) (`kicad/kicad:10.0.5-full`, by digest), which has the same `kicad-cli` and KiCad's 3D models of parts as well. Set `PCB101_RENDER_IMAGE` to render in another image.

## GUI screenshots

```bash
python3 labs/common/fetch_boards.py                     # the boards the shot files open
scripts/screenshots/kicad/shot.sh scripts/screenshots/kicad/shots/sky-breakout.sh
```

That writes three PNGs into `docs/assets/img/`, each 1600 × 1000. It took 118 s with the container limited to one CPU, 40 s of it waiting for the Schematic Editor to finish loading the symbol libraries:

| File | What it shows |
|---|---|
| `kicad-schematic-editor-sky-breakout.png` | the Schematic Editor with Tiny Tapeout's SKY130 QFN breakout open |
| `kicad-pcb-editor-sky-breakout.png` | the PCB Editor with the same board |
| `kicad-footprint-editor-sky-breakout-u4.png` | the Footprint Editor with U4, the chip's QFN-64, opened from that board |

We ran it three times. The Footprint Editor capture was byte-identical every time, and so was the Schematic Editor's in the two runs that waited for the libraries. Two of the three PCB Editor captures were byte-identical, and the third differed in 252,097 pixels, including the count on the status-bar badge described below. So compare a changed screenshot by eye before you conclude that KiCad or the board changed.

`shot.sh` builds the image `pcb101/kicad-shot:10.0.5` the first time (`build.sh`; the [`Dockerfile`](Dockerfile) adds Xvfb, openbox, xdotool and ImageMagick to the pinned KiCad image, about 35 MB). It then starts a container with the repo mounted read-only, runs [`rig.sh`](rig.sh) in it, and removes the container when the shot ends, or after 10 minutes where GNU `timeout` is installed. Only the output folder is written.

Give the container at least 2 GB of memory. When the PCB Editor opens, KiCad loads every footprint library in the background. We sampled `ps` every 2 s during the shot above, under a 2 GB limit, and `pcbnew` peaked at 2,252,672 KiB (2.1 GiB) resident; the run completed. We ran the shots with `PCB101_DOCKER_ARGS="--cpus 1 --memory 2g"`.

### The first-run wizard

KiCad 10 opens a modal "KiCad Setup" wizard before any editor if its settings folder is missing any of these (from `common/startwizard/` in the 10.0.5 source):

- `kicad_common.json`;
- a readable `sym-lib-table`, `fp-lib-table` and `design-block-lib-table`;
- `do_not_show_again.update_check_prompt` and `do_not_show_again.data_collection_prompt` set to true in `kicad_common.json`.

Under Xvfb the wizard sits over the editor and the board never loads, so `rig.sh` writes all of them before KiCad starts. It copies the two library tables from `/usr/share/kicad/template/` (the same files the image's own user has), writes an empty design-block table, runs `kicad-cli version` to get a default `kicad_common.json`, and ticks every "don't show again" box in it. KiCad then opens straight into the editor.

The rest of the rig:

- Xvfb gives a 1600 × 1000 screen (set `SCREEN=WxH` to change it), and openbox maximizes every editor window (dialogs keep their own size, see [`openbox-rc.xml`](openbox-rc.xml)), so each capture is the size of the screen.
- Captures use ImageMagick's `import -window root`. `xwd -root` returned the Footprint Editor's menus, toolbars and panels as solid black, because they are drawn in windows whose visual differs from the root window's.
- `capture` waits until the screen hasn't changed for 6 s before it grabs, because KiCad can draw an editor's canvas several seconds before its panels.
- PNGs are written without timestamps.
- In KiCad 10.0.5 every editor shows a red "9+" badge at the right-hand end of its status bar. Clicking it lists messages such as "Library 'GPU': Library not found in library table", although `GPU` and the other libraries it names are in the table the rig copies and in `/usr/share/kicad/symbols/`. ERC in the same session still counted 97 warnings on the breakout, as `kicad-cli` does. The 10.0.8 shots had no badge. We left it in the shots.

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
| [`shots/lab03-lab04-pmod.sh`](shots/lab03-lab04-pmod.sh) | the symbol chooser filtered to Tiny Tapeout's Pmod connector and to the SP0502 ESD array, and Position Relative To on J2 of Lab 03's reference board | nothing: the template and the reference board are in the repo |
| [`shots/lab05-ci.sh`](shots/lab05-ci.sh) | GerbView with the Gerbers and drill file that Lab 05's `ci/build.sh fab` writes for Lab 04's reference board, then with its File menu open, and the DRC dialog on that board with Lab 05's planted error | nothing: the shot runs the build script and `planted.py` itself |
| [`shots/lab06-review.sh`](shots/lab06-review.sh) | Lab 06's seeded board in the PCB Editor; Board Setup's Constraints page, J4 selected with the Properties panel, and J4's Footprint Properties dialog, all on Lab 04's reference board | nothing |

All but `lab03-lab04-pmod.sh` click at fixed positions on the 1600 × 1000 screen, read off earlier captures and given in a comment in the file. Typing into an editor's library filter right after it opens didn't always take in our runs; when a shot stops at a `wait_window`, run it again before changing anything.

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

`kicad-cli`'s SVG plots are transparent, and their colours were chosen for the background of the editor they come from, so on a page in the other colour mode they can be hard to read: the footprint's yellow silkscreen (`#F2EDA1`) has a contrast of 1.21:1 on the site's white page, and the symbol's dark red pins (`#840000`) 1.50:1 on its dark one. `--bg COLOR`, before the mode, puts an opaque rectangle of that colour behind a plot. Lab 02's two plots use the backgrounds their editors have: white for the symbol, and `#001023` for the footprint (sampled from the PCB Editor and Footprint Editor screenshots). They were made from Lab 02's reference solution with these commands, then copied to `docs/assets/img/lab02-rhl0024a-footprint.svg` and `lab02-sn74lvc8t245rhl-symbol.svg`:

```bash
L=labs/lab-02-a-footprint-from-a-datasheet/solutions
mkdir -p labs/common/results/figures
$R --bg '#001023' fp  $L/pcb101.pretty RHL0024A labs/common/results/figures
$R --bg '#ffffff' sym $L/pcb101.kicad_sym SN74LVC8T245RHL labs/common/results/figures
```

The top-view render took 12 s in one run and 33 s in another, with the container limited to one CPU. The header of [`render.sh`](render.sh) lists the defaults it passes to `kicad-cli`. What we measured on the SKY130 breakout, with the plots in `kicad/kicad:10.0.5` and the renders in `kicad/kicad:10.0.5-full`:

- Two runs give byte-identical SVGs, once the date that `kicad-cli` writes into each SVG's `<title>` is removed (the script removes it).
- Two renders of the same view weren't always identical. Of their 1,542,912 pixels, 1 differed between two top views, 54 between two bottom views and 4,025 between two `iso` views. Two top views of the DIP dock were byte-identical.
- A render asked for at 1600 × 1000 comes out 1568 × 984.
- The render image draws a 3D model for every part whose footprint names one it has. The pinned image has no 3D models of parts (`/usr/share/kicad/3dmodels` doesn't exist), so a render made in it, or in CI from it, shows the bare board with its pads, silkscreen and holes, and only the parts whose models are embedded in the board file, such as the breakout's two DF12 connectors.

## Files

| File | What it is |
|---|---|
| `shot.sh` | runs one shot file in the screenshot image (host side) |
| `rig.sh` | runs inside the container: settings, Xvfb, openbox, and the functions shot files use |
| `shots/` | shot files, one per set of screenshots |
| `build.sh`, `Dockerfile` | build `pcb101/kicad-shot:<version>` from the pinned KiCad image |
| `openbox-rc.xml` | maximizes editor windows |
| `render.sh` | `kicad-cli` renders and plots through `labs/common/kicad.sh` |
