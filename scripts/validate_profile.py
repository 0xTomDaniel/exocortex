#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from exo_distribution.config import (
    discover_profile_paths,
    load_profile_config,
    schema_summary,
    validate_profile_set,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate an Exo Hermes profile TOML file.")
    parser.add_argument(
        "profile",
        nargs="?",
        default="profiles/tom-local-dev/profile.toml",
        help="Profile TOML path to validate.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Validate every profile under profiles/ and enforce cross-profile isolation.",
    )
    parser.add_argument(
        "--schema",
        default="schemas/profile-config.schema.json",
        help="Checked-in schema contract path.",
    )
    args = parser.parse_args()

    schema = schema_summary(Path(args.schema))
    if args.all:
        configs = [load_profile_config(path) for path in discover_profile_paths(Path("profiles"))]
        validate_profile_set(configs)
        print(f"validated {len(configs)} profiles with {schema}")
        return 0
    config = load_profile_config(Path(args.profile))
    print(f"validated {config.profile_id} with {schema}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
