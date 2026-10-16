# Obsidian CLI Quick Reference

Source: <https://help.obsidian.md/cli>

## Prerequisites

- Install a recent Obsidian desktop installer with CLI support.
- Enable **Settings -> General -> Command line interface**.
- Register the CLI when prompted.
- Keep Obsidian running (first CLI call can launch it).

## Invocation Modes

- Run one command directly:
```bash
obsidian help
```

- Enter interactive TUI:
```bash
obsidian
help
```

## Parameter Rules

- Use parameters as `key=value`.
- Use quotes for spaced values: `content="Hello world"`.
- Use flags as standalone switches: `open`, `overwrite`.
- Use `\n` and `\t` escape sequences for multiline content.

## Targeting Rules

- Default vault selection:
  - Current working directory vault, when terminal is inside a vault.
  - Otherwise active vault in Obsidian.
- Explicit vault targeting:
```bash
obsidian vault=Notes daily
obsidian vault="My Vault" search query="test"
```
- File targeting:
  - `file=<name>` resolves like wikilinks.
  - `path=<path>` requires exact vault-root-relative path.

## Useful Commands

- Everyday workflows:
```bash
obsidian daily
obsidian daily:append content="- [ ] Buy groceries"
obsidian search query="meeting notes"
obsidian read
obsidian tasks daily
obsidian create name="Trip to Paris" template=Travel
obsidian tags counts
obsidian diff file=README from=1 to=3
```

- Developer workflows:
```bash
obsidian devtools
obsidian plugin:reload id=my-plugin
obsidian dev:screenshot path=screenshot.png
obsidian eval code="app.vault.getFiles().length"
```

## Output Handling

- Copy output to clipboard with `--copy`:
```bash
obsidian read --copy
obsidian search query="TODO" --copy
```

- Prefer machine-friendly formats when available (`json`, `csv`, `tsv`, `md`, `paths` for supporting commands).

## Command Discovery Pattern

```bash
obsidian help
obsidian help search
obsidian help create
```

Run command help before composing longer parameter chains.
