#!/usr/bin/env python3
"""Finalize a completed assessment into a hashed sidecar and linked ledger."""
from __future__ import annotations
import argparse,csv,json,re,sys
from datetime import datetime,time,timezone
from pathlib import Path
from banklib import (REVIEW_CONFIG_PATH,assessment_hash_for_rows,canonical_json,case_spec_hash,checklist_hash_for_rows,file_hash,load_json,load_manifest,load_review_config,row_bool,sha256_bytes)
LEDGER_FIELDS=['assessment_hash','case_id','case_spec_hash','checklist_hash','bank_version','bank_hash','runtime_version','runtime_hash','review_config_hash','finalized_at','evaluator','model_id','record_role','temporal_mode','supersedes_assessment_hash','post_outcome_revision','assessment_path','record_path','status','previous_row_hash','ledger_row_hash']
SOURCE_RE=re.compile(r'^(https?|doi|tx|filing|file|ipfs|inference):\S+$',re.I);DIGEST_RE=re.compile(r'^sha256:[0-9a-f]{64}$',re.I)
def rows(path):
 with path.open(newline='',encoding='utf-8-sig') as f:return [{k:(v or '').strip() for k,v in r.items()} for r in csv.DictReader(f)]
def aware(value,name):
 dt=datetime.fromisoformat(value.replace('Z','+00:00'))
 if dt.tzinfo is None:raise ValueError(f'{name} must include a timezone')
 return dt.astimezone(timezone.utc)
def date_interval(value,name):
 try:dt=datetime.fromisoformat(value.replace('Z','+00:00'))
 except ValueError:raise ValueError(f'{name} must be an ISO date or timestamp')
 if dt.tzinfo is not None:
  x=dt.astimezone(timezone.utc);return x,x
 d=dt.date();return datetime.combine(d,time.min,tzinfo=timezone.utc),datetime.combine(d,time.max,tzinfo=timezone.utc)
def ledger_hash(row):return sha256_bytes(canonical_json({k:v for k,v in row.items() if k!='ledger_row_hash'}))
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('checklist',type=Path);ap.add_argument('--case-spec',type=Path,required=True);ap.add_argument('--record',type=Path,required=True);ap.add_argument('--ledger',type=Path,required=True);ap.add_argument('--evaluator',required=True);ap.add_argument('--model-id',required=True);ap.add_argument('--record-role',choices=['primary','independent_review','adjudicated'],default='primary');ap.add_argument('--review-config',type=Path,default=REVIEW_CONFIG_PATH);ap.add_argument('--supersedes',default='');ap.add_argument('--outcomes',type=Path);ap.add_argument('--finalized-at');args=ap.parse_args()
 try:
  m=load_manifest();review_cfg=load_review_config(args.review_config);review_hash=file_hash(args.review_config);spec=load_json(args.case_spec);data=rows(args.checklist)
  configured_models={r['model_id'] for r in review_cfg['default_reviewers']};adjudicator_ids=set(review_cfg.get('adjudication',{}).get('permitted_producer_ids',[]))
  if args.model_id not in configured_models and not (args.record_role=='adjudicated' and args.model_id in adjudicator_ids):raise ValueError(f'model_id/producer is not configured for role {args.record_role} in {args.review_config}')
  if not data:raise ValueError('empty checklist')
  if args.record_role=='independent_review' and args.supersedes:raise ValueError('independent_review records do not supersede another assessment')
  if args.record_role=='adjudicated' and not args.supersedes:raise ValueError('adjudicated records must supersede an assessment')
  sh=case_spec_hash(spec);bank={r['bank_hash'] for r in data};rv={r.get('runtime_version','') for r in data};rh={r.get('runtime_hash','') for r in data};specs={r['case_spec_hash'] for r in data};checks={r['checklist_hash'] for r in data};cases={r['case_id'] for r in data}
  if bank!={m['bank_hash']} or rv!={m['runtime_version']} or rh!={m['runtime_hash']} or specs!={sh} or len(checks)!=1 or cases!={spec['case_id']}:raise ValueError('checklist case/bank/runtime/spec fields do not match')
  if not str(spec.get('outcome_definition','')).strip():raise ValueError('outcome_definition must be predeclared before finalization')
  if not spec.get('planned_horizon_end') or not spec.get('evidence_cutoff'):raise ValueError('planned_horizon_end and evidence_cutoff are required')
  cutoff=aware(spec['evidence_cutoff'],'evidence_cutoff');horizon_end=date_interval(spec['planned_horizon_end'],'planned_horizon_end')[1]
  if horizon_end<=cutoff:raise ValueError('planned_horizon_end must be after evidence_cutoff')
  if args.supersedes and not args.outcomes:raise ValueError('--outcomes is required with --supersedes to enforce outcome quarantine')
  if args.outcomes and not args.outcomes.exists():raise ValueError('--outcomes path does not exist')
  ch=next(iter(checks));expected=checklist_hash_for_rows(data,m['bank_hash'],sh)
  if ch!=expected:raise ValueError('checklist_hash mismatch; configuration changed after build')
  finalized=args.finalized_at or datetime.now(timezone.utc).isoformat();finalized_dt=aware(finalized,'finalized_at');observations=[];thresholds=spec.get('thresholds',{})
  for n,r in enumerate(data,2):
   app=row_bool(r.get('applicable',''));evid=row_bool(r.get('evidence_sufficient',''),allow_blank=True);verdict=row_bool(r.get('verdict',''),allow_blank=True);suppressed=row_bool(r.get('manifest_suppressed','NO'))
   if suppressed and (app or r.get('applicability_source')!='manifest'):raise ValueError(f'row {n}: manifest-suppressed row must remain manifest N/A')
   if not suppressed and r.get('applicability_source')=='manifest':raise ValueError(f'row {n}: false manifest applicability source')
   if not app:
    if not r.get('applicability_reason') or r.get('applicability_source') not in {'bank','manifest','evaluator'}:raise ValueError(f'row {n}: N/A requires reason/source')
    if evid is True or verdict is not None:raise ValueError(f'row {n}: N/A cannot have evidence/verdict')
    if r.get('gate_stage')=='identity' and r.get('applicability_source')!='manifest':raise ValueError(f'row {n}: identity gates may be N/A only by manifest rule')
    if r.get('applicability_source')=='evaluator' and r.get('reviewer')!=args.evaluator:raise ValueError(f'row {n}: evaluator N/A requires assessment evaluator attribution')
    continue
   if not r.get('explanation') or r.get('reviewer')!=args.evaluator:raise ValueError(f'row {n}: applicable rows require explanation and reviewer matching --evaluator')
   if not r.get('observed_at'):raise ValueError(f'row {n}: applicable rows require observed_at')
   observed=aware(r['observed_at'],f'row {n} observed_at')
   if observed>finalized_dt:raise ValueError(f'row {n}: observed_at exceeds finalized_at')
   if evid is True:
    if verdict is None:raise ValueError(f'row {n}: verdict required')
    if not SOURCE_RE.fullmatch(r.get('source_ref','')):raise ValueError(f'row {n}: answered row requires typed source_ref')
    if not r.get('evidence_available_at'):raise ValueError(f'row {n}: answered row requires evidence_available_at')
    available_start,available_end=date_interval(r['evidence_available_at'],f'row {n} evidence_available_at')
    if available_end>cutoff:raise ValueError(f'row {n}: evidence was not available by cutoff')
    if observed<available_start:raise ValueError(f'row {n}: observed_at precedes evidence availability')
    if r.get('source_digest') and not DIGEST_RE.fullmatch(r['source_digest']):raise ValueError(f'row {n}: invalid source_digest')
    observations.append(observed)
   elif verdict is not None:raise ValueError(f'row {n}: verdict requires evidence YES')
   if 'predeclared' in r.get('question','').lower() and r['construct_id'] not in thresholds:raise ValueError(f"row {n}: missing predeclared threshold for construct {r['construct_id']}")
   if r.get('adjudication') and not r.get('adjudication_reason'):raise ValueError(f'row {n}: adjudication reason required')
  temporal_mode='prospective' if all(x<=cutoff for x in observations) else 'retrospective'
  existing=[]
  if args.ledger.exists():
   with args.ledger.open(newline='',encoding='utf-8-sig') as f:existing=list(csv.DictReader(f))
  by_hash={r.get('assessment_hash'):r for r in existing};superseded_existing={r.get('supersedes_assessment_hash') for r in existing if r.get('supersedes_assessment_hash')}
  active_primary=[r for r in existing if r.get('case_spec_hash')==sh and r.get('record_role') in {'primary','adjudicated'} and r.get('assessment_hash') not in superseded_existing]
  if args.record_role=='primary' and not args.supersedes and active_primary:raise ValueError('an active primary already exists for this case spec; use independent_review or a superseding revision')
  if args.record_role=='adjudicated':
   if any(r.get('record_role')=='adjudicated' for r in active_primary):raise ValueError('an active adjudicated record already exists for this case spec')
   target=by_hash.get(args.supersedes,{})
   if target.get('record_role') not in {'primary','adjudicated'} or target.get('assessment_hash') in superseded_existing:raise ValueError('adjudicated records must supersede the active primary/adjudicated record')
  chain=set();cur=args.supersedes
  while cur:
   if cur in chain:raise ValueError('supersedes chain contains a cycle')
   chain.add(cur);cur=by_hash.get(cur,{}).get('supersedes_assessment_hash','')
  if args.supersedes and args.supersedes not in by_hash:raise ValueError('superseded assessment is absent from ledger')
  if args.record_role=='primary' and args.supersedes and (by_hash[args.supersedes].get('record_role') not in {'primary','adjudicated'} or args.supersedes in superseded_existing):raise ValueError('primary revisions must supersede the active primary/adjudicated record')
  post=False
  if args.outcomes and chain:
   for o in rows(args.outcomes):
    if o.get('assessment_hash') in chain and o.get('outcome_as_of') and finalized_dt>=aware(o['outcome_as_of'],'outcome_as_of'):post=True
  ah=assessment_hash_for_rows(data,sh,ch,finalized_at=finalized,evaluator=args.evaluator,model_id=args.model_id,record_role=args.record_role,supersedes_assessment_hash=args.supersedes,review_config_hash=review_hash)
  if any(r.get('assessment_hash')==ah for r in existing):raise ValueError('assessment_hash already exists in ledger')
  record={'schema_version':'2.0.0','status':'final','assessment_hash':ah,'case_id':spec['case_id'],'case_spec_hash':sh,'checklist_hash':ch,'bank_version':m['bank_version'],'bank_hash':m['bank_hash'],'bank_commit':m.get('bank_commit','no-vcs'),'runtime_version':m['runtime_version'],'runtime_hash':m['runtime_hash'],'review_config_hash':review_hash,'finalized_at':finalized,'evaluator':args.evaluator,'model_id':args.model_id,'record_role':args.record_role,'temporal_mode':temporal_mode,'supersedes_assessment_hash':args.supersedes,'post_outcome_revision':post,'assessment_path':str(args.checklist.resolve()),'checklist_file_sha256':file_hash(args.checklist),'case_spec_path':str(args.case_spec.resolve()),'case_spec_file_sha256':file_hash(args.case_spec),'control_strength':'Tamper-evident only when the ledger is anchored outside the evaluator’s unilateral authority; not a security boundary.'}
  previous=existing[-1].get('ledger_row_hash','') if existing else ''
  ledger_row={k:record.get(k,'') for k in LEDGER_FIELDS if k not in {'assessment_path','record_path','previous_row_hash','ledger_row_hash'}};ledger_row.update(assessment_path=str(args.checklist.resolve()),record_path=str(args.record.resolve()),post_outcome_revision='YES' if post else 'NO',previous_row_hash=previous);ledger_row['ledger_row_hash']=sha256_bytes(canonical_json(ledger_row))
  args.record.parent.mkdir(parents=True,exist_ok=True);args.record.write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8');args.ledger.parent.mkdir(parents=True,exist_ok=True);write_header=not args.ledger.exists() or args.ledger.stat().st_size==0
  with args.ledger.open('a',newline='',encoding='utf-8') as f:
   w=csv.DictWriter(f,fieldnames=LEDGER_FIELDS)
   if write_header:w.writeheader()
   w.writerow(ledger_row)
  print(json.dumps(record,indent=2));return 0
 except (OSError,ValueError,KeyError,json.JSONDecodeError,TypeError) as e:print(f'error: {e}',file=sys.stderr);return 2
if __name__=='__main__':raise SystemExit(main())
