"""Owner-approved status canon, exercised through the existing validator CLI."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / '.agents/skills/obsidian/scripts/validate_notes.py'


class NoteStatusTests(unittest.TestCase):
    def run_validator(self, *args):
        result = subprocess.run([sys.executable, str(VALIDATOR), *map(str, args)],
                                text=True, capture_output=True)
        return result, json.loads(result.stdout)

    def test_canonical_link_required_and_family_enforced(self):
        with tempfile.TemporaryDirectory() as tmp:
            note = Path(tmp) / 'Note.md'
            for kind, status, expected in [
                ('Task', '"[[Todo]]"', 0), ('Task', 'Todo', 1),
                ('Task', '"[[Active]]"', 1), ('Week', '"[[Ended]]"', 0),
                ('Person', '"[[Active]]"', 1), ('Book', '"[[Doing]]"', 0),
                ('Unknown Type', '"[[Todo]]"', 1),
            ]:
                with self.subTest(kind=kind, status=status):
                    note.write_text(f'---\ntype: "[[{kind}]]"\nstatus: {status}\n---\nBody\n')
                    result, report = self.run_validator(note)
                    self.assertEqual(result.returncode, expected, report)

    def test_repair_preserves_bytes_and_backs_up_original_without_guessing_later(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp) / 'vault'
            vault.mkdir()
            note = vault / 'Note.md'
            original = b'---\r\ntype: "[[Task]]"\r\nstatus: Doing # keep comment\r\ndue: 2026-09-09\r\n---\r\nBody **unchanged**\r\n'
            note.write_bytes(original)
            backup = Path(tmp) / 'backup'
            result, report = self.run_validator(vault, '--fix-status', '--backup-dir', backup)
            self.assertEqual(result.returncode, 0, report)
            self.assertEqual(note.read_bytes(), original.replace(b'Doing #', b'"[[Doing]]" #'))
            self.assertEqual(next(backup.rglob('*.md')).read_bytes(), original)
            note.write_text('---\ntype: "[[Task]]"\nstatus: "[[Later]]"\n---\nCommitted?\n')
            before = note.read_bytes()
            result, report = self.run_validator(note, '--fix-status', '--backup-dir', backup)
            self.assertEqual(result.returncode, 1, report)
            self.assertEqual(note.read_bytes(), before)

    def test_read_comparison_tolerates_plain_and_approved_aliases(self):
        sys.path.insert(0, str(VALIDATOR.parent))
        from status_policy import status_equal
        self.assertTrue(status_equal('Done', '[[Done]]'))
        self.assertTrue(status_equal('[[Later]]', 'Someday'))
        self.assertFalse(status_equal('[[Reviewed]]', 'Done'))
        self.assertFalse(status_equal('Complete', 'Done'))

    def test_invalid_yaml_unknown_status_and_missing_resolution_are_not_repaired(self):
        with tempfile.TemporaryDirectory() as tmp:
            note = Path(tmp) / 'Note.md'
            for metadata in ('status: Todo\nstatus: Done', 'status: "[[Banana]]"',
                             'status: "[[Closed]]"', 'status: [Todo, Doing]',
                             'status: "[[Closed]]"\nresolution: "   "'):
                note.write_text(f'---\ntype: "[[Task]]"\n{metadata}\n---\nBody\n')
                before = note.read_bytes()
                result, report = self.run_validator(note, '--fix-status', '--backup-dir', Path(tmp) / 'backup')
                self.assertEqual(result.returncode, 1, report)
                self.assertEqual(note.read_bytes(), before)

    @unittest.skipUnless(os.environ.get('NITRIDE_CLI'), 'set NITRIDE_CLI for actual Base query proof')
    def test_base_repair_preserves_unrelated_yaml_and_view_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp) / 'vault'
            vault.mkdir()
            (vault / 'Open.md').write_text('---\nstatus: "[[Todo]]"\n---\n')
            base = vault / 'Case.base'
            original = b'# preserve this comment\r\nfilters:\r\n  and:\r\n    - status != "[[Done]]" # terminal\r\nviews:\r\n  - type: table\r\n    name: No\r\n'
            base.write_bytes(original)
            query = ['node', os.environ['NITRIDE_CLI'], '--vault-path', str(vault),
                     'base:query', 'path=Case.base', 'view=No', 'format=paths']
            before = subprocess.run(query, text=True, capture_output=True)
            self.assertEqual(before.returncode, 0, before.stderr)
            repair = subprocess.run([sys.executable, str(VALIDATOR.parent / 'repair_status_filters.py'),
                                     str(base), '--apply', '--backup-dir', str(Path(tmp) / 'backup')],
                                    text=True, capture_output=True)
            self.assertEqual(repair.returncode, 0, repair.stderr)
            after = subprocess.run(query, text=True, capture_output=True)
            self.assertEqual(after.returncode, 0, after.stderr)
            self.assertEqual(after.stdout, before.stdout)
            self.assertEqual(base.read_bytes().split(b'views:', 1)[1], original.split(b'views:', 1)[1])
            self.assertTrue(base.read_bytes().startswith(b'# preserve this comment\r\n'))
            self.assertIn(b'# terminal\r\n', base.read_bytes())

    def test_base_repair_preserves_block_separator_and_rejects_shared_aliases(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp) / 'Case.base'
            command = [sys.executable, str(VALIDATOR.parent / 'repair_status_filters.py'),
                       str(base), '--apply', '--backup-dir', str(Path(tmp) / 'backup')]
            base.write_text('filters: >\n  status != "[[Done]]"\nviews:\n  - type: table\n    name: Yes\n')
            result = subprocess.run(command, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('\nviews:\n  - type: table\n    name: Yes\n', base.read_text())
            import yaml
            self.assertIn('status != "Done"', yaml.safe_load(base.read_text())['filters'])
            original = 'description: &shared status != "[[Done]]"\nfilters: *shared\nviews: []\n'
            base.write_text(original)
            result = subprocess.run(command, text=True, capture_output=True)
            self.assertEqual(result.returncode, 1, result.stdout)
            self.assertIn('anchored/aliased', result.stdout)
            self.assertEqual(base.read_text(), original)

    @unittest.skipUnless(os.environ.get('NITRIDE_CLI'), 'set NITRIDE_CLI for actual Base query proof')
    def test_repaired_saved_filters_match_plain_linked_and_missing_statuses(self):
        with tempfile.TemporaryDirectory() as tmp:
            vault = Path(tmp) / 'vault'
            vault.mkdir()
            cases = {
                'done-link': '"[[Done]]"', 'done-plain': 'Done',
                'closed-link': '"[[Closed]]"', 'closed-plain': 'Closed',
                'reviewed': '"[[Reviewed]]"', 'ended': '"[[Ended]]"',
                'later': 'Later', 'someday': '"[[Someday]]"',
                'incubating': '"[[Incubating]]"', 'waiting': 'Waiting',
                'unknown': 'Something Unexpected', 'missing': None,
                'todo-link': '"[[Todo]]"', 'todo-plain': 'Todo',
                'doing-link': '"[[Doing]]"', 'doing-plain': 'Doing',
            }
            for name, status in cases.items():
                field = f'status: {status}\n' if status else ''
                (vault / (name + '.md')).write_text('---\nreview_on: 2026-09-07\n' + field + '---\n')
            base = vault / 'Attention.base'
            base.write_text('''filters:
  and:
    - file.ext == "md"
    - review_on <= today()
    - status != "[[Done]]"
    - status != "[[Closed]]"
    - status != "[[Reviewed]]"
views:
  - type: table
    name: Attention
  - type: table
    name: Capacity
    filters:
      or:
        - status == "[[Todo]]"
        - status == "[[Doing]]"
  - type: table
    name: Committed
    filters:
      and:
        - status != "[[Someday]]"
''')
            command = [sys.executable, str(VALIDATOR.parent / 'repair_status_filters.py'),
                       str(base), '--attention', '--apply', '--backup-dir', str(Path(tmp) / 'backup')]
            result = subprocess.run(command, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            once = base.read_bytes()
            result = subprocess.run(command, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(base.read_bytes(), once)
            expected = set(cases) - {'done-link', 'done-plain', 'closed-link', 'closed-plain'}
            for view, names in [('Attention', expected),
                                ('Capacity', {'todo-link', 'todo-plain', 'doing-link', 'doing-plain'}),
                                ('Committed', expected - {'later', 'someday', 'incubating'})]:
                result = subprocess.run(['node', os.environ['NITRIDE_CLI'], '--vault-path', str(vault),
                                         '--date', '2026-09-07', '--timezone', 'America/Denver',
                                         'base:query', 'path=Attention.base', f'view={view}', 'format=paths'],
                                        text=True, capture_output=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(set(result.stdout.splitlines()), {n + '.md' for n in names})


if __name__ == '__main__':
    unittest.main()
