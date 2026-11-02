"""Warn when a new recording looks like one that is already published or waiting for approval.

Compares the new transcript with the others, phrase by phrase; the same recording gives a
nearly identical transcript even when the file itself is different (another name or format).

Usage: duplicates.py WORKDIR   → writes WORKDIR/duplicate.json if a likely duplicate is found
"""
import json
import re
import sys
from pathlib import Path

from common import TRANSCRIPTS_DIR

THRESHOLD = 0.35  # share of 5-word phrases in common; different classes score well under 0.1


def phrases(text, n=5):
    words = re.findall(r"\w+", text.lower())
    return {" ".join(words[i:i + n]) for i in range(len(words) - n + 1)}


def main(work):
    work = Path(work)
    new = phrases((work / "transcript.txt").read_text())
    if not new:
        return
    best = (0.0, None)
    for t in [*TRANSCRIPTS_DIR.glob("*.txt"), *(work / "pending" / "transcripts").glob("*.txt")]:
        old = phrases(t.read_text())
        if old:
            score = len(new & old) / min(len(new), len(old))
            best = max(best, (score, t.stem))
    print(f"Most similar earlier class: {best[1]} ({best[0]:.0%} of phrases in common)")
    if best[0] >= THRESHOLD:
        (work / "duplicate.json").write_text(json.dumps({"of": best[1], "score": round(best[0], 2)}))
        print("Likely duplicate")


if __name__ == "__main__":
    main(sys.argv[1])
