import argparse
import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('exoctl', Path(__file__).parents[1]/'scripts/exoctl.py')
p = importlib.util.module_from_spec(spec); spec.loader.exec_module(p)


class ExoctlTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.state = patch.object(p, 'STATE', Path(self.tmp.name)); self.state.start()
        self.instructions = patch.object(p, 'INSTRUCTIONS', Path(self.tmp.name)/'instructions.md'); self.instructions.start()
        self.d = p.run_dir('run_fixture'); self.d.mkdir(parents=True)

    def tearDown(self):
        self.instructions.stop(); self.state.stop(); self.tmp.cleanup()

    def poll(self, status):
        with patch.object(p, 'request', return_value=status): return p.next_batch('run_fixture')

    def raw(self, data): (self.d/'raw.sse').write_bytes(data)

    def test_native_payloads_preserved_without_speech(self):
        raw=b'event: tool.started\ndata: {"preview":"check","extra":{"x":3}}\n\nevent: tool.completed\ndata: {"duration":8,"error":false}\n\n'
        self.raw(raw); r=self.poll({'status':'running'})
        self.assertEqual(r['kind'],'activity'); self.assertEqual(len(r['events']),2)
        self.assertEqual(r['events'][0]['payload'], {'preview':'check','extra':{'x':3}})
        self.assertNotIn('speak', p.wire(r)); self.assertEqual(self.poll({'status':'running'})['kind'],'waiting')
        self.assertEqual((self.d/'raw.sse').read_bytes(),raw)

    def test_frames_multiline_unicode_crlf_partial(self):
        raw=': ping\r\n\r\nevent: tool.started\r\ndata: {"preview":\r\ndata: "café"}\r\n\r\ndata: {'.encode()
        fs=list(p.frames(raw)); self.assertEqual(fs[1]['payload'],{'preview':'café'})
        self.assertEqual(raw[fs[-1]['to_byte']:],b'data: {')

    def test_capture_verbatim_and_idempotent_follower(self):
        raw=b': ping\r\n\r\nevent: unknown\ndata: invalid \xff\n\ndata: [DONE]\n\n'
        chunks=[raw[:7],raw[7:24],raw[24:]]
        class Response:
            status=200; headers={'Content-Type':'text/event-stream'}
            def __enter__(self): return self
            def __exit__(self,*args): pass
            def read1(self,n): return chunks.pop(0) if chunks else b''
        with patch.object(p.urllib.request,'urlopen',return_value=Response()) as call:
            p.follow('run_fixture'); p.follow('run_fixture'); self.assertEqual(call.call_count,1)
        self.assertEqual((self.d/'raw.sse').read_bytes(),raw)
        self.assertEqual(p.load(self.d/'capture.json')['sha256'],hashlib.sha256(raw).hexdigest())

    def test_excludes_reasoning_and_tentative_text(self):
        self.raw(b'event: reasoning.available\ndata: {"text":"PRIVATE"}\n\nevent: message.delta\ndata: {"delta":"tentative"}\n\n')
        r=self.poll({'status':'running'}); self.assertEqual(r['kind'],'waiting')
        self.assertNotIn('PRIVATE',p.wire(r)); self.assertTrue((self.d/'exclusions.jsonl').exists())

    def test_no_timed_heartbeat(self):
        for t in [0,25,50,500]:
            with patch.object(p.time,'time',return_value=t): self.assertEqual(self.poll({'status':'running'})['kind'],'waiting')

    def test_activity_pages_preserve_order(self):
        raw=b''.join(('event: tool.started\ndata: '+json.dumps({'preview':str(i)+'x'*550})+'\n\n').encode() for i in range(8))
        self.raw(raw); events=[]
        for _ in range(10):
            r=self.poll({'status':'running'}); self.assertTrue(p.fits(r)); events.extend(r.get('events',[]))
            if r['kind']=='waiting':break
        self.assertEqual([e['payload']['preview'][0] for e in events],list('01234567'))

    def test_oversized_activity_holds_cursor_then_terminal_preempts(self):
        self.raw(b'event: tool.started\ndata: {"preview":"'+b'x'*5000+b'"}\n\n')
        self.assertEqual(self.poll({'status':'running'})['kind'],'handoff_capacity_blocked')
        self.assertEqual(p.load(self.d/'delivery.json')['raw_offset'],0)
        r=self.poll({'status':'completed','output':'done'}); self.assertEqual(r['output'],'done'); self.assertNotIn('events',r)

    def test_final_once_and_late_stream_suppressed(self):
        r=self.poll({'status':'completed','output':'Exact.'});self.assertEqual(r['output'],'Exact.')
        self.raw(b'event: tool.started\ndata: {}\n\n')
        self.assertEqual(self.poll({'status':'completed','output':'Exact.'})['kind'],'already_delivered')

    def test_large_final_pages_lossless_with_unicode_and_escaping(self):
        output=('café 🌋 "\\\n'*650)
        parts=[]
        for _ in range(100):
            r=self.poll({'status':'completed','output':output});self.assertTrue(p.fits(r))
            if r['kind']=='already_delivered':break
            self.assertEqual(r['kind'],'final_part');parts.append(r['output_part'])
            self.assertEqual(r['to_byte'],len(''.join(parts).encode()))
        self.assertEqual(''.join(parts),output)
        self.assertEqual(p.load(self.d/'final.json')['output'],output)

    def test_failed_terminal_truthful(self):
        r=self.poll({'status':'failed','error':{'message':'actual failure'}})
        self.assertEqual(r['status'],'failed'); self.assertIn('actual failure',r['output'])

    def test_old_delivery_claim_migration(self):
        (self.d/'events.jsonl').write_text(json.dumps({'seq':3,'kind':'final'})+'\n')
        (self.d/'cursor').write_text('3')
        self.assertEqual(self.poll({'status':'completed','output':'old'})['kind'],'already_delivered')

    def test_old_undelivered_run_recovers_state_without_old_narration(self):
        (self.d/'events.jsonl').write_text(json.dumps({'seq':2,'kind':'tool_started','speak':'old'})+'\n')
        self.assertEqual(self.poll({'status':'running'})['kind'],'waiting')
        self.assertEqual(self.poll({'status':'completed','output':'result'})['output'],'result')

    def test_approval_exact_and_once(self):
        s={'status':'waiting_for_approval','approval':{'request_id':'a','command':'echo test'}}
        self.assertEqual(self.poll(s)['approval'],s['approval'])
        self.assertEqual(self.poll(s)['kind'],'waiting_for_approval')
        self.poll({'status':'running'});s['approval']['request_id']='b'
        self.assertEqual(self.poll(s)['approval']['request_id'],'b')

    def test_approval_discards_old_progress_but_keeps_partial_frame(self):
        prefix=b'event: tool.started\ndata: {}\n\n'
        self.raw(prefix+b'event: tool.completed\ndata: {')
        self.poll({'status':'waiting_for_approval','approval':{'request_id':'gate'}})
        self.assertEqual(p.load(self.d/'delivery.json')['raw_offset'],len(prefix))
        self.raw(prefix+b'event: tool.completed\ndata: {}\n\n')
        r=self.poll({'status':'running'})
        self.assertEqual([e['event'] for e in r['events']],['tool.completed'])

    def test_state_failure_does_not_advance(self):
        self.raw(b'event: tool.started\ndata: {}\n\n')
        with patch.object(p,'request',side_effect=RuntimeError('offline')):
            with self.assertRaises(RuntimeError):p.next_batch('run_fixture')
        self.assertFalse((self.d/'delivery.json').exists())

    def test_start_explicit_session_and_followup_history_anchor(self):
        calls=[]
        def api(method,path,payload=None,headers=None,**kw):
            calls.append((method,path,payload))
            if method=='POST':return {'run_id':'run_'+str(sum(x[0]=='POST' for x in calls)),'status':'queued'}
            return {'status':'completed','session_id':'canonical_session'}
        with patch.object(p,'request',side_effect=api),patch.object(p,'spawn_follower',return_value=123):
            one=p.start_run('first','conversation','first_key')
            two=p.start_run('what was that?','conversation','second_key')
        self.assertTrue(calls[0][2]['session_id'].startswith('exo_'))
        self.assertEqual(calls[-1][2]['session_id'],'canonical_session')
        self.assertEqual(calls[-1][2]['input'],'what was that?')

    def test_migrates_existing_header_only_conversation(self):
        p.atomic_json(self.d/'request.json',{'run_id':'run_fixture','session_key':'old','created_at':100})
        with patch.object(p,'request',side_effect=[{'status':'completed','session_id':'old_sid'},{'run_id':'run_new','status':'queued'}]) as api,patch.object(p,'spawn_follower'):
            p.start_run('followup','old','key')
            self.assertEqual(api.call_args_list[1].args[2]['session_id'],'old_sid')

    def test_busy_conversation_not_forked(self):
        p.atomic_json(self.d/'request.json',{'run_id':'run_fixture','session_key':'busy','created_at':100})
        with patch.object(p,'request',return_value={'status':'running'}) as api:
            with self.assertRaises(RuntimeError):p.start_run('new','busy','key')
            self.assertEqual(api.call_count,1)

    def test_ambiguous_post_recovered_with_same_payload_key(self):
        posts=[]
        def api(method,path,payload=None,headers=None,**kw):
            posts.append((payload,headers))
            if len(posts)==1:raise OSError('connection lost after acceptance')
            return {'run_id':'run_recovered','status':'queued'}
        with patch.object(p,'request',side_effect=api),patch.object(p,'spawn_follower'):
            with self.assertRaises(OSError):p.start_run('same','recover')
            with self.assertRaises(RuntimeError):p.start_run('different','recover')
            result=p.start_run('same','recover')
        self.assertEqual(posts[0],posts[1]);self.assertEqual(result['run_id'],'run_recovered')

    def test_idempotency_replay_no_new_post_or_timestamp(self):
        with patch.object(p,'request',side_effect=[{'run_id':'run_once','status':'queued'},{'status':'completed'}]) as api,patch.object(p,'spawn_follower'):
            p.start_run('same','one','stable');before=(p.run_dir('run_once')/'request.json').read_text()
            r=p.start_run('same','one','stable');self.assertTrue(r['replayed'])
            self.assertEqual(api.call_args_list[1].args[0],'GET')
            self.assertEqual(before,(p.run_dir('run_once')/'request.json').read_text())
            with self.assertRaises(RuntimeError):p.start_run('changed','one','stable')

    def test_persistent_capability_instructions_in_start(self):
        p.INSTRUCTIONS.write_text('Use the installed native messaging CLI.')
        with patch.object(p,'request',return_value={'run_id':'run_cap','status':'queued'}) as api,patch.object(p,'spawn_follower'):
            p.start_run('send it','capability','cap_key')
        self.assertEqual(api.call_args.args[2]['instructions'],'Use the installed native messaging CLI.')

    def test_result_recovery_does_not_reset_delivery_claim(self):
        self.poll({'status':'completed','output':'Lost answer'})
        before=(self.d/'delivery.json').read_text()
        with contextlib.redirect_stdout(io.StringIO()) as out:
            p.cmd_result(argparse.Namespace(run_id='run_fixture',offset=0))
        self.assertEqual(json.loads(out.getvalue())['output'],'Lost answer')
        self.assertEqual(before,(self.d/'delivery.json').read_text())

    def test_replay_old_request_does_not_change_latest_conversation(self):
        replies=[{'run_id':'run_one','status':'queued'}, {'status':'completed','session_id':'sid'},
                 {'run_id':'run_two','status':'queued'}, {'status':'completed'}]
        with patch.object(p,'request',side_effect=replies),patch.object(p,'spawn_follower'):
            p.start_run('one','chain','key_one');p.start_run('two','chain','key_two');p.start_run('one','chain','key_one')
        sd=p.STATE/'sessions'/hashlib.sha256(b'chain').hexdigest()/'session.json'
        self.assertEqual(p.load(sd)['last_run_id'],'run_two')

    def test_owner_transfer_fences_old_before_service_or_cursor(self):
        self.raw(b'event: tool.started\ndata: {}\n\n')
        self.assertEqual(p.attach('run_fixture','A')['consumer_epoch'],1)
        self.assertEqual(p.attach('run_fixture','B')['consumer_epoch'],2)
        before=p.load(self.d/'delivery.json')
        with patch.object(p,'request') as api:
            self.assertEqual(p.next_batch('run_fixture','A')['kind'],'superseded')
            api.assert_not_called()
        self.assertEqual(p.load(self.d/'delivery.json'),before)
        with patch.object(p,'request',return_value={'status':'completed','output':'only B'}):
            self.assertEqual(p.next_batch('run_fixture','B')['output'],'only B')
        self.assertEqual(p.attach('run_fixture','A')['kind'],'superseded')
        self.assertEqual(p.load(self.d/'delivery.json')['owner']['consumer_id'],'B')

    def test_same_owner_attach_does_not_reset_or_advance(self):
        p.attach('run_fixture','A')
        delivery=p.load(self.d/'delivery.json');delivery.update(raw_offset=12,output_offset=30,approval='gate')
        p.atomic_json(self.d/'delivery.json',delivery)
        self.assertEqual(p.attach('run_fixture','A')['consumer_epoch'],1)
        self.assertEqual(p.load(self.d/'delivery.json'),delivery)

    def test_takeover_restarts_incomplete_report_and_resurfaces_approval(self):
        p.attach('run_fixture','A')
        d=p.load(self.d/'delivery.json');d.update(output_offset=1600,raw_offset=500,approval='old_gate')
        p.atomic_json(self.d/'delivery.json',d);p.attach('run_fixture','B')
        d=p.load(self.d/'delivery.json')
        self.assertNotIn('output_offset',d);self.assertNotIn('approval',d);self.assertEqual(d['raw_offset'],500)

    def test_takeover_preserves_terminal_claim_and_explicit_recovery(self):
        p.attach('run_fixture','A')
        with patch.object(p,'request',return_value={'status':'completed','output':'answer'}):p.next_batch('run_fixture','A')
        self.assertTrue(p.attach('run_fixture','B')['already_delivered'])
        with patch.object(p,'request',return_value={'status':'completed','output':'answer'}):
            self.assertEqual(p.next_batch('run_fixture','B')['kind'],'already_delivered')
        with patch.object(p,'current_consumer',return_value='A'),contextlib.redirect_stdout(io.StringIO()) as out:
            p.cmd_result(argparse.Namespace(run_id='run_fixture',offset=0))
        self.assertEqual(json.loads(out.getvalue())['kind'],'superseded')
        with patch.object(p,'current_consumer',return_value='B'),contextlib.redirect_stdout(io.StringIO()) as out:
            p.cmd_result(argparse.Namespace(run_id='run_fixture',offset=0))
        self.assertEqual(json.loads(out.getvalue())['output'],'answer')

    def test_old_consumer_cannot_stop_steer_or_approve(self):
        p.attach('run_fixture','A');p.attach('run_fixture','B')
        with patch.object(p,'request') as api:
            for op in ['stop','steer','approval']:
                self.assertEqual(p.owned_request('run_fixture','A',op,{})['kind'],'superseded')
            api.assert_not_called()

    def test_latest_claims_new_consumer_but_observe_does_not(self):
        p.atomic_json(self.d/'request.json',{'run_id':'run_fixture','session_key':'default','created_at':1})
        p.attach('run_fixture','A')
        with patch.object(p,'current_consumer',return_value='B'),patch.object(p,'request',return_value={'status':'running'}),contextlib.redirect_stdout(io.StringIO()):
            p.cmd_latest(argparse.Namespace(session_key='default',observe=True))
            self.assertEqual(p.load(self.d/'delivery.json')['owner']['consumer_id'],'A')
            p.cmd_latest(argparse.Namespace(session_key='default',observe=False))
        self.assertEqual(p.load(self.d/'delivery.json')['owner']['consumer_id'],'B')

    def test_start_attaches_thread_and_retired_start_does_not_create_job(self):
        with patch.object(p,'request',return_value={'run_id':'run_fixture','status':'queued'}),patch.object(p,'spawn_follower'):
            self.assertEqual(p.start_run('work','session','key','A')['ownership']['consumer_id'],'A')
        p.attach('run_fixture','B')
        with patch.object(p,'request') as api:
            self.assertEqual(p.start_run('new work','session','another-key','A')['kind'],'superseded')
            api.assert_not_called()

    def test_untagged_and_preupgrade_stale_consumers_cannot_consume_owned_run(self):
        p.attach('run_fixture','B')
        with patch.object(p,'request') as api:
            self.assertEqual(p.next_batch('run_fixture',None)['kind'],'superseded')
            self.assertEqual(p.next_batch('run_fixture','old-unregistered')['kind'],'superseded')
            self.assertEqual(p.attach('run_fixture','old-unregistered')['kind'],'superseded')
            api.assert_not_called()

    def test_legacy_first_poll_registers_consumer(self):
        with patch.object(p,'request',return_value={'status':'running'}):p.next_batch('run_fixture','A')
        self.assertEqual(p.load(self.d/'delivery.json')['owner']['consumer_id'],'A')

    def test_codex_identity_precedes_operator_fixture_override(self):
        with patch.dict(p.os.environ,{'CODEX_THREAD_ID':'real-thread','EXOCTL_CONSUMER_ID':'fixture'}):
            self.assertEqual(p.current_consumer(),'real-thread')

    def test_input_preserves_quotes(self):
        self.assertEqual(p.command_input(argparse.Namespace(input="We've done that"),'start'),"We've done that")
        with patch('sys.stdin',io.StringIO('stdin text')):self.assertEqual(p.command_input(argparse.Namespace(input=None),'start'),'stdin text')
        with self.assertRaises(RuntimeError):p.command_input(argparse.Namespace(input=' '),'start')

    def test_stop_waits_for_terminal(self):
        with patch.object(p,'request',side_effect=[{'status':'stopping'},{'status':'cancelled'}]),patch.object(p.time,'sleep'),contextlib.redirect_stdout(io.StringIO()) as out:
            p.cmd_stop(argparse.Namespace(run_id='run_fixture',wait=5))
        self.assertEqual(json.loads(out.getvalue())['status'],'cancelled')
        self.assertEqual(self.poll({'status':'cancelled'})['kind'],'already_delivered')

    def test_control_approval_scoped_and_steer_input(self):
        with patch.object(p,'request',return_value={}) as api,contextlib.redirect_stdout(io.StringIO()):
            p.cmd_control(argparse.Namespace(run_id='run_fixture',choice='once',request_id='approval1'),'approval')
            self.assertEqual(api.call_args.args[2],{'choice':'once','request_id':'approval1'})
            p.cmd_control(argparse.Namespace(run_id='run_fixture',input='new direction'),'steer')
            self.assertEqual(api.call_args.args[2],{'input':'new direction'})


if __name__=='__main__':unittest.main()
