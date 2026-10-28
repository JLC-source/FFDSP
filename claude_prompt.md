<!-- Instructions Claude follows to write each new episode's title, description and series. -->
You are helping Rabbi Hilel Raskin publish an episode of his podcast "Food for the Soul" —
Chassidus explained in a simple and clear fashion. Classes are in English with many
Hebrew and Yiddish terms.

Read these files:
- work/filename.txt — the original recording's file name (often names the topic or source, e.g. a maamar and year)
- work/transcript.txt — automatic transcript (may misspell Hebrew terms; correct them in your writing)
- work/style.md — recent episode titles and descriptions, newest first; match this style closely.
  If this class continues a series listed there (same topic), title it as the next part.

- work/series.md — the class series that already exist, with the last part number of each

Then write work/meta.json containing exactly this JSON object:
{
  "title": "...",
  "description": "...",
  "notes_for_rabbi": "...",
  "series": {"slug": "...", "title_en": "...", "title_he": "...", "subtitle": "...",
             "palette": {"bg_light": "#...", "bg": "#...", "bg_dark": "#...", "accent": "#...",
                         "title_light": "#...", "title_dark": "#...", "text": "#...", "subtext": "#..."}},
  "part": 1
}

Rules:
- title: short, like the existing titles (usually 3–9 words). Use common English
  transliterations (Chassidus, Hashem, Tanya, Shir HaShirim, Rosh Hashana). If the
  recording is clearly one part of a multi-part class, end with "part N" like the existing titles.
- description: 2–3 plain sentences saying what the class teaches, warm and simple,
  followed by a final line naming the source when you can tell it (for example
  "Maamar Mayim Rabim 5738" or "Likutei Sichot"), in the same terse way the
  existing descriptions do. No hashtags, no emojis, no markdown.
- notes_for_rabbi: one short sentence about anything you were unsure of (a name, a
  source, a term), or "" if nothing.
- series: the course/series this class belongs to (usually the maamar or sicha being
  learned). If it continues a series in work/series.md, copy that series' slug and names
  exactly and set "part" to the next number. Otherwise start a new series: slug is short
  lowercase-with-dashes (e.g. "vayeitzei-5745"), title_en is the transliterated name
  (e.g. "Mayim Rabim"), title_he is the name in Hebrew letters (e.g. "מים רבים"),
  subtitle is like "Maamar 5738 · Rabbi Hilel Raskin". part is a number, or null for a
  one-off class.
- palette (only needed for a NEW series): colors that suit the topic and differ from the
  existing series, e.g. deep burgundy with rose gold for teshuva, forest green with warm
  gold for Sukkot, royal blue with silver for Chanukah, deep purple with gold for
  Moshiach. bg_light/bg/bg_dark are a DARK background (center to edge); accent,
  title_light/title_dark (the Hebrew title gradient), text and subtext are LIGHT colors
  that read clearly on it. Use 6-digit hex colors. Draw the motif in the same palette.
- Only when you START A NEW SERIES, also write work/motif.svg: a symbolic illustration of
  the series' central idea in a warm, dignified Chassidic style (examples: a flame, a
  sukkah, a shofar, a menorah, a Torah scroll, light rays, a ladder, a seed). Look at
  site/series/mayim-rabim-5738/motif.svg for the style and quality. Rules: one <svg>
  with viewBox="0 0 1600 1200", transparent background (it sits on deep navy), gold
  and warm tones with blues as accents, smooth gradients, no text or letters, no
  people's faces, no images or external links, prefix every id with the series slug.
Write only these files. Do not modify anything else.
