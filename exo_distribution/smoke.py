from __future__ import annotations

import json
from pathlib import Path

from exo_distribution.config import ProfileConfig, ValidationError


def run_fake_telegram_smoke(config: ProfileConfig, repo_root: Path) -> list[dict[str, str]]:
    smoke = config.data["smoke"]  # type: ignore[index]
    telegram_fixture = _load_json(repo_root / smoke["telegram_fixture"])  # type: ignore[index]
    phase_fixture = _load_json(repo_root / smoke["phase_fixture"])  # type: ignore[index]
    storage_root = repo_root / smoke["storage_fixture_root"]  # type: ignore[index]

    _validate_phase_fixture(config, phase_fixture)
    if not storage_root.exists():
        raise ValidationError(f"storage fixture root is missing: {storage_root}")

    owner_id = phase_fixture["secrets"]["TELEGRAM_OWNER_ID"]
    replies: list[dict[str, str]] = []
    for update in telegram_fixture["updates"]:
        if update["chat_id"] != owner_id:
            continue
        replies.append(
            {
                "chat_id": update["chat_id"],
                "text": config.expected_reply,
            }
        )

    if replies != [{"chat_id": owner_id, "text": config.expected_reply}]:
        raise ValidationError("fake Telegram owner-only smoke did not produce the expected reply")
    return replies


def _validate_phase_fixture(config: ProfileConfig, phase_fixture: dict[str, object]) -> None:
    phase = config.data["phase"]  # type: ignore[index]
    for key in ("app", "environment", "path"):
        if phase_fixture.get(key) != phase[key]:
            raise ValidationError(f"fake Phase fixture {key} does not match TOML config")
    secrets = phase_fixture.get("secrets")
    if not isinstance(secrets, dict):
        raise ValidationError("fake Phase fixture must contain a secrets object")
    required = {
        config.data["telegram"]["bot_token_secret"],  # type: ignore[index]
        config.data["telegram"]["owner_id_secret"],  # type: ignore[index]
    }
    model_api_key_secret = config.data["model"]["api_key_secret"]  # type: ignore[index]
    if model_api_key_secret:
        required.add(model_api_key_secret)
    missing = sorted(secret for secret in required if not secrets.get(secret))
    if missing:
        raise ValidationError(f"fake Phase fixture is missing required secrets: {missing}")


def _load_json(path: Path) -> dict[str, object]:
    with path.open("r", encoding="utf-8") as json_file:
        value = json.load(json_file)
    if not isinstance(value, dict):
        raise ValidationError(f"{path} must contain a JSON object")
    return value
