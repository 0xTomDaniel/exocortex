# Herdr fabric: bounded review slice

## Surface

`scripts/herdr_fabric.py` sends one JSON line over restricted SSH to
`scripts/herdr_inventory_node.py`. Inventory accepts `agents` or `workspaces`.
The endpoint delegates `review` and `result` to `scripts/herdr_jobs.py`.
`hosts` is a local registry query, not a heartbeat.

A review creates a new Herdr workspace/pane under a fixed source directory and
runs a batch Codex worker there. It does not prompt existing user agents or
expose raw terminal control. Batch workers need not appear as interactive agents
in `agent list`; the pane, worker PID, logs, and receipt are the job evidence.

Requests:

- `{"operation":"review","request_id":"unique-id","prompt":"Review the source"}`
- `{"operation":"result","request_id":"unique-id"}`

ID reuse with identical prompt returns the existing receipt; changed content is
rejected. Per-node admission and per-job runner locks prevent normal duplicate
launch. Atomic fsynced prompt and record files retain state across client loss.
Unknown dispatch is never automatically retried. This is at-most-once launch with
recoverable receipts, not guaranteed successful execution exactly once after all
possible host/filesystem failures. A worker crash may require operator recovery.

One active review per node, 180-second worker timeout, process-group kill on
execution timeout, explicit exit status, structured final output. `completed`
requires process exit zero and a worker report of `review_status=completed`;
`blocked` remains distinct. An LLM's success claim still requires reading its
findings and limitations. The 240-second receipt deadline reports `interrupted`
without re-launching; ambiguous/stale state holds capacity until operator review.
No cancellation or interactive approval API is exposed yet.

## Deployment

Keep node configs, private addresses, keys, job output, and backups outside git.
Install node.py, herdr_jobs.py and result-schema.json together outside Hermes's
filesystem authority. Node config fields:

- `node`, `home`, `binary` (Herdr), optional `config_home`
- `jobs_root` (private owner-only directory), `review_root` (approved source)
- `python`, `codex`, `codex_home`, `model`, `result_schema`
- optional `legacy_landlock` for a verified Linux compatibility need

Authorize a dedicated key with `restrict,command="<python> <node.py> <config>"`.
The endpoint ignores SSH_ORIGINAL_COMMAND. Restrict SSH accounts/networks and
validate sshd configuration before reload. Pin host keys from previously trusted
state or a host's own public-key file. No accept-any-host-key mode.

Install client into `$HERMES_HOME/herdr-fabric/herdr_fabric.py`, with:

- `config.json`: `{"hosts":{"node-id":{"address":"HOST","user":"USER"}}}`
- `known_hosts`: verified host public keys
- `id_ed25519`: dedicated client key, 0600

Own these files/directories by the actual gateway runtime user. Container exec
may default to root while Hermes runs as UID 10000. Test under the runtime UID.
Install `skills/herdr-fabric/SKILL.md` into the profile's discovered skills path.

## Security and compatibility

Forced-command code restricts the calling Hermes key, not the node's own operator
or a compromised node account. Mac pilot code is Mac-operator-owned; Hermes has
no remote edit API. This is not a boundary against the Mac coding agent editing
those files locally. Private job-root validation reduces mistakes; it is not a
full race-proof hostile-same-UID filesystem defense.

Only new review jobs against fixed approved source snapshots are exposed. User
prompts are passed through JSON and stdin, not interpolated into shell commands.
Runner invocation is constructed from operator-configured fixed paths and a
validated ID. Worker environment is allowlisted, excluding forwarded SSH agents,
arbitrary ambient credentials, and all HERDR control-context variables. The
upstream Herdr skill remains staged for future interactive pane agents, not used
by these deliberately context-stripped batch reviewers. Authentication stays in each worker's local
Codex home; it is never copied into Hermes or from Voice into another worker.

Codex runs read-only with approval_policy=never, ignored user config/rules, and
web search disabled. This protects worker shell writes; it is not comprehensive
sensitive-file read isolation or a guarantee about every native tool. Removing
HERDR environment variables is not a denial of same-UID socket authority: a worker
that discovers the socket may still have host-account permissions. Separate worker
UIDs/containers and inaccessible control sockets are required before treating this
as a boundary against malicious reviewers or arbitrary untrusted prompts. Keep tasks
within the approved source scope and assess stronger isolation before sensitive
or consequential work. Existing Herdr service confinement does not automatically
apply to separate SSH sessions; the endpoint restricts SSH independently.

Linux pilot: Bubblewrap 0.12 is incompatible with the current Herdr systemd
hardening (openat2 is blocked by RestrictSUIDSGID; masked proc also blocks nested
proc mounting). The service's original restrictions were restored after diagnosis.
Codex 0.153.4's available but deprecated `use_legacy_landlock` backend passed
source-read/write-denial probes and is enabled only on that node. Re-test or
replace this backend before upgrading Codex; do not bypass sandboxing to fix it.
Mac uses the native Codex read-only sandbox.

Output files/logs currently have no automatic retention quota. Inventory response
size is checked after capture, not a streaming memory cap. Long-term audit,
retention, hard resource quotas, source-snapshot hashes, and supervised recovery
remain productionization work. Addresses can change with DHCP; reconcile with
host-key verification before registry changes.

## Test and rollback

Run `python3 tests/test_herdr_inventory.py` and `python3 tests/test_herdr_jobs.py`.
Verify real calls under Hermes's runtime UID, both node reviews, identical-ID
replay, conflict rejection, invalid fields/operations, no raw SSH command escape,
and worker read-only denial. Do not equate operator docker-exec proof with an
actual Hermes agent invoking the skill; test both.

Revoke by removing this dedicated authorized_keys entry on each node. Remove only
the added sshd drop-in after validation and reload. Restore backed-up endpoint
code/config if needed. Do not delete user sessions, credentials, job receipts or
Herdr state as part of rollback. Completed proof panes remain for inspection.
