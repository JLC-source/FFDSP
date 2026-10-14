"""Upload an episode MP3 to the audio host selected in config.yml.

Usage: upload_audio.py FILE.mp3 ITEM_ID "Title" "Description"
Prints the public URL. Re-running with the same ITEM_ID overwrites (safe to retry).
"""
import os
import sys
import time

import requests

from common import load_config


def upload_archive(path, item, title, description, cfg):
    import internetarchive as ia

    h = cfg["hosts"]["archive"]
    md = {
        "mediatype": "audio",
        "collection": h["collection"],
        "title": title,
        "description": description,
        "creator": cfg["show"]["author"],
        "subject": ["Chassidus", "Torah", "Judaism", "podcast", cfg["show"]["title"]],
        "language": "eng",
    }
    responses = ia.upload(
        item, files={os.path.basename(path): path}, metadata=md,
        access_key=os.environ["IA_ACCESS_KEY"], secret_key=os.environ["IA_SECRET_KEY"],
        retries=10, retries_sleep=30, verbose=True,
    )
    for r in responses:
        r.raise_for_status()
    url = f"https://archive.org/download/{item}/{os.path.basename(path)}"
    # New items can take a few minutes before the file is downloadable.
    for _ in range(40):
        if requests.head(url, allow_redirects=True, timeout=60).status_code == 200:
            return url
        time.sleep(30)
    raise SystemExit(f"Uploaded, but {url} is not reachable yet")


def main(path, item, title, description):
    cfg = load_config()
    host = cfg["audio_host"]
    if host == "archive":
        print(upload_archive(path, item, title, description, cfg))
    else:
        raise SystemExit(f"Upload to '{host}' is not set up yet")


if __name__ == "__main__":
    main(*sys.argv[1:5])
