# KiCad GUI screenshots: the course's pinned KiCad image, plus an X server to draw into.
#
# KiCad's image is made for kicad-cli and has no display. This adds Xvfb (a virtual X
# server that draws into memory), openbox (a small window manager, so windows can be
# focused, raised and maximized), xdotool (to type keys and find windows), the X11
# utilities (xdpyinfo, xwininfo) and ImageMagick (`import`, to capture the screen as PNG).
# Nothing in KiCad changes. Build it with scripts/screenshots/kicad/build.sh.
ARG KICAD_IMAGE
FROM ${KICAD_IMAGE}
USER root
RUN apt-get update \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        xvfb xauth x11-apps x11-utils xdotool openbox imagemagick \
 && rm -rf /var/lib/apt/lists/*
USER kicad
