# Hermes Personal Agent Distribution

## Intended Behavior

`exo-executive-agent` defines a reusable Hermes-based personal executive
assistant distribution. The distribution can be instantiated as separate
private Hermes agents, initially for Tom Daniel, Alex Example, and Sam
Example.

The repository owns non-secret, redeployable source material: Hermes profile
distribution manifests, identity and project-context templates, TOML config
schemas and templates, optional profile variants, portable skills, skill source
manifests, cron and MCP templates, Docker Compose templates, remote deployment
scripts, health checks, and setup documentation.

The repository does not own live instance state. Credentials, private memories,
sessions, logs, backups, mounted personal files, private machine-specific paths,
instantiated per-user Hermes homes, and Phase authentication material stay
outside git.

## Domain Concepts

**Personal-agent instance**: One running Hermes agent for one owner. Each
instance has its own Hermes data directory, Telegram identity/token path,
memory, sessions, logs, storage mounts, backup boundary, and lifecycle.

**Distribution-owned material**: Source-controlled material that should be
updated through git, such as manifests, templates, shared skills, optional
profile variants, scripts, and docs.

**User-owned material**: Runtime-local or private material that must not be
committed, such as credentials, Phase service tokens, generated secret bridge
files, Hermes memories, sessions, logs, state databases, backups, mounted
personal files, and local paths.

**Optional profile variant**: A reusable Hermes profile template or
distribution variant with a documented role, config file, secret interface,
enabled tools, and privacy boundaries. A variant is not a live profile
directory.

**Typed config file**: A TOML file that is the source of truth for non-secret
profile, deployment, storage, tool, and scheduling configuration. TOML config is
validated by a checked-in schema before rendering any Hermes-native YAML,
Compose file, minimal runtime secret bridge, or other runtime materialization.
Use Zod when the implementation is TypeScript/Node; use an equivalent Python
schema validator such as Pydantic, msgspec, or JSON Schema when the
implementation is Python.

**Secret materialization**: The process of fetching per-instance secrets from
Phase and injecting them only at runtime or deploy time. Phase is the preferred
secret-management system for production and operator deployments.

**Skills source tree**: The flat `.agents/skills/<skill-name>/` project
directory that contains checked-in Agent Skills. Each direct child directory is
a skill and must contain `SKILL.md` with a frontmatter `name` matching the
directory. General and personal categorization belongs in metadata and
`skills/sources.toml`, not nested category folders, so standard skill loaders
can discover the tree.

**Skills source manifest**: `skills/sources.toml`, a source-controlled manifest
listing approved skill sources across repositories. Entries include repo, path,
pinned ref, general/personal category, intended profiles, install destination,
collision policy, sync/update behavior, fallback/operator notes for unavailable
private sources, promotion policy, and source-of-truth expectations.

**Skill installer/package manager**: `scripts/install_skills.py`, the mechanism
that plans or installs approved skills into each personal-agent instance's
`/opt/data/skills` directory without treating writable repo-mounted skill
directories as the production source of truth.

**Three-zone storage model**: The storage contract for each instance:
per-user Hermes runtime state, agent-owned writable Markdown memory/vault
area, and broader personal files mounted read-only by default.

**Sync-health state**: The storage status vocabulary exposed to the owner or
operator. V1 recognizes `healthy`, `stale`, `errored`, and `unavailable`
without requiring a live storage provider during automated checks.

**Remote SSH deployment**: The preferred operator deployment path. Scripts
should be able to prepare or update the VM, copy or render non-secret
templates, install or update profiles and skills, start or restart Docker
Compose services, and run health checks over SSH. Live ESXi access is not
assumed for ordinary Octo implementation or QA work.

## Rules and Invariants

- Hermes Agent is the v1 runtime.
- `exo-executive-agent` is the shared git-owned distribution/setup repository.
- Durable changes to distribution-owned material must be git changes committed
  to this repository.
- Runtime Hermes instances must not silently mutate repo-owned skills,
  profiles, templates, or deployment artifacts as the durable source of truth.
- Non-secret configuration must live in TOML config files, not as hand-managed
  environment variables.
- TOML config files must be validated against a checked-in schema in tests and
  before deployment scripts materialize runtime files.
- Environment variables are allowed only as a last-mile process interface for
  secrets or third-party tools that require env vars. They are not the durable
  config source of truth and should not become a broad `.env` catalog.
- The repository should include a committed secret-only `.env.example` that
  documents required secret keys, explicitly optional provider keys, their
  Phase app/environment/path mapping, and the runtime/provider reason each key
  exists. It must not contain ordinary non-secret configuration or every
  optional provider supported by Hermes.
- If a real `.env`-compatible artifact is produced, it must be generated,
  ignored by git, instance-local, and limited to the smallest provider-required
  secret bridge. It must not contain ordinary non-secret configuration.
- Runtime secret ingestion should use Phase injection, Vite's built-in env-file
  loading where a Vite app surface exists, or Node's built-in DotEnv support
  where a Node service or CLI needs local `.env` ingestion. Do not add the
  `dotenv` package by default.
- Secrets must not use a Vite client-exposed prefix such as `VITE_`. Any
  `VITE_` variable is public client configuration and must be non-secret.
- Phase is the preferred secret-management surface. Production/deploy flows
  should fetch secrets from Phase rather than treating committed examples or
  manually edited `.env` files as authoritative.
- v1 runs one Docker container per personal-agent instance.
- Docker Compose profiles should use the current official Hermes image
  `nousresearch/hermes-agent:latest` and run the gateway command explicitly,
  unless a later operator-owned image or pin is approved.
- Active Hermes gateway containers must not share one Hermes home or one
  persistent data directory.
- Each instance must have distinct Telegram token/identity paths, runtime data,
  logs, restart boundaries, and backup boundaries.
- Deployment templates must support redeploying from scratch on a fresh VM,
  not only updating an already-working host.
- Live deployment tooling must support a shared Exo/Hermes Docker host that can
  eventually run separate Tom, Alex Example, and Sam Example containers,
  while allowing the first ESXi proof to deploy only Tom's selected profile
  without requiring Alex or Sam secrets, containers, or runtime state.
- The shared VM must attach to both the operator `VM Network` and the
  `VM Storage` network. Docker image, container, and volume state must not bloat
  the small OS disk; configure Docker's data root or equivalent container state
  storage on the `verticordia`-backed runtime volume.
- Remote deployment scripts must support dry-run, local, fixture, or mock-target
  validation so Octo agents can complete code and QA work without direct access
  to the operator's ESXi VM.
- Live ESXi deployment validation is a Human Review/HITL activity unless a
  specific issue explicitly provisions remote access and required secrets for
  the acting agent.
- Production skill installation should copy, sync, or install approved skills
  into each instance's `/opt/data/skills`.
- Hermes `skills.external_dirs` may be used as a dev/operator convenience, but
  writable repo-owned external skill directories are not the production
  source-of-truth path.
- Skill installer sync behavior must be pinned-ref based: install missing
  approved skills, keep matching installed refs unchanged, replace only the
  same source id when its pinned manifest ref changes, and fail closed on
  unmanaged or cross-source collisions.
- Runtime-created or runtime-edited skills are not durable distribution
  material until promoted back to git through a reviewed manifest/source update.
- The default distribution enables only safe/core tools.
- External-action tools that can send email, book calendar events, spend
  money, trade, post publicly, mutate broad cloud storage, or call sensitive
  provider APIs are opt-in per instance.
- v1 user-facing runtime is owner-only Telegram text chat.
- Minimal proactive v1 behavior is limited to owner-only Telegram text
  morning/evening check-ins and health/status pings for service, sync, storage
  safety, or deployment problems. It is configured in TOML, must target the
  current profile, and must be testable through fake/local providers.
- CLI, Docker, and SSH commands are operator setup, debug, and recovery
  surfaces, not equal first-class v1 user surfaces.
- Voice, file/photo/document ingestion, OCR/PDF processing, arbitrary Telegram
  attachments, group chat, and multi-principal memory boundaries are out of v1
  scope.
- Rich autonomous follow-up campaigns, complex routine scheduling, and
  proactive external actions outside the owner chat are out of v1 scope.
- v1 memory uses Hermes built-in memory/session/context behavior plus Markdown
  vault/files as the shared durable memory baseline.
- External memory providers such as Honcho are optional future or per-instance
  adapters and do not block v1.

## Interfaces/Contracts

### Distribution Interface

The distribution should expose Hermes-compatible profile material such as
`distribution.yaml`, `SOUL.md`, `AGENTS.md`, generated or templated Hermes
`config.yaml`, `.agents/skills/`, `cron/`, optional `mcp.json`, and non-secret
examples. Exo-owned configuration should be authored in TOML, validated by
schema, and rendered into Hermes-native files or process environment only where
Hermes or a provider requires that shape. The final layout may include profile
variant subdirectories if the selected Hermes-compatible installer path requires
it.

`SOUL.md` is the authoritative user-facing identity prompt. Deployment must
install it into each profile's Hermes home so Telegram replies identify the
assistant as Exo. Hermes may appear in infrastructure, status, and runtime docs,
but it must not leak into normal owner-facing self-introductions as the
assistant's name. Setup must also patch any seeded upstream personality preset
that names the assistant Hermes.

Root `AGENTS.md` is the shared always-on Exo project and operating-policy
context. It must remain safe for every owner profile and route owner-specific
guidance to profile-targeted skills such as `tom-operating-style`. Deployment
must install it into each profile workspace as `/workspace/AGENTS.md`, because
Hermes loads AGENTS project context from `terminal.cwd` / `TERMINAL_CWD` while
loading `SOUL.md` from the Hermes home. Setup must point Hermes terminal cwd at
`/workspace` through generated Compose env for first start and by patching an
existing Hermes `config.yaml` during redeploy.

Existing Hermes conversations may keep old identity context even after
`SOUL.md` or profile material is updated. Deployment and Human Review must
reset or delete a profile session only as an explicit operator action, using the
owner-visible `/reset` or `/new` Telegram command when possible, or
`hermes sessions delete --yes <session-id>` for approved recovery. Scripts
must not silently wipe sessions during ordinary redeploys because sessions are
user-owned runtime state.

Each variant must document:

- intended role;
- TOML config file and schema;
- required and optional Phase secret names;
- enabled safe/core tools;
- optional external-action tools, if any;
- privacy boundaries;
- install/update command;
- whether it is a template, an installable distribution, or both.

The initial owner template set is `tom-personal-agent`,
`alex-personal-agent`, and `sam-personal-agent`. Each template must use a
distinct Phase path, Telegram token file path, Hermes home, log path, backup
path, and container/restart name. Secret names may be generic within each Phase
path; for example every owner path can use `TELEGRAM_BOT_TOKEN` and
`TELEGRAM_OWNER_ID` without owner prefixes. The
`tom-local-dev` profile remains a fake/no-credentials smoke profile and may
coexist with the installable Tom template as a separate profile id.

### Deployment Interface

Deployment templates and scripts should support remote SSH operation against
the ESXi guest VM. The operator path should include:

- prerequisite checks;
- directory layout creation;
- rendering or copying non-secret templates;
- validating TOML config files;
- fetching or injecting secrets from Phase;
- profile install or update;
- skill install or sync;
- Docker Compose start/restart;
- health and status checks;
- log inspection;
- backup/restore procedure references.

The multi-owner Compose renderer validates every committed
`profiles/*/profile.toml` file, renders installable owner templates, and must
fail before rendering if two active profiles share a Hermes home, Telegram
token path, log boundary, backup boundary, or container name. Generated Compose
examples are repo-owned templates only; the referenced host directories and
secret bridge files stay under `${EXO_RUNTIME_ROOT}` outside git.
When a provider requires dotenv-compatible secret ingestion, the generated
Compose service references only that profile's
`${EXO_RUNTIME_ROOT}/<profile>/secret-bridge/provider.env` with `env_file`.

Secrets and private runtime state are materialized outside git. Deployment
scripts should document the Phase app, environment, and path layout they expect,
plus whether they use Phase CLI runtime injection, Docker/Compose integration,
or another Phase-supported materialization path.

The EMB-276 VM is a shared Exo/Hermes Docker host, not a Tom-only VM. The first
live ESXi proof on that host targets `tom-personal-agent` only. The multi-owner
template remains the repeatable path for Alex Example and Sam Example, but
the live proof must not require their Phase secrets, containers, or runtime
directories before Tom's instance can be accepted.

Provisioning should keep the Debian OS disk small and place Hermes runtime
state plus Docker image/container/volume state on `verticordia`-backed storage,
for example by mounting the runtime volume at `/srv/exo` and setting Docker
`data-root` below that mount.

Implementation and QA agents should be able to verify deployment logic without
live ESXi access by running schema validation, template rendering, dry-run SSH
planning, local/container smokes, and mocked or fixture-backed health checks.
When live ESXi access is not provisioned to agents, the issue should hand off a
Human Review checklist or operator-run command transcript for final deployment
evidence instead of blocking all implementation work.

### Config Interface

Repo-owned config uses TOML files plus schema validation. The config interface
should distinguish:

- committed defaults and profile variants;
- local per-instance TOML overrides that remain outside git;
- generated Hermes-native `config.yaml` or gateway files;
- generated secret bridge material used only for secrets or provider
  compatibility, with the smallest required set of process env names;
- validation commands suitable for CI, local smoke checks, and remote SSH
  deployment.

The schema should reject unknown or misplaced fields where practical, so config
drift fails before an agent container starts.

The `[proactive]` TOML table controls the minimal proactive surface:

- global enabled/disabled state;
- profile targeting through `target_profile_id`, which must match the profile;
- owner-only `telegram-owner-text` delivery;
- morning and evening local check-in toggles and times;
- fake/local health ping fixture selection for automated service, sync,
  storage-safety, and deployment problem checks.

### Secrets Interface

Phase is the preferred secret manager for per-instance secrets. The repository
may include non-sensitive Phase metadata such as app/environment/path naming
conventions or a `.phase.json` equivalent only if it contains no secret values.
Raw secret values, Phase service tokens, and exported secret files stay outside
git.

Secret names should be documented by Phase app/environment/path and purpose,
then mapped to the TOML fields or Hermes/provider runtime variables they feed.
Per-instance Phase paths, not owner-prefixed secret names, are the owner
boundary. Telegram requires `TELEGRAM_BOT_TOKEN` and `TELEGRAM_OWNER_ID` in the
selected path. `OPENAI_API_KEY` is optional and should be omitted for profiles
using Hermes Codex OAuth / ChatGPT Pro login through Hermes.
Runtime bridge files may map generic Phase names to provider-native names; for
Hermes Telegram this maps `TELEGRAM_OWNER_ID` to `TELEGRAM_ALLOWED_USERS` and
`TELEGRAM_HOME_CHANNEL`.
The first Tom live proof uses the existing Phase app `Tom's personal agent`,
Production environment, and `/tom/personal-agent` path unless the operator
renames or recreates that Phase app before final deployment.
The committed `.env.example` is allowed as a secret inventory and import/bridge
guide with blank values and comments. Do not use it as a broad config catalog.
Phase-injected values may become environment variables at process start when
Hermes, Docker Compose, Telegram, or an LLM provider requires that interface,
but only for the minimal names required by those tools. The durable source is
Phase rather than a committed or manually maintained env file.
Secret bridge materialization must fail before writing runtime bridge files if
Phase does not inject all per-profile required variables. Optional model API
keys are required only when the profile names one.

Do not add a repo dependency on the `dotenv` npm package unless an implementation
spike proves that Vite's built-in env loading, Node's built-in DotEnv support,
and Phase runtime injection cannot cover a required path. Any such exception
must be documented with the exact runtime/version gap it solves.

### Skills Interface

The repository includes `.agents/skills/` as the durable project-level skill
source tree and `skills/sources.toml` as the first durable profile-selection
manifest. The source tree is flat for Agent Skills compatibility. The manifest
records local core skills, imported Exocortex skills, an external core fixture
source, and a private external-action fallback fixture so no-credential checks
can prove multi-repo parsing and install/update behavior.

Profile-specific skills such as `tom-operating-style` may live in the shared
flat source tree, but they must be selected through `profile_targets` rather
than by nesting them in a separate personal directory. `tom-operating-style` is the sole Tom-specific preferences skill and targets
`tom-personal-agent` only. Team planning is an optional module within it.

`scripts/install_skills.py` is the first installer/package-manager path. It
loads the manifest, selects approved entries for a target profile, maps
manifest destinations under `/opt/data/skills`, and can use `--install-root` for
fixture checks without writing live runtime paths.

Production instances receive approved skills in their local Hermes skill
directory. Runtime-local skill edits are not authoritative unless intentionally
promoted through a git commit.

Collision behavior is fail-closed: duplicate selected names or install
destinations fail, existing runtime directories without Exo metadata fail, and
installed metadata from another source fails. Matching source id/repo/path/ref is up to date only when installed content
matches its recorded baseline. A changed pinned ref for the same source is
replaced only when that baseline still matches. Missing baselines (including
legacy installs), changed files, and symlink destinations fail closed; preserve
and reconcile or promote runtime edits before reinstalling. Python bytecode
caches are excluded from distribution and drift detection. Installation checks
plans again before writing; runtime writers must be stopped throughout sync.
This protects against accidental overwrite, not a compromised runtime editing
both its files and baseline metadata.

### Storage Interface

The parent PRD defines the storage contract; EMB-317 chooses the provider and
topology and owns live mount proof. This repository slice must not invent
unresolved provider details. Each instance declares mounts for:

- per-user Hermes runtime state;
- agent-owned writable Markdown memory/vault area;
- general personal files mounted read-only by default.

Each TOML declaration records the host path placeholder under
`${EXO_RUNTIME_ROOT}`, container path, read-only/read-write flag, permissions
expectation, backup expectation, recovery expectation, and explicit
`allowed_write_paths`. The default writable paths are narrow:
`/opt/data/hermes-home` for Hermes built-in memory/session/context state and
`/opt/data/vault` for agent-owned Markdown memory and vault files. Broader
personal files and provider-export placeholders default to read-only and have
no allowed write paths.

Hermes built-in memory/session/context behavior plus Markdown vault/files are
the v1 durable memory baseline. External memory providers are optional future
or per-instance adapters and do not block this contract. Sync health must
distinguish `healthy`, `stale`, `errored`, and `unavailable` through fake/local
fixtures so automated checks can validate behavior without cloud storage,
Phase access, or live mounts.

### Telegram Runtime Interface

V1 supports owner-only Telegram text chat for each user instance. Tom,
Alex Example, and Sam Example should have separate owner identity/token
paths. Automated tests use fake or mocked Telegram. A manual live Telegram
smoke test with a real token and owner account is required during Human Review
before the deployed runtime is considered usable. The smoke reply must confirm
the assistant identifies as Exo rather than Hermes.

## Edge Cases

- A skill name exists in multiple source repositories.
- A runtime-created skill should become durable distribution material.
- A repo-owned skill directory is accidentally mounted writable through
  `skills.external_dirs`.
- The ESXi guest is reachable by SSH but lacks Docker, Compose, rsync, Phase
  CLI, or required filesystem mounts.
- One personal-agent instance starts while another is unhealthy.
- Telegram tokens are swapped, duplicated, or assigned to the wrong owner.
- Phase authentication is missing, points at the wrong app/environment/path, or
  injects a secret for the wrong owner instance.
- TOML config validates locally but generated Hermes runtime files drift from
  the checked-in schema contract.
- General personal files are accidentally mounted read-write.
- Storage sync is stale, unavailable, or in conflict.
- The distribution updates while an instance has local user-owned config.
- Restore from backup is required on a fresh VM.

## Constraints

- Do not commit credentials, live env files, private memories, sessions, logs,
  state databases, backups, mounted personal files, or private machine paths.
- Do not make hand-managed env vars the durable config model. Env vars are for
  minimal runtime secret injection or provider compatibility only.
- Do not create a broad committed `.env.example` catalog for every config or
  optional provider value. Keep `.env.example` secret-only with blank values,
  Phase path/name comments, and runtime/provider rationale. Prefer TOML examples
  for config.
- Do not commit raw Phase tokens, exported secrets, or per-instance secret
  material.
- Do not depend on concrete ESXi details in the parent PRD; EMB-276 gathers
  and validates those facts as a HITL spike.
- Do not choose the storage provider in this parent spec; EMB-317 owns that
  provider/topology decision.
- Do not rely on writable external skill directories as a production
  source-of-truth boundary.
- Do not require real Telegram, model, cloud storage, or ESXi access in
  automated CI.
- Do not require ordinary Octo implementation or QA agents to have direct access
  to the operator's ESXi VM unless a specific issue explicitly provisions that
  access and its secret materialization path.
- Do not enable external-action tools by default in the shared distribution.

## Non-Goals

- Building a full web admin dashboard for v1.
- Supporting Telegram voice, media, documents, OCR, PDFs, arbitrary
  attachments, group chats, or multi-user memory boundaries in v1.
- Selecting the final cloud filesystem provider in EMB-261.
- Committing Tom's, Alex Example's, or Sam Example's private runtime profile
  data.
- Requiring Honcho or another external memory provider for v1.
- Replacing Hermes internals with a custom runtime config system. The TOML
  schema governs Exo distribution/deployment config and may render
  Hermes-native files when needed.
- Using the old Pi package/adapter acceptance criteria as executable v1 scope.

## Open Questions About System Behavior

- Which storage provider/topology will EMB-317 select?
- Which ESXi guest OS, resources, network exposure, and backup/restore details
  will EMB-276 validate?
- Which command shape should select the live deployment profile for EMB-276:
  a profile flag, target TOML profile list, or generated Tom-only target file?
- Which optional profile variants should ship first?
- Which exact Phase app/environment/path layout should Alex Example, Sam
  Example, and any renamed Tom production app use for per-instance Telegram,
  model/provider, storage, and optional external-action credentials?
- Which TOML schema implementation should be used in this repo: TypeScript/Zod
  or a Python equivalent?
- Which implementation choices require target-repo ADRs after spikes resolve?

## Decision Log Or Links To ADRs

- 2026-05-25: Use Hermes Agent as the v1 runtime and `exo-executive-agent` as
  the shared distribution/setup repo.
- 2026-05-25: Model Tom and Alex Example as separate personal-agent
  instances, not one shared runtime.
- 2026-05-26: Add Sam Example as a third initial personal-agent owner, also as a
  separate personal-agent instance with isolated runtime state.
- 2026-05-26: Treat live ESXi deployment as Human Review/HITL unless access is
  explicitly provisioned; Octo agents validate deployment code through dry-run,
  local, fixture, or mock-target paths by default.
- 2026-05-28: EMB-276 provisions a shared Exo/Hermes Docker host for the
  personal-agent containers. The first live proof on that host is scoped to
  `tom-personal-agent` only; Alex Example and Sam Example stay as documented
  repeatable follow-on instances and must not be required for the first live
  proof.
- 2026-05-28: The shared VM must use both `VM Network` and `VM Storage`, keep
  the OS disk small, and place Docker state plus Hermes runtime state on
  `verticordia`-backed storage instead of the boot disk.
- 2026-05-28: Live ESXi staging found the profile-local GHCR image reference
  denied and confirmed the official Docker Hub image
  `nousresearch/hermes-agent:latest` pulls successfully on the VM. Compose
  should run `gateway run` explicitly for gateway deployments.
- 2026-05-28: Live Phase inventory showed an existing Production app named
  `Tom's personal agent`, but no required generic Telegram secrets at
  `/tom/personal-agent`; final live start remains blocked on materializing
  `TELEGRAM_BOT_TOKEN` and `TELEGRAM_OWNER_ID` through Phase without exposing
  raw values. `OPENAI_API_KEY` is not required for the Tom proof because the
  intended model path is Hermes Codex OAuth / ChatGPT Pro login.
- 2026-05-25: Prefer one Docker container and one persistent Hermes data
  directory per personal-agent instance.
- 2026-05-25: Prefer remote SSH deployment scripts that can run the full
  deployment/update/health-check flow.
- 2026-05-25: Define the three-zone storage contract in EMB-261 and leave
  provider/topology selection to EMB-317.
- 2026-05-25: Treat the skill installer/package-manager choice as a required
  child spike.
- 2026-05-27: Use `skills/sources.toml` plus `scripts/install_skills.py` as the
  first durable skills manifest and installer path. Approved profile skills are
  copied into `/opt/data/skills`, with fixture-backed multi-repo sources,
  pinned refs, fail-closed collisions, and git promotion for runtime-created
  skills.
- 2026-05-25: Use TOML files plus schema validation as the durable non-secret
  config model. Env vars remain a runtime injection/provider compatibility
  boundary, not the config source of truth.
- 2026-05-25: Use Phase as the preferred secret-management system for
  production/operator deployments.
- 2026-05-28: Record EMB-451 terminal readiness evidence in
  `docs/human-review-checklist.md`. This finalization did not create a
  target-repo ADR because it consolidates previously accepted TOML schema,
  Phase secret materialization, skills installer, storage contract, and remote
  deployment decisions without selecting a new hard-to-reverse strategy.
- 2026-05-25: No ADR yet. Create target-repo ADRs later only when a
  hard-to-reverse or surprising implementation choice is selected.

## References To Source Issues

- EMB-261: PRD: Rework Exo as Hermes-based personal executive assistant agent
- EMB-276: Set up ESXi VM for personal Hermes agents
- EMB-317: Select privacy-preserving filesystem for personal agents
- Phase docs: https://docs.phase.dev/

### Deployment regression guarantees

Generated SSH commands preserve the complete expression through the local and
remote shells. Compose start never implicitly removes orphan services: a subset
profile deployment must preserve unselected owners in the shared project.
Removing a retired service is a separate explicit operator action. Runtime
home, workspace, vault, skills, logs, backups, and secret-bridge directories
receive explicit 0700 modes before materialization, including on redeploy;
container-writable paths are subsequently assigned to UID/GID 10000.

### Personal content ownership

General planning defaults are permitted, including schedules, capacity limits,
and habit examples, provided owner settings override them. They are not evidence
of the owner's actual state. Exactly one skill, `tom-operating-style`, owns Tom's
reusable preferences; Team planning is a module under it with adjacent assets,
references, and evals. No independently discoverable nested SKILL.md is created.
Private account bindings and historical financial incidents belong in private
configuration/memory. Shared Voice prompts resolve active owner context instead
of hardcoding a person or memory backend.

Source publication is a separate gate from runtime approval. Review descriptions,
code, references, templates, evals, examples, and deployable prompts even for
unapproved/source-only packages. Structural validation and installation filters
are insufficient. Known-identity recurrence tests supplement, not replace,
semantic review of implicit owner instructions.

When migrating existing runtimes, preserve and reconcile the retired standalone
team skill, move it outside skill discovery, then sync the consolidated package.
The installer fails closed while the retired directory remains; it never deletes
local edits automatically. Missing content baselines retain their existing
preservation requirement.
