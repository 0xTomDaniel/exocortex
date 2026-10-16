"""Create/check an explicit review progress record; never infer user confirmation."""

import argparse
import json
import re
from datetime import date
from pathlib import Path

STEPS = {
    "review": [
        "mind_dump",
        "reconstruction",
        "outcomes",
        "habits_and_balance",
        "task_debt",
        "dated_reminders",
        "rediscovery",
        "followups",
    ],
    "planning": [
        "review_stack",
        "outcome_and_evidence",
        "sequencing",
        "capacity_and_displacements",
        "life_anchors",
        "dated_reminders",
        "decision_gate",
    ],
    "startup": [
        "cadence",
        "interaction_gap",
        "review_stack",
        "habits",
        "task_debt",
        "dated_reminders",
        "rediscovery",
        "day_plan",
    ],
}


def new_state(kind, period, phase):
    return {
        "version": 1,
        "scope": f"{kind}:{period}:{phase}",
        "mode": "full",
        "workflow": {"status": "active", "reason": "", "source": "", "resume_when": ""},
        "coverage": {
            "start": None,
            "end": None,
            "missing_dates": [],
            "missing_dates_resolution": "",
        },
        "steps": {step: {"status": "pending", "evidence": []} for step in STEPS[phase]},
        "unresolved": [],
        "confirmation": None,
        "next_step": f"Work through {STEPS[phase][0]} with the user",
    }


def nonblank_text(value):
    return isinstance(value, str) and bool(value.strip())


def check_state(state):
    errors = []
    # Older version-1 records remain readable without a workflow extension.
    workflow = state.get("workflow", {"status": "active"})
    workflow_status = workflow.get("status") if isinstance(workflow, dict) else None
    if workflow_status not in {"active", "paused", "deferred", "cancelled"}:
        errors.append("invalid workflow status")
    elif workflow_status != "active":
        errors.append(f"workflow is {workflow_status}, not complete")
    scope = state.get("scope", "")
    parts = scope.split(":") if isinstance(scope, str) else []
    if (
        len(parts) != 3
        or parts[0] not in {"day", "week", "sprint", "cycle", "quarter", "year"}
        or parts[2] not in STEPS
        or not parts[1]
    ):
        return {"complete": False, "errors": ["invalid scope"], "next_step": "Repair scope"}
    phase = parts[2]
    if state.get("version") != 1 or state.get("mode") not in {"full", "reduced"}:
        errors.append("invalid version or mode")
    coverage = state.get("coverage") or {}
    try:
        start = date.fromisoformat(coverage.get("start", ""))
        end = date.fromisoformat(coverage.get("end", ""))
        if start > end:
            errors.append("coverage ends before it starts")
    except (TypeError, ValueError):
        errors.append("coverage dates must be explicit")
    missing = coverage.get("missing_dates")
    if not isinstance(missing, list) or not nonblank_text(coverage.get("missing_dates_resolution")):
        errors.append("record missing-date coverage and its resolution, including none")
    elif missing:
        # A missing day is unknown evidence, not permission to invent a habit score.
        for day in missing:
            try:
                date.fromisoformat(day)
            except (TypeError, ValueError):
                errors.append("invalid missing date")
    steps = state.get("steps") or {}
    omissions = []
    for name in STEPS[phase]:
        step = steps.get(name) or {}
        evidence = step.get("evidence")
        if (
            not isinstance(evidence, list)
            or not evidence
            or not all(isinstance(x, str) and x.strip() for x in evidence)
        ):
            errors.append(f"{name}: evidence missing")
        if (
            step.get("status") == "omitted"
            and state.get("mode") == "reduced"
            and nonblank_text(step.get("reason"))
        ):
            omissions.append(name)
        elif step.get("status") != "complete":
            errors.append(f"{name}: unfinished")
    if not isinstance(state.get("unresolved"), list) or state.get("unresolved"):
        errors.append("unresolved decisions remain or are unspecified")
    confirmation = state.get("confirmation") or {}
    if (
        confirmation.get("scope") != scope
        or confirmation.get("mode") != state.get("mode")
        or not nonblank_text(confirmation.get("source"))
        or not nonblank_text(confirmation.get("quote"))
    ):
        errors.append("exact-scope user confirmation with source, quote, and mode required")
    if omissions and sorted(confirmation.get("accepted_omissions", [])) != sorted(omissions):
        errors.append("reduced omissions require explicit acceptance")
    if not errors and state.get("next_step"):
        errors.append("clear the completed scope next step; keep other scopes separate")
    if errors and not nonblank_text(state.get("next_step")) and workflow_status != "cancelled":
        errors.append("unfinished scope needs an exact next step")
    return {
        "scope": scope,
        "workflow_status": workflow_status,
        "complete": not errors,
        "errors": errors,
        "next_step": state.get("next_step"),
    }


def read_state(path):
    text = Path(path).read_text(encoding="utf-8")
    if text.lstrip().startswith("{"):
        return json.loads(text)
    blocks = re.findall(r"^```review-state\s*\n(.*?)^```\s*$", text, re.MULTILINE | re.DOTALL)
    if len(blocks) != 1:
        raise ValueError(
            "expected exactly one review-state block; legacy completion remains unverified"
        )
    return json.loads(blocks[0])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init")
    init.add_argument(
        "--kind", required=True, choices=["day", "week", "sprint", "cycle", "quarter", "year"]
    )
    init.add_argument("--period", required=True)
    init.add_argument("--phase", required=True, choices=list(STEPS))
    check = sub.add_parser("check")
    check.add_argument("path")
    args = parser.parse_args()
    if args.command == "init":
        print(json.dumps(new_state(args.kind, args.period, args.phase), indent=2))
        return 0
    try:
        result = check_state(read_state(args.path))
    except (OSError, ValueError, TypeError, AttributeError) as exc:
        print(json.dumps({"complete": False, "errors": [str(exc)]}))
        return 2
    print(json.dumps(result, indent=2))
    return 0 if result["complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
