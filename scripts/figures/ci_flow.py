"""Outputs in CI: what one CI run does with a board, from a push to the artifact.

    pip install -r scripts/figures/requirements.txt
    python3 scripts/figures/ci_flow.py        # writes docs/assets/img/ic103-ci-flow.svg

The steps are the ones Lab 05's workflow runs: check out the commit, run ERC, DRC and
schematic parity in the pinned image (labs/common/kicad-image.txt), stop on an error, and
otherwise build the fabrication files and review images and keep them as an artifact.
"""
import schemdraw.elements as elm
import schemdraw.flow as flow

from circuit_style import drawing, save

TEXT_DROP = 0.11    # schemdraw puts the baseline on y; this centres the letters on it instead
NOTE = 11


def text(d, xy, s, halign="center", size=None):
    """Text at xy. right() stops it inheriting the last element's direction."""
    d.add(elm.Label().right().at((xy[0], xy[1] - TEXT_DROP)).label(s, halign=halign, fontsize=size))


def box(d, x, y, label, w=4.4, h=1.3, dashed=False):
    b = flow.Box(w=w, h=h).anchor("center").at((x, y)).label(label, fontsize=12)
    if dashed:
        b = b.linestyle("--")
    return d.add(b)


d = drawing()
d.config(margin=0.3)

# Top row: the push, the runner, the pinned image
push = box(d, 0, 0, "git push\nto your repository", w=3.8)
runner = box(d, 5.6, 0, "GitHub Actions runner\nchecks out the commit")
image = box(d, 11.6, 0, "kicad/kicad:10.0.8\npinned by its digest")
d.add(elm.Arrow().at(push.E).to(runner.W))
d.add(elm.Arrow().at(runner.E).to(image.W))

# The checks, and the decision they feed
checks = box(d, 11.6, -2.4, "ERC, DRC and\nschematic parity")
d.add(elm.Arrow().at(image.S).to(checks.N))
dec = d.add(flow.Decision(w=3.0, h=1.7).anchor("N").at((11.6, -3.55)).label("errors?", fontsize=12))
d.add(elm.Arrow().at(checks.S).to(dec.N))

# Yes: the run fails and nothing is built
fail = box(d, 5.6, -4.4, "the run fails\nlater steps are skipped", dashed=True)
d.add(elm.Arrow().at(dec.W).to(fail.E))
text(d, ((dec.W[0] + fail.E[0]) / 2, dec.W[1] + 0.3), "yes", size=NOTE)

# No: build the outputs and keep them
outs = box(d, 11.6, -7.0, "Gerbers and drill file, BOM,\nposition file, 3D render,\nSVG or PDF plots", w=5.0, h=1.8)
d.add(elm.Arrow().at(dec.S).to(outs.N))
text(d, (11.6 + 0.45, (dec.S[1] + outs.N[1]) / 2), "no", size=NOTE, halign="left")
art = box(d, 5.6, -7.0, "uploaded as an artifact\nof that run")
d.add(elm.Arrow().at(outs.W).to(art.E))

print(save(d, "ic103-ci-flow"))
