"""Episode artwork for a series: fixed show design + the series' own motif + "Part N".

Each series lives in site/series/<slug>/ with:
  series.yml   title_en, title_he, subtitle, (optional) accent color
  motif.svg    a symbolic illustration drawn for the series (viewBox 0 0 1600 1200)

Usage:
  make_art.py episode EPISODE.yml [...]   (re)draw artwork for episodes that belong to a series
  make_art.py series SLUG OUT.jpg [PART]  draw one image
"""
import html
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SERIES_DIR = ROOT / "site" / "series"
FONTS = ROOT / "fonts"
SIZE = 3000

TEMPLATE = """<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
     width="{S}" height="{S}" viewBox="0 0 {S} {S}">
  <defs>
    <style>
      @font-face {{ font-family: "Frank Ruhl Libre"; src: url("{fonts}/FrankRuhlLibre.ttf"); }}
      @font-face {{ font-family: "Assistant"; src: url("{fonts}/Assistant.ttf"); }}
    </style>
    <radialGradient id="bg" cx="50%" cy="38%" r="75%">
      <stop offset="0" stop-color="#1c3150"/>
      <stop offset="0.6" stop-color="#0e1a2e"/>
      <stop offset="1" stop-color="#070d18"/>
    </radialGradient>
    <radialGradient id="fade" cx="50%" cy="45%" r="55%">
      <stop offset="0.5" stop-color="#fff"/>
      <stop offset="1" stop-color="#000"/>
    </radialGradient>
    <mask id="motif-fade" maskUnits="userSpaceOnUse" x="600" y="430" width="1800" height="1350">
      <rect x="600" y="430" width="1800" height="1350" fill="url(#fade)"/>
    </mask>
    <linearGradient id="gold" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#f3d27a"/>
      <stop offset="1" stop-color="#c8962e"/>
    </linearGradient>
  </defs>
  <rect width="{S}" height="{S}" fill="url(#bg)"/>

  <!-- frame -->
  <rect x="90" y="90" width="2820" height="2820" fill="none" stroke="{accent}" stroke-opacity="0.75" stroke-width="6"/>
  <rect x="120" y="120" width="2760" height="2760" fill="none" stroke="{accent}" stroke-opacity="0.35" stroke-width="3"/>

  <text x="1500" y="330" text-anchor="middle" font-family="Assistant" font-weight="600"
        font-size="92" letter-spacing="28" fill="{accent}">FOOD FOR THE SOUL</text>

  <!-- series motif -->
  <g mask="url(#motif-fade)">
  <svg x="600" y="430" width="1800" height="1350" viewBox="0 0 1600 1200" preserveAspectRatio="xMidYMid meet">
{motif}
  </svg>
  </g>

  <text x="1500" y="2130" text-anchor="middle" font-family="Frank Ruhl Libre" font-weight="700"
        font-size="{he_size}" fill="url(#gold)" direction="rtl">{title_he}</text>
  <text x="1500" y="2370" text-anchor="middle" font-family="Frank Ruhl Libre" font-weight="500"
        font-size="{en_size}" fill="#f5ecd8">{title_en}</text>
  <text x="1500" y="2510" text-anchor="middle" font-family="Assistant" font-weight="400"
        font-size="84" letter-spacing="4" fill="#cdbf9f">{subtitle}</text>
{part}
</svg>
"""

PART = """  <rect x="1215" y="2620" width="570" height="150" rx="75" fill="{accent}"/>
  <text x="1500" y="2722" text-anchor="middle" font-family="Assistant" font-weight="700"
        font-size="90" letter-spacing="14" fill="#0e1a2e">PART {n}</text>"""


def motif_body(svg_text):
    """Inner content of the motif SVG (drop its outer <svg> wrapper and any scripts)."""
    svg_text = re.sub(r"<\?xml[^>]*>", "", svg_text)
    svg_text = re.sub(r"<script.*?</script>", "", svg_text, flags=re.S | re.I)
    m = re.search(r"<svg[^>]*>(.*)</svg>", svg_text, flags=re.S | re.I)
    return m.group(1) if m else svg_text


def fit(text, base, max_chars):
    return base if len(text) <= max_chars else int(base * max_chars / len(text))


def render(svg_path, png_path):
    if shutil.which("rsvg-convert"):
        subprocess.run(["rsvg-convert", "-w", str(SIZE), "-h", str(SIZE), "-o", png_path, svg_path], check=True)
        return
    chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"  # local preview on a Mac
    subprocess.run([chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    f"--window-size={SIZE},{SIZE}", "--force-device-scale-factor=1",
                    f"--screenshot={png_path}", f"file://{svg_path}"],
                   check=True, capture_output=True)


def render_series(slug, out, part=None):
    d = SERIES_DIR / slug
    meta = yaml.safe_load((d / "series.yml").read_text())
    try:
        _draw(d, meta, out, part, (d / "motif.svg").read_text())
    except subprocess.CalledProcessError:
        print(f"Motif for {slug} could not be drawn; using the default motif")
        _draw(d, meta, out, part, (SERIES_DIR / "_default" / "motif.svg").read_text())


def create_series(slug, title_en, title_he, subtitle, motif_svg=None):
    """Make site/series/<slug>/ for a new series (keeps an existing one untouched)."""
    d = SERIES_DIR / slug
    if (d / "series.yml").exists():
        return False
    d.mkdir(parents=True, exist_ok=True)
    (d / "series.yml").write_text(yaml.safe_dump(
        {"title_en": title_en, "title_he": title_he, "subtitle": subtitle, "accent": "#d9b45a"},
        allow_unicode=True, sort_keys=False))
    motif = motif_svg or (SERIES_DIR / "_default" / "motif.svg").read_text()
    (d / "motif.svg").write_text(motif)
    return True


def episode_art(ep_path):
    """Draw site/episode-art/<episode>.jpg for an episode with a series, and link it."""
    sys.path.insert(0, str(ROOT / "scripts"))
    from common import save_episode

    ep_path = Path(ep_path)
    ep = yaml.safe_load(ep_path.read_text())
    if not ep.get("series"):
        return
    out_rel = f"episode-art/{ep_path.stem}.jpg"
    (ROOT / "site" / "episode-art").mkdir(parents=True, exist_ok=True)
    render_series(ep["series"], ROOT / "site" / out_rel, ep.get("part"))
    if ep.get("image") != out_rel:
        ep["image"] = out_rel
        save_episode(ep, ep_path)


def _draw(d, meta, out, part, motif_text):
    accent = meta.get("accent", "#d9b45a")
    title_en = meta["title_en"]
    title_he = meta.get("title_he", "")
    svg = TEMPLATE.format(
        S=SIZE, fonts=FONTS.as_uri(), accent=accent,
        motif=motif_body(motif_text),
        title_he=html.escape(title_he), he_size=fit(title_he, 330, 9),
        title_en=html.escape(title_en), en_size=fit(title_en, 170, 20),
        subtitle=html.escape(meta.get("subtitle", "")),
        part=PART.format(accent=accent, n=part) if part else "",
    )
    with tempfile.TemporaryDirectory() as tmp:
        svg_path, png_path = os.path.join(tmp, "art.svg"), os.path.join(tmp, "art.png")
        Path(svg_path).write_text(svg)
        render(svg_path, png_path)
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", png_path,
                        "-q:v", "3", str(out)], check=True)
    print(f"Artwork → {out}")


if __name__ == "__main__":
    if sys.argv[1] == "episode":
        for p in sys.argv[2:]:
            episode_art(p)
    else:
        render_series(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else None)
