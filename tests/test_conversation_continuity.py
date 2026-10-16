"""Phase 1 acceptance at the existing review_state.py CLI.

The approved continuity plan requires interruption, deferral/cancellation and
exact-scope completion. These tests exercise that public command on saved notes;
they do not establish that a conversational model follows the instructions.
"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMMAND = ROOT / ".agents/skills/planning-rhythm-os/scripts/review_state.py"


def complete_record():
    return {
        "version": 1,
        "scope": "week:2026-W37:planning",
        "mode": "full",
        "coverage": {
            "start": "2026-09-07",
            "end": "2026-09-13",
            "missing_dates": [],
            "missing_dates_resolution": "none; all dates accounted for",
        },
        "steps": {
            name: {"status": "complete", "evidence": ["fixture: planning discussion"]}
            for name in (
                "review_stack", "outcome_and_evidence", "sequencing",
                "capacity_and_displacements", "life_anchors", "dated_reminders",
                "decision_gate",
            )
        },
        "unresolved": [],
        "confirmation": {
            "scope": "week:2026-W37:planning",
            "mode": "full",
            "source": "fixture: owner message",
            "quote": "Lock in this week",
        },
        "next_step": "",
    }


def check_note(state):
    with tempfile.TemporaryDirectory() as temporary:
        note = Path(temporary) / "week.md"
        note.write_text("# Week\n\n```review-state\n" + json.dumps(state) + "\n```\n")
        result = subprocess.run(
            [sys.executable, str(COMMAND), "check", str(note)],
            capture_output=True, text=True, check=False,
        )
        return result.returncode, json.loads(result.stdout)


class ConversationContinuityTests(unittest.TestCase):
    def test_coverage_and_reduced_omission_need_nonblank_explanations(self):
        for value in ("  ", True, ["explained"]):
            with self.subTest(field="coverage", value=value):
                state = complete_record()
                state["coverage"]["missing_dates_resolution"] = value
                self.assertFalse(check_note(state)[1]["complete"])
            with self.subTest(field="omission", value=value):
                state = complete_record()
                state["mode"] = "reduced"
                state["confirmation"].update(mode="reduced", accepted_omissions=["dated_reminders"])
                state["steps"]["dated_reminders"].update(status="omitted", reason=value)
                self.assertFalse(check_note(state)[1]["complete"])

    def test_unfinished_scope_requires_a_usable_text_next_step(self):
        for value in ("  ", True, ["resolve capacity"]):
            with self.subTest(value=value):
                state = complete_record()
                state["steps"]["sequencing"]["status"] = "pending"
                state["next_step"] = value
                result = check_note(state)[1]
                self.assertIn("unfinished scope needs an exact next step", result["errors"])

    def test_confirmation_requires_nonblank_text_source_and_quote(self):
        for field in ("source", "quote"):
            for value in ("   ", True, 1, {"text": "Lock it in"}, ["Lock it in"]):
                with self.subTest(field=field, value=value):
                    state = complete_record()
                    state["confirmation"][field] = value
                    code, result = check_note(state)
                    self.assertEqual(code, 1)
                    self.assertFalse(result["complete"])

    def test_legacy_and_active_completed_records_remain_compatible(self):
        state = complete_record()
        self.assertEqual(check_note(state)[0], 0)
        state["workflow"] = {"status": "active"}
        self.assertEqual(check_note(state)[0], 0)

    def test_invalid_disposition_cannot_bypass_completion(self):
        for workflow in (None, "cancelled", {}, {"status": "complete"}):
            with self.subTest(workflow=workflow):
                state = complete_record()
                state["workflow"] = workflow
                code, result = check_note(state)
                self.assertEqual(code, 1)
                self.assertFalse(result["complete"])

    def test_changed_priority_requires_new_confirmation_and_resolved_capacity(self):
        state = complete_record()
        state["confirmation"] = None
        state["steps"]["capacity_and_displacements"] = {
            "status": "pending", "evidence": [],
        }
        state["unresolved"] = ["Which commitment does the new priority displace?"]
        state["next_step"] = "Choose the displaced commitment"
        self.assertEqual(check_note(state)[0], 1)
        state["steps"]["capacity_and_displacements"] = {
            "status": "complete", "evidence": ["fixture: owner chose displacement"],
        }
        state["unresolved"] = []
        state["next_step"] = "Confirm the revised week"
        self.assertEqual(check_note(state)[0], 1)
        state["confirmation"] = complete_record()["confirmation"] | {
            "quote": "Lock in the revised week", "source": "fixture: subsequent message",
        }
        state["next_step"] = ""
        self.assertEqual(check_note(state)[0], 0)

    def test_missing_current_reminder_coverage_blocks_full_completion(self):
        state = complete_record()
        state["steps"]["dated_reminders"] = {
            "status": "pending", "evidence": ["fixture: only yesterday's scan is available"],
        }
        state["next_step"] = "Obtain current reminder coverage or agree explicit reduced scope"
        self.assertEqual(check_note(state)[0], 1)

    def test_new_workflow_starts_active_and_retains_the_next_step_on_resume(self):
        result = subprocess.run(
            [sys.executable, str(COMMAND), "init", "--kind", "week",
             "--period", "2026-W37", "--phase", "planning"],
            capture_output=True, text=True, check=True,
        )
        state = json.loads(result.stdout)
        self.assertEqual(state["workflow"]["status"], "active")
        state["next_step"] = "Resolve second-week capacity after the relationship discussion"
        for status in ("paused", "active"):
            state["workflow"]["status"] = status
            code, checked = check_note(state)
            self.assertEqual(code, 1)
            self.assertEqual(checked["next_step"], state["next_step"])
        # Resume never copies agreement from another scope or invents completion.
        self.assertIsNone(state["confirmation"])

    def test_paused_deferred_and_cancelled_are_never_completed(self):
        for status in ("paused", "deferred", "cancelled"):
            with self.subTest(status=status):
                state = complete_record()
                state["workflow"] = {
                    "status": status,
                    "reason": "Owner redirected the conversation",
                    "source": "fixture: owner message",
                    "resume_when": "Next planning session" if status == "deferred" else "",
                }
                code, result = check_note(state)
                self.assertEqual(code, 1)
                self.assertFalse(result["complete"])
                self.assertEqual(result["workflow_status"], status)
