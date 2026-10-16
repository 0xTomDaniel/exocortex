---
name: obsidian
description: >-
  Operate Obsidian for note automation, vault search, link-graph exploration,
  daily-note workflows, task extraction, Bases workflows, and
  plugin/theme/developer tasks using approved Nitride, Obsidian CLI, or filesystem capabilities. Use when a user asks to
  run or script Obsidian commands, inspect vault content, analyze note
  relationships, or automate repetitive Obsidian actions.
metadata:
  exo.category: general
---
# Obsidian

## Overview

Select the available tool before composing commands. For supported read-only Base discovery, view listing and queries, prefer the installed Nitride skill/CLI across runtimes. Load its skill for invocation and compatibility limits. If Nitride is unavailable or the operation is unsupported, native Obsidian is a fallback only when its approved desktop app/CLI is available. Preserve saved filters and report errors; do not turn fallback into a weaker or incomplete successful scan.

Use this skill's native workflow below for operations assigned to the Obsidian CLI. On a filesystem-only runtime, use its Adapter's supported read/edit/validation route and explicitly report unavailable application checks.
Before attention or linked-period Base scans, run `uv run scripts/validate_notes.py --attention-dates-only <vault-path>` and check its exit status. This read-only preflight rejects invalid YAML and unsupported attention/period dates while leaving status debt visible. Full pre/post-write validation checks both dates and status. Canonical `due`, `review_on`, `week_start` and `week_end` values are valid ISO calendar dates or absent/null; remove a date property to clear it rather than writing an empty string.
Prefer concise command flows, discover exact command syntax with built-in help, and verify file-impacting changes.

Respect the active vault Adapter’s capability policy before following any native workflow below. If the owner has disabled native Obsidian CLI use, skip native setup and invocation entirely, including absolute app paths; use Nitride for its supported queries and filesystem tools plus metadata validation for other supported note operations. Do not reinstall or enable a forbidden fallback.

## Native CLI workflow

1. Confirm prerequisites:
   - Ensure the Obsidian desktop app is installed and running.
   - Ensure CLI is enabled in Obsidian settings and registered on this machine.
2. Gather context before execution:
   - Identify target vault (`vault=<name|id>`) when multiple vaults exist.
   - Identify whether this should update a daily note, a dedicated topic note, or both.
   - For any date-specific note or daily-note edit, verify the live date/time with `date` and the exact note path with `obsidian daily:path` before making changes.
   - If `obsidian daily:read` returns template-like or unexpected content, do not infer the file from filesystem search; resolve the target explicitly with `obsidian daily:path` first.
3. Discover command shape first:
   - Run `obsidian help`.
   - Run `obsidian help <command>` before composing non-trivial commands.
   - For syntax/editing/formatting questions, read `references/editing-formatting.md`.
   - For linking/aliases/embed questions, read `references/linking-notes-files.md`.
   - For relationship exploration and graph traversal, read `references/navigation.md`.
4. Run discovery before creating notes (avoid duplicates):
   - Run targeted `obsidian search` queries for note title/concept variants.
   - Use relationship scripts for canonical placement and overlap checks:
     - `python scripts/link_neighborhood.py <seed> --depth 2 --include-backlinks`
     - `python scripts/unresolved_triage.py <seed> --depth 2`
     - `python scripts/bridge_finder.py <seedA> <seedB> --depth 2 --include-backlinks`
   - Prefer updating/expanding an existing canonical note when overlap is high.
   - Link a new note to relevant existing entities or context when useful; do not create a hub merely to satisfy a linking rule.
5. Model notes according to their content:
   - Use the caller's canonical note type and destination after discovery.
   - Entity notes need minimal queryable metadata; add relationships supported by source evidence.
   - Use linked values for categorical/entity properties and typed scalars for dates, numbers, and checkboxes. Before setting note `status`, read `references/status-canon.md`: each note type has a closed lifecycle family, and descriptive notes need no generic status.
   - Choose body sections appropriate to the note; do not impose a project template on every capture.
   - For true multi-value fields, use lists instead of comma-separated strings.
   - Keep workflow decisions in the invoking skill and historical/current state in the relevant notes.
6. Use Bases for structured tracking when decisions/actions evolve over time:
   - Check existing bases with `obsidian bases`.
   - Read `references/bases.md` before non-trivial Base edits or new tracker design.
   - Prefer CLI/UI operations first (`obsidian command id=bases:*`) and avoid direct `.base` edits when possible.
   - Never leave a new Base in an unscoped default state.
   - Scope Base membership intentionally (for example by dedicated folder, tags, or status/property conventions) before treating it as a tracker.
   - If direct `.base` editing is unavoidable, treat it as fallback-only: use valid filter structure (`and`/`or`/`not`), keep only intended views, and test queries immediately.
   - Query with `base:query` to verify tracked records and confirm unrelated vault files are excluded.
7. Execute with explicit parameters and flags:
   - Use `key=value` parameters.
   - Use standalone boolean flags (for example `open`, `overwrite`).
   - Prefer Obsidian CLI for note creation, discovery, app actions, and structured metadata/property updates.
   - Prefer `obsidian rename` over filesystem renames when changing note names; Obsidian updates wikilinks automatically, but headings/aliases inside the file may still need manual edits.
   - Prefer `[[wikilinks]]` over hardcoded vault paths when referencing notes in prose, logs, templates, and documentation so later moves stay clean.
   - Do not create generic `_index.md` notes or folder-index stubs by default; prefer links/backlinks/Bases first, and only create a hub note when there is explicit user intent or clear navigational/editorial/workflow value.
   - For note templates that are copied into new notes (for example Daily Notes templates), do not put template-only or template-scaffolding frontmatter in the template unless those properties are intentionally meant to propagate. This includes obvious template metadata such as `type: "[[Template]]"` and `template_for`, but also convenience metadata like `policy` if the created note already links the policy in-body. The default template flow copies frontmatter into created notes and does not selectively exclude individual properties.
   - When template metadata must be dynamic at note-creation time (for example day-level `week` / `quarter` / `cycle` / `sprint` / `period_type`), prefer templating over static frontmatter. Configure the templating plugin so new notes derive cadence fields from the system's canonical upstream period source rather than hardcoding them. If this pattern is used, ensure that upstream source artifact exists before dependent notes are created.
   - Prefer standard filesystem read/edit tools for surgical Markdown content edits when they are more precise or reliable than CLI append/prepend flows.
8. Verify outcomes:
   - Read output with `obsidian read`.
   - Before a direct metadata write, validate the candidate note with `uv run scripts/validate_notes.py <candidate.md>`; after writing, validate the saved path and check `property:read` or the relevant Base. Native property updates still require application readback. Invalid YAML, duplicate keys, noncanonical status and missing Closed resolution are errors, never empty/open/done state. The validator checks the status canon by default; safe representation repairs require `--fix-status --backup-dir <private-directory-outside-vault>`. Review evidence before semantic migrations.
   - For a maintenance sweep, pass a vault directory to the validator (hidden directories are excluded); pass a hidden skill/reference path explicitly when that is the target.
   - Re-run search/tasks/base queries to confirm state changes.
   - Validate property semantics after updates (`property:read` + note read). Trust Obsidian CLI's canonical serialization: single-value `type=list` properties may render as quoted scalars in YAML and are still valid list-typed properties.
   - For true multi-value fields, ensure values are not stored as a single comma-separated scalar.
9. Persist memory:
   - Persist substantive decisions and outcomes in the caller’s canonical memory location. Avoid logging every mechanical edit in daily notes.
10. Apply feedback loops:
   - When the user gives process feedback, classify it as (a) operational correction or (b) vault improvement.
   - For operational corrections, update the relevant canonical instruction source when in scope.
   - For system improvements, update the canonical runtime surfaces / policy artifacts (not just the current daily note).
   - Confirm changes by reading updated artifacts and summarizing what was changed.

## Command Basics

- Run a single command:
```bash
obsidian help
obsidian daily
```

- Use TUI mode:
```bash
obsidian
help
```

- Pass parameters and flags:
```bash
obsidian create name=Note content="Hello world" open
```

- Target a specific vault (place `vault=...` before command):
```bash
obsidian vault="Work Vault" search query="roadmap"
```

- Target a file by name or exact path:
```bash
obsidian read file=Recipe
obsidian read path="Templates/Recipe.md"
```

- Copy command output to clipboard:
```bash
obsidian search query="TODO" --copy
```

## Common Task Patterns

- Open and update daily note (memory log):
```bash
obsidian daily
obsidian daily:append content="- Decision: ... | Constraint: ... | Next: ..."
```

- Create/maintain a dedicated topic note:
```bash
obsidian create name="Relocation - Lisbon Decision" content="# Relocation Decision\n" open
obsidian append file="Relocation - Lisbon Decision" content="\n## Context\n...\n\n## Decisions\n...\n\n## Next Actions\n- [ ] ..."
```

- Set linked properties (favor `[[wikilinks]]` for entities):
```bash
obsidian property:set file="Relocation - Lisbon Decision" name=people value="[[Jordan]]" type=list
obsidian property:set file="Relocation - Lisbon Decision" name=current_location value="[[Lisbon]]" type=text
obsidian property:set file="Relocation - Lisbon Decision" name=blocked_by value="[[Company Deal]]" type=text
```

- For multi-value linked properties, enforce proper YAML list formatting:
```yaml
candidate_locations:
  - "[[Porto]]"
  - "[[Braga]]"
```
(Do not store multi-value links as a single quoted comma-separated string.)

- Date handling:
  - In prose and task text, use date wikilinks (example: `[[2026-03-09]]`).
  - In frontmatter date-typed properties, keep ISO date values (example: `2026-03-09`) for type correctness.

- Property conventions (default):
  - Categorical/entity fields -> linked values (example: `importance: "[[Very important]]"`, `area: "[[Work]]"`, `status: "[[Todo]]"`).
  - Machine fields -> typed scalars (example: `due: 2026-03-09`, `carry_count: 0`, `blocked: false`).
  - Task/policy notes should not be schema-empty: add enough frontmatter to support Base views, triage, and carry-forward workflows.

- When to use properties, filters, formulas, and views in Bases:
  - Use note properties (frontmatter) to store durable source data on files (status, dates, people, location, etc.).
  - Use base `properties:` config for presentation metadata (for example `displayName`), not for filtering logic.
  - Use global `filters:` for scope constraints that must apply to every view (for example folder/tag boundaries).
  - Use view-level `views[].filters` for perspective-specific slices (for example "This week", "Done", "High importance").
  - Remember global filters and view filters are combined with AND at runtime.
  - Use `formulas:` for derived/computed values reused across filtering, sorting, grouping, and display.
  - Use `order` / `groupBy` for organization, and `limit` only as a display cap (not as a data-scope substitute).

- Use Bases for evolving plans/tracking (scoped):
```bash
obsidian command id=bases:new-file
obsidian rename file="Untitled.base" name="Relocation Tracker.base"
obsidian move file="Relocation - Lisbon Decision" to="Relocation/Relocation - Lisbon Decision.md"
obsidian base:query file="Relocation Tracker.base" format=tsv
```
For deep guidance (properties vs filters vs formulas, layout choices, direct-edit fallback policy, validation, and known failure modes), read `references/bases.md`.

- Search and inspect notes:
```bash
obsidian search query="meeting notes"
obsidian read
obsidian tags counts
```

- Navigate link relationships with bundled scripts:
```bash
python scripts/link_neighborhood.py "Relocation - Lisbon Decision" --depth 2
python scripts/link_path.py "Relocation - Lisbon Decision" "Lisbon" --max-depth 4
uv run scripts/filtered_neighborhood.py "Relocation - Lisbon Decision" --depth 2 --tag relocation --prop status=Doing
python scripts/bridge_finder.py "Lisbon" "Jordan" --depth 2 --include-backlinks
python scripts/unresolved_triage.py "Relocation - Lisbon Decision" --depth 2
```
For deeper usage patterns, read `references/navigation.md`.

- Diff note versions:
```bash
obsidian diff file=README from=1 to=3
```

## Developer Task Patterns

- Open developer tools and reload plugin:
```bash
obsidian devtools
obsidian plugin:reload id=my-plugin
```

- Capture screenshots and run app-side JS:
```bash
obsidian dev:screenshot path=artifacts/ui.png
obsidian eval code="app.vault.getFiles().length"
```

## Troubleshooting

- Run `obsidian help` to verify command availability.
- Check Obsidian settings if command registration is missing.
- Start Obsidian app before running command-heavy automation.
- Prefer exact `path=` when `file=` resolution is ambiguous.

## Reference

- Read `references/api_reference.md` for compact command catalog and usage notes sourced from the Obsidian CLI docs.
- Read `references/bases.md` for Bases-specific decision rules, syntax guidance, validation checks, and layout/formula context.
- Read `references/editing-formatting.md` for `/syntax` and Editing & Formatting docs coverage, including mode behavior, properties, callouts, tags, embeds, and HTML limitations.
- Read `references/linking-notes-files.md` for `/links` coverage, including internal link formats, heading/block refs, aliases, display text, and embeds.
- Read `references/navigation.md` for relationship-navigation workflows and script usage guidance.

## Helper runtime and artifact ownership

Graph helpers share `scripts/obsidian_cli.py` for command execution, canonical note resolution, and link parsing. Select an exact path when titles are ambiguous; a tool or metadata failure is not a successful empty query. `filtered_neighborhood.py` and `validate_notes.py` declare their PyYAML dependency for `uv run`. The latter uses the same strict parser as filtering.

Use `references/artifact-lifecycle.md` when organizing sources, packaged exports, captured evidence, and local runtime files.
