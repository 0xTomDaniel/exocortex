# Relationship Navigation Reference (Obsidian skill)

Use this reference for on-demand relationship exploration in the vault.

## When to use scripts vs Bases

- Use scripts for ad hoc exploration and one-off investigations.
- Use Bases for persistent dashboards and recurring filtered views.

## Script toolbox

### 1) Neighborhood exploration

`link_neighborhood.py` — n-hop graph around one seed note.

```bash
python scripts/link_neighborhood.py "Seed Note" --depth 2
python scripts/link_neighborhood.py "Seed Note" --depth 2 --include-backlinks --json
```

Use when: you want local context quickly.

### 2) Path finding

`link_path.py` — shortest outgoing-link path from source to target.

```bash
python scripts/link_path.py "Source" "Target" --max-depth 4
```

Use when: you need to explain how two topics connect.

### 3) Filtered neighborhood

`filtered_neighborhood.py` — neighborhood traversal with filters.

```bash
python scripts/filtered_neighborhood.py "Seed" --depth 2 --tag relocation
python scripts/filtered_neighborhood.py "Seed" --depth 2 --prop status=active --date-property rental_return --date-before 2026-03-10
python scripts/filtered_neighborhood.py "Seed" --depth 2 --modified-after 2026-03-01
```

Key options:
- `--tag <tag>` (repeatable)
- `--prop key=value` (repeatable)
- `--date-property <name>` + `--date-after/--date-before`
- `--modified-after/--modified-before`
- `--strict-filter-traversal` to only expand from matching nodes

Use when: you want only a filtered subgraph for specific criteria.

### 4) Bridge discovery

`bridge_finder.py` — find notes that connect multiple seed neighborhoods.

```bash
python scripts/bridge_finder.py "Seed A" "Seed B" "Seed C" --depth 2
python scripts/bridge_finder.py "Seed A" "Seed B" --depth 2 --include-backlinks
```

Use when: you need connector notes between people/projects/topics.

### 5) Unresolved-link triage

`unresolved_triage.py` — rank unresolved link targets by frequency and source coverage.

```bash
python scripts/unresolved_triage.py "Seed" --depth 2
python scripts/unresolved_triage.py "Seed A" "Seed B" --depth 2 --top 15
```

Use when: you want to prioritize which missing notes to create first.

## Output interpretation tips

- High unresolved edge counts often indicate missing notes worth creating.
- If path/bridge results are empty, increase depth or include backlinks.
- If results are noisy, add tag/property/date filters.
