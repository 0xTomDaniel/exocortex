# Note status canon

Status expresses lifecycle, not importance, scheduling, document coverage, a
review event, or an entity's identity. This is the shared note-policy authority;
`scripts/status_policy.py` supplies its validator and comparison implementation.
Task commitment decisions remain with planning-task-os.

| Note family | Allowed status links |
|---|---|
| Tasks, projects, experiments, deals; reviews, planning/work sessions, research and assessments | `[[Todo]]`, `[[Doing]]`, `[[Waiting]]`, `[[Someday]]`, `[[Done]]`, `[[Closed]]` |
| Plans, documents, reports, worksheets, documentation | `[[Draft]]`, `[[Active]]`, `[[Closed]]` |
| Weeks, sprints, cycles, quarters, years, bonus weeks, other periods | `[[Planned]]`, `[[Active]]`, `[[Ended]]` |
| Areas, ongoing practices, habit systems, trackers, maintained portfolios/watchlists and queues | `[[Active]]`, `[[Someday]]`, `[[Closed]]` |
| Books, articles, videos and learning resources | No status merely for saving; when tracking consumption, use the six work states |
| People, companies, places, products, software, family, pets; references, inspiration, quotes, principles, preferences, reflections, historical records and taxonomy definitions | No generic status; retain specific facts in appropriate properties or history |

Specializations inherit their family: Investment Plan is a plan, Weekly Review
is a review, Asset Assessment is an assessment, and Historical Project retains
the project lifecycle (age alone does not prove completion). Research Notes and
source notes describe evidence; Research tracks the finite research workflow.
Dashboards describe views rather than commitments. New/ambiguous types require
classification in the canonical type mapping before accepting a status; do not
silently create a new family or permit an arbitrary value.

## Meanings

- Todo: committed, not started. Doing: finite work underway.
- Waiting: a commitment waiting on a dependency; retain its follow-up date.
- Someday: preserved possibility, not a current commitment. Later and Incubating
  are legacy parking names, not additional canonical states.
- Done: intended outcome achieved. Closed: commitment ended without completion,
  or a document/ongoing practice retired; record an explicit `resolution`.
- Draft: not yet adopted as the governing document. Active: currently governing
  document, ongoing practice, or current period.
- Planned: a future period. Ended: the period elapsed; this does not complete its
  work or review. Use period dates and retain the separate review workflow.

## Writes, reads and cleanup

Write one quoted wikilink, e.g. `status: "[[Todo]]"`. Missing status is permitted
for capture and descriptive notes and never means terminal. Validate candidate
and saved notes with `uv run scripts/validate_notes.py <path>`.

On reads, exact plain canonical names and linked names have identical meaning.
Explicit legacy aliases Later/Incubating → Someday, In Progress/In progress →
Doing, and Reading → Doing are recognized. Other capitalization, qualified or
display-aliased links and unknown values require correction; do not silently
guess a target or hide the note. On an authorized maintenance pass use
`--fix-status --backup-dir <private-directory-outside-vault>` for lossless,
backed-up representation fixes. It intentionally leaves Later for evidence
review: a committed task scheduled for later remains Todo/Doing/Waiting, not
Someday. Preserve real deadlines and review dates; do not manufacture capacity
by demoting commitments to fit the active-task cap.

Exploring and Trying Out describe an activity; determine commitment separately.
Queued and Want to Read become Todo only with commitment evidence, otherwise
Someday. Reviewed, Studied, Filed and Saved describe events/results. Preserve
their history instead of inventing permanent suppression. Complete and Research
Complete become Done only after checking the intended scope. Missed, partial
diligence and Reduced Review describe outcomes/coverage; preserve those facts.
Never rewrite preserved source quotations or claim research completion authorizes
an action. Keep migration evidence and original bytes in private audit backups;
use dated note history when a semantic change needs explanation.

## Retrieval

Only Done and Closed are terminal exclusions for active task and dated-reminder
views, in both plain and linked representation. Reviewed and Ended do not hide
due reminders. Missing/unknown status remains eligible when its dates match;
report validation debt separately from attention results. A reminder on a person
or reference needs no task conversion or status.

Saved Base filters encode this policy explicitly. Include plain equivalents in
positive membership tests too (Todo/Doing capacity and Someday exclusions), and
approved parking aliases where applicable. Nitride executes those filters
literally; it must not embed Exo lifecycle policy in its generic evaluator.
Filesystem property filtering uses the same status comparisons. Keep the date,
scope and deduplication contract unchanged when repairing status filters.

Audit saved standalone comparisons with
`uv run scripts/repair_status_filters.py <view.base>`. Add `--attention` only for
an attention surface whose Reviewed exclusion must be removed. To apply, add
`--apply --backup-dir <private-directory-outside-vault>`, then execute the affected
views. The helper leaves compound/custom predicates unchanged for explicit
inspection and rejects anchored/aliased Bases without writing. It edits only
targeted scalar spans, preserving unrelated YAML values, comments and line endings;
it is not a general Base optimizer or a commitment decision maker.

This contract covers note frontmatter `status` only, not machine/runtime job
fields or private workflow-progress JSON.
