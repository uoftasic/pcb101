#!/usr/bin/env python3
"""PB101 Lab 05 check: does your board repository's CI check the board and build everything a
fab and a reviewer need, and does it go red on a broken board?

    labs/common/kicad.sh python3 /w/labs/lab-05-fab-outputs-in-ci/src/check_ci.py REPO [--planted REV]

Run it through the lab's check.sh, from your board repository, so that it runs in the course's
pinned KiCad image. REPO is the repository's root folder (default: the current folder). It
runs `bash ci/build.sh all` there, the same script and stages your workflow runs, and then
checks what it built and what git sees:

  workflow   a workflow in .github/workflows/ runs ci/build.sh check, fab and images and
             uploads out/, and ci/kicad-image.txt names the image by its digest
  check      `ci/build.sh check` passes: no ERC or DRC errors, no unconnected items, no parity items
  gerbers    out/fab/ has a Gerber for each copper, mask and silkscreen layer and the outline,
             and a Gerber job file
  drill      a drill file in out/fab/ whose holes all lie inside the outline in the Gerbers
             (if they don't, the drill file and the Gerbers use different origins)
  bom        a CSV BOM in out/assembly/ that lists every footprint on the board that belongs in a BOM
  position   a CSV position file in out/assembly/, in millimetres, with every part where the board has it
  images     out/review/ has a top and a bottom render (PNG), a plot of each copper layer (SVG)
             and the schematic (PDF)
  gitignore  after the build, `git status` shows nothing untracked, and git tracks none of
             KiCad's local files (.kicad_prl, backups, lock files, fp-info-cache, .history/)
  planted    (with --planted REV) REV is an earlier commit of this branch on which
             `ci/build.sh check` fails on the board, not on the script

Exit status: 0 PASS, 1 FAIL, 2 the check couldn't run.
"""
import argparse
import csv
import glob
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "common"))
from kicad_sexpr import parse, children, child  # noqa: E402

LAYERS = ["F_Cu", "B_Cu", "F_Mask", "B_Mask", "F_Silkscreen", "B_Silkscreen", "Edge_Cuts"]
KICAD_LOCAL = [r"\.kicad_prl$", r"-backups/", r"\.lck$", r"(^|/)fp-info-cache$", r"(^|/)\.history/",
               r"_autosave-", r"\.kicad_(pcb|sch)-bak$"]


def run(cmd, cwd, **kw):
    return subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, **kw)


def git(repo, *args):
    r = run(["git", *args], repo)
    return r.returncode, r.stdout


def board_items(pcb):
    """Footprints on the board: ref -> (x, y, in_bom, in_pos), and the outline's corners."""
    with open(pcb, encoding="utf-8") as f:
        root = parse(f.read())
    fps = {}
    for fp in children(root, "footprint"):
        props = {p[1]: p[2] for p in children(fp, "property")}
        at = child(fp, "at")
        attr = child(fp, "attr") or []
        fps[props.get("Reference", "?")] = (float(at[1]), float(at[2]),
                                            "exclude_from_bom" not in attr, "exclude_from_pos_files" not in attr)
    return fps


def gerber_box(path):
    """Min and max X and Y of the coordinates in a Gerber file, in mm."""
    with open(path, encoding="utf-8", errors="replace") as f:
        text = f.read()
    m = re.search(r"%FSLAX(\d)(\d)Y(\d)(\d)\*%", text)
    dec = int(m.group(2)) if m else 6
    xs, ys = [], []
    x = y = 0
    for xm, ym in re.findall(r"^(?:G0?[123])?(?:X(-?\d+))?(?:Y(-?\d+))?(?:I-?\d+J-?\d+)?D0?[123]\*", text, re.M):
        if xm:
            x = int(xm) / 10 ** dec
        if ym:
            y = int(ym) / 10 ** dec
        if xm or ym:
            xs.append(x)
            ys.append(y)
    return (min(xs), min(ys), max(xs), max(ys)) if xs else None


def drill_hits(path):
    hits = []
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            m = re.match(r"^X(-?[\d.]+)Y(-?[\d.]+)", line.strip())
            if m:
                hits.append((float(m.group(1)), float(m.group(2))))
    return hits


def check_outputs(repo, name, rows):
    pcb = os.path.join(repo, name + ".kicad_pcb")
    fps = board_items(pcb)
    fab = os.path.join(repo, "out", "fab")
    asm = os.path.join(repo, "out", "assembly")
    rev = os.path.join(repo, "out", "review")

    # Gerbers: one per layer, any extension (.gbr, or the Protel ones), and the job file.
    files = os.listdir(fab) if os.path.isdir(fab) else []
    missing = [l for l in LAYERS if not any(re.search(rf"-{l}\.(gbr|g[a-z0-9]{{1,2}})$", f) for f in files)]
    job = [f for f in files if f.endswith(".gbrjob")]
    gbr = [f for f in files if re.search(r"\.(gbr|gtl|gbl|gto|gbo|gts|gbs|gtp|gbp|gm1)$", f)]
    if missing or not job:
        rows.append((False, "gerbers", "out/fab/ is missing " + ", ".join(
            [f"the {l.replace('_', '.')} Gerber" for l in missing] + ([] if job else ["the Gerber job file (.gbrjob)"]))))
    else:
        rows.append((True, "gerbers", f"{len(gbr)} Gerbers and {job[0]} in out/fab/"))

    # Drill: every hit inside the outline as the Gerbers draw it.
    drl = sorted(f for f in files if f.endswith(".drl"))
    edge = [f for f in files if re.search(r"-Edge_Cuts\.(gbr|gm1)$", f)]
    if not drl:
        rows.append((False, "drill", "no drill file (.drl) in out/fab/"))
    else:
        hits = [h for f in drl for h in drill_hits(os.path.join(fab, f))]
        box = gerber_box(os.path.join(fab, edge[0])) if edge else None
        if not hits:
            rows.append((False, "drill", f"{', '.join(drl)} has no holes in it"))
        elif box is None:
            rows.append((False, "drill", f"{len(hits)} holes in {', '.join(drl)}, but no outline Gerber to compare them with"))
        else:
            x0, y0, x1, y1 = box
            out = [h for h in hits if not (x0 <= h[0] <= x1 and y0 <= h[1] <= y1)]
            if out:
                rows.append((False, "drill", f"{len(out)} of {len(hits)} holes lie outside the outline in the Gerbers, "
                             f"for example ({out[0][0]:g}, {out[0][1]:g}); are the drill file and the Gerbers "
                             "using the same origin?"))
            else:
                rows.append((True, "drill", f"{', '.join(drl)}: {len(hits)} holes, all inside the outline"))

    # BOM: every footprint that belongs in a BOM, by reference.
    boms = sorted(glob.glob(os.path.join(asm, "*.csv")))
    bom = [b for b in boms if "bom" in os.path.basename(b).lower()]
    if not bom:
        rows.append((False, "bom", "no BOM in out/assembly/ (a .csv with 'bom' in its name)"))
    else:
        with open(bom[0], encoding="utf-8") as f:
            table = list(csv.reader(f))
        refs = set()
        if table:
            col = next((i for i, h in enumerate(table[0]) if h.strip().lower() in ("refs", "reference", "references", "ref")), 0)
            for r in table[1:]:
                if len(r) > col:
                    refs.update(x.strip() for x in re.split(r"[,\s]+", r[col]) if x.strip())
        # Expand ranges such as R1-R3.
        for r in list(refs):
            m = re.match(r"^([A-Z]+)(\d+)-([A-Z]+)?(\d+)$", r)
            if m:
                refs.update(f"{m.group(1)}{i}" for i in range(int(m.group(2)), int(m.group(4)) + 1))
        want = {r for r, v in fps.items() if v[2]}
        lost = sorted(want - refs)
        if lost:
            rows.append((False, "bom", f"{os.path.basename(bom[0])} doesn't list {', '.join(lost[:8])}"
                         + (" ..." if len(lost) > 8 else "")))
        else:
            rows.append((True, "bom", f"{os.path.basename(bom[0])}: {len(table) - 1} rows, every footprint listed"))

    # Position file: CSV, in mm, each part where the board has it.
    pos = [b for b in boms if "pos" in os.path.basename(b).lower()]
    if not pos:
        rows.append((False, "position", "no position file in out/assembly/ (a .csv with 'pos' in its name)"))
    else:
        with open(pos[0], encoding="utf-8") as f:
            table = list(csv.reader(f))
        head = [h.strip() for h in table[0]] if table else []
        if "PosX" not in head or "Ref" not in head:
            rows.append((False, "position", f"{os.path.basename(pos[0])} isn't KiCad's CSV position file "
                         "(no Ref and PosX columns); use --format csv"))
        else:
            ir, ix, iy = head.index("Ref"), head.index("PosX"), head.index("PosY")
            bad = []
            for r in table[1:]:
                ref = r[ir].strip()
                if ref in fps:
                    x, y = float(r[ix]), float(r[iy])
                    if abs(x - fps[ref][0]) > 0.01 or abs(abs(y) - fps[ref][1]) > 0.01:
                        bad.append((ref, x, y))
            if bad:
                ref, x, y = bad[0]
                rows.append((False, "position", f"{ref} is at ({x:g}, {y:g}) in {os.path.basename(pos[0])} and at "
                             f"({fps[ref][0]:g}, {fps[ref][1]:g}) mm on the board; use --units mm, and the same origin as the board"))
            else:
                rows.append((True, "position", f"{os.path.basename(pos[0])}: {len(table) - 1} parts, in mm, where the board has them"))

    # Review images.
    need = {"top render": r"top.*\.png$", "bottom render": r"bottom.*\.png$",
            "F.Cu plot": r"F_Cu.*\.svg$", "B.Cu plot": r"B_Cu.*\.svg$", "schematic PDF": r"\.pdf$"}
    have = os.listdir(rev) if os.path.isdir(rev) else []
    lost = [k for k, pat in need.items() if not any(re.search(pat, f) for f in have)]
    bad = []
    for f in have:
        p = os.path.join(rev, f)
        with open(p, "rb") as fh:
            head = fh.read(8)
        if f.endswith(".png") and head != b"\x89PNG\r\n\x1a\n":
            bad.append(f)
        if f.endswith(".pdf") and not head.startswith(b"%PDF"):
            bad.append(f)
    if lost or bad:
        rows.append((False, "images", "out/review/ is missing " + ", ".join(lost) if lost else
                     f"not a real image: {', '.join(bad)}"))
    else:
        rows.append((True, "images", f"{len(have)} files in out/review/: renders, copper plots and the schematic"))


def check_git(repo, rows):
    rc, out = git(repo, "status", "--porcelain", "--untracked-files=all")
    if rc != 0:
        rows.append((False, "gitignore", "git status failed: " + out.strip().splitlines()[-1]))
        return
    untracked = [l[3:] for l in out.splitlines() if l.startswith("??")]
    _, tracked = git(repo, "ls-files")
    local = [f for f in tracked.splitlines() if any(re.search(p, f) for p in KICAD_LOCAL)]
    _, ignored_tracked = git(repo, "ls-files", "--cached", "--ignored", "--exclude-standard")
    ignored_tracked = [f for f in ignored_tracked.splitlines() if f]
    if not os.path.exists(os.path.join(repo, ".gitignore")):
        rows.append((False, "gitignore", f"no .gitignore; after the build git sees {len(untracked)} untracked "
                     f"file(s): {', '.join(untracked[:4])}" + (" ..." if len(untracked) > 4 else "")))
    elif untracked:
        rows.append((False, "gitignore", f"after the build git sees {len(untracked)} untracked file(s): "
                     f"{', '.join(untracked[:4])}" + (" ..." if len(untracked) > 4 else "")
                     + "; ignore them or commit them"))
    elif local or ignored_tracked:
        f = (local or ignored_tracked)[0]
        rows.append((False, "gitignore", f"git still tracks {f}; `git rm --cached {f}` and commit"))
    else:
        rows.append((True, "gitignore", "nothing untracked after the build, and none of KiCad's local files tracked"))


def check_planted(repo, rev, rows):
    rc, sha = git(repo, "rev-parse", "--verify", "--quiet", rev + "^{commit}")
    if rc != 0:
        rows.append((False, "planted", f"{rev} isn't a commit in this repository"))
        return
    sha = sha.strip()
    _, head = git(repo, "rev-parse", "HEAD")
    if sha == head.strip():
        rows.append((False, "planted", f"{rev} is the commit you're on; name the commit with the planted error, "
                     "and fix it in a later commit"))
        return
    rc, _ = git(repo, "merge-base", "--is-ancestor", sha, "HEAD")
    if rc != 0:
        rows.append((False, "planted", f"{sha[:7]} isn't an earlier commit of the branch you're on"))
        return
    if run(["git", "cat-file", "-e", f"{sha}:ci/build.sh"], repo).returncode != 0:
        rows.append((False, "planted", f"{sha[:7]} has no ci/build.sh; plant the error after the workflow is in"))
        return
    tmp = tempfile.mkdtemp(prefix="pb101-planted-")
    try:
        r = subprocess.run(["git", "archive", "--format=tar", sha], cwd=repo, stdout=subprocess.PIPE)
        with tarfile.open(fileobj=io.BytesIO(r.stdout)) as t:
            try:
                t.extractall(tmp, filter="data")
            except TypeError:           # Python before 3.12
                t.extractall(tmp)
        b = run(["bash", "ci/build.sh", "check"], tmp)
        summary = os.path.join(tmp, "out", "reports", "summary.json")
        verdict = None
        if os.path.exists(summary):
            with open(summary) as f:
                verdict = json.load(f)
        if b.returncode == 0:
            rows.append((False, "planted", f"`ci/build.sh check` passes on {sha[:7]}, so CI would be green there"))
        elif not verdict or verdict.get("verdict") != "FAIL":
            rows.append((False, "planted", f"`ci/build.sh check` exits {b.returncode} on {sha[:7]} without a board "
                         "check verdict: the script broke, not the board"))
        else:
            what = ", ".join(f"{x['key']} {x['got']}" for x in verdict["failures"])
            rows.append((True, "planted", f"{sha[:7]} fails the board check ({what}), and the commits after it fix it"))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("repo", nargs="?", default=".")
    ap.add_argument("--planted", metavar="REV", help="the commit with the error you planted in Part 5")
    args = ap.parse_args()
    repo = os.path.abspath(args.repo)
    pros = glob.glob(os.path.join(repo, "*.kicad_pro"))
    if len(pros) != 1:
        print(f"check_ci: {repo} holds {len(pros)} .kicad_pro files; run this in your board repository", file=sys.stderr)
        return 2
    name = os.path.basename(pros[0])[:-len(".kicad_pro")]
    if run(["git", "rev-parse", "--show-toplevel"], repo).returncode != 0:
        print(f"check_ci: {repo} isn't a git repository", file=sys.stderr)
        return 2
    rows = []

    # The workflow file and the image it names.
    wfs = sorted(glob.glob(os.path.join(repo, ".github", "workflows", "*.y*ml")))
    text = ""
    for w in wfs:
        with open(w, encoding="utf-8") as f:
            text += f.read()
    image = ""
    if os.path.exists(os.path.join(repo, "ci", "kicad-image.txt")):
        with open(os.path.join(repo, "ci", "kicad-image.txt")) as f:
            image = f.readline().strip()
    lost = [s for s in ("ci/build.sh check", "ci/build.sh fab", "ci/build.sh images", "upload-artifact")
            if s not in text]
    if not wfs:
        rows.append((False, "workflow", "no workflow in .github/workflows/"))
    elif lost:
        rows.append((False, "workflow", f"{os.path.relpath(wfs[0], repo)} doesn't run {', '.join(lost)}"))
    elif "@sha256:" not in image:
        rows.append((False, "workflow", "ci/kicad-image.txt doesn't name the image by its digest (…@sha256:…)"))
    else:
        rows.append((True, "workflow", f"{os.path.relpath(wfs[0], repo)} runs check, fab and images in "
                     f"{image.split('@')[0]} by digest, and uploads out/"))

    if not os.path.exists(os.path.join(repo, "ci", "build.sh")):
        print("check_ci: no ci/build.sh; copy the lab's starter/ into your repository first", file=sys.stderr)
        return 2
    shutil.rmtree(os.path.join(repo, "out"), ignore_errors=True)
    print("PB101 Lab 05: bash ci/build.sh all, as your workflow runs it", flush=True)
    print("-" * 72, flush=True)
    b = subprocess.run(["bash", "ci/build.sh", "all"], cwd=repo, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, text=True)
    # The renders print a line per layer they build; leave those out.
    noise = re.compile(r"^(Loading|Build |Create |Load |Reload time|Rendering|Simplif|Calculating|"
                       r"Successfully created|\s*$)")
    print("\n".join(l for l in b.stdout.splitlines() if not noise.match(l)), flush=True)
    print("-" * 72, flush=True)
    summary = os.path.join(repo, "out", "reports", "summary.json")
    if b.returncode == 0:
        rows.append((True, "check", "the board check passes"))
    elif os.path.exists(summary):
        with open(summary) as f:
            v = json.load(f)
        rows.append((False, "check", "the board check fails: " + ", ".join(f"{x['key']} {x['got']} (want {x['want']})"
                                                                          for x in v.get("failures", []))
                     + "; the fab and images stages didn't run"))
    else:
        rows.append((False, "check", f"ci/build.sh exited {b.returncode} before the board check had a verdict"))

    check_outputs(repo, name, rows)
    check_git(repo, rows)
    if args.planted:
        check_planted(repo, args.planted, rows)

    print()
    print("PB101 Lab 05 check")
    print(f"  repository  {repo}")
    print()
    for ok, what, detail in rows:
        print(f"  {'ok  ' if ok else 'FAIL'}  {what:10} {detail}")
    failed = sum(1 for ok, *_ in rows if not ok)
    print()
    print(f"{'PASS' if not failed else 'FAIL'}  {name}: {len(rows) - failed} of {len(rows)} Lab 05 checks ok"
          + ("" if args.planted else "; add --planted REV once you've done Part 5"))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
