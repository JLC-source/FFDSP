"""Print recent episode titles/descriptions so Claude can match the show's style.

Uses the imported episodes once there are enough; before the migration it reads
the old Spotify for Creators feed.
"""
import html
import re
import xml.etree.ElementTree as ET

import requests

from common import load_config, load_episodes


def strip_html(s):
    return html.unescape(re.sub(r"<[^>]+>", " ", s or "")).strip()


def main(limit=25):
    # Newest episodes first, so Claude can see an ongoing series (e.g. "part 1" → "part 2").
    rows = [(e["title"], strip_html(e.get("description", ""))) for e in reversed(load_episodes())]
    seen = {t for t, _ in rows}
    if len(rows) < 8 and load_config().get("legacy_feed_url"):
        xml = requests.get(load_config()["legacy_feed_url"], timeout=60).content
        items = ET.fromstring(xml).find("channel").findall("item")
        rows += [(i.findtext("title"), strip_html(i.findtext("description"))) for i in items
                 if i.findtext("title") not in seen]
    print(f"# Recent {load_config()['show']['title']} episodes (newest first)\n")
    if not rows:
        print("(No episodes yet: this is the first one. Follow the style rules in the instructions.)\n")
    for title, desc in rows[:limit]:
        print(f"- Title: {title}\n  Description: {desc}\n")


if __name__ == "__main__":
    main()
