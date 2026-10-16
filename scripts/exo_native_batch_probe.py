#!/usr/bin/env python3
"""Isolated native SSE/Voice probe. No production exoctl state or narration.

Raw HTTP response-body bytes are authoritative. Presentation is an explicitly
filtered derivative. No SSE reconnection/replay claim and no audio-ack claim.
"""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import urllib.request

BASE = os.environ.get('EXOCTL_BASE_URL', 'http://127.0.0.1:8765').rstrip('/')
ROOT = Path(os.environ.get('EXO_NATIVE_PROBE_STATE', str(Path.home() / '.codex/native-batch-probe')))
PROMPT = '''This is an isolated, harmless Voice-stream experiment. Do not inspect files, memory, remote hosts, credentials, or other agents. Execute these three terminal commands in order, as three separate tool calls, waiting for each to finish:
1. sleep 10; printf 'PROBE: sample A contains 12 rows, 2 duplicates\\n'
2. sleep 10; printf 'PROBE: sample B contains 9 rows, 0 duplicates\\n'
3. sleep 10; printf 'PROBE: comparison completed\\n'
Then reply exactly: Native batch probe complete.
The sample statements are synthetic test fixtures, not findings about real data.'''
TERMINAL = {'completed', 'failed', 'cancelled', 'interrupted'}
# Internal reasoning and tentative assistant text are NOT voice progress.
# All bytes, including these event classes, remain in raw.sse.
VISIBLE = {'run.started', 'tool.started', 'tool.completed', 'subagent.start',
           'subagent.complete', 'approval.request', 'approval.responded', 'run.steered'}
MAX_ENVELOPE_BYTES = 2800  # conservative fixture guard, NOT a tokenizer guarantee
FINAL_PRESENTATION_MODE = 'verbatim_final'  # isolated wrappers may select summarize_final


def directory(probe):
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,100}', probe):
        raise ValueError('invalid probe id')
    return ROOT / probe


def save(path, value):
    tmp = path.with_suffix(path.suffix + '.tmp')
    with tmp.open('w') as f:
        json.dump(value, f, ensure_ascii=False)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def api(method, path, body=None, headers=None):
    req = urllib.request.Request(BASE + path,
        data=None if body is None else json.dumps(body).encode(),
        headers={'Content-Type': 'application/json', **(headers or {})}, method=method)
    with urllib.request.urlopen(req, timeout=5) as response:
        return json.load(response)


def frames(raw, offset=0):
    """Complete SSE frames + exact byte offsets; incomplete suffix stays unread."""
    start = offset
    for match in re.finditer(br'\r\n\r\n|\n\n|\r\r', raw[offset:]):
        end = offset + match.end()
        frame = raw[start:end]
        fields = {}
        data = []
        for line in frame.decode('utf-8', 'replace').splitlines():
            if not line or line.startswith(':'):
                continue
            key, _, value = line.partition(':')
            value = value[1:] if value.startswith(' ') else value
            if key == 'data':
                data.append(value)
            else:
                fields[key] = value
        text = '\n'.join(data)
        try:
            payload = json.loads(text) if data else None
        except ValueError:
            payload = {'unparsed_data': text}
        name = fields.get('event') or (payload.get('event') if isinstance(payload, dict) else None)
        yield {'from_byte': start, 'to_byte': end, 'event': name, 'payload': payload}
        start = end


def capture(probe):
    d = directory(probe)
    meta = json.loads((d / 'run.json').read_text())
    req = urllib.request.Request(BASE + '/v1/runs/' + meta['run_id'] + '/events',
                                 headers={'Accept': 'text/event-stream'})
    total = 0
    try:
        with (d / 'raw.sse').open('xb') as raw, urllib.request.urlopen(req, timeout=180) as response:
            save(d / 'response.json', {'status': response.status, 'content_type': response.headers.get('Content-Type')})
            while True:
                chunk = response.read1(65536)
                if not chunk:
                    break
                raw.write(chunk)
                raw.flush()
                os.fsync(raw.fileno())
                total += len(chunk)
        save(d / 'capture.json', {'status': 'eof', 'bytes': total,
             'sha256': hashlib.sha256((d / 'raw.sse').read_bytes()).hexdigest()})
    except Exception as exc:
        save(d / 'capture.json', {'status': 'error', 'bytes': total, 'error': str(exc)})


def start(probe):
    d = directory(probe)
    d.mkdir(parents=True, exist_ok=True, mode=0o700)
    with (d / 'lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if (d / 'run.json').exists():
            return {'probe': probe, 'existing': True, **json.loads((d / 'run.json').read_text())}
        # Stable key recovers ambiguous POST acceptance, not a new job on retry.
        body = api('POST', '/v1/runs', {'input': PROMPT},
                   {'Idempotency-Key': 'native-probe-' + probe,
                    'X-Hermes-Session-Key': 'native-probe-' + probe})
        meta = {'run_id': body['run_id'], 'created_at': time.time()}
        save(d / 'run.json', meta)
        log = (d / 'follower.log').open('ab')
        proc = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), '_capture', probe],
                 stdin=subprocess.DEVNULL, stdout=log, stderr=log, start_new_session=True)
        save(d / 'follower.json', {'pid': proc.pid})
        return {'probe': probe, 'existing': False, **meta}


def next_batch(probe):
    d = directory(probe)
    with (d / 'lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        meta = json.loads((d / 'run.json').read_text())
        status = api('GET', '/v1/runs/' + meta['run_id'])
        status_checked_at = time.time()
        cursor_file = d / 'presentation.json'
        cursor = json.loads(cursor_file.read_text()) if cursor_file.exists() else {'byte': 0}
        raw = (d / 'raw.sse').read_bytes() if (d / 'raw.sse').exists() else b''
        records = list(frames(raw, cursor['byte']))
        end = records[-1]['to_byte'] if records else cursor['byte']
        batch = {'probe': probe, 'run_id': meta['run_id'], 'status': status['status'],
                 'from_byte': cursor['byte'], 'to_byte': end, 'raw_bytes_available': len(raw)}
        if status['status'] in TERMINAL:
            batch.update(kind='already_delivered' if cursor.get('terminal') else 'final',
                         output=None if cursor.get('terminal') else status.get('output'), error=status.get('error'))
            cursor['terminal'] = True
        elif status['status'] == 'waiting_for_approval':
            batch.update(kind='approval', approval=status.get('approval'))
        else:
            visible = [r for r in records if r['event'] in VISIBLE]
            batch.update(kind='activity' if visible else 'waiting', events=visible,
                         excluded_event_types=sorted({str(r['event']) for r in records if r['event'] not in VISIBLE}))
        # Presentation control is separate from the unchanged source payloads.
        # It guides the realtime model; it is NOT an audio cancellation API.
        batch['status_checked_at'] = status_checked_at
        if batch['kind'] == 'final':
            batch['presentation'] = {
                'mode': FINAL_PRESENTATION_MODE if status['status'] == 'completed' else 'terminal_status',
                'supersedes': 'all_prior_activity_for_this_run',
                'discard_unspoken_progress': True,
                'final_text_field': 'output',
                'allow_prefix_or_suffix': FINAL_PRESENTATION_MODE != 'verbatim_final',
            }
        elif batch['kind'] == 'activity':
            batch['presentation'] = {
                'mode': 'summarize_observed_events',
                'tense': 'past',
                'not_a_current_phase_guarantee': True,
                'superseded_by_any_later_terminal': True,
            }
        elif batch['kind'] == 'already_delivered':
            batch['presentation'] = {'mode': 'silent'}
        wire = json.dumps(batch, ensure_ascii=False, separators=(',', ':'))
        if len(wire.encode()) > MAX_ENVELOPE_BYTES:
            # Do not consume or silently subdivide an oversized speech batch.
            batch = {'probe': probe, 'kind': 'handoff_capacity_blocked', 'bytes': len(wire.encode()),
                     'cursor_unchanged': True, 'status': status['status']}
        else:
            cursor['byte'] = end
            save(cursor_file, cursor)
        with (d / 'polls.jsonl').open('a') as log:
            log.write(json.dumps({'at': time.time(), 'batch': batch}, ensure_ascii=False) + '\n')
        return batch


def main():
    os.umask(0o077)
    p = argparse.ArgumentParser()
    p.add_argument('operation', choices=['start', 'next', 'status', 'stop', '_capture'])
    p.add_argument('probe')
    a = p.parse_args()
    if a.operation == '_capture':
        capture(a.probe)
        return
    if a.operation == 'start':
        result = start(a.probe)
    elif a.operation == 'next':
        result = next_batch(a.probe)
    else:
        meta = json.loads((directory(a.probe) / 'run.json').read_text())
        result = api('POST' if a.operation == 'stop' else 'GET',
                     '/v1/runs/' + meta['run_id'] + ('/stop' if a.operation == 'stop' else ''))
    print(json.dumps(result, ensure_ascii=False, separators=(',', ':')))


if __name__ == '__main__':
    main()
