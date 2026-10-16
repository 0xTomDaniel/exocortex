#!/bin/bash
set -euo pipefail

mkdir -p "$HOME/.codex"
if [[ ! -x "$HOME/.codex/packages/standalone/current/codex" ]]; then
  cp -a /opt/codex-seed/. "$HOME/.codex/"
fi

shutdown() {
  codex app-server daemon stop >/dev/null 2>&1 || true
}
trap shutdown EXIT INT TERM

codex app-server daemon bootstrap --remote-control

while codex app-server daemon version >/dev/null 2>&1; do
  sleep 5
done

echo "Codex app-server daemon stopped unexpectedly" >&2
exit 1
