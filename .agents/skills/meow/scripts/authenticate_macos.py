# /// script
# requires-python = ">=3.11"
# dependencies = ["keyring>=25,<26"]
# ///
"""Interactive setup: secrets stay in memory/private pipes and macOS Keychain."""

import json
import re
import subprocess
import sys

from safe_read import invoke, owner_context


def find_key(value):
    if isinstance(value, dict):
        if isinstance(value.get("api_key"), str) and value["api_key"]:
            return value["api_key"]
        for child in value.values():
            found = find_key(child)
            if found:
                return found
    elif isinstance(value, list):
        for child in value:
            if isinstance(child, dict) and child.get("type") == "text":
                try:
                    child = json.loads(child["text"])
                except (KeyError, json.JSONDecodeError):
                    continue
            found = find_key(child)
            if found:
                return found
    return None


def main():
    try:
        email, service = owner_context()
    except ValueError:
        print("owner_context_required: configure MEOW_EXO_EMAIL and MEOW_EXO_KEYCHAIN_SERVICE privately", file=sys.stderr)
        return 3
    if len(sys.argv) > 1:
        print("Use explicit private owner context, not positional account overrides.", file=sys.stderr)
        return 3
    try:
        from keyring.backends.macOS import Keyring

        code = subprocess.run(
            ["osascript"],
            input='display dialog "Enter the newest Meow verification code for the account being connected." default answer "" with hidden answer buttons {"Cancel", "Connect"} default button "Connect"\ntext returned of result\n',
            text=True,
            capture_output=True,
            check=True,
        ).stdout.strip()
        if not re.fullmatch("[0-9]{6}", code):
            raise ValueError("Invalid code")
        response = invoke(
            [
                "issue-onboarding-key",
                "--email",
                email,
                "--verification-code",
                code,
                "--output",
                "json",
            ]
        )
        del code
        if response.returncode:
            raise ValueError("Authentication failed")
        key = find_key(json.loads(response.stdout))
        del response
        if not key:
            raise ValueError("No key returned")
        Keyring().set_password(service, email, key)
        del key
        print("key_stored_in_macos_keychain; verify through the routine summary helper")
        return 0
    except Exception:  # noqa: BLE001 — raw exception text may contain credentials
        print("authentication_cancelled_or_failed; raw response withheld", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
