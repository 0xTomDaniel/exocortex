# Conversation continuity evals

These are model behavior evals, separate from the fast `review_state.py` CLI
regressions. They exercise the actual repository `AGENTS.md` and normally
discoverable skill descriptions/bodies in a synthetic filesystem vault. Skill
catalogs live under each owning skill's `evals/evals.json`; the two integration
conversations here own cross-skill routing. Neither catalog nor rubric is runtime
policy. Do not link grading criteria from AGENTS.md or the skill entrypoints.

## Run

Prerequisites: authenticated local `codex` with `exec --ignore-user-config`, `uv`,
and Python 3.11+. Authentication must already exist as `CODEX_HOME/auth.json` (or
`~/.codex/auth.json`). The runner creates a temporary isolated Codex home and
symlinks only that existing auth file; it does not copy credentials into results
or change user configuration. Python helper dependencies are provisioned before
model execution from the repository lockfile (`uv sync --frozen`), including for the candidate's copied helpers:

```sh
uv run --frozen python evals/agent-continuity/run.py list
uv run --frozen python evals/agent-continuity/run.py prepare \
  --case mixed --date 2027-03-14 --output /tmp/exo-mixed-fixture
uv run --frozen python evals/agent-continuity/run.py run \
  --case mixed --date 2027-03-14 --variant alternate --repeat 3 \
  --label candidate --output /tmp/exo-mixed-candidate
```

Use a new output directory outside the repository. Outputs include generated
workspaces, transcripts, prompts, per-turn snapshots, model verification,
assertions, timings and pending grader packets; they are private runtime material
and must not be committed. `prepare` does no model work. The date is a fixed
scenario clock, explicitly provided in the fixture Adapter so historical/future
runs do not accidentally write using the host date. Repeat with another date
(including a timezone/date-boundary case) and `--variant original` to vary inputs.
The Adapter declares UTC, filesystem paths and unavailable integrations; it adds
no planning procedure or ideal answer.

`--source /path/to/old-checkout --label baseline` uses the old AGENTS.md and skills
with the same current catalog, fixture factory, model, date and wording. For an
update use a snapshot of the previous instructions, not a no-skill baseline.
Use separate output directories for each arm and repeat each arm at least three
times before describing comparative reliability. Source hashes and catalog hash
are recorded. Preserve baseline/candidate failures rather than tuning fixtures
only for one arm. A model update requires rerunning both arms.

The runner requests **gpt-6-astra / low**, then checks every new actual rollout
`turn_context`. Missing evidence, fallback or a mismatch fails the run. Only model
and effort are retained from those contexts. It never treats launch arguments as
proof. `--max-turns 1` is a bounded runner smoke, visibly marked `full_case: false`;
it does not establish the whole conversation. Each `fresh_thread` turn keeps
files but withholds prior dialogue, exercising durable recovery. It does not
simulate termination in the middle of a file write.

Exit 0 means execution/model verification and selected deterministic assertions
passed; **conversational grading is still pending**. Exit 2 means a deterministic
artifact failure; evidence is retained. Execution, dependency and model errors
exit nonzero. Missing/malformed progress is failure, not an empty all-clear.

## Grade independently

Each turn's `grading.json` starts with `status: pending_independent_review` and
null outcomes. Give an independent reviewer the user prompts, full event streams
(including tool ordering), initial notes, snapshots and that rubric. Do not give
them the author's preferred verdict. Have the reviewer fill reviewer identity,
`passed` and concrete evidence (file/turn/tool ordering), then set the status to
`reviewed`. Missing evidence is a failure or explicitly unevaluated, never a pass.
No automated model judge is implemented or implied.

Grade judgment and artifacts together. Early persistence requires checking the
write occurred *before* the first substantive planning question; an end-of-turn
snapshot alone cannot prove ordering. Discovery requires observing relevant
reads, not merely a lucky answer. Detect semantic duplicate commitments, invented
dates, stale confirmation, conflicting prose and false success claims even when
basic checks pass. Deterministic predicates cover narrow observable invariants;
they do not establish the truth of agent-written evidence or all alternate note
structures. No exact assistant wording is required.

Review both arms blind to label where practical. Report per-case/per-turn
artifact failures, rubric failures and ungraded items, denominator/repeats,
model/effort/version, partial runs and environmental failures separately. Do not
collapse pending subjective grades into an overall pass rate.

## Coverage and boundaries

- `AGENTS.md`: Mixed (greeting, tangent/commitment, fresh return, scoped choice,
  deferral) and Open (greeting, hypothetical reflection, explicit planning start,
  cancellation, continued reflection). User prompts never name a skill; actual
  discovery/routing is under test.
- `planning-rhythm-os`: persistence timing, mixed recovery, deferral/cancellation,
  exact-scope agreement and missing current reminder coverage.
- `planning-capture-os`: explicit versus hypothetical intent and existing-record
  reuse, including repeated clarification of the same commitment.
- `planning-task-os`: capacity/displacement decisions versus unresolved priority,
  no duplicate task or invented due date. Semantic reconciliation requires review.
- `obsidian`: a real duplicate-key validation error with original evidence to
  preserve, and a real dependency-unavailable interpreter. The unavailable case
  is controlled environment failure, not a fake provider response. Readback and
  truthful validation claims require inspecting actual tools.

The runner tests shared backing-agent instructions locally. It does **not** load
or execute the realtime frontend, establish deployment activation, test phone
model overrides, prove long-context reliability or force mid-write interruption.
See [the Voice protocol](voice-frontend.md) for separate, still outstanding
frontend acceptance. Phase 2 query semantics/retrieval implementations are not
part of this suite.
