---
aliases:
  - Daily Enforcement Protocol
---
# Daily Rhythm

> This file is the canonical operational reference for daily planning rhythm and mode routing. Do not duplicate the same policy prose elsewhere unless there is a strong reason.

Load `review-progress.md` and persist the current startup/review/planning scope before working through this procedure. Greeting and open-conversation routing follow that reference; a greeting alone does not activate this full daily checklist.

## Day-of-week modes

### Period-type override — Bonus Week
- If the current week artifact has `period_type: [[Bonus Week]]`, that overrides normal weekday execution mode.
- Surface the bonus week by name, dates, and focus mode before setting Top 3 or starting work.
- Default lane: reflection, cleanup, recovery, catch-up, vacation, or the explicitly chosen focus mode—not automatic launch/execution mode.
- If urgent work must override the bonus week, record the tradeoff explicitly in the daily note and bonus-week note; do not let the next cycle silently consume the buffer.

### Monday-Thursday — execution days
- Default mode: focused work / delivery.
- Open the current day surface and apply the current routing surface.
- Run normal daily planning: capture, resurfacing checks, Top 3, first deep-work block, hard commitments.
- Surface both resurfacing lanes when realistic:
  - at least one planned/cadenced resurfacing item from the system
  - and at least one random rediscovery item when possible
- Treat that "at least one planned/cadenced item" rule as a floor, not permission to omit open tasks whose `due` or `review_on` is today.
- Also run the daily fall-through sweep: check overdue tasks (`due < today`) and stale resurfacing tasks (`review_on < today`) so missed weekly reviews or busy days cannot let the system fill with hidden debt.
- Treat distraction control and deep-work protection as first-class.
- When shallow/admin residue threatens to sprawl, use a bounded tactic from `execution-tactics.md` rather than letting miscellaneous work leak across the whole day.
- Default execution-day surfaces include the structured task views that support due-today, resurfacing, overdue, and carry-risk work.

### Friday — execution close + weekly review
- Preserve the main delivery lane, but protect a Friday closeout block for the weekly retrospective while evidence is fresh.
- Run the Friday weekly review from `review-cadence.md`: mind dump, week reconstruction, outcome/evidence audit, balanced-life/habit assessment, backlog hygiene, resurfacing, and a concise Sunday planning handoff.
- For sprint/cycle/quarter/year periods ending Sunday, begin the smallest-to-largest retrospective stack Friday; leave only unresolved decisions and weekend delta for Sunday.
- Friday review closes the execution week; it does not need to perfect the next-week plan.
- If Friday is constrained, use an explicit reduced review and name the recovery point; do not silently push an unlimited review into Sunday.

### Saturday — lighter day
- Default mode: recovery, leisure, relationships, errands, and the **Saturday-specific** habit cadence.
- An intentionally designed weekly off-day from a normally daily habit can be part of adherence rather than a lapse when the user has explicitly chosen it to preserve intrinsic engagement, polarity, or recovery. Do not impose a token minimum version merely to preserve a streak; keep the next scheduled re-entry visible.
- Saturday is not a default hard-core workday.
- If work is needed, prefer the smallest context-fit action or a short intentional block.
- If a real work lane exists, prefer one intentional work lane and use a bounded admin tactic only when it protects that lane.
- Still surface at least one resurfacing item so the memory system stays alive.
- Keep obligations visible without turning the day into a weekday clone.

### Sunday — weekly planning / reset day
- Default mode: protected next-week planning + weekly reset, not a replay of Friday's review.
- Read Friday's review handoff, run only a bounded Saturday/Sunday reconciliation, resolve genuine review debt or unfinished higher-level decisions, then choose the Weekly MIT, Top 3, capacity/tradeoffs, and Monday launchpad.
- Route exact-today and material new backlog items, but do not perform a second full stale-debt cleanup when Friday already did it.
- Use the effective-dated personal habit roster for Sunday’s movement/meditation anchors; planning mode does not decide the exercise schedule.

## Schedule input

Read the current personal habit roster and its effective date before choosing named movement/rest/meditation anchors. Resolve dated exceptions before the general schedule. Historical scoring uses the schedule effective then; a skipped recurring event does not reset its alternation unless explicitly agreed. Do not infer a personal exercise day from a generic weekday-mode template.

## Morning foundations

At the day-shaping level, think in a Detect → Decide → Act → Review loop:
- **Detect** the real mode, current week `period_type` (especially bonus week), constraints, resurfacing, and missing reality from yesterday.
- **Decide** the day's lane and what gets protected versus deferred.
- **Act** inside that lane rather than staying in open-ended sorting.
- **Review** with explicit closeout so the next day starts from reality.

Before advancing to execution:
- when the owner asks “what’s next?”, returns after a gap, or is in a planning/review flow, run a steering scan before recommending action: identify the correct cadence mode; check missed period boundaries; query exact-today due/review items plus overdue/stale debt; explicitly search/query for open or draft missed-review recovery artifacts/tasks (weekly/sprint/cycle/quarter/year); scan the current/next 14 days for high-salience dated artifacts and relationship/family/travel/calendar commitments; surface the active cycle/week outcome scoreboard, current release/external-evidence gate, and current sprint/cycle critical tasks; then state the recommended next step and what was intentionally deferred
- if the previous day did not receive a real closeout, reconcile where it actually landed before locking today's plan
- if there are one or more missing/incomplete dates since the last Exo interaction, run interaction-gap recovery across all missing dates before locking today's plan: enumerate dates, ask for compact per-date reality/habit/ritual status, create/update retroactive daily notes where meaningful reality surfaced, and explicitly scan the missed date range for cadence boundaries (especially Sundays and week/sprint/cycle endings) so any missed weekly/sprint/cycle/quarter review debt is named and promoted into the active review stack before current-period planning proceeds; it is not enough to list the recovery task as stale debt
- if reconciliation surfaces date-specific accomplishments, habits, events, or reflections from a missing/incomplete day, update or create that actual target daily note retroactively with a clear source/creation marker; do not leave the actual day blank just because it was reported later
- verify the current week artifact exists and read its `period_type`; if it is missing, stop and create/repair it before assuming weekday execution mode
- if `period_type` is `[[Bonus Week]]`, surface the bonus week and focus mode explicitly before any normal planning
- confirm core habits / virtues for the current mode, including any named mandatory habit, **intentional cadence off-day**, or day-specific weekly ritual from the visible habit roster; ask about it explicitly instead of hiding it behind generic "movement," and do not misclassify a designed off-day as a lapse
- for a future recovery-aware movement decision, distinguish **not fully recovered now** from **unlikely to be ready at activity time**: when the user is improving and intentionally resting ahead of the activity, preserve a readiness checkpoint at the actual decision time rather than preemptively canceling it or treating ordinary improving soreness as an injury; ask about symptom type/red flags, keep the plan conditional, and contract/substitute only if readiness evidence warrants it
- respect established combined-ritual semantics: when one habit is intentionally completed inside another named ritual (for example meditation inside the scheduled yoga session), surface and record the combined ritual rather than demanding a duplicate standalone session; if the combined ritual is deferred, make the shared re-entry point explicit
- surface the day's resurfacing items explicitly by name
- distinguish outcome progress from enabling progress; if a new enabler or lane enters today's active set, require its target outcome, blocker evidence, stop/checkpoint condition, owner/capacity, and displaced commitment before locking the plan
- explicitly name every open task with `due` today or `review_on` today, and route each one (Top 3, Admin Strike, schedule with review_on, delegation, or drop)
- run the fall-through sweep for `due < today` and `review_on < today`: name counts plus high-salience items/next actions, then decide whether to clear, defer, or schedule cleanup
- surface active weekly minimums as a radar check
- confirm non-negotiables / hard constraints

Think in terms of **ritual-critical foundations**, not isolated checklist boxes.

### Graceful degradation and re-entry
When the preferred daily rhythm breaks, do not collapse into "the system failed." Choose the strongest recoverable version:
1. **Full version** — run the ritual/tactic as designed.
2. **Reduced explicit version** — shorten it while keeping the structure visible.
3. **Minimum viable version** — do the smallest action that preserves continuity.
4. **Intentional defer + re-entry point** — explicitly defer and name when/how to restart.

Use this for morning foundations, closeout, resurfacing, weekly reset anchors, and other rhythm-critical steps. A lapse should become a concrete re-entry decision, not shame or silent omission. If deferring, record the re-entry point in the day note, task metadata, or the relevant review artifact.

### Interaction-gap recovery
When the user returns after one or more missed interaction days, recover continuity before locking the current day.

Use a compact by-date pass:
- What happened / where did the day actually land?
- Completed work, errands, relationship events, or notable constraints?
- Core habits: water, meditation, movement/training, planning/closeout.
- Named scheduled rituals and recovery-aware habits from the roster that was effective on that date; preserve intentional substitutes and combined-ritual credit.
- Open loops that should carry forward into tasks, reviews, or future-facing reminders.

For one missed day, ask directly. For multi-day gaps, use a low-friction table or summary prompt and drill only into high-salience or uncertain dates. Create/update actual retroactive daily notes for meaningful day-specific reality.

### Weekly minimum radar
Surface important non-daily minimums during morning review so they do not disappear just because they are not due today.
Examples include:
- long-form reading sessions
- Friday full weekly review + Sunday weekly planning
- training minimums
- Named training/rest/combined-ritual anchors from the effective-dated personal habit roster

## Resurfacing

Run `resurfacing.md` for the exact-today, overdue, all-class reminder, and random-rediscovery contract. Report checked surfaces, counts, high-salience names, and explicit routing before locking the plan. Keep the result in the daily startup progress record described in `review-progress.md`.

## Midday
- Re-check whether the day is still aligned with its intended mode.
- Re-scope if needed.
- Use named bounded tactics when they protect the main lane; do not let them silently expand into day-long miscellaneous work.
- In short windows before hard stops, prefer concrete context-fit next actions over large planning rituals.

## End of day / closeout
- Complete the end-of-day scorecard or review closeout appropriate to the mode.
- Carry forward unfinished work intentionally.
- Use `planning-task-os` for the exact task carry-forward metadata rules.
- Set the next relevant starting point for tomorrow.

## Design principles

- The active mode should be visually and operationally obvious.
- Important things should surface when they should.
- The day should match reality rather than forcing every day into the same workflow.
- The day-routing surface is a routing aid; policy/rhythm logic should not be buried only inside runtime-surface code.
- Portable daily-routing scaffolds should live with the skill (for example under `assets/runtime-surfaces/`); local note-system wiring may point to them directly or mirror/adapt them, but should not make a vault template the only copy.
