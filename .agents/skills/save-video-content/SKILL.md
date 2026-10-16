---
name: save-video-content
description: >-
  Saves online video content into the Obsidian vault with a companion Markdown
  note, source metadata, optional downloaded media file, and provenance-aware
  summary. Use when the user asks to save, archive, bookmark, or capture a
  video, short, reel, clip, or supported media URL for later reference,
  especially for YouTube/YouTube Shorts and other `yt-dlp`-supported sources.
metadata:
  exo.category: general
---
# Save Video Content

Use this skill to save video URLs into the vault in a reusable form: media file + companion Markdown note.

## Quick workflow

1. Verify live date/time with `date` and the active daily note with `obsidian daily:path`.
2. Run duplicate discovery before saving:
   - Search for the exact URL
   - Search for the source ID / slug when obvious
   - Search for a likely title fragment if needed
3. Run the helper script:
   - `uv run .agents/skills/save-video-content/scripts/save_video.py "<url>"`
4. The helper checks canonical source URL/provider-qualified ID across existing video notes before downloading. Sequential retries return the existing note without rewriting annotations; serialize concurrent saves. Read the generated/reused note and confirm:
   - source URL
   - creator/title metadata
   - embed path
   - provenance note about where the summary came from
5. Append a concise log line to the daily note.

## Default output shape

The script writes to:

- `Assets/Videos/YYYY-MM-DD/<Title>.md`
- `Assets/Videos/YYYY-MM-DD/<Title> - <Creator> - <SourceId>.<ext>` when download succeeds

The Markdown note should include:

- frontmatter with `created`, `source_url`, `source_title`, `source_creator`, and `source_date` when available
- an embed/reference to the saved media file when present
- context bullets
- a summary section clearly labeled as metadata-derived unless manually reviewed
- the source description text when available

## Provenance rules

- Do not imply that a summary came from manual watching/transcription unless you actually reviewed the content that way.
- By default, treat `yt-dlp` metadata/description as the source of the summary.
- Metadata extraction failure saves only the supplied URL with `metadata_status: unavailable`, no generated summary, and a visible warning. Download failure preserves available source metadata. Never treat either as a completed media archive. The helper serializes string properties, parses the result before writing, and reads the saved note back.

## Commands

Basic save:

```bash
uv run .agents/skills/save-video-content/scripts/save_video.py "https://youtube.com/shorts/..."
```

Metadata-only save (no media download):

```bash
uv run .agents/skills/save-video-content/scripts/save_video.py "<url>" --skip-download
```

Test outside the vault:

```bash
uv run .agents/skills/save-video-content/scripts/save_video.py "<url>" --vault-root /tmp/video-save-test
```

## Notes

- Prefer this skill for `yt-dlp`-supported URLs. Do not promise support for DRM-protected/private content you cannot access.
- If the user also expresses intent around the saved media (for example, wanting to watch it with someone later), capture that intent in the daily note and/or the most relevant person/task note.
- If the exact checkout/review/watch date matters later, ask for it and store it in the right task/note rather than leaving it only in chat.

Retry identity checks compare both the supplied URL and canonical provider URL, plus provider-qualified source IDs. Metadata recovery reuses a previously saved URL-only bookmark and preserves its annotations.
