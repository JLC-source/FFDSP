"""List new recordings in Drive Inbox that have not been processed yet.

Skips a file if it is already a published episode, or if a pull request for it
is open (waiting for approval). Writes a GitHub Actions matrix to $GITHUB_OUTPUT.
"""
import json
import os
import subprocess

from common import drive_ids_done, load_config


def open_pr_ids():
    out = subprocess.run(
        ["gh", "pr", "list", "--state", "open", "--limit", "200", "--json", "headRefName"],
        check=True, capture_output=True, text=True,
    ).stdout
    return {pr["headRefName"].removeprefix("episode/") for pr in json.loads(out)
            if pr["headRefName"].startswith("episode/")}


def main():
    cfg = load_config()
    d = cfg["drive"]
    listing = subprocess.run(
        ["rclone", "lsjson", "--files-only", "--no-mimetype", f"{d['remote']}{d['inbox']}"],
        check=True, capture_output=True, text=True,
    ).stdout
    exts = {e.lower() for e in d["audio_extensions"]}
    skip = drive_ids_done() | open_pr_ids()

    new = []
    for f in sorted(json.loads(listing), key=lambda f: f["ModTime"]):
        ext = f["Name"].rsplit(".", 1)[-1].lower() if "." in f["Name"] else ""
        if ext not in exts:
            print(f"Ignoring non-audio file: {f['Name']}")
            continue
        if f["ID"] in skip:
            print(f"Already handled: {f['Name']}")
            continue
        new.append({"id": f["ID"], "name": f["Name"], "modtime": f["ModTime"]})

    new = new[: d["max_per_run"]]
    print(f"New recordings to process: {len(new)}")
    for f in new:
        print(f"  - {f['name']}")
    with open(os.environ.get("GITHUB_OUTPUT", "/dev/stdout"), "a") as out:
        out.write(f"count={len(new)}\n")
        out.write(f"matrix={json.dumps({'include': new})}\n")


if __name__ == "__main__":
    main()
