#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from exo_distribution.config import load_profile_config
from exo_distribution.storage import storage_contract_summary


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate and print fake/local Exo storage contract evidence."
    )
    parser.add_argument(
        "profile",
        nargs="?",
        default="profiles/tom-local-dev/profile.toml",
        help="Profile TOML path to inspect.",
    )
    args = parser.parse_args()

    repo_root = Path.cwd()
    config = load_profile_config(Path(args.profile))
    print(json.dumps(storage_contract_summary(config, repo_root), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
