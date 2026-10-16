---
aliases:
  - Planning Periods Taxonomy
---
# Planning Periods Taxonomy

> This file is the canonical operational reference for planning-period hierarchy and cadence metadata.

## Canonical terms
- [[Year]]
- [[Quarter]]
- [[Cycle]] (6 weeks)
- [[Sprint]] (2 weeks)
- [[Bonus Week]]
- [[Week]]
- [[Day]]

## Planning cadence hierarchy
- [[Cycle]] (6 weeks) is the primary planning cadence.
- [[Sprint]] (2 weeks) is the secondary planning cadence for checkpointing and re-scoping inside the cycle.
- [[Week]] is the main execution/review rhythm for day-to-day commitments.
- [[Quarter]] and [[Year]] are primarily for directional framing, synthesis, and review rather than detailed commitment planning.
- Default rule: do not make detailed promises beyond the current 6-week cycle unless there is a true hard external commitment.

## Cycle planning and sprint decomposition
Before marking a 6-week cycle active/locked:
1. Confirm the cycle thesis and 1–3 outcomes with the user.
2. Decompose the cycle into all three 2-week sprints; do not stop at sprint links or placeholder milestones.
3. For each sprint, define the intended external evidence, success gate, capacity/tradeoff boundary, and end-of-sprint decision (continue, contract, bypass, change goal, add/remove capacity, defer, or stop).
4. Use the sprint sequence as a feasibility test: if the outcomes cannot be sequenced credibly, revise the outcomes rather than preserving an aspirational cycle plan.
5. Keep the cycle and dependent sprint artifacts provisional until the full sequence has been discussed and confirmed.

The cycle defines **what and why**; the sprints define **sequence, evidence, and correction points**. Both are required for a locked plan.

## Nested-period commitment clarity
When a week sits inside a sprint/cycle, make the boundaries explicit rather than presenting every higher-period gate as if it were due this week:
- Label **this week's committed finish lines**, **this week's working/stretch targets**, and **the entire sprint's hard gates/deadlines** separately.
- If a weekly target is earlier than the sprint deadline, state that it creates recovery/integration buffer; do not silently redefine the hard deadline.
- Give each sprint outcome a concrete weekly checkpoint or deliverable, but do not overload one week with the entire sprint scope.
- Keep internal enabler/evaluation labels subordinate to the user-facing outcome. Never make the user remember or execute an agent-invented acceptance gate (for example “issue 3”) when real delivery can generate the evidence incidentally.
- When feedback/polish is expected, define the current week's finish line and stop condition so iterative rounds do not become an unbounded substitute for the sprint outcome.

## Property conventions
- Categorical/entity fields use wikilinks.
- Machine dates use ISO values.
- Core **task** property semantics such as `importance`, `status`, `due`, and `review_on` belong to `planning-task-os`.

### Planning hierarchy properties
Use these when relevant:
- `week`
- `sprint`
- `cycle`
- `quarter`
- `period_type`
- `day_of_week`

### Bonus week modeling
- `period_type: [[Bonus Week]]`
- Optional `focus_mode`: [[Reflection]] | [[Catch-up]] | [[Cleanup]] | [[Recovery]] | [[Vacation]]
- Bonus weeks must have concrete `week`, `week_start`, and `week_end` anchors before the preceding cycle/quarter review is considered closed.
- A bonus week is a first-class cadence period, not a vague buffer. It must surface in the weekly review before it begins, the first morning start inside the week, and any next-cycle planning session that might otherwise overwrite it.
- Do not instantiate the next cycle's week plan over a scheduled bonus week unless the user explicitly chooses to sacrifice/defer the bonus week; record that tradeoff in the bonus-week note and in the plan that overrides it.
- Use a future-facing artifact (`review_on`, target week note, or target review note) so upcoming bonus weeks cannot rely on memory or passive quarter-note links.

## Day-level cadence metadata
Day logs / daily artifacts should carry:
- `week`
- `quarter`
- `cycle`
- `sprint`
- `period_type`
- `day_of_week`

For bonus weeks, `cycle` and `sprint` may be intentionally absent; `period_type: [[Bonus Week]]` and the bonus-week link/focus mode are the routing-critical fields.

In note-based systems, these may be generated at note-creation time via templating.
The canonical source should be the corresponding week artifact for that system.
That means weekly rollover should ensure the upcoming week artifact exists before dependent day artifacts are created.

## Friday review / Sunday planning semantics
- Friday's weekly review targets the current ISO week and records an explicit Friday `coverage_end`; it may be substantively complete before the calendar week ends.
- Sunday still belongs to the current ISO week. Sunday's bounded weekend reconciliation extends/corrects the Friday review only when meaningful weekend evidence changes it.
- On Sunday:
  - the current day artifact remains tagged with the current week
  - planning-period boundaries still close on their true Sunday dates
  - unresolved higher-level review decisions/weekend deltas are finalized without replaying the full Friday retrospective
  - the week plan targets the next week starting Monday

More generally: Friday begins the retrospective stack for periods ending Sunday; Sunday finalizes true deltas/decisions and protects next-period planning.

## Naming conventions
- `Weekly Review - YYYY-W##`
- `Sprint Review - YYYY-C#-S#`
- `Cycle Review - YYYY-C#`
- `Quarterly Review - YYYY-Q#`
- `Yearly Review - YYYY`

## Design principle
Cadence metadata should make routing more obvious, not more confusing.
Day artifacts and runtime surfaces should support the real planning semantics rather than silently overriding them.
