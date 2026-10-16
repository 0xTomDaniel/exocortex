---
name: asset-assessment
description: Assess and compare investable assets—including crypto tokens, stocks, private companies, commodities, currencies, real estate, collectibles, and funds—using evidence-backed atomic checklists and canonical crypto/stock question banks across durability, value capture, valuation, risk, memetic strength, and portfolio fit. Use whenever the user asks which asset is best, highest conviction, worth buying/holding, comparatively attractive, or requests investment diligence, a watchlist ranking, token analysis, stock analysis, entry assessment, or an asset-evaluation rubric.
metadata:
  exo.category: general
---
# Asset Assessment

## Core rule

Decompose the decision into atomic, positively oriented questions; evaluate each against current evidence; preserve unknowns and conflicts; aggregate by construct and layer; then perform a documented holistic residual check. Keep asset merit, instrument value capture, entry, integrity, implementation, portfolio fit, evidence confidence, and action authorization distinct.

For every comparative conviction or recommendation:

1. Read `references/rubric.md` and `references/evaluation-protocol.md` completely.
2. For crypto/stocks, also read `references/question-bank-governance.md` and use bank v2 through its manifest/scripts. Never copy rows manually or use v1.0.0 as empirical data.
3. For numeric comparison, use `scripts/score_checklist.py`; never hand-calculate rankings. Comparative cases must predeclare layer weights and retain an overall research score alongside every component layer.
4. Distinguish analytical ranking from authorization to trade; an overall score cannot clear or override a failed/unresolved gate.

## Workflow

### 1. Define and freeze the decision

Establish the bounded candidate universe, asset/instrument subtype, exposure type, horizon, evidence cutoff, purpose (`screen`, `diligence`, or `action`), reference size, predeclared thresholds, outcome definition, constraints, and any weights.

Before personalized action, consult known holdings, liabilities, cash/runway, protected reserves, tax/custody constraints, concentration, maximum loss, and current policy. If that context is missing, stop at research/diligence.

Create the case specification:

```bash
python scripts/create_case_spec.py \
  --case-id CASE-ID \
  --decision "Decision being evaluated" \
  --purpose screen --tier core \
  --candidate 'BTC=Bitcoin|crypto|monetary|direct' \
  --candidate 'ETH=Ethereum|crypto|base_layer|direct' \
  --horizon '4 years' --planned-horizon-end 2030-09-03 \
  --evidence-cutoff 2026-09-03T23:59:59-06:00 --case-spec-author EXO \
  --output case.json
```

Complete `reference_size`, construct-keyed thresholds, weights, outcome definition, constraints, and any case-local `extensions` before evaluation. Diligence/action require `tier=full`; action also requires a non-null `proposed_position`. See `assets/case-spec.example.json`.

### 2. Assemble deterministically

Validate and build:

```bash
python scripts/validate_question_bank.py
python scripts/build_assessment_checklist.py \
  --case-spec case.json --output assessment.csv
```

The manifest explicitly routes common, class, subtype, and exposure overlays. Supported v2 categories are documented in governance. Stablecoins, derivatives, and unsupported classes must use the named alternate/dynamic route; never force category-inappropriate questions.

Use all core rows for a screen and core + deep for diligence/action. Add at most eight sequential `EXT-<CASE-ID>-NN` rows only for material case requirements. They must use isolated `ext_*` constructs, never refine bank constructs, never pool, and cannot be overridden. Scored extensions must apply to the full ranked universe; only gate or informational extensions may target an asset subset.

### 3. Evaluate atomically

For every row record:

- `applicable=YES/NO`; every `NO` needs reason and source (`bank`, `manifest`, or `evaluator`); never alter `manifest_suppressed` or mark an identity gate evaluator-`N/A`;
- `evidence_sufficient=YES/NO`;
- `verdict=YES/NO` only when evidence is sufficient;
- enter the evidence brief/reference before the verdict;
- every applicable row: nonblank `explanation`, `observed_at`, confidence, and reviewer;
- every answered row: typed `source_ref`, optional `source_digest`, optional `data_as_of`, and required `evidence_available_at` no later than the frozen cutoff;
- explicit reasons for gate/scoring overrides;
- explicit adjudication when a strict parent contradicts its primary.

Evaluate rows independently before viewing aggregates. Do not infer a verdict from reputation or another row. Trace control authorities transitively to the actual signer/governance policy, threshold and enforced delay; an immediate owner's account type or empty storage does not establish who can authorize it. Verify derived addresses and intermediary controls before declaring unilateral power. Prefer primary documents, audited/on-chain records, legal title, and transparent methodology; label dashboards, marketing, social claims, and inference.

Finalization derives `temporal_mode`: prospective only when every used item was observed by the cutoff; otherwise retrospective. Claimed availability and reference truth remain evaluator assertions unless externally archived/content-addressed. `UNKNOWN` means insufficient evidence. Do not convert it to `NO` or `YES`; it receives zero pending credit only in conservative statistics and may block a later purpose.

### 4. Score by construct and layer

```bash
python scripts/score_checklist.py assessment.csv \
  --case-spec case.json \
  --rank-by composite \
  --output results.json --summary-csv summary.csv
```

Questions linked by strict refinement produce one construct result. There is no voting: the effective primary controls unless a strict-parent `NO` logically entails failure or creates a recorded conflict. Informational rows do not affect denominators.

Report separately:

- merit: durability, value capture, meme/cultural capital;
- entry: valuation and market structure;
- integrity: security, control, and legal claim;
- implementation;
- portfolio fit;
- derived evidence coverage/conflicts;
- stage-gate status and authorization ceiling.

A gate row is unscored. Use a separate scored sibling when a factor needs both a minimum floor and graded merit. In every comparative case, freeze explicit cross-layer weights ex ante and report the resulting **overall research score** for prioritization, while always displaying component layers, evidence coverage, gate state, and authorization ceiling beside it. The overall score is a summary—not a substitute for the layers—and cannot average away a failed/unresolved gate. If the decision does not justify particular weights, stop and select a documented neutral weighting rather than silently omitting the composite. Memetic strength is first-class merit but cannot bypass a gate.

When the user requests token/asset judgment before portfolio planning, freeze a token-only case covering merit, entry, integrity, token-level legal access, and market structure. Explicitly exclude personal holdings, capital, concentration, custody choice, tax treatment, maximum loss, implementation, and portfolio fit; do not request those inputs or let their absence reduce token-level coverage. Evaluate them later in a separate implementation/portfolio case.

### 5. Apply staged authorization

- **Screen:** identity must pass before scoring. Integrity failures sort as avoid; unresolved integrity remains visible and cannot authorize diligence/action.
- **Diligence:** identity through diligence and the diligence evidence threshold must pass.
- **Action:** every enforced stage, evidence threshold, portfolio policy, and implementation route must pass. A stage absent by bank design is `NOT_APPLICABLE`; an enforced stage with existing gates marked `N/A` remains unresolved.

Authorization can never exceed the case purpose. A failed gate cannot be averaged away. A holistic residual may downgrade a mechanical result but may never upgrade past a failed or unresolved gate.

### 6. Run independent review when required

The canonical policy is `assets/independent-review.toml`: an independent review requires at least **two distinct models**. Defaults are:

1. `openai-codex/gpt-6-astra:high`
2. `anthropic/claude-fable-5.1:high`

Evaluators work blind from the same frozen case specification and do not inspect each other's rows before finalizing. Blindness is a process requirement, not runtime-verifiable. Finalize the first record as `primary` and the other as `independent_review`; asserted evaluator and model identities are assessment-hash-bound but not provider-attested. Agreement is not truth: compare evidence references, effective constructs, and gate stages, and adjudicate factual, definitional, temporal, or weighting disagreements. Independent-review records never enter pooled performance statistics. A later adjudicated record may use a TOML-configured human producer ID and supersede the primary; adjudications do not count toward the two-model review requirement.

For action cases, no result is independently review-complete until this passes:

```bash
python scripts/verify_independent_review.py \
  --ledger assessment-ledger.csv \
  --case-spec-hash CASE_SPEC_SHA256
```

### 7. Perform the holistic residual

After aggregation, ask:

- Is a decisive consideration missing?
- Did decomposition become too strict for a holistic factor?
- Does the result conflict with base rates, economic logic, or lived evidence?
- Could the asset pass while remaining a bad instrument, entry, implementation, or portfolio choice?
- Are nonlinear/correlated failures hidden by atomic scoring?

Do not silently override the checklist. Record the failed assumption and add/revise only the relevant future question.

### 8. Finalize and verify

Iterate in draft. Finalize only when evidence and thresholds are complete for the declared purpose, or when intentionally freezing an explicitly labeled incomplete empirical pilot. A finalized hash proves record immutability, not substantive diligence completeness:

```bash
python scripts/finalize_assessment.py assessment.csv \
  --case-spec case.json \
  --record assessment-record.json \
  --ledger assessment-ledger.csv \
  --evaluator EXO \
  --model-id openai-codex/gpt-6-astra:high \
  --record-role primary

python scripts/verify_case.py \
  --case-spec case.json --checklist assessment.csv \
  --record assessment-record.json
```

Finalization binds bank/runtime → case spec → checklist → frozen assessment record, including evaluator, model, record role, review-config hash, and supersession lineage, and appends a linked ledger row. Never describe a finalized record as “completed diligence” when purpose status is unresolved/failed or coverage is below the declared threshold; call it an incomplete pilot or partial pass and name the missing evidence lanes. Corrections create a new hash/revision; never rewrite finalized history. Revision finalization requires `--supersedes` plus `--outcomes` so leakage quarantine can traverse the chain. Hashes are only tamper-evident when anchored outside the evaluator's unilateral control.

### 9. Resolve outcomes and improve cautiously

Record outcomes separately using `assets/outcomes.example.csv`, keyed by `(assessment_hash, asset)` and matching the predeclared definition/horizon. Supply one matched row per asset for a multi-asset resolved assessment. Then analyze:

```bash
python scripts/analyze_question_history.py \
  --ledger assessment-ledger.csv \
  --outcomes outcomes.csv \
  --output diagnostics.json
```

The analyzer verifies the ledger chain and recomputes file, case, checklist, runtime, assessment, temporal-mode, and supersession data before admission; it derives post-outcome quarantine transitively, excludes retrospective outcomes by default, excludes `EXT-*` and independent-review rows from pooling, and reports multi-model review coverage, raw/construct/stage disagreement, shared-source overlap, and repeated boilerplate. Use coverage, entropy, evidence/verdict disagreement, refinement conflicts, within-class pair associations, gate false negatives, and prospective outcomes as review prompts—not automatic bank edits. Small samples may repair wording/applicability; they do not justify predictive retirement, tiering, or weights.

## Conclusion standard

Report layer results, failed/unresolved gates, evidence coverage, verified facts versus inference, strongest bear case, falsifiers, holistic residuals, authorization ceiling, confidence, and reopen conditions. Present the token-by-token results table directly in chat rather than only summarizing it or pointing to a saved artifact. State clearly whether the work is a completed purpose-grade assessment, an incomplete empirical pilot, or a gate-first pass. Use statuses such as `research`, `watch`, `eligible for diligence`, `policy-compliant bounded action`, `hold`, `avoid`, or `insufficient evidence`.

When the user authorizes coverage closure, own completion rather than inventorying remaining work. Continue evidence retrieval and evaluation until the declared coverage targets are met; an externally researchable gap is work to execute, not a stopping condition. A gap register, failed gate, independent review, or future task does not substitute for the requested deliverable. If genuine evidence limits prevent completion, document attempted primary and substitute sources and distinguish blocked, inherently unobservable, and user-input-dependent gaps; never pad verdicts or change thresholds to manufacture coverage. Only genuinely necessary user input warrants asking the user to resume an already authorized investigation.

Never turn protocol admiration, mention frequency, momentum, or a powerful meme into automatic buy conviction.
