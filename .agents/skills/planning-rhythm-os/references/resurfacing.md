---
aliases:
  - Spaced Repetition and Resurfacing Policy
---
# Resurfacing

> This file is the canonical operational reference for resurfacing and spaced repetition inside the planning rhythm.

## Purpose
Make important things reappear when they should, while also rediscovering useful older material that would otherwise stay buried.

## Two lanes
### Planned / cadenced resurfacing
Use explicit future-facing hooks so known-important items reappear on purpose.
- Primary mechanism: `review_on`
- Secondary mechanisms: `due`, week/sprint placement, and explicit plan/review commitments
- These items should surface in daily execution and in weekly/higher-cadence reviews

### Random rediscovery
Regularly re-surface older notes, journal entries, saved media, and adjacent ideas even when they are not on a fixed schedule.
- Purpose: rediscover forgotten insights, reconnect with long-term themes, and surface non-obvious opportunities
- Use random notes, older journal entries, saved media, graph exploration, or nearby linked notes

## Daily minimum
- Every day, surface at least one resurfaced item.
- On normal execution days, prefer surfacing:
  - at least one planned/cadenced item from the system
  - and at least one random rediscovery item when possible
- Treat that planned/cadenced minimum as a floor, not a cap.
- Any open task with `due == today()` or `review_on == today()` must be surfaced by name during morning review, even if it will later be deferred.
- Older open tasks with `due < today()` or `review_on < today()` are resurfacing/overdue debt and must be acknowledged every morning via the daily fall-through sweep.
- For every task surfaced because it is exact-today, overdue, or stale-review debt, include its current concrete next action in chat when it is high-salience or selected for routing.
- If only one item is realistic that day, choose the highest-value resurfacing item for the moment while still acknowledging the existence/count of any unresolved debt.

## Dated reminder coverage

Query both open tasks and all dated reminders. `review_on` is an attention hook on any supported note class, including projects, people, health, works, and companies; it does not turn that record into a task. Include exact-today and past dates. Exclude terminal states Done and Closed (linked or plain representation); retain Reviewed, Someday, Waiting, and legacy Later/Incubating when their review date arrives.

Before an attention/linked-period scan, run the Obsidian metadata validator with
`--attention-dates-only` over the vault using its available runtime. This checks
strict YAML and valid `YYYY-MM-DD` values for `due`, `review_on`, `week_start` and
`week_end` (absent/null is allowed). Report failures as incomplete coverage;
do not silently coerce timestamps, empty strings, numbers or lists into dates.
The preflight deliberately does not reject status debt; unknown/missing statuses
remain eligible under the saved date filters. Full write validation still checks
the status canon as well as dates. Do not change a timestamp into a day without
establishing the intended owner date.

Present a task and a non-task reminder together only when their links and content establish the same underlying commitment. Keep both source references visible and do not suppress a distinct obligation on title similarity alone. Reviewing a non-task note can lead to an action, an explicitly chosen next review date, removal of an exhausted reminder, or no change with a named unresolved decision. Never auto-advance review dates or create duplicate tasks merely to clear the view.

The note-system Adapter must name the task view and the all-class reminder view, query both, and report metadata/query errors. An empty task result does not establish an empty reminder queue. Preserve each result's source membership and deduplicate identical paths when reporting a combined count. Anchor both queries to the same live date and owner timezone, and name the scan scope and freshness. The owner has resolved the terminal policy: saved attention views exclude only Done and Closed, in linked and plain form; Reviewed and Ended do not hide due reminders. Repair contradictory filters with backup and query verification, rather than silently dropping returned records. This reference owns surfacing behavior; `planning-task-os` owns task field/lifecycle meanings.

## Execution-day workflow
- Query both the task-debt and all-class dated-reminder surfaces described above.
- Explicitly enumerate open tasks whose `due` or `review_on` is today before locking the daily plan.
- Also query overdue / stale-resurfacing debt (`due < today` or `review_on < today`); surface counts plus high-salience names/next actions and route a cleanup path if the list is too large.
- Surface at least one older note / journal entry / saved media item for random rediscovery. Use the bundled `scripts/rediscover.py <eligible-paths.txt>` sampler instead of assuming GNU `shuf` is installed; inspect the selected note before summarizing it.
- Always include a concise summary of each random-rediscovery item in chat so the user does not have to open the note cold.
- If a resurfaced item matters for current execution, convert it into a task, plan line, decision checkpoint, or other explicit future-facing artifact.
- If not doing a due-today / review-today item now, re-route it explicitly rather than letting it remain background fog.
- If not doing an overdue / stale-review item now, either route it to Now, defer with a new `review_on`, mark it Done/Drop/Someday, or schedule bounded cleanup; do not let it stay invisible because the exact date passed.
- Do not leave meaningful resurfacing only in chat or reflection prose.

## Weekly and higher-cadence reviews
- Weekly, sprint, cycle, quarter, and year reviews must include a resurfacing step.
- Review both:
  - planned/cadenced resurfacing
  - random rediscovery
- When feasible, explicitly revisit at least 1–3 older notes, journal entries, or saved media items rather than only current tasks.
- If an item should come back in the upcoming period, operationalize it before closing the review.

## Design principle
Important things should surface when they should.
- Planned reminders should reappear intentionally.
- Random rediscovery should keep the system alive, surprising, and connected to the deeper memory graph.
- Both lanes matter; neither is sufficient alone.
