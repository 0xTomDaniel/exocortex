# Voice batch delivery

Canonical patch sources: `scripts/exoctl.py`, `deploy/voice/AGENTS.md`.
Tests: `python3 -m unittest discover -s tests -p test_exoctl.py -v`.

> [!important] The native-v1 default path now supersedes the timed-category contract below. Current protocol, continuity and sending behavior: `voice-native-integration.md`. Existing permission/instruction-layer guidance later in this document still applies. A new Voice/backing session must load the updated protocol instructions.

## Historical contract — retired timed-category implementation

`next-event` retains its existing command name and single `event` response for compatibility, but consumes the whole unread journal snapshot under the cursor lock. It checks current Runs API status first. Final/failed/cancelled/interrupted state takes precedence, followed by current approval; obsolete approval events are not spoken. Status failures do not consume the cursor or narrate stale progress.

Tool lifecycle events remain in the journal and accumulate across drained batches into one recent-activity summary at most every 12 seconds. Known tool names map to literal activity categories (file reads, terminal commands, session-history searches); no command arguments or unsupported task conclusions enter speech. Delegation/steering counts join the same summary. Quiet active runs get a truthful no-new-events heartbeat after 25 seconds. Terminal/approval states bypass throttling. The original silent-tool filter failed live observability for tool-only runs and has been replaced; regression tests must prove intermediate updates before a final, not only successful final delivery. No invented task semantics from generic tool names. Null events mean silence, not completion; `already_delivered` terminates polling. Approval delivery includes the current approval object for informed request-specific authorization; no approval policy was weakened.

`delivery.json` atomically stores cursor plus terminal/approval delivery claims under `cursor.lock`. Existing integer cursors are migrated on first poll. Terminal events arriving late from SSE cannot repeat a status-derived final. Ordinary new-process recovery uses the same state. Legacy results spoken directly from `status` without consuming their final event cannot be retrospectively recognized as delivered.

This is at-most-once CLI delivery, not exactly-once audible speech: a crash/disconnect after committing a delivery claim but before the user hears it can lose audible delivery. Explicit requests to repeat a lost answer may recover `status.output`. There is no audio acknowledgement protocol yet.

## Instruction-layer diagnosis

Distinguish realtime Voice's own session prompt from native backing-executor AGENTS.md/task instructions and from Hermes instructions. Failure to obey delivery metadata or a user request does not establish that an untested realtime system/session prompt cannot fix the behavior. Before ruling out a prompt-level repair, identify which component makes the decision, inspect its effective instruction source and precedence, and test at that layer while preserving unrelated behavior.

Inspected Codex source exposes `experimental_realtime_ws_backend_prompt` as a nonempty string override used by `prepare_realtime_backend_prompt`: it takes precedence over the client's realtime prompt; otherwise the client prompt is used when supplied, falling back to the bundled `prompts/templates/realtime/backend_prompt.md`. This is not an automatically discovered Voice AGENTS.md file. The override replaces rather than appends the client prompt, so inspect/preserve its phone-specific behavior before applying it. The prior streaming/terminal-envelope tests did NOT change this realtime prompt and cannot establish its limits. Even a successful prompt-level verbatim test would not demonstrate deterministic playback cancellation or a playback-finished callback.

## Effective Voice permissions (operator procedure)

Voice-side no-prompt/full-access policy applies only inside the externally constrained sidecar, not Hermes or host-level workers. A successful `codex doctor` or user config inspection is not proof of effective phone-turn permissions. Inspect the actual rollout `turn_context.approval_policy` and `sandbox_policy`; client/thread overrides may replace config defaults.

For an existing idle Voice thread, the native app-server method `thread/settings/update` can set `approvalPolicy: "never"` and `sandboxPolicy: {"type":"dangerFullAccess"}`. Verify the persisted `thread_settings_applied` record and a subsequent actual turn. This updates the specified thread; it does not guarantee future phone-created threads or explicit later client overrides inherit that choice. Do not solve this by automatically accepting approval requests.

Operator access is through the existing local Unix WebSocket control socket, normally `$CODEX_HOME/app-server-control/app-server-control.sock`; it is not newline JSON over stdio. Initialize with clientInfo and experimentalApi, then send `initialized`. A Python websockets 15.0.1 connection succeeded with URI `ws://localhost/`, `compression=None`, `user_agent_header=None`, `proxy=None`; the default options failed, so do not claim which individual option was causal without isolating it. Avoid adding public listeners. `thread/read` alone did not subscribe this operator connection to turn notifications; verify completion through persisted records rather than interpreting an observer timeout as a failed inference.

Check `codex app-server daemon version`: the managed binary and running daemon may differ. Do not restart a working daemon or change requirements just to match a newer binary without an explicit deployment reason. Requirements allowlists are not an automatic force-full-access switch: inspected sandbox requirements mandate permitting read-only, and invalid explicit turn overrides can fail rather than silently normalize.

## Deployment and rollback

Back up the currently deployed CLI and dedicated Voice instructions. The spike binds the CLI as an individual read-only file: preserve its host inode when updating to avoid a stale bind mount, or recreate the sidecar deliberately. Verify hashes from inside the container. Existing backing conversations may retain cached instructions; use a fresh Voice conversation to validate instruction changes. The CLI batching applies on the next invocation without restarting Hermes or workers.

A live regression can seed 100 synthetic journal events in an isolated `EXOCTL_STATE_DIR`, then poll an existing completed run. Assert exact output, one-poll consumption, silence on the next process, and unchanged audit history. Never use production delivery cursors for this fixture.

Scope: batch consumption, current-state priority, evidence-backed narration and delivery deduplication. Interpretation/routing of user questions such as “is it stuck?” remains explicitly deferred.
