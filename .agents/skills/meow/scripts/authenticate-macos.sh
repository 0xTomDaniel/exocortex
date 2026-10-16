#!/usr/bin/env bash
set -euo pipefail
exec uv run "$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/authenticate_macos.py" "$@"
