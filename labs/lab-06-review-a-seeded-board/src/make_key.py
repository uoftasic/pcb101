#!/usr/bin/env python3
"""Hash solutions/faults.json into data/review-key.json, the key the Lab 06 check reads.

    python3 labs/lab-06-review-a-seeded-board/src/make_key.py

For each planted fault the key holds the SHA-256 of every (word, checklist line) pair that
finds it, so the check can tell whether a review row finds a fault without the key saying
what the faults are. It's a speed bump, not a lock: the plain list is in solutions/, and the
pairs are few enough to guess. Run it again whenever faults.json changes.
"""
import hashlib
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.dirname(HERE)
SALT = "pcb101-lab06"


def digest(word, line):
    return hashlib.sha256(f"{SALT}|{word}|{line}".encode()).hexdigest()


def main():
    with open(os.path.join(LAB, "solutions", "faults.json")) as f:
        faults = json.load(f)["faults"]
    key = {"comment": "Made by src/make_key.py from solutions/faults.json; see its docstring.",
           "salt": SALT,
           "faults": [sorted(digest(w, l) for w in fault["where"] for l in fault["lines"]) for fault in faults]}
    with open(os.path.join(LAB, "data", "review-key.json"), "w") as f:
        json.dump(key, f, indent=1)
        f.write("\n")
    print(f"wrote data/review-key.json: {len(faults)} faults")


if __name__ == "__main__":
    main()
