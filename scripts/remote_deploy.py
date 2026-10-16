#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from exo_distribution.config import (
    ValidationError,
    discover_profile_paths,
    load_profile_config,
    validate_profile_set,
)
from exo_distribution.deploy import build_deploy_plan, load_deploy_target


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render a dry-run or mock remote SSH deploy plan for Hermes Exo."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("deploy/remote/mock-target.toml"),
        help="Non-secret remote deploy target TOML.",
    )
    parser.add_argument(
        "--profiles-root",
        type=Path,
        default=Path("profiles"),
        help="Directory containing profile.toml files.",
    )
    parser.add_argument(
        "--mock-check",
        action="store_true",
        help="Include fixture-backed health/status/log failure reporting.",
    )
    parser.add_argument(
        "--profile",
        action="append",
        default=[],
        help="Limit the deploy plan to an installable profile id. Repeatable.",
    )
    parser.add_argument(
        "--compose-output",
        type=Path,
        default=Path("deploy/compose/generated/hermes-multi-owner.compose.yaml"),
        help="Rendered compose path that the remote plan should copy/use.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero when mock-check reports fixture failures.",
    )
    args = parser.parse_args()

    try:
        target = load_deploy_target(args.config)
        configs = [load_profile_config(path) for path in discover_profile_paths(args.profiles_root)]
        validate_profile_set(configs)
        plan = build_deploy_plan(
            target,
            configs,
            mode="mock-check" if args.mock_check else "dry-run",
            compose_output=args.compose_output,
            selected_profile_ids=tuple(args.profile),
        )
    except ValidationError as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, indent=2))
        return 1

    print(json.dumps(plan, indent=2))
    mock_health = plan.get("mock_health")
    if args.strict and isinstance(mock_health, dict) and mock_health.get("ok") is False:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
