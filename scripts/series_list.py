"""Print the existing series (for Claude), with the last part number used in each."""
import yaml

from common import ROOT, load_episodes


def main():
    last = {}
    for e in load_episodes():
        if e.get("series") and e.get("part"):
            last[e["series"]] = max(last.get(e["series"], 0), int(e["part"]))
    print("# Existing series (slug — English / Hebrew — last part published)\n")
    for f in sorted((ROOT / "site" / "series").glob("*/series.yml")):
        slug = f.parent.name
        if slug.startswith("_"):
            continue
        s = yaml.safe_load(f.read_text())
        print(f"- {slug} — {s['title_en']} / {s.get('title_he', '')} — subtitle: {s.get('subtitle', '')} — last part: {last.get(slug, 'none')}")


if __name__ == "__main__":
    main()
