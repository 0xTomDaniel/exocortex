from __future__ import annotations

import json
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Literal, TypedDict


class ValidationError(ValueError):
    """Raised when a profile TOML file violates the Exo distribution contract."""


class ToolEntry(TypedDict):
    name: str
    reason: str


class ExternalActions(TypedDict):
    enabled: bool
    allow: list[str]
    policy: str


@dataclass(frozen=True)
class ProfileConfig:
    path: Path
    data: dict[str, object]

    @property
    def profile_id(self) -> str:
        return _table(self.data, "profile")["id"]

    @property
    def expected_reply(self) -> str:
        return _table(self.data, "smoke")["expected_reply"]

    @property
    def container_name(self) -> str:
        return _table(self.data, "container")["name"]

    @property
    def hermes_home(self) -> str:
        return _table(self.data, "hermes")["home"]

    @property
    def log_path(self) -> str:
        return _table(self.data, "logs")["path"]

    @property
    def backup_path(self) -> str:
        return _table(self.data, "backups")["path"]

    @property
    def storage_zones(self) -> dict[str, dict[str, object]]:
        storage = _table(self.data, "storage")
        return {
            "runtime": _table(storage, "runtime"),
            "vault": _table(storage, "vault"),
            "personal_files": _table(storage, "personal_files"),
        }

    @property
    def telegram_token_path(self) -> str:
        return _table(self.data, "telegram")["token_path"]

    @property
    def telegram_owner_secret(self) -> str:
        return _table(self.data, "telegram")["owner_id_secret"]

    @property
    def telegram_bot_token_secret(self) -> str:
        return _table(self.data, "telegram")["bot_token_secret"]

    @property
    def phase_scope(self) -> tuple[str, str, str]:
        phase = _table(self.data, "phase")
        return (
            str(phase["app"]),
            str(phase["environment"]),
            str(phase["path"]),
        )


REQUIRED_TOP_LEVEL = (
    "profile",
    "hermes",
    "telegram",
    "model",
    "phase",
    "storage",
    "container",
    "logs",
    "backups",
    "tools",
    "proactive",
    "smoke",
)
SECRET_NAME = re.compile(r"^[A-Z][A-Z0-9_]*$")
FORBIDDEN_RUNTIME_FRAGMENTS = (
    "/Users/",
    "/home/",
    "/Volumes/",
    "/mnt/",
    "secrets",
    "credentials",
    "sessions",
    "logs",
    "backups",
    ".env",
)
PROFILE_MODES = ("local-dev", "template")
TELEGRAM_MODES = ("fake", "phase")
MODEL_MODES = ("fake", "phase", "hermes-auth")
SAFE_TOOL_PREFIXES = ("memory.", "files.", "telegram.reply_text")


def load_profile_config(path: Path) -> ProfileConfig:
    with path.open("rb") as config_file:
        data = tomllib.load(config_file)
    config = ProfileConfig(path=path, data=data)
    validate_profile_config(config)
    return config


def validate_profile_config(config: ProfileConfig) -> None:
    data = config.data
    _require_exact_keys(data, REQUIRED_TOP_LEVEL, "root")

    profile = _table(data, "profile")
    _require_exact_keys(
        profile,
        ("id", "owner_name", "mode", "timezone", "role", "intended_profile"),
        "profile",
    )
    _require_non_empty_strings(
        profile,
        ("id", "owner_name", "mode", "timezone", "role", "intended_profile"),
        "profile",
    )
    if profile["mode"] not in PROFILE_MODES:
        raise ValidationError(f"profile.mode must be one of {PROFILE_MODES}")

    hermes = _table(data, "hermes")
    _require_exact_keys(hermes, ("runtime", "home", "workspace", "skills_dir"), "hermes")
    _require_non_empty_strings(hermes, ("runtime", "home", "workspace", "skills_dir"), "hermes")
    _validate_runtime_path(hermes["home"], "hermes.home")
    _validate_runtime_path(hermes["workspace"], "hermes.workspace")
    if hermes["skills_dir"] != "/opt/data/skills":
        raise ValidationError(
            "hermes.skills_dir must install production skills into /opt/data/skills"
        )

    telegram = _table(data, "telegram")
    _require_exact_keys(
        telegram,
        (
            "mode",
            "owner_id_secret",
            "bot_token_secret",
            "token_path",
            "owner_only",
            "text_only",
        ),
        "telegram",
    )
    if telegram["mode"] not in TELEGRAM_MODES:
        raise ValidationError(f"telegram.mode must be one of {TELEGRAM_MODES}")
    if telegram["owner_only"] is not True or telegram["text_only"] is not True:
        raise ValidationError("telegram must be owner-only and text-only for v1 local smoke")
    _validate_secret_name(telegram["owner_id_secret"], "telegram.owner_id_secret")
    _validate_secret_name(telegram["bot_token_secret"], "telegram.bot_token_secret")
    _validate_runtime_path(telegram["token_path"], "telegram.token_path")

    model = _table(data, "model")
    _require_exact_keys(model, ("mode", "provider", "api_key_secret"), "model")
    if model["mode"] not in MODEL_MODES:
        raise ValidationError(f"model.mode must be one of {MODEL_MODES}")
    _validate_model_secret(model)

    phase = _table(data, "phase")
    _require_exact_keys(phase, ("app", "environment", "path"), "phase")
    _require_non_empty_strings(phase, ("app", "environment", "path"), "phase")
    if not str(phase["path"]).startswith("/"):
        raise ValidationError("phase.path must be an absolute Phase path")

    storage = _table(data, "storage")
    _require_exact_keys(
        storage,
        ("runtime", "vault", "personal_files", "placeholder_mounts"),
        "storage",
    )
    _validate_storage_table(_table(storage, "runtime"), "runtime", required_access="read-write")
    _validate_storage_table(_table(storage, "vault"), "vault", required_access="read-write")
    _validate_storage_table(
        _table(storage, "personal_files"),
        "personal_files",
        required_access="read-only",
    )
    _validate_placeholder_mounts(storage["placeholder_mounts"])

    container = _table(data, "container")
    _require_exact_keys(container, ("name", "image", "restart_policy"), "container")
    _require_non_empty_strings(container, ("name", "image", "restart_policy"), "container")
    if container["restart_policy"] != "unless-stopped":
        raise ValidationError("container.restart_policy must be unless-stopped")

    logs = _table(data, "logs")
    _require_exact_keys(logs, ("path", "git_owned"), "logs")
    _require_non_empty_strings(logs, ("path",), "logs")
    _validate_runtime_path(logs["path"], "logs.path")
    if logs["git_owned"] is not False:
        raise ValidationError("logs.git_owned must be false")

    backups = _table(data, "backups")
    _require_exact_keys(backups, ("path", "git_owned", "scope"), "backups")
    _require_non_empty_strings(backups, ("path", "scope"), "backups")
    _validate_runtime_path(backups["path"], "backups.path")
    if backups["git_owned"] is not False:
        raise ValidationError("backups.git_owned must be false")

    tools = _table(data, "tools")
    _require_exact_keys(tools, ("safe_core", "external_actions"), "tools")
    _validate_safe_core_tools(tools["safe_core"])
    external_actions = _table(tools, "external_actions")
    _require_exact_keys(external_actions, ("enabled", "allow", "policy"), "tools.external_actions")
    if external_actions["enabled"] is not False or external_actions["allow"] != []:
        raise ValidationError("external-action tools must be disabled by default")

    proactive = _table(data, "proactive")
    _require_exact_keys(
        proactive,
        ("enabled", "target_profile_id", "delivery_surface", "check_ins", "health_pings"),
        "proactive",
    )
    _validate_boolean(proactive["enabled"], "proactive.enabled")
    if proactive["target_profile_id"] != profile["id"]:
        raise ValidationError("proactive.target_profile_id must match profile.id")
    if proactive["delivery_surface"] != "telegram-owner-text":
        raise ValidationError("proactive.delivery_surface must be telegram-owner-text")
    _validate_proactive_check_ins(_table(proactive, "check_ins"))
    _validate_proactive_health_pings(_table(proactive, "health_pings"))

    smoke = _table(data, "smoke")
    _require_exact_keys(
        smoke,
        (
            "telegram_fixture",
            "phase_fixture",
            "storage_fixture_root",
            "storage_sync_fixture",
            "expected_reply",
        ),
        "smoke",
    )
    _require_non_empty_strings(
        smoke,
        (
            "telegram_fixture",
            "phase_fixture",
            "storage_fixture_root",
            "storage_sync_fixture",
            "expected_reply",
        ),
        "smoke",
    )


def validate_profile_set(configs: list[ProfileConfig]) -> None:
    if not configs:
        raise ValidationError("at least one profile is required")
    _require_unique(configs, "profile id", lambda config: config.profile_id)
    _require_unique(configs, "container name", lambda config: config.container_name)
    _require_unique(configs, "Hermes home", lambda config: config.hermes_home)
    _require_unique(configs, "Telegram token path", lambda config: config.telegram_token_path)
    _require_unique(configs, "Phase app/env/path", lambda config: config.phase_scope)
    _require_unique(configs, "log path", lambda config: config.log_path)
    _require_unique(configs, "backup path", lambda config: config.backup_path)


def discover_profile_paths(root: Path) -> list[Path]:
    return sorted(root.glob("*/profile.toml"))


def schema_summary(schema_path: Path) -> str:
    with schema_path.open("r", encoding="utf-8") as schema_file:
        schema = json.load(schema_file)
    required = schema.get("required", [])
    if not isinstance(required, list) or sorted(required) != sorted(REQUIRED_TOP_LEVEL):
        raise ValidationError("schema required keys do not match validator top-level contract")
    return f"{schema.get('title', 'profile config')} ({schema.get('$schema', 'unknown schema')})"


def _validate_storage_table(
    table: dict[str, object],
    name: Literal["runtime", "vault", "personal_files"],
    required_access: str,
) -> None:
    required = (
        "kind",
        "path",
        "container_path",
        "access",
        "git_owned",
        "permissions",
        "backup",
        "recovery",
        "allowed_write_paths",
    )
    _require_exact_keys(table, required, f"storage.{name}")
    _require_non_empty_strings(
        table,
        ("kind", "path", "container_path", "access", "permissions", "backup", "recovery"),
        f"storage.{name}",
    )
    if table["git_owned"] is not False:
        raise ValidationError(f"storage.{name}.git_owned must be false")
    path = str(table["path"])
    _validate_runtime_path(path, f"storage.{name}.path")
    container_path = str(table["container_path"])
    if not container_path.startswith("/"):
        raise ValidationError(f"storage.{name}.container_path must be absolute")
    if table["access"] != required_access:
        raise ValidationError(f"storage.{name}.access must be {required_access}")
    expected_writes = [] if required_access == "read-only" else [container_path]
    _validate_write_paths(
        table["allowed_write_paths"],
        expected=expected_writes,
        label=f"storage.{name}.allowed_write_paths",
    )


def _validate_write_paths(value: object, expected: list[str], label: str) -> None:
    if not isinstance(value, list) or not all(isinstance(path, str) for path in value):
        raise ValidationError(f"{label} must be a list of strings")
    if value != expected:
        raise ValidationError(f"{label} must be {expected}")


def _validate_placeholder_mounts(value: object) -> None:
    if not isinstance(value, list):
        raise ValidationError("storage.placeholder_mounts must be a list")
    names: set[str] = set()
    for index, entry in enumerate(value):
        if not isinstance(entry, dict):
            raise ValidationError(f"storage.placeholder_mounts[{index}] must be a table")
        _require_exact_keys(
            entry,
            (
                "name",
                "kind",
                "path",
                "mount_path",
                "access",
                "git_owned",
                "permissions",
                "backup",
                "recovery",
                "allowed_write_paths",
            ),
            f"storage.placeholder_mounts[{index}]",
        )
        _require_non_empty_strings(
            entry,
            (
                "name",
                "kind",
                "path",
                "mount_path",
                "access",
                "permissions",
                "backup",
                "recovery",
            ),
            f"storage.placeholder_mounts[{index}]",
        )
        name = str(entry["name"])
        if name in names:
            raise ValidationError(f"duplicate placeholder mount {name}")
        names.add(name)
        _validate_runtime_path(entry["path"], f"storage.placeholder_mounts[{index}].path")
        mount_path = str(entry["mount_path"])
        if not mount_path.startswith("/mnt/"):
            raise ValidationError(
                f"storage.placeholder_mounts[{index}].mount_path must be under /mnt"
            )
        if entry["access"] != "read-only":
            raise ValidationError(f"storage.placeholder_mounts[{index}].access must be read-only")
        if entry["git_owned"] is not False:
            raise ValidationError(
                f"storage.placeholder_mounts[{index}].git_owned must be false"
            )
        _validate_write_paths(
            entry["allowed_write_paths"],
            expected=[],
            label=f"storage.placeholder_mounts[{index}].allowed_write_paths",
        )


def _validate_runtime_path(value: object, field: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{field} must be a non-empty string")
    if "${EXO_RUNTIME_ROOT}" not in value:
        raise ValidationError(f"{field} must be rooted under EXO_RUNTIME_ROOT")
    for fragment in FORBIDDEN_RUNTIME_FRAGMENTS:
        if fragment in value:
            raise ValidationError(f"{field} contains private/runtime fragment {fragment}")


def _validate_safe_core_tools(value: object) -> None:
    if not isinstance(value, list) or not value:
        raise ValidationError("tools.safe_core must be a non-empty list")
    names: set[str] = set()
    for index, entry in enumerate(value):
        if not isinstance(entry, dict):
            raise ValidationError(f"tools.safe_core[{index}] must be a table")
        _require_exact_keys(entry, ("name", "reason"), f"tools.safe_core[{index}]")
        _require_non_empty_strings(entry, ("name", "reason"), f"tools.safe_core[{index}]")
        name = str(entry["name"])
        if name in names:
            raise ValidationError(f"duplicate safe tool {name}")
        names.add(name)
        if not name.startswith(SAFE_TOOL_PREFIXES):
            raise ValidationError(f"safe/core tool {name} is not in the approved default set")


def _validate_proactive_check_ins(table: dict[str, object]) -> None:
    _require_exact_keys(
        table,
        (
            "enabled",
            "morning_enabled",
            "morning_local_time",
            "evening_enabled",
            "evening_local_time",
        ),
        "proactive.check_ins",
    )
    _validate_boolean(table["enabled"], "proactive.check_ins.enabled")
    _validate_boolean(table["morning_enabled"], "proactive.check_ins.morning_enabled")
    _validate_boolean(table["evening_enabled"], "proactive.check_ins.evening_enabled")
    _validate_local_time(table["morning_local_time"], "proactive.check_ins.morning_local_time")
    _validate_local_time(table["evening_local_time"], "proactive.check_ins.evening_local_time")


def _validate_proactive_health_pings(table: dict[str, object]) -> None:
    _require_exact_keys(
        table,
        ("enabled", "provider", "fixture"),
        "proactive.health_pings",
    )
    _validate_boolean(table["enabled"], "proactive.health_pings.enabled")
    if table["provider"] != "fake-local":
        raise ValidationError("proactive.health_pings.provider must be fake-local")
    _require_non_empty_strings(table, ("fixture",), "proactive.health_pings")


def _validate_boolean(value: object, field: str) -> None:
    if not isinstance(value, bool):
        raise ValidationError(f"{field} must be a boolean")


def _validate_local_time(value: object, field: str) -> None:
    if not isinstance(value, str) or re.fullmatch(r"[0-2][0-9]:[0-5][0-9]", value) is None:
        raise ValidationError(f"{field} must use HH:MM local time")
    hour = int(value.split(":", 1)[0])
    if hour > 23:
        raise ValidationError(f"{field} must use a 24-hour local time")


def _validate_model_secret(model: dict[str, object]) -> None:
    api_key_secret = model["api_key_secret"]
    if model["mode"] == "hermes-auth":
        if api_key_secret != "":
            raise ValidationError("model.api_key_secret must be empty for hermes-auth mode")
        return
    _validate_secret_name(api_key_secret, "model.api_key_secret")


def _validate_secret_name(value: object, field: str) -> None:
    if not isinstance(value, str) or SECRET_NAME.fullmatch(value) is None:
        raise ValidationError(f"{field} must name an uppercase secret env bridge variable")
    if value.startswith("VITE_"):
        raise ValidationError(f"{field} must not use the client-exposed VITE_ prefix")


def _table(data: dict[str, object], key: str) -> dict[str, object]:
    value = data.get(key)
    if not isinstance(value, dict):
        raise ValidationError(f"{key} must be a table")
    return value


def _require_exact_keys(data: dict[str, object], expected: tuple[str, ...], label: str) -> None:
    actual = set(data)
    expected_set = set(expected)
    missing = sorted(expected_set - actual)
    extra = sorted(actual - expected_set)
    if missing or extra:
        raise ValidationError(f"{label} keys mismatch; missing={missing}, extra={extra}")


def _require_non_empty_strings(
    data: dict[str, object],
    keys: tuple[str, ...],
    label: str,
) -> None:
    for key in keys:
        if not isinstance(data.get(key), str) or not str(data[key]).strip():
            raise ValidationError(f"{label}.{key} must be a non-empty string")


def _require_unique(
    configs: list[ProfileConfig],
    label: str,
    get_value: Callable[[ProfileConfig], object],
) -> None:
    seen: dict[object, str] = {}
    for config in configs:
        value = get_value(config)
        owner = seen.get(value)
        if owner is not None:
            raise ValidationError(
                "multiple active Hermes profiles share "
                f"{label} {value}: {owner}, {config.profile_id}"
            )
        seen[value] = config.profile_id
