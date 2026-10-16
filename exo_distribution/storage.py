from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from exo_distribution.config import ProfileConfig, ValidationError

StorageStatus = Literal["healthy", "stale", "errored", "unavailable"]


@dataclass(frozen=True)
class MountDeclaration:
    zone: str
    kind: str
    host_path: str
    container_path: str
    access: str
    permissions: str
    backup: str
    recovery: str
    allowed_write_paths: tuple[str, ...]


@dataclass(frozen=True)
class SyncHealth:
    zone: str
    status: StorageStatus
    summary: str


def storage_mount_declarations(config: ProfileConfig) -> list[MountDeclaration]:
    storage = config.data["storage"]  # type: ignore[index]
    declarations = [
        _mount_declaration("runtime", storage["runtime"]),  # type: ignore[index]
        _mount_declaration("vault", storage["vault"]),  # type: ignore[index]
        _mount_declaration("personal_files", storage["personal_files"]),  # type: ignore[index]
    ]
    for mount in storage["placeholder_mounts"]:  # type: ignore[index]
        declarations.append(_mount_declaration(f"placeholder:{mount['name']}", mount))
    return declarations


def read_fake_sync_health(config: ProfileConfig, repo_root: Path) -> list[SyncHealth]:
    fixture_path = config.data["smoke"]["storage_sync_fixture"]  # type: ignore[index]
    fixture = _load_json(repo_root / fixture_path)
    states = fixture.get("states")
    if not isinstance(states, list):
        raise ValidationError("storage sync fixture must contain a states list")

    health: list[SyncHealth] = []
    for index, state in enumerate(states):
        if not isinstance(state, dict):
            raise ValidationError(f"storage sync state {index} must be an object")
        zone = state.get("zone")
        status = state.get("status")
        summary = state.get("summary")
        if not isinstance(zone, str) or not zone:
            raise ValidationError(f"storage sync state {index} must name a zone")
        if status not in {"healthy", "stale", "errored", "unavailable"}:
            raise ValidationError(f"storage sync state {index} has unsupported status")
        if not isinstance(summary, str) or not summary.strip():
            raise ValidationError(f"storage sync state {index} must include a summary")
        health.append(SyncHealth(zone=zone, status=status, summary=summary))
    _validate_sync_health_zones(config, health)
    return health


def storage_contract_summary(config: ProfileConfig, repo_root: Path) -> dict[str, object]:
    mounts = storage_mount_declarations(config)
    health = read_fake_sync_health(config, repo_root)
    return {
        "profile": config.profile_id,
        "mounts": [mount.__dict__ for mount in mounts],
        "sync_health": [state.__dict__ for state in health],
    }


def _mount_declaration(zone: str, table: object) -> MountDeclaration:
    if not isinstance(table, dict):
        raise ValidationError(f"{zone} storage declaration must be a table")
    container_path = table.get("container_path", table.get("mount_path"))
    allowed = table.get("allowed_write_paths")
    if not isinstance(allowed, list) or not all(isinstance(path, str) for path in allowed):
        raise ValidationError(f"{zone} allowed_write_paths must be a list of strings")
    if not isinstance(container_path, str):
        raise ValidationError(f"{zone} must declare a container path")
    return MountDeclaration(
        zone=zone,
        kind=_string_field(table, "kind"),
        host_path=_string_field(table, "path"),
        container_path=container_path,
        access=_string_field(table, "access"),
        permissions=_string_field(table, "permissions"),
        backup=_string_field(table, "backup"),
        recovery=_string_field(table, "recovery"),
        allowed_write_paths=tuple(allowed),
    )


def _validate_sync_health_zones(config: ProfileConfig, health: list[SyncHealth]) -> None:
    declared_zones = {mount.zone for mount in storage_mount_declarations(config)}
    health_zones = [state.zone for state in health]
    unique_health_zones = set(health_zones)

    if len(unique_health_zones) != len(health_zones):
        duplicates = sorted(
            zone for zone in unique_health_zones if health_zones.count(zone) > 1
        )
        raise ValidationError(
            f"storage sync fixture repeats zones for {config.profile_id}: "
            f"{', '.join(duplicates)}"
        )
    if unique_health_zones != declared_zones:
        missing = sorted(declared_zones - unique_health_zones)
        unexpected = sorted(unique_health_zones - declared_zones)
        details = []
        if missing:
            details.append(f"missing declared zones: {', '.join(missing)}")
        if unexpected:
            details.append(f"unexpected zones: {', '.join(unexpected)}")
        raise ValidationError(
            f"storage sync fixture zones do not match {config.profile_id} mounts; "
            + "; ".join(details)
        )


def _string_field(table: dict[str, object], key: str) -> str:
    value = table.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"storage declaration field {key} must be a non-empty string")
    return value


def _load_json(path: Path) -> dict[str, object]:
    with path.open("r", encoding="utf-8") as json_file:
        value = json.load(json_file)
    if not isinstance(value, dict):
        raise ValidationError(f"{path} must contain a JSON object")
    return value
