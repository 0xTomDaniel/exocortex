from __future__ import annotations

import hashlib
import json
import shutil
import tomllib
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Literal

from exo_distribution.config import ValidationError

SkillKind = Literal["safe_core", "external_action"]
SkillCategory = Literal["general", "personal"]
SourceAccess = Literal["repo-fixture", "fixture-fallback", "private-git-fallback"]
PlanAction = Literal["install", "replace", "up-to-date", "collision"]

UNPINNED_REFS = {"", "HEAD", "head", "main", "master", "latest"}
SOURCE_ACCESS: set[str] = {"repo-fixture", "fixture-fallback", "private-git-fallback"}
SKILL_KINDS: set[str] = {"safe_core", "external_action"}
SKILL_CATEGORIES: set[str] = {"general", "personal"}


@dataclass(frozen=True)
class SkillSource:
    id: str
    name: str
    kind: SkillKind
    category: SkillCategory
    repo: str
    path: str
    ref: str
    profile_targets: tuple[str, ...]
    install_destination: str
    source_of_truth: str
    approved: bool
    source_access: SourceAccess
    collision_policy: str
    sync_policy: str
    promotion_policy: str
    fallback_fixture: str | None = None
    operator_note: str | None = None

    def source_dir(self, repo_root: Path) -> Path:
        if self.source_access == "repo-fixture":
            return repo_root / self.path
        if self.fallback_fixture is None:
            raise ValidationError(f"{self.id} must declare fallback_fixture")
        return repo_root / self.fallback_fixture


@dataclass(frozen=True)
class SkillsManifest:
    path: Path
    default_install_root: str
    policy: dict[str, str]
    sources: tuple[SkillSource, ...]


@dataclass(frozen=True)
class SkillInstallPlan:
    source: SkillSource
    profile_id: str
    runtime_destination: PurePosixPath
    actual_destination: Path
    source_dir: Path
    action: PlanAction
    reason: str


def load_skills_manifest(path: Path, repo_root: Path) -> SkillsManifest:
    with path.open("rb") as manifest_file:
        data = tomllib.load(manifest_file)

    _require_exact_keys(
        data,
        ("manifest_version", "default_install_root", "policy", "sources"),
        "skills manifest",
    )
    if data["manifest_version"] != 1:
        raise ValidationError("skills manifest_version must be 1")
    default_install_root = _require_non_empty_string(
        data,
        "default_install_root",
        "skills manifest",
    )
    _validate_install_destination(
        default_install_root,
        default_install_root,
        "default_install_root",
    )

    policy = data["policy"]
    if not isinstance(policy, dict):
        raise ValidationError("skills manifest policy must be a table")
    _require_exact_keys(
        policy,
        ("source_of_truth", "collision_behavior", "sync_behavior", "production_boundary"),
        "skills policy",
    )
    policy_strings = {
        key: _require_non_empty_string(policy, key, f"skills policy.{key}")
        for key in policy
    }

    raw_sources = data["sources"]
    if not isinstance(raw_sources, list) or not raw_sources:
        raise ValidationError("skills manifest sources must be a non-empty array")

    sources = tuple(
        _parse_source(index, source, default_install_root)
        for index, source in enumerate(raw_sources)
    )
    _validate_sources(sources, default_install_root, repo_root)
    return SkillsManifest(
        path=path,
        default_install_root=default_install_root,
        policy=policy_strings,
        sources=sources,
    )


def plan_skill_install(
    manifest: SkillsManifest,
    profile_id: str,
    repo_root: Path,
    install_root: Path | None = None,
) -> list[SkillInstallPlan]:
    selected = [
        source
        for source in manifest.sources
        if source.approved and profile_id in source.profile_targets
    ]
    _reject_selected_manifest_collisions(selected)

    actual_root = install_root if install_root is not None else Path(manifest.default_install_root)
    if profile_id == "tom-personal-agent" and (actual_root / "team-weekly-planning").exists():
        raise ValidationError(
            "retired standalone team-weekly-planning remains installed; preserve and reconcile "
            "its edits into tom-operating-style/modules/team-weekly-planning, then move the "
            "old directory outside skill discovery before syncing"
        )
    plans: list[SkillInstallPlan] = []
    for source in selected:
        runtime_destination = PurePosixPath(source.install_destination)
        relative_destination = runtime_destination.relative_to(
            PurePosixPath(manifest.default_install_root)
        )
        actual_destination = actual_root / Path(*relative_destination.parts)
        source_dir = source.source_dir(repo_root)
        if not source_dir.is_dir():
            raise ValidationError(f"{source.id} source directory is missing: {source_dir}")
        _refuse_repo_owned_destination(repo_root, actual_destination)
        action, reason = _classify_existing_install(source, actual_destination)
        plans.append(
            SkillInstallPlan(
                source=source,
                profile_id=profile_id,
                runtime_destination=runtime_destination,
                actual_destination=actual_destination,
                source_dir=source_dir,
                action=action,
                reason=reason,
            )
        )
    return plans


def install_planned_skills(
    plans: list[SkillInstallPlan],
    manifest: SkillsManifest,
) -> list[SkillInstallPlan]:
    collisions = [plan for plan in plans if plan.action == "collision"]
    if collisions:
        details = ", ".join(f"{plan.source.id}: {plan.reason}" for plan in collisions)
        raise ValidationError(f"skill install collision: {details}")

    # Plans are reviewable snapshots, not permission to overwrite later edits.
    # Writers must remain stopped throughout this check and installation.
    for plan in plans:
        action, reason = _classify_existing_install(plan.source, plan.actual_destination)
        if action == "collision" or action != plan.action:
            raise ValidationError(f"skill install changed since planning: {plan.source.id}: {reason}")

    installed: list[SkillInstallPlan] = []
    for plan in plans:
        if plan.action == "up-to-date":
            installed.append(plan)
            continue
        if plan.action == "replace" and plan.actual_destination.exists():
            shutil.rmtree(plan.actual_destination)
        plan.actual_destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(plan.source_dir, plan.actual_destination,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        _write_source_metadata(plan, manifest)
        installed.append(plan)
    return installed


def _parse_source(index: int, data: object, default_install_root: str) -> SkillSource:
    if not isinstance(data, dict):
        raise ValidationError(f"skills source {index} must be a table")
    allowed = {
        "id",
        "name",
        "kind",
        "category",
        "repo",
        "path",
        "ref",
        "profile_targets",
        "install_destination",
        "source_of_truth",
        "approved",
        "source_access",
        "fallback_fixture",
        "operator_note",
        "collision_policy",
        "sync_policy",
        "promotion_policy",
    }
    extra = sorted(set(data) - allowed)
    if extra:
        raise ValidationError(f"skills source {index} has unknown keys: {extra}")

    source_id = _require_non_empty_string(data, "id", f"skills source {index}")
    name = _require_non_empty_string(data, "name", source_id)
    kind = _require_choice(data, "kind", SKILL_KINDS, source_id)
    category = _require_choice(data, "category", SKILL_CATEGORIES, source_id)
    repo = _require_non_empty_string(data, "repo", source_id)
    path = _require_non_empty_string(data, "path", source_id)
    ref = _require_non_empty_string(data, "ref", source_id)
    install_destination = _require_non_empty_string(data, "install_destination", source_id)
    source_of_truth = _require_non_empty_string(data, "source_of_truth", source_id)
    source_access = _require_choice(data, "source_access", SOURCE_ACCESS, source_id)
    collision_policy = _require_non_empty_string(data, "collision_policy", source_id)
    sync_policy = _require_non_empty_string(data, "sync_policy", source_id)
    promotion_policy = _require_non_empty_string(data, "promotion_policy", source_id)
    approved = data.get("approved")
    if not isinstance(approved, bool):
        raise ValidationError(f"{source_id}.approved must be a boolean")
    profile_targets = data.get("profile_targets")
    if not isinstance(profile_targets, list) or not all(
        isinstance(item, str) and item for item in profile_targets
    ):
        raise ValidationError(f"{source_id}.profile_targets must be a string array")
    fallback_fixture = data.get("fallback_fixture")
    if fallback_fixture is not None and not isinstance(fallback_fixture, str):
        raise ValidationError(f"{source_id}.fallback_fixture must be a string")
    operator_note = data.get("operator_note")
    if operator_note is not None and not isinstance(operator_note, str):
        raise ValidationError(f"{source_id}.operator_note must be a string")

    if ref in UNPINNED_REFS:
        raise ValidationError(f"{source_id}.ref must be pinned; got {ref!r}")
    if collision_policy != "fail":
        raise ValidationError(f"{source_id}.collision_policy must be fail")
    if sync_policy != "replace-if-ref-changed":
        raise ValidationError(f"{source_id}.sync_policy must be replace-if-ref-changed")
    if source_access != "repo-fixture" and not fallback_fixture:
        raise ValidationError(f"{source_id} requires fallback_fixture for {source_access}")
    if source_access != "repo-fixture" and not operator_note:
        raise ValidationError(
            f"{source_id} requires operator_note for fixture/private fallback access"
        )
    if kind == "external_action" and approved and not operator_note:
        raise ValidationError(
            f"{source_id} approved external-action skills require operator_note audit context"
        )
    _validate_relative_source_path(path, f"{source_id}.path")
    if fallback_fixture:
        _validate_relative_source_path(fallback_fixture, f"{source_id}.fallback_fixture")
    _validate_install_destination(install_destination, default_install_root, source_id)

    return SkillSource(
        id=source_id,
        name=name,
        kind=kind,  # type: ignore[arg-type]
        category=category,  # type: ignore[arg-type]
        repo=repo,
        path=path,
        ref=ref,
        profile_targets=tuple(profile_targets),
        install_destination=install_destination,
        source_of_truth=source_of_truth,
        approved=approved,
        source_access=source_access,  # type: ignore[arg-type]
        fallback_fixture=fallback_fixture,
        operator_note=operator_note,
        collision_policy=collision_policy,
        sync_policy=sync_policy,
        promotion_policy=promotion_policy,
    )


def _validate_sources(
    sources: tuple[SkillSource, ...],
    default_install_root: str,
    repo_root: Path,
) -> None:
    seen_ids: set[str] = set()
    for source in sources:
        if source.id in seen_ids:
            raise ValidationError(f"duplicate skills source id {source.id}")
        seen_ids.add(source.id)
        source_dir = source.source_dir(repo_root)
        if not source_dir.is_dir():
            raise ValidationError(f"{source.id} source directory is missing: {source_dir}")
        _validate_agent_skill_directory(repo_root, source_dir, source.name)
        _validate_install_destination(source.install_destination, default_install_root, source.id)


def _reject_selected_manifest_collisions(sources: list[SkillSource]) -> None:
    names: dict[str, str] = {}
    destinations: dict[str, str] = {}
    for source in sources:
        if source.name in names:
            raise ValidationError(
                f"skill name collision: {source.name} from {names[source.name]} "
                f"and {source.id}"
            )
        names[source.name] = source.id
        if source.install_destination in destinations:
            raise ValidationError(
                "skill install destination collision: "
                f"{source.install_destination} from "
                f"{destinations[source.install_destination]} and {source.id}"
            )
        destinations[source.install_destination] = source.id


def _classify_existing_install(
    source: SkillSource,
    actual_destination: Path,
) -> tuple[PlanAction, str]:
    if actual_destination.is_symlink():
        return "collision", "existing skill destination is a symlink"
    if not actual_destination.exists():
        return "install", "missing from runtime skills directory"
    metadata_path = actual_destination / ".exo-skill-source.json"
    if not metadata_path.is_file():
        return "collision", "existing skill has no Exo source metadata"
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return "collision", f"existing source metadata is invalid JSON: {exc}"
    if not isinstance(metadata, dict):
        return "collision", "existing source metadata must be an object"
    expected_identity = {
        "source_id": source.id,
        "repo": source.repo,
        "path": source.path,
    }
    for key, expected in expected_identity.items():
        if metadata.get(key) != expected:
            return (
                "collision",
                f"existing metadata {key}={metadata.get(key)!r} "
                f"does not match {expected!r}",
            )
    baseline = metadata.get("installed_files")
    if not isinstance(baseline, dict):
        return "collision", "existing install lacks a content baseline; preserve and reconcile it"
    if baseline != _installed_files(actual_destination):
        return "collision", "runtime skill content changed; preserve or promote edits before syncing"
    if metadata.get("ref") == source.ref:
        return "up-to-date", "installed ref already matches manifest"
    return (
        "replace",
        f"installed ref {metadata.get('ref')!r} differs from pinned ref {source.ref!r}",
    )


def _installed_files(root: Path) -> dict[str, str]:
    """Fingerprint installed content, excluding source metadata and Python caches."""
    files: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if (relative.as_posix() == ".exo-skill-source.json"
                or "__pycache__" in relative.parts or path.suffix == ".pyc"):
            continue
        if path.is_symlink():
            files[relative.as_posix()] = "symlink:" + str(path.readlink())
        elif path.is_file():
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            files[relative.as_posix()] = f"file:{path.stat().st_mode & 0o111}:{digest}"
        elif path.is_dir():
            files[relative.as_posix()] = "directory"
        else:
            files[relative.as_posix()] = "special"
    return files


def _write_source_metadata(plan: SkillInstallPlan, manifest: SkillsManifest) -> None:
    metadata = {
        "installed_files": _installed_files(plan.actual_destination),
        "manifest": str(manifest.path),
        "profile": plan.profile_id,
        "source_id": plan.source.id,
        "name": plan.source.name,
        "kind": plan.source.kind,
        "category": plan.source.category,
        "repo": plan.source.repo,
        "path": plan.source.path,
        "ref": plan.source.ref,
        "source_of_truth": plan.source.source_of_truth,
        "promotion_policy": plan.source.promotion_policy,
    }
    (plan.actual_destination / ".exo-skill-source.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _validate_install_destination(destination: str, default_install_root: str, label: str) -> None:
    path = PurePosixPath(destination)
    root = PurePosixPath(default_install_root)
    if not path.is_absolute():
        raise ValidationError(f"{label}.install_destination must be absolute")
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ValidationError(
            f"{label}.install_destination must be inside {default_install_root}"
        ) from exc


def _validate_relative_source_path(value: str, label: str) -> None:
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts:
        raise ValidationError(f"{label} must be a repo-relative path")


def _validate_agent_skill_directory(repo_root: Path, source_dir: Path, skill_name: str) -> None:
    try:
        source_dir.relative_to(repo_root / ".agents" / "skills")
    except ValueError as exc:
        raise ValidationError(
            f"{skill_name} source directory must live under .agents/skills"
        ) from exc
    if source_dir.parent != repo_root / ".agents" / "skills" or source_dir.name != skill_name:
        raise ValidationError(
            f"{skill_name} source directory must be flat at .agents/skills/{skill_name}"
        )

    skill_file = source_dir / "SKILL.md"
    if not skill_file.is_file():
        raise ValidationError(f"{skill_name} source directory must contain SKILL.md")

    text = skill_file.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValidationError(f"{skill_name} SKILL.md must start with YAML frontmatter")
    frontmatter_end = text.find("\n---", 4)
    if frontmatter_end == -1:
        raise ValidationError(f"{skill_name} SKILL.md frontmatter is not closed")
    frontmatter = text[4:frontmatter_end].splitlines()
    declared_name = None
    declared_description = None
    for line in frontmatter:
        stripped = line.strip()
        if stripped.startswith("name:"):
            declared_name = stripped.split(":", 1)[1].strip().strip('"').strip("'")
        if stripped.startswith("description:"):
            declared_description = stripped.split(":", 1)[1].strip()
    if declared_name != skill_name:
        raise ValidationError(
            f"{skill_name} SKILL.md name must match parent directory; got {declared_name!r}"
        )
    if declared_description == "":
        raise ValidationError(f"{skill_name} SKILL.md description must be non-empty")


def _refuse_repo_owned_destination(repo_root: Path, actual_destination: Path) -> None:
    repo = repo_root.resolve()
    destination = actual_destination.resolve(strict=False)
    try:
        destination.relative_to(repo)
    except ValueError:
        return
    raise ValidationError(
        f"refusing to install skills into repo-owned path {actual_destination}; "
        "use /opt/data/skills or a non-repo temporary install root"
    )


def _require_choice(data: dict[str, object], key: str, choices: set[str], label: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or value not in choices:
        raise ValidationError(f"{label}.{key} must be one of {sorted(choices)}")
    return value


def _require_non_empty_string(data: dict[str, object], key: str, label: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{label}.{key} must be a non-empty string")
    return value


def _require_exact_keys(data: dict[str, object], expected: tuple[str, ...], label: str) -> None:
    actual = set(data)
    expected_set = set(expected)
    missing = sorted(expected_set - actual)
    extra = sorted(actual - expected_set)
    if missing or extra:
        raise ValidationError(f"{label} keys mismatch; missing={missing}, extra={extra}")
