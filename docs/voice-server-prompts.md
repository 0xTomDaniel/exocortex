# Server-side Exo identity

## Scope and canonical sources

The disposable Voice sidecar presents one Exo identity across realtime speech and native Codex backing execution. This is not a model-identity claim, a new authority boundary, or a working vault bridge. The initial identity-only deployment described here preceded the native-default promotion; current transport and acceptance scope are in `voice-native-integration.md`.

- `deploy/voice/IDENTITY.md`: server `developer_instructions` value for backing execution.
- `deploy/voice/REALTIME-PROMPT.md`: complete server `experimental_realtime_ws_backend_prompt` value for realtime Voice.
- `deploy/voice/AGENTS.md`: dedicated host routing and continuity instructions.
- `deploy/voice/WORKSPACE-AGENTS.md`: workspace routing instructions; avoids a stale special-invocation requirement contradicting the host policy.

Normal work routes to persistent Exo without “ask Exo” keywords. Outward speech uses first person, not “Hermes says” or a handoff announcement. Actual component/model distinctions remain available when asked. Existing delivery, real action approvals, uncertainty and canonical-memory limitations remain binding.

## Realtime prompt provenance and replacement semantics

The realtime prompt is adapted from the shipped Codex `prompts/templates/realtime/backend_prompt.md` at rust-v0.153.2 / rust-v0.153.4 (the two inspected files match), preserving the native [USER]/[BACKEND] message convention, completion notification, delegation, steering, user preference persistence, and concise conversational operation. It replaces the Codex persona, removes blanket claims that internal architecture must never be disclosed, and adds grounded Exo presentation and memory limits.

The phone client's exact session prompt was not retrievable from the inspected rollout: it records realtime session-start identity, not that prompt text. Thus this is a deliberate server-owned replacement based on the shipped template, NOT a verbatim preservation of an inspected phone prompt. Test phone behavior after activation; keep rollback available.

Nonempty `experimental_realtime_ws_backend_prompt` takes precedence over the client's realtime prompt. The config value contains the Markdown TEXT, not a path to the file. Editing a copied Markdown file alone does not refresh that TOML string. AGENTS.md alone is not proof realtime Voice received an instruction.

## Deployment and verification procedure

1. Back up user config, host AGENTS.md and workspace AGENTS.md inside the isolated host deployment. Check existing developer/realtime overrides before replacing them.
2. Stage canonical prompt text and update the two config keys with native `config/batchWrite` over the existing local Unix WebSocket control socket. Use the user config layer's expectedVersion to reject concurrent config edits. No public listener, phone-session message injection, restart, or extra credential is required for persisting the defaults.
3. Verify both values with parsed TOML and native `config/read`. Compare unrelated TOML fields before/after. Preserve current approvals, sandbox, model and auth configuration.
4. Install the two AGENTS files in place, preserving host inodes/ownership for bind mounts. Verify canonical/deployed hashes.
5. New threads load new defaults. Do NOT promise existing threads/calls have hot-reloaded. Inspected `refresh_runtime_config` only refreshes selected fields; a config reload notification is not evidence that the realtime prompt or developer instructions changed in an already loaded session.
6. Verify a fresh backing thread identifies as Exo without keywords, then test a fresh phone conversation for identity, unprefixed work, grounded summary, and recovery/steering. Phone-created permissions may still revert independently; inspect turn_context rather than assuming the identity update solved that issue.
7. Separate code regression tests, backing-identity evidence, and actual phone behavior. A successful operator thread is not a realtime audio acceptance result. Before broadening default routing, inventory and test the EXACT default operational path, including progress delivery, cross-turn history loading, platform tool availability and artifact delivery. Passing an isolated alternate probe is not acceptance of that default path. Explicitly disclose remaining integration gaps rather than letting a unified persona imply full capability continuity.

Local WebSocket operator connection: use `ws://localhost/` over `$CODEX_HOME/app-server-control/app-server-control.sock`. Initialize experimentalApi, then send initialized. Python websockets 15.0.1 with compression=None, user_agent_header=None, proxy=None was verified. See the effective-permissions procedure in `voice-batch-delivery.md`; never log auth secrets.

## Historical identity-only acceptance

The initial deployment persisted server defaults via native API on app-server 0.153.2, without a daemon restart or live phone-turn settings change. Canonical/deployed prompt hashes were verified. Keep backup paths, config snapshots, thread/turn IDs and per-deployment hashes in private operator records.

A fresh ephemeral backing thread returned: “Call me Exo. You can ask me to handle a task naturally—no special wording or ‘ask Exo’ prefix is needed.” No tools or persistent-brain run started. Permissions were explicitly never/full-access for this OPERATOR-created test; this did not establish phone-created defaults. Code regression tests do not test model obedience or phone audio.

At that initial identity-only checkpoint, timed/category delivery was still deployed. That statement is historical: native-default delivery subsequently replaced it, as documented in `voice-native-integration.md`.

## Rollback

Restore the three backed-up files to state/config.toml, state/AGENTS.md and workspace/AGENTS.md in the host sidecar directory, preserving inode/ownership. If config changed after this deployment, selectively restore/remove only the two identity prompt keys rather than overwriting later unrelated settings. New sessions are needed to establish rollback of session-static prompts; verify effective config and actual behavior. No credential copies or mount/network expansion are part of either deployment or rollback.

Shared Voice prompt sources are owner-neutral. Identity and available memory
surfaces come from the active profile; preferences come from its installed owner
skill. Missing owner context must not fall back to a named person or assumed
vault. Updating repository prompts alone does not update a live Voice server.
