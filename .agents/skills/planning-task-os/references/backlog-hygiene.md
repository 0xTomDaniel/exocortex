---
aliases:
  - Task Backlog Hygiene Policy
---
# Task Backlog Hygiene

> This file is the canonical operational reference for task backlog hygiene.

## Purpose
Prevent uncontrolled backlog growth and keep task lists aligned with current importance, urgency, and real commitment.

At the task layer, this is mostly the Decide/Review half of the system: decide what is actually committed now, then review unfinished work with explicit recommitment or release.

## GTD-inspired operating principles
- Maintain a **trusted system**: if open loops are captured but not regularly clarified and reviewed, the system loses trust. Stale debt is a system-maintenance failure signal, not background noise.
- Separate **capture → clarify → organize → reflect → engage**. Do not let capture masquerade as control; every active task needs a clear outcome, concrete next action, and intentional review/due hook.
- Use **next-action discipline**: if a task cannot name the next visible action, it is not ready for the active lane.
- Separate **hard landscape** from discretionary work: true deadlines, appointments, and external commitments get `due`; optional resurfacing and incubation get `review_on`.
- Keep **Waiting / delegated / blocked** items explicit instead of letting them remain as stale todos.
- Use **Someday** aggressively for worthwhile-but-not-current items so the active list stays trustworthy.
- Apply the **two-minute / obvious-completion rule** during reviews: mark obvious Done/Drop/Someday immediately instead of preserving clutter for a later cleanup pass.
- Weekly review is the keystone, but daily mini-review prevents the Sunday review from becoming archeology.
- Distinguish **surface hygiene** from **substantive review**: clearing `due` / `review_on` debt in metadata is not the same as walking through meaningful open loops with the user. Do not describe stale debt as "worked through" unless it was actually reviewed or was an obvious mechanical Done/Drop/Someday decision.

## Core rules
- Keep at most **20 active tasks** at a time. For reporting, active means `[[Todo]]` + `[[Doing]]` (Now maps to Todo); Waiting, Someday, Done, and Closed are separate lanes. Report excess for an explicit capacity decision; never auto-close, demote, or change dates to satisfy the cap.
- Weekly triage is required for unfinished tasks.
- Daily fall-through triage is required at a lighter level: every morning, check overdue and stale-review items so missed weekly reviews cannot hide debt.
- Every unfinished task should be explicitly classified into a current commitment bucket from the closed task canon in `task-model.md`. Scheduling later preserves Todo/Doing if the commitment remains; Waiting names a dependency, Someday releases current commitment, and dropping uses Closed with a resolution
- Carry-forward is allowed only when the task has:
  - a new `due` date when real urgency exists
  - a clear `importance` judgment
  - a concrete `next_action`
- If a task is carried forward 2+ times, force a decision:
  - split it
  - schedule it
  - park it
  - delegate it
  - or drop it

## Daily fall-through checklist
- Query open tasks with `due <= today()` or `review_on <= today()` before the day is locked.
- Name and route every exact-today item.
- For older overdue/stale items, surface counts plus high-salience names/next actions; if there are too many to process, schedule a bounded cleanup block and refresh `review_on` for any intentionally deferred items.
- Mark obvious completions immediately so done work does not keep polluting the active surfaces.
- If a parent decision / umbrella task's intended outcome was achieved and remaining work lives in dedicated child follow-up tasks, mark the parent `[[Done]]`. If it was replaced without completion, use `status: "[[Closed]]"` plus the truthful resolution (usually `[[Superseded]]`) and link the successor instead of keeping a stale proxy active.

## Weekly hygiene checklist
- Open the active weekly task surface (normally the system's current-week task view, plus overdue / surfaced items when needed).
- If the system uses period-scoped task surfaces/views (for example current week / current cycle / current sprint / next sprint prep), advance those views to the newly active periods during rollover and validate them immediately.
- Mark genuinely completed tasks `[[Done]]`; mark unfinished but intentionally terminated tasks `[[Closed]]` with an explicit resolution instead of conflating completion with cleanup.
- Close resolved parent / decision tasks once the core outcome is achieved, even if child cleanup tasks remain open elsewhere.
- Trim active tasks to 20 or fewer.
- Re-score `importance` for each carried-forward task.
- Confirm `next_action` and an intentional attention hook for each carry-forward. Preserve a real external `due` date; use `review_on` for discretionary re-entry instead of inventing a deadline.
- Re-check still-open surfaced overdue / Now items before concluding carry-forwards, especially relationship / admin commitments already surfaced by the system.
- Move non-current items to `[[Someday]]` with `review_on`.
- Drop stale items with no clear value.
- Close superseded formulations without destroying history: preserve unchecked outcomes, add the closure rationale and successor link, and trust the new task rather than retaining both as active emotional insurance.

## Defaults for this vault
- Carry-forward means intentional recommitment, not automatic rollover.
- Period-scoped task views are part of backlog hygiene too; if their filters drift to old week/cycle/sprint values, the execution surface is considered stale until corrected and re-validated.
- If the weekly review is skipped or incomplete, the next daily morning start must explicitly say so and run a stronger fall-through sweep rather than assuming the backlog is clean.
- Tasks without `due` + `next_action` are not eligible for the real Now lane unless there is a clear short-horizon commitment reason.
- For actionable active tasks, maintain lightweight execution metadata:
  - `next_action`
  - `est_minutes`
  - `energy`
  - `work_type`
  - optional `context` only when it materially improves filtering
- Prefer a small number of useful execution filters over context proliferation.
- Use `carry_count` as the default lightweight aging signal.
- If age/staleness needs more explanation, rely on note history / creation date or add dated bullets to a `Progress Log`.

## Boundary with task model
- Use `Task Model` for the canonical meaning of `importance`, `due`, `review_on`, and `status`.
- Use this file for active-backlog size, recommitment rules, and carry-forward hygiene.
