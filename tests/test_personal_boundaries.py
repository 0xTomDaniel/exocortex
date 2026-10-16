"""Accepted single-preferences-skill policy, exercised through distribution interfaces."""

import tempfile
import unittest
from pathlib import Path

from exo_distribution.skills import install_planned_skills, load_skills_manifest, plan_skill_install

ROOT = Path(__file__).resolve().parents[1]


class PersonalBoundaryTests(unittest.TestCase):
    def test_team_planning_is_a_module_of_the_only_tom_preferences_skill(self):
        manifest = load_skills_manifest(ROOT / "skills/sources.toml", ROOT)
        self.assertNotIn("team-weekly-planning", {s.name for s in manifest.sources})
        with tempfile.TemporaryDirectory() as temp:
            plans = plan_skill_install(manifest, "tom-personal-agent", ROOT, Path(temp))
            install_planned_skills(plans, manifest)
            tom = next(
                p.actual_destination for p in plans if p.source.name == "tom-operating-style"
            )
            self.assertTrue((tom / "modules/team-weekly-planning/guide.md").is_file())
            self.assertEqual(list(tom.rglob("SKILL.md")), [tom / "SKILL.md"])
            self.assertTrue(
                (tom / "modules/team-weekly-planning/references/icp-qualification.md").is_file()
            )
            self.assertIn("modules/team-weekly-planning/guide.md", (tom / "SKILL.md").read_text())
            for owner in ("alex-personal-agent", "sam-personal-agent"):
                self.assertNotIn(
                    "tom-operating-style",
                    {
                        p.source.name
                        for p in plan_skill_install(manifest, owner, ROOT, Path(temp) / owner)
                    },
                )

    def test_meow_missing_owner_context_never_attempts_credential_access(self):
        import os
        import subprocess
        import sys

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            spy = root / "security"
            spy.write_text('#!/bin/sh\n: > "' + str(root / "accessed") + '"\nexit 1\n')
            spy.chmod(0o755)
            env = {
                **os.environ,
                "PATH": temp,
                "MEOW_EXO_EMAIL": "",
                "MEOW_EXO_KEYCHAIN_SERVICE": "",
            }
            for script, args in [
                ("safe_read.py", ["list-bank-accounts"]),
                ("authenticate_macos.py", []),
            ]:
                result = subprocess.run(
                    [sys.executable, str(ROOT / ".agents/skills/meow/scripts" / script), *args],
                    env=env,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertIn("owner_context_required", result.stderr)
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse((root / "accessed").exists())

    def test_shared_guidance_has_no_known_owner_identity_leaks(self):
        """Owner-private names (people, companies, projects) must not appear in shared guidance.

        The names themselves are private, so they are never committed here: list them one per
        line in the file named by EXO_PRIVATE_TERMS (default ~/.config/exo/private-terms.txt).
        Without that file the check is skipped (for example in public CI)."""
        import os
        import re

        terms_file = Path(os.environ.get("EXO_PRIVATE_TERMS", Path.home() / ".config/exo/private-terms.txt"))
        if not terms_file.is_file():
            self.skipTest(f"no private terms list at {terms_file}")
        terms = [t.strip() for t in terms_file.read_text().splitlines() if t.strip() and not t.startswith("#")]
        self.assertTrue(terms, "private terms list is empty")
        personal = re.compile(r"\b(?:" + "|".join(re.escape(t) for t in terms) + r")\b", re.I)

        paths = [ROOT / "AGENTS.md", ROOT / "SOUL.md"]
        paths += list((ROOT / "deploy/voice").rglob("*.md"))
        paths += list((ROOT / "skills").rglob("*.md"))
        paths += [
            p
            for p in (ROOT / ".agents/skills").rglob("*")
            if p.suffix in {".md", ".py", ".sh", ".cjs", ".json"}
            and "tom-operating-style" not in p.parts
        ]
        failures = []
        for path in paths:
            content = path.read_text()
            # Exact routing identifiers are permitted, not arbitrary lines.
            for identifier in ("tom-operating-style", "tom-personal-agent"):
                content = content.replace(identifier, "")
            if personal.search(content):
                failures.append(str(path.relative_to(ROOT)))
        # Report paths only, never the matched private term.
        self.assertEqual(failures, [], "Owner-private name in shared guidance")

    def test_old_standalone_team_skill_requires_preserving_migration(self):
        from exo_distribution.config import ValidationError

        manifest = load_skills_manifest(ROOT / "skills/sources.toml", ROOT)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            old = root / "team-weekly-planning"
            old.mkdir()
            note = old / "SKILL.md"
            note.write_text("Runtime customization to preserve.\n")
            with self.assertRaisesRegex(ValidationError, "retired standalone"):
                plan_skill_install(manifest, "tom-personal-agent", ROOT, root)
            self.assertEqual(note.read_text(), "Runtime customization to preserve.\n")
