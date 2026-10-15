"""Turn a processed recording into an episode file + pull-request text.

  make_episode.py prepare WORKDIR   validate Claude's meta.json, choose names → plan.json
  make_episode.py finalize WORKDIR  write episodes/*.yml, transcripts, pr_body.md
"""
import json
import os
import shutil
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

from common import EPISODES_DIR, TRANSCRIPTS_DIR, load_config, save_episode, short_hash, slugify


def prepare(work):
    cfg = load_config()
    src = json.loads((work / "source.json").read_text())
    meta = json.loads((work / "meta.json").read_text(), strict=False)

    title = " ".join(str(meta.get("title", "")).split())
    desc = str(meta.get("description", "")).strip()
    if not 3 <= len(title) <= 120:
        raise SystemExit(f"Claude's title is missing or too long: {title!r}")
    if not 10 <= len(desc) <= 4000:
        raise SystemExit("Claude's description is missing or too long")

    now = datetime.now(timezone.utc)
    date = now.strftime("%Y-%m-%d")
    slug = slugify(title)
    tag = short_hash(src["id"])
    plan = {
        "title": title,
        "description": desc,
        "notes": str(meta.get("notes_for_rabbi", "")).strip(),
        "guid": str(uuid.uuid4()),
        "pub_date": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "slug": f"{date}-{slug}",
        "audio_file": f"ffts-{date}-{slug}-{tag}.mp3",
        # One archive item per year: creating many new items looks like spam to the archive.
        "archive_item": f"{cfg['hosts']['archive']['item_prefix']}-{now.year}",
    }
    (work / "plan.json").write_text(json.dumps(plan, indent=2))
    shutil.move(work / "episode.mp3", work / plan["audio_file"])
    print(json.dumps(plan, indent=2))


def finalize(work):
    cfg = load_config()
    src = json.loads((work / "source.json").read_text())
    plan = json.loads((work / "plan.json").read_text())
    stats = json.loads((work / "stats.json").read_text())
    audio_url = (work / "audio_url.txt").read_text().strip()
    mp3 = work / plan["audio_file"]

    TRANSCRIPTS_DIR.mkdir(exist_ok=True)
    for ext in ("txt", "srt"):
        shutil.copy(work / f"transcript.{ext}", TRANSCRIPTS_DIR / f"{plan['slug']}.{ext}")

    ep = {
        "guid": plan["guid"],
        "title": plan["title"],
        "description": plan["description"],
        "pub_date": plan["pub_date"],
        "episode_type": "full",
        "duration_seconds": stats["duration_seconds"],
        "audio": {
            "file": plan["audio_file"],
            "bytes": mp3.stat().st_size,
            "type": "audio/mpeg",
            "archive_item": plan["archive_item"],
        },
        "transcript": f"transcripts/{plan['slug']}.srt",
        "source": {
            "drive_file_id": src["id"],
            "drive_file_name": src["name"],
            "recorded": src["modtime"],
        },
        "processing": stats,
    }
    EPISODES_DIR.mkdir(exist_ok=True)
    save_episode(ep, EPISODES_DIR / f"{plan['slug']}.yml")

    mins = stats["duration_seconds"] // 60
    notes = f"\n> **Notes from Claude:** {plan['notes']}\n" if plan["notes"] else ""
    site = cfg["site_url"].rstrip("/")
    repo = f"https://github.com/{os.environ.get('GITHUB_REPOSITORY', 'JLC-source/FFDSP')}"
    body = f"""## 🎧 New episode ready for your approval

**{plan['title']}**

{plan['description']}
{notes}
| | |
|---|---|
| ▶️ **Listen** | [{plan['audio_file']}]({audio_url}) |
| Length | {mins} min |
| Loudness | {stats['loudness_lufs']} LUFS (target −16) |
| Original file | `{src['name']}` (moved to Drive “Done”) |
| Transcript | [`transcripts/{plan['slug']}.txt`]({repo}/blob/episode/{src['id']}/transcripts/{plan['slug']}.txt) |

### What to do
- ✅ **Approve:** tap **Merge pull request** → **Confirm merge**. It goes live at {site}/feed.xml within a few minutes.
- ✏️ **Change something:** write a comment that starts with `@claude`, for example
  `@claude make the title "Mayim Rabim: Love That Water Can't Extinguish"` or
  `@claude shorten the description and mention it is from the 5738 maamar`.
- ❌ **Reject:** tap **Close pull request**. Nothing is published. To redo it later,
  move the original recording from Drive “Done” back to “Inbox”.
"""
    (work / "pr_body.md").write_text(body)
    print(body)


if __name__ == "__main__":
    {"prepare": prepare, "finalize": finalize}[sys.argv[1]](Path(sys.argv[2]))
