---
name: planning-rhythm-os
description: >-
  Daily/weekly planning-rhythm operating system, including day-of-week modes,
  morning-foundation rules, graceful-degradation/re-entry handling,
  resurfacing cadence, Friday-review/Sunday-planning flow, weekly review and
  planning processes, review-stack semantics, and planning-period taxonomy.
  Use when the user is starting the day or week, needs cadence-aware routing
  (weekday vs Saturday vs Sunday), is running or redesigning
  weekly/sprint/cycle review flow, or is changing planning-period semantics,
  Friday/Sunday review-planning surfaces, or day-level cadence metadata.
  Also use for discovering unfinished planning work at greeting/re-entry and
  retaining its place through open conversation; do not start a planning
  workflow merely because the owner wants to talk.
metadata:
  exo.category: general
---
# Planning Rhythm OS

Own day modes, cadence discovery, morning foundations, review flow, and planning-period meanings. Use `planning-task-os` for task state/fields and `planning-capture-os` for capture routing. Personal schedules and current project judgments are memory inputs, not generic weekday rules.

## Route and execute

Before the first substantive planning/review/startup step, read `references/review-progress.md`, discover the scope's existing record, and save its initial or resumed state in the owning note. `init` only prints JSON; it does not save progress. At greeting/re-entry, use that reference's bounded discovery and conversation routing before choosing whether planning is relevant.

The following routes apply when their named workflow is active; they are not a checklist for greetings or open conversation.

1. Read `references/daily-rhythm.md` for morning start, “what next?”, resuming daily rhythm, or closeout. Resolve calendar mode, bonus-week override, missing dates, and the effective-dated habit roster before proposing execution.
2. Read `references/review-cadence.md` for Friday retrospective, Sunday planning, and the full smallest-to-largest review stack. Discover overdue/missed reviews as well as periods ending now; promote genuine debt before treating a current plan as locked.
3. During startup, review or planning, run `references/resurfacing.md` for task debt **and all-class dated reminders**, plus random rediscovery. Report checked surfaces, surfaced items, and uncertainty; a task-only scan cannot establish an all-clear.
4. Use `references/review-progress.md` to persist scope, coverage, evidence, unresolved decisions, confirmation, and the exact resumption step. Run `scripts/review_state.py check <note>` before a completion claim; check the evidence against the user discussion. Confirmation never cascades across day/week/sprint/cycle scopes.
5. Use `references/periods-taxonomy.md` for cadence metadata and bonus-week semantics. Use `references/execution-tactics.md` for bounded admin/deep-work tactics and outcome-versus-enabler decisions.
6. Instantiate only the needed scaffold under `assets/runtime-surfaces/`. It is a display/capture aid, not a completed review or a second procedural authority.

## Operating stance

Preserve raw mind dump before triage or agent synthesis. Protect ritual-critical foundations and meaningful life domains without turning interruptions into an all-or-nothing failure. Use full → reduced explicit → minimum viable → intentional defer with a named re-entry point. Preserve the unfinished step through tangents; resume when the owner returns to the workflow, without forcing exploratory conversation back into planning. Friday owns retrospective/backlog work and Sunday protects next-week planning unless the personal cadence explicitly differs.

Before locking a cycle, work through all sprint checkpoints; before locking a sprint, work through both weeks, external evidence, capacity/displacements, balanced-life anchors, and the end-of-period decision. Placeholder links and first-week agreement do not establish these decisions.

## Verification

Validate changed notes through the persistence layer, confirm real query coverage, and check review progress before advancing status. Exercise historical failure cases after workflow changes. Do not claim that structural checks or an inline rehearsal prove another model will always follow the procedure.

## Defaults and owner settings

The schedules, habit examples, durations, planning horizons, capacity limits, and escalation thresholds in this package are general defaults. Explicit owner settings and current approved commitments override them. Do not treat these defaults as evidence about an owner’s actual habits, biography, projects, or preferences. Owner-specific preferences belong in the designated owner skill; current facts belong in approved memory.
