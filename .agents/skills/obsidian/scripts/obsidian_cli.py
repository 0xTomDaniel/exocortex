"""Obsidian CLI Adapter: explicit selection, canonical paths, visible failures."""

import subprocess


def run_obsidian(args, vault=None):
    command = ["obsidian"] + ([f"vault={vault}"] if vault else []) + list(args)
    # A missing CLI response is a transport failure, not an empty graph.
    # Retry only these read-only calls, once; never retry a mutation here.
    attempts = 2 if args and args[0] in {"file", "links", "backlinks"} else 1
    for _ in range(attempts):
        try:
            result = subprocess.run(command, text=True, capture_output=True, timeout=30, check=False)
        except (OSError, subprocess.TimeoutExpired) as exc:
            return 1, "", str(exc)
        out, err = result.stdout.strip(), result.stderr.strip()
        if out or err or result.returncode or attempts == 1:
            failed = out.startswith(("Error:", "File not found", "Vault not found"))
            return result.returncode or (1 if failed else 0), out, err
    return 1, "", "Obsidian returned no response after one read-only retry"


def note_selector(note):
    return f"path={note}" if "/" in note else f"file={note.removesuffix('.md')}"


def resolve_note(note, vault=None):
    code, out, err = run_obsidian(["file", note_selector(note)], vault)
    fields = dict(line.split("\t", 1) for line in out.splitlines() if "\t" in line)
    if code or not fields.get("path"):
        raise ValueError(f"Cannot resolve {note}: {err or out or 'no canonical path returned'}")
    return fields["path"]


def parse_links_output(text, include_flags=True):
    links = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line == "No links found.":
            continue
        unresolved = line.endswith(" (unresolved)")
        target = line.removesuffix(" (unresolved)")
        if include_flags:
            links.append({"target": target, "unresolved": unresolved})
        elif not unresolved:
            links.append(target)
    return links
