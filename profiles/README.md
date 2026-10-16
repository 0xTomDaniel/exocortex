# Hermes Profile Variants

Profiles in this directory are reusable distribution templates. They are not
live Hermes homes and must not contain credentials, memories, sessions, logs,
backups, mounted personal files, generated secret bridges, or machine-specific
paths.

Each `profile.toml` is non-secret source-of-truth config validated by:

```bash
uv run python scripts/validate_profile.py --all
```

Owner template profiles:

| Profile | Owner | TOML config | Phase path | Secret names | Container |
| --- | --- | --- | --- | --- | --- |
| `tom-personal-agent` | Tom Daniel | `profiles/tom-personal-agent/profile.toml` | `/tom/personal-agent` | `TELEGRAM_BOT_TOKEN`, `TELEGRAM_OWNER_ID`; optional `OPENAI_API_KEY` only for API-key providers | `exo-hermes-tom-personal-agent` |
| `alex-personal-agent` | Alex Example | `profiles/alex-personal-agent/profile.toml` | `/alex/personal-agent` | `TELEGRAM_BOT_TOKEN`, `TELEGRAM_OWNER_ID`; optional `OPENAI_API_KEY` only for API-key providers | `exo-hermes-alex-personal-agent` |
| `sam-personal-agent` | Sam Example | `profiles/sam-personal-agent/profile.toml` | `/sam/personal-agent` | `TELEGRAM_BOT_TOKEN`, `TELEGRAM_OWNER_ID`; optional `OPENAI_API_KEY` only for API-key providers | `exo-hermes-sam-personal-agent` |

All profile TOML files validate against
`schemas/profile-config.schema.json`. Each profile records its role in
`profile.role` and whether it is an installable template in
`profile.intended_profile`.

Telegram token file paths are distinct:

- `${EXO_RUNTIME_ROOT}/tom-personal-agent/secret-bridge/telegram-bot-token`;
- `${EXO_RUNTIME_ROOT}/alex-personal-agent/secret-bridge/telegram-bot-token`;
- `${EXO_RUNTIME_ROOT}/sam-personal-agent/secret-bridge/telegram-bot-token`.

All owner templates enable only safe/core tools by default:

- `memory.read`;
- `memory.write_markdown`;
- `files.read_workspace`;
- `telegram.reply_text`.

Each profile also declares minimal proactive v1 config under `[proactive]`.
The config targets the same profile id, uses only owner-chat Telegram text
delivery, and controls morning/evening check-ins plus fake/local health pings.
Automated validation uses local fixtures only; live Telegram health ping smoke
is a Human Review activity.

Each profile declares the storage contract under `[storage]`: Hermes runtime
state, Markdown vault memory, and broader personal files. Storage entries use
`${EXO_RUNTIME_ROOT}` host path placeholders, fixed container paths, explicit
read-only/read-write modes, permissions, backup/recovery notes, and allowed
write paths. Runtime state and the Markdown vault are writable; broader
personal files and provider placeholders remain read-only by default.

External-action tools remain disabled until a specific owner instance opts in
with Phase-managed secrets and approval/audit documentation.

Privacy boundaries are per owner instance: one Hermes home, one token path, one
log directory, one backup directory, one writable Markdown vault, and read-only
placeholder personal mounts. No profile directory is a live runtime directory.

Render the multi-owner Compose example with:

```bash
uv run python scripts/render_compose.py
```

The renderer validates the whole profile set, renders the installable template
profiles, and fails if active Hermes gateways share a profile id, container
name, Hermes home, Telegram token path, log boundary, or backup boundary.
Compose output declares separate restart boundaries, runtime homes, log
directories, backup directories, and placeholder read-only storage mounts for
each owner.

To add another owner, copy one of the `*-personal-agent` profile directories,
choose a unique profile id, owner name, Phase path, container name, Hermes home,
Telegram token path, log path, backup path, and placeholder mount paths, then
run the validation and Compose render commands above. Secret names may stay
generic because each owner has a distinct Phase path and instance-local bridge.
