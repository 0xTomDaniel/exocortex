# Headless reminder retrieval

The direct-vault Voice deployment now ships Node 22.23.2 and Nitride pinned to
`0xTomDaniel/nitride-cli` commit `101629fbade8bf2d71fe2074e1c0803b996f562c`.
See the [deployment recipe](../deploy/voice/vault/README.md#pinned-nitride-retrieval)
and [host Adapter](../deploy/voice/vault/HOST-AGENTS.md#reminder-scan-route).
This is independent of the Hermes profile skill installer.

## Ownership and behavior

Exo's shared `AGENTS.md` owns capability selection across runtimes: prefer
installed approved Nitride for its supported read-only Base operations, with
native Obsidian fallback only where that capability is actually available.
The Obsidian skill routes to Nitride before entering its native CLI workflow.
Nitride owns interpretation of its documented read-only Base subset. Exo's
host Adapter owns concrete vault paths, source/view selection and runtime
invocation. The planning rhythm owns surfacing and coverage reporting. The
saved Bases own the current predicates; this integration does not change them.

The daily reminder scan executes the task fall-through view and all-note
attention view using the same live date and owner timezone. Preserve each
source membership and deduplicate identical paths for a combined count.
Different paths remain separate records even when content shows one obligation.
A reminder need not be a task. Source errors remain incomplete coverage, never
empty results or permission to substitute yesterday's scan.

The owner resolved the task/all-note terminal policy: exclude only Done and
Closed in linked and plain form; Reviewed and Ended remain eligible when due.
The shared Obsidian skill owns the closed note-type status canon, validation and
repair tooling. Saved Base filters express it explicitly; Nitride does not
normalize Exo lifecycle values internally. Linked-week/sprint filters are supported by the updated pin; query explicit
named views for the requested scope, and retain any other required unsupported
view as open coverage. A reminder-only scan does not complete the broader steering workflow.

## Initial integration validation — September 7, 2026

- Before implementation, the prior image failed the public runtime command
  check with `node: not found`.
- The new image built successfully and verified the pinned Nitride archive's
  SHA-256. Its bundled executable matched the upstream artifact byte-for-byte.
- All 71 upstream conformance cases plus package failure checks passed in a
  disposable Debian container using Node 22.23.2, with networking disabled and
  read-only input mounts. These native recordings establish a bounded subset.
- Exo's 128 repository tests, shell syntax and rendered Compose validation passed.
- Both actual daily reminder queries succeeded against a read-only vault mount.
  Per-source membership, overlap and combined path count were checked. Personal
  results and runtime evidence are private and are not source fixtures.
- The deployed Voice container exposes `node`, `nitride`, and the pinned skill
  through Codex discovery. Retained Codex 0.153.4 daemon state and remote-control
  enablement survived recreation. Sessions/model settings were not reset.
- A fresh Astra/low acceptance turn in a disposable instance of the same image,
  using the installed instructions and actual vault mounted read-only, selected
  Nitride, inspected the saved definitions, ran both current queries, read
  selected context, and reported matching overlap/counts and remaining limits.
  No private notes were changed. This is model execution evidence, not just an
  instruction walkthrough or deterministic test.

The first model test requested Codex's `read-only` sandbox inside the container;
its shell failed because the host disallowed unprivileged namespaces. It
correctly reported unknown counts and incomplete coverage. The successful test
used the container's existing isolation with a read-only vault mount instead.
Production sandbox settings were not changed.

The subsequent routing revision moved tool selection into the shared repository
`AGENTS.md` and updated the Obsidian skill to select Nitride before its native
workflow. The deployed vault received only those targeted edits, preserving its
existing local instructions. The host Adapter now supplies runtime locations and
capabilities. All 128 repository tests passed again. Inline review covered both
tools available, Nitride absent with native available, headless-only operation,
and neither tool available; the earlier model scan predates this ownership move.

## Remaining acceptance and scope

The model test was a fresh CLI backing turn, not a phone-originated realtime
audio turn. Resumed phone threads may retain stale instructions or model
overrides; fresh phone acceptance remains outstanding.

The bounded compatibility audit is now implemented: the corrected pin matches
native Markdown-only Base candidate membership, and Exo validates calendar-day
attention/period metadata before scanning. Native timestamp normalization,
malformed-date rollover and mixed-type date coercions are explicitly outside
Exo's date contract. See [the audit and preflight](retrieval-compatibility-audit.md).
No npm publication or full Obsidian CLI replacement is required for this route.

## Linked-period pin and review repairs

The new Nitride pin adds list/filter/value/length evaluation, linked scalar
metadata and file.basename, enabling the saved This Week and Current Sprint
views without rewriting them. Both actual views executed successfully against
a read-only mount before deployment. Empty output remains a saved-filter result,
not proof of plan completion or native desktop parity for private data.

The new image passed all 79 upstream package cases on Debian/Node 22.23.2, with
its executable verified against the pinned artifact; Nitride's 102 tests and
Linux/macOS CI passed. Exo's 128 tests and rendered Compose checks passed. The
Voice container was recreated with the new pin and retained Codex 0.153.4 state.

Both PR review findings were independently rechecked as fixed: the upgrade guide
now includes targeted shared AGENTS/Obsidian deployment, and counts/overlap use
exact paths even when presentation groups records describing one commitment.

A fresh final-instruction Astra/low CLI acceptance turn on the deployed image,
with the actual vault mounted read-only, loaded the shared routing policy and
ran both daily views plus This Week and Current Sprint successfully with one
owner-local date. It reproduced exact-path overlap/union counts and explained
an empty sprint result from direct task assignments and the unchanged saved
predicate. It did not infer a task's sprint from its linked week or mark planning
complete. Model/effort were verified in the recorded turn context.

Auxiliary inspection initially attempted unavailable `python` and then a missing
PyYAML module under `python3`. The agent disclosed these failures and completed
that inspection with available filesystem reads. These were not Nitride query
failures; the image does not promise a system PyYAML installation. No additional
runtime dependency was installed to conceal that limitation. Phone audio remains
separate from this fresh CLI model acceptance.

## Final reviewed pin

Nitride PR #2 merged as `0c33c7a` after repairing the independently reviewed
empty-reference defect. The final Exo pin uses that merged commit and its
verified archive hash. Nitride's 103 tests, 80 native package cases and CI pass;
the reviewer independently compared the repair with native Obsidian and closed
the finding. The final Debian image passed all 80 package cases and all four
actual saved queries, and Exo's 128 tests passed again. The earlier fresh-model
acceptance covers the final shared routing; the subsequent resolver repair has
native/public-CLI and deployed-image validation, not an additional model trial.
