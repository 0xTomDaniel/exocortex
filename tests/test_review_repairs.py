"""Regressions for the five accepted PR #1 findings.

Seams: build_deploy_plan shell output, skill install/plan, and save_note,
as identified by the accepted review and repository regression contract.
SSH replay uses the ssh(1) documented space-joined remote command; no host
or Docker daemon is contacted.
"""

import shlex
import subprocess
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from exo_distribution.config import discover_profile_paths, load_profile_config
from exo_distribution.deploy import build_deploy_plan, load_deploy_target

ROOT = Path(__file__).resolve().parents[1]


def remote_command(command):
    words = shlex.split(command)
    destination = next(i for i, word in enumerate(words) if "@" in word)
    remote = words[destination + 1 :]
    if remote[0] == "--":
        remote = remote[1:]
    return " ".join(remote)


def plan_for(root):
    target = replace(
        load_deploy_target(ROOT / "deploy/remote/mock-target.toml"),
        deploy_root=str(root / "deploy"),
        runtime_root=str(root / "runtime"),
    )
    profiles = [load_profile_config(p) for p in discover_profile_paths(ROOT / "profiles")]
    return build_deploy_plan(target, profiles, selected_profile_ids=("tom-personal-agent",))


def commands(plan, name):
    return next(step["commands"] for step in plan["steps"] if step["name"] == name)


class DeployRepairTests(unittest.TestCase):
    def test_remote_prerequisite_creates_both_directories_through_shell(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            plan = plan_for(root)
            command = next(c for c in commands(plan, "prerequisite-checks") if "mkdir" in c)
            result = subprocess.run(
                ["sh", "-c", remote_command(command)], capture_output=True, check=False
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((root / "deploy").is_dir())
            self.assertTrue((root / "runtime").is_dir())

    def test_selected_profile_start_never_removes_other_project_services(self):
        plan = plan_for(Path("/tmp/exo-review"))
        for command in commands(plan, "compose-start-or-restart"):
            self.assertNotIn("--remove-orphans", shlex.split(remote_command(command)))

    def test_unsupported_remote_paths_fail_before_commands_are_emitted(self):
        from exo_distribution.config import ValidationError

        with self.assertRaises(ValidationError):
            plan_for(Path("/tmp/exo review"))
        with self.assertRaises(ValidationError):
            plan_for(Path("/tmp/exo;false"))

    def test_profile_writers_stop_before_skill_sync(self):
        plan = plan_for(Path("/tmp/exo-review"))
        steps = [step["name"] for step in plan["steps"]]
        stop = "stop-profile-writers-before-skill-sync"
        self.assertIn(stop, steps)
        self.assertLess(steps.index(stop), steps.index("install-or-sync-profile-skills"))
        self.assertGreater(steps.index(stop), steps.index("materialize-phase-secret-bridges"))
        self.assertIn(" stop", remote_command(commands(plan, stop)[0]))

    def test_runtime_boundaries_are_private_on_creation_and_redeploy(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            plan = plan_for(root)
            command = commands(plan, "create-instance-runtime-boundaries")[0]
            # Execute filesystem operations as the fixture owner. sudo's only
            # substituted responsibility here is privilege elevation.
            shell = 'umask 022; sudo() { "$@"; }; ' + remote_command(command)
            profile = root / "runtime/tom-personal-agent"
            for _ in range(2):
                result = subprocess.run(["sh", "-c", shell], capture_output=True, check=False)
                self.assertEqual(result.returncode, 0, result.stderr)
                for name in (
                    "hermes-home",
                    "workspace",
                    "vault",
                    "skills",
                    "log-boundary",
                    "backup-boundary",
                    "secret-bridge",
                ):
                    path = profile / name
                    self.assertEqual(path.stat().st_mode & 0o777, 0o700, name)
                    path.chmod(0o755)


class SkillDriftTests(unittest.TestCase):
    def test_runtime_edits_block_same_ref_and_changed_ref_sync(self):
        from exo_distribution.config import ValidationError
        from exo_distribution.skills import (
            install_planned_skills,
            load_skills_manifest,
            plan_skill_install,
        )

        manifest = load_skills_manifest(ROOT / "skills/sources.toml", ROOT)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            plans = plan_skill_install(manifest, "tom-local-dev", ROOT, root)
            install_planned_skills(plans, manifest)
            note = plans[0].actual_destination / "SKILL.md"
            original = note.read_text() + "\nRuntime instruction to preserve.\n"
            note.write_text(original)
            for changed in (False, True):
                current = replace(
                    manifest,
                    sources=tuple(
                        replace(source, ref=source.ref + "-next") if changed else source
                        for source in manifest.sources
                    ),
                )
                planned = plan_skill_install(current, "tom-local-dev", ROOT, root)
                self.assertEqual(planned[0].action, "collision")
                with self.assertRaises(ValidationError):
                    install_planned_skills(planned, current)
                self.assertEqual(note.read_text(), original)

    def test_edit_after_planning_cannot_be_overwritten(self):
        from exo_distribution.config import ValidationError
        from exo_distribution.skills import (
            install_planned_skills,
            load_skills_manifest,
            plan_skill_install,
        )

        manifest = load_skills_manifest(ROOT / "skills/sources.toml", ROOT)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            plans = plan_skill_install(manifest, "tom-local-dev", ROOT, root)
            install_planned_skills(plans, manifest)
            updated = replace(
                manifest,
                sources=tuple(
                    replace(source, ref=source.ref + "-next") for source in manifest.sources
                ),
            )
            planned = plan_skill_install(updated, "tom-local-dev", ROOT, root)
            note = plans[0].actual_destination / "SKILL.md"
            note.write_text(note.read_text() + "\nLate runtime edit.\n")
            with self.assertRaises(ValidationError):
                install_planned_skills(planned, updated)
            self.assertIn("Late runtime edit.", note.read_text())
