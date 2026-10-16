# Atomic Evaluation Protocol

## Contents

- [Research basis](#research-basis)
- [Adaptation to assets](#adaptation-to-assets)
- [Checklist-construction standard](#checklist-construction-standard)
- [Aggregation](#aggregation)
- [Question-quality audit](#question-quality-audit)
- [Targeted refinement loop](#targeted-refinement-loop)
- [Checklist-based comparison / Best-of-N](#checklist-based-comparison--best-of-n)
- [Repeated-use calibration](#repeated-use-calibration)
- [Independent review and disagreement](#independent-review-and-disagreement)
- [Holistic residual check](#holistic-residual-check)

## Research basis

This protocol adapts two LLM-evaluation methods to high-stakes asset assessment rather than copying them mechanically.

### TICK / STICK

Jonathan Cook et al., [“TICKing All the Boxes: Generated Checklists Improve LLM Evaluation and Generation”](https://arxiv.org/abs/2410.03608) (2024):

- Generate an instruction-specific checklist covering explicit requirements and implicit domain criteria.
- Phrase precise, minimally overlapping questions so `YES` means the requirement is satisfied.
- Explicitly answer each question and aggregate the answers; merely showing a checklist before holistic scoring performed worse.
- Use failed questions as targeted self-refinement feedback and preserve passed requirements.
- Checklist-based Best-of-N selection outperformed direct self-scoring in the reported experiments.
- Checklists improved human inter-annotator agreement, but human evaluators still needed holistic judgment because a generated checklist can omit a decisive issue.
- Limitations: extra inference cost, propagated evaluator bias, and no universal advantage for trivial evaluations.

Reported results include exact LLM/human preference agreement improving from 46.4% under direct scoring to 52.2% with TICK; STICK also improved self-refinement and Best-of-N performance on the studied benchmarks. These empirical results concern LLM output evaluation, not investment performance.

### BinEval

Sangwoo Cho et al., [“Ask, Don’t Judge: Binary Questions for Interpretable LLM Evaluation and Self-Improvement”](https://arxiv.org/abs/2606.27226) (2026):

- First summarize task requirements, then decompose each into atomic binary questions grouped by dimension.
- Answer questions independently and retain a short explanation for every verdict.
- Aggregate question verdicts into interpretable per-dimension scores rather than relying on an opaque holistic score.
- Atomic decomposition helps through complexity reduction, variance reduction by aggregation, and broader failure-mode coverage.
- Use question-level disagreements between evaluators to extract deduplicated lessons and update only relevant instructions.
- Regenerate questions after a material rubric update.
- Limitations: results depend on question quality; linear pass-rate aggregation need not equal overall quality; subjective criteria can be harmed by over-decomposition; repeated updates can bloat prompts and degrade results; prompting cannot repair missing computational capability. Unavailable external evidence is an investment-domain extrapolation, not a limitation established by BinEval.

The paper reports strong correlations with human evaluation in its language-generation benchmarks, especially factual consistency. Those results do not validate an asset-ranking model; they justify the evaluation structure used here.

## Adaptation to assets

Asset analysis differs from evaluating a completed text:

- Evidence is often missing, delayed, contradictory, reflexive, or strategically disclosed.
- Criteria have unequal importance and non-linear interactions.
- A single failed security, title, solvency, legal, governance, liquidity, or protected-capital gate may dominate dozens of favorable answers.
- Some dimensions—memetic durability, management quality, portfolio fit, and expected return—retain irreducibly holistic components.
- The output can influence consequential financial action.

Therefore preserve unknowns and contradictions, separate merit/entry/integrity/implementation/fit/evidence layers, enforce purpose-specific staged gates, and retain a documented holistic residual check.

## Checklist-construction standard

### Step A — Requirement summary

Create and freeze the case specification before evaluating. Include:

1. decision, purpose, horizon, and planned outcome date;
2. bounded candidate universe with class, subtype, and exact exposure;
3. reference size and proposed position, when relevant;
4. explicit user constraints and protected-capital policy;
5. evidence cutoff and required sources;
6. construct-keyed thresholds and any within-layer weights;
7. known lived evidence and disqualifiers;
8. the prospective outcome definition;
9. the case-spec author and any case-local extension rows.

Build the checklist only from this hashed specification. Changing a predeclared input creates a new case-spec hash.

### Step B — Canonical baseline and atomic decomposition

For crypto and stocks, follow `question-bank-governance.md` and `bank-manifest.json`. Assemble common → class → one subtype → one exposure with `build_assessment_checklist.py`; never copy/select rows by hand. Use core for screening and core + deep for diligence/action. Preserve IDs, construct lineage, bank and runtime version/hashes, case-spec hash, and checklist hash. Add at most eight case-local `EXT-*` questions only for material omissions, declare them in the case spec before evidence, and let build hash-bind them. Scored extensions must apply across the full ranked universe; gate/informational extensions may target subsets. Extensions use isolated constructs and never pool. For unsupported classes or routes, use the explicitly named dynamic/alternate procedure.

For every uncovered applicable criterion, create the smallest useful number of independent questions. Split a question if separate evidence could produce different answers.

Bad:
- “Does the protocol have strong adoption, revenue, token value capture, and security?”

Good:
- “Has non-incentivized active usage remained stable or grown over the chosen observation period?”
- “Does the protocol retain positive revenue after the costs included in the stated methodology?”
- “Does protocol success create an enforceable or automatic economic benefit for this token?”
- “Has the protocol avoided an unresolved event capable of permanently impairing holders?”

Question requirements:

- one facet;
- `YES` is favorable;
- precise subject, measurement, and horizon where available;
- no double negatives;
- little semantic overlap with neighboring questions;
- evidence requirement stated;
- failure example where interpretation could drift;
- no questions added merely to increase apparent completeness.

### Step C — Applicability and evidence gates

For each question record:

- `Applicable = YES/NO`; every `NO` requires a reason and `bank|manifest|evaluator` source.
- `Evidence sufficient = YES/NO`; sufficient means current and decision-relevant.
- `Verdict = YES/NO`; answer only when evidence is sufficient.
- explanation, typed source reference, optional source digest, optional data-as-of date, evidence-availability date, observation timestamp, confidence, and reviewer.
- reasons for any gate/scoring override.
- adjudication and reason for a strict-parent/primary conflict.

Create the evidence brief/reference before entering the verdict. Finalization can enforce presence and chronology fields, not the evaluator's mental ordering. Do not convert missing evidence to either verdict. Unknown and conflict may block a later purpose.

A favorable verdict must establish **every required component** of a compound criterion or frozen threshold; evidence for one convenient component cannot stand in for the whole test. Preserve distinctions between specified capacity, measured use, and forecast growth. Likewise validate scenario meaning before crediting its arithmetic: a historical minimum that is not genuinely adverse cannot satisfy a bear test or support a usable probability-weighted forecast. Coverage targets never relax these evidentiary requirements.

## Aggregation

Aggregate scored constructs, not rows. Strict refinements produce one effective-primary construct verdict under the governance resolution rules. Informational constructs and N/A rows do not enter denominators.

For each dimension:

- `pass rate = YES / (YES + NO)`;
- `coverage = (YES + NO) / applicable constructs`;
- `conservative = YES / applicable constructs`.

`UNKNOWN` and `CONFLICT` receive zero pending credit only in the conservative statistic. Report them separately.

Report six layers separately: merit, entry, integrity, implementation, fit, and derived evidence. Comparative cases must also report a deterministic **overall research score** using explicit layer weights frozen in the case spec; retain every component output, evidence coverage, gate state, and authorization ceiling beside it. Do not infer or tune weights after seeing results. The composite supports comparison and prioritization only: it cannot average away a failed/unresolved gate or authorize an action.

### Gates

Every gate is unscored. If the same factor needs a graded measure, create a separate scored sibling construct. Stages are identity, integrity, eligibility, diligence, implementation, policy, and script-derived evidence. Enforce them by case purpose exactly as governance/manifest specify. Identity unknown blocks scoring; a screen may rank unresolved integrity with a warning but cannot authorize a higher purpose. Diligence/action require the full tier, action requires a non-null proposed position, a stage absent from the assembled bank is `NOT_APPLICABLE`, and an enforced stage whose existing gates are all `N/A` is unresolved rather than passed. A failed gate cannot be averaged away.

## Question-quality audit

Before accepting results, ask:

- Stability: Are bank, runtime, case-spec, checklist, finalized-assessment, and linked-ledger hashes retained?
- Assembly: Was every selected-tier row evaluated or visibly marked N/A with source/reason?
- Coverage: Is every applicable layer/dimension represented?
- Atomicity: Could any question contain two independently answerable claims?
- Polarity: Does `YES` always mean favorable?
- Constructs: Does every shared construct represent a genuine strict logical refinement rather than correlation?
- Independence: Does one fact earn more than one scored construct?
- Specificity: Could two careful evaluators interpret the question differently?
- Answerability: Is the required evidence obtainable and current?
- Calibration: Does a `NO` represent a meaningful failure rather than perfectionism?
- Holism: Was a soft, gestalt judgment mistakenly converted into exhaustive hard requirements?
- Gaming: Could an asset pass while violating the economic purpose of the criterion?
- Category fit: Are monetary assets, operating companies, protocols, real estate, and collectibles being judged with appropriate evidence?

If questions are duplicative, assign a valid strict-refinement chain or consolidate them. If a broad question hides distinct failure modes, split it. Do not optimize for checklist length; optimize for decision-relevant coverage, low overlap, and usable evidence.

## Targeted refinement loop

After the first evaluation:

1. Collect every `NO`, evidence-insufficient item, gate failure, and evaluator disagreement.
2. Classify each as:
   - real asset/thesis failure;
   - missing evidence;
   - stale or contradictory evidence;
   - calculation/tool need;
   - malformed question;
   - category/weighting mistake;
   - irreducibly holistic judgment.
3. Deduplicate lessons.
4. Change only the affected question, evidence-gathering step, or conclusion.
5. Preserve passed questions unless new evidence contradicts them.
6. Regenerate affected questions after a material rubric change.
7. Re-evaluate once by default.
8. Stop if no material verdict changes, no new evidence is available, or instructions begin to duplicate/compete.

Do not respond to a data or calculation limitation with more prose instructions. Use a deterministic calculation, retrieve better evidence, or mark the answer unknown.

## Checklist-based comparison / Best-of-N

When multiple conclusions or actions are genuinely plausible:

1. freeze the questions, gates, evidence packet, and any weights before comparing candidates;
2. generate materially distinct candidates, such as `avoid`, `watch`, `bounded tranche`, alternative portfolio roles, or rival theses—not cosmetic rewrites;
3. evaluate each candidate against the same checklist;
4. reject candidates that fail a gate;
5. compare dimension results, evidence coverage, and holistic residuals;
6. preserve ties on the exact pre-rounded decision statistic within the same gate/status stratum; use alphabetical order only as a non-substantive display rule.

Do not allow each candidate to generate its own favorable rubric. Checklist-based selection improves consistency; it does not create evidence or guarantee the economically correct choice.

## Repeated-use calibration

Analyze only finalized, version-compatible, non-quarantined assessments from the ledger after recomputing the file, assessment metadata, temporal mode, supersession, and complete hash chain. Exclude retrospective records from outcome-keyed statistics by default. Inspect applicability/coverage, entropy, evidence and verdict disagreement, strict-refinement conflicts, pair associations, gate false negatives, and prospectively resolved outcomes.

Outcome rows must reference `(finalized assessment hash, asset)` and the case spec's predeclared definition/horizon; multi-asset outcome sets must match the assessed assets exactly. Never attach outcomes to a rewritten assessment. Corrections create linked revisions; post-outcome revisions are excluded from outcome association by default.

Use diagnostics to propose—not automatically execute—splits, merges, wording/source changes, or retirement. Small samples support clarification only. Predictive changes require prospective definitions, chronological holdouts, class/subtype stratification, independent review, and enough adverse cases. Never rewrite historical verdicts.

## Independent review and disagreement

For every independent review, use at least two distinct models under `assets/independent-review.toml`; defaults are GPT-6 Astra high and Claude Fable 5.1 high. Give models the same frozen case spec and keep their work blind until both finalize. Compare raw verdicts, effective constructs, gate stages, and source-reference overlap; do not optimize for agreement or let independent-review records double-count in pooled statistics. Action review is incomplete until `verify_independent_review.py` passes.

For each disagreement:

1. identify whether the difference is factual, definitional, temporal, weighting-related, or risk-tolerance-related;
2. retrieve decisive evidence when possible;
3. revise the question if interpretation caused the disagreement;
4. leave the item conflicted if evidence does not resolve it;
5. do not average incompatible judgments into false consensus.

## Holistic residual check

Checklist results inform rather than replace judgment. After atomic evaluation, separately document:

- omitted decisive consideration;
- base-rate conflict;
- interaction among individually acceptable risks;
- narrative coherence of the economic mechanism;
- mismatch between instrument and underlying success;
- scenario where most questions pass but permanent impairment remains likely;
- mismatch with the user's actual goals or protected-capital constraints.

If this changes the conclusion, explain exactly which checklist assumption failed and update the checklist for future evaluations. Do not use “holistic judgment” as an unexplained override.
