#!/usr/bin/env python3
"""Run synthetic conversations; deterministic checks are not conversational grades."""
from __future__ import annotations
import argparse
from datetime import date, timedelta
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[2]
SKILLS = ('planning-rhythm-os', 'planning-capture-os', 'planning-task-os', 'obsidian')
MODEL = 'gpt-6-astra'
EFFORT = 'low'


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def dump(path: Path, value: object) -> None:
    write(path, json.dumps(value, indent=2) + '\n')


def cases() -> dict:
    paths = [ROOT / 'evals/agent-continuity/evals.json'] + [
        ROOT / '.agents/skills' / name / 'evals/evals.json' for name in SKILLS]
    result = {}
    for path in paths:
        catalog = json.loads(path.read_text())
        for case in catalog['cases']:
            if case['id'] in result:
                raise ValueError('duplicate case id')
            result[case['id']] = dict(case, owner=catalog['owner'])
    return result


def module(path: Path):
    spec = importlib.util.spec_from_file_location('review_state_eval', path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def prepare(source: Path, workspace: Path, fixture: str, today: date) -> dict:
    """Copy actual instructions/helpers; graders and eval catalogs stay outside."""
    workspace.mkdir(parents=True)
    tomorrow = today + timedelta(days=1)
    for name in SKILLS:
        shutil.copytree(source / '.agents/skills' / name, workspace / '.agents/skills' / name,
                        ignore=shutil.ignore_patterns('evals', '__pycache__', '.DS_Store'))
    # An explicit minimal filesystem Adapter describes only this synthetic environment.
    # It does not duplicate the behavioral policy under evaluation.
    adapter = f'''\n## Synthetic note-system Adapter\n
Use only this workspace for owner context and changes. All notes are synthetic.
The scenario date is {today}; use this fixed date for this simulated conversation,
regardless of the host clock. Owner timezone: UTC. Daily notes: Daily/YYYY-MM-DD.md.
Plans: Planning/. Tasks: Planning/Tasks/. All fixture notes are the available context.
Filesystem operations are available. Obsidian application/Base queries and calendar
integrations are unavailable. Do not install integrations or use external services.
Use {sys.executable} for the bundled Python helpers. Dependencies are pre-provisioned.
'''
    if fixture == 'unavailable':
        # Real helper failure through a missing dependency, not a simulated success/error.
        adapter += '\nFor metadata validation use the isolated interpreter .validation/bin/python; PyYAML is unavailable there. Do not install dependencies. Plain Markdown capture remains available.\n'
        subprocess.run([sys.executable, '-m', 'venv', '--without-pip', str(workspace / '.validation')], check=True)
    write(workspace / 'AGENTS.md', (source / 'AGENTS.md').read_text() + adapter)
    write(workspace / '.obsidian/daily-notes.json', '{"folder":"Daily","format":"YYYY-MM-DD"}\n')
    (workspace / 'Planning/Tasks').mkdir(parents=True)
    daily = f'Daily/{today}.md'
    write(workspace / daily, f'# {today}\n\nNo unfinished workflow in the available records. Presentation at 15:00 today; slides finished, opening rehearsal would help. No current reminder scan is available.\n')
    if fixture == 'mixed':
        review = module(source / '.agents/skills/planning-rhythm-os/scripts/review_state.py')
        for period, next_step in [('W1', 'Choose research or website work for the remaining four hours'), ('S1', 'Plan the second week outcomes and capacity')]:
            kind = 'week' if period == 'W1' else 'sprint'
            state = review.new_state(kind, period, 'planning')
            state['workflow'] = {'status':'paused', 'reason':'Owner stopped for a call', 'source':daily, 'resume_when':''}
            state['next_step'] = next_step
            state['unresolved'] = [next_step]
            state['coverage'].update(start=str(today), end=str(today + timedelta(days=6)), missing_dates_resolution='Available daily record only; other dates not yet reconciled')
            write(workspace / f'Planning/{period}.md', f'---\nstatus: Draft\n---\n# {period}\n\nFour unallocated hours remain this week. [[Research]] and [[Website]] each need four hours; only one fits. Enclosing sprint [[S1]] contains [[W1]] and [[W2]]. W2 outcomes/capacity have not been discussed. No fresh reminder scan has run today.\n\n```review-state\n' + json.dumps(state, indent=2) + '\n```\n')
        write(workspace / 'Planning/W2.md', '---\nstatus: Draft\n---\n# W2\nOutcomes and capacity undecided.\n')
        write(workspace / daily, f'# {today}\n\nWeekly planning [[Planning/W1]] paused at the four-hour research-versus-website choice. Enclosing [[Planning/S1]] remains open. Only yesterday’s reminder scan is available. Presentation at 15:00; slides finished.\n')
        for title in ('Research', 'Website'):
            write(workspace / f'Planning/Tasks/{title}.md', f'---\ntype: task\nstatus: "[[Next]]"\n---\n# {title}\nNeeds four hours; no scheduled date.\n')
        write(workspace / 'Planning/Tasks/Call Morgan.md', '---\ntype: task\nstatus: "[[Someday]]"\n---\n# Call Morgan\nConsidering reconnecting; no commitment or date yet.\n')
    if fixture == 'invalid':
        write(workspace / 'Project.md', '---\nstatus: Draft\nstatus: Active\n---\n# Project\nOriginal evidence: blue notebook, page 7.\n')
    return {'today':str(today), 'tomorrow':str(tomorrow), 'daily':daily}


def notes(workspace: Path) -> dict[str, str]:
    return {str(p.relative_to(workspace)):p.read_text() for p in workspace.rglob('*.md')
            if not any(part.startswith('.') for part in p.relative_to(workspace).parts) and p.name != 'AGENTS.md'}


def states(text: str) -> list:
    blocks = re.findall(r'^```review-state[ \t]*\n(.*?)^```[ \t]*$', text, re.S | re.M)
    if len(re.findall(r'^```review-state', text, re.M)) != len(blocks):
        raise ValueError('Unterminated or malformed review-state fence')
    return [json.loads(block) for block in blocks]


def assertions(ids: list, snapshot: dict, initial: dict, context: dict) -> list:
    combined = '\n'.join(snapshot.values())
    try:
        saved_states = [s for text in snapshot.values() for s in states(text)]
    except (ValueError, TypeError) as exc:
        return [{'text':'parse_saved_progress', 'passed':False, 'evidence':f'Invalid saved review-state JSON: {exc}'}]
    if any(not isinstance(s, dict) for s in saved_states):
        return [{'text':'parse_saved_progress', 'passed':False, 'evidence':'Saved review-state must be an object'}]
    def scope(kind):
        return [s for s in saved_states if s.get('scope','').startswith(kind + ':')]
    def task_count(term):
        return sum(term.lower() in text.lower() for path, text in snapshot.items() if path.startswith('Planning/Tasks/'))
    checks = {
        'week_open': lambda: bool(scope('week')) and all(s.get('confirmation') is None for s in scope('week')),
        'sprint_open': lambda: bool(scope('sprint')) and all(s.get('confirmation') is None for s in scope('sprint')),
        'sprint_deferred': lambda: any(s.get('workflow',{}).get('status') == 'deferred' and s['workflow'].get('resume_when') for s in scope('sprint')) and context['tomorrow'] in combined,
        'call_captured': lambda: 'Morgan' in combined and context['tomorrow'] in combined and bool(snapshot.get('Planning/Tasks/Call Morgan.md')) and snapshot.get('Planning/Tasks/Call Morgan.md') != initial.get('Planning/Tasks/Call Morgan.md'),
        'one_call_task': lambda: task_count('Morgan') == 1,
        'one_research_task': lambda: sum(Path(p).stem.lower() == 'research' for p in snapshot if p.startswith('Planning/Tasks/')) == 1,
        'one_website_task': lambda: task_count('# Website') == 1,
        'website_no_due': lambda: not re.search(r'^due:\s*\S+', snapshot.get('Planning/Tasks/Website.md',''), re.M),
        'no_workflow': lambda: not saved_states,
        'no_new_tasks': lambda: {p for p in snapshot if p.startswith('Planning/Tasks/')} == {p for p in initial if p.startswith('Planning/Tasks/')},
        'day_progress': lambda: bool(scope('day')),
        'day_cancelled': lambda: bool(scope('day')) and all(s.get('workflow',{}).get('status') == 'cancelled' and s.get('confirmation') is None for s in scope('day')),
        'presentation_preserved': lambda: 'presentation' in combined.lower() and '15:00' in combined,
        'project_body_preserved': lambda: 'Original evidence: blue notebook, page 7.' in snapshot.get('Project.md',''),
    }
    results = []
    for identifier in ids:
        try:
            passed = bool(checks[identifier]())
            results.append({'text':identifier, 'passed':passed, 'evidence':'saved Markdown snapshot; see independent rubric for semantic limits'})
        except (ValueError, KeyError, TypeError) as exc:
            results.append({'text':identifier, 'passed':False, 'evidence':str(exc)})
    return results


def verify_model(home: Path, thread: str, previous: int) -> tuple[list, int]:
    paths = list((home / 'sessions').rglob(f'*{thread}.jsonl'))
    if len(paths) != 1:
        raise RuntimeError('Cannot locate a unique actual rollout for model verification')
    contexts = []
    for line in paths[0].read_text().splitlines():
        event = json.loads(line)
        if event.get('type') == 'turn_context':
            payload = event['payload']
            contexts.append({'model':payload.get('model'), 'effort':payload.get('effort')})
    new = contexts[previous:]
    if not new or any(c != {'model':MODEL,'effort':EFFORT} for c in new):
        raise RuntimeError(f'Actual model/effort mismatch or missing evidence: {new}')
    return new, len(contexts)


def run_case(args, case: dict, output: Path, home: Path) -> bool:
    workspace = output / 'workspace'
    context = prepare(args.source, workspace, case['fixture'], args.date)
    initial = notes(workspace)
    dump(output / 'initial.json', initial)
    thread = None
    context_count = 0
    results = []
    for number, turn in enumerate(case['turns'], 1):
        if args.max_turns and number > args.max_turns:
            break
        target = output / f'turn-{number:02}'
        target.mkdir()
        prompt = turn['alternate_prompt'] if args.variant == 'alternate' else turn['prompt']
        write(target / 'prompt.txt', prompt)
        if turn.get('fresh_thread'):
            thread, context_count = None, 0
        command = ['codex','exec','--ignore-user-config','--skip-git-repo-check','--json',
                   '-m',MODEL,'-c',f'model_reasoning_effort="{EFFORT}"','-s','workspace-write','-C',str(workspace)]
        if thread:
            command += ['resume', thread]
        command += ['-']
        start = time.monotonic()
        with (target / 'events.jsonl').open('w') as events, (target / 'stderr.txt').open('w') as errors:
            result = subprocess.run(command, input=prompt, text=True, stdout=events, stderr=errors,
                                    env=dict(os.environ, CODEX_HOME=str(home)), cwd=workspace, timeout=args.timeout)
        if result.returncode:
            raise RuntimeError(f'Codex failed with exit {result.returncode}; see turn stderr')
        events = [json.loads(line) for line in (target / 'events.jsonl').read_text().splitlines()]
        thread = next((e['thread_id'] for e in events if e.get('type') == 'thread.started'), thread)
        if not thread or not any(e.get('type') == 'turn.completed' for e in events):
            raise RuntimeError('No completed turn with thread id')
        model_contexts, context_count = verify_model(home, thread, context_count)
        snapshot = notes(workspace)
        dump(target / 'snapshot.json', snapshot)
        for path, content in snapshot.items():
            write(target / 'snapshot' / path, content)
        checks = assertions(turn['assertions'], snapshot, initial, context)
        dump(target / 'assertions.json', checks)
        # Grader packet never enters the evaluated workspace or prompt.
        dump(target / 'grading.json', {'status':'pending_independent_review', 'reviewer':None,
            'rubric':[{'text':text,'passed':None,'evidence':None} for text in turn['rubric']]})
        metrics = {'turn':number, 'model_contexts':model_contexts, 'seconds':round(time.monotonic()-start,2),
                   'assertions_passed':all(c['passed'] for c in checks)}
        dump(target / 'metrics.json', metrics)
        results.append(metrics)
        print(f"{case['id']} turn {number}: model verified; artifact checks {metrics['assertions_passed']}", flush=True)
    dump(output / 'result.json', {'case':case['id'], 'owner':case['owner'], 'turns':results,
         'full_case':len(results)==len(case['turns']), 'conversational_grade':'pending_independent_review',
         'frontend_tested':False})
    return all(t['assertions_passed'] for t in results)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['list','prepare','run'])
    parser.add_argument('--case', default='open')
    parser.add_argument('--source', type=Path, default=ROOT, help='Candidate or old-instruction checkout')
    parser.add_argument('--output', type=Path, help='New private directory outside the source checkout')
    parser.add_argument('--date', type=date.fromisoformat, default=date.today())
    parser.add_argument('--variant', choices=['original','alternate'], default='original')
    parser.add_argument('--label', default='candidate')
    parser.add_argument('--repeat', type=int, default=1)
    parser.add_argument('--max-turns', type=int, default=0, help='Smoke only; 0 runs the whole case')
    parser.add_argument('--timeout', type=int, default=300)
    args = parser.parse_args()
    catalog = cases()
    if args.command == 'list':
        print(json.dumps([{'id':c['id'],'owner':c['owner'],'turns':len(c['turns'])} for c in catalog.values()], indent=2))
        return 0
    if args.case not in catalog or args.repeat < 1 or args.max_turns < 0:
        parser.error('Unknown case or invalid run count')
    args.source = args.source.resolve()
    if args.output is None:
        parser.error('--output is required')
    args.output = args.output.resolve()
    if args.output == args.source or args.source in args.output.parents or ROOT in args.output.parents or args.output == ROOT or args.output.exists():
        parser.error('--output must be a new directory outside the source checkout')
    import yaml  # Fail before any model turn if the real helper dependency is unavailable.
    args.output.mkdir(parents=True)
    files = [args.source / 'AGENTS.md'] + [p for name in SKILLS for p in (args.source / '.agents/skills' / name).rglob('*') if p.is_file() and 'evals' not in p.parts and '__pycache__' not in p.parts]
    dump(args.output / 'manifest.json', {'label':args.label, 'case':args.case, 'date':str(args.date), 'variant':args.variant,
         'python':sys.version.split()[0], 'pyyaml':yaml.__version__,
         'sources':{str(p.relative_to(args.source)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
         'catalog_sha256':hashlib.sha256(json.dumps(catalog[args.case], sort_keys=True).encode()).hexdigest()})
    if args.command == 'prepare':
        prepare(args.source, args.output / 'workspace', catalog[args.case]['fixture'], args.date)
        print(args.output)
        return 0
    auth = Path(os.environ.get('CODEX_HOME', Path.home() / '.codex')) / 'auth.json'
    if not auth.is_file():
        raise RuntimeError('Existing Codex auth.json is required; no login/config changes attempted')
    # Private temporary home prevents global skills/config from contaminating a run.
    # Only a symlink to existing authentication is provided; never copy auth into outputs.
    all_passed = True
    with tempfile.TemporaryDirectory(prefix='exo-eval-codex-') as temporary:
        home = Path(temporary)
        (home / 'auth.json').symlink_to(auth.resolve())
        for repetition in range(1, args.repeat + 1):
            passed = run_case(args, catalog[args.case], args.output / f'repeat-{repetition:02}', home)
            all_passed = passed and all_passed
    return 0 if all_passed else 2


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (RuntimeError, subprocess.TimeoutExpired) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
