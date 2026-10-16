# Native default Voice integration

## Active path

Phone realtime Voice → native Codex backing executor → `exoctl` native-v1 → existing Runs proxy → persistent Exo. This supersedes the timed/category narration described historically in `voice-batch-delivery.md`. It does not replace the proxy or expose credentials, filesystem mounts, SSH, or Docker to Voice.

Canonical sources: `scripts/exoctl.py`, `deploy/voice/AGENTS.md`, `deploy/voice/REALTIME-PROMPT.md`, `deploy/voice/PERSISTENT-INSTRUCTIONS.md`, `scripts/hermes_native_send.py`, `skills/native-messaging/SKILL.md`.

## Native transport contract

- Capture every received SSE response-body byte to `raw.sse` before parsing. Fsync source writes; record response metadata and an EOF/error byte-count/SHA-256 receipt. A capture lock and exclusive source creation prevent a second follower from appending replayed bytes. No automatic reconnect or complete-history guarantee.
- `next-event` queries live status first. Terminal and live approval state preempt the activity backlog. State errors do not consume delivery cursors. Approval drops only complete pre-approval frames, retaining partial frames.
- Top-level `kind` replaces old `event.speak`: `activity`, `waiting`, `final`, `final_part`, `approval`, `waiting_for_approval`, `already_delivered`, `superseded`, and explicit capacity conditions. The old caller contract is retired; fresh Voice/backing instructions are necessary.
- Activity contains unchanged parsed native event payloads with byte references. Internal reasoning, provisional message deltas, and unselected/unknown events stay in the raw archive and have exclusion receipts, not speech. No scripted semantic summary, category narration, timer narration, or heartbeat is generated.
- Send the whole unread visible batch when it fits. Otherwise page at event boundaries. A single oversized event is held without consuming it; report the presentation constraint once and keep checking live status rather than silently truncating or cancelling real work. Terminal preempts the blocked event.
- The 2800-byte presentation gate is conservative, NOT an actual tokenizer guarantee. Never concatenate independently bounded updates into one oversized backing message.
- Archive full terminal state/output in `final.json`. Small results arrive whole. Large reports use UTF-8-safe `final_part` pages with offsets, total bytes, hash and completion marker. These are raw report chunks, not script-written summaries. Voice is instructed to assemble all parts and summarize only on completion. Actual phone assembly of arbitrary large reports is not yet verified.
- Atomically commit cursors and delivery claims under a lock. Honor old journal/integer cursor terminal claims; never replay old canned progress. A confirmed cancellation is claimed to avoid an automatic duplicate cancellation result. Late SSE cannot repeat a status-derived final.
- At-most-once CLI output is not proof of heard audio. Explicit user-requested `result RUN_ID --offset N` returns bounded recovery without resetting the normal cursor. Queued/playing audio is not mechanically cancelled. Exact quotations and playback acknowledgement remain separate acceptance gaps.

## Conversation continuity

`start` supplies explicit `session_id` in the request body. Existing default conversations migrate using the previous run's actual session_id; new conversations get an explicit ID before POST. This addresses inspected upstream ordering: conversation history loading happens before header-only session-key resolution.

Persist an immutable local intent before POST, including the request body and idempotency key. Reuse it on ambiguous retries; reject changed input under the same key. Same-key replay does not resubmit accepted work or move the latest conversation pointer backward. Per-conversation locks guard local starts. An active/uncertain prior turn blocks new work: recover, steer or stop rather than forking away from required context. `latest` exposes pending submissions. This is not a proof of exactly-once external side effects.

Native per-run instructions identify the persistent system as Exo, preserve follow-up context, distinguish session history from the unfinished Obsidian bridge, and expose the native sending workflow.

### Preserve the intended executor

An observed backing rewrite changed an instruction to ask an existing worker into a direct investigation request. Persistent Exo consequently used project/API/service tools instead of prompting that worker. This was an actor-preservation failure, not a lifecycle-wait or presentation-ownership defect.

Backing instructions now preserve the intended executor, action, scope and attribution, preferring original user wording and resolving pronouns only from established context. Per-run persistent instructions and the Herdr skill independently require coordination of the assigned worker rather than silent takeover. Passive status inspection is distinct from a request that the worker investigate or answer. A diagnostic question does not authorize repairs, goal restart or approval bypass. Blocked/unavailable workers require explicit takeover authorization, not an automatic substitute investigation.

A fresh backing no-send routing check preserved the original agent-directed utterance without invoking tools. This is limited model-routing evidence, not an end-to-end worker delivery test or proof that all response latency is fixed. A live replay was intentionally deferred after a newer user request had already resumed the worker and supplied guidance; do not duplicate or override newer work for acceptance testing. Backing instruction changes require a fresh conversation; updated per-run instructions are read on new submissions, not retroactively applied to existing immutable intents.

## Accepted report workflow

The accepted normal workflow keeps the full report with persistent Exo and returns concise answers through Voice. A live exercise verified persistent report creation/save, file-backed follow-up retrieval, and user-confirmed spoken responses. The backing executor relayed those responses rather than independently writing the report. Both responses fit single final envelopes: this did NOT exercise full-report paging. Whole-report Voice assembly and exact quotations remain unverified capabilities, but are not blockers for this accepted summary/retrieval workflow. Reopen paging acceptance only for a concrete whole-document delivery requirement.

## Existing native Telegram sender

Hermes intentionally does not register `send_message` as a model tool in the inspected version. Official `hermes send` retains the existing transport. A missing model tool is not proof that messaging is disconnected.

The live test found a second boundary: terminal tool environments omit the gateway's Telegram variables. The first unqualified native send failed definitively as unconfigured; the subsequent properly initialized CLI succeeded. Do not repeat that discovery or ask the model to construct token-reading shell commands each time.

The profile-private `$HERMES_HOME/bin/hermes-native-send` launcher now loads the existing token-file reference and configured home target into a CHILD environment, then execs official `hermes send`. It performs no sending itself, copies no token to config, makes no new bot/account, and has no retry loop. `native-messaging.json` contains the native executable path, existing token-file path, and existing configured home channel, generated from the actual gateway environment. It is owned by the runtime service UID with mode 0600; no private values belong in Git.

The launcher is agent-readable/editable, not an authorization or hostile-agent security boundary. Existing runtime/provider/isolation controls remain unchanged. The skill requires user-authorized recipient/content, actual artifact verification, no blind retry on ambiguous delivery, and success receipts. `--file` is text-body input; attachments use `MEDIA:/path` in the message. A MEDIA marker returned through the Runs API is not proof the phone rendered an image.

## Deployment and acceptance

Before default migration, privately back up the CLI, config, host/workspace instructions and CLI state. Keep deployment-specific paths, run/thread/session IDs, messaging receipts and raw archive hashes in operator records, not Git. Update individual bind-mounted files in place to preserve inodes. Verify effective server config and canonical/deployed hashes. The initial migration required no daemon restart or permission expansion.

Tests:

```sh
python3 -m unittest discover -s tests -p 'test_exo*py'
python3 -m unittest discover -s tests -p 'test_hermes_native_send.py'
```

46 adapter/probe tests plus 2 native-send environment tests pass, including the subsequent ownership changes. These test transport/state preservation and credential-file loading, not model obedience or audible playback. The native-messaging and Herdr skills validate/package successfully.

Live evidence:

- A synthetic brief was generated after a harmless terminal command. A subsequent run recalled its exact marker from prior conversation with no tools, sharing the same explicit session.
- A default-path run migrated the existing conversation, resolved the previously requested image, loaded the native-messaging skill, and invoked official Hermes send. The actual tool receipt recorded success, an assigned Telegram message ID, mirroring, and exit code zero. There was one definitive failed send attempt before the successful environment-initialized attempt; no ambiguous retry or second success was found. This proves accepted delivery, not that the recipient opened it.
- SSE EOF byte/hash receipts were verified for the send and synthetic conversation tests. Full private acceptance records remain in operator memory.
- After adding the stable environment launcher, native target discovery worked under `env -i` as runtime UID10000 using only HOME/HERMES_HOME/PATH. It resolved the existing owner DM. The image was NOT resent to test the loader; the successful send preceded this launcher installation.
- Cancellation regression: observed native activity, confirmed cancelled in 0.582 seconds, subsequent recovery returned already_delivered. This measures CLI/provider cancellation confirmation, not a new independent process-tree audit.

## Consumer ownership — implemented after phone validation

The initial native-v1 deployment guarded duplicate raw capture and final claims but did NOT transfer exclusive presentation ownership. The phone recovery test exposed two backing consumers, with the old one claiming the final first. This was an incomplete integration, not a regression of a previously implemented retirement mechanism.

Evidence scope: the user's actual recovery succeeded, with one durable execution and no demonstrated lost answer. The observed defect was overlapping backing/tool work and a final-delivery race requiring explicit recovery in the new thread. It was NOT established as the cause of stale/repeated speech. Classify this change as evidence-backed handoff/resource hardening, not proof that the original audible symptom is fixed. Before prioritizing another change, state the observed behavior, user impact, causal evidence, and whether it is a required repair versus hardening; a successful fix test does not retroactively prove symptom causality.

The updated CLI derives consumer identity from runtime-injected CODEX_THREAD_ID (verified in a real backing command). Operator fixtures outside Codex may use EXOCTL_CONSUMER_ID. `start` attaches the creator; `latest` from a Codex thread takes presentation ownership for recovery; `latest --observe` and `status` are read-only. Explicit `attach RUN_ID` takes over without starting another job.

Ownership epoch, retired consumer IDs, delivery cursors and claims are stored atomically in delivery.json under cursor.lock. Every consuming poll checks ownership BEFORE calling the Runs API or advancing a cursor. Stale consumers receive superseded and cannot automatically reattach. Result recovery and stop/steer/approval commands are fenced too; control requests hold the ownership lock across their POST. New owners re-see pending approvals and restart incomplete report assembly at page one, but do not reset already-delivered final claims. Explicit lost-answer recovery remains available to the new owner.

The backing instruction on superseded is to end immediately, silently, with no further calls, reacquisition, job restart or cancellation. This fences adapter access; actual model retirement was verified separately. A retired thread cannot automatically take that same run back; use a fresh conversation for a deliberate return. Untagged CLI callers cannot consume an owned run; operator inspection should use status/latest --observe. Legacy unowned runs remain readable, and first identified polling establishes an owner for migration.

This is cooperative workflow fencing, NOT a security boundary against an agent that can edit local code/state or forge its environment. It does not expire automatically when a call closes: a NEW consumer attaching triggers retirement. Commands/results already linearized before takeover may still be in flight. Ownership does not cancel the durable job, eliminate the one remaining active poller, retract queued speech, or provide playback acknowledgements.

Live ownership acceptance executed one sleep 60 (60.165s). Real backing thread A owned epoch 1; real backing thread B took epoch 2. A received superseded and completed with OLD_POLLER_RETIRED 2.34s after takeover WHILE the persistent job was still running. B continued and received OWNERSHIP_JOB_COMPLETE for the same job. Exactly one normal final delivery was logged. This was an actual two-backing-thread test, not phone audio acceptance; private identifiers and receipts remain in operator records.

The installed stale-consumer check still returned superseded after deployment. Server config/API and canonical/deployed hashes were verified. A concurrent sidecar restart advanced the observed app-server from 0.153.2 to 0.153.4; this implementation issued no restart command and the cause is unverified. Temporary operator WebSocket dependencies needed restaging after /tmp cleared. Durable source/state/config survived and were rechecked; this observation is not a controlled recreation acceptance test or evidence that ownership caused the restart.

## Rollback and remaining acceptance

Restore matching CLI + backing instructions + realtime prompt config together; old and native-v1 caller protocols differ. Preserve live acceptance intents and delivery receipts. Do NOT blindly restore pre-send CLI state or erase knowledge of an already completed Telegram send. New sessions are needed to load session-static instructions. The new native-send launcher/config/skill can be removed independently if required; do not remove the existing bot, mounted secret or gateway configuration.

Phone evidence covers useful summaries, file-backed follow-up retrieval, stop and core recovery. Recheck ownership transfer in phone use and stale-speech ordering before expanding those claims. Do not call exact speech, deterministic preemption, large-report assembly, or universal new-phone-thread permission defaults fixed without direct evidence. Missing-page recovery is deferred with the whole-report delivery requirement, not a blocker for the accepted workflow. Existing sessions may retain old prompts. Canonical Obsidian integration, recreation automation and stronger hostile-worker isolation remain separate work; committing sources does not complete deployment automation.

## Captured sidecar deployment source

The previously host-only Dockerfile, entrypoint, and Runs proxy are now owned by
[`deploy/voice/sidecar`](../deploy/voice/sidecar/README.md), with an owner-neutral
Compose template and a fresh-runtime/rebuild/rollback runbook. This captures the
service recipe; it does not deploy that template onto the existing service or
complete account provisioning, automated restoration, or fresh-phone acceptance.
The historical recreation-automation gap above remains distinct from source capture.
