"""Build the public website + podcast RSS feed from episodes/*.yml.

Usage: build_feed.py OUT_DIR [--check-urls]
"""
import html
import shutil
import struct
import sys
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path
from xml.sax.saxutils import escape

import requests

from common import ROOT, audio_url, load_config, load_episodes

NS = ('xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd" '
      'xmlns:atom="http://www.w3.org/2005/Atom" '
      'xmlns:content="http://purl.org/rss/1.0/modules/content/" '
      'xmlns:podcast="https://podcastindex.org/namespace/1.0"')


def rfc2822(iso):
    dt = datetime.fromisoformat(str(iso).replace("Z", "+00:00"))
    return format_datetime(dt.astimezone(timezone.utc), usegmt=True)


def cdata(text):
    return "<![CDATA[" + str(text).replace("]]>", "]]]]><![CDATA[>") + "]]>"


def desc_html(text):
    if "<p>" in text:  # imported episodes already carry HTML
        return text
    paras = [p.strip() for p in str(text).split("\n\n") if p.strip()]
    return "".join("<p>" + "<br>".join(html.escape(l.strip()) for l in p.split("\n")) + "</p>" for p in paras)


def jpeg_size(path):
    data = path.read_bytes()
    i = 2
    while i < len(data):
        marker, length = data[i + 1], struct.unpack(">H", data[i + 2:i + 4])[0]
        if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):
            h, w = struct.unpack(">HH", data[i + 5:i + 9])
            return w, h
        i += 2 + length
    raise ValueError("not a JPEG")


def main(out, check_urls=False):
    cfg, show = load_config(), load_config()["show"]
    site = cfg["site_url"].rstrip("/")
    out = Path(out)
    shutil.rmtree(out, ignore_errors=True)
    (out / "transcripts").mkdir(parents=True)

    cover = ROOT / "site" / show["cover"]
    w, h = jpeg_size(cover)
    assert w == h and 1400 <= w <= 3000, f"Cover art must be square 1400–3000 px, got {w}x{h}"
    shutil.copy(cover, out / show["cover"])

    eps = load_episodes()
    seen = set()
    number = 0
    items = []
    for ep in eps:
        assert ep["guid"] not in seen, f"Duplicate GUID {ep['guid']}"
        seen.add(ep["guid"])
        if ep.get("episode_type", "full") == "full":
            number += 1
        url = audio_url(ep, cfg)
        if check_urls:
            r = requests.head(url, allow_redirects=True, timeout=60)
            assert r.status_code == 200, f"Audio not reachable ({r.status_code}): {url}"
        extra = ""
        if show.get("number_episodes") and ep.get("episode_type", "full") == "full":
            extra += f"\n      <itunes:episode>{ep.get('number', number)}</itunes:episode>"
        if ep.get("image"):
            extra += f'\n      <itunes:image href="{escape(ep["image"])}"/>'
        if ep.get("transcript"):
            t = Path(ep["transcript"])
            shutil.copy(ROOT / t, out / "transcripts" / t.name)
            extra += (f'\n      <podcast:transcript url="{site}/transcripts/{escape(t.name)}" '
                      f'type="application/srt" language="en"/>')
        d = desc_html(ep.get("description", ""))
        items.append(f"""    <item>
      <title>{escape(ep['title'])}</title>
      <description>{cdata(d)}</description>
      <content:encoded>{cdata(d)}</content:encoded>
      <guid isPermaLink="false">{escape(ep['guid'])}</guid>
      <pubDate>{rfc2822(ep['pub_date'])}</pubDate>
      <enclosure url="{escape(url)}" length="{int(ep['audio']['bytes'])}" type="{escape(ep['audio']['type'])}"/>
      <itunes:duration>{int(ep['duration_seconds'])}</itunes:duration>
      <itunes:episodeType>{ep.get('episode_type', 'full')}</itunes:episodeType>
      <itunes:explicit>false</itunes:explicit>{extra}
    </item>""")
    items.reverse()  # newest first

    now = format_datetime(datetime.now(timezone.utc), usegmt=True)
    feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" {NS}>
  <channel>
    <title>{escape(show['title'])}</title>
    <link>{site}/</link>
    <atom:link href="{site}/feed.xml" rel="self" type="application/rss+xml"/>
    <description>{cdata(show['description'])}</description>
    <language>{show['language']}</language>
    <copyright>{escape(show['copyright'])}</copyright>
    <lastBuildDate>{now}</lastBuildDate>
    <itunes:author>{escape(show['author'])}</itunes:author>
    <itunes:summary>{escape(show['description'])}</itunes:summary>
    <itunes:type>{show['type']}</itunes:type>
    <itunes:owner>
      <itunes:name>{escape(show['owner_name'])}</itunes:name>
      <itunes:email>{escape(show['owner_email'])}</itunes:email>
    </itunes:owner>
    <itunes:explicit>{'true' if show['explicit'] else 'false'}</itunes:explicit>
    <itunes:category text="{escape(show['category'])}">
      <itunes:category text="{escape(show['subcategory'])}"/>
    </itunes:category>
    <itunes:image href="{site}/{show['cover']}"/>
    <image>
      <url>{site}/{show['cover']}</url>
      <title>{escape(show['title'])}</title>
      <link>{site}/</link>
    </image>
{chr(10).join(items)}
  </channel>
</rss>
"""
    (out / "feed.xml").write_text(feed)

    rows = "\n".join(
        f"<li><h2>{html.escape(e['title'])}</h2><p class=d>{rfc2822(e['pub_date'])[:16]}</p>"
        f"<audio controls preload=none src=\"{html.escape(audio_url(e, cfg))}\"></audio></li>"
        for e in reversed(eps))
    (out / "index.html").write_text(f"""<!doctype html><html lang=en><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>{html.escape(show['title'])}</title>
<link rel=alternate type="application/rss+xml" href="feed.xml">
<style>body{{font:17px/1.5 Georgia,serif;max-width:680px;margin:0 auto;padding:24px 16px;color:#1b2333;background:#f6f7f9}}
img{{width:160px;border-radius:8px}}h1{{margin:.3em 0 0}}ul{{list-style:none;padding:0}}li{{border-top:1px solid #d8dee8;padding:12px 0}}
h2{{font-size:1.1em;margin:0}}.d{{color:#5a6578;margin:2px 0 6px;font-size:.9em}}audio{{width:100%}}</style>
<img src="{show['cover']}" alt="{html.escape(show['title'])} cover">
<h1>{html.escape(show['title'])}</h1><p>{html.escape(show['description'])}<br>{html.escape(show['author'])}</p>
<p><a href="feed.xml">Podcast RSS feed</a></p>
<ul>{rows}</ul></html>
""")
    (out / ".nojekyll").write_text("")
    print(f"Built feed with {len(eps)} episodes → {out / 'feed.xml'}")


if __name__ == "__main__":
    main(sys.argv[1], "--check-urls" in sys.argv)
