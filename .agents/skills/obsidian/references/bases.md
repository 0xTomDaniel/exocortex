# Bases Reference (Obsidian CLI skill)

Use this reference when working with `.base` files, Base views, or Base-backed planning workflows.

## Source coverage

This reference is derived from Obsidian Help pages:
- Bases/Introduction to Bases
- Bases/Create a base
- Bases/Views
- Bases/Bases syntax
- Bases/Functions
- Bases/Formulas
- Bases/Layouts/Table view
- Bases/Layouts/List view
- Bases/Layouts/Cards view
- Bases/Layouts/Map view
- Bases/Bases roadmap

## Core model

- A Base is a database-like view over vault files/properties.
- Base data comes from Markdown files and frontmatter properties.
- `.base` stores view/filter/formula configuration.
- A base can have multiple views (table, list, cards, map).

## Decision rules: properties vs filters vs formulas

- Use **note frontmatter properties** for durable source data (`status`, `due`, `people`, etc.).
- Use base `properties:` config for presentation metadata (for example `displayName`).
- Use **global `filters:`** for scope constraints that must apply to every view.
- Use **view-level `views[].filters`** for per-view slices.
- Global + view filters are combined with **AND** at runtime.
- Use `formulas:` for derived/computed values reused across sorting/filtering/display.
- Use `order` / `groupBy` to organize results; use `limit` only as a display cap.

## Safe workflow (CLI-first)

1. Discover/create base via CLI/UI commands first.
2. Immediately scope dataset (folder/tag/property constraints).
3. Query results and verify scope.
4. Add/adjust views for specific use-cases.
5. Re-verify after each change.

### Minimal command pattern

```bash
obsidian bases
obsidian command id=bases:new-file
obsidian rename file="Untitled.base" name="Relocation Tracker.base"
obsidian base:query file="Relocation Tracker.base" format=tsv
```

## Direct `.base` editing policy

Prefer CLI/UI operations. Edit `.base` directly only when CLI cannot express needed configuration.

When editing directly:
- keep valid YAML
- use valid filter structure (`and` / `or` / `not`)
- avoid unintended extra default views
- run `base:query` immediately

## Known-good scoped filter example

```yaml
views:
  - type: table
    name: Relocation
    filters:
      and:
        - file.path.startsWith("Relocation/")
```

## Common failure modes and checks

- **Noisy results (unrelated files):** Base is unscoped or scope too broad.
- **Empty results:** Scope doesn't match actual paths/tags/properties.
- **Filter parse errors:** Invalid filter object shape (must use `and`/`or`/`not`).
- **Confusing view behavior:** unintended extra default view exists.

Validation checklist:
- `obsidian base:query file="<base>.base" format=tsv` returns intended records only.
- Scope constraints are explicit and documented.
- Views have clear purpose labels (for example `Active`, `Done`, `Trips`).

## Layout-specific notes

- **Table:** best for editing properties, summaries, and bulk review.
- **List:** best for compact status-oriented scans.
- **Cards:** best for gallery-style/visual browsing.
- **Map:** requires Maps plugin; coordinates can be text `"lat, lng"` or list `[lat, lng]`.

## Formula and function usage

- Formulas can reference note properties, file properties, and other formulas (`formula.x`).
- Avoid circular formula references.
- Useful globals include `if()`, `date()`, `now()`, `today()`, `link()`, `list()`, `number()`.
- Use formulas for derived fields; keep source truth in note properties.

## Roadmap awareness

Bases is still evolving; prefer robust, explicit config and verify behavior after Obsidian updates.
