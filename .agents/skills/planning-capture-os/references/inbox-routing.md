---
aliases:
  - Inbox Processing and Routing Policy
---
# Inbox Routing

> This file is the canonical operational reference for inbox processing and routing.

## Purpose
Keep capture friction low without polluting the task system, and route incoming items into durable homes that match what they fundamentally are.

## Core rule
The temporary inbox is for capture, not storage. Clarify each item by its nature, then route it to the right durable home.

## Temporary inbox
- In live conversations, the chat itself may serve as the temporary inbox.
- The user should be able to dump raw items quickly without pre-organizing them.
- The agent should organize on the fly and ask only the minimum clarifying questions needed to route an item correctly.

## Clarify by nature
For each captured item, first ask what it fundamentally is:
- `action` — requires doing, deciding, replying, following up, or tracking
- `read` — worthwhile finite consumption, but not deep deliberate study
- `study` — deeper learning tied to a topic, skill, or intended understanding
- `watch` — media worth intentionally watching later
- `reference` — worth keeping for future reuse, but not something to act on or consume now
  - If the user already consumed the item and only wants the takeaway/source preserved, classify it as `reference`, not `read` or `study`.
- `discard` — not worth keeping

## Routing rules
### `action`
- Route to an existing or new task/project note.
- Create a standalone task only when there is a real commitment or next action.
- If the item implies multiple steps, route it into the relevant project/task structure.

### `read`
- Route to [[Planning/Queues/Reading Queue]].
- Keep this queue finite and easy to choose from during low-energy or idle gaps.

### `study`
- Route to [[Planning/Queues/Study Queue]].
- Keep this queue for deliberate learning with an intended application or question.

### `watch`
- Route to [[Planning/Queues/Watchlist]].
- Save the title itself rather than noisy search-result pages when possible.

### `reference`
- Save only if the item deserves a durable home.
- Put it in the most relevant scoped project/topic note when one clearly exists.
- Otherwise create a dedicated standalone resource note when worth remembering.

### `discard`
- Close it and move on.
- Do not preserve low-value items just because they were open.

## Anti-patterns
- Do not create one task per tab by default.
- Do not keep one giant permanent master list of mixed actions, articles, study items, and references.
- Do not assume inbox items belong in queues by default.
- Do not treat saved reading as equivalent to committed work.

## Queue design principles
- Reading/study/watch queues should be finite.
- The daily consumption surface should be short and easy to choose from.
- Match the queue to energy:
  - lighter reading for tired gaps
  - deeper study for intentional focus blocks
  - watchlist for intentional leisure

## Browser-tab application
- Browser tabs are raw inbox material, not a durable storage layer.
- Process tab dumps through `action` / `read` / `study` / `watch` / `reference` / `discard`.
- Only the kept items should survive, and only in the appropriate durable homes.
