# Remote Deploy Template

This directory contains the non-secret remote SSH deployment template for the
Hermes Exo distribution. It is safe to validate in CI or by Octo agents because
the default target is `deploy/remote/mock-target.toml` and the workflow emits a
dry-run plan instead of opening SSH sessions.

Live ESXi deployment evidence is Human Review/HITL through EMB-276 unless a
later issue explicitly grants remote access and the required Phase secrets.

## Dry Run And Mock Validation

Render the deploy plan without live SSH, Phase, Telegram, model, or cloud
credentials:

```bash
uv run python scripts/remote_deploy.py --config deploy/remote/mock-target.toml
```

Include fixture-backed health/status/log failure reporting:

```bash
uv run python scripts/remote_deploy.py --config deploy/remote/mock-target.toml --mock-check
```

Use `--strict` only when a caller wants fixture failures to produce a non-zero
exit code. The committed fake health fixture intentionally includes a critical
storage-safety problem so failure reporting stays covered without live services.

The plan covers:

- prerequisite checks for Docker, Compose, Python, uv, Phase CLI, rsync,
  deploy root, and runtime root;
- TOML profile validation through `scripts/validate_profile.py --all`;
- Hermes config and Compose rendering;
- copying distribution-owned material, including committed non-secret examples
  like `.env.example`, with live env, secret, runtime, Phase export, log,
  backup, session, memory, and personal-file exclusions;
- per-profile runtime directory creation;
- profile TOML install/update into each instance config boundary;
- `SOUL.md` install/update into each instance Hermes home and `AGENTS.md`
  install/update into each instance workspace, with Hermes `terminal.cwd`
  pointed at `/workspace` for AGENTS discovery;
- Phase-backed secret bridge materialization;
- profile skill install/sync into each instance's container-owned skills
  directory through a bounded `sudo env PATH="$PATH" uv run ...` command;
- Docker Compose pull, start, restart, status, health, and logs commands;
- backup-boundary discovery and restore/redeploy references.

## Target TOML

`mock-target.toml` documents the expected remote target shape:

- `[target]` names only non-secret SSH and path metadata.
- `[ssh]` records operator SSH options.
- `[phase]` records the materialization strategy and the instance-local bridge
  directory pattern.
- `[health]` points at a fake local fixture for mock checks.

Committed target templates must keep `target.mode = "mock"` and
`phase.live_secret_policy = "human-review-only"`. Real VM hostnames, private
paths, Phase service tokens, exported secrets, generated env files, and runtime
state stay outside git.

## Phase Secret Materialization

Profile TOML files own the non-secret Phase metadata:

- Phase app: profile-specific; Tom's first live proof currently uses
  `Tom's personal agent`
- Phase environment: profile-specific, currently `prod` for owner templates
- Phase path: one per personal-agent instance
- Secret names: generic per-instance names under each Phase path. Telegram
  requires `TELEGRAM_BOT_TOKEN` and `TELEGRAM_OWNER_ID`; `OPENAI_API_KEY` is
  optional and only used by profiles that choose an API-key model provider.

The dry-run plan runs `deploy/remote/materialize-secret-bridge.sh` from the
copied deploy root under `phase run`. That script writes only instance-local
bridge files under
`${EXO_RUNTIME_ROOT}/<profile>/secret-bridge/`:

- `telegram-bot-token`, for providers that require a token file;
- `provider.env`, a smallest-available dotenv-compatible bridge containing the
  Hermes-native Telegram runtime keys `TELEGRAM_BOT_TOKEN`,
  `TELEGRAM_ALLOWED_USERS`, and `TELEGRAM_HOME_CHANNEL`, plus a model provider
  API key only when configured.

The materializer fails closed if Phase does not inject every required generic
Telegram secret for the profile, and maps `TELEGRAM_OWNER_ID` to Hermes'
allowlist/home-channel variables. It fails on an API key only when the profile
names one.
Generated bridges are ignored runtime artifacts. Compose
connects `provider.env` through the profile-local `env_file`; other local
ingestion should use Phase runtime injection, Vite built-in env loading for
Vite surfaces, or Node built-in DotEnv support for Node services/CLIs. Do not
add broad committed env catalogs or raw secret values.

## Instance Boundaries

The generated multi-owner Compose template runs one container per
personal-agent instance. Every profile has separate runtime directories for:

- Hermes home;
- workspace;
- secret bridge;
- skills;
- writable vault;
- read-only personal files;
- logs;
- backup boundary;
- placeholder read-only mounts.

No active Hermes gateway containers may share a Hermes home, Telegram token
path, log boundary, backup boundary, skills directory, or restart/container
boundary.

## Operator Update And Redeploy

For a fresh VM or update, the operator flow is:

1. Review the dry-run plan.
2. Ensure Docker Compose, Python, uv, rsync, SSH, and Phase CLI are available.
3. Validate profiles and render templates locally.
4. Copy distribution material to the deploy root with the plan's rsync command.
5. Create runtime directories, install/update profile TOML into each profile
   config boundary, install the repo-owned `SOUL.md` into the profile's Hermes
   home, and install the repo-owned `AGENTS.md` into the profile workspace as
   `/workspace/AGENTS.md`. The generated Compose env and existing
   `config.yaml` patch point Hermes terminal cwd at `/workspace` so Hermes loads
   Exo project context from the runtime workdir.
6. Materialize Phase secret bridges.
7. Install or sync approved skills for each profile. On redeploy, this step
   runs through `sudo` because the live skills directory is owned by the Hermes
   container UID after the first normalization pass.
8. Run Compose pull and `up -d --remove-orphans`.
9. Inspect status, health, and logs.

When an update changes `SOUL.md`, profile role text, or a seeded personality
preset for an already-used profile, reset the owner conversation before
re-running the identity smoke. Prefer the owner-visible `/reset` or `/new`
Telegram command; alternatively, use `hermes sessions delete --yes <session-id>`
only with explicit operator approval. Deployment must not silently delete
Hermes sessions because they are user-owned runtime state.

To redeploy after a distribution update, repeat the same plan. Compose restart
boundaries are per service/container, so one profile can be restarted without
sharing active Hermes home state with another.

## Backup And Restore

Backup tooling should treat each profile's `backup-boundary` as the unit of
restore. At template level, a restore onto a fresh VM should:

1. Recreate the deploy root from git.
2. Recreate `${EXO_RUNTIME_ROOT}/<profile>/` directories.
3. Restore only that profile's Hermes home, writable vault, and required
   runtime config into the matching profile boundary.
4. Re-run Phase bridge materialization instead of restoring old secret exports.
5. Re-run skill install/sync from the pinned manifest.
6. Start only the restored profile's Compose service first, then inspect health
   and logs before starting the rest.

Profile-scoped deployment preserves other owners' running containers; start
commands do not remove Compose orphans. Retire services explicitly when needed.
Private writable runtime directories are repaired to mode 0700 on each deploy.

Skill sync now records installed-content fingerprints and refuses runtime drift.
Legacy installs without fingerprints also stop for reconciliation: preserve the
existing directory, compare/promote needed edits to source, then move the saved
installation aside before a fresh install. Stop runtime writers during sync.
Do not fabricate a baseline to bypass this check.

Remote deploy/runtime paths and Compose output paths must use only letters,
digits, underscores, dots, slashes, and hyphens; plans reject other characters
before emitting commands across the SSH/rsync shell layers.

Deploy plans stop the selected Compose gateways before skill sync and restart
them after installation. Keep other runtime writers stopped too. A collision
stops deployment; reconcile preserved edits before resuming the gateway.
