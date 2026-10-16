import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('probe', Path(__file__).parents[1] / 'scripts/exo_native_batch_probe.py')
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


class NativeProbeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old = p.ROOT
        p.ROOT = Path(self.tmp.name)
        self.d = p.directory('fixture')
        self.d.mkdir()
        p.save(self.d / 'run.json', {'run_id': 'run_fixture'})

    def tearDown(self):
        p.ROOT = self.old
        self.tmp.cleanup()

    def put(self, raw):
        (self.d / 'raw.sse').write_bytes(raw)

    def poll(self, status):
        with patch.object(p, 'api', return_value=status):
            return p.next_batch('fixture')

    def test_crlf_multiline_unicode_and_partial(self):
        raw = ': ping\r\n\r\nevent: tool.started\r\ndata: {"tool":"terminal",\r\ndata: "preview":"café"}\r\n\r\ndata: {'.encode()
        frames = list(p.frames(raw))
        self.assertEqual(len(frames), 2)
        self.assertEqual(frames[1]['payload']['preview'], 'café')
        self.assertEqual(raw[frames[-1]['to_byte']:], b'data: {')

    def test_batch_preserves_payload_and_drains_all(self):
        raw = b'event: tool.started\ndata: {"tool":"terminal","preview":"sample A","extra":{"unknown":3}}\n\nevent: tool.completed\ndata: {"duration":10,"error":false}\n\n'
        self.put(raw)
        result = self.poll({'status': 'running'})
        self.assertEqual(len(result['events']), 2)
        self.assertEqual(result['events'][0]['payload']['extra'], {'unknown': 3})
        self.assertNotIn('speak', result)
        self.assertEqual(result['to_byte'], len(raw))
        self.assertEqual(self.poll({'status': 'running'})['events'], [])
        self.assertEqual((self.d / 'raw.sse').read_bytes(), raw)

    def test_reasoning_and_tentative_text_archived_not_presented(self):
        raw = b'event: reasoning.available\ndata: {"text":"private reasoning fixture"}\n\nevent: message.delta\ndata: {"delta":"partial final"}\n\n'
        self.put(raw)
        result = self.poll({'status': 'running'})
        self.assertEqual(result['events'], [])
        self.assertEqual(result['excluded_event_types'], ['message.delta', 'reasoning.available'])
        self.assertEqual((self.d / 'raw.sse').read_bytes(), raw)

    def test_capacity_blocks_without_cursor_loss(self):
        self.put(('event: tool.started\ndata: '+json.dumps({'preview': 'x'*4000})+'\n\n').encode())
        self.assertEqual(self.poll({'status': 'running'})['kind'], 'handoff_capacity_blocked')
        self.assertFalse((self.d / 'presentation.json').exists())

    def test_final_preempts_large_backlog_and_deduplicates(self):
        self.put(b'event: tool.started\ndata: {"preview":"'+b'x'*5000+b'"}\n\n')
        result = self.poll({'status': 'completed', 'output': 'EXACT'})
        self.assertEqual(result['output'], 'EXACT')
        self.assertNotIn('events', result)
        self.assertEqual(result['presentation']['mode'], 'verbatim_final')
        self.assertTrue(result['presentation']['discard_unspoken_progress'])
        self.assertFalse(result['presentation']['allow_prefix_or_suffix'])
        second = self.poll({'status': 'completed', 'output': 'EXACT'})
        self.assertEqual(second['kind'], 'already_delivered')
        self.assertEqual(second['presentation']['mode'], 'silent')

    def test_activity_carries_freshness_not_current_phase_claim(self):
        self.put(b'event: tool.started\ndata: {"preview":"sleep 10"}\n\n')
        with patch.object(p.time, 'time', return_value=123):
            result = self.poll({'status': 'running'})
        self.assertEqual(result['status_checked_at'], 123)
        self.assertTrue(result['presentation']['not_a_current_phase_guarantee'])
        self.assertEqual(result['presentation']['tense'], 'past')

    def test_summary_brief_fits_without_mutating_output(self):
        brief = ('Synthetic test\nFindings: keep qualifications.\n' + 'x' * 1600)[:1600]
        with patch.object(p, 'FINAL_PRESENTATION_MODE', 'summarize_final'):
            result = self.poll({'status': 'completed', 'output': brief})
        self.assertEqual(result['kind'], 'final')
        self.assertEqual(result['output'], brief)
        self.assertEqual(result['presentation']['mode'], 'summarize_final')
        self.assertTrue(result['presentation']['discard_unspoken_progress'])
        self.assertLessEqual(len(json.dumps(result, ensure_ascii=False, separators=(',', ':')).encode()), p.MAX_ENVELOPE_BYTES)
        self.assertEqual(p.FINAL_PRESENTATION_MODE, 'verbatim_final')

    def test_oversized_final_is_not_consumed_or_truncated(self):
        with patch.object(p, 'FINAL_PRESENTATION_MODE', 'summarize_final'):
            result = self.poll({'status': 'completed', 'output': 'x' * 4000})
        self.assertEqual(result['kind'], 'handoff_capacity_blocked')
        self.assertFalse((self.d / 'presentation.json').exists())

    def test_approval_preempts_backlog(self):
        self.put(b'event: tool.started\ndata: {}\n\n')
        result = self.poll({'status': 'waiting_for_approval', 'approval': {'request_id':'a'}})
        self.assertEqual(result['kind'], 'approval')
        self.assertEqual(result['approval']['request_id'], 'a')

    def test_capture_keeps_exact_bytes_before_parsing(self):
        raw = b': ping\r\n\r\nevent: unknown\r\ndata: { bad JSON \xff}\r\n\r\n'
        class Response:
            status = 200
            headers = {'Content-Type':'text/event-stream'}
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read1(self, size): return chunks.pop(0) if chunks else b''
        chunks = [raw[:9], raw[9:21], raw[21:]]
        with patch.object(p.urllib.request, 'urlopen', return_value=Response()):
            p.capture('fixture')
        self.assertEqual((self.d / 'raw.sse').read_bytes(), raw)
        meta = json.loads((self.d / 'capture.json').read_text())
        self.assertEqual(meta['sha256'], hashlib.sha256(raw).hexdigest())


if __name__ == '__main__': unittest.main()
