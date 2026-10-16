# Editing & Formatting Reference (Obsidian CLI skill)

Use this reference when users ask about Obsidian syntax (`/syntax`) or editing/formatting behavior.

## Source coverage

Derived from Obsidian Help pages:
- Editing and formatting/Basic formatting syntax (`/syntax` permalink)
- Editing and formatting/Advanced formatting syntax
- Editing and formatting/Obsidian Flavored Markdown
- Editing and formatting/Properties
- Editing and formatting/Attachments
- Editing and formatting/Callouts
- Editing and formatting/Tags
- Editing and formatting/Views and editing mode
- Editing and formatting/Editing shortcuts
- Editing and formatting/Multiple cursors
- Editing and formatting/Folding
- Editing and formatting/Embed web pages
- Editing and formatting/HTML content

## Core mental model

- Obsidian editing is Markdown-first with Obsidian-specific extensions (wikilinks, embeds, callouts, etc.).
- Reading vs Editing are separate views; Live Preview vs Source are editing modes.
- Properties are structured YAML/JSON metadata, not a place for rich Markdown formatting.

## Syntax quick decisions

- Use **Basic formatting** for paragraphs, headings, emphasis, links, lists, tasks, code fences, footnotes, comments, escapes.
- Use **Advanced formatting** for tables, Mermaid diagrams, and MathJax.
- Use **Obsidian Flavored Markdown** rules when behavior differs from generic Markdown tools.

## High-value gotchas

- Markdown inside HTML blocks is not rendered as Markdown.
- HTML blocks must be self-contained (blank lines can break block behavior).
- In tables, escape `|` as `\|` when needed (aliases/image size syntax).
- Inline footnotes render in Reading view, not Live Preview.
- Internal links in property values should be quoted in YAML, especially in lists.

## Properties: operational guidance

- Prefer frontmatter for machine-readable metadata: status, dates, tags, links, numbers.
- Keep types consistent across vault (`text`, `list`, `number`, `checkbox`, `date`, `datetime`, `tags`).
- Use YAML list format for multi-values; avoid comma-separated strings in one scalar.
- Trust Obsidian canonical serialization: a single-value list-typed property may appear as a quoted scalar in YAML while remaining list-typed in Obsidian.
- `tags` property is special and should be a list.
- Date format: `YYYY-MM-DD`; datetime format: `YYYY-MM-DDTHH:mm:ss`.

## Editing behavior guidance

- Reading view: clean rendered output.
- Live Preview: mostly rendered while editing; syntax appears when cursor enters formatted region.
- Source mode: raw Markdown, best for exact control and troubleshooting.
- `Ctrl/Cmd+E` toggles reading/editing flow in common setups.

## Formatting/structure tools

- Use callouts for side information and warnings (`> [!type]`).
- Use foldable callouts with `+`/`-` after type.
- Use heading/list folding for large notes.
- Use multiple cursors (`Alt/Option+click`) and rectangular selection (`Shift+Alt/Option+drag`) for bulk text edits.

## Attachments and embeds

- Attachments are regular vault files and can be embedded.
- Default attachment location is configurable in Files & Links settings.
- Web embeds use `<iframe ...>`; many sites require provider-specific embed URLs.
- YouTube/Twitter embeds can use external-image style markdown links.

## Tag usage guidance

- Use `#tag` inline or `tags:` property list in frontmatter.
- Nested tags (`#a/b`) are hierarchical in search/tags view.
- Tags are case-insensitive and cannot contain spaces.

## Obsidian Flavored Markdown extensions (selected)

- `[[wikilink]]`, `![[embed]]`, block refs `^id`, footnotes, comments `%% %%`, highlights `== ==`, callouts.

## CLI-side recommendations for this skill

When answering syntax/editing questions:
1. Prefer guidance aligned with the covered docs over generic Markdown assumptions.
2. Distinguish view/mode behavior (Reading vs Live Preview vs Source) when users report rendering confusion.
3. For property issues, validate YAML structure and types first.
4. For formatting bugs, check for HTML-block limitations, escaping requirements, and mode differences.
