#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6,<7"]
# ///
import argparse
import json
import re
import subprocess
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlparse

import yaml


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, check=False)


def sanitize_name(value: str, fallback: str = "Untitled") -> str:
    value = (value or "").strip()
    if not value:
        return fallback
    value = value.replace("/", "-")
    value = re.sub(r'[\\:*?"<>|]+', "", value)
    value = re.sub(r"\s+", " ", value).strip()
    value = value.rstrip(".")
    return value or fallback


def iso_date_from_upload(upload_date: str | None) -> str | None:
    if not upload_date:
        return None
    if re.fullmatch(r"\d{8}", upload_date):
        return f"{upload_date[0:4]}-{upload_date[4:6]}-{upload_date[6:8]}"
    return None


def format_duration(seconds):
    if seconds in (None, ""):
        return None
    try:
        seconds = int(seconds)
    except (TypeError, ValueError):
        return None
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def metadata_summary_lines(title: str, description: str | None) -> list[str]:
    if not description:
        return []
    lines = []
    for raw in description.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line == title.strip():
            continue
        if line.lower().startswith(("save this", "follow for", "subscribe")):
            continue
        if line.startswith(("-", "•", "*")):
            item = line.lstrip("-•* ").strip()
            if item:
                lines.append(item)
    if lines:
        return lines[:8]

    compact = []
    for raw in description.splitlines():
        line = raw.strip()
        if not line or line == title.strip():
            continue
        compact.append(line)
        if len(compact) == 3:
            break
    return compact


def quote_block(text: str) -> str:
    return "\n".join(f"> {line}" if line else ">" for line in text.splitlines())


def infer_platform(webpage_url: str | None, extractor_key: str | None) -> str:
    if extractor_key:
        if extractor_key.lower() == "youtube":
            return "YouTube"
        return extractor_key
    if webpage_url:
        host = urlparse(webpage_url).netloc or urlparse(webpage_url).path
        return host or "online video source"
    return "online video source"


def unique_note_path(directory: Path, stem: str, source_id: str | None) -> Path:
    first = directory / f"{stem}.md"
    if not first.exists():
        return first
    if source_id:
        second = directory / f"{stem} - {source_id}.md"
        if not second.exists():
            return second
    counter = 2
    while True:
        candidate = directory / f"{stem} ({counter}).md"
        if not candidate.exists():
            return candidate
        counter += 1


def fetch_metadata(url: str) -> dict:
    cmd = ["yt-dlp", "--dump-single-json", url]
    result = run(cmd)
    if result.returncode != 0:
        raise RuntimeError(
            result.stderr.strip() or result.stdout.strip() or "yt-dlp metadata extraction failed"
        )
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Failed to parse yt-dlp metadata JSON: {exc}") from exc


def download_media(
    url: str, output_dir: Path, title: str, creator: str, source_id: str | None
) -> tuple[Path | None, str | None]:
    safe_title = sanitize_name(title)
    safe_creator = sanitize_name(creator or "Unknown Creator")
    safe_id = sanitize_name(source_id or "video")
    template = output_dir / f"{safe_title} - {safe_creator} - {safe_id}.%(ext)s"
    cmd = [
        "yt-dlp",
        "-f",
        "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/b",
        "--merge-output-format",
        "mp4",
        "-o",
        str(template),
        url,
    ]
    result = run(cmd)
    media_path = output_dir / f"{safe_title} - {safe_creator} - {safe_id}.mp4"
    if media_path.exists():
        return media_path, None

    matches = sorted(output_dir.glob(f"{safe_title} - {safe_creator} - {safe_id}.*"))
    for candidate in matches:
        if candidate.suffix.lower() != ".part":
            return candidate, None

    warning = result.stderr.strip() or result.stdout.strip() or "Download failed"
    return None, warning


def build_note(metadata: dict, created_date: str, media_rel: str | None) -> str:
    date.fromisoformat(created_date)
    title = sanitize_name(
        metadata.get("title") or metadata.get("fulltitle") or metadata.get("id") or "Untitled Video"
    )
    creator = (
        metadata.get("channel")
        or metadata.get("uploader")
        or metadata.get("creator")
        or "Unknown Creator"
    )
    source_date = iso_date_from_upload(metadata.get("upload_date"))
    source_url = metadata.get("webpage_url") or metadata.get("original_url") or metadata.get("url")
    duration = format_duration(metadata.get("duration"))
    description = (metadata.get("description") or "").strip()
    summary_lines = metadata_summary_lines(title, description)
    platform = infer_platform(metadata.get("webpage_url"), metadata.get("extractor_key"))

    frontmatter = [
        "---",
        f"created: {created_date}",
        f"source_url: {json.dumps(source_url)}",
        f"source_title: {json.dumps(metadata.get('title') or title)}",
        f"source_creator: {json.dumps(creator)}",
    ]
    for key, value in (
        ("source_original_url", metadata.get("original_url")),
        ("source_id", metadata.get("id")),
        ("source_provider", metadata.get("extractor_key")),
        ("metadata_status", metadata.get("metadata_status", "available")),
    ):
        if value is not None:
            frontmatter.append(f"{key}: {json.dumps(str(value))}")
    if source_date:
        frontmatter.append(f"source_date: {source_date}")
    frontmatter.append("---")

    body = [f"# {title}", ""]
    if media_rel:
        body.extend([f"![[{media_rel}]]", ""])

    body.extend(
        [
            "## Context",
            f"- Saved from {platform} by {creator} on [[{created_date}]] at user request.",
        ]
    )
    if duration:
        body.append(f"- Duration: {duration}.")
    body.append(
        "- Provenance: summary below is derived from source metadata/description unless manually revised later."
    )
    body.append("")

    if summary_lines:
        body.append("## Summary")
        body.append("- Best-effort summary from source metadata/description:")
        for line in summary_lines:
            body.append(f"  - {line}")
        body.append("")

    if description:
        body.extend(
            [
                "## Source Description",
                quote_block(description),
                "",
            ]
        )

    body.extend(
        [
            "## Notes",
            "- Add manual notes/reactions here if you later watch or review the video directly.",
        ]
    )

    return "\n".join(frontmatter + [""] + body).rstrip() + "\n"


def find_saved_note(vault_root: Path, metadata: dict) -> Path | None:
    """Resolve an existing capture by canonical URL or provider-qualified source ID."""
    urls = {metadata.get("webpage_url"), metadata.get("original_url")} - {None, ""}
    source_id, provider = metadata.get("id"), metadata.get("extractor_key")
    for path in sorted((vault_root / "Assets" / "Videos").rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        match = re.match(r"\A---\r?\n(.*?)^---\s*$", text, re.MULTILINE | re.DOTALL)
        if not match:
            raise ValueError(f"Cannot check duplicate identity: missing frontmatter in {path}")
        fields = yaml.safe_load(match.group(1))
        if not isinstance(fields, dict):
            raise TypeError(f"Cannot check duplicate identity: invalid metadata in {path}")
        saved_urls = {fields.get("source_url"), fields.get("source_original_url")} - {None, ""}
        if urls.intersection(saved_urls) or (
            source_id
            and provider
            and fields.get("source_id") == str(source_id)
            and fields.get("source_provider") == provider
        ):
            return path
    return None


def save_note(vault_root: Path, metadata: dict, created_date: str, media_rel: str | None) -> Path:
    """Save valid metadata once; preserve an existing capture and its user annotations.

    Sequential retry guarantee. Concurrent writers must be serialized by the caller.
    """
    date.fromisoformat(created_date)
    existing = find_saved_note(vault_root, metadata)
    if existing:
        return existing
    directory = vault_root / "Assets" / "Videos" / created_date
    directory.mkdir(parents=True, exist_ok=True)
    path = unique_note_path(
        directory,
        sanitize_name(metadata.get("title") or "Video bookmark"),
        sanitize_name(str(metadata.get("id") or "")),
    )
    text = build_note(metadata, created_date, media_rel)
    fields = yaml.safe_load(re.match(r"\A---\n(.*?)^---$", text, re.MULTILINE | re.DOTALL).group(1))
    if not isinstance(fields, dict) or not fields.get("source_url"):
        raise ValueError("Video note needs valid metadata and a source URL")
    with path.open("x", encoding="utf-8") as stream:
        stream.write(text)
    if path.read_text(encoding="utf-8") != text:
        raise OSError("Saved video note failed readback")
    return path


def main():
    parser = argparse.ArgumentParser(
        description="Save video content and a companion Markdown note into the vault."
    )
    parser.add_argument("url")
    parser.add_argument(
        "--vault-root", default=".", help="Vault root / output root. Default: current directory"
    )
    parser.add_argument("--date", help="Override created date (YYYY-MM-DD). Default: today")
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Create the Markdown note without downloading media",
    )
    args = parser.parse_args()

    created_date = args.date or datetime.now().astimezone().strftime("%Y-%m-%d")
    vault_root = Path(args.vault_root).expanduser().resolve()
    output_dir = vault_root / "Assets" / "Videos" / created_date
    date.fromisoformat(created_date)

    metadata_warning = None
    try:
        metadata = fetch_metadata(args.url)
    except (OSError, RuntimeError, ValueError):
        metadata_warning = "Source metadata unavailable; saved the supplied URL only."
        metadata = {
            "title": "Video bookmark",
            "original_url": args.url,
            "metadata_status": "unavailable",
        }
    metadata["original_url"] = args.url
    existing = find_saved_note(vault_root, metadata)
    if existing:
        print(
            json.dumps(
                {"note_path": str(existing), "reused": True, "metadata_warning": metadata_warning}
            )
        )
        return
    output_dir.mkdir(parents=True, exist_ok=True)

    title = sanitize_name(
        metadata.get("title") or metadata.get("fulltitle") or metadata.get("id") or "Untitled Video"
    )
    creator = (
        metadata.get("channel")
        or metadata.get("uploader")
        or metadata.get("creator")
        or "Unknown Creator"
    )
    source_id = metadata.get("id")

    media_path = None
    download_warning = None
    if not args.skip_download and metadata_warning is None:
        media_path, download_warning = download_media(
            args.url, output_dir, title, creator, source_id
        )

    media_rel = None
    if media_path:
        try:
            media_rel = str(media_path.relative_to(vault_root))
        except ValueError:
            media_rel = str(media_path)

    note_path = save_note(vault_root, metadata, created_date, media_rel)

    result = {
        "note_path": str(note_path),
        "media_path": str(media_path) if media_path else None,
        "download_warning": download_warning,
        "metadata_warning": metadata_warning,
        "reused": False,
        "title": title,
        "creator": creator,
        "source_url": metadata.get("webpage_url") or args.url,
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
