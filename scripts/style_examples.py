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
    eps = load_episodes()
    if len(eps) >= 8:
        rows = [(e["title"], e.get("description", "")) for e in reversed(eps)]
    else:
        xml = requests.get(load_config()["legacy_feed_url"], timeout=60).content
        items = ET.fromstring(xml).find("channel").findall("item")
        rows = [(i.findtext("title"), strip_html(i.findtext("description"))) for i in items]
    print("# Recent Food for the Soul episodes (newest first)\n")
    for title, desc in rows[:limit]:
        print(f"- Title: {title}\n  Description: {desc}\n")


if __name__ == "__main__":
    main()
