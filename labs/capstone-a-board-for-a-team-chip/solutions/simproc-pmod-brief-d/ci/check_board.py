#!/usr/bin/env python3
"""IC103 board check: ERC, DRC and schematic parity from kicad-cli's JSON reports.

    labs/common/kicad.sh python3 labs/common/check_board.py path/to/board.kicad_pro

The argument is a .kicad_pro, .kicad_sch or .kicad_pcb, or a folder holding exactly one
.kicad_pro. The schematic and the board must share its name, as KiCad saves them.

The check runs three reports through kicad-cli, with every severity included:

  kicad-cli sch erc --format json --severity-all --units mm
  kicad-cli pcb drc --format json --severity-all --schematic-parity --refill-zones --units mm

and counts what they contain. Items the designer marked as excluded in KiCad are counted
separately and never fail the check. With no expectations file, the check PASSes when there
are no ERC errors, no DRC errors, no unconnected items and no parity items of any severity.
Warnings are listed but don't fail it.

A board that is meant to have errors (a board you're asked to review, say) carries its
expected counts in a check-expect.json next to the .kicad_pro, or in a file given with
--expect. Each key is "<check>.<severity>" or "<check>.<severity>.<type>", where <check> is
erc, drc, unconnected or parity and <severity> is error, warning or excluded, and the check
PASSes only if every listed count matches exactly. For example:

  {"erc.error": 10, "erc.error.power_pin_not_driven": 8, "drc.error": 0,
   "unconnected.error": 0, "parity.error": 0, "parity.warning": 0}

Exit status: 0 PASS, 1 FAIL, 2 the check couldn't run (a file is missing, or kicad-cli
failed to load it).
"""
import argparse
import collections
import glob
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
CHECKS = ("erc", "drc", "unconnected", "parity")
SEVERITIES = ("error", "warning", "excluded")
DEFAULT_RULES = {"erc.error": 0, "drc.error": 0, "unconnected.error": 0,
                 "parity.error": 0, "parity.warning": 0}


def pinned_image():
    try:
        with open(os.path.join(HERE, "kicad-image.txt")) as f:
            return f.readline().strip()
    except OSError:
        return ""


def pinned_version(image):
    # "kicad/kicad:10.0.8@sha256:..." -> "10.0.8"
    tag = image.split("@")[0]
    return tag.rsplit(":", 1)[1] if ":" in tag else ""


def seed_library_tables():
    """Give this HOME the image's default global library tables if it has none.
    labs/common/image-entry.sh does the same; this covers a plain `docker run`."""
    template = "/usr/share/kicad/template"
    cfg = os.path.join(os.path.expanduser("~"), ".config", "kicad", "10.0")
    if not os.path.isdir(template):
        return
    for name in ("fp-lib-table", "sym-lib-table"):
        if not os.path.exists(os.path.join(cfg, name)):
            os.makedirs(cfg, exist_ok=True)
            shutil.copy(os.path.join(template, name), os.path.join(cfg, name))


def find_project(arg):
    if os.path.isdir(arg):
        pros = sorted(glob.glob(os.path.join(arg, "*.kicad_pro")))
        if len(pros) != 1:
            raise SystemExit(f"check_board: {arg} holds {len(pros)} .kicad_pro files; name one")
        arg = pros[0]
    stem, ext = os.path.splitext(arg)
    if ext not in (".kicad_pro", ".kicad_sch", ".kicad_pcb"):
        raise SystemExit(f"check_board: {arg} isn't a .kicad_pro, .kicad_sch or .kicad_pcb")
    return stem


def shown(path):
    """A path as the student typed it: relative when it's under the current folder."""
    rel = os.path.relpath(path)
    return os.path.abspath(path) if rel.startswith("..") else rel


def run(cmd):
    r = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    return r.returncode, r.stdout


def tally(items, check, counts, by_type, listed):
    for v in items:
        sev = "excluded" if v.get("excluded") else v.get("severity", "error")
        counts[f"{check}.{sev}"] += 1
        by_type[f"{check}.{sev}.{v.get('type', '?')}"] += 1
        listed[(check, sev)].append(v)


def describe(v):
    where = "; ".join(i.get("description", "") for i in v.get("items", []))
    return f"{v.get('description', '')}" + (f"  [{where}]" if where else "")


def main():
    ap = argparse.ArgumentParser(description="ERC, DRC and schematic parity, with a PASS or FAIL.",
                                 epilog="Run it through labs/common/kicad.sh so that it uses the pinned KiCad.")
    ap.add_argument("project", help=".kicad_pro, .kicad_sch, .kicad_pcb, or a folder with one .kicad_pro")
    ap.add_argument("--expect", help="expected counts (default: check-expect.json next to the project, if any)")
    ap.add_argument("--no-refill", action="store_true", help="don't refill zones before DRC")
    ap.add_argument("--reports", help="keep erc.json and drc.json in this folder")
    ap.add_argument("--summary", help="write the counts and the verdict to this JSON file")
    ap.add_argument("--show", type=int, default=20, help="list up to this many errors per check (default 20)")
    args = ap.parse_args()

    stem = find_project(args.project)
    sch, pcb = stem + ".kicad_sch", stem + ".kicad_pcb"
    name = shown(stem + ".kicad_pro")
    missing = [p for p in (sch, pcb) if not os.path.exists(p)]
    if missing:
        print(f"check_board: missing {', '.join(shown(p) for p in missing)}", file=sys.stderr)
        return 2
    if shutil.which("kicad-cli") is None:
        print("check_board: kicad-cli isn't on the PATH. Run this through labs/common/kicad.sh,\n"
              "which runs it in the course's pinned KiCad image.", file=sys.stderr)
        return 2

    image = os.environ.get("IC103_KICAD_IMAGE", "")
    want_version = pinned_version(pinned_image())
    seed_library_tables()
    _, version = run(["kicad-cli", "version"])
    version = version.strip().splitlines()[-1] if version.strip() else "?"

    expect_file = args.expect
    if expect_file is None and os.path.exists(os.path.join(os.path.dirname(stem), "check-expect.json")):
        expect_file = os.path.join(os.path.dirname(stem), "check-expect.json")
    if expect_file:
        with open(expect_file) as f:
            rules = {k: v for k, v in json.load(f).items() if not k.startswith("comment")}
        bad = [k for k in rules if k.split(".")[0] not in CHECKS or len(k.split(".")) < 2
               or k.split(".")[1] not in SEVERITIES]
        if bad:
            print(f"check_board: {expect_file}: keys must look like erc.error or drc.warning.<type>; "
                  f"not {', '.join(bad)}", file=sys.stderr)
            return 2
    else:
        rules = DEFAULT_RULES

    out = args.reports or tempfile.mkdtemp(prefix="ic103-check-")
    os.makedirs(out, exist_ok=True)
    erc_json, drc_json = os.path.join(out, "erc.json"), os.path.join(out, "drc.json")

    rc, log = run(["kicad-cli", "sch", "erc", "--format", "json", "--severity-all",
                   "--units", "mm", "-o", erc_json, sch])
    if rc != 0 or not os.path.exists(erc_json):
        print(f"check_board: kicad-cli sch erc exited {rc}:\n{log}", file=sys.stderr)
        return 2
    drc_cmd = ["kicad-cli", "pcb", "drc", "--format", "json", "--severity-all",
               "--schematic-parity", "--units", "mm", "-o", drc_json, pcb]
    if not args.no_refill:
        drc_cmd.insert(-3, "--refill-zones")
    rc, log = run(drc_cmd)
    if rc != 0 or not os.path.exists(drc_json):
        print(f"check_board: kicad-cli pcb drc exited {rc}:\n{log}", file=sys.stderr)
        return 2

    with open(erc_json) as f:
        erc = json.load(f)
    with open(drc_json) as f:
        drc = json.load(f)

    counts, by_type, listed = collections.Counter(), collections.Counter(), collections.defaultdict(list)
    tally([v for s in erc.get("sheets", []) for v in s.get("violations", [])], "erc", counts, by_type, listed)
    tally(drc.get("violations", []), "drc", counts, by_type, listed)
    tally(drc.get("unconnected_items", []), "unconnected", counts, by_type, listed)
    tally(drc.get("schematic_parity", []), "parity", counts, by_type, listed)

    def count(key):
        return by_type[key] if len(key.split(".")) > 2 else counts[key]

    failures = [(k, count(k), v) for k, v in rules.items() if count(k) != v]
    verdict = "FAIL" if failures else "PASS"

    print("IC103 board check")
    print(f"  project   {name}")
    note = ""
    if version != want_version:
        note = f"  (the course pins {want_version}, so counts can differ from the lab pages)"
    print(f"  kicad     {version}{note}")
    print(f"  image     {image or 'not recorded (labs/common/kicad.sh records it)'}")
    print(f"  rules     {shown(expect_file) if expect_file else 'no errors, no unconnected items, no parity items'}")
    print()
    print(f"  {'':12}{'errors':>8}{'warnings':>10}{'excluded':>10}")
    for c in CHECKS:
        print(f"  {c.upper() if c in ('erc', 'drc') else c:12}{counts[c + '.error']:>8}"
              f"{counts[c + '.warning']:>10}{counts[c + '.excluded']:>10}")
    print()

    for c in CHECKS:
        errs = listed[(c, "error")]
        if c == "parity":
            errs = errs + listed[(c, "warning")]
        if errs:
            label = c.upper() if c in ("erc", "drc") else c
            print(f"  {label} {'items' if c == 'parity' else 'errors'} ({len(errs)}):")
            for v in errs[:args.show]:
                print(f"    {v.get('type', '?'):24} {describe(v)}")
            if len(errs) > args.show:
                print(f"    ... and {len(errs) - args.show} more (--show {len(errs)} lists them all)")
            print()
    for c in CHECKS:
        for sev in ("warning", "excluded"):
            if c == "parity" and sev == "warning":
                continue
            kinds = sorted(((k.split(".", 2)[2], n) for k, n in by_type.items()
                            if k.startswith(f"{c}.{sev}.")), key=lambda t: (-t[1], t[0]))
            if kinds:
                label = c.upper() if c in ("erc", "drc") else c
                plural = {"warning": "warnings", "excluded": "excluded"}[sev]
                print(f"  {label} {plural} by type: " + ", ".join(f"{t} {n}" for t, n in kinds))
    if any(by_type[k] for k in by_type if ".warning." in k or ".excluded." in k):
        print()

    if args.reports:
        print(f"  reports   {shown(erc_json)}, {shown(drc_json)}")
        print()

    if failures:
        for k, got, want in failures:
            print(f"FAIL  {k}: {got} (want {want})")
    else:
        print(f"PASS  {name}")

    if args.summary:
        with open(args.summary, "w") as f:
            json.dump({"project": name, "verdict": verdict, "kicad_version": version, "image": image,
                       "rules": rules, "counts": dict(counts), "by_type": dict(by_type),
                       "failures": [{"key": k, "got": g, "want": w} for k, g, w in failures]},
                      f, indent=2, sort_keys=True)
            f.write("\n")
    if not args.reports:
        shutil.rmtree(out, ignore_errors=True)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
