#!/usr/bin/env python3
"""Run a board repository's GitHub Actions workflow on this machine, step by step.

    python3 labs/lab-05-fab-outputs-in-ci/src/run_workflow.py REPO [--workflow FILE] [--artifact DIR]

We can't push to GitHub from the course's build machine, so this is how the Lab 05 workflow
was tested: it reads .github/workflows/board.yml (or FILE) in REPO, and runs every `run:`
step of its one job with bash, in REPO, in order, the way a runner would. A failed step
skips the steps after it, except those with `if: always()`. `uses:` steps are stood in for:
actions/checkout does nothing (REPO is already the checkout), and actions/upload-artifact
copies its `path` into DIR (default: REPO/../artifact), which is what you'd download from
the run's page. GITHUB_ENV works as on GitHub: lines written to it become environment
variables for the later steps.

It needs Python 3 with PyYAML and Docker on this machine. It prints each step's name, its
output, and its exit status, then the run's result: success or failure. Exit status 0 if
every step that ran succeeded.
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile

try:
    import yaml
except ImportError:
    sys.exit("run_workflow: needs PyYAML (pip install pyyaml, or apt install python3-yaml)")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("repo")
    ap.add_argument("--workflow", default=".github/workflows/board.yml")
    ap.add_argument("--artifact", help="where upload-artifact steps copy to (default: REPO/../artifact)")
    args = ap.parse_args()
    repo = os.path.abspath(args.repo)
    with open(os.path.join(repo, args.workflow)) as f:
        wf = yaml.safe_load(f)
    jobs = wf["jobs"]
    if len(jobs) != 1:
        sys.exit(f"run_workflow: {args.workflow} has {len(jobs)} jobs; this runner handles one")
    (job_name, job), = jobs.items()
    art_dir = os.path.abspath(args.artifact or os.path.join(repo, "..", "artifact"))

    env = dict(os.environ)
    env_file = tempfile.NamedTemporaryFile(prefix="github-env-", delete=False)
    env_file.close()
    env.update({"GITHUB_ENV": env_file.name, "GITHUB_WORKSPACE": repo, "CI": "true",
                "GITHUB_STEP_SUMMARY": os.devnull})
    failed = False
    print(f"workflow {wf.get('name', '?')}, job {job_name}", flush=True)
    for i, step in enumerate(job["steps"], 1):
        name = step.get("name") or step.get("uses") or step.get("run", "").splitlines()[0]
        cond = str(step.get("if", "success()"))
        if failed and "always()" not in cond and "failure()" not in cond:
            print(f"\n--- step {i}: {name}: skipped, because an earlier step failed", flush=True)
            continue
        print(f"\n--- step {i}: {name}", flush=True)
        if "uses" in step:
            action = step["uses"].split("@")[0]
            if action == "actions/checkout":
                print("(the repository is already checked out here)", flush=True)
                rc = 0
            elif action == "actions/upload-artifact":
                w = step.get("with", {})
                src = os.path.join(repo, w["path"])
                dst = os.path.join(art_dir, w["name"])
                shutil.rmtree(dst, ignore_errors=True)
                if os.path.exists(src):
                    shutil.copytree(src, dst)
                    n = sum(len(fs) for _, _, fs in os.walk(dst))
                    print(f"artifact {w['name']}: {n} files, copied to {dst}", flush=True)
                else:
                    print(f"artifact {w['name']}: nothing at {w['path']}", flush=True)
                rc = 0
            else:
                print(f"run_workflow: no stand-in for {step['uses']}", flush=True)
                rc = 1
        else:
            r = subprocess.run(["bash", "-e", "-c", step["run"]], cwd=repo, env=env)
            rc = r.returncode
            with open(env_file.name) as f:
                for line in f:
                    if "=" in line:
                        k, v = line.rstrip("\n").split("=", 1)
                        env[k] = v
        print(f"--- step {i}: exit status {rc}", flush=True)
        if rc != 0:
            failed = True
    os.unlink(env_file.name)
    print(f"\nrun result: {'failure' if failed else 'success'}", flush=True)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
