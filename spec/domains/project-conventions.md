# Project Conventions

This repository is a Hermes profile-distribution/setup repository. Conventions
below apply to repo-owned distribution material and local validation tooling.

## Paths

- Distribution-owned material lives in git under `distribution.yaml`, `SOUL.md`,
  `AGENTS.md`, `.agents/skills/`, `docs/`, `profiles/`, `skills/`,
  `schemas/`, `exo_distribution/`, `scripts/`, `tests/`, and `spec/`.
- User-owned/runtime material must stay outside git. This includes Hermes
  homes, memories, sessions, logs, backups, state databases, mounted personal
  files, Phase service tokens, generated secret bridge files, and
  machine-specific paths.
- Profile directories in this repo are templates or examples, not live Hermes
  homes.
- Owner template profiles must keep unique profile ids, container names, Hermes
  homes, Telegram token paths, log paths, and backup paths.
- Docker/Compose examples are generated distribution material. Host paths they
  reference remain user-owned/runtime paths under `${EXO_RUNTIME_ROOT}`.
- Remote deployment templates live under `deploy/remote/`. Committed targets
  are non-secret mock/dry-run templates only; live VM host facts, generated
  secret bridges, Phase service tokens, and runtime state stay outside git.

## Config

- Non-secret config is TOML and must validate through
  `uv run python scripts/validate_profile.py`.
- Hermes-native config output is rendered from TOML and template material with
  `uv run python scripts/render_hermes_config.py`.
- Multi-owner Compose output is rendered from all committed profiles with
  `uv run python scripts/render_compose.py`.
- Remote deploy plans validate profiles and render a mock SSH workflow with
  `uv run python scripts/remote_deploy.py --config deploy/remote/mock-target.toml`.
- Minimal proactive behavior is configured only in TOML under `[proactive]`.
  It targets the same profile id, uses the `telegram-owner-text` surface, and
  validates with fake/local health providers for automated checks.
- Storage contracts are configured only in TOML under `[storage]`. Each
  profile must declare runtime, vault, and personal-file zones with host path
  placeholders, container paths, access mode, permissions, backup/recovery
  expectations, and explicit allowed write paths.
- Unknown or misplaced TOML fields should fail validation before deployment or
  smoke execution.

## Secrets

- `.env.example` is secret-only, blank, and limited to required provider bridge
  variables.
- Ordinary config must not be added to `.env.example`.
- Real env files, Phase exports, service tokens, and generated secret bridges
  are ignored runtime artifacts.
- Prefer Phase injection and native runtime env ingestion. Do not add `dotenv`
  by default.
- Do not use `VITE_` prefixes for secrets.
- Any generated dotenv-compatible provider bridge must be instance-local under
  `${EXO_RUNTIME_ROOT}/<profile>/secret-bridge/`, ignored by git, and limited to
  the smallest provider-required secret names.
- Generated provider bridges must fail closed when Phase does not inject every
  required per-profile secret, and Compose services that need the bridge must
  reference the profile-local `provider.env` with `env_file`.

## Runtime Defaults

- Local/dev automated validation uses fake Telegram, fake model mode, fake Phase
  fixtures, fake proactive health/status fixtures, and local storage fixtures.
- The default profile enables safe/core tools only.
- External-action tools require explicit per-instance opt-in, Phase-managed
  secrets, and approval/audit documentation.
- Proactive v1 may emit only owner-chat Telegram text check-ins and
  health/status pings. Broad follow-up campaigns, complex scheduling, and
  proactive external actions are out of scope.
- Hermes built-in memory/session/context state plus agent-owned Markdown
  vault/files are the v1 durable memory baseline. Personal files and provider
  exports are read-only by default; live provider/topology proof remains
  outside this repo slice with EMB-317.
- Active Hermes gateway containers must not share a Hermes home, Telegram token
  path, log boundary, backup boundary, or restart/container boundary.
- Remote deploy validation uses dry-run or mock-target paths. Live ESXi
  execution remains Human Review/HITL unless a later issue grants access and
  secrets.
- Remote deploy plans must verify remote Docker, Compose, Python, uv, Phase
  CLI, and rsync availability before later steps depend on them.
- Remote deploy Compose commands must set `EXO_RUNTIME_ROOT` to the target
  runtime root, and Phase secret bridge materialization must run from the
  copied deploy root or an absolute deploy-root script path.
- Remote deploy setup must install `SOUL.md` into each profile Hermes home and
  `AGENTS.md` into each profile workspace as `/workspace/AGENTS.md`; `AGENTS.md`
  must remain shared/profile-neutral, with owner-specific behavior selected
  through profile-targeted skills. Generated Compose env and existing Hermes
  `config.yaml` must point terminal cwd at `/workspace` so Hermes actually
  loads the workspace AGENTS context.
- Remote deploy skill sync must be repeatable after the first ownership
  normalization pass. If the profile skills directory is container-owned, the
  installer runs through a bounded `sudo env PATH="$PATH" uv run ...` command
  and the later ownership step returns files to the Hermes runtime UID.
- Remote deploy copy plans must keep committed non-secret examples such as
  `.env.example`, while excluding ignored secret/runtime artifacts including
  live `.env*` files, `.phase/`, Phase exports, generated secret bridges,
  Hermes homes, memories, sessions, logs, backups, and personal files.

## Skills

- `.agents/skills/<skill-name>/` is the flat Agent Skills source tree. Each
  direct child must contain `SKILL.md` with a frontmatter `name` matching the
  directory. Do not nest skill directories under category folders.
- `skills/sources.toml` is the repo-owned source manifest for installable
  skills. It must record repo, path, pinned ref, target profile, install
  destination, source-of-truth expectations, collision policy, sync policy, and
  runtime-promotion policy for each source.
- Approved profile skills install into `/opt/data/skills` through
  `uv run python scripts/install_skills.py`; repo-owned writable
  `skills.external_dirs` must not become the production source of truth.
- Private or unavailable external sources must have explicit fixture fallback
  metadata and operator notes so AFK checks can validate behavior without live
  credentials.
- Runtime-created or runtime-edited skills must be treated as unmanaged
  collisions until promoted back to git with a reviewed pinned manifest update.
