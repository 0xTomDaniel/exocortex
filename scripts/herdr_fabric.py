#!/usr/bin/env python3
"""Read-only inventory client for registered Herdr nodes over restricted SSH."""
import argparse
import json
from pathlib import Path
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("operation", choices=["hosts", "agents", "workspaces", "review", "result"])
    parser.add_argument("--host")
    parser.add_argument("--request-id")
    parser.add_argument("--input", help="review prompt; otherwise read stdin")
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    config_path = Path(args.config).resolve()
    config = json.loads(config_path.read_text())
    if args.operation == "hosts":
        print(json.dumps({"hosts": list(config["hosts"]), "capabilities": ["agents", "workspaces", "review", "result"],
                          "delegation": "bounded read-only batch reviews; node configuration determines availability"}))
        return 0
    if args.host not in config["hosts"]:
        parser.error("select a registered --host")
    host = config["hosts"][args.host]
    cmd = ["ssh", "-T", "-o", "BatchMode=yes", "-o", "IdentitiesOnly=yes",
           "-o", "StrictHostKeyChecking=yes", "-o", "ConnectTimeout=5",
           "-o", "ClearAllForwardings=yes", "-o", "ForwardAgent=no",
           "-o", "UserKnownHostsFile=" + str(config_path.parent / "known_hosts"),
           "-i", str(config_path.parent / "id_ed25519"),
           host["user"] + "@" + host["address"], "inventory"]
    request = {"operation": args.operation}
    if args.operation in {"review", "result"}:
        if not args.request_id:
            parser.error("--request-id required")
        request["request_id"] = args.request_id
    if args.operation == "review":
        request["prompt"] = args.input if args.input is not None else sys.stdin.read(8001)
    try:
        result = subprocess.run(cmd, input=json.dumps(request) + "\n",
                                capture_output=True, text=True, timeout=20)
        if result.returncode and not result.stdout:
            print(json.dumps({"host": args.host, "error": result.stderr.strip()}))
            return 1
        print(json.dumps(json.loads(result.stdout)))
        return int(result.returncode != 0)
    except (subprocess.TimeoutExpired, ValueError, OSError) as exc:
        print(json.dumps({"host": args.host, "error": str(exc)}))
        return 1


if __name__ == "__main__":
    sys.exit(main())
