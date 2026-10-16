## Local vault Adapter

Load `obsidian` for note capture and metadata validation and `nitride` for
supported Base queries. Native Obsidian CLI is disabled for this deployment;
do not invoke it by name or absolute application path, re-enable it, or use it
as fallback. The owner can continue using the Obsidian desktop application.

Use filesystem read/search/edit tools for Markdown and YAML operations. Resolve
the live owner date/time before dated work. Inspect `.obsidian/daily-notes.json`
and existing daily-note paths to determine the daily note; when unset, the native
daily-note defaults are root folder and `YYYY-MM-DD`. Resolve custom-plugin or
ambiguous mappings before writing. Validate candidate and saved metadata and
reread files after edits. Filesystem renames do not maintain links automatically:
inspect and repair affected links explicitly. Desktop/plugin operations and
unsupported Base semantics remain unavailable.

This vault's `.agents/skills` is canonical. Pi and Codex discover it directly
when launched here. `.claude/skills` links to `../.agents/skills` and
`.claude/CLAUDE.md` links to `../AGENTS.md`. Edit canonical files only. Do not add
a visible root instruction symlink: Nitride rejects visible symlink candidates.

Resolve the Nitride script relative to its installed skill location. Invoke
`node <nitride-skill>/scripts/nitride.mjs` with an explicit absolute vault path
and owner timezone. Before attention/linked-period queries, require success from
`uv run <obsidian-skill>/scripts/validate_notes.py --attention-dates-only <vault>`.
Discover the actual saved views and query both tasks and all-class reminders
with the same live owner date. Invalid metadata or unsupported queries leave
coverage incomplete; never substitute a weaker filter or a stale result.
