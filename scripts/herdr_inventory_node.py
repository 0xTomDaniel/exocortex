#!/usr/bin/env python3
"""Restricted SSH forced-command endpoint. No pane input or process launch API."""
import json
import os
import signal
import subprocess
import sys

MAX_REQUEST = 16384


def command_for(request):
    if not isinstance(request, dict) or set(request) != {"operation"}:
        raise ValueError("expected exactly one operation field")
    commands = {
        "agents": ["agent", "list"],
        "workspaces": ["workspace", "list"],
    }
    operation = request["operation"]
    if not isinstance(operation, str) or operation not in commands:
        raise ValueError("operation denied; allowed: agents, workspaces")
    return commands[operation]


def main():
    signal.alarm(15)
    try:
        if len(sys.argv) != 2:
            raise ValueError("operator configuration path required")
        with open(sys.argv[1]) as f:
            config = json.load(f)
        line = sys.stdin.buffer.readline(MAX_REQUEST + 1)
        if len(line) > MAX_REQUEST:
            raise ValueError("request too large")
        request = json.loads(line)
        if isinstance(request, dict) and isinstance(request.get("operation"), str) and request["operation"] in {"review", "result"}:
            from herdr_jobs import handle
            print(json.dumps(handle(config, sys.argv[1], request)))
            return 0
        args = command_for(request)
        env = {"HOME": config["home"], "PATH": "/usr/bin:/bin", "LANG": "en_US.UTF-8"}
        if "config_home" in config:
            env["XDG_CONFIG_HOME"] = config["config_home"]
        proc = subprocess.run([config["binary"], *args], env=env,
                              capture_output=True, timeout=10)
        if len(proc.stdout) + len(proc.stderr) > 262144:
            raise ValueError("response too large")
        payload = json.loads(proc.stdout or proc.stderr)
        print(json.dumps({"node": config["node"], "exit_code": proc.returncode,
                          "response": payload}))
        return int(proc.returncode != 0)
    except (ValueError, OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
        print(json.dumps({"error": str(exc)}))
        return 1


if __name__ == "__main__":
    sys.exit(main())
