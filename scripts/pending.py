"""Look at episodes still waiting for approval (open pull requests).

A new recording is often the next part of a class whose earlier part is not merged yet.
This makes those episodes visible, so the new one continues the same series (same
picture, next part number) and can be checked against them for duplicates.

Usage: pending.py WORKDIR
Writes WORKDIR/pending/episodes/*.yml and WORKDIR/pending/transcripts/*.txt, and copies
series folders that so far exist only on an open pull request into site/series/.
"""
import json
import subprocess
import sys
from pathlib import Path

from common import ROOT, SHOW_DIR, SITE_DIR


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True, text=True).stdout


def main(work):
    out = Path(work) / "pending"
    (out / "episodes").mkdir(parents=True, exist_ok=True)
    (out / "transcripts").mkdir(parents=True, exist_ok=True)
    prs = json.loads(subprocess.run(
        ["gh", "pr", "list", "--state", "open", "--limit", "200", "--json", "number,headRefName"],
        check=True, capture_output=True, text=True).stdout)
    rel = SHOW_DIR.relative_to(ROOT).as_posix()
    rel = "" if rel == "." else rel + "/"
    for pr in sorted(prs, key=lambda p: p["number"]):  # oldest first: its series picture wins
        branch = pr["headRefName"]
        if not branch.startswith("episode/"):
            continue
        ref = f"refs/remotes/origin/{branch}"
        git("fetch", "-q", "--depth=1", "origin", f"+{branch}:{ref}")
        files = git("ls-tree", "-r", "--name-only", ref, "--",
                    f"{rel}episodes", f"{rel}transcripts", f"{rel}site/series").split()
        for f in files:
            if (ROOT / f).exists():
                continue
            name = f[len(rel):]
            if name.startswith("episodes/") and name.endswith(".yml"):
                dest = out / "episodes" / Path(f).name
            elif name.startswith("transcripts/") and name.endswith(".txt"):
                dest = out / "transcripts" / Path(f).name
            elif name.startswith("site/series/"):
                dest = SITE_DIR / name[len("site/"):]
            else:
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(subprocess.run(["git", "show", f"{ref}:{f}"], cwd=ROOT, check=True,
                                            capture_output=True).stdout)
            print(f"PR #{pr['number']}: {name}")


if __name__ == "__main__":
    main(sys.argv[1])
