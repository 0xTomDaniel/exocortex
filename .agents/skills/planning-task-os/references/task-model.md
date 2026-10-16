# Task Model

> This file is the canonical operational reference for the planning/task operating system. Do not duplicate the same policy prose elsewhere unless there is a strong reason.

## Canonical distinction

Treat these as separate concepts:

- **Importance** — how much the task matters in principle
- **Urgency** — how much time pressure exists
- **Commitment** — whether it is actively in play now
- **Resurfacing** — when it should come back if not active now

Preferred property meanings:

- `importance` — canonical importance field
- `due` — urgency anchor / external time pressure; if the task is open and `due == today()`, it must be explicitly surfaced during morning review; if `due < today()`, it is overdue debt for the daily fall-through sweep
- `review_on` — resurfacing date for future reconsideration; if the task is open and `review_on == today()`, it must be explicitly surfaced during morning review; if `review_on < today()`, it is stale resurfacing debt for the daily fall-through sweep
- `status` — one of `[[Todo]]`, `[[Doing]]`, `[[Waiting]]`, `[[Someday]]`, `[[Done]]`, `[[Closed]]`; follow the Obsidian skill’s `references/status-canon.md` for the shared note-type canon and normalization rules
- `resolution` — why a terminal task ended when status alone is not enough (for example `[[Superseded]]`, cancelled, duplicate, or no longer relevant)
- `next_action` — one concrete visible next step
- `est_minutes`, `energy`, `work_type`, optional `context` — execution support metadata

If the vault still contains legacy `priority` properties, treat them as migration debt unless the system intentionally chooses to keep that name.
If the vault still contains legacy importance values such as `[[High]]` / `[[Medium]]`, treat those as transitional calibration debt until the richer verbal importance scale is fully applied.

## Truthful terminal-state semantics

- `[[Done]]` means the intended outcome was actually completed. Do not use it merely to make an unfinished task disappear.
- `[[Closed]]` means the task is no longer an active commitment even though its original outcome was not completed.
- A closed unfinished task must preserve an auditable explanation: add `resolution`, `closed`, a dated closure note, and `superseded_by` when another task now owns the value.
- `[[Superseded]]` does not mean the old work was worthless or completed. It means the old task formulation no longer governs action because a newer task, experiment, release contract, or decision now owns the relevant outcome.
- Closing is reversible: if the old outcome later becomes relevant as a distinct commitment, reopen it with current metadata or create a newly scoped task and link back. Do not keep obsolete task shells active as emotional insurance.
- Runtime surfaces must exclude both `[[Done]]` and `[[Closed]]` (including equivalent plain-text forms) from active-work views while preserving the notes as history.

## Hard surfacing semantics

- For non-terminal tasks, `due == today()` and `review_on == today()` do not automatically mean "must finish today," but they do mean "must be brought to awareness today."
- During morning-start, every open task matching either exact-today condition must be explicitly named in chat and in the daily note before the daily plan is locked.
- `due < today()` and `review_on < today()` mean the task did not get resolved when it was supposed to surface; these are debt signals, not expired reminders.
- During the daily fall-through sweep, acknowledge older debt with counts plus high-salience names/next actions before locking the plan. High-salience means all `[[Extremely important]]` / `[[Very important]]`, imminent external deadlines, relationship/admin commitments, and current sprint/cycle items.
- If not doing a surfaced item today, route it intentionally: Top 3, bounded Admin Strike, defer with a new `review_on`, delegate, `[[Someday]]`, or drop.

## Importance scale

Use verbal anchors tied to planning horizons so they stay less fuzzy.

### Extremely important
- Top leverage / top consequence.
- Usually only a tiny number of active tasks should have this level.
- Think: **current week / current crunch lane**.
- Example: a must-ship deadline path like [[Projects/Example Release]] during the final days.

### Very important
- Clearly matters this week or sprint.
- Strongly valuable, but not the single defining lane.
- Think: **current sprint / this week's major secondary commitments**.

### Important
- Meaningful within the current cycle.
- Should not be forgotten, but should not automatically outrank the week's main lane.
- Think: **current cycle / active domain commitments**.

### Somewhat important
- Worth preserving, but easy to defer.
- Usually better as Someday / scheduled resurfacing material than as a daily competitor.
- Think: **background but real**.

### Not important
- Useful mainly as a landing zone for Eisenhower-style decisions: drop, delegate, park, or move to `[[Someday]]`.
- Avoid keeping many active tasks here; if it is truly not important, it usually should not stay in the active backlog.

## Why the timeframe tie-in helps

The verbal categories become much less fuzzy when they imply different planning horizons:

- **Extremely important** -> week / crunch
- **Very important** -> sprint
- **Important** -> cycle
- **Somewhat important** -> later / background
- **Not important** -> drop / delegate / someday

This keeps the scale grounded in operational reality rather than vibes alone.

## Eisenhower interpretation

Use Eisenhower as a decision lens, not necessarily a stored field.

- **Urgent + Important** -> do now / protect
- **Important + Not urgent** -> schedule / resurface / protect from drift
- **Urgent + Not important** -> constrain, batch, delegate, or minimize
- **Neither** -> drop, someday, or remove from active competition

This is one reason `importance` is a cleaner stored field name than `priority`: `priority` often implies a blended decision that already incorporates urgency and other factors.

## Anti-inflation rules

- Keep `Extremely important` scarce.
- Recalibrate if too many tasks sit in the top two bands.
- In a true deadline-compression window, demote almost everything outside the minimum ship path.
- If a task is repeatedly deferred and never wins attention, lower its importance, park it, split it, or drop it.

## Practical interpretation examples

- A deadline-critical ship task can be **Extremely important** and urgent.
- A strategic system design project can be **Very important** or **Important** but not urgent.
- A phone-tab cleanup task can be **Somewhat important** or **Not important** right now and live in `[[Someday]]` with `review_on`.

## Design principle

Store source facts cleanly; derive blended judgments later.

Good stored facts:
- `importance`
- `due`
- `review_on`
- `status`
- `next_action`

Derived decision concepts:
- what should happen today
- what is "hot"
- Eisenhower quadrant placement
- blended priority ordering inside a Base view or review session
