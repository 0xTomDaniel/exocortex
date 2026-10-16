from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from exo_distribution.config import ProfileConfig, ValidationError

HealthCategory = Literal["service", "sync", "storage_safety", "deployment"]
HealthSeverity = Literal["warning", "critical"]


@dataclass(frozen=True)
class ProactiveDelivery:
    kind: str
    chat_id: str
    text: str


def run_fake_proactive_smoke(config: ProfileConfig, repo_root: Path) -> list[dict[str, str]]:
    proactive = config.data["proactive"]  # type: ignore[index]
    if proactive["enabled"] is not True:  # type: ignore[index]
        return []

    _validate_owner_delivery_surface(config)
    smoke = config.data["smoke"]  # type: ignore[index]
    phase_fixture = _load_json(repo_root / smoke["phase_fixture"])  # type: ignore[index]
    owner_chat_id = _owner_chat_id(config, phase_fixture)

    deliveries: list[ProactiveDelivery] = []
    deliveries.extend(_check_in_deliveries(config, owner_chat_id))
    deliveries.extend(_health_ping_deliveries(config, repo_root, owner_chat_id))
    return [
        {"kind": delivery.kind, "chat_id": delivery.chat_id, "text": delivery.text}
        for delivery in deliveries
    ]


def _validate_owner_delivery_surface(config: ProfileConfig) -> None:
    proactive = config.data["proactive"]  # type: ignore[index]
    profile = config.data["profile"]  # type: ignore[index]
    telegram = config.data["telegram"]  # type: ignore[index]

    if proactive["target_profile_id"] != profile["id"]:  # type: ignore[index]
        raise ValidationError("proactive.target_profile_id must match profile.id")
    if proactive["delivery_surface"] != "telegram-owner-text":  # type: ignore[index]
        raise ValidationError("proactive delivery must use telegram-owner-text")
    if telegram["owner_only"] is not True or telegram["text_only"] is not True:
        raise ValidationError("proactive delivery requires owner-only text Telegram")


def _owner_chat_id(config: ProfileConfig, phase_fixture: dict[str, object]) -> str:
    secrets = phase_fixture.get("secrets")
    if not isinstance(secrets, dict):
        raise ValidationError("fake Phase fixture must contain a secrets object")
    owner_secret = config.data["telegram"]["owner_id_secret"]  # type: ignore[index]
    owner_chat_id = secrets.get(owner_secret)
    if not isinstance(owner_chat_id, str) or not owner_chat_id:
        raise ValidationError("fake Phase fixture is missing the Telegram owner id")
    return owner_chat_id


def _check_in_deliveries(config: ProfileConfig, owner_chat_id: str) -> list[ProactiveDelivery]:
    profile = config.data["profile"]  # type: ignore[index]
    check_ins = config.data["proactive"]["check_ins"]  # type: ignore[index]
    if check_ins["enabled"] is not True:
        return []

    owner_name = str(profile["owner_name"]).split()[0]
    deliveries: list[ProactiveDelivery] = []
    if check_ins["morning_enabled"] is True:
        deliveries.append(
            ProactiveDelivery(
                kind="morning_check_in",
                chat_id=owner_chat_id,
                text=(
                    f"Good morning, {owner_name}. "
                    f"Minimal Exo check-in is ready for {check_ins['morning_local_time']}."
                ),
            )
        )
    if check_ins["evening_enabled"] is True:
        deliveries.append(
            ProactiveDelivery(
                kind="evening_check_in",
                chat_id=owner_chat_id,
                text=(
                    f"Evening check-in for {owner_name}: "
                    f"minimal status review is ready for {check_ins['evening_local_time']}."
                ),
            )
        )
    return deliveries


def _health_ping_deliveries(
    config: ProfileConfig,
    repo_root: Path,
    owner_chat_id: str,
) -> list[ProactiveDelivery]:
    health_pings = config.data["proactive"]["health_pings"]  # type: ignore[index]
    if health_pings["enabled"] is not True:
        return []
    if health_pings["provider"] != "fake-local":
        raise ValidationError("automated proactive smoke only supports fake-local health pings")

    fixture = _load_json(repo_root / health_pings["fixture"])  # type: ignore[index]
    problems = fixture.get("problems")
    if not isinstance(problems, list):
        raise ValidationError("fake health fixture must contain a problems list")

    deliveries: list[ProactiveDelivery] = []
    for index, problem in enumerate(problems):
        if not isinstance(problem, dict):
            raise ValidationError(f"fake health problem {index} must be an object")
        category = problem.get("category")
        severity = problem.get("severity")
        summary = problem.get("summary")
        if category not in {"service", "sync", "storage_safety", "deployment"}:
            raise ValidationError(f"fake health problem {index} has unsupported category")
        if severity not in {"warning", "critical"}:
            raise ValidationError(f"fake health problem {index} has unsupported severity")
        if not isinstance(summary, str) or not summary.strip():
            raise ValidationError(f"fake health problem {index} must include a summary")
        deliveries.append(
            ProactiveDelivery(
                kind=f"health_{category}",
                chat_id=owner_chat_id,
                text=f"Exo {severity} health ping ({category}): {summary}",
            )
        )
    return deliveries


def _load_json(path: Path) -> dict[str, object]:
    with path.open("r", encoding="utf-8") as json_file:
        value = json.load(json_file)
    if not isinstance(value, dict):
        raise ValidationError(f"{path} must contain a JSON object")
    return value
