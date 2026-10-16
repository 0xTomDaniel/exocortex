# Repository Regression Suite

Run these commands before handing off changes that affect distribution
material, profile TOML, templates, validator logic, smoke behavior, or docs that
name supported local commands.

```bash
uv run python scripts/validate_profile.py
uv run python scripts/validate_profile.py --all
uv run python scripts/render_hermes_config.py
uv run python scripts/install_skills.py --profile tom-local-dev
uv run python scripts/render_compose.py
uv run python scripts/remote_deploy.py --config deploy/remote/mock-target.toml
uv run python scripts/remote_deploy.py --config deploy/remote/mock-target.toml --mock-check
uv run python scripts/check_storage_contract.py
uv run python scripts/smoke_tom_local.py
uv run python -m unittest discover -s tests
```

Expected coverage:

- the Tom local/dev profile validates against the checked-in schema contract;
- Tom Daniel, Alex Example, and Sam Example owner templates validate against
  the checked-in schema contract;
- the rendered Hermes config matches the committed generated example and
  contains no secret values;
- the skills manifest parses, selects only approved Tom profile skills, plans
  `/opt/data/skills` installs, and excludes unapproved private external-action
  fallback sources;
- the rendered Compose example declares one Hermes container per profile and
  rejects shared Hermes homes, Telegram token paths, logs, backups, and restart
  boundaries, with one profile-local skills mount per container, explicit
  read-write runtime/vault mounts, and read-only personal-file mounts;
- the remote deploy dry-run validates mock target TOML, profiles, render/copy
  plans, profile install/update commands, Phase secret bridge metadata, skills
  install/sync, Compose lifecycle, health/status/log commands, backup/redeploy
  references, remote uv/Phase/rsync prerequisites, `EXO_RUNTIME_ROOT`
  Compose command exports, deploy-root Phase bridge execution, rsync
  exclusions for ignored secret/runtime artifacts, Compose `env_file`
  ingestion of the profile-local provider bridge, fail-closed missing-secret
  materialization, and HITL live-ESXi boundaries without opening SSH or using
  live secrets;
- the mock deploy health path reports fixture failures without requiring real
  Phase, Telegram, model, cloud storage, or ESXi access;
- storage contract fixtures declare runtime, Markdown vault, personal-files,
  and placeholder mounts with permissions, backup/recovery hooks, explicit
  allowed write paths, and fake healthy/stale/errored/unavailable sync-health
  states;
- fake Phase fixtures provide only minimal required secret bridge names;
- fake Telegram smoke replies to the owner-only text interaction and ignores a
  non-owner message;
- fake proactive smoke plans only owner-chat Telegram text deliveries for
  configured morning/evening check-ins and fake service, sync, storage safety,
  and deployment health/status problems;
- the Human Review checklist records accepted EMB-261 child slices, the
  no-child-owned-PR boundary for EMB-451, the manual live Telegram evidence,
  and the EMB-276/EMB-317 HITL exclusions;
- no live Telegram, model provider, Phase service, ESXi host, or private storage
  access is required.
- committed files do not include private runtime homes, logs, backups, sessions,
  personal files, Phase exports, or generated secret bridge values.

PR #1 repair regressions exercise generated SSH commands through a local shell,
selected-profile preservation, explicit private directory modes, runtime skill
drift rejection, and video retry identity across metadata recovery. They do not
claim live SSH/Docker/provider integration proof.

Personal-boundary tests cover source identity recurrence, modular owner-skill
installation, legacy migration preservation, and missing Meow owner context.
See `docs/personal-content-boundary.md` for semantic review and history limits.

## Captured Voice sidecar

Validate the portable Compose template and captured implementation without live
credentials or a running Docker daemon (Compose v2 must be installed):

```bash
VOICE_INSTANCE=fixture-voice HERMES_CONTAINER=fixture-hermes VOICE_RUNTIME_ROOT=/tmp/fixture-voice docker compose -f deploy/voice/sidecar/compose.yaml config --quiet
bash -n deploy/voice/sidecar/entrypoint.sh
uv run python -m py_compile deploy/voice/sidecar/proxy.py
```

Missing deployment selectors must fail Compose rendering. Image builds require
Docker and upstream network access; they do not authenticate or test phone Voice.
See `deploy/voice/sidecar/README.md` for private runtime and acceptance boundaries.
