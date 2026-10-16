# Asset Assessment — [case ID]

> [!warning] Runtime rule
> Generate the CSV from a frozen `case.json`; do not copy this narrative scaffold as a substitute for the canonical bank. Draft scores are analysis only. Finalized hashes are audit records, not trade authorization or security boundaries.

## Frozen decision specification

- Case ID:
- Decision:
- Purpose: screen / diligence / action
- Bank version/hash:
- Runtime version/hash:
- Case-spec hash:
- Checklist hash:
- Tier: core / full
- Candidate universe and qualifying scope:
- Class / subtype / exposure for each asset:
- Horizon and planned outcome date:
- Reference size / proposed position:
- Evidence cutoff:
- Predeclared construct thresholds:
- Within-layer weights / optional layer weights:
- Outcome definition:
- Case-spec author:
- Case-local `EXT-*` rows (maximum eight):
- Constraints and protected capital:

## Requirement summary

- Explicit requirements:
- Category-specific considerations:
- Known lived evidence:
- Known disqualifiers/contradictions:
- Required primary sources:
- Case-specific `EXT-*` additions:

## Atomic evaluation

Use `assets/assessment-checklist.csv` as the generated schema. For every row:

- `applicable=NO` requires `applicability_reason` and `applicability_source`; do not alter `manifest_suppressed` or mark identity gates evaluator-N/A.
- `evidence_sufficient=NO` leaves verdict blank.
- Enter the evidence brief/reference before the verdict; `YES` is favorable.
- Every applicable row needs an explanation, `observed_at`, and reviewer. Every answered row also needs typed `source_ref` and `evidence_available_at`; `data_as_of` and `source_digest` are optional.
- Gate/scoring overrides require reasons.
- Primary/strict-parent contradictions require explicit adjudication or remain `CONFLICT`.
- Informational constructs do not affect score or coverage.

## Construct results

| Construct | Effective primary | State | Resolved by | Support coverage | Conflict/adjudication |
|---|---|---|---|---:|---|
|  |  | YES / NO / UNKNOWN / CONFLICT / N/A |  |  |  |

## Layer results

| Layer | Dimension | YES | NO | Unknown | Conflict | N/A | Pass rate | Coverage | Conservative |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Merit | Durability |  |  |  |  |  |  |  |  |
| Merit | Value capture |  |  |  |  |  |  |  |  |
| Merit | Meme/cultural capital |  |  |  |  |  |  |  |  |
| Entry | Valuation |  |  |  |  |  |  |  |  |
| Entry | Market structure |  |  |  |  |  |  |  |  |
| Integrity | Security |  |  |  |  |  |  |  |  |
| Integrity | Control |  |  |  |  |  |  |  |  |
| Integrity | Legal claim |  |  |  |  |  |  |  |  |
| Implementation | Implementation |  |  |  |  |  |  |  |  |
| Fit | Portfolio fit |  |  |  |  |  |  |  |  |

## Stage gates and authorization

| Stage | Passed | Failed | Unresolved | Enforced for purpose? | Consequence |
|---|---:|---:|---:|---|---|
| Identity |  |  |  |  |  |
| Integrity |  |  |  |  |  |
| Eligibility |  |  |  |  |  |
| Diligence |  |  |  |  |  |
| Implementation |  |  |  |  |  |
| Policy |  |  |  |  |  |
| Evidence |  |  |  |  |  |

- Requested purpose:
- Independent-review policy: at least two distinct models; defaults are GPT-6 Astra high and Claude Fable 5.1 high.
- Assessment evaluator/model/record role:
- Temporal mode: prospective / retrospective
- Screening labels (`avoid_failed_integrity`, `unresolved_integrity`, identity block):
- Authorization ceiling:
- Failed gates:
- Unresolved gates:

## Question-quality audit

- [ ] Every selected bank row remains visible or is explicitly N/A.
- [ ] Every N/A has a reason/source, and every enforced all-N/A stage remains unresolved.
- [ ] Each question tests one facet and YES is favorable.
- [ ] Shared constructs are strict logical refinements, not merely correlated questions.
- [ ] One fact contributes at most one scored construct.
- [ ] Gate rows are unscored; graded siblings are separate.
- [ ] Every “predeclared” question resolves to a frozen threshold.
- [ ] Missing evidence was not converted into a verdict.
- [ ] Evidence availability does not exceed the cutoff; observation does not exceed finalization.
- [ ] Scored `EXT-*` rows apply to the full ranked universe; extensions never pool.
- [ ] Category/subtype/exposure routing is correct.
- [ ] Vetoes cannot be averaged away.

## Failed, unknown, and conflicted review

| Construct/question | Classification | Next evidence/action | Resolution |
|---|---|---|---|
|  | thesis failure / evidence gap / contradiction / calculation / malformed question / category mistake / holistic |  |  |

## Independent-review disagreements

| Question | Evaluator A | Evaluator B / human | Type | Resolution/evidence |
|---|---|---|---|---|
|  |  |  | factual / definitional / temporal / weighting / risk tolerance |  |

## Holistic residual

- Omitted decisive consideration:
- Base-rate/economic-logic conflict:
- Nonlinear or correlated risks:
- Instrument/underlying mismatch:
- Case where the checklist passes but the action remains poor:
- User-goal/policy mismatch:
- Question or assumption requiring future revision:

## Conclusion

- Merit:
- Entry:
- Integrity:
- Implementation:
- Portfolio fit:
- Evidence confidence:
- Strongest bear case and falsifiers:
- Status: research / watch / eligible for diligence / policy-compliant bounded action / hold / avoid / insufficient evidence
- Authorization ceiling:
- Overall confidence:
- Reopen conditions:
- Finalized assessment hash, if final:
- Independent-review verification result:
