"""Real eval CLI/fixture checks; no provider simulator or model-adherence claims."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / 'evals/agent-continuity/run.py'


class ContinuityEvalTests(unittest.TestCase):
    def invoke(self, *args):
        return subprocess.run([sys.executable, str(RUNNER), *args], capture_output=True, text=True)

    def test_catalog_has_distinct_skill_and_integration_owners(self):
        result = self.invoke('list')
        self.assertEqual(result.returncode, 0, result.stderr)
        catalog = json.loads(result.stdout)
        self.assertEqual(len(catalog), 12)
        self.assertEqual({c['owner'] for c in catalog}, {'AGENTS.md', 'planning-rhythm-os', 'planning-task-os', 'planning-capture-os', 'obsidian'})

    def test_prepare_is_reproducible_and_withholds_grading_material(self):
        with tempfile.TemporaryDirectory() as temporary:
            outputs = [Path(temporary) / name for name in ('first', 'second')]
            for output in outputs:
                result = self.invoke('prepare', '--case', 'mixed', '--date', '2027-03-14', '--output', str(output))
                self.assertEqual(result.returncode, 0, result.stderr)
                workspace = output / 'workspace'
                self.assertTrue((workspace / 'Daily/2027-03-14.md').is_file())
                self.assertFalse(list(workspace.rglob('evals.json')))
                self.assertFalse(list(workspace.rglob('grading.json')))
                self.assertIn('2027-03-14', (workspace / 'AGENTS.md').read_text())
                self.assertTrue((workspace / '.agents/skills/planning-rhythm-os/SKILL.md').is_file())
            first = {str(p.relative_to(outputs[0])):p.read_bytes() for p in outputs[0].rglob('*') if p.is_file()}
            second = {str(p.relative_to(outputs[1])):p.read_bytes() for p in outputs[1].rglob('*') if p.is_file()}
            self.assertEqual(first, second)

    def test_prepare_rejects_existing_output_without_overwrite(self):
        with tempfile.TemporaryDirectory() as temporary:
            marker = Path(temporary) / 'owner-note'; marker.write_text('keep')
            result = self.invoke('prepare', '--output', temporary)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(marker.read_text(), 'keep')

    def test_prepare_rejects_output_inside_source(self):
        result = self.invoke('prepare', '--output', str(ROOT / 'forbidden-eval-output'))
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((ROOT / 'forbidden-eval-output').exists())

    def test_invalid_fixture_exercises_actual_metadata_validator(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / 'run'
            result = self.invoke('prepare', '--case', 'obsidian-invalid', '--output', str(output))
            self.assertEqual(result.returncode, 0, result.stderr)
            workspace = output / 'workspace'
            result = subprocess.run([sys.executable, str(workspace / '.agents/skills/obsidian/scripts/validate_notes.py'), str(workspace / 'Project.md')], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('duplicate property', result.stdout + result.stderr)
            self.assertIn('blue notebook', (workspace / 'Project.md').read_text())

    def test_unavailable_fixture_really_lacks_yaml(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / 'run'
            result = self.invoke('prepare', '--case', 'obsidian-unavailable', '--output', str(output))
            self.assertEqual(result.returncode, 0, result.stderr)
            result = subprocess.run([str(output / 'workspace/.validation/bin/python'), '-c', 'import yaml'], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('ModuleNotFoundError', result.stderr)

    def test_artifact_checks_detect_missing_and_duplicated_commitment(self):
        spec = importlib.util.spec_from_file_location('continuity_eval', RUNNER)
        runner = importlib.util.module_from_spec(spec); spec.loader.exec_module(runner)
        malformed = runner.assertions([], {'broken.md':'```review-state\n{broken}\n```'}, {}, {})
        self.assertFalse(malformed[0]['passed'])
        truncated = runner.assertions([], {'broken.md':'```review-state\n{}'}, {}, {})
        self.assertFalse(truncated[0]['passed'])
        initial = {'Planning/Tasks/Call Morgan.md':'Considering a call'}
        context = {'tomorrow':'2027-03-15'}
        missing = runner.assertions(['call_captured'], initial, initial, context)
        self.assertFalse(missing[0]['passed'])
        saved = {'Planning/Tasks/Call Morgan.md':'Call Morgan 2027-03-15 afternoon'}
        self.assertTrue(runner.assertions(['call_captured','one_call_task'], saved, initial, context)[0]['passed'])
        saved['Planning/Tasks/Duplicate.md'] = 'Call Morgan'
        self.assertFalse(runner.assertions(['one_call_task'], saved, initial, context)[0]['passed'])


if __name__ == '__main__':
    unittest.main()
