#!/usr/bin/env python3
"""Fetch the Tiny Tapeout boards and libraries the labs use, at pinned commits.

    python3 labs/common/fetch_boards.py            # everything in upstream.json
    python3 labs/common/fetch_boards.py breakout-pcb tinytapeout-kicad-libs
    python3 labs/common/fetch_boards.py --list     # what would be fetched, and the licences

Needs git and Python 3.8 or newer, and nothing else. Without them on your machine, run it
in the course image instead: labs/common/kicad.sh python3 labs/common/fetch_boards.py

Each source in upstream.json is checked out at its commit into labs/common/upstream/<dest>,
with git's partial clone and sparse checkout, so only the listed files are downloaded.
A source that is already at its commit with no local changes is left alone. A source you
have edited (for example by saving a board in KiCad) is never overwritten unless you pass
--force. Exit status: 0 when every source is at its commit, 1 otherwise.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MANIFEST = os.path.join(HERE, "upstream.json")
DEFAULT_DEST = os.path.join(HERE, "upstream")


def git(repo, *args, capture=True):
    cmd = ["git", "-C", repo, "-c", "advice.detachedHead=false", *args]
    r = subprocess.run(cmd, stdout=subprocess.PIPE if capture else None,
                       stderr=subprocess.PIPE, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed in {repo}:\n{r.stderr.strip()}")
    return (r.stdout or "").strip()


def head_of(repo):
    try:
        return git(repo, "rev-parse", "HEAD")
    except RuntimeError:
        return None


def local_changes(repo):
    """Tracked files that differ from the checked-out commit (untracked files don't count:
    KiCad writes backups, .kicad_prl and fp-info-cache next to a board you open)."""
    out = git(repo, "status", "--porcelain", "--untracked-files=no")
    # Each line is "XY path". git() strips the output, which takes the leading space off
    # the first line's status, so cut the two status characters and then the spaces.
    return [line[2:].strip() for line in out.splitlines() if line.strip()]


def fetch(src, root, force):
    dest = os.path.join(root, src["dest"])
    sha = src["commit"]
    if os.path.isdir(os.path.join(dest, ".git")):
        if head_of(dest) == sha:
            changed = local_changes(dest)
            if not changed:
                return "already at", dest
            if not force:
                raise RuntimeError(
                    f"{dest} has local changes to "
                    + (f"1 file, {changed[0]}" if len(changed) == 1
                       else f"{len(changed)} files, for example {changed[0]}")
                    + ". Rerun with --force to discard them.")
    elif os.path.exists(dest) and os.listdir(dest):
        if not force:
            raise RuntimeError(f"{dest} exists and isn't a git checkout. Remove it, or rerun with --force.")
        shutil.rmtree(dest)

    os.makedirs(dest, exist_ok=True)
    if not os.path.isdir(os.path.join(dest, ".git")):
        git(dest, "init", "-q")
        git(dest, "remote", "add", "origin", src["url"])
    else:
        git(dest, "remote", "set-url", "origin", src["url"])

    # Sparse checkout in non-cone mode: exactly the patterns in the manifest.
    git(dest, "config", "core.sparseCheckout", "true")
    git(dest, "config", "core.sparseCheckoutCone", "false")
    info = os.path.join(dest, ".git", "info")
    os.makedirs(info, exist_ok=True)
    with open(os.path.join(info, "sparse-checkout"), "w") as f:
        f.write("\n".join(src["paths"]) + "\n")

    # One commit, no history, and file contents only for what the checkout needs.
    git(dest, "fetch", "-q", "--depth", "1", "--filter=blob:none", "origin", sha)
    git(dest, "checkout", "-q", "--force", "--detach", sha)
    got = head_of(dest)
    if got != sha:
        raise RuntimeError(f"{dest} is at {got} after checkout, expected {sha}")
    return "fetched", dest


def size_of(path):
    total = 0
    for dp, dns, fns in os.walk(path):
        if ".git" in dns:
            dns.remove(".git")
        for fn in fns:
            fp = os.path.join(dp, fn)
            if not os.path.islink(fp):
                total += os.path.getsize(fp)
    return total


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("names", nargs="*", help="sources to fetch (default: all)")
    ap.add_argument("--dest", default=DEFAULT_DEST, help="where to put them (default: %(default)s)")
    ap.add_argument("--force", action="store_true", help="discard local changes to fetched files")
    ap.add_argument("--list", action="store_true", help="list the sources and exit")
    args = ap.parse_args()

    with open(MANIFEST) as f:
        sources = json.load(f)["sources"]
    known = {s["name"] for s in sources}
    unknown = [n for n in args.names if n not in known]
    if unknown:
        print(f"unknown source{'' if len(unknown) == 1 else 's'}: {', '.join(unknown)}; "
              f"known: {', '.join(sorted(known))}", file=sys.stderr)
        return 2
    if args.names:
        sources = [s for s in sources if s["name"] in args.names]

    if args.list:
        for s in sources:
            print(f"{s['name']:28} {s['commit'][:7]}  {s['date']}  {s['url']}")
            print(f"{'':28} licence: {s['license']}")
            print(f"{'':28} into:    upstream/{s['dest']}")
        return 0

    if shutil.which("git") is None:
        print("git isn't on your PATH. Install git, or run this in the course image:\n"
              "  labs/common/kicad.sh python3 labs/common/fetch_boards.py", file=sys.stderr)
        return 2

    failed = 0
    # Parents before children: tinytapeout-kicad-libs lives inside breakout-pcb's tree.
    for s in sorted(sources, key=lambda s: s["dest"].count("/")):
        try:
            what, dest = fetch(s, args.dest, args.force)
            mb = size_of(dest) / 1e6
            print(f"{what:10} {s['name']:28} {s['commit'][:7]}  {mb:6.1f} MB  {os.path.relpath(dest)}")
        except RuntimeError as e:
            failed += 1
            print(f"FAILED     {s['name']:28} {e}", file=sys.stderr)
    if failed:
        print(f"{failed} {'source is' if failed == 1 else 'sources are'} not at "
              f"{'its pinned commit' if failed == 1 else 'their pinned commits'}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
