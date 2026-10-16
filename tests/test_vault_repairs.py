"""Regression cases from the approved Exocortex audit: public helper contracts."""

import importlib.util
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def script(skill, filename):
    path = ROOT / ".agents" / "skills" / skill / "scripts" / filename
    spec = importlib.util.spec_from_file_location(filename.removesuffix(".py"), path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class VideoNoteTests(unittest.TestCase):
    def test_creator_and_source_values_round_trip_without_yaml_injection(self):
        video = script("save-video-content", "save_video.py")
        note = video.build_note(
            {
                "title": "An interview",
                "channel": "No Priors: AI",
                "webpage_url": "https://example.test/watch?v=1",
            },
            "2026-09-06",
            None,
        )
        properties = yaml.safe_load(note.split("---", 2)[1])
        self.assertEqual(properties["source_creator"], "No Priors: AI")
        self.assertEqual(properties["source_url"], "https://example.test/watch?v=1")
        self.assertIn("metadata/description", note)

    def test_repeated_source_reuses_note_across_dates_without_rewriting_annotations(self):
        import tempfile

        video = script("save-video-content", "save_video.py")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            meta = {
                "title": "Interview",
                "id": "abc",
                "extractor_key": "Example",
                "webpage_url": "https://example.test/watch/abc",
            }
            first = video.save_note(root, meta, "2026-09-05", None)
            first.write_text(first.read_text() + "\nMy annotation.\n")
            second = video.save_note(root, meta, "2026-09-06", None)
            self.assertEqual(first, second)
            self.assertIn("My annotation.", second.read_text())
            self.assertEqual(len(list(root.rglob("*.md"))), 1)

    def test_metadata_recovery_reuses_original_url_bookmark(self):
        import tempfile

        video = script("save-video-content", "save_video.py")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            original_url = "https://youtu.be/fixture"
            first = video.save_note(root, {"original_url": original_url,
                "metadata_status": "unavailable"}, "2026-09-05", None)
            first.write_text(first.read_text() + "\nKeep my annotation.\n")
            recovered = {"original_url": original_url,
                "webpage_url": "https://www.youtube.com/watch?v=fixture",
                "id": "fixture", "extractor_key": "Youtube", "title": "Recovered"}
            second = video.save_note(root, recovered, "2026-09-06", None)
            self.assertEqual(second, first)
            self.assertIn("Keep my annotation.", second.read_text())
            self.assertEqual(len(list(root.rglob("*.md"))), 1)

    def test_cli_keeps_url_when_metadata_tool_is_unavailable(self):
        import os
        import subprocess
        import sys
        import tempfile

        with tempfile.TemporaryDirectory() as temp:
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / ".agents/skills/save-video-content/scripts/save_video.py"),
                    "https://example.test/unavailable",
                    "--vault-root",
                    temp,
                    "--skip-download",
                    "--date",
                    "2026-09-06",
                ],
                env={**os.environ, "PATH": temp},
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            notes = list(Path(temp).rglob("*.md"))
            self.assertEqual(len(notes), 1)
            fields = yaml.safe_load(notes[0].read_text().split("---", 2)[1])
            self.assertEqual(fields["metadata_status"], "unavailable")
            self.assertEqual(fields["source_url"], "https://example.test/unavailable")
            self.assertNotIn("## Summary", notes[0].read_text())


class MetadataValidationTests(unittest.TestCase):
    def test_invalid_or_duplicate_metadata_is_reported_instead_of_empty_state(self):
        import subprocess
        import sys
        import tempfile

        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "Note.md"
            path.write_text('---\nstatus: "[[Done]]"},{\n---\nBody\n')
            command = [
                sys.executable,
                str(ROOT / ".agents/skills/obsidian/scripts/validate_notes.py"),
                str(path),
            ]
            result = subprocess.run(command, text=True, capture_output=True, check=False)
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertIn("invalid", result.stdout)
            path.write_text("---\nstatus: Todo\nstatus: Done\n---\nBody\n")
            result = subprocess.run(command, text=True, capture_output=True, check=False)
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertIn("duplicate", result.stdout)
            path.write_text(
                '---\ntags: [alpha, beta]\nnext_action: "Read: then discuss"\n---\nBody\n'
            )
            result = subprocess.run(command, text=True, capture_output=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)


class MeowOutputTests(unittest.TestCase):
    def test_routine_output_drops_secrets_urls_and_unrecognized_fields(self):
        meow = script("meow", "safe_read.py")
        # Synthetic local-policy input, not a Meow response recording.
        result = meow.summarize(
            {
                "data": {
                    "balance": 125.5,
                    "currency": "USD",
                    "status": "active",
                    "account_number": "123456789",
                    "api_key": "secret",
                    "card_pan": "4111111111111111",
                    "url": "https://example.test/signed",
                    "last_four": "1234",
                    "unknown": {"secret": "hidden"},
                }
            }
        )
        self.assertEqual(
            result,
            {
                "data": {
                    "balance": 125.5,
                    "currency": "USD",
                    "status": "active",
                    "last_four": "1234",
                }
            },
        )

    def test_sensitive_reads_and_raw_overrides_are_blocked_before_credentials(self):
        import subprocess
        import sys

        for args in [
            ["get-card-details"],
            ["get-card-pan"],
            ["get-card", "--raw", "{}"],
            ["list-cards", "--output=raw"],
        ]:
            result = subprocess.run(
                [sys.executable, str(ROOT / ".agents/skills/meow/scripts/safe_read.py"), *args],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 3)
            self.assertNotIn("credential", result.stdout)


class ReviewProgressTests(unittest.TestCase):
    def test_week_confirmation_cannot_complete_a_sprint(self):
        review = script("planning-rhythm-os", "review_state.py")
        state = review.new_state("sprint", "2026-C5-S3", "planning")
        self.assertFalse(review.check_state(state)["complete"])
        for step in state["steps"].values():
            step.update(status="complete", evidence=["test: explicit discussion"])
        state["coverage"] = {
            "start": "2026-08-24",
            "end": "2026-09-06",
            "missing_dates": [],
            "missing_dates_resolution": "none",
        }
        state["confirmation"] = {
            "scope": "week:2026-W35:planning",
            "source": "test: user message",
            "quote": "Week looks good",
            "mode": "full",
        }
        self.assertFalse(review.check_state(state)["complete"])
        state["confirmation"].update(
            scope="sprint:2026-C5-S3:planning", quote="Confirm the full sprint"
        )
        state["next_step"] = ""
        self.assertTrue(review.check_state(state)["complete"])
        state["unresolved"].append("Second-week capacity remains undecided")
        self.assertFalse(review.check_state(state)["complete"])

    def test_reduced_review_requires_accepted_omissions_and_resumes_pending_work(self):
        review = script("planning-rhythm-os", "review_state.py")
        state = review.new_state("week", "2026-W36", "review")
        state["mode"] = "reduced"
        state["coverage"] = {
            "start": "2026-08-31",
            "end": "2026-09-06",
            "missing_dates": ["2026-09-02"],
            "missing_dates_resolution": "User cannot recall this date; limit accepted in review",
        }
        for step in state["steps"].values():
            step.update(status="complete", evidence=["test: reviewed record"])
        state["steps"]["rediscovery"].update(status="omitted", reason="Short recovery review")
        state["confirmation"] = {
            "scope": state["scope"],
            "mode": "reduced",
            "source": "test: user message",
            "quote": "Confirm the reduced review",
        }
        state["next_step"] = ""
        self.assertFalse(review.check_state(state)["complete"])
        state["confirmation"]["accepted_omissions"] = ["rediscovery"]
        self.assertTrue(review.check_state(state)["complete"])
        state["steps"]["task_debt"]["status"] = "pending"
        state["next_step"] = "Discuss the unresolved county commitment"
        result = review.check_state(state)
        self.assertFalse(result["complete"])
        self.assertEqual(result["next_step"], "Discuss the unresolved county commitment")
        del state["steps"]["dated_reminders"]
        self.assertIn("dated_reminders: unfinished", review.check_state(state)["errors"])


class SkillExportTests(unittest.TestCase):
    def test_exports_exclude_caches_and_nested_exports(self):
        import sys
        import tempfile
        import zipfile

        sys.path.insert(0, str(ROOT / ".agents/skills/skill-creator/scripts"))
        packager = script("skill-creator", "package_skill.py")
        with tempfile.TemporaryDirectory() as temp:
            skill = Path(temp) / "example-skill"
            skill.mkdir()
            (skill / "SKILL.md").write_text(
                "---\nname: example-skill\ndescription: Example skill for an explicit export test.\n---\nBody\n"
            )
            cache = skill / "__pycache__"
            cache.mkdir()
            (cache / "old.pyc").write_bytes(b"cache")
            (skill / "previous.skill").write_bytes(b"old export")
            (skill / "helper.py").write_text('print("source")\n')
            archive = packager.package_skill(skill, Path(temp) / "dist")
            with zipfile.ZipFile(archive) as zf:
                self.assertEqual(
                    set(zf.namelist()), {"example-skill/SKILL.md", "example-skill/helper.py"}
                )
