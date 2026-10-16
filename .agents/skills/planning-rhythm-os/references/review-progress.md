# Review progress and resumption

This reference owns completion and resumption across daily startup, retrospective review, and next-period planning. Cadence discovery remains in `review-cadence.md`; reminder coverage in `resurfacing.md`; task lifecycle in `planning-task-os`.

## Conversation and re-entry

At greeting or re-entry, check the current dated note, relevant current period notes and their linked open handoffs using the available note-system Adapter. Follow references to older unfinished recovery scopes; search existing planning/review records when the likely notes do not resolve what remains open. Inspect actual records and their evidence, not titles or a `Planned` label alone. This is bounded discovery of continuity, not a claim to have scanned every reminder. Report missing access or unresolved discovery rather than asserting there is no unfinished work.

If unfinished work is relevant now, briefly name its scope and exact next step and offer to resume. Prefer the owner's latest explicit priority, a due re-entry commitment or a hard deadline; mention a competing obligation only when it changes that recommendation. Honour deferred re-entry points and explicit cancellation. A paused workflow remains available without becoming an obligation to resume immediately. Avoid repeatedly steering back after the owner redirects.

If no unfinished workflow is found in the checked context, act as an executive assistant: consider known commitments, upcoming events, available time, relevant personal context and opportunities to prepare or remove friction. Offer a useful next action when supported, or respond naturally when the owner wants to explore or talk. Use current memory before personalizing; do not invent urgency, a task list, or a completion gate. A full daily scan begins when the owner enters startup/planning or requests steering, not merely on “hello.”

For non-rhythm workflows, use their owning skill and existing task/project artifact for scope, completed work, unresolved decisions and next action. Do not impose this period-specific JSON schema on unrelated work. Canonical task records continue to own obligations; progress records link them rather than storing a second task database.

## One record per scope

Store one `review-state` fenced JSON block in the actual daily/review/plan note for the scope being worked. Generate its initial shape with:

```bash
python3 scripts/review_state.py init --kind week --period 2026-W37 --phase planning
```

Kinds: day, week, sprint, cycle, quarter, year. Phases: startup, review, planning. Use actual period identity, never the example value by default. A week review and its next-week plan are separate scopes; a sprint plan is not confirmed by either week. Do not use one completion flag for an entire stack.

The generated record has mandatory steps, evidence references, coverage dates, missing-date resolution, unresolved decisions, exact next step, confirmation and workflow disposition. `init` prints JSON only. Save it in the owning note before the first substantive step, then read it back. Update it through the approved persistence layer after each material decision or substantive step and before a known interruption; do not rely on an end-of-call flush. An abrupt interruption can prevent a final write, so resume from saved evidence and reconcile any unsaved discussion before retrying actions. Preserve the user's raw capture separately from Exo synthesis.

The optional version-1 `workflow` extension has `status`, `reason`, `source` and `resume_when` fields. Newly initialized records include it. Status is `active`, `paused`, `deferred` or `cancelled`; completion is still derived from the exact-scope evidence contract, never a manually assigned workflow status.

- `active`: work is being pursued. Keep the exact next unfinished step.
- `paused`: a tangent or interruption has suspended work. Retain scope, evidence, unresolved decisions and next step; record the reason and available source without inventing a user decision.
- `deferred`: the owner explicitly chose a later return. Record that decision's source and a concrete date or trigger in `resume_when`; use the existing dated reminder/target-period mechanism if future attention is needed.
- `cancelled`: the owner explicitly ended this workflow. Record reason and source, retain its history, and clear the executable next step. Cancellation is not completion and does not cancel linked tasks or other scopes without an applicable decision.

On resumption, set the disposition to `active` and continue the preserved next step. Material changes must invalidate affected evidence and confirmation as described below. Old version-1 records without the extension remain checker-compatible; that compatibility does not prove they are currently active. Reconcile actual notes and owner decisions before adding the extension when an unfinished scope is resumed.

During a tangent, explore naturally. Capture a meaningful commitment in its canonical task or other appropriate record, link it from affected planning work, and update capacity/displacement decisions if necessary. An idea, hypothetical or reflection is not automatically a commitment. Do not ask bookkeeping questions when the scope is clear. When the owner returns, resume the exact preserved step; neither the tangent nor completion of its action closes the enclosing workflow.

## Beginning and resuming

1. Read the relevant period notes, recent dated reality, current habit roster and the existing progress record. Enumerate missing dates and missed boundaries. Missing notes/interactions are unknown evidence, not proof that a habit was skipped or done.
2. Discover the full review stack, including older open recovery artifacts. Record missing artifacts and uncertainty explicitly; do not treat absent review files as completed work or silently begin the next cycle.
3. Resume the exact unfinished step when returning to that workflow. Record task and non-task reminder query evidence; an empty task view alone cannot satisfy coverage. Record the scan date/time, checked surfaces and limitations. Prior-day results and reading Base definitions do not establish current coverage. If the available Adapter cannot perform a required scan, leave that step pending and report the missing coverage; proceed with supported work or an explicitly accepted reduced scope. Do not mark unavailable retrieval complete.
4. A step may be complete only after the named work is actually performed. Attach source references to discussion, decisions, or checked records. Drafting a scaffold, updating a date, or naming a future task is not evidence that its substantive review occurred.

## Completion check

Save a material decision and its source promptly in the owning note, invalidate affected step evidence and confirmation there, and record any remaining cross-note reconciliation as unresolved with an exact next step. Then reconcile its consequences across the affected canonical task, day, week and enclosing plan notes: dates, ordering, capacity totals, displaced commitments, current-status prose and next steps. Do not delay initial capture until all notes can be reconciled. On interruption or re-entry, consult these pending changes before relying on an affected note's older confirmation or status.

Update the current instructions; keep superseded decisions clearly historical so the active plan is unambiguous. Clear affected scopes' prior confirmation and reopen their status until the revised scopes are checked and confirmed. Preserve unrelated confirmed scopes. If an affected note cannot be updated, retain that inconsistency as unresolved and do not claim the plan is consistent or complete.

```bash
python3 scripts/review_state.py check /path/to/review-or-plan.md
```

Exit 0 means the recorded evidence/confirmation contract is structurally complete; 1 means work remains; 2 means the record is missing or malformed. Read the returned errors and next step. Only after a successful check **and cross-checking its evidence against the actual user discussion** may the scope's status be advanced. This helper is not independent proof of human agreement and is not a security boundary against its editor.

Paused, deferred and cancelled records never pass as completed scopes. A cancelled scope needs no executable next step and should not be presented as work to resume. Check each scope whose status you advance, including every week being marked planned alongside a sprint. An enclosing record must reference the actual child decisions; it cannot substitute for their own checks. “Lock it in” applies only to the scope actually discussed; resolve material ambiguity instead of propagating consent through a stack.

Distinguish saved content (write and readback), structurally valid metadata/progress (validator result), owner-confirmed decisions (scope-specific source) and completed scope (actual work plus the check). Summarize what was saved, what remains open and its next step; a successful tool call or finished backing turn establishes none of these other outcomes by itself.

Record a user confirmation quote and source that explicitly apply to this scope and mode. Never manufacture historical consent or copy week confirmation to a sprint/cycle. A coherent reduced review may complete when the user explicitly accepts its omissions and remaining coverage; list each omitted step, rationale and source, and mirror those names in `confirmation.accepted_omissions`. An unresolved substantive decision stays open rather than being relabeled an omission just to pass the check.

Coverage can end Friday when Friday's retrospective is honestly finished and Sunday owns the weekend addendum. A blank missing-date list still needs an explicit `missing_dates_resolution` such as `none; all dates accounted for`. When dates are missing, state what is known, what remains unknown, and what limitation the user accepted. Do not impose the newest habit schedule on earlier dates.

## Existing records

Do not bulk rewrite historical statuses to fit this schema. For an already closed historical review, report legacy completion as unverified by this checker unless the source evidence is actually reconciled. Initialize a record when an unfinished scope is next resumed, carrying forward only the work supported by its current notes/transcript. Keep the exact unresolved handoff; adding a record does not confirm the review.
