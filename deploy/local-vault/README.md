# Local vault setup for Pi, Codex and Claude

This recipe installs Exo's shared skills into an existing Markdown vault without
Hermes or a server container. Syncthing carries vault files; Node, uv, agent
executables, login state, model defaults and shell configuration remain local
machine responsibilities. Do not put home-directory settings, credentials,
sessions, machine paths or backups in this repository or the synced vault.

## Canonical source and discovery

Use `<vault>/.agents/skills` as the only editable skill source. Pi and Codex
already discover that location when launched in the vault; adding duplicate
`.pi/skills` or `.codex/skills` trees is unnecessary. Trust the vault in Pi so
project resources can load. Preserve existing project settings and owner skills.

Claude uses these relative projections, created only after checking that their
paths are absent or already point to the intended source:

```sh
cd "$EXO_VAULT"
mkdir -p .claude
ln -s ../.agents/skills .claude/skills
ln -s ../AGENTS.md .claude/CLAUDE.md
```

Do not copy the source into each harness directory or overwrite a conflicting
file/link. Relative links survive different Mac/Linux vault roots. Keep these
links inside hidden provider directories: the pinned Nitride CLI rejects visible
symlinks, including a root `CLAUDE.md` symlink. Check receiving-device links after
sync; clients that cannot materialize symlinks need a local projection step.

## Install the pinned Nitride skill

Require Node 22 or newer and uv. Use the Nitride commit and source archive SHA
from [`../voice/vault/Dockerfile`](../voice/vault/Dockerfile), the single shared
pin for local and server deployment. Download
`https://codeload.github.com/0xTomDaniel/nitride-cli/tar.gz/<NITRIDE_COMMIT>`, verify
its SHA-256 before extraction, then install only
`nitride-cli-<NITRIDE_COMMIT>/skills/nitride` as
`<vault>/.agents/skills/nitride`. No npm install or build is needed.

For upgrades, compare the current package with the prior pin, preserve any local
changes for reconciliation, and back it up outside the vault. Stage and verify
the complete replacement before switching directories; do not merge new files
into an old package and leave stale files behind. Compare the installed package
with the verified archive after Syncthing settles. This is a pinned upstream
package: upgrade it deliberately, rather than editing its generated bundle.

Agents can invoke the bundle directly through Node. Optionally link a local
PATH entry such as `~/.local/bin/nitride` to the absolute installed
`<vault>/.agents/skills/nitride/scripts/nitride.mjs`; this machine-specific link
stays outside source and is not synchronized to other machines.

Reconcile this repo's shared `AGENTS.md`, skills and the
[local Adapter fragment](AGENTS.fragment.md) into the vault's canonical files.
Replace obsolete native-CLI instructions for the same scope; preserve owner
context and unrelated guidance. The fragment is input to the existing vault
`AGENTS.md`, not a second always-loaded policy file. Do not copy an entire skill
tree over owner-customized content.

Deploy both Obsidian validator files (`note_metadata.py`, `validate_notes.py`)
from the same Exo revision together, preserving the existing `status_policy.py`
dependency. Follow the backup, reconciliation and preflight requirements in the
[server recipe](../voice/vault/README.md#pinned-nitride-retrieval). These helpers
remain in the `obsidian` skill even when native CLI use is disabled.

## Pi defaults

Back up and merge these fields into the private `~/.pi/agent/settings.json`;
preserve its other settings, extensions and credentials:

```json
{
  "defaultProvider": "openai-codex",
  "defaultModel": "gpt-6-astra",
  "defaultThinkingLevel": "low"
}
```

This is Pi's native JSON configuration, not a new Exo configuration authority.
Verify the exact model exists with `pi --offline --list-models gpt-6-astra`.
Existing authentication must already work. Launch a fresh session from the
vault; project settings, explicit flags and resumed sessions can override the
global default. No session reset is necessary.

## Disable native Obsidian CLI on the Mac

Disable the CLI setting in the Obsidian desktop application and remove its CLI
PATH registration from the shell startup file where it was installed. Keep the
application itself: its executable also hosts the GUI and is not a standalone
CLI package to delete. For a direct local-settings-file update, close the application first and reopen
it afterward. Preserve vault registrations and all unrelated preferences.

An existing terminal may retain the old PATH. Open a fresh login shell and check
`command -v obsidian` finds nothing. If a parent application still supplies the
old entry, remove `/Applications/Obsidian.app/Contents/MacOS` from the inherited
PATH during shell initialization too. Confirm the app's CLI setting remains off
after restart. The Adapter forbids absolute-path fallback as well.

Nitride provides supported Base queries, not note-writing or desktop parity.
Use filesystem tools plus validation for edits, and report unsupported app
operations. Do not keep obsolete instructions that require `obsidian daily:path`
or native property readback as a prerequisite for ordinary note work.

## Acceptance and rollback

- In a fresh Pi session, inspect RPC `get_state`: model `gpt-6-astra`, thinking
  `low`; inspect `get_commands` for one `skill:nitride` from canonical source.
  Complete a small fresh model request; configuration alone does not prove access.
- Check Claude's projection targets and instruction discovery. Codex uses its
  native canonical discovery; do not create a duplicate tree to make it visible.
- Run the actual date preflight, then the vault's named task and reminder views
  through the installed bundle, using the current owner date and timezone.
  Check errors and preserve source membership. Do not publish personal results.
- Verify synchronized instructions, package hashes and hidden links on receiving
  devices. Server images still carry their own pinned `/opt/nitride` package;
  syncing a vault package does not rebuild a server image. Both must follow the
  same reviewed pin when upgrading.

Restore affected settings/files from private backups if needed. Remove only
links created by this setup after verifying their targets; preserve notes,
owner edits, login state and sessions. Re-enabling native CLI use requires an
explicit owner decision.
