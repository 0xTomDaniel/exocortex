# Linking Notes & Files Reference (Obsidian CLI skill)

Use this reference when users ask about internal links, aliases, embeds, headings/blocks, or link display behavior.

## Source coverage

Derived from Obsidian Help pages:
- Linking notes and files/Internal links (`/links` permalink)
- Linking notes and files/Aliases
- Linking notes and files/Embed files

## Core model

- Internal links connect notes/attachments/files in the vault.
- Obsidian supports both wikilinks and markdown links.
- Embeds are internal links prefixed with `!`.
- Aliases are reusable alternate names stored in frontmatter.

## Link formats and interoperability

- Wikilink: `[[Note]]`, `[[Note#Heading]]`, `[[Note#^block-id]]`
- Markdown: `[Label](Note%20Name.md)` (URL-encode paths, e.g., spaces as `%20`)
- Obsidian can auto-update internal links on file rename (Files & Links setting).
- If interoperability with non-Obsidian tools is important, prefer markdown links.

## When to use display text vs alias

- Use link display text for one-off phrasing in one location:
  - Wikilink: `[[Target|Shown text]]`
  - Markdown: `[Shown text](Target.md)`
- Use aliases for reusable alternate names across vault:
  - frontmatter list under `aliases:`

## Heading and block linking

- Heading link in same note: `[[#Heading]]`
- Heading in other note: `[[Note#Heading]]`
- Subheading chain: `[[Note#H1#H2]]`
- Block link: `[[Note#^block-id]]`
- Cross-vault heading search in link autocomplete: `[[## query]]`
- Cross-vault block search in link autocomplete: `[[^^query]]`

## Block ID guidance

- Human-readable IDs are supported: `^quote-of-the-day`
- IDs should contain letters, numbers, and dashes.
- For lists/quotes/callouts/tables, block-id placement matters; prefer explicit block boundary and verify target.
- Block refs are Obsidian-specific and may not work in other markdown tools.

## Embeds guidance

- Note embed: `![[Note]]`
- Heading/block embed: `![[Note#Heading]]`, `![[Note#^block-id]]`
- Image embed resize: `![[Image.png|300x200]]` or width-only `|300`
- PDF embed supports page/height fragments:
  - `![[File.pdf#page=3]]`
  - `![[File.pdf#height=400]]`

## Alias/property formatting rules

- Keep aliases as YAML list:

```yaml
aliases:
  - AI
  - Artificial Intelligence
```

- For internal links inside properties/lists, quote wikilinks in YAML.

## Known pitfalls

- Markdown links must be URL-encoded.
- Filenames containing certain special characters can cause link issues.
- Excluded files are deprioritized in link suggestions.
- Page preview must be enabled for hover previews.

## CLI-side recommendations for this skill

When helping with link issues:
1. Confirm target path/name resolution (`file=` vs `path=`) and naming collisions.
2. Validate whether user needs alias vs display text.
3. For heading/block failures, confirm exact heading text or block-id placement.
4. For portability requirements, convert to markdown links.
