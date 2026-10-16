"""The existing metadata-validator CLI is the accepted scan preflight Seam."""
from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest

VALIDATOR = Path(__file__).resolve().parents[1] / '.agents/skills/obsidian/scripts/validate_notes.py'


class AttentionDateTests(unittest.TestCase):
    def test_rejects_noncalendar_attention_values_instead_of_allowing_silent_coercion(self):
        with tempfile.TemporaryDirectory() as tmp:
            note = Path(tmp) / 'Task.md'
            for value, expected in [('2026-09-07', 0), ('"2026-09-07"', 0),
                                    ('null', 0), ('2026-02-30', 1), ('"2026-9-7"', 1),
                                    ('"2026-09-07T12:00:00Z"', 1), ('42', 1),
                                    ('false', 1), ('[2026-09-07]', 1), ('""', 1)]:
                with self.subTest(value=value):
                    note.write_text('---\ntype: "[[Task]]"\nstatus: "[[Todo]]"\nreview_on: '+value+'\n---\n')
                    r = subprocess.run([sys.executable, str(VALIDATOR), str(note)], text=True, capture_output=True)
                    self.assertEqual(r.returncode, expected, r.stdout+r.stderr)
                    report = json.loads(r.stdout)
                    self.assertEqual(bool(report['invalid']), expected == 1)

    def test_scan_preflight_does_not_hide_unknown_status_but_rejects_bad_period_dates(self):
        with tempfile.TemporaryDirectory() as tmp:
            note = Path(tmp) / 'Note.md'
            for field in ('due', 'review_on', 'week_start', 'week_end'):
                for value, expected in [('2026-09-07', 0), ('"2026-02-30"', 1)]:
                    note.write_text('---\nstatus: "[[Unknown]]"\n'+field+': '+value+'\n---\n')
                    original = note.read_bytes()
                    r = subprocess.run([sys.executable, str(VALIDATOR), '--attention-dates-only', str(note)], text=True, capture_output=True)
                    self.assertEqual(r.returncode, expected, r.stdout+r.stderr)
                    self.assertEqual(note.read_bytes(), original)
