#!/usr/bin/env python3
"""End-to-end regression tests for asset-assessment bank/runtime v2."""
from __future__ import annotations
import csv,json,subprocess,sys,tempfile,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent;REFS=ROOT/'references'
sys.path.insert(0,str(HERE))
from banklib import load_manifest
GPT='openai-codex/gpt-6-astra:high';FABLE='anthropic/claude-fable-5.1:high'
def run(*args,ok=True):
 p=subprocess.run([sys.executable,*map(str,args)],text=True,capture_output=True)
 if ok and p.returncode:raise AssertionError(p.stderr or p.stdout)
 return p
def csv_rows(path):
 with path.open(newline='',encoding='utf-8') as f:return list(csv.DictReader(f))
def write_rows(path,rows):
 with path.open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
class Tests(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.d=Path(self.t.name);m=load_manifest();self.spec={'schema_version':'2.0.0','case_id':'TEST-1','decision':'test','purpose':'screen','tier':'core','horizon':'4 years','planned_horizon_end':'2030-01-01','candidate_universe':[{'asset':'BTC','asset_name':'Bitcoin','asset_class':'crypto','subtype':'monetary','exposure_type':'direct'}],'reference_size':{'value':10000,'unit':'USD'},'proposed_position':None,'evidence_cutoff':'2026-01-01T23:59:59+00:00','thresholds':{},'overrides':{},'extensions':[],'weights':{'dimensions_by_layer':{'merit':{'durability':50,'value_capture':30,'meme_cultural_capital':20}},'layer_weights':{}},'outcome_definition':'Positive real risk-adjusted result at horizon.','constraints':['test only'],'case_spec_author':'tester','created_at':'2026-01-01T00:00:00+00:00','bank_version':m['bank_version'],'bank_hash':m['bank_hash'],'runtime_version':m['runtime_version'],'runtime_hash':m['runtime_hash']}
  for name in m['files']:
   for r in csv_rows(REFS/name):self.spec['thresholds'][r['construct_id']]={'name':'test','value':1,'unit':'test'}
  self.sp=self.d/'case.json';self.blank=self.d/'blank.csv';self.write_spec();self.build()
 def tearDown(self):self.t.cleanup()
 def write_spec(self,path=None,spec=None):p=path or self.sp;p.write_text(json.dumps(spec or self.spec,indent=2)+'\n');return p
 def build(self,spec=None,out=None,ok=True):return run(HERE/'build_assessment_checklist.py','--case-spec',spec or self.sp,'--output',out or self.blank,ok=ok)
 def completed(self,evaluator='exo',mutator=None,blank=None,name='completed.csv',observed='2026-01-01T12:00:00+00:00'):
  rows=csv_rows(blank or self.blank);fields=list(rows[0])
  for r in rows:
   if r['applicable']=='':r['applicable']='YES';r['applicability_reason']='Applies.';r['applicability_source']='bank'
   if r['applicable']=='YES':r.update(evidence_sufficient='YES',verdict='YES',explanation='Evidence supports this atomic verdict.',source_ref='https://example.test/source',source_digest='',data_as_of='2025-12-31',evidence_available_at='2025-12-31',observed_at=observed,confidence='high',reviewer=evaluator)
  if mutator:mutator(rows)
  p=self.d/name
  with p.open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
  return p
 def score(self,p,spec=None,rank='merit',summary=None,ok=True):
  out=self.d/f'score-{p.stem}.json';cmd=[HERE/'score_checklist.py',p,'--case-spec',spec or self.sp,'--rank-by',rank,'--output',out]
  if summary:cmd+=['--summary-csv',summary]
  r=run(*cmd,ok=ok);return json.loads(out.read_text()) if ok else r
 def finalize(self,p,evaluator='exo',model=GPT,role='primary',record='record.json',ledger='ledger.csv',time='2026-01-02T00:00:00+00:00',extra=(),ok=True):
  rec=self.d/record;led=self.d/ledger;r=run(HERE/'finalize_assessment.py',p,'--case-spec',self.sp,'--record',rec,'--ledger',led,'--evaluator',evaluator,'--model-id',model,'--record-role',role,'--finalized-at',time,*extra,ok=ok);return (rec,led) if ok else r
 def outcomes(self,items):
  fields=['assessment_hash','case_spec_hash','case_id','asset','outcome_definition','planned_horizon_end','outcome_as_of','outcome_met','underperformed','adverse_event','decision_taken','regime_window','source','recorder'];p=self.d/'outcomes.csv'
  with p.open('w',newline='',encoding='utf-8') as f:
   w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
   for rec,asset in items:w.writerow({'assessment_hash':rec['assessment_hash'],'case_spec_hash':rec['case_spec_hash'],'case_id':rec['case_id'],'asset':asset,'outcome_definition':self.spec['outcome_definition'],'planned_horizon_end':self.spec['planned_horizon_end'],'outcome_as_of':'2030-01-02T00:00:00+00:00','outcome_met':'YES','underperformed':'NO','adverse_event':'NO','decision_taken':'screen','regime_window':'test','source':'fixture','recorder':'tester'})
  return p
 def test_validator_and_all_assemblies(self):
  run(HERE/'validate_question_bank.py');m=load_manifest()
  for i,a in enumerate(m['assemblies']):
   s=dict(self.spec);s['case_id']=f'ASSEMBLY-{i}';s['tier']='full';s['candidate_universe']=[{'asset':f'A{i}','asset_name':f'Asset {i}','asset_class':a['class'],'subtype':a['subtype'],'exposure_type':a['exposure']}];sp=self.write_spec(self.d/f'a{i}.json',s);out=self.d/f'a{i}.csv';self.build(sp,out);self.assertTrue(csv_rows(out))
 def test_happy_finalize_verify(self):
  p=self.completed();rec,_=self.finalize(p);v=run(HERE/'verify_case.py','--case-spec',self.sp,'--checklist',p,'--record',rec);self.assertTrue(json.loads(v.stdout)['valid']);self.assertEqual(json.loads(rec.read_text())['temporal_mode'],'prospective')
 def test_provenance_rejections(self):
  cases=[('explanation','', 'explanation'),('reviewer','wrong','reviewer'),('evidence_available_at','2026-01-02','available by cutoff'),('observed_at','2025-01-01T00:00:00+00:00','precedes evidence availability'),('observed_at','2026-01-03T00:00:00+00:00','exceeds finalized_at'),('source_digest','sha256:bad','source_digest')]
  for field,value,message in cases:
   def bad(rows,field=field,value=value):next(r for r in rows if r['applicable']=='YES')[field]=value
   result=self.finalize(self.completed(mutator=bad,name=f'bad-{field}.csv'),ok=False);self.assertIn(message,result.stderr)
 def test_provenance_rejections_and_retrospective(self):
  def bad(rows):next(r for r in rows if r['applicable']=='YES')['source_ref']='example.test'
  self.assertIn('typed source_ref',self.finalize(self.completed(mutator=bad),ok=False).stderr)
  p=self.completed(name='retro.csv',observed='2026-01-02T12:00:00+00:00');rec,_=self.finalize(p,record='retro.json',time='2026-01-03T00:00:00+00:00');self.assertEqual(json.loads(rec.read_text())['temporal_mode'],'retrospective')
 def test_evaluator_na_requires_attribution(self):
  def bad(rows):
   r=next(x for x in rows if x['applicable']=='YES' and x['gate_stage']!='identity');r.update(applicable='NO',applicability_source='evaluator',applicability_reason='Not relevant.',evidence_sufficient='',verdict='',source_ref='',evidence_available_at='',reviewer='wrong')
  self.assertIn('evaluator attribution',self.finalize(self.completed(mutator=bad),ok=False).stderr)
 def test_case_slug_and_extension_ids_and_cap_are_enforced(self):
  self.spec['case_id']='bad case';self.write_spec();self.assertIn('case_id',self.build(ok=False).stderr);self.spec['case_id']='TEST-1'

  base={'question':'Does the extension pass?','role':'informational','gate_stage':'','factor':'use_case','dimension':'durability','assets':[],'evidence_standard':'Evidence.','failure_example':'Failure.'}
  self.spec['extensions']=[dict(base,question_id='EXT-TEST-1-02',construct_id='ext_wrong_order')];self.write_spec();self.assertIn('sequential',self.build(ok=False).stderr)
  self.spec['extensions']=[dict(base,question_id=f'EXT-TEST-1-{i:02d}',construct_id=f'ext_item_{i}') for i in range(1,10)];self.write_spec();self.assertIn('at most 8',self.build(ok=False).stderr)
 def test_extension_build_and_anti_gaming(self):
  self.spec['candidate_universe'].append({'asset':'ETH','asset_name':'Ethereum','asset_class':'crypto','subtype':'base_layer','exposure_type':'direct'});self.spec['extensions']=[{'question_id':'EXT-TEST-1-01','question':'Does the case-specific evidence support this comparable criterion?','role':'scored','gate_stage':'','construct_id':'ext_special_criterion','factor':'use_case','dimension':'durability','assets':[],'evidence_standard':'Case-specific primary evidence.','failure_example':'The criterion fails.'}];self.write_spec();self.build();ext=[r for r in csv_rows(self.blank) if r['origin']=='extension'];self.assertEqual(len(ext),2)
  self.spec['extensions'][0]['assets']=['BTC'];self.write_spec();self.assertIn('full candidate universe',self.build(ok=False).stderr)
 def test_extension_gate_subset_allowed_and_never_pooled(self):
  self.spec['extensions']=[{'question_id':'EXT-TEST-1-01','question':'Is the case-specific hard requirement satisfied?','role':'gate','gate_stage':'diligence','construct_id':'ext_hard_requirement','factor':'failure_modes','dimension':'security','assets':['BTC'],'evidence_standard':'Case-specific primary evidence.','failure_example':'The requirement fails.'}];self.write_spec();self.build();p=self.completed();rec,ledger=self.finalize(p);out=self.d/'hist.json';run(HERE/'analyze_question_history.py','--ledger',ledger,'--output',out);x=json.loads(out.read_text());self.assertFalse(any(s['question_id'].startswith('EXT-') for s in x['question_stats']))
 def test_extension_gate_remains_in_failure_diagnostics(self):
  self.spec['extensions']=[{'question_id':'EXT-TEST-1-01','question':'Is the case-specific hard requirement satisfied?','role':'gate','gate_stage':'diligence','construct_id':'ext_hard_requirement','factor':'failure_modes','dimension':'security','assets':['BTC'],'evidence_standard':'Case-specific primary evidence.','failure_example':'The requirement fails.'}];self.write_spec();self.build();p=self.completed();recp,ledger=self.finalize(p);rec=json.loads(recp.read_text());outs=self.outcomes([(rec,'BTC')]);rows=csv_rows(outs);rows[0]['adverse_event']='YES';write_rows(outs,rows);out=self.d/'hist.json';run(HERE/'analyze_question_history.py','--ledger',ledger,'--outcomes',outs,'--output',out);self.assertIn('EXT-TEST-1-01',{x['question_id'] for x in json.loads(out.read_text())['gate_false_negatives']})
 def test_two_model_independent_review_policy_and_diagnostics(self):
  p1=self.completed('exo-gpt',name='gpt.csv');rec1,ledger=self.finalize(p1,'exo-gpt',GPT,'primary','gpt.json')
  def differ(rows):
   r=next(x for x in rows if x['question_id']=='COM-MEM01');r['verdict']='NO';r['source_ref']='https://second.example/source'
  p2=self.completed('fable',differ,name='fable.csv');self.finalize(p2,'fable',FABLE,'independent_review','fable.json',time='2026-01-02T00:01:00+00:00')
  out=self.d/'hist.json';run(HERE/'analyze_question_history.py','--ledger',ledger,'--output',out);x=json.loads(out.read_text());self.assertTrue(x['review_sets'][0]['policy_met']);self.assertEqual(x['pooled_assessments'],1);self.assertTrue(x['question_disagreements']);run(HERE/'verify_independent_review.py','--ledger',ledger,'--require-all-purposes')
 def test_assessment_metadata_is_hash_bound(self):
  p=self.completed();rec,ledger=self.finalize(p);data=json.loads(rec.read_text());data['model_id']=FABLE;rec.write_text(json.dumps(data));out=self.d/'tampered.json';run(HERE/'analyze_question_history.py','--ledger',ledger,'--output',out);self.assertEqual(json.loads(out.read_text())['excluded_assessments'][0]['reason'],'hash_mismatch')
 def test_temporal_label_mismatch_is_excluded(self):
  p=self.completed();rec,ledger=self.finalize(p);data=json.loads(rec.read_text());data['temporal_mode']='retrospective';rec.write_text(json.dumps(data));out=self.d/'temporal-tamper.json';run(HERE/'analyze_question_history.py','--ledger',ledger,'--output',out);self.assertEqual(json.loads(out.read_text())['excluded_assessments'][0]['reason'],'hash_mismatch')
 def test_model_and_role_controls(self):
  p=self.completed();self.assertIn('not configured',self.finalize(p,model='fake/model:high',ok=False).stderr);self.assertIn('must supersede',self.finalize(p,role='adjudicated',ok=False).stderr);self.assertIn('do not supersede',self.finalize(p,role='independent_review',extra=('--supersedes','x','--outcomes',self.d/'none.csv'),ok=False).stderr)
  primary,ledger=self.finalize(p);self.assertIn('active primary already exists',self.finalize(p,record='p2.json',time='2026-01-02T00:01:00+00:00',ok=False).stderr)
  outcomes=self.outcomes([]);human=self.completed('human',name='human.csv');adjudicated,_=self.finalize(human,'human','human','adjudicated','adjudicated.json',time='2026-01-02T00:02:00+00:00',extra=('--supersedes',json.loads(primary.read_text())['assessment_hash'],'--outcomes',outcomes));self.assertTrue(adjudicated.exists());self.assertIn('active adjudicated',self.finalize(human,'human','human','adjudicated','adjudicated-2.json',time='2026-01-02T00:03:00+00:00',extra=('--supersedes',json.loads(primary.read_text())['assessment_hash'],'--outcomes',outcomes),ok=False).stderr)
 def test_same_evaluator_different_models_fails_independence(self):
  p1=self.completed('same',name='one.csv');_,ledger=self.finalize(p1,'same',GPT);p2=self.completed('same',name='two.csv');self.finalize(p2,'same',FABLE,'independent_review','two.json',time='2026-01-02T00:01:00+00:00');self.assertEqual(run(HERE/'verify_independent_review.py','--ledger',ledger,'--require-all-purposes',ok=False).returncode,1)
 def test_one_model_review_fails_policy(self):
  p=self.completed('exo');_,ledger=self.finalize(p,'exo',GPT);r=run(HERE/'verify_independent_review.py','--ledger',ledger,'--require-all-purposes',ok=False);self.assertEqual(r.returncode,1);self.assertEqual(run(HERE/'verify_independent_review.py','--ledger',ledger).returncode,0)
 def test_retrospective_outcomes_are_excluded_by_default(self):
  p=self.completed(observed='2026-01-02T12:00:00+00:00');recp,ledger=self.finalize(p,time='2026-01-03T00:00:00+00:00');rec=json.loads(recp.read_text());outs=self.outcomes([(rec,'BTC')]);out=self.d/'retro-history.json';run(HERE/'analyze_question_history.py','--ledger',ledger,'--outcomes',outs,'--output',out);self.assertTrue(all(x['outcome_n']==0 for x in json.loads(out.read_text())['question_stats']))
  run(HERE/'analyze_question_history.py','--ledger',ledger,'--outcomes',outs,'--include-retrospective-outcomes','--output',out);self.assertTrue(any(x['outcome_n']>0 for x in json.loads(out.read_text())['question_stats']))
 def test_post_outcome_revision_is_quarantined(self):
  p=self.completed();recp,ledger=self.finalize(p);rec=json.loads(recp.read_text());outs=self.outcomes([(rec,'BTC')]);self.finalize(p,record='revision.json',ledger='ledger.csv',time='2031-01-02T00:00:00+00:00',extra=('--supersedes',rec['assessment_hash'],'--outcomes',outs));out=self.d/'post.json';run(HERE/'analyze_question_history.py','--ledger',ledger,'--outcomes',outs,'--output',out);self.assertIn('post_outcome_revision',{x['reason'] for x in json.loads(out.read_text())['excluded_assessments']})
 def test_ties_share_rank(self):
  self.spec['candidate_universe'].append({'asset':'XBT','asset_name':'Bitcoin clone fixture','asset_class':'crypto','subtype':'monetary','exposure_type':'direct'});self.write_spec();self.build();p=self.completed();summary=self.d/'summary.csv';self.score(p,summary=summary);self.assertEqual([r['rank'] for r in csv_rows(summary)],['1','1'])
 def test_identity_and_manifest_controls(self):
  def bad(rows):
   r=next(x for x in rows if x['gate_stage']=='identity');r.update(applicable='NO',applicability_reason='skip',applicability_source='evaluator',evidence_sufficient='',verdict='',explanation='',source_ref='',observed_at='')
  self.assertIn('identity gates',self.score(self.completed(mutator=bad),ok=False).stderr)
 def test_action_gate_na_fails_closed(self):
  self.spec['purpose']='action';self.spec['tier']='full';self.spec['proposed_position']={'value':1000,'unit':'USD'};self.write_spec();self.build()
  def mutate(rows):
   for r in rows:
    if r['gate_stage']=='implementation':r.update(applicable='NO',applicability_reason='omitted',applicability_source='evaluator',evidence_sufficient='',verdict='',source_ref='',evidence_available_at='');r['reviewer']='exo'
  a=self.score(self.completed(mutator=mutate))['assets'][0];self.assertEqual(a['purpose_status'],'UNRESOLVED')
 def test_hash_tamper(self):
  def bad(rows):r=next(x for x in rows if x['scored']=='YES');r['scored']='NO';r['scored_override_reason']='late'
  self.assertIn('checklist_hash mismatch',self.score(self.completed(mutator=bad),ok=False).stderr)
 def test_missing_threshold_and_blank_outcome_rejected(self):
  del self.spec['thresholds']['crypto_market_depth'];self.write_spec();self.build();self.assertIn('missing predeclared threshold',self.finalize(self.completed(),ok=False).stderr)
  self.spec['thresholds']['crypto_market_depth']={'name':'x','value':1,'unit':'x'};self.spec['outcome_definition']='';self.write_spec();self.build();self.assertIn('outcome_definition',self.finalize(self.completed(),ok=False).stderr)
 def test_parent_entailment(self):
  def mutate(rows):
   for r in rows:
    if r['question_id']=='COM-A01':r['verdict']='NO'
    if r['question_id']=='CRY-A01':r['evidence_sufficient']='NO';r['verdict']='';r['source_ref']='';r['evidence_available_at']=''
  x=self.score(self.completed(mutator=mutate));c=next(c for c in x['assets'][0]['constructs'] if c['construct_id']=='material_adoption');self.assertEqual((c['state'],c['resolved_by']),('NO','parent_entailment'))
if __name__=='__main__':unittest.main()
