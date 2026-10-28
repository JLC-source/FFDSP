# Food for the Soul — podcast pipeline

Free, automatic publishing for **Food for the Soul** (Rabbi Hilel Raskin).
Feed: <https://jlc-source.github.io/FFDSP/feed.xml>

## How to publish an episode

1. Drop the class recording into Google Drive → **Torah Classes / Inbox**.
2. Every morning (~6:15am New York) the pipeline picks it up: cleans the audio, transcribes it,
   has Claude write a title and description, and uploads the audio to the Internet Archive.
3. You get a GitHub notification for a new **pull request** with the title, description and a
   link to listen.
   - **Approve:** Merge pull request → Confirm. Live in a few minutes.
   - **Change:** comment `@claude …` with what to change.
   - **Reject:** Close pull request.
4. The original recording and the edited MP3 end up in **Torah Classes / Done**.

Want it sooner than tomorrow morning? Actions tab → **Process new recordings** → **Run workflow**.
If anything fails, GitHub emails you.

## Where things live

| What | Where |
|---|---|
| Settings (show info, audio host) | `config.yml` |
| One file per episode | `episodes/` |
| Transcripts | `transcripts/` |
| Cover art | `site/cover.jpg` |
| Hebrew/Yiddish words for the transcriber | `glossary.txt` |
| Automation | `.github/workflows/` and `scripts/` |

## Spanish show: Alimento para la Neshamá

The same pipeline also runs a Spanish sister podcast. Drop Spanish recordings in
Drive **Torah Classes / Clases en Español / Inbox**; they come back as pull requests
like the English ones, with Spanish titles and descriptions and the teal-and-copper artwork.

- Feed: https://jlc-source.github.io/FFDSP/es/feed.xml
- Everything for it lives in `shows/es/`: `config.yml`, `claude_prompt.md` (how Claude writes),
  `glossary.txt` (terms for the transcriber), `episodes/`, `transcripts/`, `site/` (cover and series art).
- Another show can be added the same way: a new `shows/<code>/` folder with its own `config.yml`
  (add a build line for it in `.github/workflows/publish.yml`).

## Secrets (Settings → Secrets and variables → Actions)

| Name | What |
|---|---|
| `RCLONE_CONF` | Google Drive connection (rclone, own Google OAuth client in project `ffts-podcast`) |
| `IA_ACCESS_KEY`, `IA_SECRET_KEY` | Internet Archive upload keys (archive.org/account/s3.php) |
| `CLAUDE_CODE_OAUTH_TOKEN` | Claude subscription token from `claude setup-token`. **Expires October 2027** — make a new one and replace it. |

## Changing the audio host

`audio_host` in `config.yml` decides which host every episode's link points to. Episode GUIDs
never change, so switching hosts (e.g. to Cloudflare R2) never creates duplicates in podcast apps.
