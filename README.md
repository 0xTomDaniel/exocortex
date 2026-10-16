# exocortex

Exo is Tom's personal executive assistant agent. This repository holds the **agent instance**: identity (`SOUL.md`), always-on policy (`AGENTS.md`), skills, profile configuration and setup tooling. It does not own live runtime state; the memory vault is not in git.

## Current runtime — October 2026

Exo now runs daily as **Pi + [OptChat](https://github.com/jonaslsaa/pi-optchat)** (one growing chat session, summary-tree memory) working directly in the synced vault, with [BB](https://getbb.app) as the desktop entry point. The BB plugins and the canvas interface live in the private **[exosurface](https://github.com/0xTomDaniel/exosurface)** repo, which this instance enables; Exosurface does not depend on this repo. **[Exomachina](https://github.com/0xTomDaniel/Exomachina)** is the separate factory product.

- OptChat runs pure upstream; the one local fix needed on a proxy route that sets 1h cache TTLs is proposed upstream as [jonaslsaa/pi-optchat#187](https://github.com/jonaslsaa/pi-optchat/pull/187). Compactor: Sonnet 5.5 medium.
- [`tools/optchat-compactor-eval/`](tools/optchat-compactor-eval/) compares compactor models on real memory tasks (outputs stay local: they contain memory excerpts).
- Vault setup for Pi/Codex/Claude: [local vault setup](deploy/local-vault/README.md).

**Historical:** the Hermes distribution below (Telegram-first profiles, compose deployments, voice sidecar) was the May–September 2026 runtime. It is kept as reference and for its tests; it is not the current daily path.

## Hermes distribution (historical)

The first runnable slice is `tom-local-dev`: a Tom-oriented local/dev profile
that validates TOML config, renders a Hermes-native config example, and proves a
mocked owner-only Telegram text loop without live Telegram, model credentials,
Phase access, ESXi access, or private storage. The distribution also includes
installable template profiles for Tom Daniel, Alex Example, and Sam Example.

For Pi, Codex or Claude working directly in a synced vault, follow the
[local vault setup](deploy/local-vault/README.md). It keeps `.agents/skills`
canonical and configures pinned Nitride retrieval without native Obsidian CLI.

## Repository Boundary

Distribution-owned paths in git:

- `distribution.yaml`: Hermes-compatible distribution manifest shape;
- `SOUL.md`: identity and behavioral direction for Exo;
- `AGENTS.md`: always-on runtime policy and project context installed into
  each profile workspace;
- `profiles/tom-local-dev/`: non-secret Tom local/dev profile template,
  fixtures, and rendered Hermes config example;
- `profiles/*-personal-agent/`: non-secret installable owner template
  profiles;
- `deploy/compose/`: Docker Compose templates and generated examples;
- `docs/`: operator checklists and parent PRD readiness evidence;
- `schemas/profile-config.schema.json`: checked-in config contract;
- `exo_distribution/` and `scripts/`: validator, renderer, and smoke tooling;
- `tests/`: fake/no-credentials regression coverage;
- `spec/`: durable product and regression docs.

User-owned/runtime paths outside git:

- real Hermes homes, `/opt/data` instance directories, memories, sessions,
  logs, backups, state databases, and mounted personal files;
- credentials, Phase service tokens, exported secrets, and generated secret
  bridge files;
- machine-specific storage mount paths and private owner data.

## Config and Secrets

Non-secret config lives in TOML:

```bash
uv run python scripts/validate_profile.py profiles/tom-local-dev/profile.toml
```

Render the committed Hermes config example from TOML:

```bash
uv run python scripts/render_hermes_config.py
```

Validate every committed profile and cross-profile isolation:

```bash
uv run python scripts/validate_profile.py --all
```

Render the multi-owner Compose example:

```bash
uv run python scripts/render_compose.py
```

Secrets are Phase-backed and documented only as a blank bridge inventory in
`.env.example`. The example intentionally contains the Telegram token and
Telegram owner id keys required by the local/dev and production per-instance
bridges, plus optional provider keys such as `OPENAI_API_KEY`. `OPENAI_API_KEY`
is only used by profiles that select an API-key model provider; Hermes Codex
OAuth / ChatGPT Pro login does not require it. Ordinary profile, storage, tool,
and deployment config belongs in TOML, not `.env`.

Production/operator runs should prefer Phase injection, such as:

```bash
phase run --app exo-executive-agent --env dev --path /tom/local -- <command>
```

Template owner paths are `/tom/personal-agent`,
`/alex/personal-agent`, and `/sam/personal-agent`. Their blank secret
names are inventoried in `.env.example` for bridge compatibility only; live
secret values stay in Phase and outside git.

If a local dotenv-compatible bridge is required by a provider, keep it
generated, instance-local, ignored by git, and limited to the smallest required
secret interface. Use native Phase, Vite, or Node env ingestion where relevant;
do not add `dotenv` by default and do not use `VITE_` prefixes for secrets.

## Remote Voice sidecar

The captured Codex Voice service, Runs proxy, private-state preparation, and
rebuild/rollback procedure are in [deploy/voice/sidecar](deploy/voice/sidecar/README.md).
It attaches to an existing owner Hermes service; it does not deploy Hermes or
commit authentication, conversations, or host configuration.

### Voice thread model selection quirk

In iOS remote tests on 2026-09-07 with Codex app-server `0.153.4`, creating a
thread directly in Voice selected `gpt-5.6-terra` with low reasoning effort,
despite the server default being `gpt-6-astra` / low. This concerns the backing
agent model, not the realtime speech model. The cause of the startup selection
has not been established; the server default alone did not prevent it.

**Workaround:** create a text thread with the model selector set to
`gpt-6-astra` and low effort, send a text message, then enter Voice in that same
thread. In the tested text-created thread, the text turn, subsequent Voice
backing turn, and call-ending handoff all used Astra / low. Creating another
thread directly in Voice can encounter the quirk again. Verify the actual
backing model in turn logs when checking whether a client/server update fixes
this behavior.

## Local Smoke

Run the no-credentials Tom local/dev smoke:

```bash
uv run python scripts/smoke_tom_local.py
```

Run the full no-real-credentials regression suite before handoff:

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

Or run the unit/regression suite directly:

```bash
uv run python -m unittest discover -s tests
```

Inspect the fake/local storage contract evidence:

```bash
uv run python scripts/check_storage_contract.py
```

The smoke uses:

- fake Telegram updates from
  `profiles/tom-local-dev/fixtures/fake_telegram_owner_text.json`;
- fake Phase/minimal secret bridge values from
  `profiles/tom-local-dev/fixtures/fake_phase_minimal.json`;
- fake proactive health/status problems from
  `profiles/tom-local-dev/fixtures/fake_health_status_problems.json`;
- local storage fixtures under `profiles/tom-local-dev/fixtures/storage`;
- fake storage sync-health states from
  `profiles/tom-local-dev/fixtures/storage/sync-health.json`;
- fake model mode, with no live provider calls.

The expected behavior is one reply to the owner chat and no reply to a
non-owner chat. The smoke also plans owner-only Telegram text proactive
deliveries for the configured morning check-in, evening check-in, and fake
service/sync/storage-safety/deployment health problems.

## Minimal Proactive v1

Profiles configure minimal proactive behavior in TOML under `[proactive]`.
The v1 scope is deliberately narrow:

- enable or disable all proactive delivery per profile;
- target exactly the current profile via `target_profile_id`;
- deliver only through the `telegram-owner-text` surface;
- configure morning and evening local check-in times;
- configure fake/local health pings for service, sync, storage safety, and
  deployment problems.

Automated validation uses the fake local provider only. It never contacts live
Telegram, Phase, model providers, cloud storage, or ESXi, and it never sends to
groups, arbitrary contacts, or non-owner principals. Rich follow-up campaigns,
complex routine scheduling, and proactive external actions remain outside this
distribution slice.

## Tools and External Actions

The default Tom local/dev profile enables only safe/core tools:

- `memory.read`;
- `memory.write_markdown`;
- `files.read_workspace`;
- `telegram.reply_text`.

External-action tools that can send email, book calendar events, spend money,
trade, post publicly, mutate broad cloud storage, or call sensitive provider
APIs are disabled by default. They require explicit per-instance opt-in,
Phase-managed secrets, and approval/audit documentation.

## Skills Manifest and Installer

Repo-owned skills live as flat Agent Skills directories under
`.agents/skills/<skill-name>/`, where each skill has a `SKILL.md` file whose
frontmatter `name` matches the directory name. The flat `.agents/skills/`
layout is the cross-client discovery surface; do not nest skills under
category folders such as `general/` or `personal/`.

`skills/sources.toml` is the profile-aware manifest. Each entry records the
source repository, source path, pinned ref, general/personal category, target
profiles, install destination, source-of-truth policy, collision policy, sync
behavior, and the promotion path for runtime-created skills. Tom/profile-specific
procedural guidance is owned solely by `tom-operating-style` (including its team-planning module), which
stays in the main flat skill tree, but the manifest targets it only to
`tom-personal-agent`.

Plan the Tom local/dev install set:

```bash
uv run python scripts/install_skills.py --profile tom-local-dev
```

Production/operator installs write approved profile skills into the instance
skills directory rooted at `/opt/data/skills`:

```bash
uv run python scripts/install_skills.py --profile tom-local-dev --apply
```

Automated checks can install into a temporary root without live credentials:

```bash
uv run python scripts/install_skills.py --profile tom-local-dev --install-root /tmp/exo-skills --apply
```

The installer fails closed when a selected manifest entry collides with another
selected skill name or destination, or when an existing runtime skill directory
lacks `.exo-skill-source.json` metadata. Matching pinned refs are left
unchanged; changed refs for the same source id are replaced. Runtime-created or
runtime-edited skills are not authoritative until promoted back to git with a
reviewed manifest update.

`skills.external_dirs` may remain a developer convenience, but writable
repo-owned skill directories are not the production source of truth. Sensitive
external-action skills remain unapproved by default and require owner approval,
Phase-managed secrets, and audit notes before a profile targets them. The
private calendar fallback in `.agents/skills/private-calendar-audit/` exists
only so AFK checks can validate private-source metadata without repository
credentials.

## Multi-Owner Isolation

Each owner profile declares a distinct Hermes container, Hermes home, Telegram
token path, log directory, backup directory, and placeholder storage mounts
under `${EXO_RUNTIME_ROOT}`. The Compose renderer validates this profile set and
fails before rendering if two active gateways share a Hermes home or another
restart/runtime boundary.

Remote setup installs the repo-owned `SOUL.md` into each profile Hermes home and
the repo-owned `AGENTS.md` into each profile workspace as
`/workspace/AGENTS.md`. Hermes loads the workspace `AGENTS.md` as project
context through `terminal.cwd` / `TERMINAL_CWD=/workspace`, while `SOUL.md`
remains the primary identity prompt.

The generated Compose example declares one service per installable owner
template. It mounts each Hermes home at `/opt/data/hermes-home`, the owner
vault at `/opt/data/vault`, personal files read-only at `/mnt/personal-files`,
and additional placeholder personal mounts read-only. These host paths are
runtime/operator paths and are ignored by git.

## Storage Contract

Each profile declares the three EMB-261 storage zones in TOML:

- per-user Hermes runtime state mounted read-write at `/opt/data/hermes-home`;
- agent-owned Markdown memory/vault mounted read-write at `/opt/data/vault`;
- broader personal files mounted read-only at `/mnt/personal-files`.

Every storage declaration records a host path placeholder under
`${EXO_RUNTIME_ROOT}`, a container path, read-only/read-write mode, permission
expectation, backup expectation, recovery expectation, and explicit allowed
write paths. The only default write paths are `/opt/data/hermes-home` for
Hermes memory/session/context state and `/opt/data/vault` for agent-owned
Markdown memory. Personal files and placeholder provider exports declare no
write paths.

`scripts/check_storage_contract.py` uses fake/local fixtures to report storage
mount declarations and the four sync-health states: `healthy`, `stale`,
`errored`, and `unavailable`. This repository slice does not choose the live
provider or topology. EMB-317 owns provider/topology choice and live mount
proof; unresolved provider details must stay placeholders here.

## Human Review Live Smoke

Automated checks do not use live Telegram. Human Review remains responsible for
one manual live Telegram smoke with a real bot token and owner account before a
deployed personal-agent runtime is considered usable. That manual smoke should
confirm that the assistant identifies as Exo, configured check-ins and
health/status pings appear only in the owner chat, and no group, non-owner, or
external-action delivery occurs.

After identity or persona updates on an already-used profile, clear the test
conversation before re-running that smoke. Prefer `/reset` or `/new` in
Telegram; use `hermes sessions delete --yes <session-id>` only as an explicit
operator-approved recovery action. Deployment does not silently delete sessions.

Use [docs/human-review-checklist.md](docs/human-review-checklist.md) for the
required EMB-261 parent readiness summary, accepted child-slice evidence,
manual Telegram transcript requirements, backup/restore evidence, and the
explicit HITL boundaries for EMB-276 and EMB-317.

Direct filesystem voice deployment: [vault voice setup](deploy/voice/vault/README.md).
