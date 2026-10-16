#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from exo_distribution.config import load_profile_config
from exo_distribution.render import render_hermes_config


def main() -> int:
    parser = argparse.ArgumentParser(description="Render Hermes config from Exo TOML.")
    parser.add_argument(
        "profile",
        nargs="?",
        default="profiles/tom-local-dev/profile.toml",
        help="Profile TOML path.",
    )
    parser.add_argument(
        "--template",
        default="profiles/tom-local-dev/hermes/config.yaml.template",
        help="Hermes config template path.",
    )
    parser.add_argument(
        "--output",
        default="profiles/tom-local-dev/generated/config.yaml",
        help="Output path for rendered Hermes config.",
    )
    args = parser.parse_args()

    config = load_profile_config(Path(args.profile))
    rendered = render_hermes_config(config, Path(args.template))
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered, encoding="utf-8")
    print(f"rendered {config.profile_id} Hermes config to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
