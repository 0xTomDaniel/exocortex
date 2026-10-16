from __future__ import annotations

from pathlib import Path

from exo_distribution.config import ProfileConfig


def render_hermes_config(config: ProfileConfig, template_path: Path) -> str:
    output = template_path.read_text(encoding="utf-8")
    replacements = _flatten(config.data)
    replacements["tools.safe_core_yaml"] = _safe_core_yaml(config)
    replacements["storage.placeholder_mounts_yaml"] = _placeholder_mounts_yaml(config)
    replacements["tools.external_actions.enabled"] = _yaml_bool(
        bool(config.data["tools"]["external_actions"]["enabled"])  # type: ignore[index]
    )
    for key, value in replacements.items():
        output = output.replace("{{ " + key + " }}", value)
    return output


def render_compose(configs: list[ProfileConfig], template_path: Path) -> str:
    output = template_path.read_text(encoding="utf-8")
    services = "\n\n".join(_compose_service(config) for config in configs)
    return output.replace("{{ hermes_services_yaml }}", services)


def _flatten(data: object, prefix: str = "") -> dict[str, str]:
    values: dict[str, str] = {}
    if isinstance(data, dict):
        for key, value in data.items():
            next_prefix = f"{prefix}.{key}" if prefix else str(key)
            values.update(_flatten(value, next_prefix))
    elif isinstance(data, bool):
        values[prefix] = _yaml_bool(data)
    elif isinstance(data, (str, int, float)):
        values[prefix] = str(data)
    return values


def _safe_core_yaml(config: ProfileConfig) -> str:
    tools = config.data["tools"]["safe_core"]  # type: ignore[index]
    return "\n".join(f'    - "{tool["name"]}"' for tool in tools)  # type: ignore[index]


def _placeholder_mounts_yaml(config: ProfileConfig) -> str:
    mounts = config.data["storage"]["placeholder_mounts"]  # type: ignore[index]
    if not mounts:
        return "    []"
    lines: list[str] = []
    for mount in mounts:  # type: ignore[assignment]
        lines.extend(
            [
                f'    - name: "{mount["name"]}"',
                f'      kind: "{mount["kind"]}"',
                f'      path: "{mount["path"]}"',
                f'      mount_path: "{mount["mount_path"]}"',
                f'      access: "{mount["access"]}"',
                f'      permissions: "{mount["permissions"]}"',
                f'      backup: "{mount["backup"]}"',
                f'      recovery: "{mount["recovery"]}"',
                "      allowed_write_paths: []",
            ]
        )
    return "\n".join(lines)


def _compose_service(config: ProfileConfig) -> str:
    data = config.data
    container = data["container"]  # type: ignore[index]
    hermes = data["hermes"]  # type: ignore[index]
    telegram = data["telegram"]  # type: ignore[index]
    model = data["model"]  # type: ignore[index]
    phase = data["phase"]  # type: ignore[index]
    storage = data["storage"]  # type: ignore[index]
    logs = data["logs"]  # type: ignore[index]
    backups = data["backups"]  # type: ignore[index]

    service_name = str(config.profile_id).replace("_", "-")
    runtime_container_path = storage["runtime"]["container_path"]  # type: ignore[index]
    workspace_container_path = "/workspace"
    telegram_token_container_path = "/run/secrets/telegram-bot-token"
    lines = [
        f"  {service_name}:",
        f'    image: "{container["image"]}"',
        f'    container_name: "{container["name"]}"',
        f'    restart: "{container["restart_policy"]}"',
        '    command: "gateway run"',
        "    env_file:",
        f'      - "${{EXO_RUNTIME_ROOT}}/{config.profile_id}/secret-bridge/provider.env"',
        "    environment:",
        f'      HERMES_PROFILE_ID: "{config.profile_id}"',
        f'      HERMES_HOME: "{runtime_container_path}"',
        f'      HERMES_WORKSPACE: "{workspace_container_path}"',
        f'      TERMINAL_CWD: "{workspace_container_path}"',
        f'      TELEGRAM_BOT_TOKEN_FILE: "{telegram_token_container_path}"',
        f'      TELEGRAM_OWNER_ID_SECRET: "{telegram["owner_id_secret"]}"',
        f'      PHASE_APP: "{phase["app"]}"',
        f'      PHASE_ENVIRONMENT: "{phase["environment"]}"',
        f'      PHASE_PATH: "{phase["path"]}"',
        "    volumes:",
        (
            f'      - "{hermes["home"]}:{storage["runtime"]["container_path"]}:rw"'
        ),  # type: ignore[index]
        f'      - "{hermes["workspace"]}:{workspace_container_path}"',
        f'      - "{telegram["token_path"]}:{telegram_token_container_path}:ro"',
        f'      - "${{EXO_RUNTIME_ROOT}}/{config.profile_id}/skills:/opt/data/skills"',
        (
            f'      - "{storage["vault"]["path"]}:{storage["vault"]["container_path"]}:rw"'
        ),  # type: ignore[index]
        (
            f'      - "{storage["personal_files"]["path"]}:'
            f'{storage["personal_files"]["container_path"]}:ro"'
        ),  # type: ignore[index]
        f'      - "{logs["path"]}:/var/log/hermes"',
        f'      - "{backups["path"]}:/opt/backups"',
    ]
    if model["api_key_secret"]:
        lines.insert(
            lines.index(f'      PHASE_APP: "{phase["app"]}"'),
            f'      MODEL_API_KEY_SECRET: "{model["api_key_secret"]}"',
        )
    for mount in storage["placeholder_mounts"]:  # type: ignore[index]
        mode = "ro" if mount["access"] == "read-only" else "rw"
        lines.append(f'      - "{mount["path"]}:{mount["mount_path"]}:{mode}"')
    return "\n".join(lines)


def _yaml_bool(value: bool) -> str:
    return "true" if value else "false"
