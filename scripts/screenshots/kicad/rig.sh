#!/usr/bin/env bash
# Runs inside ic103/kicad-shot (started by shot.sh). Sets up a KiCad that starts straight
# into its editor, starts a virtual screen, then sources one shot file, which drives KiCad
# with the functions below and captures PNGs into /out.
#
#   rig.sh SHOT_FILE
#
# The repo is mounted read-only at /w. A shot file starts with `work FOLDER`, which copies a
# folder of the repo to /tmp/work, because KiCad writes .kicad_prl, backups and lock files
# next to anything it opens, and none of that should land in the repo.
set -euo pipefail

SHOT_FILE="$1"
SCREEN="${SCREEN:-1600x1000}"
export HOME=/tmp/home
CFG="$HOME/.config/kicad/10.0"

# --- KiCad settings, written before KiCad starts ------------------------------------------
# KiCad 10 opens a modal "KiCad Setup" wizard before any editor when one of three things is
# missing (common/startwizard/ in the 10.0.8 source):
#   1. kicad_common.json in the settings folder (SETTINGS_MANAGER::SettingsDirectoryValid);
#   2. a readable global sym-lib-table, fp-lib-table *and* design-block-lib-table
#      (LIBRARY_MANAGER::GlobalTablesValid);
#   3. do_not_show_again.update_check_prompt and .data_collection_prompt set to true in
#      kicad_common.json (STARTWIZARD_PROVIDER_PRIVACY::NeedsUserInput).
# Under Xvfb the wizard sits on top of the editor and the board never loads. Writing all
# three first means it never opens.
mkdir -p "$CFG"
cp /usr/share/kicad/template/fp-lib-table /usr/share/kicad/template/sym-lib-table "$CFG/"
printf '(design_block_lib_table\n\t(version 7)\n)\n' > "$CFG/design-block-lib-table"
kicad-cli version >/dev/null          # writes a default kicad_common.json and kicad.json
python3 - "$CFG/kicad_common.json" <<'PY'
import json, sys
path = sys.argv[1]
with open(path) as f:
    settings = json.load(f)
# Every "don't show this again" box ticked: the privacy prompts the wizard asks about, and
# the zone-fill and 3D-model notices that would otherwise pop up over a board.
for key in settings["do_not_show_again"]:
    settings["do_not_show_again"][key] = True
with open(path, "w") as f:
    json.dump(settings, f, indent=2)
PY

# --- A virtual screen with a window manager -----------------------------------------------
export DISPLAY=:99
Xvfb "$DISPLAY" -screen 0 "${SCREEN}x24" -nolisten tcp >/tmp/xvfb.log 2>&1 &
for _ in $(seq 1 50); do xdpyinfo >/dev/null 2>&1 && break; sleep 0.1; done
mkdir -p "$HOME/.config/openbox"
cp /rig/openbox-rc.xml "$HOME/.config/openbox/rc.xml"
openbox >/tmp/openbox.log 2>&1 &
sleep 1

# --- Functions for shot files --------------------------------------------------------------
WIN=""

log() { echo "rig: $*" >&2; }

# work FOLDER: copy FOLDER (relative to the repo root) to /tmp/work, where KiCad may write.
work() {
    rm -rf /tmp/work
    mkdir -p /tmp/work
    cp -r "/w/$1/." /tmp/work/
}

# launch APP FILE TITLE_REGEX: start pcbnew or eeschema on FILE (relative to /tmp/work) and
# wait for a visible window whose title matches TITLE_REGEX.
launch() {
    local app="$1" file="$2" title="$3"
    "$app" "/tmp/work/$file" >"/tmp/$app.log" 2>&1 &
    wait_window "$title" 120
}

# wait_window TITLE_REGEX [SECONDS]: make the newest matching window the current one.
wait_window() {
    local title="$1" limit="${2:-60}" i w
    for i in $(seq 1 "$limit"); do
        w="$(xdotool search --onlyvisible --name "$title" 2>/dev/null | tail -n 1 || true)"
        if [ -n "$w" ]; then
            WIN="$w"
            log "window '$(xdotool getwindowname "$w")' after ${i}s"
            focus
            return 0
        fi
        sleep 1
    done
    log "no window matching '$title' after ${limit}s; windows open:"
    windows >&2
    capture "failed-$(basename "$SHOT_FILE" .sh)" || true
    exit 1
}

windows() {
    local w n
    for w in $(xdotool search --onlyvisible --name '.+' 2>/dev/null); do
        n="$(xdotool getwindowname "$w" 2>/dev/null || true)"
        [ -n "$n" ] && echo "  $w  $n"
    done
}

focus() { xdotool windowactivate --sync "$WIN" >/dev/null 2>&1 || true; sleep 0.5; }

# key KEY...: press keys in whatever has the keyboard focus, for example: key ctrl+f.
# Call focus first when a dialog may have taken the focus away from the editor.
key() { xdotool key --clearmodifiers "$@"; sleep 1; }

# type TEXT: type text into whatever has the keyboard focus
type_text() { xdotool type --delay 60 "$1"; sleep 0.5; }

# quit APP: end an editor you've finished with (it never saved anything, so nothing is lost).
quit() { pkill -x "$1" || true; sleep 2; }

# grab FILE: the whole screen as it looks, into FILE (any ImageMagick format).
# This uses ImageMagick's `import` rather than `xwd -root`. KiCad's Footprint Editor draws
# its menus, toolbars and panels in windows whose visual differs from the root window's,
# and `xwd -root` returns those as solid black; `import` reads each window in its own
# visual, so they come out as they look on screen.
grab() { import -window root "$1" 2>/dev/null; }

# settle: wait until the screen has stopped changing for 6 s (four identical grabs, 2 s
# apart), for at most 2 minutes. KiCad can pause for a few seconds between drawing an
# editor's canvas and its menus and panels, so a single pair of equal grabs isn't enough.
settle() {
    local prev="" cur same=0 i
    for i in $(seq 1 60); do
        # A grab can fail while a window is being mapped; count that as "changed".
        cur="$( (grab rgb:- || date +%N) | md5sum)"
        if [ "$cur" = "$prev" ]; then
            same=$((same + 1))
            [ "$same" -ge 3 ] && return 0
        else
            same=0
        fi
        prev="$cur"
        sleep 2
    done
    log "screen still changing after 2 minutes; capturing anyway"
}

# pause SECONDS: wait, for an editor that is still loading libraries in the background.
pause() { sleep "$1"; }

# capture NAME: settle, then write /out/NAME.png. The PNG has no timestamps in it, so the
# same screen gives the same file.
capture() {
    local i
    for i in 1 2 3 4 5; do
        settle
        if grab /tmp/capture.miff; then
            convert /tmp/capture.miff -strip -define png:exclude-chunks=date,time "png:/out/$1.png"
            log "wrote $1.png ($(identify -format '%wx%h' "/out/$1.png"))"
            return 0
        fi
        sleep 1
    done
    log "couldn't grab the screen for $1"
    return 1
}

# --- The shot ---------------------------------------------------------------------------------
# shellcheck source=/dev/null
. "$SHOT_FILE"
