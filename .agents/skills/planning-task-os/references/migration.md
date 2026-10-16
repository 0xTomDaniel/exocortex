# Task Model Migration

Use this when changing task-related schema, especially field renames such as `priority` -> `importance`.

## Source-of-truth rule

Pick one canonical source and de-duplicate toward it.

- For the planning/task operating system, prefer this skill's references as the canonical operational source.
- Retire duplicated policy notes after migration; keep only temporary breadcrumbs if truly needed during the cutover.
- Avoid maintaining two full prose descriptions of the same task-model rules.

## Migration workflow

1. **Discover all affected artifacts first**
   - Search task notes, runtime surfaces, policies, structured trackers/views, and skills.
   - Include both metadata fields and prose references.

2. **Decide the canonical semantics before editing**
   - Confirm the destination field name and its exact meaning.
   - For this vault, prefer:
     - `importance` = how much it matters
     - `due` = urgency pressure
     - `review_on` = resurfacing
     - `status` = commitment state
   - If the migration also changes the allowed values for `importance`, treat the field rename and the value-taxonomy recalibration as distinct sub-steps so they can be validated separately.

3. **Update one representative task first**
   - Test the new field on a small sample before mass edits.
   - Re-read it and verify query behavior.

4. **Update dependent artifacts intentionally**
   - Task runtime surfaces
   - Skill references that define or consume task properties
   - Structured trackers / filters / formulas / views
   - Any dashboards or review notes that rely on the old field name

5. **Migrate task notes in batches**
   - Prefer controlled edits over one giant blind replace.
   - Watch for mixed semantics where prose still talks about `priority` as a blended concept.

6. **Validate the system**
   - Re-read representative tasks.
   - Re-run searches for the old field.
   - Re-query the affected structured trackers/views using the current note-system tooling.
   - Confirm that filters/views still include the intended tasks.

7. **Capture the decision**
   - Log the schema change in the current day log.
   - Update the canonical skill/policy so future work uses the new model.

## Recommended search targets

Use searches like:

```bash
rg -n '^priority:|\bpriority\b|\bimportance\b' . --glob '*.md'
```

Then validate with the system's current note/tracker tooling (for example the `obsidian` skill in this environment).

## Guardrails

- Do not leave the vault half-migrated without an explicit reason.
- Do not rename the field in tasks but forget runtime surfaces or structured trackers.
- Do not collapse importance and urgency back into one ambiguous field during migration.
- If the change is too large for one pass, create an explicit staged migration plan and leave visible breadcrumbs.
