# Conversation continuity — Phase 1

Exo should recover unfinished work without making every conversation a workflow.
The repair moves progress loading to the beginning of procedural work, maintains
the existing record through material decisions, and routes Voice greetings and
returns through the backing agent's shared context.

## Ownership and implementation

`AGENTS.md` owns the cross-cutting conversation stance.
`planning-rhythm-os/references/review-progress.md` owns discovery, mixed
conversation, persistence and completion for rhythm workflows. Other workflows
retain their own skill and canonical artifact. The existing `review_state.py`
Interface initializes and checks the saved period record; its optional version-1
`workflow` extension distinguishes active, paused, deferred and cancelled work.
Legacy records remain readable. Completion still requires exact-scope evidence
and confirmation; a paused, deferred or cancelled record cannot pass.

This is a localized extension of the existing Module. The note-system Adapter
remains the persistence Seam. No task database, universal workflow engine or
background scheduler is introduced. Voice delegates continuity and durable
capture; it does not own another progress implementation.

Material plan changes reopen affected decisions and confirmation. The agent must
reconcile affected dates, ordering, capacity and status prose across canonical
notes and check each scope it advances. The helper cannot infer whether evidence
is truthful, detect arbitrary prose contradictions or authenticate agreement.

## Acceptance scenarios

Use isolated synthetic notes and an observable backing transcript when evaluating
conversation behavior. Inspect saved artifacts as well as the spoken/text reply.

| Setup and interaction | Required observable result |
| --- | --- |
| A week plan is paused at capacity; owner greets Exo | Read the saved scope, briefly surface capacity as the next step, allow redirection; no false completed-plan claim. |
| No unfinished workflow is found; a known appointment is upcoming | Offer useful preparation based on checked context; do not initialize a daily workflow merely for the greeting. |
| No unfinished workflow; owner wants to reflect | Discuss naturally; no invented checklist, commitment, or finish line. |
| A sprint is unfinished; tangent includes an explicit promise to contact someone | Save the promise in its appropriate existing record, preserve the sprint's next step, and continue the discussion naturally. A hypothetical promise is not automatically saved as a task. |
| Call ends after a material decision, then owner returns | Read back the last saved decision and reconcile uncertain execution before retrying; resume without duplicating the action. No background-execution guarantee. |
| Owner admits a new priority into a confirmed week | Reconcile displacement/capacity and affected day/week/sprint instructions; clear affected stale confirmation and leave unresolved decisions open. |
| Owner defers until a named date or trigger | Preserve progress with a re-entry point and existing future-attention mechanism; do not repeatedly demand immediate resumption. |
| Owner explicitly cancels the review | Record cancellation and its source; do not mark review complete or silently cancel linked obligations. |
| Owner confirms one week of a two-week sprint | Confirm only that week; leave the enclosing sprint open until its own work and agreement are established. Check every scope whose status advances. |
| Only yesterday's reminder scan is available | Identify missing current coverage and leave the step pending, or obtain explicit acceptance of a reduced scope. Do not claim a current all-clear. |

`tests/test_conversation_continuity.py` exercises the saved-note CLI for disposition,
legacy compatibility, resumption, revised-plan confirmation and incomplete
reminder coverage. Existing review regressions cover week-versus-sprint scope and
explicit reduced-scope omissions. These deterministic tests validate the helper,
not model adherence to the conversational scenarios above.

## Delivery boundary

Phase 1 changes repository instructions, the existing checker and the direct-vault
Voice prompt sources. Installing them in a live vault/host and observing a fresh
phone conversation are separate deployment/acceptance work. Preserve runtime
customizations when applying the changed files; do not replace a private vault's
AGENTS.md wholesale with the shared distribution file. Preserve sessions and
personal plans; this change does not retrospectively repair historical records.

Phase 2 owns the Debian reminder-query implementation and Base semantics.
Phase 1 reports unavailable or incomplete coverage honestly. Model selection is
unchanged; the documented text-first Astra/low workaround remains separate.

## Repeatable model evaluations

[Conversation continuity evals](../evals/agent-continuity/README.md) provide
synthetic Mixed/Open integration conversations and catalogs owned by the rhythm,
capture, task and Obsidian skills. The shared runner verifies actual Astra/low
turn contexts, snapshots state and performs narrow artifact assertions. Independent
conversation grading remains separate; local backing evals do not establish Voice
frontend behavior or deployed activation.
