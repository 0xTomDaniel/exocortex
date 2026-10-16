#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from exo_distribution.config import (
    discover_profile_paths,
    load_profile_config,
    validate_profile_set,
)
from exo_distribution.render import render_compose


def main() -> int:
    parser = argparse.ArgumentParser(description="Render multi-owner Hermes Compose template.")
    parser.add_argument(
        "--profiles-root",
        default="profiles",
        help="Directory containing profile subdirectories.",
    )
    parser.add_argument(
        "--template",
        default="deploy/compose/hermes-multi-owner.compose.yaml.template",
        help="Compose template path.",
    )
    parser.add_argument(
        "--output",
        default="deploy/compose/generated/hermes-multi-owner.compose.yaml",
        help="Output path for rendered Compose example.",
    )
    parser.add_argument(
        "--profile",
        action="append",
        default=[],
        help="Limit rendered services to an installable profile id. Repeatable.",
    )
    args = parser.parse_args()

    profile_paths = discover_profile_paths(Path(args.profiles_root))
    configs = [load_profile_config(path) for path in profile_paths]
    validate_profile_set(configs)
    compose_configs = [
        config
        for config in configs
        if config.data["profile"]["intended_profile"]  # type: ignore[index]
        == "installable-template"
    ]
    if args.profile:
        selected = set(args.profile)
        unknown = sorted(selected - {config.profile_id for config in compose_configs})
        if unknown:
            raise SystemExit(
                "selected compose profiles must be installable-template profiles; "
                f"unknown={unknown}"
            )
        compose_configs = [
            config for config in compose_configs if config.profile_id in selected
        ]
    validate_profile_set(compose_configs)
    rendered = render_compose(compose_configs, Path(args.template))
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered, encoding="utf-8")
    print(f"rendered {len(compose_configs)} Hermes services to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
