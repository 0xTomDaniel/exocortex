"""Routine Meow summaries. No raw provider output or sensitive detail commands."""

import json
import math
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

COMMANDS = frozenset(
    [
        "get-my-entity",
        "list-bank-accounts",
        "get-bank-account",
        "get-account-balances",
        "list-account-transactions",
        "list-cards",
        "list-card-transactions",
        "get-card-insights",
        "get-card",
        "list-invoices",
        "get-invoice",
        "list-bills",
        "get-bill",
    ]
)
CONTAINERS = frozenset(
    [
        "data",
        "result",
        "accounts",
        "bank_accounts",
        "balances",
        "transactions",
        "cards",
        "invoices",
        "bills",
        "items",
        "results",
    ]
)
NUMBERS = frozenset(
    [
        "balance",
        "available_balance",
        "current_balance",
        "amount",
        "amount_cents",
        "total",
        "total_amount",
        "total_count",
        "count",
        "limit",
        "offset",
        "total_spend",
        "cashback_earned",
    ]
)
STATUSES = frozenset(
    [
        "active",
        "inactive",
        "open",
        "closed",
        "pending",
        "pending_approval",
        "approved",
        "rejected",
        "cancelled",
        "canceled",
        "completed",
        "settled",
        "posted",
        "paid",
        "unpaid",
        "overdue",
        "draft",
        "submitted",
        "processing",
        "failed",
        "available",
        "blocked",
        "frozen",
    ]
)


def summarize(value):
    if isinstance(value, list):
        return [summary for item in value if (summary := summarize(item))]
    if not isinstance(value, dict):
        return {}
    result = {}
    for key, item in value.items():
        if key in CONTAINERS and isinstance(item, (dict, list)):
            child = summarize(item)
            if child:
                result[key] = child
        elif (
            key in NUMBERS
            and type(item) in (int, float)
            and math.isfinite(item)
            and abs(item) < 10**12
            or key == "currency"
            and isinstance(item, str)
            and re.fullmatch("[A-Z]{3}", item)
            or key == "status"
            and isinstance(item, str)
            and item.lower() in STATUSES
            or key in {"last4", "last_four"}
            and isinstance(item, str)
            and re.fullmatch("[0-9]{4}", item)
        ):
            result[key] = item
        elif key == "step_instructions":
            result["next_step_requires_review"] = True
    return result


def invoke(arguments):
    entry = shutil.which("meow")
    node = shutil.which("node")
    if not entry or not node:
        raise RuntimeError("Meow CLI and Node must be installed")
    return subprocess.run(
        [
            node,
            str(Path(__file__).with_name("credential_launcher.cjs")),
            str(Path(entry).resolve()),
        ],
        input=json.dumps({"args": arguments}),
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )


def owner_context():
    """Require explicit approved account selection; never infer another owner."""
    email = os.environ.get("MEOW_EXO_EMAIL", "").strip()
    service = os.environ.get("MEOW_EXO_KEYCHAIN_SERVICE", "").strip()
    if not email or not service:
        raise ValueError("owner_context_required")
    return email, service


def main():
    args = sys.argv[1:]
    if not args or args[0] not in COMMANDS:
        print(
            "Blocked: command is outside routine summaries; use a separately approved operation.",
            file=sys.stderr,
        )
        return 3
    # Caller cannot override credential, result format, or raw request fields.
    if any(
        arg.split("=", 1)[0] in {"--api-key", "--raw", "--output", "-o", "--help", "-h"}
        for arg in args[1:]
    ):
        print("Blocked: credential/raw/output overrides are not allowed.", file=sys.stderr)
        return 3
    try:
        email, service = owner_context()
    except ValueError:
        print("owner_context_required: configure MEOW_EXO_EMAIL and MEOW_EXO_KEYCHAIN_SERVICE privately", file=sys.stderr)
        return 3
    try:
        credential = subprocess.run(
            [
                "security",
                "find-generic-password",
                "-a",
                email,
                "-s",
                service,
                "-w",
            ],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        if not credential:
            raise RuntimeError("Credential missing")
        response = invoke([*args, "--api-key", credential, "--output", "json"])
        del credential
        if response.returncode:
            raise RuntimeError("Provider call failed")
        data = json.loads(response.stdout)
        if isinstance(data, dict) and data.get("isError"):
            raise RuntimeError("Provider reported error")
        # Standard MCP text envelope, when returned by the installed CLI.
        if isinstance(data, dict) and isinstance(data.get("content"), list):
            data = [
                json.loads(block["text"])
                for block in data["content"]
                if block.get("type") == "text"
            ]
        summary = summarize(data)
        if not summary:
            print(
                json.dumps(
                    {
                        "status": "unsupported_response",
                        "detail": "No approved summary fields; raw output withheld.",
                    }
                )
            )
            return 2
        print(json.dumps(summary, indent=2))
        return 0
    except Exception:  # noqa: BLE001 — raw exception text may contain credentials
        print("Meow read failed; raw provider output and credentials withheld.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
