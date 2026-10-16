#!/usr/bin/env python3
"""Exo Runs adapter: native raw SSE, bounded presentation, explicit history.

Delivery claims are at-most-once CLI output, NOT audio acknowledgements.
No automatic stream reconnect/replay, automatic approvals, or Telegram secrets.
"""
from __future__ import annotations
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
import urllib.error
import urllib.request
import uuid

BASE = os.environ.get('EXOCTL_BASE_URL', 'http://127.0.0.1:8765').rstrip('/')
STATE = Path(os.environ.get('EXOCTL_STATE_DIR', str(Path.home() / '.codex/exoctl-state')))
SESSION_KEY = os.environ.get('EXOCTL_SESSION_KEY', 'exo-remote-voice')
INSTRUCTIONS = Path(os.environ.get('EXOCTL_INSTRUCTIONS', str(Path.home() / 'Documents/Codex/server-prompts/PERSISTENT-INSTRUCTIONS.md')))
TERMINAL = {'completed', 'failed', 'cancelled', 'interrupted'}
VISIBLE = {'run.started', 'tool.started', 'tool.completed', 'subagent.start', 'subagent.started',
           'subagent.complete', 'subagent.completed', 'approval.responded', 'run.steered'}
MAX_ENVELOPE_BYTES = 2800  # conservative transport guard, not a tokenizer guarantee


def wire(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'))


def emit(value):
    print(wire(value))


def load(path, default=None):
    return json.loads(path.read_text()) if path.exists() else default


def atomic_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
    with tmp.open('w') as out:
        out.write(wire(value)); out.flush(); os.fsync(out.fileno())
    os.replace(tmp, path)
    fd = os.open(path.parent, os.O_RDONLY)
    try: os.fsync(fd)
    finally: os.close(fd)


def request(method, path, payload=None, headers=None, timeout=30):
    data = None if payload is None else wire(payload).encode()
    req = urllib.request.Request(BASE + path, data=data,
        headers={'Accept': 'application/json', 'Content-Type': 'application/json', **(headers or {})}, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            body = response.read()
            return json.loads(body) if body else None
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f'Exo service HTTP {exc.code}: ' + exc.read().decode('utf-8', 'replace')[:2000]) from exc


def run_dir(run_id):
    if not re.fullmatch(r'run_[A-Za-z0-9_]+', run_id): raise ValueError('invalid run id')
    return STATE / 'runs' / run_id


def read_events(run_id):
    # Legacy journals remain readable; never regenerate speech from them.
    path = run_dir(run_id) / 'events.jsonl'
    result = []
    if path.exists():
        for line in path.read_text().splitlines():
            try: result.append(json.loads(line))
            except ValueError: pass
    return result


def frames(raw, offset=0):
    """Complete SSE frames, unchanged parsed payloads and byte references."""
    start = offset
    for m in re.finditer(br'\r\n\r\n|\n\n|\r\r', raw[offset:]):
        end = offset + m.end()
        fields, data = {}, []
        for line in raw[start:end].decode('utf-8', 'replace').splitlines():
            if not line or line.startswith(':'): continue
            key, sep, value = line.partition(':')
            if value.startswith(' '): value = value[1:]
            if key == 'data': data.append(value)
            elif sep: fields[key] = value
        try: payload = json.loads('\n'.join(data))
        except ValueError: payload = None
        name = fields.get('event') or (payload.get('event') if isinstance(payload, dict) else None)
        yield {'from_byte': start, 'to_byte': end, 'event': name, 'payload': payload}
        start = end


def follow(run_id):
    d = run_dir(run_id); d.mkdir(parents=True, exist_ok=True)
    with (d / 'capture.lock').open('a') as lock:
        try: fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError: return
        # A second follower must never append a replay into the source record.
        if (d / 'raw.sse').exists(): return
        digest = hashlib.sha256(); total = 0
        try:
            req = urllib.request.Request(BASE + f'/v1/runs/{run_id}/events', headers={'Accept': 'text/event-stream'})
            with urllib.request.urlopen(req, timeout=1800) as response, (d / 'raw.sse').open('xb') as raw:
                atomic_json(d / 'response.json', {'status': response.status, 'content_type': response.headers.get('Content-Type')})
                while True:
                    chunk = response.read1(65536)
                    if not chunk: break
                    raw.write(chunk); raw.flush(); os.fsync(raw.fileno())
                    digest.update(chunk); total += len(chunk)
            atomic_json(d / 'capture.json', {'status': 'eof', 'bytes': total, 'sha256': digest.hexdigest()})
        except Exception as exc:
            atomic_json(d / 'capture.json', {'status': 'error', 'bytes': total,
                'sha256': digest.hexdigest(), 'error': str(exc)[:500]})


def spawn_follower(run_id):
    d = run_dir(run_id); d.mkdir(parents=True, exist_ok=True)
    if (d / 'raw.sse').exists(): return None
    with (d / 'follower.log').open('ab') as log:
        proc = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), '_follow', run_id],
            stdin=subprocess.DEVNULL, stdout=log, stderr=log, start_new_session=True, close_fds=True)
    atomic_json(d / 'follower.json', {'pid': proc.pid})
    return proc.pid


def command_input(args, operation):
    text = args.input if getattr(args, 'input', None) is not None else sys.stdin.read()
    if not text.strip(): raise RuntimeError(f'{operation} requires input text')
    return text


def latest_metadata(session_key=None):
    items = []
    for p in (STATE / 'runs').glob('run_*/request.json'):
        m = load(p)
        if session_key is None or m.get('session_key') == session_key:
            items.append(m)
    return max(items, key=lambda m: float(m.get('created_at', 0)), default=None)


def current_consumer():
    # Codex injects the real thread ID into every execution environment.
    # Operator fixtures can supply EXOCTL_CONSUMER_ID when outside Codex.
    value = os.environ.get('CODEX_THREAD_ID') or os.environ.get('EXOCTL_CONSUMER_ID')
    if value and not re.fullmatch(r'[A-Za-z0-9_.:-]{1,160}', value):
        raise ValueError('Invalid consumer identity')
    return value


def superseded(run_id, epoch=None):
    return {'ok': True, 'kind': 'superseded', 'run_id': run_id,
            'consumer_epoch': epoch, 'presentation': {'mode': 'silent'},
            'action': 'end_this_backing_turn_without_further_polling',
            'do_not_stop_run': True, 'do_not_reattach_or_restart': True}


def _attach_locked(run_id, consumer):
    """Called under cursor.lock; ownership and delivery state commit together."""
    d = run_dir(run_id); delivery = load(d / 'delivery.json', {})
    owner = delivery.get('owner') or {}
    if not consumer:
        return {'ok': False, 'kind': 'consumer_identity_required', 'run_id': run_id}
    retired = delivery.get('retired_consumers', [])
    if consumer in retired: return superseded(run_id, owner.get('epoch'))
    if owner.get('consumer_id') != consumer:
        previous = owner.get('consumer_id')
        if previous: retired.append(previous)
        owner = {'consumer_id': consumer, 'epoch': int(owner.get('epoch', 0)) + 1,
                 'attached_at': time.time()}
        delivery.update(owner=owner, retired_consumers=retired)
        delivery.pop('approval', None)  # a new listener must see a pending gate
        if not delivery.get('terminal'):
            delivery.pop('output_offset', None)  # reconstruct an interrupted report from page one
        atomic_json(d / 'delivery.json', delivery)
    return {'ok': True, 'kind': 'attached', 'run_id': run_id,
            'consumer_id': consumer, 'consumer_epoch': owner['epoch'],
            'already_delivered': bool(delivery.get('terminal'))}


def attach(run_id, consumer):
    d = run_dir(run_id)
    if not d.exists():
        request('GET', f'/v1/runs/{run_id}', timeout=5)  # validate unknown run before local state
        d.mkdir(parents=True, exist_ok=True)
    with (d / 'cursor.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        return _attach_locked(run_id, consumer)


def _fence_locked(run_id, consumer, initialize=False):
    d = run_dir(run_id); delivery = load(d / 'delivery.json', {})
    owner = delivery.get('owner') or {}
    if not owner:
        if initialize and consumer: _attach_locked(run_id, consumer)
        return None  # pre-ownership legacy/operator compatibility only
    if owner.get('consumer_id') == consumer: return None
    # Even pre-upgrade, previously unregistered callers cannot fence-hop by
    # responding to superseded with a fresh attach. This is not a security boundary.
    if consumer and consumer not in delivery.get('retired_consumers', []):
        delivery.setdefault('retired_consumers', []).append(consumer)
        atomic_json(d / 'delivery.json', delivery)
    return superseded(run_id, owner.get('epoch'))


def owned_request(run_id, consumer, operation, payload=None):
    d = run_dir(run_id); d.mkdir(parents=True, exist_ok=True)
    with (d / 'cursor.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        denied = _fence_locked(run_id, consumer)
        if denied: return denied
        return request('POST', f'/v1/runs/{run_id}/{operation}', payload, timeout=5)


def start_run(prompt, session_key, idempotency_key=None, consumer=None):
    if not session_key or len(session_key) > 200: raise ValueError('invalid session key')
    sd = STATE / 'sessions' / hashlib.sha256(session_key.encode()).hexdigest()
    sd.mkdir(parents=True, exist_ok=True)
    with (sd / 'lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        state = load(sd / 'session.json', {})
        key = idempotency_key or state.get('pending_key') or 'exoctl-' + uuid.uuid4().hex
        if not re.fullmatch(r'[A-Za-z0-9_.:-]{1,200}', key): raise ValueError('invalid idempotency key')
        ip = STATE / 'intents' / (hashlib.sha256(key.encode()).hexdigest() + '.json')
        intent = load(ip)
        if intent and (intent['input'] != prompt or intent['session_key'] != session_key):
            raise RuntimeError('Idempotency conflict: recover the pending request; do not submit changed input under its key')
        if state.get('pending_key') and state['pending_key'] != key:
            raise RuntimeError('An ambiguous submission is pending; recover its original request/key before starting new work')
        if not intent:
            prior = state.get('last_run_id')
            if not prior:
                m = latest_metadata(session_key); prior = m['run_id'] if m else None
            if prior:
                prior_delivery = load(run_dir(prior) / 'delivery.json', {})
                if consumer and consumer in prior_delivery.get('retired_consumers', []):
                    return superseded(prior, (prior_delivery.get('owner') or {}).get('epoch'))
                previous = request('GET', f'/v1/runs/{prior}', timeout=5)
                if previous.get('status') not in TERMINAL:
                    raise RuntimeError(f'Existing run {prior} is not terminal; recover, steer or stop it before starting another turn')
                sid = previous.get('session_id')
                if not sid: raise RuntimeError('Previous run lacks a verified session_id; refusing to silently lose history')
            else:
                sid = state.get('session_id') or 'exo_' + uuid.uuid4().hex
            payload = {'input': prompt, 'session_id': sid}
            if INSTRUCTIONS.exists(): payload['instructions'] = INSTRUCTIONS.read_text()
            intent = {'input': prompt, 'session_key': session_key, 'key': key, 'payload': payload, 'created_at': time.time()}
            atomic_json(ip, intent)
        if not intent.get('run_id'):
            state['pending_key'] = key; atomic_json(sd / 'session.json', state)
            body = request('POST', '/v1/runs', intent['payload'],
                {'Idempotency-Key': key, 'X-Hermes-Session-Key': session_key})
            intent['run_id'] = body['run_id']; atomic_json(ip, intent)
        else:
            body = {'run_id': intent['run_id'], 'status': request('GET', f"/v1/runs/{intent['run_id']}", timeout=5)['status'], 'replayed': True}
        rid = intent['run_id']; d = run_dir(rid); d.mkdir(parents=True, exist_ok=True)
        if not (d / 'request.json').exists():
            atomic_json(d / 'request.json', {'run_id': rid, 'session_key': session_key,
                'session_id': intent['payload']['session_id'], 'idempotency_key': key,
                'created_at': intent['created_at'], 'transport': 'native-v1'})
        # Replaying an old request must not move the current conversation pointer backwards.
        if state.get('pending_key') == key or not state.get('last_run_id'):
            state.update(session_id=intent['payload']['session_id'], last_run_id=rid)
            state.pop('pending_key', None); atomic_json(sd / 'session.json', state)
        ownership = attach(rid, consumer) if consumer else None
        if ownership and ownership['kind'] == 'superseded': return ownership
        pid = spawn_follower(rid)
        return {'ok': True, 'run_id': rid, 'ownership': ownership, 'status': body.get('status'), 'replayed': body.get('replayed', False),
                'session_key': session_key, 'session_id': intent['payload']['session_id'],
                'idempotency_key': key, 'follower_pid': pid}


def fits(value):
    return len(wire(value).encode()) <= MAX_ENVELOPE_BYTES


def terminal_batch(base, status, delivery):
    state = status['status']
    output = status.get('output') or ''
    if not isinstance(output, str): output = wire(output)
    if state != 'completed' and status.get('error'): output = wire(status['error'])
    raw = output.encode(); offset = int(delivery.get('output_offset', 0))
    common = {**base, 'presentation': {'mode': 'summarize_final' if state == 'completed' else 'terminal_status',
              'supersedes': 'all_prior_activity_for_this_run', 'discard_unspoken_progress': True}}
    full = {**common, 'kind': 'final', 'output': output, 'complete': True}
    if offset == 0 and fits(full):
        delivery['terminal'] = True
        return full
    # Lossless bounded report pages, not a script-written semantic summary.
    text = raw[offset:offset+1600].decode('utf-8', 'ignore')
    while text:
        end = offset + len(text.encode())
        part = {**common, 'kind': 'final_part', 'output_part': text,
                'from_byte': offset, 'to_byte': end, 'total_bytes': len(raw),
                'sha256': hashlib.sha256(raw).hexdigest(), 'complete': end == len(raw)}
        if fits(part):
            delivery['output_offset'] = end
            if part['complete']: delivery['terminal'] = True
            return part
        text = text[:len(text)//2]
    return {**base, 'kind': 'handoff_capacity_blocked', 'complete': False}


def next_batch(run_id, consumer=None):
    d = run_dir(run_id); d.mkdir(parents=True, exist_ok=True)
    with (d / 'cursor.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        denied = _fence_locked(run_id, consumer, initialize=True)
        if denied: return denied  # no service poll, source consumption, or final claim
        status = request('GET', f'/v1/runs/{run_id}', timeout=2)
        checked = time.time()
        delivery = load(d / 'delivery.json', {})
        # Import old delivery claims, including installations with only a legacy cursor.
        cursor = int(delivery.get('cursor', (d / 'cursor').read_text() if (d / 'cursor').exists() else 0))
        if any(e.get('kind') in {'final', 'terminal'} and int(e.get('seq', 0)) <= cursor for e in read_events(run_id)):
            delivery['terminal'] = True
        raw = (d / 'raw.sse').read_bytes() if (d / 'raw.sse').exists() else b''
        base = {'ok': True, 'protocol': 'native-v1', 'run_id': run_id, 'status': status.get('status'), 'status_checked_at': checked}
        if delivery.get('owner'): base['consumer_epoch'] = delivery['owner']['epoch']
        if delivery.get('terminal'):
            batch = {**base, 'kind': 'already_delivered', 'presentation': {'mode': 'silent'}}
        elif status.get('status') in TERMINAL:
            saved = load(d / 'final.json')
            if saved is None:
                atomic_json(d / 'final.json', status); saved = status
            batch = terminal_batch(base, saved, delivery)
            delivery['raw_offset'] = len(raw)
        elif status.get('status') == 'waiting_for_approval':
            # The live approval supersedes pre-approval activity. Retain partial
            # frames, but never replay the old backlog after approval resolves.
            delivery['raw_offset'] = max((f['to_byte'] for f in frames(raw)), default=0)
            approval = status.get('approval') or {}
            identity = wire(approval)
            if delivery.get('approval') == identity:
                batch = {**base, 'kind': 'waiting_for_approval'}
            else:
                batch = {**base, 'kind': 'approval', 'approval': approval}
                if fits(batch): delivery['approval'] = identity
                else: batch = {**base, 'kind': 'approval_capacity_blocked', 'request_id': approval.get('request_id')}
        else:
            delivery.pop('approval', None)
            offset = int(delivery.get('raw_offset', 0)); end = offset; visible = []; excluded = set()
            batch = {**base, 'kind': 'waiting'}
            for item in frames(raw, offset):
                if item['event'] not in VISIBLE:
                    excluded.add(item['event'] or '(non-JSON/unnamed)'); end = item['to_byte']; continue
                candidate = {**base, 'kind': 'activity', 'events': visible + [item],
                    'presentation': {'mode': 'summarize_observed_events', 'not_a_current_phase_guarantee': True}}
                if not fits(candidate):
                    if not visible: batch = {**base, 'kind': 'handoff_capacity_blocked', 'from_byte': item['from_byte'], 'to_byte': item['to_byte']}
                    break
                visible.append(item); end = item['to_byte']; batch = candidate
            delivery['raw_offset'] = end
            # Exclusion receipts live in the audit log, not unbounded speech metadata.
            if excluded:
                with (d / 'exclusions.jsonl').open('a') as f:
                    f.write(wire({'from_byte': offset, 'to_byte': end, 'types': sorted(excluded)})+'\n')
        atomic_json(d / 'delivery.json', delivery)
        with (d / 'polls.jsonl').open('a') as f:
            f.write(wire({'at': checked, 'batch': batch})+'\n')
        return batch


def cmd_next(args):
    deadline = time.monotonic() + min(max(args.timeout, 0), 2)
    while True:
        batch = next_batch(args.run_id, current_consumer())
        if batch['kind'] != 'waiting' or time.monotonic() >= deadline:
            emit(batch); return
        time.sleep(0.2)


def cmd_status(args):
    emit(request('GET', f'/v1/runs/{args.run_id}', timeout=5))


def cmd_result(args):
    d = run_dir(args.run_id); d.mkdir(parents=True, exist_ok=True)
    with (d / 'cursor.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        denied = _fence_locked(args.run_id, current_consumer())
        if denied: emit(denied); return
        emit(result_batch(args))


def result_batch(args):
    status = load(run_dir(args.run_id) / 'final.json') or request('GET', f'/v1/runs/{args.run_id}', timeout=5)
    if status.get('status') not in TERMINAL: raise RuntimeError('Result is not terminal')
    output = status.get('output') or ''
    if status.get('status') != 'completed' and status.get('error'): output = wire(status['error'])
    raw = (output if isinstance(output, str) else wire(output)).encode()
    if args.offset < 0 or args.offset > len(raw): raise ValueError('Invalid result byte offset')
    raw[:args.offset].decode('utf-8')  # require a valid UTF-8 boundary
    if args.offset and args.offset == len(raw):
        return {'ok': True, 'kind': 'result_end', 'complete': True}
    return terminal_batch({'ok': True, 'run_id': args.run_id, 'status': status['status'], 'explicit_recovery': True},
                          status, {'output_offset': args.offset})


def cmd_latest(args):
    m = latest_metadata(args.session_key)
    pending = []
    for p in (STATE / 'sessions').glob('*/session.json'):
        s = load(p)
        if s.get('pending_key'):
            intent = load(STATE / 'intents' / (hashlib.sha256(s['pending_key'].encode()).hexdigest()+'.json'), {})
            if intent.get('session_key') == args.session_key:
                pending.append({'idempotency_key': s['pending_key'], 'input': intent.get('input'), 'run_id': intent.get('run_id')})
    ownership = None
    if m and current_consumer() and not getattr(args, 'observe', False):
        ownership = attach(m['run_id'], current_consumer())
        if ownership['kind'] == 'superseded': emit(ownership); return
    emit({'ok': True, 'run': m, 'pending_submissions': pending, 'ownership': ownership,
          'status': request('GET', f"/v1/runs/{m['run_id']}", timeout=5) if m else None})


def cmd_control(args, operation):
    payload = {'input': command_input(args, 'steer')} if operation == 'steer' else {'choice': args.choice, 'request_id': args.request_id}
    emit(owned_request(args.run_id, current_consumer(), operation, payload))


def cmd_stop(args):
    body = owned_request(args.run_id, current_consumer(), 'stop')
    if body.get('kind') == 'superseded': emit(body); return
    deadline = time.monotonic() + args.wait
    while body.get('status') not in TERMINAL and time.monotonic() < deadline:
        time.sleep(0.1); body = request('GET', f'/v1/runs/{args.run_id}', timeout=5)
    if body.get('status') in {'cancelled', 'failed', 'interrupted'}:
        d = run_dir(args.run_id); d.mkdir(parents=True, exist_ok=True)
        with (d / 'cursor.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            delivery = load(d / 'delivery.json', {}); delivery['terminal'] = True
            atomic_json(d / 'delivery.json', delivery)
            atomic_json(d / 'stop.json', body)
    emit({'ok': True, 'run_id': args.run_id, 'status': body.get('status'), 'terminal': body.get('status') in TERMINAL})


def main():
    os.umask(0o077)
    p = argparse.ArgumentParser(prog='exoctl'); sub = p.add_subparsers(dest='command', required=True)
    c = sub.add_parser('start'); c.add_argument('--session-key', default=SESSION_KEY); c.add_argument('--idempotency-key'); c.add_argument('--input')
    c.set_defaults(func=lambda a: emit(start_run(command_input(a, 'start'), a.session_key, a.idempotency_key, current_consumer())))
    c = sub.add_parser('attach'); c.add_argument('run_id'); c.set_defaults(func=lambda a: emit(attach(a.run_id, current_consumer())))
    c = sub.add_parser('next-event'); c.add_argument('run_id'); c.add_argument('--timeout', type=float, default=2); c.set_defaults(func=cmd_next)
    c = sub.add_parser('status'); c.add_argument('run_id'); c.set_defaults(func=cmd_status)
    c = sub.add_parser('result'); c.add_argument('run_id'); c.add_argument('--offset', type=int, default=0); c.set_defaults(func=cmd_result)
    c = sub.add_parser('latest'); c.add_argument('--session-key', default=SESSION_KEY); c.add_argument('--observe', action='store_true'); c.set_defaults(func=cmd_latest)
    c = sub.add_parser('events'); c.add_argument('run_id'); c.set_defaults(func=lambda a: emit({'legacy_events': read_events(a.run_id), 'raw_source': str(run_dir(a.run_id)/'raw.sse')}))
    c = sub.add_parser('steer'); c.add_argument('run_id'); c.add_argument('--input'); c.set_defaults(func=lambda a: cmd_control(a, 'steer'))
    c = sub.add_parser('approve'); c.add_argument('run_id'); c.add_argument('--choice', choices=['once','session','always','deny'], default='once'); c.add_argument('--request-id', required=True); c.set_defaults(func=lambda a: cmd_control(a, 'approval'))
    c = sub.add_parser('stop'); c.add_argument('run_id'); c.add_argument('--wait', type=float, default=5); c.set_defaults(func=cmd_stop)
    c = sub.add_parser('_follow', help=argparse.SUPPRESS); c.add_argument('run_id'); c.set_defaults(func=lambda a: follow(a.run_id))
    a = p.parse_args()
    try: a.func(a)
    except (RuntimeError, ValueError, OSError, urllib.error.URLError) as exc:
        print(wire({'ok': False, 'error': str(exc)}), file=sys.stderr); raise SystemExit(1)


if __name__ == '__main__': main()
