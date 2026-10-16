# Human Review Checklist

This checklist is the EMB-451 terminal PRD evidence for EMB-261. EMB-451 is a
non-owning PRD child slice; EMB-261 remains the only final PR and Human Review
owner.

## Parent PRD Readiness

Accepted child slices on the parent PRD integration branch:

- EMB-445: Scaffold Hermes profile distribution and local Tom smoke.
- EMB-446: Add multi-owner Hermes profiles and container isolation.
- EMB-447: Build Exo skills source manifest and installer path.
- EMB-448: Build remote deploy templates and mock SSH workflow.
- EMB-449: Implement storage contract fixtures and mount declarations.
- EMB-450: Add minimal proactive check-ins and health pings.
- EMB-451: Final docs, smoke evidence, and Human Review checklist.

Related HITL Drafts remain outside this repo-owned parent PRD scope:

- EMB-276 owns live ESXi VM provisioning and deployment proof.
- EMB-317 owns storage provider/topology selection and live mount proof.

No child-owned final PR should be opened or attached for EMB-451.

## Agent-Side Smoke Evidence

These commands are expected to pass without real Telegram, model, cloud
storage, Phase, or ESXi access:

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

Expected fake/local coverage:

- distribution structure and profile TOML validation;
- schema rejection of invalid profile sets;
- Hermes config and Compose template rendering;
- secret-only `.env.example` inventory;
- skills manifest planning, fixture install/update, and collision refusal;
- storage-zone mount declarations and sync-health fixture states;
- remote deploy dry-run, mock health/status/log reporting, rsync exclusions,
  Phase secret bridge materialization plan, and Compose lifecycle commands;
- owner-only fake Telegram text smoke and minimal proactive check-in/health
  ping planning.

## Manual Live Telegram Smoke

Human Review requires one real bot token and one real owner account. The
operator should capture a transcript or compact evidence bundle with:

1. The selected profile id, Phase app/environment/path, and generated secret
   bridge location, with secret values redacted.
2. Confirmation that the bot starts from validated TOML and rendered Hermes
   config, not from hand-maintained ordinary `.env` config.
3. A real owner chat message and the assistant's text reply, confirming the
   assistant identifies as Exo and does not present Hermes as its name.
   If `SOUL.md`, role text, or seeded personality config changed after the
   conversation already existed, first send `/reset` or `/new` in Telegram, or
   record the explicit operator-approved `hermes sessions delete` action used
   to clear that profile's test session.
4. A non-owner or wrong-chat attempt showing no assistant reply.
5. Morning/evening check-in delivery to the owner chat only, or the exact
   disabled setting if the profile has proactive delivery disabled.
6. A health/status ping proof using a safe fake or operator-triggered problem,
   delivered only to the owner chat.
7. Logs/status output for the relevant Compose service, with tokens, owner ids,
   private file paths, and message contents redacted where needed.
8. Confirmation that external-action tools remain disabled unless the instance
   has explicit secrets, docs, approval, and audit rules.

Ordinary CI, Agent Review, and Agent QA must not require real Telegram, model,
cloud storage, Phase, or ESXi access.

## Operator Commands

Validate and render local distribution material:

```bash
uv run python scripts/validate_profile.py --all
uv run python scripts/render_hermes_config.py
uv run python scripts/render_compose.py
```

Install or update profile skills:

```bash
uv run python scripts/install_skills.py --profile tom-local-dev
uv run python scripts/install_skills.py --profile tom-local-dev --apply
```

Plan a remote update without opening SSH:

```bash
uv run python scripts/remote_deploy.py --config deploy/remote/mock-target.toml
```

Operator deployment status, logs, and restart commands are emitted by the
remote deploy plan. They use `EXO_RUNTIME_ROOT=<runtime-root> docker compose`
from the copied deploy root, then inspect `ps`, `logs`, health checks, and
service-scoped restarts.

## Backup And Restore Evidence

For each profile, Human Review should verify that backup/restore operates at
the profile backup boundary:

- restore the git-owned deploy root from source;
- recreate `${EXO_RUNTIME_ROOT}/<profile>/` directories;
- restore only that profile's Hermes home, writable vault, and runtime config;
- re-materialize Phase secret bridges instead of restoring old secret exports;
- reinstall skills from `skills/sources.toml`;
- start the restored profile's service first, then inspect health and logs.

## V1 Scope Boundaries

V1 is Telegram-first, owner-only text. The parent PRD excludes voice, media,
file/photo/document ingestion, OCR/PDF processing, arbitrary attachments,
groups, and multi-principal memory. Safe/core tools are enabled by default.
External-action tools require explicit per-instance secrets, documentation,
approval, and audit rules.
