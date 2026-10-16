# Codex remote Voice sidecar

For voice that operates directly in a Syncthing vault without Hermes, use the
[new vault deployment](../vault/README.md). This page describes the older
Hermes-connected mode.

This is the source capture of the working Linux Voice sidecar and narrow Hermes
Runs proxy. It attaches to an **existing, running owner Hermes container** whose
Runs API listens on `127.0.0.1:8642` inside that container. It does not install
Hermes, enable its Runs API, provision accounts, or mount the owner's vault.
The proxy listens on `127.0.0.1:8765` in that same network namespace. There are
no published host ports and no Docker socket or Hermes filesystem mount.

## Source and runtime boundaries

- `Dockerfile`, `entrypoint.sh`, and `proxy.py` capture the deployed implementation.
  The proxy and entrypoint are unchanged. The image no longer bakes a redundant
  `exoctl` copy: Compose already mounts the canonical script at runtime.
- `compose.yaml` replaces the deployed owner/container names and relative private
  paths with required deployment selectors. These environment variables are
  Compose boundary inputs, not a second owner-profile configuration system.
- `config.toml.example` records the dedicated sidecar's approval/sandbox policy.
  Canonical identity and realtime prompt text comes from the parent directory.
- `.dockerignore` admits only the Dockerfile and entrypoint into the build context.
  Credentials, state, and workspaces must live outside the repository.

The captured image seeds **Codex 0.153.1**. The observed running deployment used
**0.153.4** from persistent state. The entrypoint only seeds a home that lacks an
executable `packages/standalone/current/codex`; an image rebuild does not upgrade
or downgrade an existing home. The installer is SHA-256 checked and fetched from
a mutable URL: a changed installer must fail the build until separately reviewed.
Base image tags and Debian packages are not digest/snapshot pinned; this is a
recreation recipe, not a bit-for-bit reproducible image.

The proxy is unauthenticated to callers in the shared network namespace. It
injects the Hermes credential and restricts routes, but any process able to reach
that loopback listener can invoke the allowed run lifecycle endpoints. This is
not per-agent authorization. Maintain the existing owner/approval boundary in
Hermes. Do not publish the proxy or attach untrusted containers to its namespace.
The captured proxy drops query strings and is not a general HTTP/WebDAV proxy.

## Prepare a fresh private runtime

Run on the Linux Docker host from the repository root, with Docker Compose v2,
Python 3.11+, and `uv` installed. Choose private values for these required inputs:

```bash
export VOICE_INSTANCE=owner-voice
export HERMES_CONTAINER=existing-owner-hermes-container
export VOICE_RUNTIME_ROOT=/srv/voice/owner-voice
```

`VOICE_RUNTIME_ROOT` must be an absolute path outside this checkout. Use a unique
runtime root, instance name, and Compose project for each owner. The Hermes
container must already exist; Compose cannot create that external dependency.
Do not use this fresh-runtime procedure on existing sessions.

```bash
set -eu
test ! -e "$VOICE_RUNTIME_ROOT"
sudo install -d -m 0711 "$VOICE_RUNTIME_ROOT"
sudo install -d -m 0700 -o 10001 -g 10001 \
  "$VOICE_RUNTIME_ROOT/state" "$VOICE_RUNTIME_ROOT/workspace"
sudo install -d -m 0700 -o 10002 -g 10002 "$VOICE_RUNTIME_ROOT/secrets"
sudo install -d -m 0700 -o 10001 -g 10001 \
  "$VOICE_RUNTIME_ROOT/workspace/bin" "$VOICE_RUNTIME_ROOT/workspace/server-prompts"
sudo install -m 0755 -o 10001 -g 10001 scripts/exoctl.py \
  "$VOICE_RUNTIME_ROOT/workspace/bin/exoctl"
sudo install -m 0600 -o 10001 -g 10001 deploy/voice/AGENTS.md \
  "$VOICE_RUNTIME_ROOT/state/AGENTS.md"
sudo install -m 0600 -o 10001 -g 10001 deploy/voice/WORKSPACE-AGENTS.md \
  "$VOICE_RUNTIME_ROOT/workspace/AGENTS.md"
sudo install -m 0600 -o 10001 -g 10001 deploy/voice/PERSISTENT-INSTRUCTIONS.md \
  "$VOICE_RUNTIME_ROOT/workspace/server-prompts/PERSISTENT-INSTRUCTIONS.md"
```

Run the shell block with `set -eu` so a failed prerequisite stops preparation.
Render the two server prompt strings into a private config, without printing it:

```bash
uv run python - "$VOICE_RUNTIME_ROOT" <<'PY'
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import tomllib

source = Path('deploy/voice')
text = ''.join(
    f'{key} = {json.dumps((source / name).read_text(), ensure_ascii=False)}\n'
    for key, name in (
        ('developer_instructions', 'IDENTITY.md'),
        ('experimental_realtime_ws_backend_prompt', 'REALTIME-PROMPT.md'),
    )
) + (source / 'sidecar/config.toml.example').read_text()
tomllib.loads(text)
with tempfile.TemporaryDirectory() as directory:
    config = Path(directory) / 'config.toml'
    config.write_text(text)
    config.chmod(0o600)
    subprocess.run(['sudo', 'install', '-m', '0600', '-o', '10001', '-g', '10001',
                    str(config), str(Path(sys.argv[1]) / 'state/config.toml')], check=True)
PY
```

Materialize the existing owner Hermes Runs API credential as
`$VOICE_RUNTIME_ROOT/secrets/hermes-api-key`, owned by `10002:10002`, mode `0400`.
Use the approved secret store/materialization procedure; do not print the value,
pass it in command arguments, or commit it. The proxy reads this through
`HERMES_API_KEY_FILE=/run/secrets/hermes-api-key`. A missing/empty key is a startup
failure. This recipe does not guess a Phase app, environment, path, or secret name.
Only the proxy mounts this credential. Codex authentication lives separately in
private `state`; restore an approved existing home or perform interactive login.

## Build, authenticate, and start

Use the same project and variables for every command below:

```bash
docker compose -p "$VOICE_INSTANCE" -f deploy/voice/sidecar/compose.yaml config --quiet
docker compose -p "$VOICE_INSTANCE" -f deploy/voice/sidecar/compose.yaml build
```

For a new account/home, seed its standalone installation and log in interactively
before starting the daemon (the one-off container uses the same private mounts):

```bash
docker compose -p "$VOICE_INSTANCE" -f deploy/voice/sidecar/compose.yaml run --rm \
  --no-deps --entrypoint /bin/bash codex-remote-voice -c \
  'if [[ ! -x "$HOME/.codex/packages/standalone/current/codex" ]]; then cp -a /opt/codex-seed/. "$HOME/.codex/"; fi; exec codex login --device-auth'
docker compose -p "$VOICE_INSTANCE" -f deploy/voice/sidecar/compose.yaml up -d
```

Complete the login on the owner's device; account availability and remote-control
access are external prerequisites. Never copy login links, auth files, or tokens
into repository evidence. The entrypoint runs
`codex app-server daemon bootstrap --remote-control` and monitors daemon liveness.
A stopped daemon exits the container and Compose's restart policy retries it.

## Verify

```bash
docker compose -p "$VOICE_INSTANCE" -f deploy/voice/sidecar/compose.yaml ps
docker compose -p "$VOICE_INSTANCE" -f deploy/voice/sidecar/compose.yaml exec \
  codex-remote-voice codex login status
docker compose -p "$VOICE_INSTANCE" -f deploy/voice/sidecar/compose.yaml exec \
  codex-remote-voice codex app-server daemon version
docker compose -p "$VOICE_INSTANCE" -f deploy/voice/sidecar/compose.yaml exec \
  codex-remote-voice python3 -c \
  'import urllib.request; r=urllib.request.urlopen("http://127.0.0.1:8765/health", timeout=10); print("Runs health HTTP", r.status)'
```

Inspect only bounded/redacted failures; logs and health bodies can contain
private material. Verify canonical/deployed `exoctl` and prompt hashes, then use
[server prompt verification](../../../docs/voice-server-prompts.md) and
[native integration acceptance](../../../docs/voice-native-integration.md).
Check a fresh phone conversation's identity, follow-up continuity, real progress,
stop/recovery, and actual turn permissions. A healthy daemon does not prove voice
audio, account access, phone permission defaults, or effective realtime prompts.
These remain operator acceptance steps, not automated claims from a source commit.

## Existing deployment, updates, and rollback

Keep the live service running while reviewing these sources. Before adopting
this Compose file, record its current Compose project/service/container names,
image ID, daemon version, ownership, and mounts in private operator records.
Schedule a stop of only the Voice sidecar and proxy, then take a consistent private
backup of their existing Compose/build files and **entire** `state`, `workspace`,
and `secrets` trees. The Hermes service and its sessions remain independent.

Point the selectors at the existing private runtime and Hermes container. Stop
and remove the old sidecar/proxy containers before creating renamed replacements;
do not run two sidecars against the same home or two proxies on port 8765.
Never use the fresh preparation block to overwrite an existing config or state.
Update `exoctl`, persistent instructions, and backing/realtime prompts as a
compatible set; apply existing-home config updates with the expectedVersion/native
API procedure in `voice-server-prompts.md`. Preserve user settings and ownership.

To roll back, stop the replacement containers and restore the recorded image,
Compose definition, and matching code/prompts/config. Preserve new authentication,
conversations, submission intents, and delivery receipts created since the backup.
Do not blindly restore an old state tree and replay a completed external action.
Keep the old image until fresh-phone acceptance succeeds. Recreating the Hermes
container also requires recreating the sidecar/proxy to join its new network
namespace; a name alone does not reattach an already running container.

## Validation scope

Repository regression commands are in
[the regression suite](../../../spec/domains/repository-regression-suite.md).
Compose syntax can be validated without a Docker daemon using non-secret fixture
selectors. Python compilation and Bash syntax checks validate the captured source.
The live `exoctl` hash matched the repository when captured. No production restart,
new login, phone call, or controlled state-restoration test is implied by those
checks. The source capture does not implement a general deployment controller.

Capture validation (2026-09-06): all documented repository regression commands
passed, including 112 unit tests. Compose accepted fixture selectors and rejected
missing selectors. Prompt TOML round-tripped without changing canonical text;
Bash syntax, Python compilation, staged credential-pattern checks, and private
path exclusions passed. An uncached Linux amd64 Docker build verified the installer
checksum and installed Codex 0.153.1; an isolated no-network container reported
that version. The existing Voice container remained running. No authenticated
fresh-runtime or phone acceptance test was performed.
