"""Upload an episode MP3 to the audio host selected in config.yml.

Usage: upload_audio.py FILE.mp3 ITEM_ID "Title" "Description" URL_OUT.txt
Writes the public URL to URL_OUT.txt. Re-running with the same ITEM_ID overwrites (safe to retry).
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
        "title": f"{cfg['show']['title']} — {item.rsplit('-', 1)[-1]} episodes",
        "description": f"{cfg['show']['description']} Episodes of the {cfg['show']['title']} podcast by {cfg['show']['author']}.",
        "creator": cfg["show"]["author"],
        "subject": ["Chassidus", "Torah", "Judaism", "podcast", cfg["show"]["title"]],
        "language": "eng",
    }
    # The archive is sometimes slow or briefly down; keep trying for about 40 minutes.
    for attempt in range(1, 9):
        try:
            responses = ia.upload(
                item, files={os.path.basename(path): path}, metadata=md,
                access_key=os.environ["IA_ACCESS_KEY"], secret_key=os.environ["IA_SECRET_KEY"],
                retries=10, retries_sleep=30, verbose=True,
            )
            for r in responses:
                r.raise_for_status()
            break
        except (requests.ConnectionError, requests.Timeout) as e:
            if attempt == 8:
                raise
            print(f"Internet Archive not responding (attempt {attempt}): {e.__class__.__name__}; retrying in 5 min")
            time.sleep(300)
    url = f"https://archive.org/download/{item}/{os.path.basename(path)}"
    # The archive processes uploads in a queue; a file can take a while to become
    # downloadable. Wait up to an hour, then carry on: the feed is only published
    # after approval, and publishing checks every link first.
    for _ in range(60):
        if requests.head(url, allow_redirects=True, timeout=60).status_code == 200:
            return url
        time.sleep(60)
    print(f"Note: {url} is uploaded but still processing at the Internet Archive")
    return url


def main(path, item, title, description, url_out):
    cfg = load_config()
    host = cfg["audio_host"]
    if host != "archive":
        raise SystemExit(f"Upload to '{host}' is not set up yet")
    url = upload_archive(path, item, title, description, cfg)
    with open(url_out, "w") as f:
        f.write(url + "\n")
    print(f"Audio is live at {url}")


if __name__ == "__main__":
    main(*sys.argv[1:6])
