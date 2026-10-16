---
name: planning-task-os
description: >-
  Task/backlog operating-system design, including routine task creation and completion/closure, task schema design,
  importance-vs-urgency modeling, commit / schedule / park / close triage,
  carry-forward hygiene, task-calibration rules, and task-schema migrations
  (for example renaming `priority` to `importance` and updating trackers,
  runtime surfaces, and policies). Use when the user wants to redesign or
  calibrate the task system, interpret Eisenhower or JTBD-style importance
  scales, triage tasks using the system's decision model, or safely update
  task-related notes, runtime surfaces, policies, and structured trackers.
metadata:
  exo.category: general
---
# Planning Task OS

Use this skill for routine task creation, triage, completion/closure, carry-forward, and task-model changes. Read only the reference needed for the transition.

## Core model

- Separate **importance**, **urgency**, and **commitment**.
- Prefer `importance` as the canonical property name for how much something matters.
- Treat `priority` as a blended human decision concept, not the preferred stored source field.
- Let urgency come mainly from `due`, overdue state, and nearby deadlines.
- Let `review_on` handle intentional resurfacing for things that are not urgent now. The daily surfacing procedure is owned by `planning-rhythm-os/references/resurfacing.md`.
- Treat `due < today()` and `review_on < today()` as active debt signals: they must be visible in the daily fall-through sweep and resolved through commit / schedule / park / close or a bounded cleanup pass.
- Let `status` express commitment/lifecycle state (`[[Todo]]`, `[[Doing]]`, `[[Waiting]]`, `[[Someday]]`, `[[Done]]`, `[[Closed]]`). Use `[[Done]]` only when the intended outcome was completed; use `[[Closed]]` plus an explicit `resolution` when unfinished work is cancelled, duplicated, or superseded.
- Use Eisenhower as a **thinking lens / Base view**, not necessarily as stored metadata on every task.
- Treat this skill and its references as the **canonical operational source** for the planning/task operating system unless explicitly superseded.
- At the task layer, this skill mainly owns the Decide/Review parts of the Detect → Decide → Act → Review loop: classify commitments clearly before work and carry them forward intentionally after work.
- Avoid duplicated policy prose across the vault and the skill. Retire duplicated policy notes after migration; keep only the minimum breadcrumbs needed during transition.

## Default workflow

1. **Identify the job**
   - Distinguish between:
     - task triage / calibration
     - schema design
     - task migration
     - tracker / runtime-surface / policy updates caused by task-model changes
   - If the task is primarily about day modes, cadence, Sunday routing, weekly review flow, or planning-period semantics, use `planning-rhythm-os` instead of stretching this skill beyond its boundary.

2. **Read the right reference**
   - Read `references/task-model.md` for canonical field meanings, the importance scale, and anti-inflation rules.
   - Read `references/backlog-hygiene.md` for active-task-cap rules, carry-forward hygiene, and backlog defaults.
   - Read `references/migration.md` before renaming fields or changing task-related runtime surfaces, policies, or structured trackers.
   - Read overlapping legacy notes only when needed for migration scope or cleanup — not as a competing second source of truth.

3. **Use the note-system operation layer for persistence**
   - Use the system's note/persistence layer for note updates and tracker validation.
   - Use filesystem edits for precise Markdown changes when safer.
   - Persist important task-model decisions to the current day log and the best canonical policy/procedure artifact.

4. **Keep changes coherent**
   - If the schema changes, update all affected layers intentionally:
     - task notes
     - runtime surfaces
     - structured trackers / filters / formulas
     - relevant skill references
     - any dashboards or operational notes that consume the task model
   - Do not rename a field in only one layer and leave the system semantically split.

5. **Validate after changes**
   - Re-read representative tasks.
   - Re-run task searches / Base queries.
   - Confirm that new or renamed fields are consistent and queryable.

## Guardrails

- Do not treat `importance` as urgency.
- Do not let too many tasks sit in the top importance band; recalibrate aggressively.
- Do not keep weak tasks active just because they are mildly worthwhile; use `[[Someday]]`, `review_on`, delegation, or drop.
- Do not treat `due` / `review_on` hitting today as advisory metadata that can be silently skipped during morning review.
- Do not let overdue or stale `review_on` items disappear just because the exact date has passed; daily planning must surface and route the debt.
- Do not store the same concept twice unless there is a clear reason.
- Do not perform schema migrations without also checking downstream views and policy docs.

## Reference map

- `references/task-model.md` — canonical semantics, importance scale, Eisenhower interpretation, and anti-inflation rules.
- `references/backlog-hygiene.md` — active-task-cap rules, carry-forward hygiene, and backlog defaults.
- `references/migration.md` — workflow for renaming task properties and updating dependent artifacts safely.

## Defaults and owner settings

The schedules, habit examples, durations, planning horizons, capacity limits, and escalation thresholds in this package are general defaults. Explicit owner settings and current approved commitments override them. Do not treat these defaults as evidence about an owner’s actual habits, biography, projects, or preferences. Owner-specific preferences belong in the designated owner skill; current facts belong in approved memory.
