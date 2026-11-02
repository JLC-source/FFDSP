"""Print the existing series (for Claude), with the last part number used in each."""
import sys
from pathlib import Path

import yaml

from common import SITE_DIR, load_episodes


def main(pending_dir=None):
    """pending_dir: episodes still waiting for approval (from pending.py) also count."""
    pending = [yaml.safe_load(p.read_text()) for p in sorted(Path(pending_dir).glob("*.yml"))] if pending_dir else []
    last = {}
    for e in load_episodes() + pending:
        if e.get("series") and e.get("part"):
            last[e["series"]] = max(last.get(e["series"], 0), int(e["part"]))
    print("# Existing series (slug — English / Hebrew — last part published or waiting for approval)\n")
    for f in sorted((SITE_DIR / "series").glob("*/series.yml")):
        slug = f.parent.name
        if slug.startswith("_"):
            continue
        s = yaml.safe_load(f.read_text())
        print(f"- {slug} — {s['title_en']} / {s.get('title_he', '')} — subtitle: {s.get('subtitle', '')} — last part: {last.get(slug, 'none')}")


if __name__ == "__main__":
    main(*sys.argv[1:2])
