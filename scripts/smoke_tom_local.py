#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from exo_distribution.config import load_profile_config
from exo_distribution.proactive import run_fake_proactive_smoke
from exo_distribution.smoke import run_fake_telegram_smoke


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the no-credentials Tom local/dev fake Telegram smoke."
    )
    parser.add_argument(
        "profile",
        nargs="?",
        default="profiles/tom-local-dev/profile.toml",
        help="Profile TOML path.",
    )
    args = parser.parse_args()

    repo_root = Path.cwd()
    config = load_profile_config(Path(args.profile))
    replies = run_fake_telegram_smoke(config, repo_root)
    proactive_deliveries = run_fake_proactive_smoke(config, repo_root)
    print(
        json.dumps(
            {
                "profile": config.profile_id,
                "replies": replies,
                "proactive_deliveries": proactive_deliveries,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
