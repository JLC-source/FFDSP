"""Shared helpers: config, episode files, slugs, audio URLs."""
import hashlib
import re
import unicodedata
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
EPISODES_DIR = ROOT / "episodes"
TRANSCRIPTS_DIR = ROOT / "transcripts"


def load_config():
    return yaml.safe_load((ROOT / "config.yml").read_text())


def load_episodes():
    """All published episodes, oldest first."""
    eps = []
    for p in sorted(EPISODES_DIR.glob("*.yml")):
        ep = yaml.safe_load(p.read_text())
        ep["_path"] = p
        eps.append(ep)
    eps.sort(key=lambda e: str(e["pub_date"]))
    return eps


def _str_presenter(dumper, value):
    style = "|" if "\n" in value else None
    return dumper.represent_scalar("tag:yaml.org,2002:str", value, style=style)


yaml.SafeDumper.add_representer(str, _str_presenter)


def save_episode(ep, path):
    data = {k: v for k, v in ep.items() if not k.startswith("_")}
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=100))


def slugify(text, max_len=60):
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text[:max_len].rstrip("-") or "episode"


def short_hash(value, n=8):
    return hashlib.sha1(value.encode()).hexdigest()[:n]


def audio_url(ep, cfg):
    """Public URL of an episode's audio on the host selected in config.yml."""
    host = cfg["audio_host"]
    a = ep["audio"]
    if host == "archive":
        return f"https://archive.org/download/{a['archive_item']}/{a['file']}"
    if host == "r2":
        base = cfg["hosts"]["r2"]["public_base_url"].rstrip("/")
        if not base:
            raise SystemExit("audio_host is r2 but hosts.r2.public_base_url is empty")
        return f"{base}/{a['file']}"
    raise SystemExit(f"Unknown audio_host: {host}")


def drive_ids_done():
    """Drive file IDs that already became an episode (never process twice)."""
    return {e["source"]["drive_file_id"] for e in load_episodes() if e.get("source", {}).get("drive_file_id")}
