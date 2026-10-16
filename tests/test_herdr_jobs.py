import importlib.util
import json
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('jobs', Path(__file__).parents[1] / 'scripts/herdr_jobs.py')
jobs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(jobs)


class JobTests(unittest.TestCase):
    def test_validation(self):
        for r in [{}, {'operation':'review','request_id':'../x','prompt':'x'},
                  {'operation':'review','request_id':'x','prompt':'x','command':'id'},
                  {'operation':'review','request_id':'x','prompt':'x'*8001},
                  {'operation':'review','request_id':'x','prompt':''}]:
            with self.subTest(r=r), self.assertRaises(ValueError): jobs.validate(r)

    def test_once_replay_conflict_capacity(self):
        with tempfile.TemporaryDirectory() as tmp:
            config={'jobs_root':tmp,'node':'test','review_root':tmp,'python':'python3'}
            responses=[{'workspace':{'workspace_id':'w1'},'root_pane':{'pane_id':'w1:p1'}},{}]
            with patch.object(jobs,'call',side_effect=responses) as call:
                req={'operation':'review','request_id':'one','prompt':'review'}
                first=jobs.handle(config,'/fixed/config',req)
                again=jobs.handle(config,'/fixed/config',req)
                self.assertFalse(first['replayed'])
                self.assertTrue(again['replayed'])
                self.assertEqual(call.call_count,2)
                with self.assertRaises(ValueError): jobs.handle(config,'/fixed/config',dict(req,prompt='changed'))
                with self.assertRaises(ValueError): jobs.handle(config,'/fixed/config',dict(req,request_id='two'))

    def test_lost_dispatch_never_retried(self):
        with tempfile.TemporaryDirectory() as tmp:
            config={'jobs_root':tmp,'node':'test','review_root':tmp,'python':'python3'}
            req={'operation':'review','request_id':'lost','prompt':'review'}
            with patch.object(jobs,'call',side_effect=RuntimeError('lost')) as call:
                first=jobs.handle(config,'/fixed/config',req)
                replay=jobs.handle(config,'/fixed/config',req)
                self.assertEqual(first['status'],'dispatch_unknown')
                self.assertTrue(replay['replayed'])
                self.assertEqual(call.call_count,1)

    def test_environment_excludes_secrets(self):
        with patch.dict(os.environ, {'SECRET_TOKEN':'secret','SSH_AUTH_SOCK':'socket','HERDR_ENV':'1'}):
            env=jobs.environment({'home':'/fixed'})
            self.assertNotIn('SECRET_TOKEN',env)
            self.assertNotIn('SSH_AUTH_SOCK',env)
            self.assertEqual(env['HERDR_ENV'],'1')

    def test_atomic_writers(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'record.json'
            with ThreadPoolExecutor(max_workers=8) as pool:
                list(pool.map(lambda n: jobs.save(p, {'number':n}),range(50)))
            self.assertIn(json.loads(p.read_text())['number'],range(50))

    def test_private_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'link';p.symlink_to(tmp)
            with self.assertRaises(ValueError): jobs.private_directory(p)
            Path(tmp).chmod(0o755)
            with self.assertRaises(ValueError): jobs.private_directory(Path(tmp))

    def test_receipt_deadline(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)
            (p/'record.json').write_text(json.dumps({'status':'running','created_at':0}))
            self.assertEqual(jobs.receipt({'node':'test'},p)['status'],'interrupted')


if __name__ == '__main__': unittest.main()
