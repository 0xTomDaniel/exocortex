from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from exo_distribution.config import (
    ProfileConfig,
    ValidationError,
    discover_profile_paths,
    load_profile_config,
    schema_summary,
    validate_profile_set,
)
from exo_distribution.deploy import build_deploy_plan, load_deploy_target
from exo_distribution.proactive import run_fake_proactive_smoke
from exo_distribution.render import render_compose, render_hermes_config
from exo_distribution.skills import (
    install_planned_skills,
    load_skills_manifest,
    plan_skill_install,
)
from exo_distribution.smoke import run_fake_telegram_smoke
from exo_distribution.storage import read_fake_sync_health, storage_mount_declarations


REPO_ROOT = Path(__file__).resolve().parents[1]
PROFILE = REPO_ROOT / "profiles/tom-local-dev/profile.toml"
SCHEMA = REPO_ROOT / "schemas/profile-config.schema.json"
TEMPLATE = REPO_ROOT / "profiles/tom-local-dev/hermes/config.yaml.template"
GENERATED = REPO_ROOT / "profiles/tom-local-dev/generated/config.yaml"
COMPOSE_TEMPLATE = REPO_ROOT / "deploy/compose/hermes-multi-owner.compose.yaml.template"
COMPOSE_GENERATED = REPO_ROOT / "deploy/compose/generated/hermes-multi-owner.compose.yaml"
ENV_EXAMPLE = REPO_ROOT / ".env.example"
SKILLS_MANIFEST = REPO_ROOT / "skills/sources.toml"
AGENT_SKILLS = REPO_ROOT / ".agents/skills"
REMOTE_TARGET = REPO_ROOT / "deploy/remote/mock-target.toml"
HUMAN_REVIEW_CHECKLIST = REPO_ROOT / "docs/human-review-checklist.md"
SOUL = REPO_ROOT / "SOUL.md"
AGENTS = REPO_ROOT / "AGENTS.md"
TOM_OPERATING_STYLE = AGENT_SKILLS / "tom-operating-style/SKILL.md"
TOM_OPERATING_PATTERNS = AGENT_SKILLS / "tom-operating-style/references/operating-patterns.md"
PLANNING_RHYTHM_DAILY = AGENT_SKILLS / "planning-rhythm-os/references/daily-rhythm.md"
OBSIDIAN_SKILL = AGENT_SKILLS / "obsidian/SKILL.md"
TEAM_WEEKLY_SKILL = AGENT_SKILLS / "tom-operating-style/modules/team-weekly-planning/guide.md"
TEAM_WEEKLY_ICP = AGENT_SKILLS / "tom-operating-style/modules/team-weekly-planning/references/icp-qualification.md"


class TomLocalDistributionTest(unittest.TestCase):
    def test_profile_validates_against_checked_in_contract(self) -> None:
        self.assertIn("Exo Hermes Profile Config", schema_summary(SCHEMA))
        config = load_profile_config(PROFILE)
        self.assertEqual(config.profile_id, "tom-local-dev")

    def test_multi_owner_profiles_have_isolated_runtime_boundaries(self) -> None:
        configs = [
            load_profile_config(path)
            for path in discover_profile_paths(REPO_ROOT / "profiles")
        ]
        validate_profile_set(configs)
        by_id = {config.profile_id: config for config in configs}
        self.assertIn("tom-personal-agent", by_id)
        self.assertIn("alex-personal-agent", by_id)
        self.assertIn("sam-personal-agent", by_id)

        owner_profiles = [
            by_id["tom-personal-agent"],
            by_id["alex-personal-agent"],
            by_id["sam-personal-agent"],
        ]
        self.assertEqual(
            {
                config.data["profile"]["owner_name"]  # type: ignore[index]
                for config in owner_profiles
            },
            {"Tom Daniel", "Alex Example", "Sam Example"},
        )
        for config in owner_profiles:
            role = config.data["profile"]["role"]  # type: ignore[index]
            self.assertIn("Exo executive assistant", role)
            self.assertNotIn("Hermes executive assistant", role)
        self.assertEqual(len({config.hermes_home for config in owner_profiles}), 3)
        self.assertEqual(len({config.telegram_token_path for config in owner_profiles}), 3)
        self.assertEqual(len({config.log_path for config in owner_profiles}), 3)
        self.assertEqual(len({config.backup_path for config in owner_profiles}), 3)

    def test_soul_pins_exo_as_user_facing_identity(self) -> None:
        content = SOUL.read_text(encoding="utf-8")
        self.assertIn("Your name is Exo.", content)
        self.assertIn("Hermes is the runtime and infrastructure layer", content)
        self.assertIn("Do not say \"I am Hermes\"", content)

    def test_agents_md_records_shared_exo_runtime_policy(self) -> None:
        content = AGENTS.read_text(encoding="utf-8")
        self.assertIn("Agent name: **Exo**.", content)
        self.assertIn("Hermes is the runtime and infrastructure layer", content)
        self.assertIn("tom-operating-style", content)
        self.assertIn("owner-only Telegram text", content)
        self.assertIn("/workspace/AGENTS.md", content)

    def test_imported_exocortex_operating_rules_are_captured_in_skills(self) -> None:
        # The owner's personal skill content is private (placeholder in the public distribution);
        # only the shared planning and note skills are checked for captured operating rules.
        daily_rhythm = PLANNING_RHYTHM_DAILY.read_text(encoding="utf-8")
        obsidian_skill = OBSIDIAN_SKILL.read_text(encoding="utf-8")
        for path in (TOM_OPERATING_STYLE, TOM_OPERATING_PATTERNS, TEAM_WEEKLY_SKILL, TEAM_WEEKLY_ICP):
            self.assertIn("lives only in the owner's private vault", path.read_text(encoding="utf-8"))
        self.assertIn("Core habits: water, meditation, movement/training", daily_rhythm)
        self.assertIn("Named scheduled rituals and recovery-aware habits", daily_rhythm)
        self.assertIn("Prefer Obsidian CLI for note creation", obsidian_skill)
        self.assertIn("Bases for structured tracking", obsidian_skill)

    def test_rendered_hermes_config_matches_committed_example(self) -> None:
        config = load_profile_config(PROFILE)
        rendered = render_hermes_config(config, TEMPLATE)
        self.assertEqual(rendered, GENERATED.read_text(encoding="utf-8"))
        self.assertIn('token_env: "TELEGRAM_BOT_TOKEN"', rendered)
        self.assertIn(
            'token_path: "${EXO_RUNTIME_ROOT}/tom-local-dev/secret-bridge/telegram-bot-token"',
            rendered,
        )
        self.assertNotIn("fake-token-not-live", rendered)

    def test_rendered_compose_declares_one_container_per_instance(self) -> None:
        configs = [
            load_profile_config(path)
            for path in discover_profile_paths(REPO_ROOT / "profiles")
        ]
        validate_profile_set(configs)
        rendered = render_compose(
            [
                config
                for config in configs
                if config.data["profile"]["intended_profile"]  # type: ignore[index]
                == "installable-template"
            ],
            COMPOSE_TEMPLATE,
        )
        self.assertEqual(rendered, COMPOSE_GENERATED.read_text(encoding="utf-8"))
        for profile_id in (
            "tom-personal-agent",
            "alex-personal-agent",
            "sam-personal-agent",
        ):
            self.assertIn(f"{profile_id}:", rendered)
            self.assertIn(f"${{EXO_RUNTIME_ROOT}}/{profile_id}/hermes-home", rendered)
            self.assertIn(
                f'    env_file:\n      - "${{EXO_RUNTIME_ROOT}}/{profile_id}/secret-bridge/provider.env"',
                rendered,
            )
            self.assertIn(
                f"${{EXO_RUNTIME_ROOT}}/{profile_id}/secret-bridge/telegram-bot-token",
                rendered,
            )
            self.assertIn(f"${{EXO_RUNTIME_ROOT}}/{profile_id}/skills:/opt/data/skills", rendered)
            self.assertIn(f"${{EXO_RUNTIME_ROOT}}/{profile_id}/log-boundary", rendered)
            self.assertIn(f"${{EXO_RUNTIME_ROOT}}/{profile_id}/backup-boundary", rendered)
        self.assertEqual(rendered.count("/opt/data/hermes-home"), 6)
        self.assertEqual(rendered.count('HERMES_HOME: "/opt/data/hermes-home"'), 3)
        self.assertEqual(rendered.count('HERMES_WORKSPACE: "/workspace"'), 3)
        self.assertEqual(rendered.count('TERMINAL_CWD: "/workspace"'), 3)
        self.assertEqual(
            rendered.count('TELEGRAM_BOT_TOKEN_FILE: "/run/secrets/telegram-bot-token"'),
            3,
        )
        self.assertEqual(rendered.count("/opt/data/skills"), 3)
        self.assertEqual(rendered.count(":/opt/data/hermes-home:rw"), 3)
        self.assertEqual(rendered.count(":/opt/data/vault:rw"), 3)
        self.assertEqual(rendered.count(":/mnt/personal-files:ro"), 3)
        self.assertNotIn("tom-local-dev:", rendered)

    def test_storage_contract_declares_zones_and_write_boundaries(self) -> None:
        config = load_profile_config(PROFILE)
        mounts = storage_mount_declarations(config)
        by_zone = {mount.zone: mount for mount in mounts}

        self.assertEqual(
            set(by_zone),
            {"runtime", "vault", "personal_files", "placeholder:calendar-export"},
        )
        self.assertEqual(by_zone["runtime"].container_path, "/opt/data/hermes-home")
        self.assertEqual(by_zone["runtime"].access, "read-write")
        self.assertEqual(by_zone["runtime"].allowed_write_paths, ("/opt/data/hermes-home",))
        self.assertEqual(by_zone["vault"].kind, "markdown-vault")
        self.assertEqual(by_zone["vault"].allowed_write_paths, ("/opt/data/vault",))
        self.assertEqual(by_zone["personal_files"].access, "read-only")
        self.assertEqual(by_zone["personal_files"].allowed_write_paths, ())
        self.assertEqual(by_zone["placeholder:calendar-export"].allowed_write_paths, ())
        for mount in mounts:
            self.assertIn("${EXO_RUNTIME_ROOT}", mount.host_path)
            self.assertTrue(mount.permissions)
            self.assertTrue(mount.backup)
            self.assertTrue(mount.recovery)

    def test_fake_storage_sync_health_covers_all_placeholder_states(self) -> None:
        config = load_profile_config(PROFILE)
        health = read_fake_sync_health(config, REPO_ROOT)

        self.assertEqual(
            {state.status for state in health},
            {"healthy", "stale", "errored", "unavailable"},
        )
        self.assertEqual(
            {state.zone for state in health},
            {"runtime", "vault", "personal_files", "placeholder:calendar-export"},
        )

    def test_installable_owner_storage_sync_health_matches_declared_mounts(self) -> None:
        for profile_path in (
            REPO_ROOT / "profiles/tom-personal-agent/profile.toml",
            REPO_ROOT / "profiles/alex-personal-agent/profile.toml",
            REPO_ROOT / "profiles/sam-personal-agent/profile.toml",
        ):
            with self.subTest(profile=profile_path.parent.name):
                config = load_profile_config(profile_path)
                mounts = storage_mount_declarations(config)
                health = read_fake_sync_health(config, REPO_ROOT)

                self.assertEqual(
                    {state.zone for state in health},
                    {mount.zone for mount in mounts},
                )
                self.assertIn("placeholder:personal-documents", {state.zone for state in health})
                self.assertEqual(
                    {state.status for state in health},
                    {"healthy", "stale", "errored", "unavailable"},
                )

    def test_storage_sync_health_rejects_undeclared_fixture_zones(self) -> None:
        config = load_profile_config(REPO_ROOT / "profiles/tom-personal-agent/profile.toml")
        data = copy.deepcopy(config.data)
        data["smoke"]["storage_sync_fixture"] = (  # type: ignore[index]
            "profiles/tom-local-dev/fixtures/storage/sync-health.json"
        )
        mismatched_config = ProfileConfig(path=config.path, data=data)

        with self.assertRaisesRegex(
            ValidationError,
            "missing declared zones: placeholder:personal-documents; "
            "unexpected zones: placeholder:calendar-export",
        ):
            read_fake_sync_health(mismatched_config, REPO_ROOT)

    def test_storage_contract_command_uses_fake_local_fixture(self) -> None:
        result = subprocess.run(
            [sys.executable, "scripts/check_storage_contract.py"],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertIn('"profile": "tom-local-dev"', result.stdout)
        self.assertIn('"zone": "runtime"', result.stdout)
        self.assertIn('"status": "unavailable"', result.stdout)

    def test_fake_telegram_smoke_replies_only_to_owner(self) -> None:
        config = load_profile_config(PROFILE)
        replies = run_fake_telegram_smoke(config, REPO_ROOT)
        self.assertEqual(
            replies,
            [
                {
                    "chat_id": "fake-tom-owner",
                    "text": (
                        "Tom local/dev Exo is loaded with fake Telegram "
                        "and safe-core tools only."
                    ),
                }
            ],
        )

    def test_proactive_config_controls_owner_check_ins_and_health_pings(self) -> None:
        config = load_profile_config(PROFILE)
        proactive = config.data["proactive"]  # type: ignore[index]
        check_ins = proactive["check_ins"]  # type: ignore[index]
        health_pings = proactive["health_pings"]  # type: ignore[index]

        self.assertTrue(proactive["enabled"])  # type: ignore[index]
        self.assertEqual(proactive["target_profile_id"], "tom-local-dev")  # type: ignore[index]
        self.assertEqual(
            proactive["delivery_surface"],  # type: ignore[index]
            "telegram-owner-text",
        )
        self.assertEqual(check_ins["morning_local_time"], "09:00")
        self.assertEqual(check_ins["evening_local_time"], "18:00")
        self.assertEqual(health_pings["provider"], "fake-local")

    def test_fake_proactive_smoke_delivers_only_owner_telegram_texts(self) -> None:
        config = load_profile_config(PROFILE)
        deliveries = run_fake_proactive_smoke(config, REPO_ROOT)

        self.assertEqual({delivery["chat_id"] for delivery in deliveries}, {"fake-tom-owner"})
        self.assertEqual(
            [delivery["kind"] for delivery in deliveries],
            [
                "morning_check_in",
                "evening_check_in",
                "health_service",
                "health_sync",
                "health_storage_safety",
                "health_deployment",
            ],
        )
        for delivery in deliveries:
            self.assertNotIn("fake-non-owner", delivery["text"])

    def test_proactive_disabled_state_sends_nothing(self) -> None:
        config = load_profile_config(PROFILE)
        data = copy.deepcopy(config.data)
        data["proactive"]["enabled"] = False  # type: ignore[index]
        disabled_config = ProfileConfig(path=config.path, data=data)

        self.assertEqual(run_fake_proactive_smoke(disabled_config, REPO_ROOT), [])

    def test_health_problem_reporting_uses_fake_local_provider(self) -> None:
        config = load_profile_config(PROFILE)
        deliveries = run_fake_proactive_smoke(config, REPO_ROOT)
        health_texts = [
            delivery["text"]
            for delivery in deliveries
            if delivery["kind"].startswith("health_")
        ]

        self.assertEqual(len(health_texts), 4)
        self.assertTrue(any("(service)" in text for text in health_texts))
        self.assertTrue(any("(sync)" in text for text in health_texts))
        self.assertTrue(any("(storage_safety)" in text for text in health_texts))
        self.assertTrue(any("(deployment)" in text for text in health_texts))
        self.assertTrue(any("critical" in text for text in health_texts))

    def test_smoke_command_uses_no_live_credentials(self) -> None:
        result = subprocess.run(
            [sys.executable, "scripts/smoke_tom_local.py"],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        self.assertIn('"profile": "tom-local-dev"', result.stdout)
        self.assertIn("fake Telegram", result.stdout)
        self.assertIn('"kind": "morning_check_in"', result.stdout)
        self.assertIn('"kind": "health_storage_safety"', result.stdout)

    def test_env_example_is_secret_only_and_blank(self) -> None:
        content = ENV_EXAMPLE.read_text(encoding="utf-8")
        self.assertIn("TELEGRAM_BOT_TOKEN=", content)
        self.assertIn("TELEGRAM_OWNER_ID=", content)
        self.assertIn("OPENAI_API_KEY=", content)
        for line in content.splitlines():
            self.assertFalse(line.startswith("VITE_"), line)
            if line and not line.startswith("#") and "=" in line:
                self.assertTrue(line.endswith("="), line)

    def test_human_review_checklist_records_parent_prd_readiness_boundaries(self) -> None:
        content = HUMAN_REVIEW_CHECKLIST.read_text(encoding="utf-8")

        for issue_key in (
            "EMB-445",
            "EMB-446",
            "EMB-447",
            "EMB-448",
            "EMB-449",
            "EMB-450",
            "EMB-451",
        ):
            self.assertIn(issue_key, content)
        self.assertIn("EMB-261 remains the only final PR", content)
        self.assertIn("No child-owned final PR should be opened or attached for EMB-451", content)
        self.assertIn("Human Review requires one real bot token and one real owner account", content)
        self.assertIn("EMB-276 owns live ESXi VM provisioning and deployment proof", content)
        self.assertIn("EMB-317 owns storage provider/topology selection and live mount proof", content)
        self.assertIn("Ordinary CI, Agent Review, and Agent QA must not require real Telegram", content)
        self.assertIn("send `/reset` or `/new` in Telegram", content)
        self.assertIn("explicit operator-approved `hermes sessions delete`", content)

    def test_identity_updates_require_explicit_session_reset_guidance(self) -> None:
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        remote_readme = (REPO_ROOT / "deploy/remote/README.md").read_text(encoding="utf-8")
        spec = (REPO_ROOT / "spec/domains/hermes-personal-agent-distribution.md").read_text(
            encoding="utf-8"
        )

        for content in (readme, remote_readme, spec):
            self.assertIn("/reset", content)
            self.assertIn("/new", content)
            self.assertIn("hermes sessions delete", content)
            self.assertIn("not silently", content)

    def test_no_private_runtime_state_is_committed(self) -> None:
        forbidden_parts = {
            "runtime",
            "data",
            "hermes-home",
            "memories",
            "sessions",
            "logs",
            "backups",
            "personal-files",
            ".phase",
        }
        for path in REPO_ROOT.rglob("*"):
            if ".git" in path.parts or ".venv" in path.parts:
                continue
            relative_parts = set(path.relative_to(REPO_ROOT).parts)
            self.assertTrue(relative_parts.isdisjoint(forbidden_parts), path)

    def test_skills_manifest_records_pinned_multi_repo_sources(self) -> None:
        manifest = load_skills_manifest(SKILLS_MANIFEST, REPO_ROOT)
        self.assertEqual(manifest.default_install_root, "/opt/data/skills")
        sources_by_id = {source.id: source for source in manifest.sources}
        self.assertEqual(
            {
                path.name
                for path in AGENT_SKILLS.iterdir()
                if path.is_dir()
            },
            {
                "agent-browser",
                "asset-assessment",
                "exo-daily-brief",
                "hermes-file-brief",
                "meow",
                "obsidian",
                "planning-capture-os",
                "planning-rhythm-os",
                "planning-task-os",
                "private-calendar-audit",
                "save-video-content",
                "skill-creator",
                "tom-operating-style",
                "tutor",
            },
        )
        self.assertEqual(
            sources_by_id["exo.daily_brief"].repo,
            "github.com/0xTomDaniel/exo-executive-agent",
        )
        self.assertEqual(sources_by_id["exo.daily_brief"].path, ".agents/skills/exo-daily-brief")
        self.assertEqual(
            sources_by_id["hermes.file_brief"].repo,
            "github.com/hermes-fixtures/core-skills",
        )
        self.assertEqual(
            sources_by_id["hermes.file_brief"].fallback_fixture,
            ".agents/skills/hermes-file-brief",
        )
        self.assertFalse(sources_by_id["private.calendar_audit"].approved)
        self.assertEqual(sources_by_id["exo.tom_operating_style"].category, "personal")
        self.assertEqual(
            sources_by_id["exo.tom_operating_style"].profile_targets,
            ("tom-personal-agent",),
        )
        for source_id in ("exo.meow", "exo.asset_assessment"):
            self.assertFalse(sources_by_id[source_id].approved)
            self.assertEqual(sources_by_id[source_id].profile_targets, ())
        self.assertFalse(sources_by_id["exo.agent_browser"].approved)
        self.assertFalse(sources_by_id["exo.obsidian"].approved)
        self.assertFalse(sources_by_id["exo.save_video_content"].approved)
        self.assertFalse(sources_by_id["exo.skill_creator"].approved)
        for source in manifest.sources:
            self.assertNotIn(source.ref, {"HEAD", "main", "master", "latest"})
            self.assertTrue(source.install_destination.startswith("/opt/data/skills/"))
            self.assertEqual(source.source_dir(REPO_ROOT).parent, AGENT_SKILLS)
            self.assertTrue((source.source_dir(REPO_ROOT) / "SKILL.md").is_file())

    def test_profile_specific_skill_plan_excludes_unapproved_private_source(self) -> None:
        manifest = load_skills_manifest(SKILLS_MANIFEST, REPO_ROOT)
        plans = plan_skill_install(
            manifest,
            "tom-local-dev",
            REPO_ROOT,
            install_root=Path("/tmp/exo-skills"),
        )
        self.assertEqual(
            [plan.source.id for plan in plans],
            ["exo.daily_brief", "hermes.file_brief"],
        )
        self.assertEqual(
            [str(plan.runtime_destination) for plan in plans],
            ["/opt/data/skills/exo-daily-brief", "/opt/data/skills/hermes-file-brief"],
        )
        self.assertEqual(plan_skill_install(manifest, "unknown-profile", REPO_ROOT), [])
        tom_plans = plan_skill_install(
            manifest,
            "tom-personal-agent",
            REPO_ROOT,
            install_root=Path("/tmp/exo-skills"),
        )
        self.assertEqual(
            [plan.source.id for plan in tom_plans],
            [
                "exo.planning_capture_os",
                "exo.planning_rhythm_os",
                "exo.planning_task_os",
                "exo.tutor",
                "exo.tom_operating_style",
            ],
        )
        self.assertNotIn("exo.obsidian", [plan.source.id for plan in tom_plans])

    def test_skill_installer_installs_updates_and_refuses_unmanaged_collisions(self) -> None:
        manifest = load_skills_manifest(SKILLS_MANIFEST, REPO_ROOT)
        with tempfile.TemporaryDirectory() as tmp:
            install_root = Path(tmp) / "skills"
            plans = plan_skill_install(
                manifest,
                "tom-local-dev",
                REPO_ROOT,
                install_root=install_root,
            )
            self.assertEqual([plan.action for plan in plans], ["install", "install"])
            install_planned_skills(plans, manifest)
            self.assertTrue((install_root / "exo-daily-brief/SKILL.md").is_file())
            metadata = install_root / "exo-daily-brief/.exo-skill-source.json"
            self.assertIn('"source_id": "exo.daily_brief"', metadata.read_text(encoding="utf-8"))

            up_to_date = plan_skill_install(
                manifest,
                "tom-local-dev",
                REPO_ROOT,
                install_root=install_root,
            )
            self.assertEqual([plan.action for plan in up_to_date], ["up-to-date", "up-to-date"])

            updated_manifest_path = Path(tmp) / "sources-updated.toml"
            updated_manifest_path.write_text(
                SKILLS_MANIFEST.read_text(encoding="utf-8").replace(
                    "fixture-2026-05-28-core-v2",
                    "fixture-2026-05-28-core-v3",
                    1,
                ),
                encoding="utf-8",
            )
            updated_manifest = load_skills_manifest(updated_manifest_path, REPO_ROOT)
            update_plan = plan_skill_install(
                updated_manifest,
                "tom-local-dev",
                REPO_ROOT,
                install_root=install_root,
            )
            self.assertEqual([plan.action for plan in update_plan], ["replace", "up-to-date"])

        with tempfile.TemporaryDirectory() as tmp:
            install_root = Path(tmp) / "skills"
            unmanaged = install_root / "exo-daily-brief"
            unmanaged.mkdir(parents=True)
            (unmanaged / "SKILL.md").write_text("# Runtime-created skill\n", encoding="utf-8")
            collision_plan = plan_skill_install(
                manifest,
                "tom-local-dev",
                REPO_ROOT,
                install_root=install_root,
            )
            self.assertEqual(collision_plan[0].action, "collision")
            with self.assertRaisesRegex(Exception, "existing skill has no Exo source metadata"):
                install_planned_skills(collision_plan, manifest)

    def test_skill_installer_refuses_repo_owned_install_roots(self) -> None:
        manifest = load_skills_manifest(SKILLS_MANIFEST, REPO_ROOT)
        with self.assertRaisesRegex(Exception, "refusing to install skills into repo-owned path"):
            plan_skill_install(
                manifest,
                "tom-local-dev",
                REPO_ROOT,
                install_root=REPO_ROOT / "skills",
            )

    def test_install_skills_command_can_apply_to_fixture_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/install_skills.py",
                    "--profile",
                    "tom-local-dev",
                    "--install-root",
                    str(Path(tmp) / "skills"),
                    "--apply",
                ],
                cwd=REPO_ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertIn('"mode": "apply"', result.stdout)
            self.assertIn(
                '"runtime_destination": "/opt/data/skills/exo-daily-brief"',
                result.stdout,
            )

    def test_remote_deploy_plan_covers_mock_ssh_workflow(self) -> None:
        target = load_deploy_target(REMOTE_TARGET)
        configs = [
            load_profile_config(path)
            for path in discover_profile_paths(REPO_ROOT / "profiles")
        ]
        validate_profile_set(configs)
        plan = build_deploy_plan(target, configs)
        step_names = [step["name"] for step in plan["steps"]]  # type: ignore[index]

        self.assertEqual(plan["profiles"], [  # type: ignore[index]
            "alex-personal-agent",
            "sam-personal-agent",
            "tom-personal-agent",
        ])
        self.assertEqual(
            step_names,
            [
                "prerequisite-checks",
                "validate-toml-configs",
                "render-compose-and-profile-templates",
                "copy-distribution-material",
                "create-instance-runtime-boundaries",
                "install-or-update-profile-material",
                "materialize-phase-secret-bridges",
                "stop-profile-writers-before-skill-sync",
                "install-or-sync-profile-skills",
                "normalize-container-runtime-ownership",
                "compose-start-or-restart",
                "health-checks",
                "status-and-log-inspection",
                "backup-restore-and-redeploy-reference",
            ],
        )
        command_text = json.dumps(plan["steps"])
        steps_by_name = {
            step["name"]: step
            for step in plan["steps"]  # type: ignore[index]
        }
        prereq_commands = "\n".join(
            steps_by_name["prerequisite-checks"]["commands"]  # type: ignore[index]
        )
        compose_command_list = [
            command
            for step_name in (
                "compose-start-or-restart",
                "health-checks",
                "status-and-log-inspection",
                "backup-restore-and-redeploy-reference",
            )
            for command in steps_by_name[step_name]["commands"]  # type: ignore[index]
            if "docker compose" in command
        ]
        compose_commands = "\n".join(compose_command_list)
        secret_bridge_commands = "\n".join(
            steps_by_name["materialize-phase-secret-bridges"]["commands"]  # type: ignore[index]
        )
        ownership_commands = "\n".join(
            steps_by_name["normalize-container-runtime-ownership"]["commands"]  # type: ignore[index]
        )
        copy_commands = "\n".join(
            steps_by_name["copy-distribution-material"]["commands"]  # type: ignore[index]
        )
        self.assertIn("scripts/validate_profile.py --all", command_text)
        self.assertIn("scripts/render_compose.py", command_text)
        self.assertIn("scripts/install_skills.py", command_text)
        self.assertIn("sudo env PATH", command_text)
        self.assertIn("UV_PROJECT_ENVIRONMENT=/tmp/exo-executive-agent-venv", command_text)
        self.assertIn("docker compose", command_text)
        self.assertIn("/SOUL.md", command_text)
        self.assertIn("/hermes-home/SOUL.md", command_text)
        self.assertIn("/AGENTS.md", command_text)
        self.assertIn("/workspace/AGENTS.md", command_text)
        self.assertIn("sudo install -o 10000 -g 10000 -m 0640", command_text)
        self.assertIn("Captain Exo", command_text)
        self.assertIn("They call me Exo", command_text)
        self.assertIn("cwd: /workspace", command_text)
        self.assertIn("command -v uv", prereq_commands)
        self.assertIn("command -v phase", prereq_commands)
        self.assertIn("command -v rsync", prereq_commands)
        self.assertIn("nousresearch/hermes-agent:latest", COMPOSE_GENERATED.read_text())
        self.assertIn('command: "gateway run"', COMPOSE_GENERATED.read_text())
        self.assertGreaterEqual(len(compose_command_list), 6)
        for command in compose_command_list:
            self.assertIn("EXO_RUNTIME_ROOT=/srv/exo/hermes docker compose", command)
        self.assertIn("cd /opt/exo/exo-executive-agent &&", secret_bridge_commands)
        self.assertIn("--app", secret_bridge_commands)
        self.assertIn("personal agent", secret_bridge_commands)
        self.assertIn(
            "./deploy/remote/materialize-secret-bridge.sh",
            secret_bridge_commands,
        )
        self.assertIn("sudo chown -R 10000:10000", ownership_commands)
        self.assertIn("telegram-bot-token", ownership_commands)
        for excluded_path in (
            ".phase",
            "phase-export*",
            "secret-bridge",
            "provider.env",
            "hermes-home",
            "logs",
            "backups",
            "personal-files",
            "memories",
            "sessions",
        ):
            self.assertIn(excluded_path, copy_commands)
        self.assertIn("--include .env.example", copy_commands)
        self.assertGreaterEqual(copy_commands.count("--exclude"), 15)
        self.assertIn("logs --tail 100", command_text)
        self.assertIn("restart", command_text)
        self.assertIn(
            "Live ESXi execution is Human Review/HITL",
            plan["live_esxi_boundary"],  # type: ignore[index]
        )

    def test_remote_deploy_secret_bridge_plan_is_non_secret_and_instance_local(self) -> None:
        target = load_deploy_target(REMOTE_TARGET)
        configs = [
            load_profile_config(path)
            for path in discover_profile_paths(REPO_ROOT / "profiles")
        ]
        plan = build_deploy_plan(target, configs)

        for bridge in plan["secret_bridges"]:  # type: ignore[index]
            if bridge["profile_id"] == "tom-personal-agent":
                self.assertEqual(bridge["phase"]["app"], "Tom's personal agent")
            else:
                self.assertEqual(bridge["phase"]["app"], "exo-executive-agent")
            self.assertEqual(bridge["phase"]["environment"], "prod")
            self.assertTrue(bridge["phase"]["path"].startswith("/"))
            self.assertIn("/srv/exo/hermes/", bridge["dotenv_bridge"])
            self.assertTrue(bridge["dotenv_bridge"].endswith("/secret-bridge/provider.env"))
            self.assertEqual(
                bridge["dotenv_keys"],
                [
                    "TELEGRAM_BOT_TOKEN",
                    "TELEGRAM_ALLOWED_USERS",
                    "TELEGRAM_HOME_CHANNEL",
                ],
            )
            self.assertEqual(
                bridge["secret_names"],
                ["TELEGRAM_BOT_TOKEN", "TELEGRAM_OWNER_ID"],
            )
            for secret_name in bridge["secret_names"]:
                self.assertTrue(secret_name.endswith(("_TOKEN", "_OWNER_ID")))
                self.assertNotIn("fake-token-not-live", secret_name)

    def test_secret_bridge_materializer_fails_without_phase_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [
                    "sh",
                    "deploy/remote/materialize-secret-bridge.sh",
                    "tom-personal-agent",
                    "TELEGRAM_BOT_TOKEN",
                    "TELEGRAM_OWNER_ID",
                ],
                cwd=REPO_ROOT,
                env={"EXO_RUNTIME_ROOT": tmp},
                capture_output=True,
                text=True,
            )

            bridge_dir = Path(tmp) / "tom-personal-agent" / "secret-bridge"
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("missing required Phase-injected secrets", result.stderr)
            self.assertFalse((bridge_dir / "telegram-bot-token").exists())
            self.assertFalse((bridge_dir / "provider.env").exists())

    def test_secret_bridge_materializer_allows_missing_optional_model_key(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [
                    "sh",
                    "deploy/remote/materialize-secret-bridge.sh",
                    "tom-personal-agent",
                    "TELEGRAM_BOT_TOKEN",
                    "TELEGRAM_OWNER_ID",
                ],
                cwd=REPO_ROOT,
                env={
                    "EXO_RUNTIME_ROOT": tmp,
                    "TELEGRAM_BOT_TOKEN": "fake-token-not-live",
                    "TELEGRAM_OWNER_ID": "12345",
                },
                capture_output=True,
                text=True,
            )

            bridge_dir = Path(tmp) / "tom-personal-agent" / "secret-bridge"
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(
                (bridge_dir / "telegram-bot-token").read_text(encoding="utf-8"),
                "fake-token-not-live",
            )
            self.assertEqual(
                (bridge_dir / "provider.env").read_text(encoding="utf-8"),
                "\n".join(
                    [
                        "TELEGRAM_BOT_TOKEN=fake-token-not-live",
                        "TELEGRAM_ALLOWED_USERS=12345",
                        "TELEGRAM_HOME_CHANNEL=12345",
                        "",
                    ]
                ),
            )
            self.assertNotIn("OPENAI_API_KEY", (bridge_dir / "provider.env").read_text())

    def test_remote_deploy_mock_check_reports_fixture_failures(self) -> None:
        target = load_deploy_target(REMOTE_TARGET)
        configs = [
            load_profile_config(path)
            for path in discover_profile_paths(REPO_ROOT / "profiles")
        ]
        plan = build_deploy_plan(target, configs, mode="mock-check")
        mock_health = plan["mock_health"]  # type: ignore[index]

        self.assertFalse(mock_health["ok"])  # type: ignore[index]
        self.assertEqual(mock_health["problem_count"], 4)  # type: ignore[index]
        self.assertEqual(
            mock_health["failures"],  # type: ignore[index]
            [
                {
                    "category": "storage_safety",
                    "severity": "critical",
                    "summary": "Vault fixture reports a missing backup marker.",
                }
            ],
        )

    def test_remote_deploy_plan_can_select_tom_only_profile(self) -> None:
        target = load_deploy_target(REMOTE_TARGET)
        configs = [
            load_profile_config(path)
            for path in discover_profile_paths(REPO_ROOT / "profiles")
        ]
        validate_profile_set(configs)
        plan = build_deploy_plan(
            target,
            configs,
            compose_output=Path("deploy/compose/generated/hermes-tom-personal-agent.compose.yaml"),
            selected_profile_ids=("tom-personal-agent",),
        )
        command_text = json.dumps(plan["steps"])

        self.assertEqual(plan["profiles"], ["tom-personal-agent"])  # type: ignore[index]
        self.assertIn("tom-personal-agent", command_text)
        self.assertNotIn("sam-personal-agent/secret-bridge", command_text)
        self.assertNotIn("alex-personal-agent/secret-bridge", command_text)
        self.assertIn(
            "hermes-tom-personal-agent.compose.yaml",
            command_text,
        )

    def test_remote_deploy_command_outputs_dry_run_json_without_live_access(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "scripts/remote_deploy.py",
                "--config",
                "deploy/remote/mock-target.toml",
                "--mock-check",
            ],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        payload = json.loads(result.stdout)

        self.assertEqual(payload["target"]["host"], "mock-exo-vm.local")
        self.assertEqual(payload["mode"], "mock-check")
        self.assertFalse(payload["mock_health"]["ok"])


if __name__ == "__main__":
    unittest.main()
