# Canonical Question-Bank Governance

## Purpose

Use stable binary questions to accumulate evidence about question quality without confusing analyst effort with asset merit. Bank v2.0.0 is the first empirical baseline. Version 1.0.0 is preserved under `versions/1.0.0/` as `draft-invalidated` and must never be pooled.

The bank is an evaluation instrument—not an oracle, investment policy, or security boundary.

## Architecture

Read `bank-manifest.json` as the machine-readable authority for:

- bank version/hash, runtime version/hash, audit-artifact hashes, and file hashes;
- the fixed 18 factors;
- dimension→layer mapping;
- legal class/subtype/exposure assemblies;
- staged gates and purpose-specific evidence thresholds;
- version comparability and unsupported routes.

Assembly hierarchy:

`common → class → exactly one subtype → exactly one exposure`

Supported v2 routes:

- crypto subtype: `monetary`, `base_layer`, `protocol_token`, or `other`;
- crypto exposure: `direct`, `wrapped`, or `yield_position`, only in manifest-listed combinations;
- stock subtype: `operating_company`, `financial`, or `other`; exposure is `direct`.

Stablecoins and derivatives are not forced through the appreciation bank. Stablecoins require a separate par-preservation/outcome family. Unsupported assets use the dynamic rubric procedure and case-specific `EXT-*` questions.

## Layers and dimensions

For comparative cases, report a predeclared overall research composite alongside—not instead of—the separate layers, coverage, and gate states.

| Layer | Dimensions | Meaning |
|---|---|---|
| merit | `durability`, `value_capture`, `meme_cultural_capital` | Underlying and instrument quality |
| entry | `valuation`, `market_structure` | Price, catalysts, positioning, and market liquidity |
| integrity | `security`, `control`, `legal_claim` | Instrument-level survivability and rights |
| implementation | `implementation` | Custody, venue, bridge, settlement, and proposed-position exit |
| fit | `portfolio_fit` | Role, concentration, protected capital, tax, and burden |
| evidence | derived only | Coverage, conflicts, provenance, and unresolved gates |

Weights live inside the frozen case specification and apply within layers. A cross-layer composite requires explicit layer weights and must still display every component layer. Memetic strength is first-class within merit; it never bypasses a gate.

## Constructs and refinements

Score constructs, not raw question rows.

- Every row has `construct_id`.
- A more-specific row may share a construct only through explicit `parent_question_id` and `relation_to_parent=strict_refinement`.
- In every legal assembly, a construct must form one acyclic root→leaf path.
- Semantic entailment is a human-review obligation; structural validation cannot prove it.
- The highest-specificity applicable row is the effective primary.
- Generic corroborating diagnostics use separate informational constructs (`gate=NO`, `scored=NO`) and never affect denominators.
- Gate constructs contain one row only.

Construct resolution:

1. Primary `NO` → construct `NO`.
2. Primary `YES`, no answered parent `NO` → `YES`.
3. Primary `YES` plus parent `NO` → `CONFLICT` until `primary_upheld` or `supporting_upheld` is recorded with a reason.
4. Primary unknown plus strict-parent `NO` → `NO` by `parent_entailment`.
5. Primary unknown otherwise → `UNKNOWN`.
6. Parent `YES` never upgrades an unknown primary.

Pass rate is `YES / (YES + NO)` over applicable scored constructs. Coverage is `(YES + NO) / applicable scored constructs`. `UNKNOWN` and `CONFLICT` receive zero pending credit only in the conservative statistic; neither is relabeled as factual `NO`.

## Staged gates

A bank row is either a gate or scored, never both. To represent both a minimum floor and graded merit, use separate sibling constructs.

Stages, in order:

1. `identity`
2. `integrity`
3. `eligibility`
4. `diligence`
5. `implementation`
6. `policy`
7. `evidence` (script-derived; no question row)

Purposes:

- **screen:** identity must pass before scoring. Integrity failure sorts as avoid; unresolved integrity remains rankable only with a prominent warning. No trade authorization.
- **diligence:** requires the full tier; identity through diligence plus the diligence evidence threshold must pass.
- **action:** requires the full tier and a non-null proposed position; every enforced stage and the action evidence threshold must pass. A stage absent by bank design is `NOT_APPLICABLE`; an enforced stage whose existing gates were all marked `N/A` is unresolved, never implicitly passed. Any evaluator-sourced gate `N/A` makes that stage unresolved.

The authorization ceiling cannot exceed the case specification's requested purpose. A failed gate cannot be averaged away.

## Frozen case workflow

1. Validate the active bank.
2. Create a case specification containing the decision, purpose, horizon/end date, candidate universe, subtype/exposure, reference size, proposed position, timezone-aware evidence cutoff, construct-keyed thresholds, weights, outcome definition, constraints, case-spec author, zero-to-eight case-local extensions, bank and runtime version/hashes, and creation time.
3. Build only from the case specification. Record `case_spec_hash` and `checklist_hash`.
4. Evaluate in draft state. Every `applicable=NO` needs `applicability_reason` and `applicability_source=bank|manifest|evaluator`. Enter the evidence brief/reference before the verdict.
5. Record reasons for gate/scoring overrides and complete required provenance fields.
6. Finalize only after validation. Hash-bind evaluator, model ID, record role, review-config hash, temporal provenance, and any superseded assessment; derive temporal mode; record everything in the sidecar and ledger.
7. Attach later outcomes by `(assessment_hash, asset)` only, using the predeclared outcome definition/horizon. A multi-asset assessment needs one matched outcome row per asset when outcomes are supplied.
8. Corrections create new immutable revisions. Post-outcome revisions are quarantined from outcome analysis by default.

Hash chain:

`(bank_hash + runtime_hash + review_config_hash) → case_spec_hash → checklist_hash → assessment_hash → asset outcome`

The ledger uses linked `previous_row_hash` / `ledger_row_hash` values, and history analysis recomputes the bank, runtime, case, checklist, file, and assessment hashes before admitting a record. Hashes and timestamps are still only conventions while the evaluator can rewrite every artifact. They become tamper-evident—not tamper-proof—only when the ledger is anchored in an external append-only or version-controlled record outside the evaluator's unilateral authority.

## Identity, applicability, and overrides

- Never silently change a stable question's construct.
- `YES` always means favorable.
- `UNKNOWN` is evidence-insufficient, not `NO`.
- Manifest-suppressed rows remain visible with immutable `manifest_suppressed=YES`, manifest-sourced `N/A`, and exclusion from denominators. An evaluator cannot claim manifest provenance for an unsuppressed row.
- Identity gates cannot be evaluator-sourced `N/A`.
- A canonical default may be overridden only with a recorded reason; gate/scored overrides are forbidden on multi-row refinement constructs.
- Case-specific questions use sequential, slug-safe `EXT-<CASE-ID>-NN`, live only in the case spec, use unique parentless `ext_*` constructs, and are capped at eight. They are never canonical or pooled.
- Scored extensions must apply to the complete ranked universe. Only gate/informational extensions may target an asset subset. Extensions cannot be overridden.
- Every applicable finalized row requires explanation, reviewer, and `observed_at`; every answered row also requires typed `source_ref` and `evidence_available_at`. `data_as_of` and `source_digest` are optional.
- `evidence_available_at` is evaluator-asserted and must not exceed the cutoff. `observed_at` is verifiable against cutoff/finalization and determines prospective versus retrospective mode. Retrospective records are excluded from outcome statistics by default.

## Independent-review governance

- `assets/independent-review.toml` is the policy/configuration surface. Every independent review requires at least two distinct model IDs. The defaults are GPT-6 Astra high and Claude Fable 5.1 high.
- Models work blind from the same case-spec hash. Do not expose another evaluator's rows before finalization. Blindness is a process requirement, not something the local runtime can verify.
- Assessment-hash-bound roles are `primary`, `independent_review`, and `adjudicated`; producer/evaluator identity and supersession are also hash-bound. Model/evaluator identities are asserted and tamper-evident, not provider-attested. Finalization accepts only model IDs configured in the TOML, except that an adjudicated record may use a configured non-model producer ID such as `human`. Such IDs are forbidden for primary/review records. Review completion counts only primary and independent-review records and requires distinct configured model IDs and distinct evaluator IDs.
- Independent-review records are excluded from pooled question/outcome statistics: only the one active primary/adjudicated record per case-spec hash pools. Duplicate active primaries are excluded and flagged. An adjudicated record supersedes the primary. Agreement is not truth: diagnostics compare raw questions, effective constructs, gate stages, and shared source references.
- Action cases are not independently review-complete until `verify_independent_review.py` confirms at least two distinct models. By default the verifier enforces only purposes listed in TOML `required_for_purposes`; use `--require-all-purposes` to enforce it for screens or diligence cases too.
- A holistic residual may downgrade any result. It cannot upgrade authorization past a failed or unresolved gate; correction requires pre-evidence override or a new-evidence revision.

## Versioning and migration

- Patch: editorial/evidence clarification preserving construct and ID.
- Minor: additions/retirements with lineage and explicit comparability.
- Major: incompatible runtime or scoring-semantics change after an empirical runtime has entered use. A release candidate superseded before any empirical finalization may be recorded as non-empirical and replaced by the same final semantic version with a new runtime hash.
- Semantic rewrite, split, or merge requires new IDs and a migration relation.
- Historical assessments retain their exact bank, wording, case spec, and hashes.
- `migration-1.0.0-to-2.0.0.csv` maps every v1 row. `poolable=NO` is authoritative.
- `comparable_with` stores explicit `{bank_version, bank_hash}` tuples; `compatible_runtimes` stores explicit `{runtime_version, runtime_hash}` tuples. History analysis pools only declared tuples. `superseded_runtimes` records non-empirical release candidates that must never enter pooled history.

## Question optimization

Optimize decision usefulness—not agreement, score spread, or recent returns.

Diagnostics may inspect applicability, coverage, entropy, verdict and evidence disagreement, pair associations, refinement conflicts, gate false negatives, and prospectively resolved outcomes. Treat every diagnostic as a review prompt.

Minimum evidence conventions:

| Change | Evidence floor |
|---|---|
| Editorial/applicability clarification | One documented misreading or two repeated reviewer disagreements may justify review; no calibration claim |
| Split/merge | Pattern across roughly 20 heterogeneous cases plus back-test; new IDs |
| Core/deep re-tier | Roughly 30 answered target-class observations and demonstrated decision effect |
| Non-discrimination retirement | Roughly 50 observations across multiple windows/subtypes; gates exempt from entropy-only retirement |
| Outcome-based tier/weight change | Prospectively defined outcomes, chronological holdout, class/subtype stratification, independent review, and enough adverse cases; 50 per class is only a review floor |
| Calibration claim | At least 100 resolved outcomes and 20 adverse outcomes per class is still only a convention, not proof |

Twenty observations can expose wording and coverage problems; they do not justify predictive weighting or retirement. Preserve veto sensitivity for rare permanent impairments even when statistical discrimination is low.

## Guardrails

- Separate researched candidates from owned positions and analysis from authorization.
- Never rewrite prior verdicts or attach a later definition to an earlier outcome.
- Do not optimize solely to one model, evaluator preferences, selected winners, or short-window price returns.
- Report excluded/incomparable/quarantined assessments.
- Retain the holistic residual and explain it at the assumption/question level.
