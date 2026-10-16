# Personal content boundary and import review

The approved rule is one reusable preferences package: `tom-operating-style`.
Its team-planning procedure is an optional module, with local assets,
references, and evals. General planning defaults remain permitted; they are
configurable starting points, not assertions about a specific person's life.

## Why content escaped the boundary

Git history shows three concrete gaps, not a previously enforced single-skill
rule being silently bypassed:

- `ece7c2c` added a separate team-planning skill and explicitly updated routing,
  the distribution specification, and tests to support two profile-targeted
  personal skills. Profile isolation was treated as sufficient ownership.
- `5c666f2` imported current vault skill sources and preserved capability
  approvals, deferring cleanup. Excluding private vault notes missed personal
  information embedded in descriptions, helper defaults, examples, and assets.
- `96fe559` repaired reliability and credential handling but retained personal
  account defaults. Structural validation and passing preservation tests were
  not tests of source-publication privacy. Voice prompts introduced by
  `606dc43` also lived outside the skill manifest's scope.

The resulting source leaks were real even where a package was unapproved and
never installed. The previous review did not evaluate the right boundary.

## Required classification before publication

Review every changed source surface, including unapproved packages and deployed
prompt text. Choose its owner before copying:

| Content | Owner |
| --- | --- |
| Reusable personal preferences and team rituals | Sole owner skill and its modules |
| General procedures and configurable defaults | General skills |
| Current habits, biography, account history | Approved private memory |
| Account identity and credential namespace | Private runtime configuration |
| Profile identity, capability approval, routing IDs | Profile configuration |
| Transport, evidence, approval, and reliability rules | Shared instructions |

Review descriptions, code, references, templates, evals, and examples. Check both
explicit names and implicit assumptions: real customer stories, default account
selection, fixed personal presentation instructions, and assumed memory backends.
Do not move general defaults merely because they originated in a personal vault.
Do not call content generic merely because names were replaced with “owner.”

## Enforcement and limits

`tests/test_personal_boundaries.py` verifies modular installation, absence of a
standalone team skill, isolation from other profiles, fail-closed missing Meow
owner context, and known personal identity recurrence across shared skills,
root instructions, and all Voice prompts. A narrow routing-identifier exemption
permits references to the designated preferences skill and target profile.
The regression suite runs these checks before publication. Human semantic review
remains required: a known-token scan cannot detect every new name or implicit
preference, and structural skill validation is not privacy certification.

The skill-authoring procedure and root AGENTS routing carry this classification
step so future imports encounter it before copying. Review source-publication
privacy separately from installation/capability approval.

## Migration and scope

Existing runtimes must preserve and reconcile the retired standalone team skill,
move it outside skill discovery, and then install the consolidated package.
Installation refuses to proceed while that directory remains. Missing baseline
metadata retains its preservation requirement; do not fabricate a baseline.
Meow setup now requires explicit private email and Keychain service selectors;
there is no built-in personal fallback and no live credential migration.

These changes clean the current source tree. Earlier published commits still
contain removed references; no Git history rewrite, live deployment, or remote
credential change is performed by this correction.
