# Tom Local/Dev Profile

This profile is a reusable distribution template, not Tom's live Hermes home.
It is safe to commit because it contains only non-secret TOML config,
Hermes-native templates, and generated example output.

Distribution-owned paths:

- `profile.toml`: non-secret source-of-truth config;
- `hermes/config.yaml.template`: Hermes-native config template;
- `generated/config.yaml`: committed example output rendered from TOML;
- `fixtures/`: fake Telegram, fake Phase, storage sync-health, and local
  storage fixtures for tests.

User-owned/runtime paths that must stay outside git:

- real Hermes homes and `/opt/data` instance directories;
- credentials, Phase service tokens, and generated secret bridge files;
- memories, sessions, logs, backups, and mounted personal files;
- machine-specific storage mount paths.

Default tools are safe/core only. External-action tools such as email,
calendar booking, public posting, spending, trading, broad cloud mutation, or
sensitive provider APIs require a separate per-instance opt-in, explicit
Phase-managed secrets, and approval/audit documentation.

The local/dev storage contract is a fixture, not live storage. It declares
Hermes runtime state at `/opt/data/hermes-home`, Markdown vault memory at
`/opt/data/vault`, read-only personal files at `/mnt/personal-files`, and a
read-only calendar export placeholder. Fake sync-health coverage lives in
`fixtures/storage/sync-health.json` and intentionally covers healthy, stale,
errored, and unavailable states without choosing a live provider.
