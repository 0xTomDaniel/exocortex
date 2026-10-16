#!/usr/bin/env python3
"""Verify finalized v2 history, diagnose questions, and compare independent models."""
from __future__ import annotations
import argparse,csv,itertools,json,math,sys
from collections import Counter,defaultdict
from datetime import datetime,timezone
from pathlib import Path
from banklib import (REVIEW_CONFIG_PATH,assessment_hash_for_rows,canonical_json,case_spec_hash,checklist_hash_for_rows,file_hash,load_json,load_manifest,load_review_config,row_bool,sha256_bytes)

def csv_rows(path):
 with path.open(newline='',encoding='utf-8-sig') as f:return [{k:(v or '').strip() for k,v in r.items()} for r in csv.DictReader(f)]
def instant(v,name):
 d=datetime.fromisoformat(v.replace('Z','+00:00'))
 if d.tzinfo is None:raise ValueError(f'{name} must include timezone')
 return d.astimezone(timezone.utc)
def ledger_hash(r):return sha256_bytes(canonical_json({k:v for k,v in r.items() if k!='ledger_row_hash'}))
def phi(xs,ys):
 n11=sum(a and b for a,b in zip(xs,ys));n10=sum(a and not b for a,b in zip(xs,ys));n01=sum(not a and b for a,b in zip(xs,ys));n00=len(xs)-n11-n10-n01;den=math.sqrt((n11+n10)*(n01+n00)*(n11+n01)*(n10+n00));return None if not den else (n11*n00-n10*n01)/den
def entropy(vals):
 c=Counter(vals);n=sum(c.values());return 0 if not n else -sum((v/n)*math.log2(v/n) for v in c.values())
def state(r):
 if not row_bool(r.get('applicable','')):return 'NA'
 e=row_bool(r.get('evidence_sufficient',''),allow_blank=True);v=row_bool(r.get('verdict',''),allow_blank=True)
 return 'YES' if e is True and v is True else 'NO' if e is True else 'UNKNOWN'
def resolve_construct(rs):
 app=[r for r in rs if row_bool(r.get('applicable',''))]
 if not app:return 'NA'
 top=max(int(r['specificity_rank']) for r in app);p=next(r for r in app if int(r['specificity_rank'])==top);ps=state(p);parent_no=any(int(r['specificity_rank'])<top and state(r)=='NO' for r in app)
 if ps=='NO':return 'NO'
 if ps=='YES':return 'NO' if parent_no and p.get('adjudication')=='supporting_upheld' else 'YES' if not parent_no or p.get('adjudication')=='primary_upheld' else 'CONFLICT'
 return 'NO' if parent_no else 'UNKNOWN'
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--ledger',type=Path,required=True);ap.add_argument('--outcomes',type=Path);ap.add_argument('--manifest',type=Path,default=Path(__file__).resolve().parent.parent/'references'/'bank-manifest.json');ap.add_argument('--review-config',type=Path,default=REVIEW_CONFIG_PATH);ap.add_argument('--include-post-outcome',action='store_true');ap.add_argument('--include-retrospective-outcomes',action='store_true');ap.add_argument('--output',type=Path);args=ap.parse_args()
 try:
  m=load_manifest(args.manifest);cfg=load_review_config(args.review_config);ledger=csv_rows(args.ledger);outcomes=csv_rows(args.outcomes) if args.outcomes and args.outcomes.exists() else []
  previous=''
  for n,le in enumerate(ledger,2):
   if le.get('previous_row_hash','')!=previous or not le.get('ledger_row_hash') or ledger_hash(le)!=le['ledger_row_hash']:raise ValueError(f'ledger chain/hash mismatch at row {n}')
   previous=le['ledger_row_hash']
  by_hash={r['assessment_hash']:r for r in ledger};outcome_map={}
  for o in outcomes:
   key=(o.get('assessment_hash',''),o.get('asset',''))
   if not all(key) or key in outcome_map or key[0] not in by_hash:raise ValueError(f'invalid or duplicate outcome {key}')
   outcome_map[key]=o
  compatible_banks={(x['bank_version'],x['bank_hash']) for x in m['comparable_with']};compatible_runtimes={(x['runtime_version'],x['runtime_hash']) for x in m['compatible_runtimes']}
  superseded={x.get('supersedes_assessment_hash') for x in ledger if x.get('supersedes_assessment_hash')};excluded=[];records=[]
  def ancestors(le):
   seen=set();cur=le.get('supersedes_assessment_hash','')
   while cur:
    if cur in seen or cur not in by_hash:raise ValueError('invalid supersedes chain')
    seen.add(cur);cur=by_hash[cur].get('supersedes_assessment_hash','')
   return seen
  for le in ledger:
   reason=None
   if le.get('status')!='final':reason='not_final'
   elif (le.get('bank_version'),le.get('bank_hash')) not in compatible_banks:reason='incomparable_bank'
   elif (le.get('runtime_version'),le.get('runtime_hash')) not in compatible_runtimes:reason='incompatible_runtime'
   finalized=instant(le['finalized_at'],'finalized_at');chain=ancestors(le);derived_post=any(instant(o['outcome_as_of'],'outcome_as_of')<=finalized for (h,_),o in outcome_map.items() if h in chain)
   if not reason and (derived_post or le.get('post_outcome_revision')=='YES') and not args.include_post_outcome:reason='post_outcome_revision'
   try:
    rec=load_json(Path(le['record_path']));assessment_path=Path(le['assessment_path']);spec_path=Path(rec['case_spec_path']);rs=csv_rows(assessment_path);spec=load_json(spec_path);sh=case_spec_hash(spec);ch=checklist_hash_for_rows(rs,le['bank_hash'],sh);ah=assessment_hash_for_rows(rs,sh,ch,finalized_at=le['finalized_at'],evaluator=le['evaluator'],model_id=le['model_id'],record_role=le['record_role'],supersedes_assessment_hash=le.get('supersedes_assessment_hash',''),review_config_hash=le.get('review_config_hash',''))
    observed=[instant(r['observed_at'],'observed_at') for r in rs if row_bool(r.get('evidence_sufficient',''),allow_blank=True) is True];cutoff=instant(spec['evidence_cutoff'],'evidence_cutoff');mode='prospective' if all(x<=cutoff for x in observed) else 'retrospective'
    match_fields=('assessment_hash','case_spec_hash','checklist_hash','bank_version','bank_hash','runtime_version','runtime_hash','review_config_hash','finalized_at','evaluator','model_id','record_role','temporal_mode','supersedes_assessment_hash')
    valid=(file_hash(assessment_path)==rec['checklist_file_sha256'] and file_hash(spec_path)==rec['case_spec_file_sha256'] and sh==le['case_spec_hash']==rec['case_spec_hash'] and ch==le['checklist_hash']==rec['checklist_hash'] and ah==le['assessment_hash']==rec['assessment_hash'] and mode==le.get('temporal_mode')==rec.get('temporal_mode') and all(str(le.get(f,''))==str(rec.get(f,'')) for f in match_fields))
    if not valid:reason=reason or 'hash_mismatch'
   except (OSError,ValueError,KeyError,json.JSONDecodeError,TypeError):reason=reason or 'hash_mismatch';rs=[];spec={};rec={};mode=''
   if reason:excluded.append({'assessment_hash':le.get('assessment_hash'),'reason':reason});continue
   assets={r['asset'] for r in rs};attached={a for h,a in outcome_map if h==le['assessment_hash']}
   if attached and attached!=assets:raise ValueError(f"outcome assets for {le['assessment_hash']} must exactly match assessment assets")
   outcome_allowed=mode=='prospective' or args.include_retrospective_outcomes
   for asset in attached:
    o=outcome_map[(le['assessment_hash'],asset)]
    if o.get('case_spec_hash')!=le['case_spec_hash'] or o.get('outcome_definition')!=spec.get('outcome_definition') or o.get('planned_horizon_end')!=spec.get('planned_horizon_end') or instant(o['outcome_as_of'],'outcome_as_of')<=finalized:raise ValueError(f'outcome specification mismatch for {(le["assessment_hash"],asset)}')
   for r in rs:r['_assessment_hash']=le['assessment_hash'];r['_case_spec_hash']=le['case_spec_hash'];r['_model_id']=le['model_id'];r['_record_role']=le['record_role'];r['_outcome']=outcome_map.get((le['assessment_hash'],r['asset'])) if outcome_allowed else None
   records.append({'ledger':le,'record':rec,'spec':spec,'rows':rs,'active':le['assessment_hash'] not in superseded})
  primary_groups=defaultdict(list)
  for x in records:
   if x['active'] and x['ledger']['record_role'] in {'primary','adjudicated'}:primary_groups[x['ledger']['case_spec_hash']].append(x)
  duplicate_primaries=[{'case_spec_hash':sh,'assessment_hashes':[x['ledger']['assessment_hash'] for x in xs]} for sh,xs in primary_groups.items() if len(xs)>1]
  duplicate_hashes={h for x in duplicate_primaries for h in x['assessment_hashes']}
  decision_rows=[r for x in records if x['active'] and x['ledger']['record_role'] in {'primary','adjudicated'} and x['ledger']['assessment_hash'] not in duplicate_hashes for r in x['rows']]
  pooled=[r for r in decision_rows if r.get('origin')!='extension']
  by_q=defaultdict(list)
  for r in pooled:by_q[(r['asset_class'],r['question_id'])].append(r)
  question_stats=[]
  for (cls,qid),rs in sorted(by_q.items()):
   states=[state(r) for r in rs if state(r)!='NA'];answered=[x for x in states if x in {'YES','NO'}];pred=[];under=[]
   for r in rs:
    s=state(r)
    if s in {'YES','NO'} and r['_outcome'] and r['_outcome'].get('underperformed') in {'YES','NO'}:pred.append(s=='YES');under.append(r['_outcome']['underperformed']=='YES')
   question_stats.append({'asset_class':cls,'question_id':qid,'n':len(rs),'applicable_n':len(states),'unknown_rate':round(states.count('UNKNOWN')/len(states),4) if states else None,'yes_rate_answered':round(answered.count('YES')/len(answered),4) if answered else None,'entropy_bits':round(entropy(answered),4),'outcome_n':len(pred),'phi_yes_vs_underperformance':phi(pred,under) if len(pred)>=2 else None})
  cg=defaultdict(list)
  for r in pooled:cg[(r['_assessment_hash'],r['asset'],r['asset_class'],r['construct_id'])].append(r)
  co=defaultdict(list)
  for (_,_,cls,cid),rs in cg.items():co[(cls,cid)].append(resolve_construct(rs))
  construct_stats=[]
  for (cls,cid),states in sorted(co.items()):
   app=[s for s in states if s!='NA'];ans=[s for s in app if s in {'YES','NO'}];construct_stats.append({'asset_class':cls,'construct_id':cid,'n':len(states),'applicable_n':len(app),'unknown_or_conflict_rate':round(sum(s in {'UNKNOWN','CONFLICT'} for s in app)/len(app),4) if app else None,'pass_rate_answered':round(ans.count('YES')/len(ans),4) if ans else None,'entropy_bits':round(entropy(ans),4)})
  verdict_map=defaultdict(dict)
  for r in pooled:
   if state(r) in {'YES','NO'}:verdict_map[(r['asset_class'],r['question_id'])][(r['_assessment_hash'],r['asset'])]=state(r)=='YES'
  pairs=[]
  for cls in sorted({k[0] for k in verdict_map}):
   qids=sorted(k[1] for k in verdict_map if k[0]==cls)
   for a,b in itertools.combinations(qids,2):
    common=sorted(set(verdict_map[(cls,a)])&set(verdict_map[(cls,b)]))
    if len(common)>=2:pairs.append({'asset_class':cls,'question_a':a,'question_b':b,'n':len(common),'phi':phi([verdict_map[(cls,a)][k] for k in common],[verdict_map[(cls,b)][k] for k in common])})
  # Review policy and disagreement diagnostics use verified primary/review records, never adjudications.
  review_sets=[];review_groups=defaultdict(list)
  for x in records:
   if x['ledger']['record_role'] in {'primary','independent_review'}:review_groups[x['ledger']['case_spec_hash']].append(x)
  configured={r['model_id'] for r in cfg['default_reviewers']}
  for sh,xs in sorted(review_groups.items()):
   models=sorted({x['ledger']['model_id'] for x in xs});evaluators=sorted({x['ledger']['evaluator'] for x in xs});purpose=xs[0]['spec']['purpose'];review_sets.append({'case_spec_hash':sh,'purpose':purpose,'required':purpose in cfg['required_for_purposes'],'minimum_distinct_models':cfg['minimum_distinct_models'],'distinct_models':models,'distinct_evaluators':evaluators,'default_models_present':sorted(set(models)&configured),'identities_asserted_not_provider_verified':True,'policy_met':len(models)>=cfg['minimum_distinct_models'] and len(evaluators)>=2 and set(models)<=configured})
  raw=defaultdict(list);construct_reviews=defaultdict(list);stage_reviews=defaultdict(list)
  for x in records:
   if x['ledger']['record_role'] not in {'primary','independent_review'}:continue
   for r in x['rows']:
    raw[(x['ledger']['case_spec_hash'],r['asset'],r['question_id'])].append((x['ledger']['assessment_hash'],x['ledger']['model_id'],state(r),r.get('source_ref','')))
   groups=defaultdict(list)
   for r in x['rows']:groups[(r['asset'],r['construct_id'])].append(r)
   for (asset,cid),rs in groups.items():construct_reviews[(x['ledger']['case_spec_hash'],asset,cid)].append((x['ledger']['assessment_hash'],x['ledger']['model_id'],resolve_construct(rs),sorted({r.get('source_ref','') for r in rs if r.get('source_ref')})))
   stage_group=defaultdict(list)
   for r in x['rows']:
    if r.get('gate')=='YES':stage_group[(r['asset'],r['gate_stage'])].append(r)
   for (asset,stage),rs in stage_group.items():
    states=[state(r) for r in rs];stage_state='FAILED' if 'NO' in states else 'UNRESOLVED' if any(s in {'UNKNOWN','NA'} for s in states) else 'PASSED';sources=sorted({r.get('source_ref','') for r in rs if r.get('source_ref')});stage_reviews[(x['ledger']['case_spec_hash'],asset,stage)].append((x['ledger']['assessment_hash'],x['ledger']['model_id'],stage_state,sources))
  def disagreements(groups,label):
   out=[]
   for key,vals in groups.items():
    models={v[1] for v in vals};states={v[2] for v in vals}
    if len(models)>=2 and len(states)>1:
     sources=[]
     for v in vals:sources.extend(v[3] if isinstance(v[3],list) else [v[3]] if v[3] else [])
     out.append({label:list(key),'judgments':vals,'shared_source_refs':sorted(k for k,n in Counter(sources).items() if n>1)})
   return out
  boilerplate=[]
  explanations=defaultdict(list)
  for r in pooled:
   if r.get('explanation'):explanations[r['explanation']].append((r['_assessment_hash'],r['asset'],r['question_id']))
  for text,uses in explanations.items():
   if len(uses)>=3:boilerplate.append({'explanation':text,'uses':uses})
  gate_false=[]
  for r in decision_rows:
   if r.get('gate')=='YES' and state(r)=='YES' and r['_outcome'] and r['_outcome'].get('adverse_event')=='YES':gate_false.append({'assessment_hash':r['_assessment_hash'],'asset':r['asset'],'question_id':r['question_id']})
  result={'bank_version':m['bank_version'],'runtime_version':m['runtime_version'],'admitted_assessments':len(records),'pooled_assessments':len({r['_assessment_hash'] for r in pooled}),'excluded_assessments':excluded,'duplicate_primary_groups_excluded_from_pooling':duplicate_primaries,'review_sets':review_sets,'question_disagreements':disagreements(raw,'case_spec_asset_question'),'construct_disagreements':disagreements(construct_reviews,'case_spec_asset_construct'),'gate_stage_disagreements':disagreements(stage_reviews,'case_spec_asset_stage'),'question_stats':question_stats,'construct_stats':construct_stats,'pairwise_phi_within_class':pairs,'boilerplate_rationales':boilerplate,'gate_false_negatives':gate_false,'caution':'Diagnostics are descriptive. Minimum sample size and semantic review are required; do not automate retirement, weighting, or refinement from phi, yes rates, or agreement.'}
  text=json.dumps(result,indent=2)
  if args.output:args.output.write_text(text+'\n',encoding='utf-8')
  else:print(text)
  return 0
 except (OSError,ValueError,KeyError,json.JSONDecodeError,TypeError) as e:print(f'error: {e}',file=sys.stderr);return 2
if __name__=='__main__':raise SystemExit(main())
