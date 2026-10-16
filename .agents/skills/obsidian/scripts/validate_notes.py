# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6,<7"]
# ///
"""Validate metadata/status; optionally repair safe status forms with backups."""

import argparse
import json
import hashlib
import os
import tempfile
from pathlib import Path

from note_metadata import MetadataError, parse_frontmatter, validate_attention_dates
from status_policy import repair_status, validate_status


def save_repair(path: Path, original: bytes, candidate: bytes, backup: Path) -> None:
    if path.is_symlink():
        raise MetadataError('refusing to replace a symlink')
    backup.mkdir(parents=True, exist_ok=True, mode=0o700)
    name = hashlib.sha256(str(path.resolve()).encode() + original).hexdigest() + '.md'
    target = backup / name
    if target.exists():
        if target.read_bytes() != original:
            raise MetadataError('backup collision')
    else:
        with target.open('xb') as handle:
            handle.write(original)
        target.chmod(0o600)
    fd, temporary = tempfile.mkstemp(prefix='.status-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as handle:
            handle.write(candidate)
        os.chmod(temporary, path.stat().st_mode & 0o777)
        if path.read_bytes() != original:
            raise MetadataError('note changed during repair; retry after rereading')
        os.replace(temporary, path)
        if path.read_bytes() != candidate:
            raise MetadataError('saved note changed before readback; inspect before retrying')
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument('--fix-status', action='store_true', help='repair unambiguous status forms only')
    parser.add_argument('--attention-dates-only', action='store_true', help='read-only scan preflight: check YAML and attention/period dates without rejecting status debt')
    parser.add_argument('--backup-dir', type=Path, help='required with --fix-status; outside scanned paths')
    args = parser.parse_args()
    if args.attention_dates_only and args.fix_status:
        parser.error('--attention-dates-only is read-only and cannot be combined with --fix-status')
    if args.fix_status and not args.backup_dir:
        parser.error('--fix-status requires --backup-dir')
    if args.fix_status and any(args.backup_dir.resolve().is_relative_to(p.resolve()) for p in args.paths):
        parser.error('--backup-dir must be outside scanned paths')
    checked, invalid, repaired = 0, [], []
    for source in args.paths:
        paths = (
            sorted(
                p
                for p in source.rglob("*.md")
                if not any(part.startswith(".") for part in p.relative_to(source).parts)
            )
            if source.is_dir()
            else [source]
        )
        for path in paths:
            checked += 1
            try:
                original = path.read_bytes()
                text = original.decode('utf-8')
                candidate = repair_status(text) if args.fix_status else text
                metadata = parse_frontmatter(candidate)
                validate_attention_dates(metadata)
                if not args.attention_dates_only:
                    validate_status(metadata)
                if candidate != text:
                    save_repair(path, original, candidate.encode('utf-8'), args.backup_dir)
                    repaired.append(str(path))
            except (OSError, UnicodeError, MetadataError) as exc:
                invalid.append({"path": str(path), "error": str(exc)})
    print(json.dumps({"checked": checked, "invalid": invalid, "repaired": repaired}, indent=2))
    return 1 if invalid else 0


if __name__ == "__main__":
    raise SystemExit(main())
