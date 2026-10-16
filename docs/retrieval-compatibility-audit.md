# Retrieval compatibility audit

The Phase 2 audit compared native Obsidian 1.13.7 / installer 1.12.4 with Nitride
using a disposable synthetic vault and the public CLI. Its source evidence and
dispositions live in Nitride's `docs/compatibility-audit.md`, four added conformance
cases and nine separately recorded native observations. These are not personal
vault fixtures or a claim of complete Base compatibility.

## Closed questions

- Valid quoted/unquoted ISO days select the same due/exact-day/past/future notes.
- Empty strings differ from absent/null; native malformed-date rollover and
  timestamp/numeric/date coercions can differ from Nitride. Exo's existing
  calendar-day contract must therefore be validated rather than inferred.
- Dotfiles/hidden folders are excluded. Native file discovery includes visible
  attachments, while native Base queries return Markdown only. The new pin fixes
  Nitride's candidate membership to match that query contract.
- Ten Nitride public-process clock cases cover Denver midnight and both DST
  transitions with a different host timezone. These control only the test child
  process clock, not the OS or native application clock.
- Existing native cases continue covering ordinary numeric/string and boolean
  comparisons, empty groups, guarded operations and linked period properties.
  General coercion outside those recordings remains an explicit compatibility limit.

## Enforcement and execution

Before an attention or linked-period scan, invoke the installed Obsidian skill's
existing validator:

```sh
uv run <obsidian-skill>/scripts/validate_notes.py --attention-dates-only <vault>
```

Require success before claiming complete query coverage. `due`, `review_on`,
`week_start` and `week_end` must be valid ISO calendar days or absent/null.
Timestamps, blank strings, lists, numbers, booleans, non-padded or impossible dates
are errors. Missing dates remain valid; this is not a requirement to invent a
due/review date for every note. Do not truncate timestamps without deciding the
intended owner date. Remove a date property to clear it.

The read-only mode deliberately skips status validation so unknown/missing status
does not hide eligible reminders. Full write validation checks both contracts.
YAML parsing failures, including invalid YAML-native date values, are structured
errors; existing duplicate-key diagnostics remain intact. Never describe failure
as an empty scan or silently normalize date values to satisfy a query.

Nitride stays generic: its evaluator does not contain Exo field names or workflow
policy. The visible Markdown vault remains authoritative and no new task store
or persistent scan index is introduced.

## Validation and remaining acceptance

The Nitride change passes 117 tests and 84 recorded conformance/package cases.
Exo passes 137 tests, including the actual validator CLI for all four date fields,
structured failures, and unknown-status scan eligibility. A bounded private vault
inventory found all current attention/period values within the supported contract;
no date migration was necessary. Private deployment/query evidence stays outside
the repository.

Linux and macOS Nitride CI passed. The built Debian image passed all 84 isolated
package cases, matched the pinned bundle hash and was deployed with retained
sessions and Codex 0.153.4. Both live metadata checks passed; five named acceptance
views returned identical desktop/Debian JSON. Model defaults remain Astra/low and
the process owner timezone remains America/Denver. This verifies runtime queries,
not a new phone-originated agent turn.

The source image now pins merged Nitride commit `101629fbade8bf2d71fe2074e1c0803b996f562c` and its
verified source archive SHA. The merged skill files are byte-identical to the
reviewed `d20fb50` skill used in the live validation above; that deployed image
retains its pre-merge tag until rebuilt. Deployment retained sessions, model settings,
timezone and mounts and installed the targeted shared skill/adapter changes with
backups. Fresh preflight and named-query comparisons passed. Closing these compatibility
checks does not establish phone-originated Voice acceptance, which remains separate.
