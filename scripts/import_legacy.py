"""One-time import of past episodes from the Spotify for Creators feed.

For every old episode: download the audio unchanged, upload it to the Internet
Archive, save its artwork, and write episodes/*.yml with the ORIGINAL GUID so
podcast apps treat it as the same episode (no duplicates, stats kept).

Safe to re-run: episodes already imported are skipped, and files already on the
Internet Archive are not uploaded again.
"""
import html
import os
import re
import subprocess
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from datetime import timezone
from email.utils import parsedate_to_datetime

import requests

from common import EPISODES_DIR, ROOT, load_config, load_episodes, save_episode, short_hash, slugify

ITUNES = {"itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd"}
EXT = {"audio/x-m4a": "m4a", "audio/mp4": "m4a", "audio/mpeg": "mp3", "audio/mp3": "mp3"}
ART_DIR = ROOT / "site" / "episode-art"


def seconds(hms):
    parts = [float(p) for p in (hms or "0").split(":")]
    total = 0
    for p in parts:
        total = total * 60 + p
    return int(total)


def download(url, path):
    with requests.get(url, stream=True, timeout=120) as r:
        r.raise_for_status()
        with open(path, "wb") as f:
            for chunk in r.iter_content(1 << 20):
                f.write(chunk)
    return os.path.getsize(path)


def save_art(url, slug):
    ART_DIR.mkdir(parents=True, exist_ok=True)
    out = ART_DIR / f"{slug}.jpg"
    if out.exists():
        return out
    with tempfile.NamedTemporaryFile(suffix=".img") as tmp:
        download(url, tmp.name)
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", tmp.name,
                        "-vf", "scale=1400:1400:force_original_aspect_ratio=increase,crop=1400:1400",
                        "-q:v", "4", str(out)], check=True)
    return out


def upload(item, path, title, description, date, cfg):
    import internetarchive as ia

    name = os.path.basename(path)
    existing = {f["name"]: int(f.get("size", 0)) for f in ia.get_item(item).files}
    if existing.get(name) == os.path.getsize(path):
        print(f"    already on the Internet Archive")
        return
    show = cfg["show"]
    md = {
        "mediatype": "audio",
        "collection": cfg["hosts"]["archive"]["collection"],
        "title": f"{show['title']} — past episodes",
        "description": f"{show['description']} Episodes of the {show['title']} podcast by {show['author']}.",
        "creator": show["author"],
        "subject": ["Chassidus", "Torah", "Judaism", "podcast", cfg["show"]["title"]],
        "language": "eng",
    }
    for r in ia.upload(item, files={name: path}, metadata=md,
                       access_key=os.environ["IA_ACCESS_KEY"], secret_key=os.environ["IA_SECRET_KEY"],
                       retries=10, retries_sleep=30):
        r.raise_for_status()
    time.sleep(PAUSE_SECONDS)  # go slowly; the archive flags fast bulk uploads


PAUSE_SECONDS = 90


def main():
    cfg = load_config()
    xml = requests.get(cfg["legacy_feed_url"], timeout=120).content
    items = ET.fromstring(xml).find("channel").findall("item")
    have = {e["guid"] for e in load_episodes()}

    todo = [i for i in reversed(items) if i.findtext("guid") not in have]  # oldest first
    print(f"{len(items)} episodes in the old feed, {len(todo)} to import")

    for n, it in enumerate(todo, 1):
        guid = it.findtext("guid").strip()
        title = html.unescape(it.findtext("title").strip())
        enc = it.find("enclosure")
        pub = parsedate_to_datetime(it.findtext("pubDate")).astimezone(timezone.utc)
        date = pub.strftime("%Y-%m-%d")
        slug = f"{date}-{slugify(title)}"
        ext = EXT.get(enc.get("type"), "m4a")
        tag = short_hash(guid)
        fname = f"ffts-{slug}-{tag}.{ext}"
        item = cfg["hosts"]["archive"]["past_item"]
        desc = (it.findtext("description") or "").strip()
        print(f"[{n}/{len(todo)}] {date} {title}")

        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, fname)
            size = download(enc.get("url"), path)
            print(f"    downloaded {size/1e6:.1f} MB")
            plain = re.sub(r"<[^>]+>", " ", html.unescape(desc)).strip()
            upload(item, path, title, plain or title, date, cfg)

        ep = {
            "guid": guid,
            "title": title,
            "description": desc,
            "pub_date": pub.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "episode_type": it.findtext("itunes:episodeType", namespaces=ITUNES) or "full",
            "duration_seconds": seconds(it.findtext("itunes:duration", namespaces=ITUNES)),
            "audio": {"file": fname, "bytes": size, "type": enc.get("type"), "archive_item": item},
            "imported_from": {"feed": cfg["legacy_feed_url"], "link": it.findtext("link")},
        }
        img = it.find("itunes:image", ITUNES)
        if img is not None and img.get("href"):
            ep["image"] = f"episode-art/{save_art(img.get('href'), slug).name}"
        path = EPISODES_DIR / f"{slug}.yml"
        if path.exists():  # two old episodes with the same date and title
            path = EPISODES_DIR / f"{slug}-{tag}.yml"
        save_episode(ep, path)

    # Wait until every imported file is downloadable from the Internet Archive.
    pending = {e["audio"]["file"]: f"https://archive.org/download/{e['audio']['archive_item']}/{e['audio']['file']}"
               for e in load_episodes() if "imported_from" in e}
    for _ in range(60):
        pending = {k: u for k, u in pending.items()
                   if requests.head(u, allow_redirects=True, timeout=60).status_code != 200}
        if not pending:
            print("All imported audio is live on the Internet Archive")
            return
        print(f"Waiting for {len(pending)} files to become available…")
        time.sleep(60)
    sys.exit(f"Still not available: {sorted(pending)}")


if __name__ == "__main__":
    main()
