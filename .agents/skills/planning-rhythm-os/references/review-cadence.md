---
aliases:
  - Review Cadence Policy
  - Weekly Review Process
---
# Review Cadence

> This file is the canonical operational reference for the Friday-review / Sunday-planning cadence, review debt, review stacks, and weekly planning handoff.

## Core cadence rule

The configurable default weekly split is:
- **Friday: weekly review / execution closeout.** Review the week while work evidence is fresh; run retrospective synthesis, outcome conversion, balance/habits, resurfacing, and backlog hygiene.
- **Sunday: weekly planning / reset.** Reconcile only material Saturday/Sunday evidence, consume Friday's review outputs, choose the next Weekly MIT and Top 3, establish capacity/tradeoffs, and set Monday's launchpad.

Protect the split. Do not rerun the full Friday review on Sunday by default; that recreates the overlong combined session and consumes the attention needed for planning. Friday's review normally covers Monday through the review time on Friday. Sunday's brief weekend reconciliation appends meaningful weekend reality without reopening settled work-week conclusions unless the new evidence genuinely changes them.

Periods still close on their true calendar boundary. For a sprint/cycle/quarter/year ending Sunday, start its retrospective on Friday after the weekly review while evidence is fresh, then use Sunday only for a bounded weekend delta, explicit final decision/confirmation, and next-period planning. If no weekend evidence affects the conclusion, do not repeat the retrospective.

If Friday review is missed, Sunday must detect the debt before planning. Use graceful degradation: a bounded recovery review that extracts only decision-critical evidence, then protect enough attention for actual planning. Record the miss and Friday re-entry point for the next week.

If Exo interaction skips a Friday/Sunday or period boundary, the next re-entry must check which weekly/sprint/cycle/quarter/year review or planning artifacts were missed. Promote genuine review debt into the active recovery stack before treating a current/next period plan as locked.

## Covered timeframes
- [[Week]]
- [[Sprint]] (2 weeks)
- [[Cycle]] (6 weeks)
- [[Quarter]]
- [[Year]]

## Review stack order
When multiple periods close on the coming Sunday, begin the retrospective stack Friday from **smallest to largest**:
1. Weekly review
2. Sprint review
3. Cycle review
4. Quarterly review
5. Yearly review

This lets higher-level reviews synthesize lower-level evidence. Sunday finalizes only unresolved decisions/weekend deltas, then plans from largest relevant period down into the next week and Monday.

## Review-stack integrity
- Before declaring the active Friday review stack or Sunday planning/finalization stack, run review-debt discovery, not only date math.
- When reporting that no **older review debt** was found, distinguish that from reviews or plans closing/starting this weekend and restate the active stack.
- Review-debt discovery includes:
  - inspect current and immediately prior period artifacts for open/unfinished review or planning-recovery pointers;
  - query/search open tasks whose purpose is missed weekly/sprint/cycle/quarter/year review recovery;
  - query/search review artifacts with all plausible unfinished-status variants (including compound values such as `Missed - Draft`) where the review date is today or earlier;
  - **distinguish substantive review debt from metadata-only status drift:** read the artifact body, source day note/conversation, immediate continuation, downstream period plan/review, and completed recovery tasks before deciding a stale marker means the review was not worked;
  - when evidence shows a review was substantively completed or explicitly recovered in reduced form, correct it to `Done` with review mode, completion/correction dates, and evidence; when invalidated, close it truthfully with successor/rationale.
- Create/use every required review artifact; instantiating a scaffold is not completion.
- A Friday retrospective may be complete before the calendar period ends when its declared coverage is explicit and Sunday owns the weekend addendum. This is not a missed review.
- A higher-level Friday first pass remains `In Progress` only when substantive decisions are unresolved; do not keep it open merely because Sunday has not occurred.
- If time/energy only allows a scaffold, label it draft/first-pass. If the full stack is not recoverable, choose reduced review, minimum viable review, or intentional defer with a named re-entry point.
- Genuine overdue higher-cadence review debt outranks ordinary current-period planning, but recovery must be bounded enough to preserve planning attention.
- If admin/inbox items interrupt review or planning, capture/route them and explicitly return to the exact unfinished cadence step.

## Balanced-life lens
Every cadence review and next-period plan explicitly considers:
- work / mission / craft
- health / body / recovery
- relationships / love / friendship / family
- hobbies / play / exploration / creative nourishment
- soul / meaning / spirit / inner life

The goal is not fake equal weighting. Startup-founder periods may be intentionally asymmetric; record what is protected, consciously deferred, and why.

Preserve intrinsically motivated play separately from externally evidenced expression. Private creative nourishment can count without publication unless the selected outcome is inherently communicative or the owner explicitly chose a sharing contract.

## Governing-purpose alignment
When the user has an explicit higher-level purpose or mission, treat it as a governing layer over the portfolio rather than automatically creating another equal lane.
- Friday review: name direct purpose/mission progress, enabling progress, drift/displacement, and how each major lane funded, embodied, transmitted, constrained, or protected the purpose.
- Sunday planning: select at least one bounded progress signal for the coming week, relate the Weekly MIT/Top 3 to the governing purpose, and state any deliberate week with no direct progress plus its re-entry point.
- Require evidence appropriate to the purpose: a tested thesis, artifact, experiment, relationship, governance decision, or externally observable step. Repeatedly restating the purpose is not progress.
- Preserve support lanes such as income, health, relationships, family, and responsible closure. The check is whether support remains intentionally connected to the governing purpose rather than silently replacing it.

## Weekly semantics
- `review_week` = the ISO week being closed/reviewed.
- `plan_week` = the upcoming ISO week being planned.
- Friday's review and Sunday's planning refer to the same review/plan pair.
- The Friday review artifact records `review_date` and `coverage_end`; Sunday's weekend addendum may extend evidence through Sunday.
- Sunday's daily artifact still belongs to `review_week`; committed carry-forwards target `plan_week`.

## Friday weekly review process
1. **Mind dump first**
   - Capture the owner's raw thoughts in their own words before opening structured task views.
   - Do not pre-fill the mind dump from system summaries.
2. **Read the week back**
   - Read available daily artifacts/message logs from Monday through Friday.
   - Treat missing days as evidence and reconcile material gaps.
3. **Review the week**
   - Wins, misses, lessons, habits, notable constraints, and the balanced-life lens.
4. **Audit outcome conversion and external evidence**
   - Read the active cycle/week outcome scoreboard back explicitly.
   - Separate shipped/external outcome, external evidence, and enabling/internal progress.
   - After two missed weekly gates or a sprint gate, force continue / contract / bypass / change-goal / defer / stop.
   - Confirm an external-evidence test occurred or is deliberately planned.
   - For any new strategic/external lane, name owner, capacity, evidence, stop condition, and displacement.
5. **Run backlog hygiene**
   - Open the current task surface plus overdue/stale views.
   - Include `due < today` and `review_on < today`; clear obvious Done/Drop/Someday, recommit true current work, and date any remainder.
   - Meaningful stale items must be discussed/batched unless they are mechanical completions or low-value incubations.
   - Hand exact task semantics to `planning-task-os`.
6. **Explore resurfacing**
   - Preserve planned/cadenced and random-rediscovery lanes.
   - Operationalize anything that should affect next week.
7. **Produce a planning handoff—not the plan**
   - Name decision inputs: outcome/evidence verdicts, unresolved decisions, hard dates, realistic available capacity, candidate MITs, risks, and balanced-life minimums.
   - Do not spend Friday attention perfecting next week's daily plan unless needed for a team commitment or imminent Monday constraint.
8. **Close the Friday review**
   - State habit assessment, planned and random resurfacing, debt disposition, and the concise change signal for next week.
   - Mark the review complete when its retrospective work is complete; note `coverage_end: Friday` and leave a clear Sunday planning pointer.

## Sunday weekly planning process
1. **Protect planning attention**
   - State that Sunday is planning/reset, not a default replay of Friday's review.
   - If Friday review exists, read its handoff first.
2. **Run a bounded weekend reconciliation**
   - Capture meaningful Saturday/Sunday outcomes, habits, relationship events, constraints, or decisions.
   - Append only evidence that changes the weekly assessment or next-week plan.
3. **Resolve cadence debt and closing-period decisions**
   - Audit review debt and the periods ending today.
   - Finalize only unresolved higher-level decisions/weekend deltas from Friday; do not repeat settled retrospectives.
   - If Friday review was missed, use a time-bounded reduced recovery review before planning.
4. **Run Sunday surfacing delta**
   - Explicitly route exact-today `due` / `review_on` items and acknowledge overdue/stale debt.
   - Do not perform another full backlog-hygiene session if Friday already did it; process only material new/due items or explicitly route a bounded remainder.
5. **Choose the Weekly MIT**
   - Name one best lever, externally observable finish line, why it matters, explicit non-goals/fallback, and at most one manually intensive enabler.
6. **Build the next-week plan**
   - Create/repair the next week artifact and validate cadence fields.
   - Re-check hard dates, active outcomes, still-open overdue/Now items, relationship/admin commitments, and realistic capacity.
   - Choose Top 3, named life anchors, lane boundaries, evidence/stop conditions, and displaced commitments.
   - If a bonus week intervenes, surface and plan it explicitly rather than silently starting the next cycle.
   - Advance/validate current-week structured surfaces where needed.
7. **Create Monday's launchpad**
   - Pre-select Monday Top 3, first deep-work block, hard habits/appointments, and any bounded pre-deep-work Admin Strike.
8. **Close planning**
   - Link Friday review to the next-week artifact.
   - Propagate commit / schedule / close and carry-forward decisions into real task metadata.
   - Remove provisional markers and mark the plan locked only after the owner confirms it.
   - State what changes next week and resume the remaining Sunday habit anchors from the effective-dated roster.

## Required outputs
### Friday review
- reconstructed intended goals/commitments
- wins, misses, lessons, habits, and balance assessment
- outcome/external-evidence verdicts and forced decisions
- resurfacing worth carrying forward
- backlog/debt disposition
- concise Sunday planning handoff

### Sunday planning
- weekend delta / final closing-period decisions
- Weekly MIT with external finish line and non-goals
- Top 3 with capacity/displacement clarity
- balanced-life protections/deferrals
- next-week artifact and Monday launchpad
- propagated task metadata and a confirmed/locked plan

## Follow-up rule
Do not leave explicit review/planning follow-ups as plain-text ritual reminders. Complete them or convert them into explicit future-facing artifacts.

## Runtime-surface boundary
Canonical procedure lives here. Runtime surfaces can point, prompt, and summarize, but must not become a second hidden procedural source. Portable scaffolds live in `../assets/runtime-surfaces/`.

## Common artifacts
- `Weekly Review - YYYY-W##` — normally worked Friday, with optional Sunday weekend addendum
- `Planning/Weeks/YYYY-W##` — next-week execution/plan artifact, normally locked Sunday
- optional sprint/cycle/quarter/year review and plan artifacts

## Boundary with planning-task-os
Use this skill for cadence/review/planning flow. Use `planning-task-os` for task property semantics, carry-forward, commit / schedule / park / close, `importance`, `due`, `review_on`, and `status` updates.

## Durable completion and interruptions

Use `review-progress.md` for the single completion/resumption contract. Maintain a distinct progress record for each review or planning scope. Its mandatory steps include both task debt and all-class reminders; reduced coverage, missing dates, and user confirmation must be explicit. Before advancing status, run the checker and inspect the referenced discussion. On interruption, persist the exact next step, then resume it before introducing a fresh plan.
