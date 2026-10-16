#!/usr/bin/env python3
"""Build a v2 checklist deterministically from a frozen case specification."""
from __future__ import annotations
import argparse,csv,json,re,sys
from datetime import datetime
from pathlib import Path
from banklib import REFS,case_spec_hash,checklist_hash_for_rows,legal_assemblies,load_csv,load_json,load_manifest,selected_files,specificity_for_file,suppression_map

FIELDS=['case_id','bank_version','bank_hash','bank_commit','runtime_version','runtime_hash','case_spec_hash','checklist_hash','purpose','bank_tier','asset','asset_name','asset_class','subtype','exposure_type','origin','question_id','construct_id','parent_question_id','relation_to_parent','construct_role','specificity_rank','factor','dimension','layer','question','manifest_suppressed','applicable','applicability_reason','applicability_source','evidence_sufficient','verdict','gate','gate_stage','scored','gate_override_reason','scored_override_reason','adjudication','adjudication_reason','explanation','source_ref','source_digest','data_as_of','evidence_available_at','observed_at','confidence','reviewer']
CASE_RE=re.compile(r'^[A-Z0-9]+(?:-[A-Z0-9]+)*$')

def validate_spec(spec,m):
 required={'case_id','decision','purpose','tier','horizon','planned_horizon_end','candidate_universe','reference_size','proposed_position','evidence_cutoff','thresholds','overrides','extensions','weights','outcome_definition','constraints','case_spec_author','created_at','bank_version','bank_hash','runtime_version','runtime_hash'}
 missing=required-set(spec)
 if missing:raise ValueError(f"case spec missing fields: {', '.join(sorted(missing))}")
 if not CASE_RE.fullmatch(str(spec['case_id'])):raise ValueError('case_id must use uppercase alphanumerics separated by single hyphens')
 if spec['purpose'] not in m['purposes']:raise ValueError('invalid purpose')
 if spec['tier'] not in {'core','full'}:raise ValueError('tier must be core or full')
 if spec['purpose'] in {'diligence','action'} and spec['tier']!='full':raise ValueError('diligence and action require tier=full')
 if spec['purpose']=='action' and not spec.get('proposed_position'):raise ValueError('action requires a non-null proposed_position')
 if spec['bank_version']!=m['bank_version'] or spec['bank_hash']!=m['bank_hash']:raise ValueError('case spec bank version/hash does not match active manifest')
 if spec['runtime_version']!=m['runtime_version'] or spec['runtime_hash']!=m['runtime_hash']:raise ValueError('case spec runtime version/hash does not match active manifest')
 for field in ('created_at','evidence_cutoff'):
  dt=datetime.fromisoformat(str(spec[field]).replace('Z','+00:00'))
  if dt.tzinfo is None:raise ValueError(f'{field} must include a timezone')
 if not isinstance(spec['candidate_universe'],list) or not spec['candidate_universe']:raise ValueError('candidate_universe must be a non-empty list')
 legal=legal_assemblies(m);seen=set()
 for a in spec['candidate_universe']:
  for f in ('asset','asset_name','asset_class','subtype','exposure_type'):
   if not str(a.get(f,'')).strip():raise ValueError(f'candidate missing {f}')
  key=(a['asset_class'],a['subtype'],a['exposure_type'])
  if key not in legal:raise ValueError(f'unsupported assembly {key}')
  if a['asset'] in seen:raise ValueError(f"duplicate asset {a['asset']}")
  seen.add(a['asset'])
 validate_extensions(spec,m,seen)

def validate_extensions(spec,m,assets):
 ext=spec.get('extensions')
 if not isinstance(ext,list) or len(ext)>8:raise ValueError('extensions must be a list of at most 8 rows')
 expected=[f"EXT-{spec['case_id']}-{i:02d}" for i in range(1,len(ext)+1)];ids=[x.get('question_id') for x in ext]
 if ids!=expected:raise ValueError(f'extension IDs must be sequential: {expected}')
 bank_ids=set();bank_constructs=set()
 for name in m['files']:
  for r in load_csv(REFS/name):bank_ids.add(r['question_id']);bank_constructs.add(r['construct_id'])
 constructs=set()
 for x in ext:
  required={'question_id','question','role','gate_stage','construct_id','factor','dimension','assets','evidence_standard','failure_example'}
  if required-set(x):raise ValueError(f"extension {x.get('question_id')} missing {sorted(required-set(x))}")
  if x['question_id'] in bank_ids or not x['question'].endswith('?'):raise ValueError(f"invalid extension {x['question_id']}")
  if x['role'] not in {'gate','scored','informational'}:raise ValueError(f"invalid extension role {x['question_id']}")
  if not re.fullmatch(r'ext_[a-z0-9_]+',x['construct_id']) or x['construct_id'] in bank_constructs or x['construct_id'] in constructs:raise ValueError(f"extension construct must be unique ext_* for {x['question_id']}")
  constructs.add(x['construct_id'])
  if x['factor'] not in m['factors'] or x['dimension'] not in m['dimension_layer_map']:raise ValueError(f"invalid extension taxonomy {x['question_id']}")
  if not x['evidence_standard'] or not x['failure_example']:raise ValueError(f"extension evidence/failure text required {x['question_id']}")
  targets=x['assets'] or sorted(assets)
  if not isinstance(targets,list) or not set(targets)<=assets or not targets:raise ValueError(f"invalid extension assets {x['question_id']}")
  if x['role']=='scored' and set(targets)!=assets:raise ValueError(f"scored extension {x['question_id']} must apply to the full candidate universe")
  if x['role']=='gate' and x['gate_stage'] not in m['gate_stages'][:-1]:raise ValueError(f"gate extension {x['question_id']} needs a valid gate_stage")
  if x['role']!='gate' and x['gate_stage']:raise ValueError(f"non-gate extension {x['question_id']} cannot have gate_stage")
  if x['question_id'] in spec.get('overrides',{}):raise ValueError(f"overrides are forbidden on extension {x['question_id']}")

def base_row(spec,m,spec_hash,a,q,origin,role,gate,stage,scored,suppressed=False,reason='',override=None):
 override=override or {}
 return {'case_id':spec['case_id'],'bank_version':m['bank_version'],'bank_hash':m['bank_hash'],'bank_commit':m.get('bank_commit','no-vcs'),'runtime_version':m['runtime_version'],'runtime_hash':m['runtime_hash'],'case_spec_hash':spec_hash,'checklist_hash':'','purpose':spec['purpose'],'bank_tier':spec['tier'],'asset':a['asset'],'asset_name':a['asset_name'],'asset_class':a['asset_class'],'subtype':a['subtype'],'exposure_type':a['exposure_type'],'origin':origin,'question_id':q['question_id'],'construct_id':q['construct_id'],'parent_question_id':q.get('parent_question_id',''),'relation_to_parent':q.get('relation_to_parent',''),'construct_role':role,'specificity_rank':str(q['_rank']),'factor':q['factor'],'dimension':q['dimension'],'layer':m['dimension_layer_map'][q['dimension']],'question':q['question'],'manifest_suppressed':'YES' if suppressed else 'NO','applicable':'NO' if suppressed else '','applicability_reason':reason if suppressed else '','applicability_source':'manifest' if suppressed else '','evidence_sufficient':'','verdict':'','gate':gate,'gate_stage':stage,'scored':scored,'gate_override_reason':override.get('gate_override_reason',''),'scored_override_reason':override.get('scored_override_reason',''),'adjudication':'','adjudication_reason':'','explanation':'','source_ref':'','source_digest':'','data_as_of':'','evidence_available_at':'','observed_at':'','confidence':'','reviewer':''}

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--case-spec',type=Path,required=True);ap.add_argument('--manifest',type=Path,default=REFS/'bank-manifest.json');ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
 try:
  m=load_manifest(args.manifest);spec=load_json(args.case_spec);validate_spec(spec,m);sh=case_spec_hash(spec);rows=[]
  ext_targets={x['question_id']:set(x['assets'] or [a['asset'] for a in spec['candidate_universe']]) for x in spec['extensions']}
  for a in spec['candidate_universe']:
   names=selected_files(m,a['asset_class'],a['subtype'],a['exposure_type']);suppression=suppression_map(m,a['asset_class'],a['subtype'],a['exposure_type']);selected=[]
   for name in names:
    rank=specificity_for_file(m,name)
    for q in load_csv(args.manifest.parent/name):
     if q['status']!='active' or (spec['tier']=='core' and q['tier']!='core'):continue
     q['_rank']=rank;selected.append(q)
   groups={}
   for q in selected:groups.setdefault(q['construct_id'],[]).append(q)
   for q in selected:
    members=groups[q['construct_id']];override=spec['overrides'].get(f"{a['asset']}:{q['question_id']}",spec['overrides'].get(q['question_id'],{}));gate=str(override.get('gate',q['default_gate'])).upper();scored=str(override.get('scored',q['default_scored'])).upper();stage=override.get('gate_stage',q['gate_stage'] if gate=='YES' else '')
    if gate not in {'YES','NO'} or scored not in {'YES','NO'}:raise ValueError(f"invalid override for {q['question_id']}")
    if len(members)>1 and (gate!=q['default_gate'] or scored!=q['default_scored']):raise ValueError(f"gate/scored overrides are forbidden on multi-row construct {q['construct_id']}")
    if gate=='YES' and (scored=='YES' or stage not in m['gate_stages'][:-1]):raise ValueError(f"invalid gate override for {q['question_id']}")
    if gate!=q['default_gate'] and not override.get('gate_override_reason'):raise ValueError(f"gate override reason required for {q['question_id']}")
    if scored!=q['default_scored'] and not override.get('scored_override_reason'):raise ValueError(f"scored override reason required for {q['question_id']}")
    highest=max(x['_rank'] for x in members);role='gate' if gate=='YES' else 'informational' if scored=='NO' else 'primary' if q['_rank']==highest else 'strict_parent';sup=q['question_id'] in suppression
    rows.append(base_row(spec,m,sh,a,q,'bank',role,gate,stage,scored,sup,suppression.get(q['question_id'],''),{'gate_override_reason':override.get('gate_override_reason','') if gate!=q['default_gate'] else '','scored_override_reason':override.get('scored_override_reason','') if scored!=q['default_scored'] else ''}))
   for x in spec['extensions']:
    if a['asset'] not in ext_targets[x['question_id']]:continue
    q=dict(x);q['_rank']=4;role=x['role'];gate='YES' if role=='gate' else 'NO';scored='YES' if role=='scored' else 'NO'
    rows.append(base_row(spec,m,sh,a,q,'extension',role,gate,x['gate_stage'],scored))
  ch=checklist_hash_for_rows(rows,m['bank_hash'],sh)
  for r in rows:r['checklist_hash']=ch
  args.output.parent.mkdir(parents=True,exist_ok=True)
  with args.output.open('w',newline='',encoding='utf-8') as f:w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(rows)
  print(json.dumps({'output':str(args.output),'rows':len(rows),'extensions':len(spec['extensions']),'assets':len(spec['candidate_universe']),'bank_version':m['bank_version'],'runtime_version':m['runtime_version'],'case_spec_hash':sh,'checklist_hash':ch},indent=2));return 0
 except (OSError,ValueError,json.JSONDecodeError) as e:print(f'error: {e}',file=sys.stderr);return 2
if __name__=='__main__':raise SystemExit(main())
