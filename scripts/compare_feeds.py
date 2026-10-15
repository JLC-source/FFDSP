"""Check the new feed against the old Spotify for Creators feed before switching.

Usage: compare_feeds.py NEW_FEED.xml   (file path or URL)
Fails if any old episode is missing, its GUID changed, or titles/dates differ.
"""
import sys
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime

import requests

from common import load_config


def items(src):
    data = requests.get(src, timeout=120).content if src.startswith("http") else open(src, "rb").read()
    return {i.findtext("guid").strip(): i for i in ET.fromstring(data).find("channel").findall("item")}


def main(new_src):
    old, new = items(load_config()["legacy_feed_url"]), items(new_src)
    problems = []
    for guid, o in old.items():
        n = new.get(guid)
        if n is None:
            problems.append(f"MISSING: {o.findtext('title')}")
            continue
        if o.findtext("title").strip() != n.findtext("title").strip():
            problems.append(f"TITLE CHANGED: {o.findtext('title')!r} → {n.findtext('title')!r}")
        if parsedate_to_datetime(o.findtext("pubDate")) != parsedate_to_datetime(n.findtext("pubDate")):
            problems.append(f"DATE CHANGED: {o.findtext('title')}")
    extra = [n.findtext("title") for g, n in new.items() if g not in old]
    print(f"Old feed: {len(old)} episodes. New feed: {len(new)} episodes "
          f"({len(old) - len([p for p in problems if p.startswith('MISSING')])} matched by GUID, {len(extra)} new).")
    for t in extra:
        print(f"  new episode: {t}")
    for p in problems:
        print("  " + p)
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main(sys.argv[1])
