# Canonical note status enforcement

Plain `Done` previously passed metadata validation and could remain visible in a
view excluding only `[[Done]]`. Open-ended lifecycle names also conflated scheduled
commitments, uncommitted possibilities, review events and elapsed periods.

The owner-approved [status canon](../.agents/skills/obsidian/references/status-canon.md)
defines lifecycle families by note type. `AGENTS.md` routes all note writes to
the existing Obsidian metadata validator; task and rhythm skills retain their
commitment and review responsibilities. Machine/job status fields are unaffected.

## Interfaces and ownership

- `validate_notes.py <paths...>` validates strict YAML plus canonical linked
  status membership and nonblank Closed resolution. Missing status is permitted
  and never means terminal; an unknown note type cannot receive an arbitrary status.
- `--fix-status --backup-dir <outside-vault>` repairs unambiguous representations,
  preserves unrelated metadata/body bytes, backs up originals, checks for concurrent
  changes and reads back the result. Legacy Later is intentionally not automatically
  parked: an actual commitment remains Todo/Doing/Waiting.
- `filtered_neighborhood.py --prop status=...` treats plain/linked canonical names
  and explicitly approved aliases equivalently through the status-policy Module.
- `repair_status_filters.py <base...>` audits standalone status predicates;
  `--attention` removes Reviewed exclusions. Applying requires `--apply` and a
  private backup directory. Compound/custom predicates require explicit inspection.
  Only targeted scalar spans are rewritten, preserving unrelated YAML values,
  comments and line endings. Anchored/aliased Bases are rejected for explicit
  inspection. Repeated application is idempotent. Queries must verify the result.

These existing metadata and saved-query Interfaces are the test Seams authorized
by the enforcement/cleanup request. The status-policy Module owns vocabulary and
normalization; Nitride remains the literal Base evaluator. No second task store,
filesystem daemon or write interception service is introduced. A direct filesystem
edit can bypass the validator; mandatory agent instructions plus pre/post-write
validation and maintenance audits are the enforcement supplied here.

## Migration rules

Preserve note bodies, dates, recorded outcomes and source evidence. Record prior
values and reasons in dated `status_history`, with original bytes in private
backups. Distinguish a scheduled commitment from Someday, and an elapsed period
from its unfinished review. A finalized bounded research pass can be Done while
retaining adverse/unknown decision gates; that is not action authorization.
Preserve owner-local guidance when installing shared changes.

Removing a generic status from a descriptive note must preserve its original
meaning in history or an appropriate domain property. No task conversion is
needed to retain a reminder. Report capacity consequences rather than adjusting
commitments merely to satisfy an active-count limit.

## Verification

Run the repository suite with the real installed/pinned Nitride bundle:

```sh
NITRIDE_CLI=/absolute/path/to/nitride/scripts/nitride.mjs \
  uv run python -m unittest discover -s tests
```

The status cases cover family validation, plain-text rejection on writes, safe
repair/readback and exact-byte backups, ambiguous values, invalid YAML, nonblank
closure reasons, read equivalence, and actual saved-query results for terminal,
parking, missing/unknown, Reviewed and Ended statuses. The query case explicitly
skips when Nitride is not supplied; a default test run alone is not query proof.

For deployment, run a full vault audit and fresh named attention/capacity/period
queries in both desktop filesystem and Debian runtime. Compare exact results and
preserve private migration and query evidence outside the repository. Deterministic
validation does not establish model adherence; phone-originated acceptance remains
a separate check.
