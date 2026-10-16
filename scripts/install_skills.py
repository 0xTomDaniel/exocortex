#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from exo_distribution.config import ValidationError
from exo_distribution.skills import install_planned_skills, load_skills_manifest, plan_skill_install


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = REPO_ROOT / "skills/sources.toml"


def main() -> int:
    parser = argparse.ArgumentParser(description="Plan or install Exo skills for a profile.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--profile", default="tom-local-dev")
    parser.add_argument(
        "--install-root",
        type=Path,
        default=None,
        help="Override /opt/data/skills for fixture tests or operator staging.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write selected skills to the install root.",
    )
    args = parser.parse_args()

    try:
        manifest = load_skills_manifest(args.manifest, REPO_ROOT)
        plans = plan_skill_install(
            manifest,
            args.profile,
            REPO_ROOT,
            install_root=args.install_root,
        )
        if args.apply:
            plans = install_planned_skills(plans, manifest)
    except ValidationError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        return 1

    print(
        json.dumps(
            {
                "ok": True,
                "mode": "apply" if args.apply else "plan",
                "profile": args.profile,
                "default_install_root": manifest.default_install_root,
                "skills": [
                    {
                        "id": plan.source.id,
                        "name": plan.source.name,
                        "kind": plan.source.kind,
                        "category": plan.source.category,
                        "repo": plan.source.repo,
                        "path": plan.source.path,
                        "ref": plan.source.ref,
                        "runtime_destination": str(plan.runtime_destination),
                        "actual_destination": str(plan.actual_destination),
                        "action": plan.action,
                        "reason": plan.reason,
                    }
                    for plan in plans
                ],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
