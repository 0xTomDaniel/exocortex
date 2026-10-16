# Execution Tactics

> Use these tactics when the day mode is already clear but the main risk is fragmentation, admin drag, or a weak launch into the real work lane.

## Design principles
- Prefer named, bounded tactics over vague "catch up on stuff" blocks.
- Use tactics to protect the main lane, not replace it.
- Provide one strong default plus an escape hatch; avoid equal-weight menus.
- If a tactic breaks, degrade gracefully and re-enter cleanly rather than treating the whole day as invalid.

## Admin Strike

### Purpose
Contain real admin residue so it does not sprawl across the day or poison a deep-work block.

### When to use
- 1-3 real admin items are creating drag or background tension.
- The items are small enough to clear or route quickly.
- You want to protect a main work lane, not avoid it.
- A small bounded admin task with `due` today or `review_on` today has surfaced and should be cleared or deliberately routed rather than left as background drag.
- Common placements: before the first main block, at a checkpoint, or on a lighter day with one intentional work lane.

### Default shape
1. Pick 1-3 concrete items.
2. Timebox 5-20 minutes.
3. Clear or route each item.
4. Stop as soon as the list is done or the timebox ends.
5. Re-enter the main lane immediately.

### Variants
- **Micro strike:** 1 item, 2-5 minutes.
- **Standard strike:** 2-3 items, 10-20 minutes.
- **Compressed strike:** up to 30 minutes only when the residue is unusually consequential and still clearly bounded.

### Guardrails
- A 5–20 minute Admin Strike assumes the next action and classification are already clear. Financial/accounting reconciliation, ambiguous records, research, or a decision tree is not automatically a micro-strike just because the final click is small.
- If hidden ambiguity appears, stop at the original 20-minute boundary (30 minutes maximum for a compressed strike), explicitly reclassify the work, and choose: finish because consequences justify it, or park it with the exact unresolved question and re-entry point. Do not let “Admin Strike” become a misleading label for an unbounded mini-project.
- Treat the original duration as a forecast, but own meaningful estimation misses and the opportunity cost they impose on the main lane.
- Do not turn it into inbox wandering.
- Do not keep extending the block because more admin appears.
- Do not use it when the items can simply be deferred into capture/review without creating real drag.
- Do not bury an open admin task with `due` today or `review_on` today without explicitly placing it or re-routing it.
- If the list keeps growing, stop and hand off the rest to `planning-capture-os` or the next review surface.

### Outputs
- The items are done, replied to, delegated, or routed.
- Any follow-up that must resurface later is captured explicitly.
- The main work lane is cleaner, not replaced.

## Single intentional work lane

### Purpose
Prevent a messy day or lighter day from fragmenting into multiple half-starts.

### When to use
- Saturday or another lighter day with some real work pressure.
- A day with many open loops but one work lane clearly matters most.
- A day vulnerable to context switching or reactive drift.

### Default shape
1. Name the single work lane explicitly.
2. Protect that lane after foundations and any bounded admin tactic.
3. Treat other work as defer/routing material unless it becomes truly hot.

### Guardrails
- This is a day-shaping choice, not an iron law; adapt if reality materially changes.
- Relationship, health, and core-habit anchors can still outrank the work lane.
- Do not silently let secondary work lanes creep in without naming the change.

## Bounded tail completion

### Purpose
Avoid unnecessary context-switching and unfinished-loop costs when a finite consumption/activity tail is genuinely short, while preventing “just finish this” from becoming drift.

### When to use
- An intentional video, article, meal-adjacent activity, or similar item has roughly 10 minutes or less remaining.
- Finishing does not violate a hard stop, appointment, safety constraint, or non-negotiable anchor.
- The item ends cleanly rather than feeding an algorithmic queue.

### Default shape
1. Verify the actual remaining time at the intended playback/reading pace.
2. Finish the bounded tail, capped at 10 minutes by default.
3. No autoplay, comments, recommendations, related-item browsing, or second item.
4. Close the consumption surface completely.
5. Use a 30–60 second transition: stand up, water/bathroom if needed, state the next action, and begin it.

### Escape hatch
If more than about 10 minutes remains, the item is expanding, or a hard commitment is close, stop at a clean boundary and capture the exact timestamp/next section. Resume in the appropriate watch/read/study context rather than keeping it ambient.

### Guardrails
- Do not call an algorithmic rabbit hole “avoiding fragmentation.”
- Do not finish optional media through a scheduled Admin Strike, deep-work start, movement anchor, sleep boundary, or appointment.
- Meal-time educational viewing is normally consumption, not completed study; if the material matters, capture one takeaway or schedule active recall later rather than pretending passive viewing created mastery.

## Release contract + enabler checkpoint

### Purpose
Convert hard technical work into externally observable delivery instead of allowing individually reasonable enablers to accumulate as serial prerequisites.

### When to use
- A product/release/customer-evidence outcome is the active MIT.
- Tooling, architecture, research, infrastructure, or newly discovered product complexity is entering the critical path.
- The same ship/evidence gate has slipped once already or enabling work is expanding.

### Release contract
Before execution, state:
1. **Externally observable finish line** — what a user/customer/stakeholder can see, use, test, or respond to.
2. **Current release stage** — mock/manual service, shadow/internal, approval-gated, limited cohort, or broader production.
3. **Explicit non-goals** — important work that is not required for this stage.
4. **Fallback/bypass path** — how to preserve the external learning loop if the preferred enabler fails.
5. **Active enabler** — at most one manually intensive enabler on the critical path.
6. **Expansion criteria** — evidence required before adding sophistication or widening rollout.

### One-working-day enabler checkpoint
If the owner spends one full working day of manual effort on an enabler without moving the release/evidence gate:
1. Stop before silently beginning another day.
2. Name what changed and whether the enabler is still truly blocking.
3. Choose explicitly: continue deliberately, bypass, reduce, delegate/parallelize, or park.
4. Record the displaced commitment and updated finish line.

The checkpoint is a decision gate, not an automatic abandonment rule. Safety-critical or financially consequential work may justify continuation, but continuation must be explicit.

### Repeated-miss escalation
If the same key outcome misses two consecutive weekly gates or one sprint gate, do not carry it forward unchanged. Force one decision:
- contract the release
- bypass/remove an enabler
- change the goal
- add capacity/remove another lane
- explicitly defer or stop

### Guardrails
- Do not label enabling progress as shipped outcome progress.
- Do not dismiss legitimate product discovery; translate it into defaults, configuration, staged safeguards, or explicit non-goals.
- Do not require a finished product for every external test; use mockups, specs, manual service, or structured interviews where valid.
- Do not let parallel agentic/tooling work consume the owner's attention merely because it can continue autonomously; measure it by whether it advances the release contract.

## Final rule
These tactics are defaults, not brittle laws. When reality breaks them, choose the smallest explicit degradation path and re-enter cleanly.
